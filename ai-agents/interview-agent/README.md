# Interview Prep Agent

A multi-agent practice tool for technical interview preparation. Ask it a practice
question by voice or text and it routes the question to a specialist agent, returning
a structured model answer to study and critique.

Built to drill fullstack and JavaScript/TypeScript fundamentals, behavioral storytelling,
and debugging technique.

---

## Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Add your API key
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# 3. Run
python3 main.py serve          # web UI at http://localhost:5000
python3 main.py ask "Explain closures in JavaScript"
python3 main.py listen         # voice input
```

---

## Voice Input

```bash
pip install sounddevice soundfile openai-whisper numpy

python3 main.py listen                # record once → answer
python3 main.py listen --loop         # continuous practice session
python3 main.py listen --file q.wav   # transcribe an existing recording
```

Whisper runs fully offline, so transcription needs no API key.

---

## Architecture

A classifier tags each question, then the orchestrator dispatches it to the matching
specialist in a two-wave parallel routing pass — a fast coaching cue returns immediately
while the fuller answer is still generating.

| Agent | Model | Purpose |
|---|---|---|
| `ClassifierAgent` | Haiku | Detects question type and urgency |
| `SpeedTipAgent` | Haiku | One-line coaching cue, fires in parallel |
| `BehavioralAgent` | Sonnet | STAR-format answer structuring |
| `CoderAgent` | Sonnet | TypeScript solutions, Big-O, edge cases |
| `JSExplainerAgent` | Sonnet | Event loop, closures, Promises, hooks, TS |
| `DebuggerAgent` | Sonnet | Root-cause analysis and corrected code |
| `FullstackAgent` | Sonnet | System design, APIs, React/Node architecture |
| `MotivationAgent` | Sonnet | Framing motivation and interest answers |

### Practice Areas

- **Fullstack fundamentals** → `FullstackAgent`
- **JS/TS proficiency** → `JSExplainerAgent`, `CoderAgent`
- **Problem solving and debugging** → `CoderAgent`, `DebuggerAgent`
- **Ownership and learning velocity** → `BehavioralAgent`, `MotivationAgent`

---

## Self-Improvement Loop

Every 20 questions, `loops/improvement.py`:

1. Reads recent task history from SQLite
2. Identifies agents scoring below a 70% success rate
3. Uses Sonnet to rewrite those agents' system prompts
4. Saves the revised prompts — agents pick them up on their next call

---

## Project Structure

```
interview-agent/
├── main.py              # CLI — ask / listen / serve
├── app.py               # Flask server + SSE streaming
├── orchestrator.py      # 2-wave parallel routing engine
├── mic.py               # Whisper voice input
├── config.py            # Model and path config
├── requirements.txt
├── agents/
│   ├── base.py          # Shared call logic, DB logging
│   ├── classifier.py
│   ├── speed_tip.py
│   ├── behavioral.py
│   ├── coder.py
│   ├── js_explainer.py
│   ├── debugger.py
│   ├── fullstack.py
│   └── motivation.py
├── loops/
│   └── improvement.py   # Auto prompt-rewrite cycle
├── memory/
│   ├── store.py         # SQLite wrapper
│   └── schema.sql
├── tools/
│   ├── filesystem.py
│   ├── shell.py
│   └── search.py
└── static/
    └── index.html       # Web UI entry point
```

---

## Notes

Intended for solo practice and self-review before interviews — rehearsing answers,
checking your reasoning against a model answer, and finding gaps to study.
