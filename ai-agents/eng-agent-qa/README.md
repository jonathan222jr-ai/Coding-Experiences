# Engineering Agent System

An AI-powered multi-agent system that takes a natural-language prompt and delivers
industry-standard, reviewed, and debugged code — packaged as a zip — alongside a
professional report authored by Google Gemini.

## How It Works

1. **You type a goal** into the prompt box (e.g. "Build a FastAPI JWT auth service")
2. **The Orchestrator** plans the best sequence of specialized sub-agents
3. **Code-producing agents** (code_gen, scaffolder) run and generate output
4. **Automatic QA pipeline** — every code generation step is *automatically* followed by:
   - 🔍 **Code Review Agent** — audits for correctness, security, performance
   - 🐛 **Debugger Agent** — fixes issues flagged by the reviewer, provides diffs
5. **A zip file** of the generated project is created and made available for download
6. **A professional report** is written by Google Gemini summarizing the entire run

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in your ANTHROPIC_API_KEY and GEMINI_API_KEY
python app.py
# → http://localhost:5001
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | Powers all engineering sub-agents |
| `GEMINI_API_KEY` | Optional | Powers professional Gemini report narratives (falls back to template if absent) |

## Agents

| Agent | Role |
|-------|------|
| `code_gen` | Writes production-grade Python/FastAPI/SQLAlchemy code |
| `code_review` | Reviews for bugs, security, performance (auto-runs after code_gen) |
| `debugger` | Fixes issues from review, produces diffs (auto-runs after code_gen) |
| `scaffolder` | Generates a full project zip from a description |
| `researcher` | Researches tech topics, produces specs |
| `optimizer` | Performance profiling and architecture advice |
| `documenter` | Generates README, API docs, runbooks |
| `requirements` | Analyzes and clarifies stakeholder requirements |

## Outputs

- **Zip files** → `output/` directory, downloadable from the UI
- **Reports** → `reports/` directory (Markdown, Gemini-authored narrative)
