"""
Research Runner: Orchestrates batch optimization and learning loop

Runs multiple benchmarks through the ML-PGO pipeline:
1. Profile baseline
2. Generate optimization suggestions
3. Apply optimizations
4. Re-profile optimized code
5. Validate and learn
6. Report compression ratios and speedups

Implements the iterative learning loop that improves as more
benchmarks are processed.
"""

import json
import os
import tempfile
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import logging

from ml_pgo_agent_enhanced import EnhancedMLPGOAgent
from memory_system import CaseStudy
from token_tracker import TokenReporter, PromptOptimizer

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkConfig:
    """Configuration for a single benchmark."""
    name: str
    baseline_csv: str
    optimized_csv: Optional[str] = None
    hardware: str = "A100"
    expected_speedup: Optional[float] = None


class ResearchRunner:
    """
    Orchestrates batch processing of benchmarks with learning loop.
    
    Workflow:
    1. Load benchmark configs
    2. For each benchmark:
       a. Analyze profile using agent (memory system helps)
       b. Generate suggestions (cached patterns reduce tokens)
       c. If optimized version exists, validate
       d. Learn: Update success rates and cache
    3. Report total token savings and compression ratios
    """
    
    def __init__(self, agent: EnhancedMLPGOAgent, 
                 output_dir: str = None):
        self.agent = agent
        # Use cross-platform temp directory if not specified
        if output_dir is None:
            output_dir = os.path.join(tempfile.gettempdir(), "ml_pgo_results")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results: List[Dict] = []
        self.start_time = None
    
    def run_benchmarks(self, configs: List[BenchmarkConfig], 
                      save_results: bool = True) -> Dict:
        """Run optimization pipeline on multiple benchmarks."""
        logger.info(f"Starting research run with {len(configs)} benchmarks")
        self.start_time = datetime.now()
        
        overall_results = {
            "timestamp": self.start_time.isoformat(),
            "benchmark_count": len(configs),
            "benchmarks": [],
            "aggregate_metrics": {
                "total_speedup": 0,
                "avg_speedup": 0,
                "total_tokens_baseline": 0,
                "total_tokens_optimized": 0,
                "overall_compression_ratio": 0,
                "learning_curve": []
            }
        }
        
        total_speedup = 0
        total_baseline_tokens = 0
        total_optimized_tokens = 0
        
        for i, config in enumerate(configs, 1):
            logger.info(f"[{i}/{len(configs)}] Processing: {config.name}")
            
            benchmark_result = self._process_benchmark(config)
            overall_results["benchmarks"].append(benchmark_result)
            
            # Accumulate metrics
            if config.optimized_csv:
                speedup = benchmark_result.get("speedup", 1.0)
                total_speedup += speedup
            
            total_baseline_tokens += benchmark_result.get("token_usage_baseline", 0)
            total_optimized_tokens += benchmark_result.get("token_usage_optimized", 0)
            
            # Track learning curve (reduction in tokens per benchmark as memory fills)
            compression = benchmark_result.get("token_compression_ratio", 1.0)
            overall_results["aggregate_metrics"]["learning_curve"].append({
                "benchmark": config.name,
                "tokens_used": benchmark_result.get("token_usage_optimized", 0),
                "compression_ratio": compression
            })
            
            logger.info(f"  Speedup: {speedup:.2f}x, "
                       f"Token compression: {compression:.2%}")
        
        # Calculate aggregates
        processed_count = sum(1 for c in configs if c.optimized_csv)
        overall_results["aggregate_metrics"]["total_speedup"] = total_speedup
        overall_results["aggregate_metrics"]["avg_speedup"] = (
            total_speedup / processed_count if processed_count > 0 else 1.0
        )
        overall_results["aggregate_metrics"]["total_tokens_baseline"] = total_baseline_tokens
        overall_results["aggregate_metrics"]["total_tokens_optimized"] = total_optimized_tokens
        overall_results["aggregate_metrics"]["overall_compression_ratio"] = (
            total_optimized_tokens / total_baseline_tokens 
            if total_baseline_tokens > 0 else 1.0
        )
        
        if save_results:
            self._save_results(overall_results)
        
        return overall_results
    
    def _process_benchmark(self, config: BenchmarkConfig) -> Dict:
        """Process a single benchmark through the pipeline."""
        result = {
            "name": config.name,
            "timestamp": datetime.now().isoformat(),
            "hardware": config.hardware,
            "speedup": 1.0,
            "token_usage_baseline": 0,
            "token_usage_optimized": 0,
            "token_compression_ratio": 1.0
        }
        
        try:
            # Step 1: Analyze baseline
            logger.debug(f"  Analyzing baseline profile")
            analysis = self.agent.analyze_profile(
                config.baseline_csv,
                hardware=config.hardware
            )
            
            baseline_tokens = analysis.get("token_usage", {}).get("baseline_tokens", 0)
            optimized_tokens = analysis.get("token_usage", {}).get("optimized_tokens", 0)
            
            result["token_usage_baseline"] += baseline_tokens
            result["token_usage_optimized"] += optimized_tokens
            result["analysis"] = analysis
            
            # Step 2: Suggest optimizations
            logger.debug(f"  Generating optimization suggestions")
            suggestions = self.agent.suggest_optimizations(
                analysis,
                hardware=config.hardware
            )
            
            result["token_usage_baseline"] += suggestions.get("token_usage", {}).get("baseline_tokens", 0)
            result["token_usage_optimized"] += suggestions.get("token_usage", {}).get("optimized_tokens", 0)
            result["suggestions"] = suggestions
            
            # Step 3: Validate (if optimized profile provided)
            if config.optimized_csv:
                logger.debug(f"  Validating optimizations")
                validation = self.agent.validate_results(
                    config.baseline_csv,
                    config.optimized_csv,
                    hardware=config.hardware
                )
                
                result["token_usage_baseline"] += validation.get("token_usage", {}).get("baseline_tokens", 0)
                result["token_usage_optimized"] += validation.get("token_usage", {}).get("optimized_tokens", 0)
                result["validation"] = validation
                
                # Extract speedup
                result["speedup"] = validation.get("overall_speedup", 1.0)
                
                # Learn from results
                self._learn_from_optimization(config, analysis, validation)
            
            # Calculate compression ratio for this benchmark
            if result["token_usage_baseline"] > 0:
                result["token_compression_ratio"] = (
                    result["token_usage_optimized"] / result["token_usage_baseline"]
                )
            
            result["success"] = True
        
        except Exception as e:
            logger.error(f"Error processing benchmark {config.name}: {e}")
            result["success"] = False
            result["error"] = str(e)
        
        return result
    
    def _learn_from_optimization(self, config: BenchmarkConfig,
                                 analysis: Dict, validation: Dict):
        """
        Learn from optimization results and update memory system.
        
        This is where the agent improves over time by:
        1. Recording successful optimizations
        2. Updating success rates
        3. Learning bottleneck patterns
        """
        logger.debug(f"  Learning from {config.name}")
        
        try:
            # Extract kernel-level results
            for i, comparison in enumerate(validation.get("comparison", [])):
                kernel_name = comparison.get("kernel")
                speedup = comparison.get("speedup", 1.0)
                
                # Find corresponding analysis
                kernel_analysis = next(
                    (k for k in analysis.get("kernels", [])
                     if k.get("name") == kernel_name),
                    None
                )
                
                if not kernel_analysis:
                    continue
                
                # Create case study record
                case_study = CaseStudy(
                    study_id=f"{config.name}_{kernel_name}_{datetime.now().timestamp()}",
                    kernel_name=kernel_name,
                    input_signature=kernel_analysis.get("signature", ""),
                    optimizations_applied=self._extract_optimizations(config),
                    baseline_time_ms=comparison.get("baseline_time", 0),
                    optimized_time_ms=comparison.get("optimized_time", 0),
                    baseline_metrics=kernel_analysis.get("metrics", {}),
                    optimized_metrics=comparison,  # Simplified
                    tokens_original=1000,  # Placeholder
                    tokens_optimized=500,  # Placeholder
                    hardware=config.hardware,
                    success=speedup > 1.05,  # Success if >5% speedup
                    lessons_learned=[
                        f"Achieved {speedup:.2f}x speedup",
                        f"Bottleneck shifted: {comparison.get('baseline_bottleneck')} → "
                        f"{comparison.get('optimized_bottleneck')}"
                    ]
                )
                
                # Record in memory system
                self.agent.memory.record_case_study(case_study)
        
        except Exception as e:
            logger.warning(f"Error learning from optimization: {e}")
    
    def _extract_optimizations(self, config: BenchmarkConfig) -> List[str]:
        """Extract list of optimizations from config/suggestions."""
        # In a real scenario, this would parse the suggestions
        # For now, return generic list
        return ["memory_optimization", "kernel_fusion"]
    
    def _save_results(self, results: Dict):
        """Save results to disk."""
        results_file = self.output_dir / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {results_file}")
        
        # Also save latest
        (self.output_dir / "latest_results.json").write_text(json.dumps(results, indent=2))
    
    def generate_research_report(self) -> str:
        """Generate comprehensive research report."""
        report = "=" * 80 + "\n"
        report += "ML-PGO RESEARCH REPORT\n"
        report += "=" * 80 + "\n\n"
        
        if not self.results:
            return "No results to report yet"
        
        report += f"Timestamp: {self.start_time}\n"
        report += f"Benchmarks Processed: {len(self.results)}\n\n"
        
        # Speedup statistics
        speedups = [r.get("speedup", 1.0) for r in self.results if r.get("speedup")]
        if speedups:
            report += "SPEEDUP METRICS:\n"
            report += f"  Average Speedup: {sum(speedups)/len(speedups):.2f}x\n"
            report += f"  Min Speedup: {min(speedups):.2f}x\n"
            report += f"  Max Speedup: {max(speedups):.2f}x\n"
            report += f"  Total Speedup: {sum(speedups):.2f}x cumulative\n\n"
        
        # Token efficiency
        total_baseline = sum(r.get("token_usage_baseline", 0) for r in self.results)
        total_optimized = sum(r.get("token_usage_optimized", 0) for r in self.results)
        
        report += "TOKEN EFFICIENCY:\n"
        report += f"  Total Baseline Tokens: {total_baseline:,}\n"
        report += f"  Total Optimized Tokens: {total_optimized:,}\n"
        report += f"  Tokens Saved: {total_baseline - total_optimized:,}\n"
        compression = total_optimized / total_baseline if total_baseline > 0 else 1.0
        report += f"  Overall Compression Ratio: {compression:.2%}\n"
        report += f"  Efficiency Gain: {(1-compression)*100:.1f}%\n\n"
        
        # Learning curve
        report += "LEARNING CURVE (Token usage per benchmark):\n"
        for i, result in enumerate(self.results, 1):
            tokens = result.get("token_usage_optimized", 0)
            compression_ratio = result.get("token_compression_ratio", 1.0)
            report += f"  {i:2d}. {result.get('name'):30s} - {tokens:5d} tokens ({compression_ratio:.1%})\n"
        
        report += "\n" + "=" * 80 + "\n"
        
        return report
    
    def save_report(self, filename: Optional[str] = None) -> str:
        """Save report to file."""
        report = self.generate_research_report()
        
        if filename is None:
            filename = self.output_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        else:
            filename = Path(filename)
        
        filename.write_text(report)
        logger.info(f"Report saved to {filename}")
        
        return report


def create_benchmark_configs_from_directory(directory: str, 
                                           hardware: str = "A100") -> List[BenchmarkConfig]:
    """
    Create benchmark configs by scanning directory for profile CSVs.
    
    Looks for patterns like:
    - baseline_*.csv and optimized_*.csv pairs
    - Single profiles named *_profile.csv
    """
    configs = []
    path = Path(directory)
    
    # Find baseline/optimized pairs
    baseline_files = sorted(path.glob("*baseline*.csv"))
    
    for baseline in baseline_files:
        # Look for corresponding optimized file
        name = baseline.stem.replace("_baseline", "").replace("baseline_", "")
        optimized = path / f"{name}_optimized.csv"
        
        if optimized.exists():
            configs.append(BenchmarkConfig(
                name=name,
                baseline_csv=str(baseline),
                optimized_csv=str(optimized),
                hardware=hardware
            ))
        else:
            # Add as single profile
            configs.append(BenchmarkConfig(
                name=name,
                baseline_csv=str(baseline),
                hardware=hardware
            ))
    
    logger.info(f"Found {len(configs)} benchmark configs in {directory}")
    return configs


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example: Run research pipeline
    agent = EnhancedMLPGOAgent()
    runner = ResearchRunner(agent)
    
    # Create example configs
    configs = [
        BenchmarkConfig(
            name="matmul_baseline",
            baseline_csv="/tmp/ml-pgo-research/agent/examples/example_baseline.csv",
            hardware="A100"
        )
    ]
    
    # Run benchmarks
    results = runner.run_benchmarks(configs)
    
    # Generate report
    report = runner.generate_research_report()
    print(report)
    
    runner.save_report()
    agent.save_memory()
