#!/usr/bin/env python3
"""Sintesi vocale della risposta di JARVIS: edge-tts (voce neurale, richiede
internet) con fallback su pyttsx3 (offline, voce di sistema) se edge-tts
non e' raggiungibile. La riproduzione usa ffplay (ffmpeg) per restare
identica su macOS/Windows/Linux.
"""
import asyncio
import os
import subprocess
import tempfile

import edge_tts

VOICE = "it-IT-DiegoNeural"


async def _synthesize(text: str, out_path: str) -> None:
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(out_path)


def _play_audio_file(path: str) -> None:
    subprocess.run(
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
        check=True,
    )


def _speak_offline(text: str) -> None:
    import pyttsx3

    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


def speak(text: str) -> None:
    if not text:
        return
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name
        asyncio.run(_synthesize(text, tmp_path))
        _play_audio_file(tmp_path)
    except Exception:
        _speak_offline(text)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
