# ML-Guided Profile-Guided Optimization

Undergraduate research on using an LLM agent to interpret GPU memory profiles and
propose profile-guided optimizations.

## Contents

| Path | Description |
|---|---|
| `agent/ml_pgo_agent.py` | Core agent — reads profiler output and proposes optimizations |
| `agent/ml_pgo_agent_enhanced.py` | Extended agent with a richer analysis pass |
| `agent/memory_system.py` | Persistent store so the agent can learn across runs |
| `agent/token_tracker.py` | Token accounting for API usage |
| `agent/research_runner.py` | Batch experiment driver |
| `agent/helpers/parse_drgpum_csv.py` | Parses profiler CSV output |
| `agent/helpers/benchmark_runner.py` | Builds and times benchmark programs |
| `main.py` | Entry point |
| `skills/enhanced-skills/` | Three authored agent skills, each a `SKILL.md` with frontmatter — `drg-profile-analyzer` (read a profile, find hotspots), `optimization-suggester` (rank concrete fixes by impact and effort), and `benchmark-validator` (confirm a speedup is real and the bottleneck actually moved). They chain in that order. |

## Setup

```bash
pip install -r agent/requirements.txt
```

The agent reads its credentials from the environment:

```bash
export ANTHROPIC_API_KEY=your-key-here
```

## Note on scope

Only my own agent and analysis code is published here. The profiler this work builds
on, **DrGPUM** (Lin, Zhou, and Su — ASPLOS 2023), is a separate third-party project and
is deliberately not vendored into this repository. See the
[DrGPUM repository](https://github.com/Lin-Mao/DrGPUM) for that component.
