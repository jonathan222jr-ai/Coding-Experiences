"""
Token Tracking System for ML-PGO Agent

Measures token usage via ccusage and optimizes prompts for efficiency.
Tracks compression ratios (original vs optimized) for research metrics.

Integration points:
- ccusage: Command-line tool for token measurement
- prompt_optimizer: Reduces prompt size
- results_reporter: Documents compression ratios
"""

import json
import subprocess
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import logging
import tempfile
import os

logger = logging.getLogger(__name__)


@dataclass
class TokenMeasurement:
    """Records token usage for a single operation."""
    operation_id: str
    operation_type: str  # "analysis", "suggestion", "validation"
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model: str
    timestamp: str
    metadata: Dict = None
    
    @property
    def cost_usd(self) -> float:
        """Estimated cost at Claude pricing."""
        # Sonnet 4 pricing: $3/1M input, $15/1M output
        return (self.input_tokens * 3 + self.output_tokens * 15) / 1_000_000
    
    def to_dict(self):
        return asdict(self)


@dataclass
class OptimizationMetrics:
    """Tracks improvements from prompt optimization."""
    baseline_tokens: int
    optimized_tokens: int
    compression_ratio: float
    quality_score: float  # 0-1, how well optimization maintained quality
    speedup: float  # time reduction
    
    @property
    def efficiency_gain(self) -> float:
        """Combined score: (1 - compression_ratio) * quality_score"""
        return (1 - self.compression_ratio) * self.quality_score


class PromptOptimizer:
    """Reduces prompt size while maintaining effectiveness."""
    
    @staticmethod
    def compress_profile_data(metrics: List[Dict]) -> str:
        """Compress profile metrics into compact format."""
        # Instead of verbose prose, use structured format
        lines = []
        for m in metrics:
            # Format: kernel_name:runtime:sm%:bw%
            line = f"{m.get('kernel_name', 'unknown')}:{m.get('runtime_ms', 0):.1f}:{m.get('sm_utilization', 0):.0f}:{m.get('bandwidth_percent', 0):.0f}"
            lines.append(line)
        return "\n".join(lines)
    
    @staticmethod
    def create_compact_prompt(profile_data: Dict, 
                             memory_lookup: Optional[Dict] = None) -> str:
        """Create optimized prompt using cached knowledge."""
        prompt = f"""Analyze GPU kernel profile:
Metrics (name:time_ms:sm%:bw%):
{PromptOptimizer.compress_profile_data(profile_data.get('kernels', []))}

Bottleneck classification:
"""
        # Add pre-computed classifications to avoid repeating analysis
        if memory_lookup:
            for sig, data in memory_lookup.items():
                bottleneck = data.get("bottleneck_type", "UNKNOWN")
                prompt += f"- {sig}: {bottleneck}\n"
        
        prompt += "\nProvide: 1) Diagnosis 2) Top 3 optimizations ranked by Impact/Effort"
        return prompt
    
    @staticmethod
    def optimize_suggestions_prompt(analysis: str, 
                                   cached_techniques: List[Dict]) -> str:
        """Reuse cached optimization suggestions."""
        # Structure: Instead of asking Claude everything, provide cached ranked list
        if not cached_techniques:
            return f"Suggest specific optimizations for: {analysis}"
        
        prompt = f"""Given analysis: {analysis}

Pre-computed applicable techniques (ranked):
"""
        for i, tech in enumerate(cached_techniques[:3], 1):
            prompt += f"{i}. {tech['name']}: {tech['expected_speedup_min']:.1f}-{tech['expected_speedup_max']:.1f}x (success: {tech['success_rate']:.0%})\n"
        
        prompt += "\nRank these and suggest implementation approach for top choice."
        return prompt
    
    @staticmethod
    def create_validation_prompt(baseline: Dict, optimized: Dict) -> str:
        """Minimal prompt for validation."""
        speedup = baseline.get('total_time', 1) / optimized.get('total_time', 1)
        return f"""Baseline time: {baseline.get('total_time'):.1f}ms
Optimized time: {optimized.get('total_time'):.1f}ms
Speedup: {speedup:.2f}x

Assess: Was this speedup worthwhile? Any further optimization opportunities?"""


class CCUsageIntegration:
    """Integration with Claude's ccusage token measurement tool."""
    
    @staticmethod
    def is_available() -> bool:
        """Check if ccusage is installed."""
        try:
            subprocess.run(["ccusage", "--version"], capture_output=True, timeout=5)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    @staticmethod
    def measure_command(command: str, model: str = "claude-sonnet-4-6") -> Optional[TokenMeasurement]:
        """
        Measure tokens used by a Claude CLI command via ccusage.
        
        Usage:
            ccusage model_name "prompt text"
            
        Returns token counts and cost.
        """
        if not CCUsageIntegration.is_available():
            logger.warning("ccusage not available, returning None")
            return None
        
        try:
            # Format: ccusage claude-sonnet-4-6 "your prompt"
            result = subprocess.run(
                ["ccusage", model, command],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse output to extract token counts
            # Expected format varies, but typically includes "input_tokens: X, output_tokens: Y"
            output = result.stdout + result.stderr
            
            input_match = re.search(r'input_tokens[:\s]+(\d+)', output)
            output_match = re.search(r'output_tokens[:\s]+(\d+)', output)
            
            if input_match and output_match:
                input_tokens = int(input_match.group(1))
                output_tokens = int(output_match.group(1))
                
                return TokenMeasurement(
                    operation_id=f"op_{datetime.now().timestamp()}",
                    operation_type="claude_call",
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=input_tokens + output_tokens,
                    model=model,
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            logger.error(f"Error measuring tokens with ccusage: {e}")
        
        return None


class TokenReporter:
    """Generates reports on token usage and compression."""
    
    def __init__(self, storage_path: str = None):
        # Use cross-platform temp directory if not specified
        if storage_path is None:
            storage_path = os.path.join(tempfile.gettempdir(), "ml_pgo_tokens")
        
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.measurements: List[TokenMeasurement] = self._load_measurements()
    
    def _load_measurements(self) -> List[TokenMeasurement]:
        """Load previous measurements from disk."""
        measurements_file = self.storage_path / "measurements.json"
        if measurements_file.exists():
            with open(measurements_file, 'r') as f:
                data = json.load(f)
                return [TokenMeasurement(**m) for m in data]
        return []
    
    def record_measurement(self, measurement: TokenMeasurement):
        """Record a token measurement."""
        self.measurements.append(measurement)
        self._save_measurements()
        logger.info(f"Recorded: {measurement.operation_type} - "
                   f"{measurement.total_tokens} tokens (${measurement.cost_usd:.4f})")
    
    def _save_measurements(self):
        """Persist measurements to disk."""
        measurements_file = self.storage_path / "measurements.json"
        with open(measurements_file, 'w') as f:
            json.dump([m.to_dict() for m in self.measurements], f, indent=2)
    
    def get_summary_by_type(self) -> Dict[str, Dict]:
        """Aggregate statistics by operation type."""
        summary = {}
        for m in self.measurements:
            op_type = m.operation_type
            if op_type not in summary:
                summary[op_type] = {
                    "count": 0,
                    "total_tokens": 0,
                    "avg_tokens": 0,
                    "total_cost": 0,
                    "min_tokens": float('inf'),
                    "max_tokens": 0
                }
            
            stats = summary[op_type]
            stats["count"] += 1
            stats["total_tokens"] += m.total_tokens
            stats["total_cost"] += m.cost_usd
            stats["min_tokens"] = min(stats["min_tokens"], m.total_tokens)
            stats["max_tokens"] = max(stats["max_tokens"], m.total_tokens)
        
        # Calculate averages
        for op_type in summary:
            count = summary[op_type]["count"]
            summary[op_type]["avg_tokens"] = summary[op_type]["total_tokens"] // count if count > 0 else 0
        
        return summary
    
    def get_compression_report(self, baseline_measurements: List[TokenMeasurement],
                              optimized_measurements: List[TokenMeasurement]) -> Dict:
        """Compare token usage before/after optimization."""
        baseline_total = sum(m.total_tokens for m in baseline_measurements)
        optimized_total = sum(m.total_tokens for m in optimized_measurements)
        
        if baseline_total == 0:
            compression_ratio = 1.0
        else:
            compression_ratio = optimized_total / baseline_total
        
        return {
            "baseline_tokens": baseline_total,
            "optimized_tokens": optimized_total,
            "tokens_saved": baseline_total - optimized_total,
            "compression_ratio": compression_ratio,
            "percent_reduction": (1 - compression_ratio) * 100,
            "baseline_cost": sum(m.cost_usd for m in baseline_measurements),
            "optimized_cost": sum(m.cost_usd for m in optimized_measurements),
            "cost_savings": sum(m.cost_usd for m in baseline_measurements) - 
                           sum(m.cost_usd for m in optimized_measurements)
        }
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate human-readable report."""
        summary = self.get_summary_by_type()
        
        report = "=" * 60 + "\n"
        report += "TOKEN USAGE SUMMARY REPORT\n"
        report += "=" * 60 + "\n\n"
        
        total_tokens = sum(m.total_tokens for m in self.measurements)
        total_cost = sum(m.cost_usd for m in self.measurements)
        
        report += f"Total Operations: {len(self.measurements)}\n"
        report += f"Total Tokens: {total_tokens:,}\n"
        report += f"Total Cost: ${total_cost:.2f}\n"
        report += f"Average Tokens/Operation: {total_tokens // len(self.measurements) if self.measurements else 0}\n\n"
        
        report += "By Operation Type:\n"
        report += "-" * 60 + "\n"
        for op_type, stats in summary.items():
            report += f"\n{op_type.upper()}:\n"
            report += f"  Operations: {stats['count']}\n"
            report += f"  Total Tokens: {stats['total_tokens']:,}\n"
            report += f"  Avg Tokens: {stats['avg_tokens']:,}\n"
            report += f"  Range: {stats['min_tokens']}-{stats['max_tokens']}\n"
            report += f"  Cost: ${stats['total_cost']:.2f}\n"
        
        if output_file:
            Path(output_file).write_text(report)
            logger.info(f"Report saved to {output_file}")
        
        return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example: Check ccusage
    print(f"ccusage available: {CCUsageIntegration.is_available()}")
    
    # Example: Create optimized prompts
    profile_data = {
        "kernels": [
            {"kernel_name": "matmul", "runtime_ms": 50, "sm_utilization": 45, "bandwidth_percent": 85},
            {"kernel_name": "softmax", "runtime_ms": 25, "sm_utilization": 30, "bandwidth_percent": 20}
        ]
    }
    
    original = f"Please analyze this GPU profile and provide optimization suggestions:\n{json.dumps(profile_data, indent=2)}"
    optimized = PromptOptimizer.create_compact_prompt(profile_data)
    
    print("Original prompt length:", len(original))
    print("Optimized prompt length:", len(optimized))
    print(f"Compression: {len(optimized) / len(original):.2%}")
    
    print("\nOptimized prompt:")
    print(optimized)
