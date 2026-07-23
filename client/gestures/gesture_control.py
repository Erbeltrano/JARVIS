#!/usr/bin/env python3
"""Riconoscimento gesti dalla webcam per il controllo di media/dashboard.

Gesti riconosciuti in questa v1:
- mano aperta (5 dita alzate)  -> play/pause
- pollice su / pollice giu'    -> volume su / volume giu'
- pugno chiuso                 -> mute
- swipe orizzontale della mano -> cambia vista sulla dashboard

Il riconoscimento vero e proprio (MediaPipe Hands) e' separato dall'azione:
ogni gesto confermato invoca una callback, e' il chiamante (client.py) a
decidere cosa fare davvero (tasti multimediali, chiamata all'API della
dashboard, ecc).
"""
import time
from collections import deque
from typing import Callable, Optional

import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands

FINGER_TIPS = [4, 8, 12, 16, 20]
FINGER_PIPS = [3, 6, 10, 14, 18]

SWIPE_THRESHOLD = 0.08  # variazione minima di x (normalizzata) tra due frame


def _fingers_up(landmarks) -> list:
    """Una entry per dito (pollice, indice, medio, anulare, mignolo)."""
    fingers = [landmarks[4].x < landmarks[3].x]  # il pollice si muove sull'asse x
    for tip, pip in zip(FINGER_TIPS[1:], FINGER_PIPS[1:]):
        fingers.append(landmarks[tip].y < landmarks[pip].y)
    return fingers


def _classify_gesture(landmarks) -> Optional[str]:
    fingers = _fingers_up(landmarks)
    total_up = sum(fingers)

    if total_up == 5:
        return "open_palm"
    if total_up == 0:
        return "fist"
    if fingers[0] and total_up == 1:
        wrist_y = landmarks[0].y
        thumb_tip_y = landmarks[4].y
        return "thumbs_up" if thumb_tip_y < wrist_y else "thumbs_down"
    return None


class GestureController:
    def __init__(
        self,
        on_gesture: Callable[[str], None],
        camera_index: int = 0,
        hold_frames: int = 5,
        cooldown_seconds: float = 1.5,
    ):
        self.on_gesture = on_gesture
        self.camera_index = camera_index
        self.hold_frames = hold_frames
        self.cooldown_seconds = cooldown_seconds
        self._recent: deque = deque(maxlen=hold_frames)
        self._last_trigger_at = 0.0
        self._last_wrist_x: Optional[float] = None

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
        try:
            with mp_hands.Hands(
                max_num_hands=1, min_detection_confidence=0.6, min_tracking_confidence=0.5
            ) as hands:
                while True:
                    ok, frame = cap.read()
                    if not ok:
                        break
                    frame = cv2.flip(frame, 1)
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = hands.process(rgb)

                    gesture = None
                    if results.multi_hand_landmarks:
                        hand_landmarks = results.multi_hand_landmarks[0]
                        landmarks = hand_landmarks.landmark
                        gesture = _classify_gesture(landmarks)

                        wrist_x = landmarks[0].x
                        if self._last_wrist_x is not None:
                            delta = wrist_x - self._last_wrist_x
                            if delta > SWIPE_THRESHOLD:
                                gesture = "swipe_right"
                            elif delta < -SWIPE_THRESHOLD:
                                gesture = "swipe_left"
                        self._last_wrist_x = wrist_x

                        if show_preview:
                            mp.solutions.drawing_utils.draw_landmarks(
                                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                            )
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
