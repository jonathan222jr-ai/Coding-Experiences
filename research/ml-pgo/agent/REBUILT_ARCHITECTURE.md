# ML-PGO Research Project - Rebuilt Architecture

## Overview

This document describes the rebuilt ML-PGO system with:
1. **Memory System** - Prevents Cartesian product explosion (SQL-like optimization)
2. **Token Tracking** - Measures efficiency gains with ccusage
3. **Integrated Agent** - Uses memory system for efficient recommendations
4. **Research Runner** - Orchestrates batch processing and learning loop

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        GPU Code / Benchmark                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
                   [DrGPUM Profiling]
                         │
                         ▼
        ┌────────────────────────────────────┐
        │   Enhanced ML-PGO Agent            │
        ├────────────────────────────────────┤
        │                                    │
        │  Skill 1: Profile Analysis        │
        │  ├─ Register signature            │
        │  ├─ Check memory cache            │─────────┐
        │  ├─ Query Claude if needed        │         │
        │  └─ Cache results                 │         │
        │                                    │         │
        │  Skill 2: Optimize Suggestions    │         │
        │  ├─ Get cached patterns           │         │
        │  ├─ Rank by success_rate          │         │
        │  └─ Generate recommendations      │         │
        │                                    │         │
        │  Skill 3: Validate Results        │         │
        │  ├─ Compare before/after          │         │
        │  ├─ Calculate speedups            │─────────┤
        │  └─ Learn from results            │         │
        │                                    │         │
        └────────────────────────────────────┘         │
                         │                              │
        ┌────────────────▼──────────────────┐          │
        │   Memory System                    │◄────────┘
        ├────────────────────────────────────┤
        │                                    │
        │  Signature Index                  │
        │  ├─ Kernel hashes                 │
        │  ├─ Bottleneck classifications    │
        │  └─ Success rates                 │
        │                                    │
        │  Optimization Pattern Library     │
        │  ├─ MEMORY_BOUND → shared_mem     │
        │  ├─ COMPUTE_BOUND → parallelism  │
        │  └─ LAUNCH_OVERHEAD → fusion     │
        │                                    │
        │  Case Study Archive               │
        │  ├─ Historical results            │
        │  ├─ Token measurements            │
        │  └─ Lessons learned               │
        │                                    │
        │  Hardware Profiles                │
        │  ├─ A100, H100, L40, V100        │
        │  └─ Capabilities & bottlenecks    │
        │                                    │
        │  Learning Cache                   │
        │  └─ Claude's analyses (avoid recompute)
        │                                    │
        └────────────────────────────────────┘
                         │
        ┌────────────────▼──────────────────┐
        │   Token Tracking System            │
        ├────────────────────────────────────┤
        │                                    │
        │  Prompt Optimizer                 │
        │  ├─ Compress metrics to CSV format│
        │  ├─ Structure data instead of prose
        │  └─ Reuse cached recommendations  │
        │                                    │
        │  CCUsage Integration               │
        │  ├─ Measure actual token usage    │
        │  └─ Track input/output tokens     │
        │                                    │
        │  Token Reporter                   │
        │  ├─ Aggregate statistics          │
        │  ├─ Calculate compression ratios  │
        │  └─ Generate efficiency reports   │
        │                                    │
        └────────────────────────────────────┘
                         │
        ┌────────────────▼──────────────────┐
        │   Research Runner                  │
        ├────────────────────────────────────┤
        │                                    │
        │  Batch Processing                 │
        │  ├─ Process multiple benchmarks   │
        │  ├─ Track learning curve          │
        │  └─ Aggregate metrics             │
        │                                    │
        │  Learning Loop                    │
        │  ├─ Record successful optimizations
        │  ├─ Update success rates          │
        │  └─ Improve future recommendations
        │                                    │
        │  Reporting                        │
        │  ├─ Speedup metrics               │
        │  ├─ Token efficiency gains        │
        │  └─ Compression ratios            │
        │                                    │
        └────────────────────────────────────┘
                         │
                         ▼
                    [Results + Reports]
```

## Key Improvements Over Naive Approach

### Problem 1: Cartesian Product Explosion
**Naive:** Each kernel → Ask Claude everything → Generic output → No learning

**Solution (Memory System):**
```
Kernel signature → Fast lookup → Cached similar cases
             ├─ If found: Use cached optimizations (0 tokens)
             └─ If new: Query Claude once, cache forever (reuse 1000s of times)
```

**Example Savings:**
- Naive: 100 matmul kernels × 2500 tokens = 250,000 tokens
- Smart: First kernel 2500 tokens + 99 cache hits = 2500 tokens total
- **Ratio: 1%**

### Problem 2: Redundant Token Usage
**Naive:** Long prompts with full data dumps, verbose explanations

**Solution (Prompt Optimizer):**
```
Naive prompt:
  "We have a kernel called matmul with the following metrics:
   sm_utilization: 45%, bandwidth_utilization: 85%, runtime: 50ms
   This suggests a memory-bound bottleneck. Can you analyze..."
   → 300+ tokens just describing the data

Optimized prompt:
  "Metrics: matmul:50:45:85
   Bottleneck: MEMORY_BOUND
   Cached applicable techniques: [shared_memory, coalescing]
   Rank by success rate and suggest implementation"
   → 80 tokens, same information
```

**Token Savings: 73%**

### Problem 3: No Learning Loop
**Naive:** Process benchmark, forget, repeat

**Solution (Case Study Archive):**
- Record every optimization result
- Update success rates based on actual outcomes
- Learn which techniques work best for which patterns
- Share knowledge across all future benchmarks

## Data Structures

### 1. Bottleneck Signature Index
```json
{
  "kernel_signatures": {
    "a1b2c3d4": {
      "kernel_name": "matmul",
      "bottleneck_type": "MEMORY_BOUND",
      "metrics": {
        "sm_utilization": 45,
        "bandwidth_percent": 85,
        "runtime_ms": 50
      },
      "applicable_optimizations": [
        {
          "name": "shared_memory_tiling",
          "expected_speedup_min": 1.5,
          "expected_speedup_max": 2.5,
          "success_rate": 0.92,
          "tokens_baseline": 450,
          "tokens_optimized": 200
        }
      ],
      "seen_count": 47,
      "success_count": 43
    }
  }
}
```

### 2. Case Study Archive
```json
{
  "case_studies": {
    "matmul_optimization_1234567": {
      "input_signature": "a1b2c3d4",
      "optimizations_applied": ["shared_memory", "coalescing"],
      "speedup": 2.01,
      "tokens_original": 2100,
      "tokens_optimized": 850,
      "compression_ratio": 0.405,
      "success": true,
      "lessons_learned": [
        "Shared memory gave 1.8x, then coalescing added 1.1x → compound effect",
        "Worth implementing when bandwidth_percent > 75"
      ]
    }
  }
}
```

## Module Reference

### memory_system.py
**Purpose:** Structured knowledge base preventing Cartesian product explosion

**Key Classes:**
- `MemorySystem` - Main knowledge base
- `BottleneckClassifier` - Signature generation
- `KernelMetrics` - Metric data structure
- `CaseStudy` - Historical record

**Example:**
```python
from memory_system import MemorySystem, KernelMetrics

memory = MemorySystem()

# Register a kernel
metrics = KernelMetrics(
    sm_utilization=45,
    bandwidth_percent=85,
    runtime_ms=50,
    kernel_name="matmul"
)
sig = memory.register_kernel_signature(metrics)

# Get optimizations for its bottleneck type
opts = memory.get_optimizations_for_bottleneck("MEMORY_BOUND", hardware="A100")
for opt in opts:
    print(f"{opt.name}: {opt.expected_speedup_min}x expected")

# Record results
study = CaseStudy(
    study_id="matmul_opt_001",
    input_signature=sig,
    optimizations_applied=["shared_memory"],
    baseline_time_ms=50,
    optimized_time_ms=25,
    tokens_original=2500,
    tokens_optimized=1200,
    success=True
)
memory.record_case_study(study)
```

### token_tracker.py
**Purpose:** Measure and optimize token usage

**Key Classes:**
- `PromptOptimizer` - Compress prompts
- `CCUsageIntegration` - Measure with ccusage CLI
- `TokenReporter` - Report efficiency gains

**Example:**
```python
from token_tracker import PromptOptimizer, TokenReporter

# Compress prompt
compact = PromptOptimizer.create_compact_prompt(
    profile_data,
    memory_lookup=similar_kernels
)

# Track measurements
reporter = TokenReporter()
compression_report = reporter.get_compression_report(
    baseline_measurements,
    optimized_measurements
)
print(f"Compression ratio: {compression_report['compression_ratio']:.2%}")
```

### ml_pgo_agent_enhanced.py
**Purpose:** Refactored agent using memory system

**Key Methods:**
- `analyze_profile()` - SKILL 1: Parse profile using cache
- `suggest_optimizations()` - SKILL 2: Ranked suggestions
- `validate_results()` - SKILL 3: Compare before/after + learn
- `run_full_pipeline()` - Run all three skills

**Token Efficiency:**
- Caches Claude's analyses to avoid recomputation
- Uses structured data format to reduce token size
- Queries Claude only for novel patterns
- ~75% token reduction with 50+ similar kernels

### research_runner.py
**Purpose:** Batch processing and learning loop

**Key Methods:**
- `run_benchmarks()` - Process multiple profiles
- `generate_research_report()` - Aggregate metrics
- `_learn_from_optimization()` - Update memory after success

**Learning Loop:**
```
For each benchmark:
  1. Analyze (may be cached)
  2. Suggest optimizations (ranked by success rate)
  3. Validate improvements (if optimized profile exists)
  4. Record case study (update success rates + lessons)
  
As more benchmarks processed:
  - Signatures become more reliable
  - Optimization ranking improves
  - Token usage per benchmark decreases
  - Quality of suggestions increases
```

## Workflow: From Profile to Knowledge

### Step 1: Profile Baseline
```bash
# Generate profile with DrGPUM
drgpum ./gpu_code --output baseline.csv
```

### Step 2: First Analysis (Expensive)
```python
from ml_pgo_agent_enhanced import EnhancedMLPGOAgent

agent = EnhancedMLPGOAgent()
results = agent.run_full_pipeline("baseline.csv")

# Tokens used: ~2500 (querying Claude multiple times)
# But results cached for future similar kernels
```

### Step 3: Process Similar Kernel (Cheap)
```python
# Process another kernel with same bottleneck type
results = agent.analyze_profile("similar_kernel.csv")

# Tokens used: ~500 (mostly cached lookups)
# 5x fewer tokens for similar pattern
```

### Step 4: Validate & Learn
```python
# After optimization
results = agent.validate_results("baseline.csv", "optimized.csv")

# Automatically records success rate and lessons
# Next similar kernel gets better recommendations
```

### Step 5: Research Report
```python
from research_runner import ResearchRunner

runner = ResearchRunner(agent)
report = runner.generate_research_report()

# Shows:
# - Average speedup across all benchmarks
# - Token efficiency improvements
# - Learning curve (how token usage decreased)
# - Knowledge base statistics
```

## Expected Improvements

| Metric | Baseline | After Memory | Ratio |
|--------|----------|--------------|-------|
| Tokens/kernel (1st) | 2500 | 2500 | 1.0x |
| Tokens/kernel (2-10th) | 2500 | 400 | 0.16x |
| Tokens/kernel (11-50th) | 2500 | 200 | 0.08x |
| Tokens/kernel (50+) | 2500 | 100 | 0.04x |
| **Overall compression** | - | - | **0.15-0.20x** |
| Time/kernel | 20s | 1s | **0.05x** |
| Recommendation quality | 1.8x speedup | 2.1x speedup | **1.17x** |

## Integration Checklist

- [x] Memory System (`memory_system.py`)
  - [x] Bottleneck signature generation
  - [x] Optimization pattern library
  - [x] Case study archive
  - [x] Hardware profiles
  - [x] Learning cache

- [x] Token Tracking (`token_tracker.py`)
  - [x] Prompt optimizer
  - [x] CCUsage integration
  - [x] Token reporter
  - [x] Compression metrics

- [x] Enhanced Agent (`ml_pgo_agent_enhanced.py`)
  - [x] Three skills using memory
  - [x] Token measurement integration
  - [x] Conversation history (agentic memory)
  - [x] Learning feedback loop

- [x] Research Runner (`research_runner.py`)
  - [x] Batch processing
  - [x] Learning loop orchestration
  - [x] Report generation
  - [x] Benchmark discovery

## Next Steps to Full Deployment

1. **Copy modules to project:**
   ```bash
   cp memory_system.py /path/to/ml-pgo-research/agent/
   cp token_tracker.py /path/to/ml-pgo-research/agent/
   cp ml_pgo_agent_enhanced.py /path/to/ml-pgo-research/agent/
   cp research_runner.py /path/to/ml-pgo-research/agent/
   ```

2. **Update requirements.txt** with new dependencies

3. **Create integration wrapper** that chains everything:
   ```python
   # Full pipeline in one call
   runner = ResearchRunner(agent)
   results = runner.run_benchmarks(configs)
   report = runner.generate_research_report()
   ```

4. **Set up benchmarks** from your research corpus

5. **Measure token compression** with ccusage:
   ```bash
   ccusage claude-sonnet-4-6 "prompt_text"
   ```

6. **Track learning curve** as you process more benchmarks

## Research Metrics to Track

- **Speedup improvements** - Agent's recommendations quality
- **Token compression ratio** - Efficiency of memory system
- **Learning curve** - How quickly agent improves
- **Success rates by technique** - Which optimizations work best
- **Hardware-specific patterns** - Device-dependent recommendations
- **Cost-benefit analysis** - Speedup per token spent

## File Structure

```
ml-pgo-research/
├── agent/
│   ├── ml_pgo_agent.py          (original - keep for reference)
│   ├── ml_pgo_agent_enhanced.py (NEW - refactored with memory)
│   ├── memory_system.py          (NEW - knowledge base)
│   ├── token_tracker.py          (NEW - efficiency measurement)
│   ├── research_runner.py        (NEW - batch orchestration)
│   ├── REBUILT_ARCHITECTURE.md   (NEW - this file)
│   ├── INTEGRATION_GUIDE.md      (NEW - step-by-step setup)
│   └── examples/
│       └── research_pipeline_demo.py (NEW - full example)
├── profiler-enhanced/
│   └── (unchanged)
├── skills/
│   └── (unchanged)
└── (other original files unchanged)
```

## References

- **NSys AI** - Similar pattern: https://www.claudepluginhub.com/skills/gindachen-nsys-ai/analyze
- **NCU Report** - Humanized reporting: https://www.claudepluginhub.com/skills/bbuf-humanize-humanize/ncu-report

## Questions or Issues?

The system is designed to:
1. Scale to many benchmarks without token explosion
2. Learn and improve as more data is processed
3. Provide detailed efficiency metrics
4. Enable reproducible research

Each component is independent and can be tested/improved separately.
