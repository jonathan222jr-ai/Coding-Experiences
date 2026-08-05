---
name: optimization-suggester
description: Suggest GPU kernel optimizations based on bottleneck diagnosis. Recommends concrete fixes ranked by impact and effort.
---

# Skill 2: Optimization Suggester

**When to use:** After Skill 1 diagnoses bottleneck, to get specific optimization recommendations.

## Input: Bottleneck Diagnosis from Skill 1

You know:
- Kernel name and runtime
- Bottleneck type (memory-bound, compute-bound, launch-overhead)
- Key metrics (SM%, bandwidth%)

## Output: Ranked Recommendations

### For MEMORY-BOUND Kernels

**Recommendation 1: Fix Memory Coalescing**
- Impact: 9/10 (fixes scattered access)
- Effort: 3/10 (requires understanding)
- Score: 3.0 (HIGHEST PRIORITY)
- Expected: 2-5x kernel speedup

Before (BAD - scattered):
```cuda
out[y * N + x] = in[x * N + y];
```

After (GOOD - coalesced):
```cuda
__shared__ float tile[32][32];
tile[threadIdx.y][threadIdx.x] = in[y * N + x];
__syncthreads();
out[...] = tile[...];
```

**Recommendation 2: Kernel Fusion**
- Impact: 8/10 (eliminates memory roundtrips)
- Effort: 5/10 (algorithmic changes)
- Score: 1.6 (medium priority)
- Expected: 1.5-2.5x speedup

Combine adjacent kernels to avoid writing intermediate results to global memory.

### For COMPUTE-BOUND Kernels

**Recommendation 1: Increase Arithmetic Intensity**
- Impact: 8/10 (more work per byte)
- Effort: 2/10 (loop unrolling)
- Score: 4.0 (VERY HIGH PRIORITY)
- Expected: 2-3x speedup

Before (low intensity):
```cuda
out[idx] = in[idx] + 1.0f;  // 1 FLOP per 4 bytes
```

After (high intensity):
```cuda
float sum = 0.0f;
for (int i = 0; i < 8; i++) {
    float val = in[idx + i * stride];
    sum += val * val + sin(val);  // Many FLOPs per byte
}
out[idx] = sum;
```

**Recommendation 2: Reduce Thread Divergence**
- Impact: 6/10 (improves warp efficiency)
- Effort: 2/10 (code refactoring)
- Score: 3.0 (medium priority)
- Expected: 1.5-2x speedup

### For LAUNCH-OVERHEAD Kernels

**Recommendation: Fuse Adjacent Kernels**
- Impact: 9/10 (eliminates launch cost)
- Effort: 3/10 (merging logic)
- Score: 3.0 (HIGHEST PRIORITY)
- Expected: 2-5x speedup (depends on % of time spent in launch)

## How to Rank

Priority Score = Impact / Effort

Optimize in this order:
1. Score > 3.0 (do first)
2. Score 1.5-3.0 (do second)
3. Score < 1.5 (do last if time)

## Success Criteria

✅ Bottleneck correctly matched to patterns
✅ 3-5 optimizations recommended
✅ Each ranked by priority score
✅ Before/after code provided
✅ Expected speedup quantified
✅ Ready for benchmark-validator skill

