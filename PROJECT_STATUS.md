# Aliya Chat — Project Status

## What This Is

A standalone chat application that brings the game character **Aliya** (from 彼方的她-Aliya) to life. She's a young woman engineer on a stranded spaceship, talking to you across 1000 years of time.

Instead of scripted game dialogue, Aliya is powered by an LLM (via OpenAI-compatible API at yunwu.ai). She has her own personality, speech patterns, and memory — all locally stored.

## Current Status: Working MVP

The app runs. You can chat with Aliya. She replies one sentence at a time with human-like delays. Conversations are saved in SQLite. The UI is dark-themed to match the game.

## Tech Stack

- **Python 3** + **CustomTkinter** — dark chat UI
- **OpenAI SDK** — connected to yunwu.ai proxy (supports GPT-4o, Claude, etc.)
- **SQLite** — local conversation storage with auto-summarization
- **Threading + Queue** — non-blocking API calls from tkinter mainloop

## Project Structure

```
Aliya personality/
├── .env                          # API key + base URL + model names
├── .gitignore
├── aliya_system_prompt.txt       # Aliya's personality (system prompt)
├── ALIYA_SYSTEM_PROMPT.md        # Detailed character breakdown
├── ALIYA_EXAMPLE_DIALOGUES.md    # 7 dialogue patterns with examples
├── ALIYA_KNOWLEDGE_MAP.md        # World knowledge & emotional anchors
├── aliya_dialogue_db.json        # All 3,378 game dialogue lines (raw)
├── PROJECT_STATUS.md             # This file
├── aliya_chat/                   # The app
│   ├── main.py                   # Entry point
│   ├── config.py                 # Settings (env vars, colors, thresholds)
│   ├── ui.py                     # CustomTkinter chat window
│   ├── chat_engine.py            # LLM streaming + sentence delivery
│   ├── timing.py                 # Human-like typing delay calculator
│   ├── memory.py                 # SQLite storage + auto-summarization
│   └── assets/portraits/         # 170 character images extracted from game
└── extract_portraits.py          # Script used to extract game assets
```

## How to Run

```bash
cd "Desktop/Aliya personality/aliya_chat"
pip install customtkinter pillow openai python-dotenv
python main.py
```

## Current Models

- **Chat**: gpt-4o (via yunwu.ai/v1)
- **Summarization**: gpt-4o-mini (cheaper, used for memory compression)

## Known Working Features

- Chat with Aliya via text input
- She responds one sentence at a time with typing delays
- Input locked while she's responding
- Conversations saved in SQLite (survives restart)
- Auto-summarization after 15K+ characters to control costs
- Dark theme matching game aesthetic
- Character portrait in header (A_00.png)
- "Ship Time" clock in header

## Known Issues

- None critical at the moment (all 5 initial bugs fixed)

## Future Roadmap

### 1. Random Event Module
Aliya should be able to message you unprompted. Random events like:
- "I found something weird in the air ducts!"
- "The stars look amazing right now..."
- "Something's making noise in the engine room..."

Implementation idea: background timer that occasionally triggers Aliya to send a message based on random story prompts. User doesn't initiate — Aliya does.

### 2. Rest Module
Aliya is a living character. She needs to:
- Sleep (replies become slow/delayed, eventually says goodnight)
- Use the bathroom (brief absences)
- Eat meals
- Have energy levels that affect her response style

Her status should be visible somewhere in the UI.

### 3. Heart Rate Module
Real-time heart rate display that updates every second:
- Normal: ~75 BPM
- Excited/scared: ~110-130 BPM
- During danger events: ~150+ BPM
- Sleeping: ~55 BPM

Needs a small HUD widget with animated pulse indicator. Heart rate should correlate with the emotional content of the conversation.

### 4. Chat History & Lazy Loading
Currently loads last 100 messages on startup. Should work like WeChat:
- On open, show recent messages
- Scroll up to load older messages (lazy load in batches of 50)
- Visual indicator when loading older history
- Preserve scroll position after loading

### 5. Response Length Variation
Current issue: Aliya always replies with 7-8 sentences per message. Too much.
Should vary based on context:
- Simple acknowledgment: 1-2 messages ("Got it!", "Alright~")
- Emotional moment: 3-5 messages
- Story/explanation: 5-8 messages
- One-word reply sometimes: just "Yes" or "No..."

Implementation: add a "response density" hint to the system prompt, or let the LLM decide based on the conversation context. The sentence splitter is fine — the issue is the LLM generates too many sentences per response.

### 6. Image Generation Module
Aliya should be able to send photos:
- Looking out at space from the ship window
- Daily life scenes (eating, working in engine room)
- Selfies with different expressions
- Things she "found" during random events

Implementation:
- LLM generates a detailed image prompt based on the conversation context
- Call an image generation API (DALL-E, Stable Diffusion, Midjourney, etc.)
- Display the generated image in the chat as a photo bubble
- Could also use pre-generated images from the game assets for common scenes

## API Configuration

The app uses an OpenAI-compatible proxy (yunwu.ai). Config in `.env`:
```
API_KEY=sk-...
BASE_URL=https://yunwu.ai/v1
CHAT_MODEL=gpt-4o
SUMMARY_MODEL=gpt-4o-mini
```

To switch providers, just change the `.env` values. The code uses standard OpenAI SDK format.

## Character Data

- **1,775 Aliya messages** and **1,603 player choices** extracted from the game
- **170 character portraits** extracted from Unity assets
- System prompt distilled from all game dialogue into a single personality file
- Character speaks English with Chinese translations in parentheses for hard words
- Player name: Nolan (configurable in system prompt)
