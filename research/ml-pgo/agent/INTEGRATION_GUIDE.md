# ML-PGO Research Project - Integration Guide

Complete step-by-step guide to integrate the rebuilt components into your existing project.

## Prerequisites

- Python 3.8+
- `anthropic>=0.39.0` (Claude API)
- `numpy`, `pandas` (for data processing)
- `ccusage` (optional, for token measurement via CLI)
- Existing DrGPUM profiles in CSV format

## Installation

### Step 1: Copy New Modules

```bash
cd /path/to/ml-pgo-research
cp /path/to/memory_system.py agent/
cp /path/to/token_tracker.py agent/
cp /path/to/ml_pgo_agent_enhanced.py agent/
cp /path/to/research_runner.py agent/
```

### Step 2: Install Dependencies

```bash
# Already in requirements.txt
pip install anthropic>=0.39.0

# Optional: for ccusage token measurement
npm install -g @anthropic-ai/ccusage
```

### Step 3: Set API Key

```bash
export ANTHROPIC_API_KEY=sk-your-key-here
```

### Step 4: Verify Installation

```python
# test_integration.py
from agent.memory_system import MemorySystem
from agent.token_tracker import TokenReporter
from agent.ml_pgo_agent_enhanced import EnhancedMLPGOAgent

print("✓ Memory system imported")
print("✓ Token tracker imported")
print("✓ Enhanced agent imported")

# Quick test
agent = EnhancedMLPGOAgent()
print("✓ Agent initialized successfully")
```

Run test:
```bash
cd agent
python test_integration.py
```

## Usage Guide

### Simple Usage (Single Profile Analysis)

```python
from agent.ml_pgo_agent_enhanced import EnhancedMLPGOAgent

# Initialize agent (loads memory system automatically)
agent = EnhancedMLPGOAgent()

# Analyze a baseline profile
results = agent.analyze_profile("baseline.csv", hardware="A100")

# Get optimization suggestions
suggestions = agent.suggest_optimizations(results)

# If you have an optimized version, validate it
validation = agent.validate_results("baseline.csv", "optimized.csv")

# Save to persist memory (for learning)
agent.save_memory()
```

### Full Pipeline (Complete Workflow)

```python
from agent.ml_pgo_agent_enhanced import EnhancedMLPGOAgent

agent = EnhancedMLPGOAgent()

# Run complete pipeline in one call
results = agent.run_full_pipeline(
    baseline_csv="baseline.csv",
    optimized_csv="optimized.csv",  # Optional
    hardware="A100"
)

# Check token efficiency
print(f"Baseline tokens: {results['total_token_usage']['baseline']}")
print(f"Optimized tokens: {results['total_token_usage']['optimized']}")
print(f"Compression ratio: {results['total_token_usage']['compression_ratio']:.2%}")

agent.save_memory()
```

### Batch Processing (Multiple Benchmarks)

```python
from agent.ml_pgo_agent_enhanced import EnhancedMLPGOAgent
from agent.research_runner import ResearchRunner, BenchmarkConfig

# Initialize
agent = EnhancedMLPGOAgent()
runner = ResearchRunner(agent)

# Define benchmarks
configs = [
    BenchmarkConfig(
        name="matmul_optimization",
        baseline_csv="benchmarks/matmul_baseline.csv",
        optimized_csv="benchmarks/matmul_optimized.csv",
        hardware="A100"
    ),
    BenchmarkConfig(
        name="convolution_optimization",
        baseline_csv="benchmarks/conv_baseline.csv",
        optimized_csv="benchmarks/conv_optimized.csv",
        hardware="A100"
    ),
    BenchmarkConfig(
        name="softmax_optimization",
        baseline_csv="benchmarks/softmax_baseline.csv",
        optimized_csv="benchmarks/softmax_optimized.csv",
        hardware="H100"
    ),
]

# Run all benchmarks (learns from each one)
results = runner.run_benchmarks(configs)

# Generate report
report = runner.generate_research_report()
print(report)

# Save results
runner.save_report()
agent.save_memory()
```

### Auto-Discovery of Benchmarks

```python
from agent.ml_pgo_agent_enhanced import EnhancedMLPGOAgent
from agent.research_runner import ResearchRunner, create_benchmark_configs_from_directory

agent = EnhancedMLPGOAgent()
runner = ResearchRunner(agent)

# Auto-discover all baseline/optimized pairs in directory
configs = create_benchmark_configs_from_directory(
    "benchmarks/",
    hardware="A100"
)

# Run all found benchmarks
results = runner.run_benchmarks(configs)
```

### Token Measurement with ccusage

```python
from agent.token_tracker import CCUsageIntegration, TokenReporter

# Check if ccusage is available
if CCUsageIntegration.is_available():
    print("✓ ccusage is installed")
    
    # Measure tokens for a specific prompt
    measurement = CCUsageIntegration.measure_command(
        "Analyze this GPU profile: ...",
        model="claude-sonnet-4-6"
    )
    
    if measurement:
        print(f"Input tokens: {measurement.input_tokens}")
        print(f"Output tokens: {measurement.output_tokens}")
        print(f"Total tokens: {measurement.total_tokens}")
        print(f"Estimated cost: ${measurement.cost_usd:.4f}")
else:
    print("✗ ccusage not installed. Install with: npm install -g @anthropic-ai/ccusage")

# Generate token report
reporter = TokenReporter()
summary = reporter.get_summary_by_type()
print(reporter.generate_report())
```

## Configuration

### Custom Memory Storage

```python
from agent.ml_pgo_agent_enhanced import EnhancedMLPGOAgent

# Use custom storage directory
agent = EnhancedMLPGOAgent(
    memory_path="/custom/path/to/memory",
    token_path="/custom/path/to/tokens"
)
```

### Different Claude Models

```python
agent = EnhancedMLPGOAgent(
    model="claude-opus-4-1"  # For more complex analysis
)
```

### Custom Hardware Profile

```python
from agent.memory_system import MemorySystem

memory = MemorySystem()

# Add custom hardware
memory.hardware["RTX4090"] = {
    "sm_count": 128,
    "memory_bandwidth": 1008,
    "max_threads_per_block": 1024,
    "tensor_ops_per_cycle": 256,
    "common_bottlenecks": ["COMPUTE_BOUND", "LAUNCH_OVERHEAD"],
    "effective_techniques": ["tensor_cores", "shared_memory"]
}

memory.save()
```

## Understanding Memory System

### Bottleneck Classification

The system automatically classifies kernels into types:

```python
from agent.memory_system import BottleneckClassifier, KernelMetrics

metrics = KernelMetrics(
    sm_utilization=45,
    bandwidth_percent=85,
    runtime_ms=50,
    kernel_name="matmul"
)

# Classify bottleneck
bottleneck = BottleneckClassifier.classify(metrics)
# → "MEMORY_BOUND"

# Generate signature for caching
signature = BottleneckClassifier.generate_signature(metrics)
# → "a1b2c3d4" (8-char hash)
```

### Checking What's in Memory

```python
from agent.memory_system import MemorySystem

memory = MemorySystem()

# See how many kernels we've learned about
print(f"Registered kernels: {len(memory.signatures)}")
print(f"Case studies: {len(memory.case_studies)}")

# Look up a specific bottleneck type
optimizations = memory.get_optimizations_for_bottleneck("MEMORY_BOUND")
print(f"Optimizations for MEMORY_BOUND:")
for opt in optimizations:
    print(f"  - {opt.name}: {opt.success_rate:.0%} success rate")

# Find similar kernels
signature = "a1b2c3d4"
similar = memory.lookup_similar_kernels(signature, top_k=3)
print(f"Found {len(similar)} similar kernels in memory")
```

### Learning from Optimization Results

```python
from agent.memory_system import CaseStudy

# Manually record an optimization if not using research_runner
study = CaseStudy(
    study_id="my_optimization_001",
    kernel_name="matmul",
    input_signature="a1b2c3d4",
    optimizations_applied=["shared_memory", "coalescing"],
    baseline_time_ms=150.5,
    optimized_time_ms=75.2,
    baseline_metrics={},
    optimized_metrics={},
    tokens_original=2500,
    tokens_optimized=1200,
    hardware="A100",
    success=True,
    lessons_learned=[
        "Shared memory provided 1.8x speedup",
        "Coalescing added another 1.1x",
        "Total 2x speedup achieved"
    ]
)

memory.record_case_study(study)
```

## Token Efficiency Measurement

### Before & After Comparison

```python
from agent.token_tracker import TokenReporter

reporter = TokenReporter()

# Simulate baseline measurements (before optimization)
baseline_measurements = [...]  # List of TokenMeasurement objects

# Simulate optimized measurements (after optimization)
optimized_measurements = [...]

# Get compression report
report = reporter.get_compression_report(
    baseline_measurements,
    optimized_measurements
)

print(f"Original tokens: {report['baseline_tokens']:,}")
print(f"Optimized tokens: {report['optimized_tokens']:,}")
print(f"Tokens saved: {report['tokens_saved']:,}")
print(f"Compression ratio: {report['compression_ratio']:.2%}")
print(f"Cost savings: ${report['cost_savings']:.2f}")
```

### Generating Reports

```python
from agent.research_runner import ResearchRunner

runner = ResearchRunner(agent)
results = runner.run_benchmarks(configs)

# Text report
text_report = runner.generate_research_report()
print(text_report)

# Save to file
runner.save_report("my_research_report.txt")

# JSON results
import json
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
```

## Troubleshooting

### Issue: "API key not provided"

```bash
# Make sure to set environment variable
export ANTHROPIC_API_KEY=sk-your-key-here

# Or pass directly (not recommended for production)
agent = EnhancedMLPGOAgent(api_key="sk-your-key")
```

### Issue: "Profile file not found"

```python
# Check file exists
from pathlib import Path
csv_path = "baseline.csv"
if not Path(csv_path).exists():
    print(f"File not found: {csv_path}")
    print(f"Current directory: {Path.cwd()}")
    print(f"Files here: {list(Path.cwd().glob('*.csv'))}")
```

### Issue: Memory not persisting between runs

```python
# Make sure to call save() after running pipeline
agent.save_memory()

# Verify files were created
from pathlib import Path
memory_dir = Path("/tmp/ml_pgo_memory")
if memory_dir.exists():
    print(f"Memory files: {list(memory_dir.glob('*.json'))}")
```

### Issue: Low quality recommendations

This usually means the memory system hasn't learned enough patterns yet.
Solution: Process more benchmarks. The learning curve is exponential:
- 1-10 benchmarks: Recommendations may be generic
- 10-50 benchmarks: Pattern recognition improves significantly
- 50+ benchmarks: High-quality, specialized recommendations

## Advanced Usage

### Custom Optimization Techniques

```python
from agent.memory_system import OptimizationTechnique

# Add a technique to the memory system
tech = OptimizationTechnique(
    name="custom_optimization",
    expected_speedup_min=1.2,
    expected_speedup_max=1.5,
    difficulty="Medium",
    tokens_baseline=400,
    tokens_optimized=180,
    success_rate=0.75,
    applicable_hardware=["A100", "H100"],
    pseudocode="Your implementation strategy here"
)

# Add to memory
memory.patterns["CUSTOM_BOTTLENECK"]["techniques"].append(asdict(tech))
memory.save()
```

### Conversation History (Agentic Memory)

The agent maintains conversation history for more intelligent follow-ups:

```python
agent = EnhancedMLPGOAgent()

# First query
results1 = agent.analyze_profile("baseline.csv")

# Follow-up query (has context from first)
followup = agent._query_claude(
    "Given the earlier analysis, what if we combined techniques 1 and 2?",
    system="You have context from the previous profile analysis."
)

# The agent remembers both queries and can reason across them
```

### Batch Token Measurement

```python
from agent.token_tracker import CCUsageIntegration

prompts = [
    "First prompt to measure",
    "Second prompt to measure",
    "Third prompt to measure"
]

measurements = []
for prompt in prompts:
    m = CCUsageIntegration.measure_command(prompt)
    if m:
        measurements.append(m)
        print(f"Prompt used {m.total_tokens} tokens")

# Analyze
total = sum(m.total_tokens for m in measurements)
avg = total / len(measurements)
print(f"Average tokens: {avg:.0f}")
```

## Performance Targets

After full integration, you should see:

| Metric | Target | How to Achieve |
|--------|--------|----------------|
| **1st kernel analysis** | 2500 tokens | New pattern, queries Claude |
| **2-10th similar kernels** | 400 tokens | Cache + lookup |
| **11-50th similar kernels** | 200 tokens | Optimized prompts |
| **50+ kernels** | 100 tokens | Fully amortized |
| **Speedup improvements** | 2x average | Better recommendations |
| **Overall compression** | 0.15-0.20x | Memory system + optimization |
| **Processing time** | 1-2s/kernel | Cache hits vs 20s queries |

## Next Steps

1. **Run integration test:**
   ```bash
   cd agent
   python test_integration.py
   ```

2. **Process your first benchmark:**
   ```python
   agent = EnhancedMLPGOAgent()
   results = agent.run_full_pipeline("your_baseline.csv")
   ```

3. **Build benchmark corpus:**
   Collect all DrGPUM profiles into `benchmarks/` directory

4. **Run batch research:**
   ```python
   runner.run_benchmarks(configs)
   runner.generate_research_report()
   ```

5. **Measure token efficiency:**
   ```bash
   npm install -g @anthropic-ai/ccusage
   python measure_tokens.py
   ```

6. **Track learning curve:**
   Monitor how tokens per benchmark decrease as system learns

## References

- **Original ML-PGO Agent:** See `ml_pgo_agent.py`
- **Memory System Design:** See `REBUILT_ARCHITECTURE.md`
- **Token Optimization:** See `token_tracker.py` documentation
- **Research Examples:** See `examples/` directory

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review detailed architecture in `REBUILT_ARCHITECTURE.md`
3. Examine example code in docstrings
4. Test individual modules in isolation

The system is designed to be modular and testable at each layer.
