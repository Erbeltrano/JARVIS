#!/usr/bin/env python3
"""Client minimale per l'API REST di Home Assistant.

Usato per il momento solo per il toggle di una luce dal gesto "pugno chiuso"
(vedi client.py). In futuro ospiterà anche la logica di "spatial pointing"
(puntare una luce con la mano) descritta in docs/ROADMAP.md.
"""
import os

import requests

HA_URL = os.environ.get("HA_URL")
HA_TOKEN = os.environ.get("HA_TOKEN")


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }


def call_service(domain: str, service: str, entity_id: str) -> None:
    if not HA_URL or not HA_TOKEN:
        print("Home Assistant non configurato (HA_URL/HA_TOKEN mancanti), salto.")
        return
    url = f"{HA_URL}/api/services/{domain}/{service}"
    response = requests.post(url, headers=_headers(), json={"entity_id": entity_id}, timeout=5)
    response.raise_for_status()


def toggle_light(entity_id: str) -> None:
    call_service("light", "toggle", entity_id)


def turn_on_light(entity_id: str) -> None:
    call_service("light", "turn_on", entity_id)


def turn_off_light(entity_id: str) -> None:
    call_service("light", "turn_off", entity_id)
