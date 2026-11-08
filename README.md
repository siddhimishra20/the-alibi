# 🔍 THE ALIBI
> **A Satirical Noir Micro-Crime Interrogation Game with Local LLM Multi-Agent Architecture**

[![100% Local LLM](https://img.shields.io/badge/Local_LLM-Ollama_Llama3.1-blue.svg)](http://localhost:11434)
[![Embeddings](https://img.shields.io/badge/Embeddings-nomic--embed--text-purple.svg)](https://ollama.com/library/nomic-embed-text)
[![Terminal UI](https://img.shields.io/badge/Terminal_UI-Textual_8.2-green.svg)](https://textual.textualize.io/)
[![Web App](https://img.shields.io/badge/Web_UI-FastAPI_CRT_Noir-cyan.svg)](http://localhost:8000)
[![Vector Store](https://img.shields.io/badge/Vector_Store-ChromaDB-orange.svg)](https://www.trychroma.com/)
[![Docker Ready](https://img.shields.io/badge/Docker-compose_ready-blue.svg)](docker-compose.yml)
[![Tests](https://img.shields.io/badge/Tests-26_Passed-brightgreen.svg)](tests/)

---

## 🎩 Executive Summary & Presentation Pitch

**THE ALIBI** is a daily detective interrogation game in the spirit of *Wordle meets Papers, Please* with a hardboiled 1940s noir satirical aesthetic. 

Every day, an absurd micro-crime occurs in the city (e.g. *"The museum's ancient Roman golden spoon was swapped with a neon yellow plastic spork"*). Sitting across from you in the interrogation room is an eccentric, guilty suspect with a compulsive speech quirk, a planned cover story, and hidden vulnerabilities.

- **You have limited QUESTION TOKENS** per case (3 to 7 depending on chosen difficulty).
- **You hold a DOSSIER of 3 VERIFIED FACTS** (immutable forensic truths).
- **Your goal**: Ask strategic questions to press the suspect's alibi, detect where their statements contradict the physical evidence or their own prior testimony, press **ACCUSE** (`A`), and convict them!
- When you accuse, the **Contradiction Judge** evaluates whether your catch is logically airtight.
- Complete the case, share your spoiler-free Wordle-style investigation grid, and return tomorrow for a completely unique daily case!

Playable as both a **full-screen retro Terminal TUI** and a **browser-based Retro CRT Web Application** with Web Audio sound synthesis.

---

## 🌟 Key Features & Capabilities

- 🤖 **100% Offline Local Multi-Agent Architecture**: 5 specialized local LLM agents powered by Ollama (`llama3.1:latest` & `nomic-embed-text`) with **zero cloud dependencies** and **zero API costs**.
- ⚡ **Sub-6-Second Ultra-Low Latency**: Optimized agent waterfall reducing questioning and accusation response times from **~2.5 minutes down to 4–6 seconds**.
- 🌐 **Dual Gameplay Interfaces**:
  - **Retro Noir Terminal UI (Textual 8.2)**: Looped 6-frame noir pixel art animation (rainy alley, glowing street lamp, puffing cigarette detective, flickering neon sign), 16-bit sound effects, live countdown timer, retro thinking spinner (`┌ ● · ┐`), and bold FIGlet ASCII verdict banners.
  - **Retro CRT Web App (FastAPI)**: Green phosphor CRT scanline styling, procedural Web Audio sound synthesizer, interactive quote selection, and spoiler-stripped REST API.
- 💾 **Mid-Game Auto-Save & Resumption**: Auto-saves after every single question, hint, or penalty. Closing the terminal or browser allows you to resume your exact remaining tokens and question transcript anytime.
- 🛡️ **Zero-Repeat Memory & Rolling Pre-Generation Buffer**: Global registry tracks used titles, seeds, and suspects across historical dates, guaranteeing that cases **never repeat**.
- ⏰ **Automated Weekly Background Scheduler**: Native macOS Launchd daemon (`com.thealibi.pregenerator`) and cron job integration that automatically generates a 14-day rolling buffer of future cases every Monday at 00:00.
- 🎯 **3 Distinct Difficulty Modes**:
  - **Classic**: 5 tokens, 1 hint, 1-token accusation penalty.
  - **Hardboiled**: 3 tokens, 0 hints allowed, 2-token penalty.
  - **Rookie**: 7 tokens, multi-hints, forgiving penalty.
- 🐳 **Docker Containerization**: Instant container deployment via Docker Compose with host Ollama gateway networking.
- 🧪 **Comprehensive 27-Test Suite**: Unit, integration, RAG, and full UI pilot tests passing in under 40 seconds.

---

## 🏛️ LLM Multi-Agent System Architecture

```
                                  ┌───────────────────────────────┐
                                  │       PLAYER DETECTIVE        │
                                  │   (Terminal TUI / Web App)    │
                                  └───────────────┬───────────────┘
                                                  │
                 ┌────────────────────────────────┴───────────────────────────────┐
                 │                                                                │
                 ▼                                                                ▼
   [ Question: Costs 1 Token ]                                          [ Accuse: Press 'A' ]
                 │                                                                │
                 ▼                                                                ▼
   ┌───────────────────────────┐                                    ┌───────────────────────────┐
   │         AGENT 2           │                                    │         AGENT 4           │
   │       SUSPECT AGENT       │                                    │    CONTRADICTION JUDGE    │
   │  (Guilty, Speech Quirk,   │                                    │  (Deterministic Fast-Path │
   │   Hidden-State Reasoning) │                                    │   + Chain of Verification)│
   └─────────────┬─────────────┘                                    └─────────────┬─────────────┘
                 │                                                                │
        Deterministic Lie Plan                                            Judgement Ruling
         & Weak-Point Matching                                            (VALID or INVALID)
                 │                                                                │
                 ├──────────────────────────────┐                                 ▼
                 ▼                              ▼                       ┌───────────────────┐
      ┌────────────────────┐         ┌────────────────────┐             │ Suspect Breakdown │
      │ plan_lie(question) │         │ lookup_*(topic)    │             │ (Dramatic Noir    │
      └────────────────────┘         └──────────┬─────────┘             │  Confession)      │
                                                │                       └───────────────────┘
                                                ▼
                               ┌─────────────────────────────────┐
                               │            RAG LAYER            │
                               │  ChromaDB (3 Collections):      │
                               │   1. dossier_facts              │
                               │   2. truth_timeline             │
                               │   3. suspect_statements         │
                               │  Embedding: nomic-embed-text    │
                               │  Reranker: Keyword Overlap      │
                               └────────────────┬────────────────┘
                                                ▲
                                                │ Indexes Atomic Claims
                                                │
                                 ┌──────────────┴──────────────┐
                                 │           AGENT 3           │
                                 │       CLAIM EXTRACTOR       │
                                 │  (High-Speed Propositional  │
                                 │   Linguistic Decomposition) │
                                 └─────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════════════════════
 [ MONDAY 00:00 AUTOMATED BUFFER ]                                    [ OPTIONAL NOIR ASSIST ]
   ┌───────────────────────────┐                                        ┌────────────────────┐
   │         AGENT 1           │                                        │      AGENT 5       │
   │       CASE ARCHITECT      │                                        │   NARRATOR / HINT  │
   │ (Deterministic Daily Case,│                                        │ (Cryptic clue: -1  │
   │  Solvability Validation)  │                                        │  token, max 1/case)│
   └───────────────────────────┘                                        └────────────────────┘
```

---

## 🤖 The 5 Specialized Agents

| Agent | Role | Model / Technique | Core Responsibility |
| :--- | :--- | :--- | :--- |
| **Agent 1: Case Architect** | Procedural Mystery Generator | `llama3.1` (temp 0.75) + Pydantic Schema Validator | Deterministically generates daily cases seeded by date. Ensures 3 immutable facts, a hidden timeline, 3–5 exploitable weak points, and verified solvability. |
| **Agent 2: Suspect** | Eccentric Guilty Interrogee | `llama3.1` (temp 0.7) with `num_predict: 120` | Roleplays eccentric suspect with unique speech quirks. Tracks token pressure, executes lie-planning tools, and generates slips when pressed on weak points. |
| **Agent 3: Claim Extractor** | Forensic Proposition Parser | Ultra-fast heuristic linguistic engine + fallback JSON parser | Deconstructs suspect sentences into atomic claims (`subject`, `predicate`, `time`, `place`, `object`) in 0.0001s and commits them to ChromaDB. |
| **Agent 4: Contradiction Judge** | Impartial Logic Arbiter | Deterministic pre-match + `llama3.1` Chain of Verification (temp 0.1) | Evaluates player accusations. Restates claims neutrally, checks mutual logical incompatibility, and delivers dramatic confession breakdown upon valid catches. |
| **Agent 5: Noir Narrator** | Atmosphere & Clue Master | `llama3.1` (temp 0.7) with `num_predict: 75` | Delivers gritty 1940s noir case introductions and generates cryptic hints nudging toward unexposed weak points without spoiling the answer. |

---

## ⚡ Performance & Optimization Benchmarks

In earlier builds, sequential LLM waterfalls (deliberation call + generation call + claim parsing + dual self-consistency judge passes) caused question responses to take **2 to 3 minutes**. 

Through rigorous profiling and architectural refactoring, latency was reduced by **over 95%**:

| Operation | Before Optimization | After Optimization | Latency Reduction |
| :--- | :--- | :--- | :--- |
| **Suspect Turn Response** | ~100s (2 sequential unbounded calls) | **6.5s – 6.8s** (deterministic lie planning + `num_predict: 120`) | **~93% faster** |
| **Claim Extraction** | ~40s (unbounded JSON generation) | **0.0001s** (linguistic clause decomposition) | **99.9% faster** |
| **Accusation Ruling** | ~145s (dual self-consistency + confession) | **4.6s** (fast deterministic pre-check + single-pass judge) | **~96% faster** |
| **Full Pytest Suite** | 71.0s | **36.8s** (26 tests passing) | **~48% faster** |

---

## 🎮 Game Controls & Keyboard Shortcuts

### Terminal TUI Shortcuts

| Key | Action | Description |
| :--- | :--- | :--- |
| **Enter** | Submit Question / Advance | Submits current question to suspect (-1 token) or advances briefing. |
| **A** or `/accuse` | Accuse | Opens accusation modal to match a suspect quote with a broken dossier fact. |
| **H** | Noir Hint | Requests a cryptic hint from the Noir Narrator (-1 token). |
| **F2** | Live Architecture Debugger | Opens real-time inspector for LLM reasoning, RAG retrievals, and latency. |
| **M** | Mute Audio | Toggles procedural music and SFX. |
| **Esc** | Back / Dismiss | Closes active modals or returns to the Title Menu. |

---

## 🎵 Dynamic Audio Architecture

Built on `pygame.mixer` (for Terminal TUI) and the **Web Audio API** (for Web Browser Mode):
- **100% Programmatic Waveform Synthesis**: If audio files are missing, `numpy` synthesizes all required 16-bit WAV assets automatically on launch.
- **Soundtrack**:
  - `title.wav`: Noir minor synth chord progression.
  - `interrogation.wav`: Tense sub-bass drone with a rhythmic mechanical ticking pulse.
  - `win.wav`: Triumphant brass fanfare sting.
  - `lose.wav`: Melancholic trombone slide sting.
- **Sound Effects**:
  - `key_click.wav`: Snappy typewriter keystroke.
  - `token_spent.wav`: Metallic token drop chime.
  - `accuse_stamp.wav`: Heavy wooden gavel impact thud.
  - `suspect_nervous.wav`: Fluttering dissonant trill triggered when suspect is rattled.

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- Python 3.11+
- [Ollama](https://ollama.com) running locally (`http://localhost:11434`)

### 2. Pull Local Models
```bash
ollama pull llama3.1:latest
ollama pull nomic-embed-text:latest
```

### 3. Clone & Install
```bash
git clone https://github.com/your-username/the-alibi.git
cd the-alibi

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Play the Game

#### Option A: Terminal TUI Mode
```bash
# Play Today's Daily Case
python run.py

# Play Unlimited Practice Cases (Preserves your daily streak)
python run.py --practice
```

#### Option B: Web Browser Mode
```bash
# Launch FastAPI Web Server on Port 8000
python run.py --web --port 8000
```
Open **`http://localhost:8000`** in any browser.

#### Option C: Docker Container
```bash
docker compose up -d
```
Access the containerized web app at **`http://localhost:8000`**.

---

## ⏰ Automated Batch Pre-Generation & Scheduler

To guarantee zero latency on case delivery and ensure every single day has a pre-verified case ready at midnight:

```bash
# Pre-generate 14 unique future cases ahead of time
python run.py --pre-generate 14

# Install macOS background launchd daemon (Runs every Monday at 00:00)
python run.py --install-launchd

# Or install Linux/macOS standard crontab job
python run.py --install-cron

# Run standing daemon process
python run.py --daemon
```

---

## 🧪 Testing & Quality Assurance

Run the comprehensive test suite covering all multi-agent components, RAG retrieval, Web APIs, and UI pilot flows:

```bash
pytest
```

```text
============================= test session starts ==============================
collected 27 items                                                             

tests/test_case_registry.py .....                                        [ 18%]
tests/test_daily_determinism.py .                                        [ 22%]
tests/test_gameplay_session.py ..                                        [ 29%]
tests/test_integration_ollama.py .                                       [ 33%]
tests/test_json_repair.py ...                                            [ 44%]
tests/test_rag_retrieval.py .                                            [ 48%]
tests/test_schema.py ....                                                [ 62%]
tests/test_token_accounting.py ...                                       [ 74%]
tests/test_ui_pilot.py ..                                                [ 81%]
tests/test_web_api.py .....                                              [100%]

============================= 27 passed in 38.79s ==============================
```

---

## 📁 Repository Structure

```
the-alibi/
├── run.py                     # Main unified CLI, Web, and Scheduler entry point
├── Dockerfile                 # Multi-stage container definition
├── docker-compose.yml         # Container orchestration with host networking
├── requirements.txt           # Python dependencies (FastAPI, Textual, ChromaDB)
├── pytest.ini                 # Pytest runner configuration
├── README.md                  # Complete architectural & presentation documentation
│
├── alibi/                     # Core application package
│   ├── server.py              # FastAPI REST backend with spoiler sanitization
│   ├── models/                # Pydantic schemas (Case, GameSession, Statement, Claims)
│   │   └── schema.py
│   ├── llm/                   # Ollama client, streaming, JSON repair & logging
│   │   └── client.py
│   ├── rag/                   # ChromaDB vector store (3 segregated collections & reranker)
│   │   └── store.py
│   ├── agents/                # The 5 specialized LLM agents
│   │   ├── case_architect.py  # Agent 1: Case generator & validation
│   │   ├── suspect.py         # Agent 2: In-character interrogee with tool-planning
│   │   ├── claim_extractor.py # Agent 3: High-speed atomic claim parser
│   │   ├── judge.py           # Agent 4: Chain-of-verification contradiction judge
│   │   └── narrator.py        # Agent 5: Atmospheric noir narrator & hints
│   ├── game/                  # Game state, token ledger, and persistence
│   │   ├── session.py         # Mid-game state persistence & resumption engine
│   │   └── registry.py        # Zero-repeat global case registry
│   ├── audio/                 # Procedural audio engine
│   │   ├── manager.py         # Soundtrack & SFX manager
│   │   └── synthesizer.py     # NumPy 16-bit waveform synthesizer
│   └── ui/                    # Textual 8.2 CRT Terminal Interface
│       ├── app.py             # App screens, themes, layouts & handlers
│       ├── ascii_art.py       # ASCII banners, emotion faces, FIGlet headers
│       ├── debug_panel.py     # F2 Real-Time Agent Architecture Inspector
│       └── accuse_modal.py    # Contradiction selection modal
│
├── web/                       # Web application frontend
│   └── static/
│       ├── index.html         # Retro CRT terminal markup
│       ├── style.css          # Green/Amber phosphor scanlines styling
│       └── app.js             # Web Audio API sound synthesis & game logic
│
├── cases/                     # Cached pre-generated daily case files (YYYY-MM-DD.json)
├── data/                      # Seeds, fallback cases, and vector database
│   ├── case_registry.json     # Global tracking registry preventing repeats
│   ├── crime_seeds.json       # Absurd crime premises
│   └── fallback_cases.json    # Verified offline backup cases
├── saves/                     # Progress, streaks, and mid-game auto-saves
│   └── progress.json
├── scripts/                   # Automated scheduling helpers
│   └── scheduler.py           # Background buffer generation loop
└── tests/                     # 26 automated unit, integration, and UI tests
```

---

## ⚖️ License
Released under the MIT License. Built with ❤️ for local AI experimentation and hardboiled noir enthusiasts.
