#!/usr/bin/env python3
"""Registra una frase dal microfono dopo la wake word e la trascrive in locale
con faster-whisper (nessun invio audio a servizi cloud).
"""
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
CHUNK_MS = 100
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_MS / 1000)


class SpeechToText:
    def __init__(self, model_size: str = "small"):
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def record_utterance(
        self,
        max_seconds: float = 8.0,
        silence_seconds: float = 1.2,
        silence_threshold: int = 500,
    ) -> np.ndarray:
        """Registra finche' non rileva silence_seconds di silenzio (o max_seconds)."""
        silence_chunks_needed = int(silence_seconds * 1000 / CHUNK_MS)
        max_chunks = int(max_seconds * 1000 / CHUNK_MS)

        frames = []
        silence_run = 0
        with sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=CHUNK_SAMPLES
        ) as stream:
            for _ in range(max_chunks):
                chunk, _ = stream.read(CHUNK_SAMPLES)
                frames.append(chunk.copy())
                volume = np.abs(chunk).mean()
                if volume < silence_threshold:
                    silence_run += 1
                    if silence_run >= silence_chunks_needed and len(frames) > silence_chunks_needed:
                        break
                else:
                    silence_run = 0

        return np.concatenate(frames)[:, 0]

    def transcribe(self, audio: np.ndarray) -> str:
        audio_float = audio.astype(np.float32) / 32768.0
        segments, _ = self.model.transcribe(audio_float, language="it")
        return " ".join(segment.text.strip() for segment in segments).strip()
