# Engineering Agent System

A multi-agent AI system for a Python data platform built on
FastAPI · PostgreSQL · Delta Lake · Dagster · ClickHouse · Docker · HashiCorp · AWS.

## Project Structure

```
eng-agent/
├── agents/
│   ├── base.py          # BaseAgent — shared Anthropic client, memory logging
│   ├── all_agents.py    # All 9 stack-specific agents
│   ├── scaffolder.py    # ScaffolderAgent — generates projects as zip files
│   └── __init__.py
├── memory/
│   ├── store.py         # SQLite-backed session/task/learning store
│   └── schema.sql       # DB schema
├── loops/
│   └── improvement.py   # Auto self-improvement cycle (every 10 tasks)
├── static/
│   └── index.html       # Web UI
├── tests/
│   └── test_agents.py
├── deploy/
│   ├── docker/Dockerfile
│   ├── nomad/agent-system.nomad
│   └── vault/agent-system-read.hcl
├── output/              # Generated project zips land here
├── reports/             # Markdown run reports
├── config.py
├── orchestrator.py      # Plans and routes goals through agents
├── reports.py           # Markdown report generator
├── app.py               # Flask web server
├── main.py              # Click CLI
└── requirements.txt
```

## Quick Start

```bash
cp .env.example .env
# Set ANTHROPIC_API_KEY in .env

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python app.py            # Web UI → http://localhost:5001
```

## CLI

```bash
python main.py goal "Write a FastAPI endpoint for Dagster asset materializations"
python main.py scaffold "FastAPI auth service with JWT and PostgreSQL"
python main.py status
python main.py reflect
python main.py improve
python main.py research "ClickHouse projection design patterns"
python main.py fix path/to/broken_file.py
```

## Agents

| Agent | Key | Role |
|---|---|---|
| CodeGenAgent | `code_gen` | FastAPI routes, SQLAlchemy models, Dagster assets |
| CodeReviewAgent | `code_review` | Security, async correctness, query plans |
| DebuggerAgent | `debugger` | Root cause from tracebacks and logs |
| ResearchAgent | `researcher` | Library evaluation, ADRs, stack trade-offs |
| OptimizerAgent | `optimizer` | Latency, ClickHouse tuning, Delta Lake compaction |
| DocumenterAgent | `documenter` | READMEs, runbooks, OpenAPI annotations |
| RequirementsAgent | `requirements` | Specs with OLTP/OLAP/lakehouse routing |
| ReflectorAgent | `reflector` | Analyses recent failures → improvement JSON |
| AgentBuilderAgent | `agent_builder` | Rewrites agent prompts from perf data |
| ScaffolderAgent | `scaffolder` | Generates a complete project as a zip file |

## Scaffold Feature

Ask the system to generate a full project:

```bash
python main.py scaffold "FastAPI service that ingests events to ClickHouse via Kafka"
# → output/event_ingest_service_20260502_143012.zip
```

Or click **📦 Scaffold Project** in the web UI. The zip contains a complete,
runnable project with all files, tests, Dockerfile, and README.

## Deploy

```bash
# Apply Vault policy
vault policy write agent-system-read deploy/vault/agent-system-read.hcl

# Deploy with Nomad
nomad job run deploy/nomad/agent-system.nomad

# Or Docker
docker build -f deploy/docker/Dockerfile -t eng-agent .
docker run --env-file .env -p 5001:5001 eng-agent
```
