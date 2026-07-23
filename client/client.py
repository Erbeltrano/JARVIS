#!/usr/bin/env python3
"""Loop principale del client JARVIS: per ora gira su questo MacBook,
in futuro sul PC Windows fisso (stesso PC del bot Clash of Clans).

Ascolta la wake word "hey jarvis", registra la frase, la invia al core
(Claude, sul mini PC) via WebSocket e parla la risposta. In parallelo,
un thread separato ascolta i gesti dalla webcam per i comandi rapidi di
media/dashboard (vedi gestures/gesture_control.py).

Nota: la preview della webcam (finestra OpenCV) resta sul thread
principale perche' su macOS le finestre vanno create sul main thread;
il loop vocale gira quindi in un thread in background.
"""
import os
import sys
import threading

import websockets.sync.client as ws_client

from gestures.gesture_control import GestureController
from home_assistant import turn_off_light, turn_on_light
from voice.stt import SpeechToText
from voice.tts import speak
from voice.wake_word import WakeWordListener

CORE_URL = os.environ.get("JARVIS_CORE_URL")
if not CORE_URL:
    sys.exit(
        "Errore: variabile d'ambiente JARVIS_CORE_URL mancante.\n"
        "Crea un file 'cred' (vedi cred.example) e fai 'source cred' prima di avviare il client."
    )

HA_LIGHT_ENTITY_ID = os.environ.get("HA_LIGHT_ENTITY_ID", "light.luce_camera_1")


def ask_core(text: str) -> str:
    with ws_client.connect(CORE_URL) as connection:
        connection.send(text)
        return connection.recv()


def handle_gesture(gesture: str) -> None:
    print(f"[gesto] {gesture}")
    if gesture == "thumbs_up":
        print(f"Pollice su rilevato: accendo {HA_LIGHT_ENTITY_ID}")
        turn_on_light(HA_LIGHT_ENTITY_ID)
    elif gesture == "fist":
        print(f"Pugno chiuso rilevato: spengo {HA_LIGHT_ENTITY_ID}")
        turn_off_light(HA_LIGHT_ENTITY_ID)
    # altri gesti: solo log per ora. In futuro: tasti multimediali reali o
    # chiamate all'API della dashboard per cambiare vista.


def voice_loop() -> None:
    wake_word = WakeWordListener()
    stt = SpeechToText()

    print("JARVIS pronto. Di' 'hey jarvis' per iniziare.")
    while True:
        wake_word.wait_for_wake_word()
        print("Wake word rilevata, ti ascolto...")
        audio = stt.record_utterance()
        text = stt.transcribe(audio)
        if not text:
            continue
        print(f"Tu: {text}")
        reply = ask_core(text)
        print(f"JARVIS: {reply}")
        speak(reply)


def main() -> None:
    voice_thread = threading.Thread(target=voice_loop, daemon=True)
    voice_thread.start()

    controller = GestureController(on_gesture=handle_gesture)
    controller.run(show_preview=True)


if __name__ == "__main__":
    main()
