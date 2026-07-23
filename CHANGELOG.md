# Changelog

Ogni voce spiega cosa è cambiato e **perché**, non solo il cosa — per quello basta `git log`.

## v0.2.0 — Integrazione Home Assistant reale (gesti → luci), fix verificati dal vivo

- **Home Assistant collegato davvero**, in anticipo sulla Fase 3 della roadmap: `client/home_assistant.py` parla con l'API REST (`turn_on_light`/`turn_off_light`/`toggle_light`). **Pollice su accende, pugno chiuso spegne** una luce reale (`HA_LIGHT_ENTITY_ID`), verificato dal vivo. Volutamente indipendente dal `core`/Claude: funziona anche senza chiave Anthropic configurata, perché il client parla direttamente con Home Assistant.
- **Fix wake word**: openWakeWord di default richiede `tflite-runtime`, non disponibile per Python 3.11 su Apple Silicon (scoperto lanciando `client.py` dal vivo: il thread vocale andava in crash all'avvio). Passato esplicitamente a `inference_framework="onnx"` (onnxruntime è già una dipendenza di mediapipe) e aggiunto il download automatico della variante `.onnx` del modello (openWakeWord scarica di suo solo la `.tflite`).
- **Fix selezione webcam**: scoperto dal vivo che con un iPhone vicino e sbloccato, macOS può dirottare Continuity Camera sull'indice `0` al posto della webcam integrata del Mac. `gesture_control.py` ora usa AVFoundation (via pyobjc, già presente come dipendenza di mediapipe) per trovare esplicitamente l'indice della camera il cui nome non contiene "iPhone", invece di assumere sempre l'indice `0`. Fallback automatico all'indice `0` su piattaforme diverse da macOS (utile per la Fase 2, migrazione al PC Windows).

## v0.1.0 — Prima versione: voce + Claude + gesti base

- **Struttura del progetto**: `core/` (cervello, Claude API + tool-use, pensato per girare sempre acceso sul mini PC) separato da `client/` (voce + gesti, pensato per girare dove c'è microfono/webcam), collegati via WebSocket con solo testo che passa tra le due parti.
- **Perché questo split**: la chiave Claude API resta solo sul mini PC, mai sul client; e spostare in futuro il client dal MacBook al PC Windows fisso (Fase 2 della roadmap) non richiederà toccare il cervello, solo ripuntare `JARVIS_CORE_URL`.
- **Voce**: wake word "hey jarvis" (openWakeWord, modello pre-addestrato incluso), trascrizione locale (faster-whisper, nessun audio inviato al cloud), risposta sintetizzata (edge-tts, con fallback offline pyttsx3).
- **Gesti**: riconoscimento base via MediaPipe Hands (mano aperta, pollice su/giù, pugno, swipe) mappato a comandi media/dashboard — per ora solo loggati, non ancora collegati ad azioni reali.
- **Cervello**: primo scaffold di tool-use con Claude (`get_current_time`, `get_system_status`), pensato per essere esteso in futuro con tool Home Assistant.
- Python 3.11 usato esplicitamente per entrambe le parti (via `python3.11`), perché su questo Mac Python di default è 3.14 e alcune dipendenze (`mediapipe`, `faster-whisper`, pacchetti audio) non hanno ancora wheel pronte per versioni Python così recenti.
