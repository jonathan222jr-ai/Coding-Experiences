# Coding Portfolio — Jonathan Ramirez

A collection of personal projects and university coursework, spanning AI agents, web
applications, Outlook add-ins, game development, and systems programming in C/C++.

---

## Personal Projects

### AI Agents (`ai-agents/`)

Python agent frameworks built on the Anthropic API.

| Project | Description |
|---|---|
| [`ai-agent-v2`](ai-agents/ai-agent-v2) | Multi-agent system with a dispatching classifier and specialized agents — `coder`, `debugger`, `fullstack`, `behavioral`, `js_explainer`, `reflector` — plus an `agent_builder` for composing new ones. Includes a Flask web UI. |
| [`eng-agent`](ai-agents/eng-agent) | Engineering agent system targeting a Python data platform (FastAPI, PostgreSQL, Delta Lake, Dagster, ClickHouse). Nine stack-specific agents over a shared `BaseAgent`, a SQLite memory store, a scaffolder that emits projects as zip files, and a self-improvement loop that runs every 10 tasks. |
| [`interview-agent`](ai-agents/interview-agent) | Interview-preparation assistant with a web UI and a voice mode, offering CLI, server, and continuous-listen entry points. |

### Web Applications (`web-apps/`)

| Project | Stack | Description |
|---|---|---|
| [`live-chat-hub`](web-apps/live-chat-hub) | Flask, SQLAlchemy | Multi-user chat with account registration and login. Passwords stored as scrypt hashes. |
| [`calculator-app`](web-apps/calculator-app) | React | Calculator built on Create React App. |
| [`ai-training-tracker`](web-apps/ai-training-tracker) | Vanilla HTML/JS | Self-contained single-file workout tracker with local persistence. |

### Outlook Add-ins (`office-addins/`)

| Project | Description |
|---|---|
| [`fraud-email-scanner`](office-addins/fraud-email-scanner) | TypeScript Outlook add-in that flags suspicious email. Layered design: `featureExtractor` pulls signals from a message, `ruleEngine` evaluates them, and `riskScorer` produces a score surfaced in the task pane. |
| [`my-office-add-in`](office-addins/my-office-add-in) | Scanner add-in scaffold in TypeScript. |

### Security Tools (`security-tools/`)

| Project | Description |
|---|---|
| [`email-scanner-python`](security-tools/email-scanner-python) | The fraud-scanner engine reimplemented in Python with unit tests — same extractor / rule-engine / risk-scorer layering as the TypeScript add-in, useful for comparing the two. |

### Games (`games/`)

| Project | Description |
|---|---|
| [`learn-to-fly`](games/learn-to-fly) | Godot 4 penguin-launcher game with an upgrade shop, inspired by the classic *Learn to Fly*. GDScript across `Penguin`, `Main`, `Shop`, and `GameData`. |
| [`godot-prototypes`](games/godot-prototypes) | Smaller Godot 4 movement and scene experiments that preceded the finished game. |

### D&D Tools (`dnd-tools/`)

| Project | Description |
|---|---|
| [`greek_npc_roller.html`](dnd-tools/greek_npc_roller.html) | Self-contained browser NPC generator for a Greek-myth D&D setting. |
| [`elemental_cataclysm_generator.py`](dnd-tools/elemental_cataclysm_generator.py) | Blender script that procedurally builds an elemental 5e creature with generated shader materials. |

### Research (`research/`)

| Project | Description |
|---|---|
| [`ml-pgo`](research/ml-pgo) | Undergraduate research on LLM-guided profile-guided optimization: an agent that reads GPU memory-profiler output and proposes optimizations, with a persistent memory store, token accounting, and a batch experiment runner. |

---

## Coursework (`coursework/`)

| Area | Contents |
|---|---|
| [`data-structures-cpp`](coursework/data-structures-cpp) | C++ labs — binary search trees and related structures, built with Makefiles. |
| [`compilers`](coursework/compilers) | Scanner and LL(1) parser implementations in C++, with grammar definitions and test suites. Also includes a parser (`gee-parser`) and an AST-walking interpreter with its own IR and lowering pass (`gee-interpreter`) for the *gee* language, both in Python. |
| [`machine-learning`](coursework/machine-learning) | CSE 190 deep-learning labs in PyTorch — implicit neural fields, semantic segmentation, linear/Flash attention, graph neural networks, and Stable Diffusion. |
| [`parallel-computing`](coursework/parallel-computing) | Ten labs in C/C++ covering OpenMP, Pthreads, MPI (point-to-point, collectives, parallel I/O), and CUDA. |
| [`web-dev`](coursework/web-dev) | Full-stack labs pairing HTML/CSS/JS front ends with Flask back ends. |

`misc/` holds standalone snippets, a Jupyter tutorial notebook, and a GDScript reference sheet.

---

## Notes

- Secrets, local databases, dependencies, and build output are excluded via `.gitignore`.
  Projects that need credentials read them from a `.env` file you supply yourself.
- Python projects: `pip install -r requirements.txt`. Node projects: `npm install`.
  C/C++ labs build with `make`.
- Coursework is published as a record of my own submitted work.
- Only my own code is published here. Where a project builds on a third-party codebase —
  the DrGPUM profiler in `research/ml-pgo`, the LULESH benchmark in
  `coursework/parallel-computing` — that dependency is referenced rather than vendored,
  and is noted in the relevant README.
