#!/usr/bin/env python3
"""Riconoscimento gesti dalla webcam per il controllo di media/dashboard.

Usa il `GestureRecognizer` della Tasks API di MediaPipe con il modello
pre-addestrato di Google: riconosce gia' "Open_Palm", "Closed_Fist",
"Thumb_Up", "Thumb_Down" (tra gli altri) senza bisogno di addestrare nulla.
Il modello (~8MB) viene scaricato automaticamente in questa cartella al
primo avvio.

Gesti mappati in questa v1:
- Open_Palm   -> play/pause
- Thumb_Up    -> volume su
- Thumb_Down  -> volume giu'
- Closed_Fist -> mute
- swipe orizzontale della mano (calcolato dalla posizione del polso, non dal
  modello di gesti) -> cambia vista sulla dashboard

Il riconoscimento e' separato dall'azione: ogni gesto confermato invoca una
callback, e' il chiamante (client.py) a decidere cosa fare davvero.
"""
import time
import urllib.request
from collections import deque
from pathlib import Path
from typing import Callable, Optional

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/"
    "gesture_recognizer/float16/latest/gesture_recognizer.task"
)
MODEL_PATH = Path(__file__).parent / "gesture_recognizer.task"

SWIPE_THRESHOLD = 0.08  # variazione minima di x (normalizzata) tra due frame

GESTURE_NAMES = {
    "Open_Palm": "open_palm",
    "Closed_Fist": "fist",
    "Thumb_Up": "thumbs_up",
    "Thumb_Down": "thumbs_down",
}


def _ensure_model() -> None:
    if not MODEL_PATH.exists():
        print("Scarico il modello di riconoscimento gesti (~8MB, una tantum)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)


class GestureController:
    def __init__(
        self,
        on_gesture: Callable[[str], None],
        camera_index: int = 0,
        hold_frames: int = 5,
        cooldown_seconds: float = 1.5,
        min_score: float = 0.6,
    ):
        _ensure_model()
        self.on_gesture = on_gesture
        self.camera_index = camera_index
        self.hold_frames = hold_frames
        self.cooldown_seconds = cooldown_seconds
        self.min_score = min_score
        self._recent: deque = deque(maxlen=hold_frames)
        self._last_trigger_at = 0.0
        self._last_wrist_x: Optional[float] = None

        base_options = mp_python.BaseOptions(model_asset_path=str(MODEL_PATH))
        options = vision.GestureRecognizerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
        )
        self.recognizer = vision.GestureRecognizer.create_from_options(options)

    def _maybe_trigger(self, gesture: Optional[str]) -> None:
        now = time.monotonic()
        if now - self._last_trigger_at < self.cooldown_seconds:
            return
        self._recent.append(gesture)
        if len(self._recent) == self.hold_frames and all(g == gesture for g in self._recent) and gesture:
            self._last_trigger_at = now
            self._recent.clear()
            self.on_gesture(gesture)

    def run(self, show_preview: bool = True) -> None:
        """Loop bloccante: apre la webcam e riconosce i gesti finche' non premi 'q'
        (con preview attiva) o il processo viene interrotto."""
        cap = cv2.VideoCapture(self.camera_index)
        start_time = time.monotonic()
        consecutive_failures = 0
        max_consecutive_failures = 60  # tollera ~2s di frame falliti (webcam in "warm-up")
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        print("Impossibile leggere dalla webcam, esco.")
                        break
                    time.sleep(0.03)
                    continue
                consecutive_failures = 0
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                timestamp_ms = int((time.monotonic() - start_time) * 1000)
                result = self.recognizer.recognize_for_video(mp_image, timestamp_ms)

                gesture = None
                if result.gestures and result.gestures[0]:
                    top = result.gestures[0][0]
                    if top.category_name in GESTURE_NAMES and top.score >= self.min_score:
                        gesture = GESTURE_NAMES[top.category_name]

                if result.hand_landmarks:
                    hand = result.hand_landmarks[0]
                    wrist_x = hand[0].x
                    if self._last_wrist_x is not None:
                        delta = wrist_x - self._last_wrist_x
                        if delta > SWIPE_THRESHOLD:
                            gesture = "swipe_right"
                        elif delta < -SWIPE_THRESHOLD:
                            gesture = "swipe_left"
                    self._last_wrist_x = wrist_x

                    if show_preview:
                        h, w = frame.shape[:2]
                        for landmark in hand:
                            cv2.circle(frame, (int(landmark.x * w), int(landmark.y * h)), 3, (0, 255, 0), -1)
                else:
                    self._last_wrist_x = None

                self._maybe_trigger(gesture)

                if show_preview:
                    cv2.putText(
                        frame, gesture or "", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2,
                    )
                    cv2.imshow("JARVIS - gesti", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
        finally:
            cap.release()
            if show_preview:
                cv2.destroyAllWindows()
