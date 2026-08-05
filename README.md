# Coding Portfolio — Jonathan Ramirez

Personal projects and university coursework: multi-agent AI systems, full-stack web
applications, Outlook add-ins, game development, GPU and parallel computing, and
compilers.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat&logo=pytorch&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white)
![C++](https://img.shields.io/badge/C%2B%2B-00599C?style=flat&logo=cplusplus&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white)
![CUDA](https://img.shields.io/badge/CUDA-76B900?style=flat&logo=nvidia&logoColor=white)
![Godot](https://img.shields.io/badge/Godot-478CBF?style=flat&logo=godotengine&logoColor=white)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Start here

If you only look at three things:

| Project | Why |
|---|---|
| **[Chronicler](ai-agents/chronicler-dnd-agent)** | Nine cooperating agents maintaining a consistent D&D world, including a contradiction checker that catches conflicts before they're committed to state |
| **[Multiplayer Blackjack](web-apps/blackjack-multiplayer)** | Full-stack real-time game — FastAPI + Socket.IO backend, vanilla JS front end, synchronized play across clients |
| **[ML-PGO Research](research/ml-pgo)** | Undergraduate research using an LLM agent to read GPU memory profiles and propose optimizations |

---

## Contents

- [AI Agents](#ai-agents-ai-agents) · [Web Applications](#web-applications-web-apps) ·
  [Outlook Add-ins](#outlook-add-ins-office-addins) · [Security Tools](#security-tools-security-tools)
- [Games](#games-games) · [D&D Tools](#dd-tools-dnd-tools) · [Research](#research-research)
- [Coursework](#coursework-coursework)

---

## Personal Projects

### AI Agents (`ai-agents/`)

Python multi-agent frameworks built on the Anthropic API, several with Flask web UIs and
persistent SQLite memory.

| Project | Description |
|---|---|
| [`chronicler-dnd-agent`](ai-agents/chronicler-dnd-agent) | **Chronicler** — a D&D campaign intelligence system. A DM seed prompt becomes a full world; session notes are ingested and their consequences propagate across every NPC, faction, and plot thread. Nine domain agents (`WorldBuilder`, `SessionIngestion`, `Contradiction`, `NPC`, `LoreKeeper`, `Map`, `PlotWeaver`, `Faction`, `Rules`) over a SQLite world state, with model routing across Claude, GPT-4o, and Gemini, and a Flask UI with a map, lore browser, and encounter builder. |
| [`eng-agent`](ai-agents/eng-agent) | Engineering agent system targeting a Python data platform (FastAPI, PostgreSQL, Delta Lake, Dagster, ClickHouse). Nine stack-specific agents over a shared `BaseAgent`, a SQLite memory store, a scaffolder that emits projects as zip files, and a self-improvement loop that runs every 10 tasks. |
| [`eng-agent-qa`](ai-agents/eng-agent-qa) | A later take on the same system, built around automatic quality gates: every code-generation step is followed by a review agent and then a debugger agent that fixes what the review flags. Adds a `ReportPackager` that turns a finished run report into a runnable zip. |
| [`ai-agent-v2`](ai-agents/ai-agent-v2) | Multi-agent system with a dispatching classifier and specialized agents — `coder`, `debugger`, `fullstack`, `behavioral`, `js_explainer`, `reflector` — plus an `agent_builder` for composing new ones. |
| [`interview-agent`](ai-agents/interview-agent) | Interview-preparation assistant with a web UI and a voice mode, offering CLI, server, and continuous-listen entry points. |

### Web Applications (`web-apps/`)

| Project | Stack | Description |
|---|---|---|
| [`blackjack-multiplayer`](web-apps/blackjack-multiplayer) | FastAPI, Socket.IO, SQLAlchemy | Real-time multiplayer Blackjack. REST handles the game lifecycle; turn-by-turn play runs over Socket.IO so every client sees the same table state. |
| [`live-chat-hub`](web-apps/live-chat-hub) | Flask, Socket.IO, SQLAlchemy | Multi-user chat with registration and login. Passwords stored as scrypt hashes. |
| [`calculator-app`](web-apps/calculator-app) | React | Calculator built on Create React App. |
| [`ai-training-tracker`](web-apps/ai-training-tracker) | Vanilla HTML/JS | Self-contained single-file workout tracker with local persistence. |

### Outlook Add-ins (`office-addins/`)

| Project | Description |
|---|---|
| [`fraud-email-scanner`](office-addins/fraud-email-scanner) | TypeScript Outlook add-in that flags suspicious email. Layered design: `featureExtractor` pulls signals from a message, `ruleEngine` evaluates them, and `riskScorer` produces a score surfaced in the task pane. |
| [`my-office-add-in`](office-addins/my-office-add-in) | The scaffold the scanner grew out of. |

### Security Tools (`security-tools/`)

| Project | Description |
|---|---|
| [`email-scanner-python`](security-tools/email-scanner-python) | The fraud-scanner engine reimplemented in Python with unit tests — same extractor / rule-engine / risk-scorer layering as the TypeScript add-in. |

### Games (`games/`)

| Project | Description |
|---|---|
| [`learn-to-fly`](games/learn-to-fly) | Godot 4 penguin-launcher with an upgrade shop, inspired by the classic *Learn to Fly*. GDScript across `Penguin`, `Main`, `Shop`, and `GameData`. |
| [`godot-prototypes`](games/godot-prototypes) | Smaller Godot 4 movement and scene experiments that preceded the finished game. |

### D&D Tools (`dnd-tools/`)

| Project | Description |
|---|---|
| [`greek_npc_roller.html`](dnd-tools/greek_npc_roller.html) | Self-contained browser NPC generator for a Greek-myth setting — no build step or dependencies. |
| [`elemental_cataclysm_generator.py`](dnd-tools/elemental_cataclysm_generator.py) | Blender script that procedurally builds an elemental 5e creature with generated shader materials. |

### Research (`research/`)

| Project | Description |
|---|---|
| [`ml-pgo`](research/ml-pgo) | Undergraduate research on LLM-guided profile-guided optimization: an agent that reads GPU memory-profiler output and proposes optimizations, with a persistent memory store, token accounting, a batch experiment runner, and three chained agent skills. |

---

## Coursework (`coursework/`)

| Area | Contents |
|---|---|
| [`machine-learning`](coursework/machine-learning) | CSE 190 deep learning in PyTorch — implicit neural fields, semantic segmentation, linear and Flash attention, graph neural networks, and Stable Diffusion. |
| [`parallel-computing`](coursework/parallel-computing) | Ten labs in C/C++ — OpenMP, Pthreads, MPI (point-to-point, collectives, parallel I/O), and CUDA. |
| [`compilers`](coursework/compilers) | Scanners and LL(1) parsers in C++, plus a parser and AST-walking interpreter with its own IR and lowering pass for the *gee* language in Python. |
| [`data-structures-cpp`](coursework/data-structures-cpp) | CSE 100 — binary search trees and related structures in C++, built with Makefiles. |
| [`web-dev`](coursework/web-dev) | CSE 108 — HTML/CSS/JS front ends against Flask back ends, working up to a database-backed app. |

`misc/` holds intermediate snippets, a Jupyter tutorial notebook, and a GDScript
reference sheet.

---

## Running things

| Kind | Setup |
|---|---|
| Python | `pip install -r requirements.txt` |
| Node | `npm install` |
| C / C++ | `make` in the lab directory |
| Godot | Open the project's `project.godot` in Godot 4 |
| Notebooks | Written for Google Colab with a GPU runtime |

Projects that call an API read their credentials from the environment. Where a project
needs one, it ships a `.env.example` listing the variables — copy it to `.env` and fill
in your own keys.

---

## Notes

- **No secrets are committed.** Keys, local databases, dependencies, and build output are
  excluded via `.gitignore`; every project reads credentials from the environment.
- **Only my own code is published here.** Where a project builds on a third-party
  codebase — the DrGPUM profiler in `research/ml-pgo`, the LULESH benchmark in
  `coursework/parallel-computing` — that dependency is referenced rather than vendored,
  and noted in the relevant README.
- **Coursework** is published as a record of my own submitted work. Some directories
  contain instructor-supplied starter files and test fixtures; these are marked as
  vendored in `.gitattributes` and called out in [LICENSE](LICENSE).

## License

[MIT](LICENSE) — see the notice there regarding coursework and third-party material.
