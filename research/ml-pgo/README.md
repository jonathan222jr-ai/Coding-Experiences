# ML-PGO — agent-guided GPU memory optimization

Undergraduate research (CSE 195) on whether an LLM agent can read GPU memory profiles,
find inefficiencies, and propose fixes a human would.

Built on **DrGPUM** (Lin, Zhou, Su — ASPLOS 2023), a memory profiler for NVIDIA GPUs.
Measured on an RTX 3090 running Ubuntu 22.04, CUDA 12.4, PyTorch 2.6.

## Result

On a PyTorch training workload, profiled end to end:

| | |
|---|---|
| Peak GPU memory | 62.3 MB |
| Optimal peak (profiler's computed lower bound) | 44.0 MB |
| **Recoverable** | **18.3 MB — 29.3% of peak** |
| PyTorch tensors observed | 180, inside 11 allocator segments |
| Allocations traced to a source line | 327 |

The interesting part isn't the percentage — it's that every allocation is attributed to
a specific line of the user's own Python, which is what makes an automated fix possible.

## The design constraint

**Detection is deterministic and runs locally. The model never produces a number.**

Every figure above is computed from the profiler's own bytes by `agent/drgpum/`. The
language model reads those findings and reasons about what to change in the source — it
is not asked what the memory usage was, because a model asked for a metric will produce
a plausible one.

That rule exists because the first version of this project didn't have it. It parsed a
profile format DrGPUM does not emit — `kernel_name,runtime_ms,sm_utilization_%` — and no
part of the pipeline had ever run against real profiler output. [MIGRATION.md](MIGRATION.md)
documents what went wrong and how it was found.

## Pipeline

```
gvprof -e memory_liveness     ->  plain-text profile files
        |
agent/drgpum/parser.py        ->  objects x ALLOC/COPYT/ACCESS/FREE ops
        |
agent/drgpum/detectors.py     ->  findings ranked by idle byte-kernels
        |
agent/ml_pgo_agent.py         ->  model diagnoses, locates in source, proposes a fix
        |
re-profile, compare peaks     ->  accept or revert; append to the ledger
```

### Detectors

| Finding | Condition |
|---|---|
| `NEVER_USED` | Allocated, never accessed, set, or copied |
| `LATE_FIRST_USE` | Long gap between allocation and first use |
| `DELAYED_FREE` | Long gap between last use and free |
| `NEVER_FREED` | Allocation with no matching free |
| `REDUNDANT_H2D_COPY` | Host-to-device copy overwritten before any read |
| `PEAK_MEMORY_GAP` | Current peak exceeds the profiler's optimal peak |

### Measuring harm

DrGPUM emits no timestamps — `op_id` orders events but its magnitude is meaningless, so
wall-clock cost can't be derived from a profile. Kernel launches are the only countable
unit of progress, so harm is measured in **idle byte-kernels**: bytes resident × kernel
launches during which those bytes went untouched. It's the discrete analogue of the
memory×time integral the profiler's own optimal-peak figure is computed against.

## Contents

| Path | Description |
|---|---|
| `main.py` | Entry point — `profile`, `analyze`, `agent`, `compare`, `ledger` |
| `agent/drgpum/` | Parser, detectors, reporting. All analysis lives here |
| `agent/ledger.py` | Append-only record of optimization attempts; enforces the stop conditions |
| `agent/ml_pgo_agent.py` | Claude-assisted analyze → suggest → validate |
| `agent/helpers/benchmark_runner.py` | Runs a workload under the profiler |
| `skills/drgpum-memory-pgo/` | The master agent skill — `SKILL.md` plus `scripts/`, `references/`, `assets/` |
| `skills/drg-profile-analyzer/` | Stage 1 — parse and rank |
| `skills/optimization-suggester/` | Stage 2 — locate in source, propose a fix |
| `skills/benchmark-validator/` | Stage 3 — verify, and decide whether to iterate |
| `tests/` | 37 tests, no GPU required; 13 run against real captured profiles |

## Two things the profiler does that aren't documented upstream

Both were found while validating the parser, and both change how the tool must be used.

**Without `torch-monitor`, DrGPUM reports allocator segments, not tensors.** The
top-ranked finding was a 20 MB object never accessed — for a model whose parameters total
2.51 MiB. Bisecting the workload showed it appearing at `model.to(device)`, and six of ten
objects were exact multiples of 2 MiB, with the 20 MB ones being exactly PyTorch's
`kLargeBuffer`. They're caching-allocator segments; the tensors live inside them.

**A second control knob decides whether the headline metric exists.**
`HPCRUN_SANITIZER_LIVENESS_ONGPU` is off by default, and without it no `ACCESS` operation
is recorded anywhere — so `optimal_memory_peak` reads as `0`, indistinguishable from a
real zero, and every object looks unused (86 false findings before this was caught). The
detectors now refuse to report usage-based findings when no access data is present.

Full write-up: [`skills/drgpum-memory-pgo/references/pytorch-allocator-segments.md`](skills/drgpum-memory-pgo/references/pytorch-allocator-segments.md)

## Running it

Analysis needs no GPU — real captured profiles are committed:

```bash
python main.py analyze tests/fixtures/real_pytorch_full
python -m pytest tests/ -q
```

Profiling needs the DrGPUM toolchain and a GPU:

```bash
python main.py profile -- python3 train.py
python main.py compare runs/baseline/... runs/optimized/...
```

`main.py agent` calls the Claude API and reads `ANTHROPIC_API_KEY` from the environment.
Everything else runs offline.

## Status

The profiler is built, the pipeline is complete and tested against real captures, and the
agent skill is written. **A full find-fix-verify cycle has not yet been completed** — the
system identifies and quantifies inefficiencies but has not yet been shown to repair one.
The current workload also peaks at 62 MB on a 24 GB card, so recovering 18 MB doesn't
enable anything observable; demonstrating that it matters needs a workload that presses
against device capacity.

## Note on scope

Only my own agent and analysis code is published here. **DrGPUM** is a separate
third-party project and is deliberately not vendored — see the
[DrGPUM repository](https://github.com/Lin-Mao/DrGPUM).

Building it on a current toolchain needed five fixes, two of which are upstream defects
(non-const comparators that GCC 11+ rejects, and a missing `typedef` that makes a header
define a variable). Those are documented in the
[main project repository](https://github.com/jonathan222jr-ai/ml-pgo-skill).
