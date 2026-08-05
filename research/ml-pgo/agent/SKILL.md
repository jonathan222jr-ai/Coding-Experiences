---
name: ml-pgo-with-claude-api
description: AI-powered end-to-end ML-PGO workflow using Claude API for profile analysis, optimization suggestions, and benchmark validation.
---

# Master Skill: ML-PGO with Claude API Integration

An intelligent GPU optimization pipeline powered by Claude AI. Automates the complete workflow from profiling to optimization validation.

## The Three-Skill Pipeline

```
Your GPU Code (CUDA/PyTorch)
    ↓
Profile with DrGPUM
    ↓
SKILL 1: Profile Analysis
  └─ Parse profile data
  └─ Identify hotspot kernels
  └─ Classify bottleneck types (Memory-Bound, Compute-Bound, Launch-Overhead)
  └─ Claude analyzes and provides diagnosis
    ↓
SKILL 2: Optimization Suggestions
  └─ Claude recommends specific optimizations
  └─ Ranks by Impact/Effort ratio
  └─ Provides expected speedups and implementation guidance
    ↓
SKILL 3: Benchmark Validation (if optimized profile available)
  └─ Compare baseline vs optimized metrics
  └─ Claude assesses speedup significance
  └─ Identifies bottleneck shifts
  └─ Recommends next steps
    ↓
Decision: Iterate or Ship
```

## Quick Start

### 1. Set Your API Key

```bash
# Option A: Environment variable (recommended)
export ANTHROPIC_API_KEY=sk-...

# Option B: Pass as command-line argument
python ml_pgo_agent.py --api-key sk-... --baseline profile.csv
```

### 2. Analyze a Baseline Profile

```bash
python ml_pgo_agent.py --baseline baseline_profile.csv
```

**What happens:**
- ✓ Parses your DrGPUM CSV output
- ✓ Claude analyzes bottleneck patterns
- ✓ Generates specific optimization recommendations
- ✓ Saves results to `pgo_results.json`

### 3. Validate Optimized Code

```bash
python ml_pgo_agent.py \
  --baseline baseline_profile.csv \
  --optimized optimized_profile.csv
```

**What happens:**
- ✓ Compares before/after metrics
- ✓ Claude validates the improvements
- ✓ Identifies which bottlenecks were fixed
- ✓ Recommends further optimizations or declares success

## Skills Breakdown

### SKILL 1: Profile Analysis (`analyze_profile()`)

**Trigger:** User has DrGPUM CSV output and wants to understand it.

**Input:** DrGPUM profile CSV with columns:
```
kernel_name,runtime_ms,sm_utilization_%,memory_bandwidth_%
matmul_kernel,50.0,45,85
softmax_kernel,25.0,30,20
layernorm_kernel,15.0,35,25
```

**Process:**
1. Parse CSV and extract metrics
2. Classify bottleneck type for each kernel:
   - **MEMORY_BOUND**: bandwidth > 70% AND sm_util < 60%
   - **COMPUTE_BOUND**: bandwidth < 50% AND sm_util < 50%
   - **LAUNCH_OVERHEAD**: sm_util < 30% (many small kernels)
   - **BALANCED**: Other combinations
3. Sort kernels by runtime impact
4. Query Claude to analyze patterns and diagnose root causes

**Output:**
- Detailed bottleneck analysis
- Per-kernel diagnosis with specific metrics
- Root cause explanations
- Critical observations for optimization

### SKILL 2: Optimization Suggestions (`suggest_optimizations()`)

**Trigger:** After analyzing profile, user wants actionable recommendations.

**Process:**
1. Provide Claude with profile summary and analysis
2. Request ranked optimization recommendations
3. Include expected speedups and implementation difficulty

**Output:**
- Specific optimization techniques (not generic advice)
- Expected speedup estimates
- Difficulty ratings (Easy/Medium/Hard)
- Pseudocode examples or kernel patterns
- Ranked by Impact/Effort ratio

**Examples of good suggestions:**
- "Use shared memory instead of global memory for this matmul (expected 1.5-2x, Easy)"
- "Fuse these three kernels to reduce launch overhead (expected 1.2x, Medium)"
- "Apply tensor core operations via cuBLAS (expected 3-5x, Medium)"

### SKILL 3: Benchmark Validation (`validate_results()`)

**Trigger:** User has optimized code and new profile, wants validation.

**Input:** Baseline and optimized profile CSVs

**Process:**
1. Compare metrics side-by-side
2. Calculate per-kernel and overall speedups
3. Detect bottleneck type shifts (e.g., Memory → Compute)
4. Query Claude to assess quality and significance of improvements
5. Get recommendations for next steps

**Output:**
- Overall speedup achieved
- Per-kernel comparison with speedups
- Bottleneck reclassification (did we fix the right thing?)
- Assessment of diminishing returns
- Recommendations to iterate or ship

## Golden Rules

1. **Profile First** - Never guess about performance. Always collect data.
2. **Diagnose Carefully** - Match observations to known bottleneck patterns.
3. **Validate Always** - Measure before/after. Optimization without measurement is just guessing.
4. **Rank by Priority** - Use Impact/Effort to find the best bang-for-buck optimizations.
5. **Stop When Returns Diminish** - If speedup < 5%, the optimization probably isn't worth it.

## Bottleneck Types Explained

| Type | Indicators | Root Causes | Typical Fixes |
|------|-----------|-------------|--------------|
| **MEMORY_BOUND** | High BW %, Low SM % | Inefficient memory access patterns | Shared memory, coalescing, tiling |
| **COMPUTE_BOUND** | Low BW %, Low SM % | Insufficient parallelism or low FLOPs/byte | Increase parallelism, better algorithms |
| **LAUNCH_OVERHEAD** | Many small kernels | Kernel launch cost dominates | Fuse kernels, batching |
| **BALANCED** | Moderate all metrics | Well-optimized kernel | Already good, look for algorithmic improvements |

## File Structure

```
ml-pgo-agent-enhanced/
├── SKILL.md                    # This file - skill definition
├── ml_pgo_agent.py            # Main agent (import & run this)
├── requirements.txt            # Python dependencies
├── helpers/
│   ├── parse_drgpum_csv.py    # CSV parsing utilities
│   └── benchmark_runner.py    # Profiling automation (optional)
├── examples/
│   ├── example_baseline.csv   # Sample DrGPUM output
│   └── example_optimized.csv  # Sample optimized profile
└── docs/
    └── TROUBLESHOOTING.md     # Common issues & fixes
```

## Setup & Dependencies

### Requirements

```bash
pip install -r requirements.txt
```

**Key dependencies:**
- `anthropic>=0.39.0` - Claude API client
- Python 3.8+

### Get Your API Key

1. Go to https://console.anthropic.com
2. Create/use an account (free trial available)
3. Get your API key from the dashboard
4. Set it: `export ANTHROPIC_API_KEY=sk-...`

## Usage Examples

### Example 1: Simple Profile Analysis

```bash
python ml_pgo_agent.py --baseline my_profile.csv
```

Output:
- Console output with profile summary
- Claude's analysis of bottlenecks
- Optimization suggestions ranked by impact
- Results saved to `pgo_results.json`

### Example 2: Before/After Comparison

```bash
python ml_pgo_agent.py \
  --baseline baseline.csv \
  --optimized optimized.csv \
  --output my_results.json
```

Output:
- Speedup metrics per kernel
- Bottleneck shift analysis
- Claude's assessment of optimization quality
- Recommendations for further improvements

### Example 3: Using Environment Variable

```bash
export ANTHROPIC_API_KEY=sk-proj-...
python ml_pgo_agent.py --baseline profile.csv
```

### Example 4: Custom Model

```bash
python ml_pgo_agent.py \
  --baseline profile.csv \
  --model claude-opus-4-1
```

## Python API

Use the agent programmatically in your own scripts:

```python
from ml_pgo_agent import MLPGOAgent

# Initialize
agent = MLPGOAgent(api_key="sk-...")

# Run full pipeline
results = agent.run_full_pipeline(
    baseline_csv="baseline.csv",
    optimized_csv="optimized.csv"
)

# Or use individual skills
analysis = agent.analyze_profile("baseline.csv")
suggestions = agent.suggest_optimizations(analysis)
validation = agent.validate_results("baseline.csv", "optimized.csv")

# Access Claude's insights
print(analysis["claude_analysis"])
print(suggestions["suggestions"])
print(validation["claude_assessment"])
```

## Understanding the Output

### pgo_results.json

```json
{
  "analysis": {
    "profile_summary": {
      "total_runtime_ms": 150.5,
      "top_kernels": [
        {
          "name": "matmul_kernel",
          "runtime_ms": 75.2,
          "sm_utilization": 45,
          "memory_bandwidth": 85,
          "bottleneck_type": "MEMORY_BOUND"
        }
      ]
    },
    "claude_analysis": "Claude's detailed bottleneck diagnosis..."
  },
  "suggestions": {
    "suggestions": "Claude's ranked optimization recommendations..."
  },
  "validation": {
    "comparison_summary": {
      "overall_speedup": 1.85,
      "kernel_results": [...]
    },
    "claude_assessment": "Assessment of optimization quality..."
  }
}
```

## When to Use Each Skill

| Situation | Skill | Command |
|-----------|-------|---------|
| New profiling data, need to understand bottlenecks | #1 | `--baseline profile.csv` |
| Want specific optimization recommendations | #2 | (Automatic after #1) |
| Have optimized code, want validation | #3 | `--baseline baseline.csv --optimized optimized.csv` |
| Iterating multiple optimization attempts | All 3 | Run multiple times with different profiles |

## Tips & Best Practices

- **Run baseline first:** Always establish a solid baseline profile before starting optimizations.
- **Profile with realistic data:** Use actual data sizes and workloads, not tiny test inputs.
- **Measure after each change:** Don't batch multiple optimizations - profile each individually to understand impact.
- **Trust the data, not intuition:** The profile reveals the truth; follow the numbers.
- **Use the agent iteratively:** After implementing Suggestion #1, re-profile and analyze again.
- **Save results:** The JSON output is valuable for tracking progress across optimization iterations.

## Troubleshooting

**Q: "API key not found" error**
```bash
# Set it:
export ANTHROPIC_API_KEY=sk-...
# Or pass it:
python ml_pgo_agent.py --api-key sk-... --baseline profile.csv
```

**Q: "Invalid CSV format" error**
- Ensure CSV has headers: `kernel_name,runtime_ms,sm_utilization_%,memory_bandwidth_%`
- Check for extra whitespace or special characters in kernel names

**Q: Claude gives vague suggestions**
- Provide more context: Use both baseline and optimized profiles
- Claude works better with complete data

**Q: How much does this cost?**
- Each analysis uses ~1000-2000 tokens (Claude API pricing: $3 per 1M input tokens)
- A full pipeline with analysis, suggestions, and validation: ~$0.01-0.05 per run

## References

This skill builds on the agent skills concept from:
- https://github.com/mit-han-lab/ncu-report-skill
- https://github.com/addyosmani/agent-skills
- https://github.com/VoltAgent/awesome-agent-skills
- https://mcpservers.org/agent-skills

## Next Steps

1. ✓ Set your `ANTHROPIC_API_KEY`
2. ✓ Run `python ml_pgo_agent.py --baseline <your_profile.csv>`
3. ✓ Implement Claude's top optimization suggestion
4. ✓ Re-profile and validate improvements
5. ✓ Iterate until diminishing returns
