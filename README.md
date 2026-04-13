# NYRA v2 — Windows Voice Assistant

NYRA v2 is a Windows-first desktop voice assistant with a modern full-screen interface, real-time conversational flow, bilingual support, speech input, speech output, and a FastAPI + React architecture.

It is designed for local development on Windows and focuses on a clean user experience, voice interaction, and extensibility for desktop automation.

---

## Features

* Modern fullscreen interface with animated visual states
* English as the primary language, German as a supported secondary language
* Voice input using microphone audio streamed to the backend
* Speech-to-text using Whisper on the backend
* Speech output generated with Edge TTS and played in the browser
* WebSocket-based real-time communication between frontend and backend
* Extensible backend tool routing for launching apps, notes, and future automation
* Windows-first workflow and setup

---

## Tech Stack

### Frontend

* React
* TypeScript
* Vite
* Web Audio API
* WebSocket client

### Backend

* FastAPI
* Uvicorn
* Python 3.12
* faster-whisper
* edge-tts
* WebSockets

### AI / Model

* OpenRouter for LLM responses
* Configurable model routing

---

## Project Structure

```text
NYRA v2/
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ config.py
│  │  ├─ schemas.py
│  │  ├─ services/
│  │  │  ├─ llm.py
│  │  │  ├─ stt.py
│  │  │  └─ tts.py
│  │  └─ tools/
│  │     ├─ router.py
│  │     ├─ system_tools.py
│  │     └─ notes_tools.py
│  ├─ requirements.txt
│  └─ .env.example
├─ frontend/
│  ├─ src/
│  │  ├─ App.tsx
│  │  ├─ main.tsx
│  │  ├─ types.ts
│  │  └─ styles.css
│  ├─ package.json
│  └─ vite.config.ts
└─ README.md
```

---

## Prerequisites

Before starting, make sure you have the following installed:

* **Windows 10 or Windows 11**
* **Python 3.12**
* **Node.js 18+**
* **npm**
* A microphone
* An OpenRouter API key

Recommended:

* VS Code
* A modern Chromium-based browser such as Edge or Chrome

---

## Environment Variables

Create a `.env` file inside `backend/` based on `.env.example`.

Example:

```env
APP_NAME=NYRA v2
APP_ENV=development
ALLOWED_ORIGIN=http://localhost:5173

OPENROUTER_API_KEY=YOUR_OPENROUTER_KEY
OPENROUTER_MODEL=openrouter/free

ENABLE_TTS=true
TTS_PROVIDER=edge
EDGE_TTS_VOICE=en-US-AriaNeural

PROJECTS_DIR=projects
HF_HUB_DISABLE_SYMLINKS_WARNING=1
```

### Environment Variable Notes

* `OPENROUTER_API_KEY`: required for LLM replies
* `OPENROUTER_MODEL`: free or paid model route
* `ENABLE_TTS`: enables browser-played speech output
* `TTS_PROVIDER=edge`: uses Edge TTS generation on the backend
* `EDGE_TTS_VOICE`: choose the voice used for speech output
* `PROJECTS_DIR`: directory for generated project files and future automation artifacts

---

## Step-by-Step Setup

## 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd "NYRA v2"
```

## 2. Set up the backend

Open PowerShell and run:

```powershell
cd backend
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Then edit `backend/.env` and add your real values.

## 3. Start the backend

```powershell
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If `uvicorn` is not recognized, use:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 4. Set up the frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

## 5. Open the app

Open your browser at:

```text
http://localhost:5173
```

## 6. Allow microphone access

The first time you open the app, the browser will ask for microphone permissions.

You must allow microphone access or voice input will not work.

---

## How the App Works

### Voice Input

The frontend captures microphone audio and sends speech segments to the backend via WebSocket.

The backend:

1. receives raw audio
2. converts it to text using Whisper
3. runs tool logic if needed
4. sends the final answer back to the frontend

### Speech Output

The backend generates TTS audio using Edge TTS.
The frontend receives audio as base64 and plays it directly in the browser.

### Language Behavior

* **English** is the default mode
* **German** is also supported
* **Auto** mode can be used to follow the user’s input language

---

## Recommended Voices

You can change `EDGE_TTS_VOICE` in your `.env`.

Good options to try:

* `en-US-AriaNeural`
* `en-US-JennyNeural`
* `de-DE-KatjaNeural`
* `de-DE-SeraphinaMultilingualNeural`

---

## Running in Development

You need **two terminals** running at the same time:

### Terminal 1 — Backend

```powershell
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Terminal 2 — Frontend

```powershell
cd frontend
npm run dev
```

---

## Troubleshooting

## Microphone is not working

Check the following:

* Browser microphone permission is enabled
* The correct microphone is selected in Windows
* Another app is not exclusively blocking the microphone
* You are using Edge or Chrome for best compatibility

## I cannot hear the assistant

Check the following:

* `ENABLE_TTS=true` in `backend/.env`
* Browser audio is not muted
* Your output device is correct in Windows
* The backend is successfully generating TTS audio

## The backend says `uvicorn` is not recognized

This usually means the virtual environment is not active.

Use:

```powershell
.venv\Scripts\activate
```

or run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## The backend is slow on first voice input

This is normal when Whisper loads for the first time.
The first transcription can take longer than later ones.

## OpenRouter replies are not working

Check:

* `OPENROUTER_API_KEY` is present
* the key is valid
* the selected model route is available

---

## Security Notes

Do **not** upload secrets to GitHub.

Never commit:

* `.env`
* API keys
* local caches
* generated credentials
* private audio samples

You should commit only `.env.example`, never the real `.env`.

---

## What to Check Before Uploading to GitHub

Before pushing the repository, check all of the following carefully.

### 1. Remove secrets

Make sure your repository does **not** contain:

* OpenRouter API keys
* ElevenLabs keys if you tested them before
* personal tokens
* copied credentials from terminal history

### 2. Add a proper `.gitignore`

Your repo should ignore at least:

```gitignore
# Python
backend/.venv/
backend/__pycache__/
backend/.env
backend/.pytest_cache/

# Node
frontend/node_modules/
frontend/dist/

# OS / Editor
.vscode/
.DS_Store
Thumbs.db

# Temp / audio
*.mp3
*.wav
*.log
```

### 3. Check hardcoded paths

Avoid committing code that depends on your own machine paths such as:

* `C:\Users\yazen\...`
* your desktop folder
* your personal notes folder

Use relative paths or environment variables instead.

### 4. Test on a clean run

Before uploading, verify that someone else could start the project with only:

```powershell
cd backend
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

and:

```powershell
cd frontend
npm install
npm run dev
```

### 5. Make sure the README matches reality

Your README should match:

* the real folder structure
* real environment variables
* real commands
* the current project name

### 6. Remove broken or experimental files

If a file is outdated, broken, or no longer used, remove it before upload.
That includes:

* old App.tsx versions
* abandoned service files
* dead TTS experiments
* legacy configs

### 7. Check API usage and rate limits

If you use free model routes or free TTS routes, mention clearly in the README that:

* availability may vary
* free model quality may vary
* users may need their own API key

### 8. Add screenshots or demo GIFs

A good GitHub repo looks much stronger with:

* one clean screenshot of the UI
* one short GIF showing voice input/output
* one screenshot of the settings panel

---

## Suggested Repository Sections

If you want your GitHub repo to look polished, include these sections:

* Overview
* Features
* Tech Stack
* Setup
* Configuration
* Usage
* Troubleshooting
* Security Notes
* Roadmap
* License

---

## Roadmap

Possible next improvements:

* Better Windows app detection and launching
* Richer coding tools for project scaffolding
* File creation and project bootstrapping from natural language
* Better VAD and interruption handling
* More robust bilingual logic
* Wake-word support
* Better local system integrations

---

## License

Choose a license before publishing publicly.

Common choices:

* MIT
* Apache-2.0
* GPL-3.0

If you want the least friction for reuse, MIT is usually the simplest.

---

## Final Notes

NYRA v2 is a strong base for a Windows voice assistant project, but voice products are sensitive to environment, permissions, browser behavior, and audio device setup.

For the best first impression on GitHub:

* keep setup simple
* keep secrets out of the repo
* document known limitations honestly
* show screenshots
* make the README match the real code exactly
