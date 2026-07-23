#!/usr/bin/env python3
"""Server del 'cervello' di JARVIS: gira sul mini PC sempre acceso.

Espone un WebSocket (/ws) su cui i client (voce/gesti) inviano testo gia'
trascritto e ricevono la risposta di Claude, piu' una dashboard web minimale
di stato su http://<ip-minipc>:8080/
"""
import asyncio
import logging
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from brain import Brain

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("jarvis-core")

app = FastAPI(title="JARVIS core")
brain = Brain()

conversation_log: list[dict] = []

STATIC_DIR = os.path.join(os.path.dirname(__file__), "dashboard", "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def dashboard():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/api/log")
def get_log():
    return conversation_log[-50:]


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connesso: %s", websocket.client)
    try:
        while True:
            user_text = await websocket.receive_text()
            logger.info("Utente: %s", user_text)
            reply = await asyncio.to_thread(brain.ask, user_text)
            logger.info("JARVIS: %s", reply)
            conversation_log.append({"user": user_text, "jarvis": reply})
            await websocket.send_text(reply)
    except WebSocketDisconnect:
        logger.info("Client disconnesso: %s", websocket.client)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
