# ML-PGO Agent: AI-Powered GPU Optimization Pipeline

Intelligent GPU optimization using Claude AI. Automates the complete workflow from profiling to validation.

**What it does:**
- 🔍 **Profile Analysis**: Parses DrGPUM CSV, classifies bottlenecks
- 💡 **Optimization Suggestions**: Claude recommends specific, ranked optimizations  
- ✅ **Benchmark Validation**: Compares before/after, assesses improvements
- 💬 **Agentic Memory**: Maintains context across all three skills

## Key Difference from Manual Profiling

| Manual | With ML-PGO Agent |
|--------|-------------------|
| You read the profile | Claude analyzes it |
| You guess what's wrong | Claude diagnoses bottlenecks |
| You search for solutions | Claude suggests optimizations |
| You manually track progress | Claude validates & recommends next steps |

## Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Set API key
export ANTHROPIC_API_KEY=sk-...

# 3. Analyze your profile
python ml_pgo_agent.py --baseline profile.csv

# 4. Validate optimized version
python ml_pgo_agent.py --baseline baseline.csv --optimized optimized.csv
```

See **QUICKSTART.md** for detailed setup.

## The Three Skills

### Skill 1: Profile Analysis
**Input:** DrGPUM CSV with kernel metrics  
**Process:** Parse data, classify bottlenecks, ask Claude to diagnose  
**Output:** Detailed bottleneck analysis from Claude  

Example bottleneck types:
- **MEMORY_BOUND**: High bandwidth %, low SM % → Use shared memory
- **COMPUTE_BOUND**: Low bandwidth %, low SM % → Increase parallelism
- **LAUNCH_OVERHEAD**: Many small kernels → Fuse kernels
- **BALANCED**: Well-optimized → Look for algorithms

### Skill 2: Optimization Suggestions
**Input:** Profile data and analysis from Skill 1  
**Process:** Ask Claude for specific, ranked recommendations  
**Output:** Actionable suggestions with expected speedups  

Claude provides:
- Specific optimization technique (not generic advice)
- Expected speedup (1.2x, 2x, etc.)
- Difficulty (Easy/Medium/Hard)
- Implementation guidance or pseudocode

### Skill 3: Benchmark Validation
**Input:** Baseline and optimized profile CSVs  
**Process:** Compare metrics, ask Claude to assess quality  
**Output:** Speedup report, bottleneck shifts, next step recommendations  

Claude evaluates:
- Was the speedup meaningful? (>5% is usually worth it)
- Did we fix the right bottleneck? (bottleneck type shift)
- Are there opportunities for further optimization?
- Should we iterate or ship?

## How It Works

```
GPU Code (CUDA/PyTorch)
    ↓
DrGPUM Profiling
    ↓ (CSV file)
Skill 1: Analyze Profile
    ├─ Parse metrics
    ├─ Classify bottlenecks
    └─ Claude diagnoses
       ↓
Skill 2: Suggest Optimizations
    ├─ Provide profile to Claude
    ├─ Request ranked suggestions
    └─ Claude recommends
       ↓
Skill 3: Validate Results (if optimized profile)
    ├─ Compare before/after
    ├─ Calculate speedups
    └─ Claude assesses quality
       ↓
Results JSON
    └─ Archive for tracking progress
```

## Python API

Use in your own scripts:

```python
from ml_pgo_agent import MLPGOAgent

# Initialize with API key
agent = MLPGOAgent(api_key="sk-...")

# Option A: Run full pipeline
results = agent.run_full_pipeline(
    baseline_csv="baseline.csv",
    optimized_csv="optimized.csv"  # optional
)

# Option B: Use individual skills
analysis = agent.analyze_profile("profile.csv")
suggestions = agent.suggest_optimizations(analysis)
validation = agent.validate_results("baseline.csv", "optimized.csv")

# Access Claude's insights
print(analysis["claude_analysis"])
print(suggestions["suggestions"])
print(validation["claude_assessment"])
```

## Command Line Usage

### Analyze a Profile
```bash
python ml_pgo_agent.py --baseline profile.csv
```

Output:
- Console: Profile summary + Claude's analysis + suggestions
- File: `pgo_results.json` with full results

### Validate Optimizations
```bash
python ml_pgo_agent.py \
  --baseline baseline.csv \
  --optimized optimized.csv \
  --output results.json
```

Output:
- Speedup metrics per kernel
- Bottleneck shift analysis
- Claude's assessment and recommendations

### All Options
```bash
python ml_pgo_agent.py --help
```

## CSV Format

DrGPUM output CSV should have these columns:

```csv
kernel_name,runtime_ms,sm_utilization_%,memory_bandwidth_%
```

Example:
```csv
kernel_name,runtime_ms,sm_utilization_%,memory_bandwidth_%
matmul_kernel,50.0,45,85
softmax_kernel,25.0,30,20
layernorm_kernel,15.0,35,25
```

## Understanding Results

### pgo_results.json Structure

```json
{
  "analysis": {
    "profile_summary": {
      "total_runtime_ms": 150.5,
      "num_kernels": 10,
      "bottleneck_summary": {
        "MEMORY_BOUND": 3,
        "COMPUTE_BOUND": 2,
        "BALANCED": 5
      },
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
    "suggestions": "Claude's ranked optimization recommendations...",
    "timestamp": "2024-01-15T10:30:00"
  },
  "validation": {
    "comparison_summary": {
      "overall_speedup": 1.85,
      "baseline_total_ms": 150.5,
      "optimized_total_ms": 81.4,
      "kernel_results": [
        {
          "kernel": "matmul_kernel",
          "speedup": 1.97,
          "baseline_bottleneck": "MEMORY_BOUND",
          "optimized_bottleneck": "COMPUTE_BOUND",
          "bottleneck_changed": true
        }
      ]
    },
    "claude_assessment": "Assessment of optimization quality and recommendations...",
    "timestamp": "2024-01-15T10:35:00"
  }
}
```

## Workflow Example

### Step 1: Profile Your Code
```bash
# Run DrGPUM profiler
drgpum ./your_program --output baseline.csv
```

### Step 2: Analyze with Claude
```bash
python ml_pgo_agent.py --baseline baseline.csv

# You'll see:
# - Profile summary (total time, kernel count, bottleneck types)
# - Claude's analysis of each bottleneck
# - Ranked optimization suggestions
# - Cost/benefit analysis
```

### Step 3: Implement Top Suggestion
```bash
# Based on Claude's recommendations, modify your code
# Example: Use shared memory for MEMORY_BOUND kernel
```

### Step 4: Re-Profile
```bash
drgpum ./your_program --output optimized_v1.csv
```

### Step 5: Validate
```bash
python ml_pgo_agent.py \
  --baseline baseline.csv \
  --optimized optimized_v1.csv

# You'll see:
# - Speedup for each kernel
# - Whether we fixed the right bottleneck
# - Remaining optimization opportunities
# - Claude's assessment of results
```

### Step 6: Decide
- **If speedup < 5%**: Probably not worth more work
- **If 5-20% speedup**: Continue with next suggestion
- **If > 20% speedup**: Great! Consider shipping or iterating

Repeat Steps 3-6 until diminishing returns.

## Golden Rules

1. **Profile First** - Never guess. Always collect real data.
2. **Diagnose Carefully** - Match data to known bottleneck patterns.
3. **Validate Always** - Measure before/after. Never ship without proof.
4. **Rank by Priority** - Use Impact/Effort to find best optimizations.
5. **Stop When Returns Diminish** - After 3-5x speedup or <5% gains, ship it.

## FAQ

**Q: How much does this cost?**  
A: Very cheap! Each analysis uses ~1000-2000 tokens. At $0.003/1K tokens, that's $0.01-0.05 per run.

**Q: Does Claude see my actual kernel code?**  
A: No, only the profiling metrics (runtime, SM%, bandwidth%). Your code is private.

**Q: What if Claude's suggestions don't work?**  
A: That's valuable data. You can:
- Implement the suggestion and re-profile to get more context
- Run analysis again for alternative suggestions
- Provide additional context (hardware, workload size)

**Q: Can I use this without internet?**  
A: No, the API calls to Claude require internet. The parsing/analysis code is local though.

**Q: What Claude model does this use?**  
A: Default is `claude-3-5-sonnet-20241022` (fast & cost-effective). You can specify others with `--model`.

**Q: How accurate are the speedup estimates?**  
A: Claude gives educated estimates based on patterns. Always validate with actual profiling.

**Q: Can I integrate this into CI/CD?**  
A: Yes! Use the Python API to programmatically analyze profiles in your pipeline.

## File Structure

```
ml-pgo-agent-enhanced/
├── SKILL.md                    # Comprehensive skill documentation
├── QUICKSTART.md              # Quick start guide (read this first!)
├── README.md                  # This file
├── ml_pgo_agent.py           # Main agent script (run this)
├── requirements.txt           # Python dependencies
├── helpers/
│   ├── parse_drgpum_csv.py   # CSV parsing utilities
│   └── benchmark_runner.py   # Profiling automation
├── examples/
│   ├── example_baseline.csv  # Sample profile (before optimization)
│   └── example_optimized.csv # Sample profile (after optimization)
└── pgo_results.json          # Output (generated after running)
```

## Setup

### Installation

```bash
# Clone or download this folder
cd ml-pgo-agent-enhanced

# Install dependencies
pip install -r requirements.txt
```

### Get API Key

1. Go to **https://console.anthropic.com**
2. Sign up or log in (free trial available)
3. Create API key from dashboard
4. Set environment variable:
   ```bash
   export ANTHROPIC_API_KEY=sk-...
   ```

### Verify Setup

```bash
python ml_pgo_agent.py --baseline examples/example_baseline.csv
```

If it works, you'll see:
- Profile summary
- Claude's analysis
- Optimization suggestions
- Results saved to `pgo_results.json`

## Troubleshooting

**Error: "No API key provided"**
```bash
export ANTHROPIC_API_KEY=sk-your-key-here
```

**Error: "Baseline file not found"**
```bash
# Make sure the file exists and path is correct
python ml_pgo_agent.py --baseline /full/path/to/profile.csv
```

**Error: "Invalid CSV format"**
- Check headers: `kernel_name,runtime_ms,sm_utilization_%,memory_bandwidth_%`
- Check for extra spaces/special characters

**No output after running**
- Add `-v` flag for verbose mode (in future versions)
- Check your internet connection (needed for Claude API)
- Verify API key is valid

## Integration with DrGPUM

To generate profile CSVs for this tool:

```bash
# Install DrGPUM (see: https://github.com/Lin-Mao/DrGPUM)
cd /path/to/DrGPUM
make

# Profile your GPU code
./bin/drgpum ./your_cuda_program --output profile.csv

# Analyze with our agent
python ml_pgo_agent.py --baseline profile.csv
```

## Advanced Usage

### Custom Model Selection

```bash
python ml_pgo_agent.py \
  --baseline profile.csv \
  --model claude-opus-4-1  # For more complex analysis
```

### Programmatic Usage with Conversation History

```python
from ml_pgo_agent import MLPGOAgent

agent = MLPGOAgent(api_key="sk-...")

# Analyze baseline
analysis = agent.analyze_profile("baseline.csv")

# Ask follow-up questions (context preserved)
followup = agent._query_claude(
    "Can you focus on the matmul_kernel specifically? "
    "What GPU architecture would benefit most from the shared memory optimization?"
)
print(followup)
```

### Batch Processing

```python
import json
from ml_pgo_agent import MLPGOAgent

agent = MLPGOAgent(api_key="sk-...")

profiles = [
    ("baseline_v1.csv", "optimized_v1.csv"),
    ("baseline_v2.csv", "optimized_v2.csv"),
]

results = {}
for baseline, optimized in profiles:
    results[baseline] = agent.run_full_pipeline(baseline, optimized)

# Save all results
with open("all_results.json", "w") as f:
    json.dump(results, f, indent=2)
```

## Benchmarking Workflow

Typical optimization pipeline:

1. **Establish Baseline**
   ```bash
   python ml_pgo_agent.py --baseline baseline.csv
   ```

2. **Implement Suggestion 1**
   - Code change
   - Re-profile

3. **Validate Suggestion 1**
   ```bash
   python ml_pgo_agent.py --baseline baseline.csv --optimized v1.csv
   ```

4. **Implement Suggestion 2**
   - Code change
   - Re-profile

5. **Validate Cumulative Impact**
   ```bash
   python ml_pgo_agent.py --baseline baseline.csv --optimized v2.csv
   ```

6. **Decide: Ship or Continue**
   - If 3-5x speedup: Generally worth shipping
   - If <5% gain: Diminishing returns
   - If 5-20% gain: Continue if time permits

## Related Resources

- **DrGPUM**: GPU profiler - https://github.com/Lin-Mao/DrGPUM
- **NCU Report Skill**: Similar approach - https://github.com/mit-han-lab/ncu-report-skill
- **Agent Skills**: Framework - https://github.com/addyosmani/agent-skills
- **Claude API Docs**: https://docs.anthropic.com
- **CUDA Optimization**: https://developer.nvidia.com/cuda-zone

## Contributing

This is your agent to modify and extend! Example enhancements:

- Add support for other profilers (NCU, Nsys, etc.)
- Integrate with hardware-specific optimization libraries
- Build automated optimization loops
- Add visualization of results
- Create domain-specific optimizers (transformers, graphs, etc.)

## License

MIT License - See your needs

## Support

Need help?

1. Check **QUICKSTART.md** for common issues
2. Read **SKILL.md** for detailed documentation
3. Review example CSVs in `examples/`
4. Check console output for specific error messages
5. Verify API key and internet connection

---

**Ready to optimize?** Start with:
```bash
python ml_pgo_agent.py --baseline examples/example_baseline.csv
```

Then adapt to your real profiling data!

🚀 Happy optimizing!
