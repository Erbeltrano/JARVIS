# JARVIS — assistente vocale personale per la homelab

**Versione:** 0.1.0 (vedi `CHANGELOG.md`)

Assistente vocale personale ispirato a JARVIS di Iron Man: ascolta una wake word ("hey jarvis"), trascrive quello che dici, ragiona con Claude (Anthropic) e ti risponde a voce. In parallelo riconosce alcuni gesti dalla webcam per comandi rapidi (media/dashboard), stile "controllo gestuale".

Il progetto è diviso in due parti che girano su macchine diverse della homelab:

- **`core/`** — il "cervello": server sempre acceso che parla con Claude, gestito su un mini PC Linux.
- **`client/`** — il "corpo": ascolto vocale + riconoscimento gesti, per ora su questo MacBook, in futuro sul PC Windows fisso.

## Architettura

```
┌─────────────────────────┐         WebSocket (testo)        ┌──────────────────────────┐
│  client/  (MacBook ora,  │  ───────────────────────────▶   │  core/  (mini PC, sempre  │
│  PC Windows in futuro)   │  ◀───────────────────────────   │  acceso)                  │
│                          │                                  │                          │
│  wake word → STT (voce)  │                                  │  Claude API (brain.py)   │
│  gesti webcam → comandi  │                                  │  + tool use (tools.py)   │
│  TTS (risposta parlata)  │                                  │  + dashboard web :8080    │
└─────────────────────────┘                                  └──────────────────────────┘
```

Il client non ha mai accesso diretto alla chiave Claude: invia solo il testo trascritto al core via WebSocket e riceve la risposta da leggere ad alta voce. Questo rende banale, in futuro, spostare `client/` su un'altra macchina (es. il PC Windows che oggi fa girare il bot di Clash of Clans) senza toccare il cervello.

## Struttura del progetto

```
JARVIS/
├── core/                     # gira sul mini PC (sempre acceso)
│   ├── main.py                 # server FastAPI + WebSocket + dashboard
│   ├── brain.py                  # conversazione + tool-use con Claude
│   ├── tools.py                   # tool che Claude può chiamare (ora/data, stato sistema)
│   ├── dashboard/static/index.html
│   ├── requirements.txt
│   ├── cred.example                # ANTHROPIC_API_KEY (copia in `cred`, non versionato)
│   └── jarvis-core.service           # unit systemd --user per il deploy sul mini PC
├── client/                   # gira sul MacBook ora, sul PC Windows in futuro
│   ├── voice/
│   │   ├── wake_word.py          # rilevazione "hey jarvis" (openWakeWord)
│   │   ├── stt.py                  # trascrizione locale (faster-whisper)
│   │   └── tts.py                    # sintesi vocale della risposta (edge-tts)
│   ├── gestures/
│   │   └── gesture_control.py      # riconoscimento gesti (MediaPipe Hands)
│   ├── client.py                # loop principale
│   ├── requirements.txt
│   └── cred.example                # JARVIS_CORE_URL (copia in `cred`, non versionato)
└── docs/
    └── ROADMAP.md               # fasi future del progetto
```

## Requisiti

### `core/` (mini PC, sempre acceso)

- Python 3.11+ (usato 3.11 per compatibilità con le dipendenze)
- Una chiave API Anthropic ([console.anthropic.com](https://console.anthropic.com))
- `pip install -r core/requirements.txt`

### `client/` (MacBook per ora, PC Windows in futuro)

- Python 3.11 (mediapipe/faster-whisper spesso non hanno ancora wheel per le versioni Python più recenti: su questo Mac, che ha di serie Python 3.14, va usato `python3.11` esplicitamente, es. `brew install python@3.11`)
- Un microfono e una webcam
- [ffmpeg](https://ffmpeg.org/) nel `PATH` (usato per riprodurre la voce sintetizzata):
  ```bash
  brew install ffmpeg   # macOS, già presente su questo Mac
  ```
- `pip install -r client/requirements.txt`
- Su macOS: la prima volta che parte, il sistema chiederà il permesso di accesso a **microfono** e **fotocamera** per il Terminale/l'app che lancia lo script (Impostazioni di Sistema → Privacy e sicurezza)

## Configurazione delle credenziali

Come negli altri progetti, le credenziali non sono scritte nel codice ma lette da variabili d'ambiente in un file `cred` locale (escluso da git).

**`core/cred`** (formato `KEY=VALUE`, letto anche da systemd come `EnvironmentFile`):
```bash
cp core/cred.example core/cred
# poi modifica core/cred con la tua chiave
```
```
ANTHROPIC_API_KEY=la_tua_chiave_anthropic
JARVIS_MODEL=claude-sonnet-5
```

Per caricarlo manualmente in bash (senza systemd):
```bash
set -o allexport && source core/cred && set +o allexport
```

**`client/cred`** (formato bash, va sourced):
```bash
cp client/cred.example client/cred
# poi modifica client/cred con l'IP del mini PC
```
```bash
export JARVIS_CORE_URL="ws://<ip-minipc>:8080/ws"
```

## Installazione e avvio

### Core (mini PC)

```bash
cd core
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp cred.example cred   # poi modifica cred con la tua chiave Anthropic
set -o allexport && source cred && set +o allexport
python main.py
```

Il server parte su `http://<ip-minipc>:8080` (dashboard `/`, health-check `/health`, WebSocket `/ws`).

Per farlo girare come servizio sempre attivo (systemd `--user`, stesso pattern usato in `ocr-bot/minipc`):
```bash
mkdir -p ~/.config/systemd/user
cp jarvis-core.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now jarvis-core.service
loginctl enable-linger $USER   # resta attivo anche senza sessione loggata
```

### Client (MacBook)

```bash
cd client
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp cred.example cred   # poi modifica cred con l'IP del mini PC
source cred
python client.py
```

Al primo avvio openWakeWord e il riconoscimento gesti scaricano in automatico i rispettivi modelli pre-addestrati (serve internet una volta sola, ~8MB per i gesti). Di' **"hey jarvis"**, aspetta il messaggio "ti ascolto...", poi fai la tua domanda. In parallelo si apre la finestra della webcam con il riconoscimento gesti (premi `q` per chiuderla).

Su macOS, al primo avvio va concesso il permesso Fotocamera all'app che ospita il terminale (es. Terminal/iTerm/VS Code) in **Impostazioni di Sistema → Privacy e sicurezza → Fotocamera**, altrimenti OpenCV non riesce ad aprire la webcam.

> Se hai un iPhone vicino e sbloccato con Continuity Camera attiva, macOS potrebbe usare quello al posto della webcam integrata del Mac. Se succede, allontana/blocca l'iPhone e rilancia lo script: `client/gestures/gesture_control.py` apre semplicemente l'indice `0`, che macOS assegna dinamicamente a qualsiasi fotocamera consideri "primaria" in quel momento.

## Gesti riconosciuti (v1)

Il riconoscimento usa il `GestureRecognizer` della [Tasks API di MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer) (il modello pre-addestrato di Google, scaricato in automatico in `client/gestures/gesture_recognizer.task`, non versionato): niente da addestrare per i gesti statici.

| Gesto | Azione |
|---|---|
| Pollice su (`Thumb_Up`) | Accende la luce (`HA_LIGHT_ENTITY_ID`, via Home Assistant) |
| Pugno chiuso (`Closed_Fist`) | Spegne la luce (`HA_LIGHT_ENTITY_ID`, via Home Assistant) |
| Mano aperta (`Open_Palm`) | Loggato, non ancora collegato ad un'azione |
| Pollice giù (`Thumb_Down`) | Loggato, non ancora collegato ad un'azione |
| Swipe orizzontale della mano (calcolato dalla posizione del polso, non dal modello) | Loggato, non ancora collegato ad un'azione |

Verificato dal vivo con la webcam del MacBook: pollice su/giù accende/spegne davvero la luce configurata in Home Assistant (vedi `client/home_assistant.py`).

## Integrazione Home Assistant

`client/home_assistant.py` parla con l'API REST di Home Assistant (`turn_on_light` / `turn_off_light` / `toggle_light`, tramite `POST /api/services/light/...`). Configurazione in `client/cred`:

```bash
export HA_URL="https://il-tuo-homeassistant.example"
export HA_TOKEN="il_tuo_long_lived_access_token"   # Profilo utente HA → Long-Lived Access Tokens
export HA_LIGHT_ENTITY_ID="light.nome_entita"
```

Questa parte **non richiede la chiave Anthropic**: funziona in modo completamente indipendente dal `core`/Claude, quindi è testabile anche senza aver configurato il cervello.

## Tool disponibili a Claude (v1)

Definiti in `core/tools.py`, pensati come scaffold da estendere:

- `get_current_time` — data/ora attuale
- `get_system_status` — CPU/RAM/disco del mini PC

## Roadmap

Le fasi future del progetto (migrazione del client sul PC Windows, integrazione Home Assistant, controllo luci "a puntamento" con i gesti) sono descritte in [`docs/ROADMAP.md`](docs/ROADMAP.md).

## File generati (non versionati)

Esclusi da git tramite `.gitignore`, perché sono credenziali/dati locali o ambienti virtuali:

- `core/cred`, `client/cred` — le tue credenziali
- `core/venv/`, `client/venv/` — i virtualenv Python
- `__pycache__/` — cache di Python
