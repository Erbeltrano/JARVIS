#!/usr/bin/env python3
"""Tool che il cervello di JARVIS (brain.py) puo' invocare tramite Claude.

Per ora solo placeholder (ora/data, stato del mini PC) per validare la
pipeline di tool-use. In una fase futura qui verranno aggiunti i tool
per il controllo di Home Assistant (luci, prese, sensori).
"""
import datetime
import platform

try:
    import psutil
except ImportError:
    psutil = None

TOOLS = [
    {
        "name": "get_current_time",
        "description": "Restituisce la data e l'ora attuali nella homelab.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_system_status",
        "description": "Restituisce CPU, RAM e disco del mini PC che esegue il cervello di JARVIS.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def _get_current_time(_tool_input: dict) -> str:
    now = datetime.datetime.now()
    return now.strftime("%A %d %B %Y, ore %H:%M")


def _get_system_status(_tool_input: dict) -> str:
    if psutil is None:
        return "psutil non installato: impossibile leggere lo stato del sistema."
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return (
        f"CPU al {cpu}%, RAM al {mem.percent}% "
        f"({mem.used // (1024 ** 2)}MB usati su {mem.total // (1024 ** 2)}MB), "
        f"disco al {disk.percent}% su {platform.node()}."
    )


_HANDLERS = {
    "get_current_time": _get_current_time,
    "get_system_status": _get_system_status,
}


def dispatch_tool(name: str, tool_input: dict) -> str:
    handler = _HANDLERS.get(name)
    if handler is None:
        return f"Tool sconosciuto: {name}"
    try:
        return handler(tool_input)
    except Exception as exc:
        return f"Errore nell'esecuzione del tool {name}: {exc}"
