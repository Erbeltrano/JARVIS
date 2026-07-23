#!/usr/bin/env python3
"""Rilevazione della wake word ('hey jarvis') dal microfono, con openWakeWord.

openWakeWord include gia' un modello pre-addestrato "hey_jarvis": non serve
addestrare nulla per la v1. Il modello lavora su blocchi audio mono a 16kHz,
tipicamente 1280 campioni (80ms) alla volta.
"""
import numpy as np
import sounddevice as sd
from openwakeword.model import Model

SAMPLE_RATE = 16000
CHUNK_SAMPLES = 1280  # 80ms a 16kHz, formato atteso da openWakeWord


class WakeWordListener:
    def __init__(self, wakeword_model: str = "hey_jarvis", threshold: float = 0.5):
        self.model = Model(wakeword_models=[wakeword_model])
        self.threshold = threshold

    def wait_for_wake_word(self) -> None:
        """Blocca finche' non sente la wake word, poi ritorna."""
        with sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=CHUNK_SAMPLES
        ) as stream:
            while True:
                audio_chunk, _ = stream.read(CHUNK_SAMPLES)
                audio = audio_chunk[:, 0]
                predictions = self.model.predict(audio)
                if any(score > self.threshold for score in predictions.values()):
                    self.model.reset()
                    return
