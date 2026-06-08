# FRIDAY (JARVIS) — Modular AI Assistant

FRIDAY (also known as JARVIS) is a modular AI assistant that combines:
- an **LLM-based intent router** (Decision Making Model)
- **general chat** (Groq + fallbacks)
- **real-time web search + synthesis** (Tavily + fallback scraping)
- **system automation** (open/close/play/content generation)
- **voice input/output** in the web UI (Chrome/Edge Web Speech API + backend TTS)
- a **desktop GUI** (PyQt5)

The project is primarily implemented in Python with a **Flask** backend and a **TailwindCSS**-based web frontend.

---

## Features

### 1) Decision Making Model (DMM / Router)
`Backend/Model.py` classifies each user prompt into one (or more) intents such as:
- `general <query>` — answer conversationally
- `realtime <query>` — fetch fresh info and answer
- `open <app/website>` / `close <app/website>`
- `play <song>`
- `content <topic>` — generate content and open it in Notepad
- `system <task>` — volume mute/unmute/volume up/down
- `google search <topic>` / `youtube search <topic>`
- `generate image <prompt>` (declared in router; generation code exists in `Backend/ImageGeneration.py`)
- `exit` — end conversation

Cohere is attempted first, with **Groq fallback**.

### 2) Real-time Web Search
`Backend/RealtimeSearchEngine.py`:
- queries the web using **Tavily** (`TAVILY_API_KEY`)
- if Tavily fails, falls back to `googlesearch-python` scraping
- passes search results to an LLM (Groq with fallbacks like Cohere/HuggingFace)

### 3) General Chat (with Memory retrieval)
`Backend/Chatbot.py`:
- uses Groq models in sequence until one succeeds
- falls back to HuggingFace inference if Groq fails (when `HuggingFaceAPIKey` is configured)
- integrates **user memory** via `Backend/Memory/Retriever.py`
- spawns a background thread to extract new memories via `Backend/Memory/Extractor.py`

### 4) System Automation
`Backend/Automation.py` can:
- open/close applications (via `AppOpener` when available, otherwise uses Google result scraping + browser open)
- play YouTube content (via `pywhatkit` when available)
- write content using the LLM and open it in **Notepad**
- perform volume mute/unmute/volume up/volume down (via `keyboard` when available)

### 5) Web UI: Voice + Chat + Research Hub
`Frontend/templates/index.html` provides:
- voice input using **SpeechRecognition / webkitSpeechRecognition**
- chat interface
- a “Research Hub” view that renders search results and the AI summary
- TTS playback using `/api/audio`

### 6) Desktop GUI
`Frontend/GUI.py` is a PyQt5 interface that:
- displays live status text (from `Frontend/Files/Status.data`)
- displays assistant responses (from `Frontend/Files/Responses.data`)
- uses a microphone toggle stored in `Frontend/Files/Mic.data`

---

## Project Structure

```text
jarvis/
  app.py                 # Flask server + request routing
  Main.py                # launcher for the web interface
  README.md

  Backend/
    Model.py             # DMM intent router (Cohere -> Groq fallback)
    Chatbot.py           # general chat (Groq -> HuggingFace fallback)
    RealtimeSearchEngine.py # web search + synthesis (Tavily -> google fallback)
    Automation.py        # open/close/play/content/system automation
    ImageGeneration.py   # image generation logic
    SpeechToText.py      # speech-to-text (backend module)
    TextToSpeech.py      # text-to-audio generation

    env.py               # env loading helpers

    Memory/
      DB.py              # memory DB utilities
      Retriever.py       # retrieve relevant memories for a prompt
      Extractor.py       # extract memory candidates from user interaction
      Reflection.py      # periodic reflection job

  Frontend/
    templates/index.html # web UI
    GUI.py               # PyQt5 desktop UI
    Files/               # local IPC files for GUI state
    Graphics/           # UI images/icons

  Data/
    chroma_db/           # local chroma persistence (sqlite + bin files)
    *.txt/*.json        # datasets / chat log / planning content

  vercel.json, .vercelignore, .env, etc.
```

---

## How the System Works (Request Flow)

1. **Client sends a query** to the Flask backend:
   - Web UI calls `POST /api/process` with `{ "query": "..." }`.
2. `app.py` calls **FirstLayerDMM**:
   - If it returns `general`, `ChatBot` is used.
   - If it returns `realtime`, `RealtimeSearchEngine` is used.
   - If it returns automation intents (e.g., `open`, `close`, `play`, `content`, `system`), `Automation` is executed.
3. The backend optionally creates **TTS audio** for the final answer.
4. The response includes:
   - `answer`
   - `search_data` (when using realtime search)
   - `decision` (router outputs)
   - `audio_available`

---

## Supported Intent Outputs (DMM)

From `Backend/Model.py`, the router aims to output strings like:
- `general <query>`
- `realtime <query>`
- `open <app/website>`
- `close <app/website>`
- `play <song>`
- `content <topic>`
- `system <task>`
- `google search <topic>`
- `youtube search <topic>`
- `generate image <prompt>`
- `reminder <datetime message>`
- `exit`

Note: only the intents that are actually wired into `app.py` and `Automation.py` will have effects. (The router may still classify additional intents.)

---

## Setup

### 1) Requirements
- Python **3.9+**
- Google Chrome (or a Chromium-based browser) for browser voice input
- API keys for the LLM/search providers you want to enable

### 2) Install dependencies

```bash
pip install -r Requirements.txt
```

### 3) Configure environment variables (`.env`)
Create a `.env` file in the `jarvis/` folder.

The code reads these keys (at minimum):

```env
Username=YourName
Assistantname=FRIDAY

# API Keys
CohereAPIKey=your_cohere_key_here
GroqAPIKey=your_groq_key_here
HuggingFaceAPIKey=your_huggingface_key_here
TAVILY_API_KEY=your_tavily_key_here
```

Additional keys may be attempted in some fallback paths (depending on which modules run), so configuring them can improve robustness.

---

## Running the Project

### Web Interface (recommended)
Run the Flask server:

```bash
python app.py
# or
python Main.py
```

Open:
- `http://localhost:5000`

The web UI will handle:
- voice input (SpeechRecognition)
- sending queries to `/api/process`
- playing audio from `/api/audio`

### Desktop GUI (PyQt5)
```bash
python Frontend/GUI.py
```

The desktop GUI reads/writes local state via files in `Frontend/Files/`.

---

## Backend API

### `POST /api/process`
**Request body**:
```json
{ "query": "your text" }
```

**Response**:
```json
{
  "status": "success",
  "answer": "...",
  "search_data": [ ... ],
  "decision": [ ... ],
  "audio_available": true
}
```

### `GET /api/audio`
Returns the latest generated TTS audio file as `audio/mpeg` when available.

---

## Memory Subsystem

FRIDAY uses a memory pipeline to personalize responses:
- `Chatbot.py` and `RealtimeSearchEngine.py` call:
  - `Backend/Memory/Retriever.py` to fetch relevant memories
- `Chatbot.py` starts a background thread:
  - `Backend/Memory/Extractor.py` to extract new memories
- `app.py` tries to start a reflection job on startup:
  - `Backend/Memory/Reflection.py` (`start_reflection_job()`)

Memory is backed by the local `Data/chroma_db/` directory.

---

## Troubleshooting

### Voice input doesn’t work
- Ensure you’re using **Chrome/Edge**.
- Verify mic permissions.
- Some browsers restrict Web Speech features on `http://`.

### “Backend timed out” errors
- Increase backend responsiveness by ensuring API keys and network access are valid.
- Some external model calls can take longer than expected.

### Search errors / empty results
- Confirm `TAVILY_API_KEY`.
- Network restrictions may block scraping fallback.

### Automation not working
- Some automation components are optional dependencies (e.g., `AppOpener`, `pywhatkit`, `keyboard`).
- If an optional dependency is missing, automation may use fallback logic or be limited.

---

## Security & Safety Notes

- Automation can open/close apps and control system volume depending on routing decisions.
- Keep `.env` private—API keys are required for external services.
- When running locally, be cautious with prompts that ask the assistant to operate on your system.

---

## License

Copyright © 2026

This project is provided under the **MIT License** (or replace with your actual license).



