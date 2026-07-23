#!/usr/bin/env python3
"""Orchestrazione del 'cervello' di JARVIS: conversazione + tool-use su Claude.

Mantiene la history in memoria per una sessione (nessuna persistenza su disco
in questa fase). Il ciclo tool-use segue il pattern standard dell'SDK Anthropic:
si richiama messages.create finche' Claude non risponde con testo puro invece
di un altro tool_use.
"""
import os
import sys

import anthropic

from tools import TOOLS, dispatch_tool

if not os.environ.get("ANTHROPIC_API_KEY"):
    sys.exit(
        "Errore: variabile d'ambiente ANTHROPIC_API_KEY mancante.\n"
        "Crea un file 'cred' (vedi cred.example) e fai 'source cred' prima di avviare il core."
    )

DEFAULT_MODEL = os.environ.get("JARVIS_MODEL", "claude-sonnet-5")
MAX_TOKENS = 1024

SYSTEM_PROMPT = (
    "Sei JARVIS, l'assistente vocale personale di Simone nella sua homelab. "
    "Rispondi sempre in italiano, in modo conciso e naturale: le tue risposte "
    "vengono lette ad alta voce da un sintetizzatore vocale, quindi non usare mai "
    "elenchi puntati, markdown o formattazioni: solo frasi semplici, come parleresti. "
    "Usa i tool disponibili quando servono informazioni concrete invece di indovinare."
)


class Brain:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.client = anthropic.Anthropic()
        self.model = model
        self.history = []

    def reset(self):
        self.history = []

    def ask(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})

        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=self.history,
            )
            self.history.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                return "".join(
                    block.text for block in response.content if block.type == "text"
                )

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = dispatch_tool(block.name, block.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        }
                    )
            self.history.append({"role": "user", "content": tool_results})
