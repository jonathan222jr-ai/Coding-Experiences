---
name: drg-profile-analyzer
description: Analyze GPU profiling reports from DrGPUM. Use when user needs to understand profile output, identify kernel hotspots, or diagnose performance bottlenecks.
---

# Skill 1: DrGPUM Profile Analyzer

**When to use:** User has DrGPUM profiling output (CSV) and needs to understand it.

## What This Skill Does

1. Parse DrGPUM CSV output
2. Identify hotspot kernels (longest runtime)
3. Classify bottleneck type:
   - Memory-Bound (high bandwidth %, low SM %)
   - Compute-Bound (low bandwidth %, low SM %)
   - Launch-Overhead (many small kernels)
   - I/O-Bound (waiting for data)
4. Generate diagnostic report

## Golden Rule

**Profile data is facts. Never hypothesize before reading the numbers.**

## Workflow

### Input: DrGPUM CSV Profile

```csv
kernel_name,runtime_ms,sm_utilization_%,memory_bandwidth_%
matmul_kernel,50.0,45,85
softmax_kernel,25.0,30,20
layernorm_kernel,15.0,35,25
```

### Analysis Steps

1. Extract metrics from CSV
2. Sort by runtime (find top bottlenecks)
3. Classify each kernel:
   - If (bandwidth > 70% AND sm_util < 60%) → MEMORY_BOUND
   - If (bandwidth < 50% AND sm_util < 50%) → COMPUTE_BOUND
   - If (many kernels < 0.5ms) → LAUNCH_OVERHEAD
4. Generate report

### Output: Diagnostic Report
