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

### Games (`games/`)

| Project | Description |
|---|---|
| [`learn-to-fly`](games/learn-to-fly) | Godot 4 penguin-launcher game with an upgrade shop, inspired by the classic *Learn to Fly*. GDScript across `Penguin`, `Main`, `Shop`, and `GameData`. |

---

## Coursework (`coursework/`)

| Area | Contents |
|---|---|
| [`data-structures-cpp`](coursework/data-structures-cpp) | C++ labs — binary search trees and related structures, built with Makefiles. |
| [`compilers`](coursework/compilers) | Scanner and LL(1) parser implementations in C++, with grammar definitions and test suites. |
| [`parallel-computing`](coursework/parallel-computing) | Shared-memory parallelism in C using OpenMP. |
| [`web-dev`](coursework/web-dev) | Full-stack labs pairing HTML/CSS/JS front ends with Flask back ends. |

`misc/` holds standalone snippets, a Jupyter tutorial notebook, and a GDScript reference sheet.

---

## Notes

- Secrets, local databases, dependencies, and build output are excluded via `.gitignore`.
  Projects that need credentials read them from a `.env` file you supply yourself.
- Python projects: `pip install -r requirements.txt`. Node projects: `npm install`.
  C/C++ labs build with `make`.
- Coursework is published as a record of my own submitted work.
