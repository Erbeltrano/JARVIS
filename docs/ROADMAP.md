# Roadmap

## Fase 1 — v0.1.0 (attuale)

- Assistente vocale: wake word ("hey jarvis") → trascrizione locale → Claude API → risposta parlata.
- Controllo gesti base via webcam (MediaPipe): play/pause, volume, mute, cambio vista dashboard.
- Cervello (`core/`) sul mini PC Linux della homelab, sempre acceso.
- Client (`client/`) sul MacBook, con codice scritto in modo cross-platform in vista della Fase 2.
- Repository privato documentato su GitHub.

## Fase 2 — migrazione del client

- Spostare `client/` dal MacBook al PC Windows fisso (lo stesso che oggi fa girare il bot di Clash of Clans via BlueStacks).
- Nessuna modifica al `core/`: basta puntare `JARVIS_CORE_URL` allo stesso mini PC.
- Verificare che le librerie usate (`sounddevice`, `opencv-python`, `mediapipe`, `openwakeword`, `edge-tts`) funzionino allo stesso modo su Windows; possibile necessità di installare `ffmpeg` per Windows e aggiungerlo al `PATH`.

## Fase 3 — domotica reale (Home Assistant)

- ✅ **Fatto (v0.2.0), in anticipo**: `client/home_assistant.py` collega direttamente i gesti a una luce reale via API REST di Home Assistant (pollice su = accendi, pugno chiuso = spegni). Indipendente da Claude/core: passa solo per il client.
- **Ancora da fare**: integrare Home Assistant come tool in `core/tools.py`, per dare a Claude la possibilità di controllare luci/prese/sensori **via voce** (oggi solo i gesti sono collegati), e per gestire più dispositivi oltre alla singola luce di test.
- **Feature "spatial pointing"** (richiesta esplicitamente): puntando con la mano/il dito verso un punto della stanza tramite la webcam, JARVIS deve capire a quale luce/dispositivo fisico ci si riferisce e attivarlo di conseguenza — senza doverlo nominare a voce. Serve:
  - Calibrazione della posizione dei dispositivi controllabili rispetto all'inquadratura della webcam (mappatura spaziale).
  - Estensione di `gestures/gesture_control.py` per stimare la direzione di puntamento (non solo il gesto statico).
  - Un tool Home Assistant che riceva "punto stimato" → dispositivo più vicino → azione.

## Idee non ancora prioritizzate

- Persistenza della conversazione (oggi la history di `brain.py` vive solo in RAM, si perde al riavvio del core).
- Autenticazione sul WebSocket del core (oggi chiunque sulla rete della homelab può connettersi a `/ws`).
- Notifiche/allarmi proattivi (es. JARVIS che avvisa di qualcosa senza essere interpellato).
