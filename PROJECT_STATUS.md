# Aliya Chat — Project Status

## What This Is

A standalone chat application that brings the game character **Aliya** (from 彼方的她-Aliya) to life. She's a young woman engineer on a stranded spaceship, talking to you across 1000 years of time.

Instead of scripted game dialogue, Aliya is powered by an LLM. She has her own personality, speech patterns, daily routines, and memory — all locally stored.

## Current Status: Active Development (v2 Phase 1 Complete)

Core architecture has been rebuilt. Aliya now has state, a daily routine, random events, relationship phases, and offline catch-up. See `ALIYA_GAME_DESIGN.md` for the full design spec.

## Tech Stack

- **Python 3** + **CustomTkinter** — dark chat UI
- **OpenAI SDK** — connected to yunwu.ai proxy (currently using Claude models)
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
├── ALIYA_GAME_DESIGN.md          # Game design & development plan (v2.1)
├── PROJECT_STATUS.md             # This file
├── aliya_dialogue_db.json        # All 3,378 game dialogue lines (raw)
├── aliya_chat/                   # The app
│   ├── main.py                   # Entry point + phase check + god dice thread
│   ├── config.py                 # Settings (env vars, colors, time offset)
│   ├── ui.py                     # CustomTkinter chat window + offline messages
│   ├── chat_engine.py            # LLM streaming + state injection
│   ├── state.py                  # Aliya's dynamic state (ship time, activity, mood)
│   ├── god.py                    # God module (daily schedule, event dice, catch-up)
│   ├── timing.py                 # Human-like typing delay calculator
│   ├── memory.py                 # SQLite storage (sessions, messages, schedules, events, relationship)
│   ├── seeds.json                # 29 situation seeds for random events
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

- **Chat**: claude-sonnet-4-20250514 (via yunwu.ai/v1)
- **Summarization**: claude-haiku-4-5-20251001 (cheaper, used for memory compression)

## Architecture Overview

```
User Input ──┐
              ├──→ Prompt Builder ──→ LLM ──→ UI
Life Sim ────┘        ↑                ↑
                 State Module      Database
                 (state injection) (message persistence)
                      ↑
                 God Module
                 (daily schedule + event dice)
```

### Module Responsibilities

| Module | File | What it does |
|--------|------|-------------|
| **State** | `state.py` | Ship time (-5h), activity, mood, relationship phase, prompt block generation |
| **God** | `god.py` | Daily schedule (wake/sleep/mood/work), random event dice, offline catch-up |
| **ChatEngine** | `chat_engine.py` | LLM API calls, streaming, injects state into system prompt |
| **Memory** | `memory.py` | SQLite: sessions, messages, summaries, schedules, events, relationship |
| **UI** | `ui.py` | Chat bubbles, typing indicator, ship time display, proactive message queue |
| **Timing** | `timing.py` | Human-like typing delays and sentence splitting |
| **Config** | `config.py` | All constants, paths, colors, model names |

## Database Schema (7 tables)

| Table | Purpose |
|-------|---------|
| `sessions` | Chat sessions |
| `messages` | All conversation messages |
| `summaries` | Auto-generated conversation memory summaries |
| `daily_schedule` | God-generated daily routine per Aliya-day |
| `event_log` | Random event history |
| `relationship` | Phase tracking (1-4), turn count, active days |
| `aliya_state` | Key-value store for app lifecycle (last shutdown, etc.) |

## Key Design Decisions

1. **Time is 1:1 real time, Aliya is always 5 hours behind user** — no acceleration
2. **God module uses random functions, not LLM** — simple, cheap, deterministic
3. **User can always send messages** — they go to DB regardless of Aliya's state
4. **Aliya can NOT reply** — if sleeping/busy/low mood, message is saved but no API call
5. **System prompt has a `{{RELATIONSHIP_DESCRIPTION}}` placeholder** — replaced dynamically by state.py based on relationship phase
6. **Offline catch-up on startup** — max 5 messages, very conservative
7. **Background dice thread** — rolls every 30-90 min for random events

## Current Features (Working)

- Chat with Aliya via text input
- She responds one sentence at a time with typing delays
- Dynamic state injection (ship time, activity, mood)
- Relationship phase system (4 phases, gradual progression)
- Random event seeds (29 seeds across 4 categories)
- Daily schedule generation (wake time, sleep time, mood, work assignment)
- Aliya doesn't reply when sleeping
- Offline catch-up messages on startup
- Ship time display (-5 hours offset)
- Conversations saved in SQLite with auto-summarization
- Dark theme matching game aesthetic

## Known Issues

- Proactive messages from background dice thread appear without typing delay (they pop in instantly)
- Event context is injected as raw text — Aliya sees the seed description but doesn't have a natural way to "discover" it yet
- Relationship phase descriptions in `state.py` are English only (should match bilingual style of system prompt)
- No UI indicator that Aliya is asleep (user sends message, gets no response, no explanation)

## Development Roadmap

### Phase 1 (Done)
- [x] State system + dynamic prompt injection
- [x] God module + seed library
- [x] Offline catch-up
- [x] Sleep/wake cycle
- [x] Relationship phase system

### Phase 2 (Next)
- [ ] Proactive messages with typing delay (not instant pop-in)
- [ ] Seed context refinement — Aliya "discovers" events naturally
- [ ] Sleep state UX — subtle hint when Aliya is asleep
- [ ] Expand seed library to 50+
- [ ] Bilingual relationship descriptions (Chinese translations)

### Phase 3 (Future)
- [ ] God module upgrade to LLM-driven "narrative director" for long story arcs
- [ ] Image generation module
- [ ] Heart rate HUD widget
- [ ] Chat history lazy loading (scroll up to load older)
- [ ] Multiple sessions / conversation threads

## How to Debug

- Console prints ship time, activity, mood on startup
- `[God]` prefix on random event triggers in console
- `[Relationship]` prefix on phase advancement in console
- Database is at `aliya_chat/aliya_chat.db` — open with any SQLite browser
- Check `daily_schedule` table to see what God decided for today
- Check `event_log` table to see all triggered events
- Check `relationship` table to see phase progress

## API Configuration

The app uses an OpenAI-compatible proxy (yunwu.ai). Config in `.env`:
```
API_KEY=sk-...
BASE_URL=https://yunwu.ai/v1
CHAT_MODEL=claude-sonnet-4-20250514
SUMMARY_MODEL=claude-haiku-4-5-20251001
```

To switch providers, just change the `.env` values. The code uses standard OpenAI SDK format.

## Character Data

- **1,775 Aliya messages** and **1,603 player choices** extracted from the game
- **170 character portraits** extracted from Unity assets
- System prompt distilled from all game dialogue into a single personality file
- Character speaks English with Chinese translations in parentheses for hard words
- Player name: Nolan (configurable in system prompt)
