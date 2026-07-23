# Changelog

Ogni voce spiega cosa è cambiato e **perché**, non solo il cosa — per quello basta `git log`.

## v0.1.0 — Prima versione: voce + Claude + gesti base

- **Struttura del progetto**: `core/` (cervello, Claude API + tool-use, pensato per girare sempre acceso sul mini PC) separato da `client/` (voce + gesti, pensato per girare dove c'è microfono/webcam), collegati via WebSocket con solo testo che passa tra le due parti.
- **Perché questo split**: la chiave Claude API resta solo sul mini PC, mai sul client; e spostare in futuro il client dal MacBook al PC Windows fisso (Fase 2 della roadmap) non richiederà toccare il cervello, solo ripuntare `JARVIS_CORE_URL`.
- **Voce**: wake word "hey jarvis" (openWakeWord, modello pre-addestrato incluso), trascrizione locale (faster-whisper, nessun audio inviato al cloud), risposta sintetizzata (edge-tts, con fallback offline pyttsx3).
- **Gesti**: riconoscimento base via MediaPipe Hands (mano aperta, pollice su/giù, pugno, swipe) mappato a comandi media/dashboard — per ora solo loggati, non ancora collegati ad azioni reali.
- **Cervello**: primo scaffold di tool-use con Claude (`get_current_time`, `get_system_status`), pensato per essere esteso in futuro con tool Home Assistant.
- Python 3.11 usato esplicitamente per entrambe le parti (via `python3.11`), perché su questo Mac Python di default è 3.14 e alcune dipendenze (`mediapipe`, `faster-whisper`, pacchetti audio) non hanno ancora wheel pronte per versioni Python così recenti.
