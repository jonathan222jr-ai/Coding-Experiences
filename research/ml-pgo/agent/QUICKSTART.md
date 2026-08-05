# ML-PGO Agent with Claude API - Quick Start

Get your GPU optimization workflow running in 5 minutes.

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Get Your Claude API Key

1. Go to **https://console.anthropic.com**
2. Sign up or log in (free trial available)
3. Navigate to "API Keys" and create a new key
4. Copy the key (starts with `sk-`)

## Step 3: Set Your API Key

**Option A: Environment Variable (Recommended)**
```bash
export ANTHROPIC_API_KEY=sk-your-api-key-here
```

**Option B: Command Line**
```bash
python ml_pgo_agent.py --api-key sk-your-api-key-here --baseline your_profile.csv
```

## Step 4: Test with Sample Data

```bash
# Analyze the example baseline profile
python ml_pgo_agent.py --baseline examples/example_baseline.csv

# Or test the full pipeline with before/after
python ml_pgo_agent.py \
  --baseline examples/example_baseline.csv \
  --optimized examples/example_optimized.csv
```

## Step 5: Use with Your Real Profiling Data

```bash
# Analyze your DrGPUM profile
python ml_pgo_agent.py --baseline your_profile.csv

# After implementing optimizations, validate them
python ml_pgo_agent.py \
  --baseline your_profile.csv \
  --optimized your_optimized_profile.csv
```

## What You'll Get

### Console Output
- **Profile Summary**: Total runtime, kernel count, bottleneck breakdown
- **Claude's Analysis**: Specific bottleneck diagnosis with metrics
- **Optimization Suggestions**: Ranked by impact/effort ratio
- **Validation Report** (if you provide optimized profile): Speedup achieved, bottleneck shifts

### Results File (pgo_results.json)
Save your analysis results for:
- Tracking optimization progress
- Sharing findings with team
- Comparing multiple optimization attempts

## Understanding the Output

### Bottleneck Types

When Claude analyzes your profile, you'll see one of these classifications:

| Type | Meaning | Solution |
|------|---------|----------|
| **MEMORY_BOUND** | Waiting on memory bandwidth | Use shared memory, improve coalescing |
| **COMPUTE_BOUND** | Not enough GPU utilization | Increase parallelism, improve algorithms |
| **LAUNCH_OVERHEAD** | Many small kernels | Fuse kernels together |
| **BALANCED** | Well-optimized | Look for algorithmic improvements |

### Speedup

- **1.5x** = 50% faster (good optimization)
- **2.0x** = 2x faster (excellent)
- **3.0x+** = 3x faster (great optimization or major restructuring)

## Example Workflow

```
1. Profile your code:
   $ drgpum ... > baseline.csv

2. Analyze with Claude:
   $ python ml_pgo_agent.py --baseline baseline.csv
   
   ← Claude tells you the bottlenecks and suggests fixes

3. Implement top suggestion

4. Re-profile:
   $ drgpum ... > optimized_v1.csv

5. Validate improvement:
   $ python ml_pgo_agent.py \
     --baseline baseline.csv \
     --optimized optimized_v1.csv
   
   ← Claude shows speedup and recommends next steps

6. Repeat if needed (diminishing returns usually kick in at 3-5x speedup)
```

## Common Questions

**Q: How much does this cost?**
A: Very cheap! Each run uses ~1000-2000 tokens. At Claude's pricing, that's $0.01-0.05 per analysis.

**Q: What if my profile CSV format is different?**
A: Update the CSV headers to match:
```
kernel_name,runtime_ms,sm_utilization_%,memory_bandwidth_%
```

**Q: Can I use this offline?**
A: No, you need internet for Claude API calls. But the parsing/analysis logic is all local.

**Q: Does Claude see my kernel implementations?**
A: No, only the profiling metrics (runtime, SM utilization, bandwidth). Your actual code stays private.

**Q: What if Claude's suggestions don't help?**
A: That's valuable data! Share the before/after profiles for additional analysis. You can also:
- Run the analysis again for different suggestions
- Provide additional context about your hardware/workload

## Next Steps

1. ✅ Run the example: `python ml_pgo_agent.py --baseline examples/example_baseline.csv`
2. ✅ Adapt to your data: Change `--baseline` to your CSV file
3. ✅ Implement suggestions and re-profile
4. ✅ Validate improvements with `--optimized`
5. ✅ Iterate until you hit diminishing returns

## Need Help?

- Check **SKILL.md** for detailed documentation
- Review **ml_pgo_agent.py** for Python API usage
- See **examples/** for sample profiles

Good luck optimizing! 🚀
