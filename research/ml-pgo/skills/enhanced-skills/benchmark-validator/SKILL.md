---
name: benchmark-validator
description: Validate GPU kernel optimizations by benchmarking and profiling. Verify speedup, correctness, and confirm bottleneck was fixed.
---

# Skill 3: Benchmark Validator

**When to use:** After optimization implemented, to validate improvements with hard numbers.

## Workflow

1. Validate Correctness
2. Benchmark Baseline Kernel
3. Benchmark Optimized Kernel
4. Re-profile with DrGPUM
5. Generate Comparison Report

## Step 1: Correctness Validation

Before benchmarking, verify outputs match:

```python
import torch

baseline_output = baseline_kernel(inputs)
optimized_output = optimized_kernel(inputs)

match = torch.allclose(baseline_output, optimized_output, rtol=1e-5, atol=1e-5)

if match:
    print("✓ Correctness check PASSED")
else:
    print("✗ Correctness check FAILED")
    print(f"Max difference: {(baseline_output - optimized_output).abs().max()}")
```

**STOP if correctness fails. Fix the bug first.**

## Step 2: Benchmark Baseline

```python
import torch

times = []
for _ in range(10):
    start_event = torch.cuda.Event(enable_timing=True)
    end_event = torch.cuda.Event(enable_timing=True)
    
    start_event.record()
    baseline_kernel(inputs)
    end_event.record()
    torch.cuda.synchronize()
    
    times.append(start_event.elapsed_time(end_event))

baseline_mean = sum(times) / len(times)
print(f"Baseline: {baseline_mean:.3f} ms")
```

## Step 3: Benchmark Optimized

Same as baseline but with `optimized_kernel()`.

## Step 4: Re-profile with DrGPUM

```bash
# Profile baseline
drg -o baseline_profile.csv python baseline_script.py

# Profile optimized
drg -o optimized_profile.csv python optimized_script.py
```

## Step 5: Generate Report
OPTIMIZATION VALIDATION REPORT
═════════════════════════════════════════
Optimization: Memory Coalescing Fix
CORRECTNESS: ✓ PASS
Max difference: 1.2e-6 (within tolerance)
LOCAL KERNEL SPEEDUP:
Baseline:    50.2 ± 0.3 ms
Optimized:   33.5 ± 0.2 ms
Speedup:     1.50x ✓
END-TO-END APPLICATION SPEEDUP:
Baseline:    102.0 ± 1.2 ms
Optimized:   84.2 ± 0.8 ms
Speedup:     1.22x ✓
PROFILE COMPARISON:
Metric               Baseline  Optimized  Change
───────────────────────────────────────────────
matmul SM Util       45%       68%        +23pp ✓
matmul Bandwidth     85%       72%        -13pp ✓
matmul Time          50.2ms    33.5ms     -33% ✓
VALIDATION:
✓ Correctness confirmed
✓ Kernel speedup matches prediction
✓ SM utilization improved
✓ Bottleneck characteristic changed
✓ Ready for next optimization or deployment

## Success Criteria

✅ Correctness validation passed
✅ Local kernel speedup measured
✅ End-to-end application speedup measured
✅ Profile re-run and compared
✅ Bottleneck actually fixed (evidence in profile)
✅ Report generated with before/after metrics

## Next Steps

- If speedup achieved: Celebrate! Consider next optimization.
- If no speedup: Hypothesis was wrong, revisit Skill 1.
- If partial speedup: Good progress, continue optimizing.
