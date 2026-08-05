# ML-PGO with DrGPUM: End-to-End GPU Optimization with LLM Agent Skills

**Complete system for GPU kernel optimization combining DrGPUM profiling, LLM agent skills, and automated validation.**

---

## 🎯 What This Project Does

This is a comprehensive ML-PGO (Machine Learning Profile-Guided Optimization) workflow that helps you:

1. **Profile GPU Code** - Identify performance bottlenecks with DrGPUM
2. **Analyze Results** - Use SKILL 1 to classify bottleneck types
3. **Get Recommendations** - Use SKILL 2 for specific, ranked optimization suggestions
4. **Implement & Validate** - Use SKILL 3 to measure improvements before/after
5. **Iterate Intelligently** - Continue optimizing with measurable progress

---

## 📁 Project Structure

```
ml-pgo-skill/
├── setup/                             ← START HERE
│   └── REMOTE_GPU_SETUP.md           ← Complete setup guide for remote GPU
│
├── examples/                          ← Learn by doing
│   └── matmul-optimization/
│       ├── baseline_matmul.py         ← Unoptimized kernel
│       ├── optimized_matmul.py        ← Optimized version
│       ├── README.md                  ← Complete walkthrough
│       └── sample_baseline_profile.csv ← Example output
│
├── agent-skills/                      ← Core system
│   ├── drg-profile-analyzer/SKILL.md        [SKILL 1] Analyze profiles
│   ├── optimization-suggester/SKILL.md      [SKILL 2] Get suggestions
│   └── benchmark-validator/SKILL.md         [SKILL 3] Validate results
│
├── helpers/                           ← Utilities
│   ├── parse_drgpum_csv.py           ← Parse profiling data
│   └── benchmark_runner.py            ← Automate benchmarking workflow
│
├── drgpum-profiler/                   ← Full DrGPUM source
│   ├── README.md
│   ├── bin/install                    ← Installation script
│   ├── bin/compile                    ← Compilation script
│   └── src/                           ← Source code
│
├── MASTER_SKILL.md                    ← Load into your LLM agent
└── README.md                          ← This file
```

---

## 🚀 Quick Start (5 minutes)

### Step 1: Setup Remote GPU (if needed)
```bash
# Read this first if using remote machine:
cat setup/REMOTE_GPU_SETUP.md
```

### Step 2: Install DrGPUM
```bash
cd drgpum-profiler
./bin/install                          # Takes 30-60 minutes
export DrGPUM_PATH=$(pwd)/gvprof
export PATH=${DrGPUM_PATH}/bin:$PATH
drg --version                          # Verify
```

### Step 3: Try the Example
```bash
cd examples/matmul-optimization
python baseline_matmul.py              # Run baseline (50ms)
python optimized_matmul.py             # Run optimized (33ms, 1.5x faster)
```

### Step 4: Profile with DrGPUM
```bash
drg -o baseline_profile.csv python baseline_matmul.py
drg -o optimized_profile.csv python optimized_matmul.py
```

### Step 5: Load Skills Into Your LLM Agent
```
Agent: "Load MASTER_SKILL.md and all three skills.
        Analyze these profiles and tell me what's happening."
```

---

## 🎓 Learning Path

### For First-Time Users

1. **Read:** `setup/REMOTE_GPU_SETUP.md` (10 min)
   - Understand remote GPU workflow
   - Set up environment

2. **Run:** `examples/matmul-optimization/README.md` (20 min)
   - Execute baseline code
   - Profile it
   - See the three-skill pipeline in action

3. **Apply:** Load MASTER_SKILL.md into your agent
   - Analyze sample profiles
   - Get recommendations
   - Understand the workflow

### For Advanced Users

1. Profile your own GPU code
2. Load profiles into SKILL 1
3. Follow SKILL 2 recommendations
4. Implement optimizations
5. Validate with SKILL 3

---

## 🛠️ The Three-Skill System

### SKILL 1: Profile Analyzer
**Input:** DrGPUM CSV profile  
**Output:** Bottleneck diagnosis
```
Kernel: matmul_kernel
SM: 45%, Bandwidth: 85%
→ Diagnosis: MEMORY-BOUND
```

📄 File: `agent-skills/drg-profile-analyzer/SKILL.md`

### SKILL 2: Optimization Suggester
**Input:** Bottleneck diagnosis  
**Output:** Ranked recommendations
```
MEMORY-BOUND kernel?
→ Recommendation 1: Memory Coalescing (Score: 3.0) - 2-5x speedup
→ Recommendation 2: Kernel Fusion (Score: 1.6) - 1.5-2.5x speedup
```

📄 File: `agent-skills/optimization-suggester/SKILL.md`

### SKILL 3: Benchmark Validator
**Input:** Before/after code + profiles  
**Output:** Validation report
```
Baseline: 50.2ms, Optimized: 33.5ms
→ Speedup: 1.50x ✓ VALIDATED
→ SM: 45%→68%, Bandwidth: 85%→72%
→ Bottleneck Fixed ✓
```

📄 File: `agent-skills/benchmark-validator/SKILL.md`

---

## 🔧 Utilities

### Parse Profile Data
```bash
python helpers/parse_drgpum_csv.py baseline_profile.csv

# Or compare two profiles
python helpers/parse_drgpum_csv.py baseline_profile.csv optimized_profile.csv
```

### Automated Benchmarking
```bash
python helpers/benchmark_runner.py baseline.py optimized.py

# Creates timestamped results directory with:
# - baseline_run output
# - baseline_profile.csv
# - optimized_run output
# - optimized_profile.csv
# - comparison report
```

---

## 📚 Golden Rules

1. **Profile First** - Never guess bottlenecks
2. **Diagnose Carefully** - Match profile data to known patterns
3. **Validate Always** - Measure both before/after with hard numbers
4. **Rank by Priority** - Use Impact/Effort score from SKILL 2
5. **Stop When Diminishing** - Quit when speedup < 5%

---

## 📊 Bottleneck Types Reference

| Bottleneck | Indicator | Solution | Expected Speedup |
|------------|-----------|----------|------------------|
| **Memory-Bound** | High bandwidth %, low SM % | Coalesce access, tiling, fuse kernels | 2-5x |
| **Compute-Bound** | Low bandwidth %, low SM % | Increase arithmetic intensity, fuse | 2-3x |
| **Launch-Overhead** | Many small kernels | Fuse adjacent kernels | 2-5x |
| **I/O-Bound** | Waiting for data | Prefetch, pipeline, overlap | 1.5-2x |

---

## ❓ FAQ

### Q: How long does DrGPUM install take?
**A:** First-time install: 30-60 minutes (depends on hardware)
- Compiles from source
- Downloads dependencies via spack
- Builds hpctoolkit, redshow, etc.

### Q: Can I use this on a remote GPU?
**A:** Yes! See `setup/REMOTE_GPU_SETUP.md`
- Use SSH + tmux to survive disconnects
- Profile over network (profiling is fast)

### Q: What GPU do I need?
**A:** Any NVIDIA GPU with Compute Capability 5.0+
- Tesla K40/M40: CC 5.0 ✓
- GTX 1080/Titan X: CC 6.1 ✓
- A100/H100: CC 8.0 ✓
- RTX 4090: CC 8.9 ✓

### Q: Can I use this for my own code?
**A:** Absolutely!
1. Profile with: `drg -o profile.csv python your_code.py`
2. Load profile into SKILL 1
3. Follow the three-skill workflow

### Q: How much speedup should I expect?
**A:** Depends on bottleneck type (see table above)
- Memory-bound: Often 1.5-3x (realistic)
- Compute-bound: Often 2-3x
- Launch-overhead: Often 2-5x (highly variable)

---

## 🎯 Next Steps

### To Get Started Today:
1. ✅ Read `setup/REMOTE_GPU_SETUP.md`
2. ✅ Follow `examples/matmul-optimization/README.md`
3. ✅ Load `MASTER_SKILL.md` into your LLM agent

### To Apply to Your Code:
1. Profile your GPU kernel: `drg -o profile.csv python your_code.py`
2. Use SKILL 1 to analyze the profile
3. Follow SKILL 2's recommendations
4. Implement the optimization
5. Use SKILL 3 to validate

### For More Information:
- **Remote Setup:** `setup/REMOTE_GPU_SETUP.md`
- **Complete Example:** `examples/matmul-optimization/README.md`
- **DrGPUM Docs:** `drgpum-profiler/README.md`
- **CUDA Performance:** https://docs.nvidia.com/cuda/
- **GPU Architecture:** NVIDIA Compute Capability documentation

---

## 📖 References

- **DrGPUM Original:** https://github.com/Lin-Mao/DrGPUM
- **NVIDIA CUDA Docs:** https://docs.nvidia.com/cuda/
- **cuBLAS Optimization:** https://docs.nvidia.com/cuda/cublas/
- **GPU Computing:** https://developer.nvidia.com/gpu-computing

---

## ✨ Example Workflow

See `examples/matmul-optimization/README.md` for a complete walkthrough:

```
Naive MatMul (50ms)
    ↓ [Profile]
Baseline Profile: SM=45%, BW=85%
    ↓ [SKILL 1: Analyze]
Diagnosis: MEMORY-BOUND
    ↓ [SKILL 2: Suggest]
Recommendation: Memory Coalescing (3.0 priority)
    ↓ [Implement]
Optimized MatMul (33ms)
    ↓ [Profile]
Optimized Profile: SM=68%, BW=72%
    ↓ [SKILL 3: Validate]
Result: 1.50x Speedup ✓ Bottleneck Fixed ✓
```

---

**Ready to optimize your GPU kernels? Start with the setup guide!** 🚀

```bash
cat setup/REMOTE_GPU_SETUP.md
```
