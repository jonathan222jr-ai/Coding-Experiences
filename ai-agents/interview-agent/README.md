# micro1 Co-Pilot — Interview Agent v2

Real-time AI interview assistant for the **Software Engineer, New Grad (Zara)** role at micro1.
Speak or type the question → get a structured answer in ~2 seconds.

---

## Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Add your API key
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# 3. Run
python3 main.py serve          # web UI at http://localhost:5000
python3 main.py listen --loop  # voice mode (continuous)
python3 main.py ask "Explain closures in JavaScript"
```

---

## Voice Mode

```bash
pip install sounddevice soundfile openai-whisper numpy

python3 main.py listen           # record once → answer
python3 main.py listen --loop    # keep looping (best for live interview)
python3 main.py listen --file q.wav  # transcribe existing file
```

Whisper runs fully offline — no API key needed for transcription.

---

## Agent Roster

| Agent | Model | Purpose |
|---|---|---|
| `ClassifierAgent` | Haiku | Detects question type + urgency |
| `SpeedTipAgent` | Haiku | 1-liner coaching cue, fires in parallel |
| `BehavioralAgent` | Sonnet | STAR-format answers, micro1-tuned |
| `CoderAgent` | Sonnet | TypeScript solutions, Big-O, edge cases |
| `JSExplainerAgent` | Sonnet | Event loop, closures, Promises, hooks, TS |
| `DebuggerAgent` | Sonnet | Root-cause analysis + fixed code |
| `FullstackAgent` | Sonnet | System design, APIs, React/Node architecture |
| `MotivationAgent` | Sonnet | "Why micro1 / Zara" answers |

---

## Interview Focus Areas

- **Fullstack Fundamentals** → `FullstackAgent`
- **JS/TS Proficiency** → `JSExplainerAgent`, `CoderAgent`
- **Problem Solving & Debugging** → `CoderAgent`, `DebuggerAgent`
- **Ownership & Learning Velocity** → `BehavioralAgent`, `MotivationAgent`

---

## Self-Improvement

Every 20 questions, the `loops/improvement.py` cycle:
1. Reads recent task history
2. Identifies agents below 70% success rate
3. Uses Sonnet to rewrite their system prompts
4. Saves improved prompts to SQLite — agents pick them up on the next call

---

## Project Structure

```
interview-agent/
├── main.py              # CLI — ask / listen / serve
├── app.py               # Flask web server + SSE streaming
├── orchestrator.py      # 2-wave parallel routing engine
├── mic.py               # Whisper voice input
├── config.py            # Model + path config
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
│   └── improvement.py   # Auto-prompt-rewrite cycle
├── memory/
│   ├── store.py         # SQLite wrapper
│   └── schema.sql
├── tools/
│   ├── filesystem.py
│   ├── shell.py
│   └── search.py
└── static/
    └── index.html       # Landing page + web UI entry
```
