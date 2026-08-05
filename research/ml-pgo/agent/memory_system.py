"""
Memory System for ML-PGO Agent

Implements a structured knowledge base for GPU optimization patterns.
Prevents Cartesian product explosion by caching and indexing similar kernels.

Architecture:
- Signature Index: Fast lookup of similar kernels
- Pattern Library: Known optimization techniques
- Case Study Archive: Historical results with tokens/speedups
- Hardware Profiles: Device-specific capabilities
"""

import json
import hashlib
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
import tempfile
import os

logger = logging.getLogger(__name__)


@dataclass
class KernelMetrics:
    """GPU kernel performance metrics."""
    sm_utilization: float
    bandwidth_percent: float
    runtime_ms: float
    kernel_name: str
    
    def to_dict(self):
        return asdict(self)


@dataclass
class OptimizationTechnique:
    """Description of an optimization technique."""
    name: str
    expected_speedup_min: float
    expected_speedup_max: float
    difficulty: str  # "Easy", "Medium", "Hard"
    tokens_baseline: int
    tokens_optimized: int
    success_rate: float
    applicable_hardware: List[str]
    pseudocode: Optional[str] = None
    prerequisites: List[str] = None
    
    def to_dict(self):
        return asdict(self)


@dataclass
class CaseStudy:
    """Record of a completed optimization."""
    study_id: str
    kernel_name: str
    input_signature: str
    optimizations_applied: List[str]
    baseline_time_ms: float
    optimized_time_ms: float
    baseline_metrics: Dict
    optimized_metrics: Dict
    tokens_original: int
    tokens_optimized: int
    hardware: str
    success: bool
    lessons_learned: List[str] = None
    
    @property
    def speedup(self) -> float:
        if self.baseline_time_ms == 0:
            return 1.0
        return self.baseline_time_ms / self.optimized_time_ms
    
    @property
    def compression_ratio(self) -> float:
        """Ratio of optimized to baseline tokens."""
        if self.tokens_original == 0:
            return 1.0
        return self.tokens_optimized / self.tokens_original
    
    def to_dict(self):
        data = asdict(self)
        data['speedup'] = self.speedup
        data['compression_ratio'] = self.compression_ratio
        return data


class BottleneckClassifier:
    """Classifies kernel bottleneck types and generates signatures."""
    
    BOTTLENECK_TYPES = {
        "MEMORY_BOUND": {
            "conditions": lambda m: m.bandwidth_percent > 70 and m.sm_utilization < 60,
            "typical_fixes": ["shared_memory", "coalescing", "caching"]
        },
        "COMPUTE_BOUND": {
            "conditions": lambda m: m.bandwidth_percent < 50 and m.sm_utilization < 50,
            "typical_fixes": ["increase_parallelism", "reduce_operations", "better_algorithm"]
        },
        "LAUNCH_OVERHEAD": {
            "conditions": lambda m: m.sm_utilization < 30,
            "typical_fixes": ["fuse_kernels", "batching", "grid_optimize"]
        },
        "BALANCED": {
            "conditions": lambda m: True,
            "typical_fixes": ["algorithmic_improvements"]
        }
    }
    
    @staticmethod
    def classify(metrics: KernelMetrics) -> str:
        """Classify bottleneck type based on metrics."""
        for btype, rules in BottleneckClassifier.BOTTLENECK_TYPES.items():
            if rules["conditions"](metrics):
                return btype
        return "BALANCED"
    
    @staticmethod
    def generate_signature(metrics: KernelMetrics) -> str:
        """Generate a hash signature for this kernel's characteristics."""
        bottleneck = BottleneckClassifier.classify(metrics)
        
        # Quantize metrics to reduce noise
        sm_bucket = int(metrics.sm_utilization / 10) * 10
        bw_bucket = int(metrics.bandwidth_percent / 10) * 10
        
        signature_str = f"{bottleneck}:sm_{sm_bucket}:bw_{bw_bucket}:{metrics.kernel_name[:10]}"
        return hashlib.md5(signature_str.encode()).hexdigest()[:8]


class MemorySystem:
    """Main knowledge base system."""
    
    def __init__(self, storage_path: str = None):
        # Use cross-platform temp directory if not specified
        if storage_path is None:
            storage_path = os.path.join(tempfile.gettempdir(), "ml_pgo_memory")
        
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory indexes (loaded from disk on init)
        self.signatures: Dict = self._load_or_create("signatures.json", {})
        self.patterns: Dict = self._load_or_create("patterns.json", self._default_patterns())
        self.hardware: Dict = self._load_or_create("hardware.json", self._default_hardware())
        self.case_studies: Dict = self._load_or_create("case_studies.json", {})
        self.learning_cache: Dict = self._load_or_create("learning_cache.json", {})
        
        logger.info(f"Memory system initialized: {len(self.signatures)} signatures, "
                   f"{len(self.case_studies)} case studies")
    
    def _load_or_create(self, filename: str, default: Dict) -> Dict:
        """Load from disk or create with defaults."""
        path = self.storage_path / filename
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
        return default
    
    def save(self):
        """Persist all data to disk."""
        (self.storage_path / "signatures.json").write_text(json.dumps(self.signatures, indent=2))
        (self.storage_path / "patterns.json").write_text(json.dumps(self.patterns, indent=2))
        (self.storage_path / "hardware.json").write_text(json.dumps(self.hardware, indent=2))
        (self.storage_path / "case_studies.json").write_text(json.dumps(self.case_studies, indent=2))
        (self.storage_path / "learning_cache.json").write_text(json.dumps(self.learning_cache, indent=2))
        logger.info("Memory system saved to disk")
    
    def lookup_similar_kernels(self, signature: str, top_k: int = 3) -> List[Tuple[str, Dict]]:
        """Find similar kernels in memory."""
        if signature not in self.signatures:
            return []
        
        current = self.signatures[signature]
        bottleneck = current.get("bottleneck_type", "UNKNOWN")
        
        # Find other kernels with same bottleneck type
        similar = []
        for sig, data in self.signatures.items():
            if sig != signature and data.get("bottleneck_type") == bottleneck:
                # Score by success rate of optimizations
                score = max([opt.get("success_rate", 0) for opt in data.get("applicable_optimizations", [])])
                similar.append((sig, score, data))
        
        # Sort by score and return top-k
        similar.sort(key=lambda x: x[1], reverse=True)
        return [(sig, data) for sig, _, data in similar[:top_k]]
    
    def get_optimizations_for_bottleneck(self, bottleneck_type: str, 
                                        hardware: str = "A100") -> List[OptimizationTechnique]:
        """Get applicable optimizations for a bottleneck type."""
        if bottleneck_type not in self.patterns:
            return []
        
        techniques = self.patterns[bottleneck_type].get("techniques", [])
        
        # Filter for this hardware
        applicable = [t for t in techniques 
                     if hardware in t.get("applicable_hardware", [])]
        
        # Sort by success_rate * expected_speedup / difficulty_score
        def score(t):
            difficulty_score = {"Easy": 1, "Medium": 2, "Hard": 3}.get(t.get("difficulty"), 2)
            speedup_avg = (t.get("expected_speedup_min", 1) + t.get("expected_speedup_max", 1)) / 2
            return (t.get("success_rate", 0) * speedup_avg) / difficulty_score
        
        applicable.sort(key=score, reverse=True)
        return applicable
    
    def register_kernel_signature(self, metrics: KernelMetrics, 
                                 bottleneck_type: str = None):
        """Register a new kernel signature."""
        if bottleneck_type is None:
            bottleneck_type = BottleneckClassifier.classify(metrics)
        
        signature = BottleneckClassifier.generate_signature(metrics)
        
        if signature not in self.signatures:
            self.signatures[signature] = {
                "kernel_name": metrics.kernel_name,
                "metrics": metrics.to_dict(),
                "bottleneck_type": bottleneck_type,
                "applicable_optimizations": [],
                "common_next_states": [],
                "seen_count": 0,
                "success_count": 0
            }
        
        self.signatures[signature]["seen_count"] += 1
        logger.info(f"Registered signature {signature} for {metrics.kernel_name}")
        return signature
    
    def record_case_study(self, study: CaseStudy):
        """Record results of an optimization."""
        self.case_studies[study.study_id] = study.to_dict()
        
        # Update signature statistics
        if study.input_signature in self.signatures:
            sig_data = self.signatures[study.input_signature]
            if study.success:
                sig_data["success_count"] = sig_data.get("success_count", 0) + 1
                
                # Update success rates for used techniques
                for technique in study.optimizations_applied:
                    for opt in sig_data.get("applicable_optimizations", []):
                        if opt.get("name") == technique:
                            old_rate = opt.get("success_rate", 0.5)
                            new_rate = (old_rate + 1.0) / 2  # Simple moving average
                            opt["success_rate"] = new_rate
        
        logger.info(f"Recorded case study {study.study_id} (speedup: {study.speedup:.2f}x)")
        self.save()
    
    def get_cache_key(self, metrics: KernelMetrics) -> str:
        """Get cache key for this kernel's analysis."""
        bottleneck = BottleneckClassifier.classify(metrics)
        return f"{bottleneck}:{metrics.kernel_name}"
    
    def get_cached_analysis(self, metrics: KernelMetrics) -> Optional[Dict]:
        """Retrieve cached analysis if available."""
        key = self.get_cache_key(metrics)
        return self.learning_cache.get(key)
    
    def cache_analysis(self, metrics: KernelMetrics, analysis: Dict):
        """Cache Claude's analysis to avoid recomputation."""
        key = self.get_cache_key(metrics)
        self.learning_cache[key] = {
            "metrics": metrics.to_dict(),
            "analysis": analysis,
            "timestamp": str(Path.cwd())
        }
        self.save()
    
    @staticmethod
    def _default_patterns() -> Dict:
        """Initialize with common optimization patterns."""
        return {
            "MEMORY_BOUND": {
                "conditions": "bandwidth_percent > 70 AND sm_utilization < 60",
                "techniques": [
                    {
                        "name": "shared_memory_tiling",
                        "expected_speedup_min": 1.5,
                        "expected_speedup_max": 2.5,
                        "difficulty": "Easy",
                        "tokens_baseline": 450,
                        "tokens_optimized": 200,
                        "success_rate": 0.92,
                        "applicable_hardware": ["A100", "H100", "L40", "V100"],
                        "pseudocode": "Use shared memory to cache frequently accessed data"
                    },
                    {
                        "name": "memory_coalescing",
                        "expected_speedup_min": 1.1,
                        "expected_speedup_max": 1.4,
                        "difficulty": "Medium",
                        "tokens_baseline": 500,
                        "tokens_optimized": 250,
                        "success_rate": 0.85,
                        "applicable_hardware": ["A100", "H100", "L40", "V100"],
                        "pseudocode": "Ensure consecutive threads access consecutive memory"
                    }
                ]
            },
            "COMPUTE_BOUND": {
                "conditions": "bandwidth_percent < 50 AND sm_utilization < 50",
                "techniques": [
                    {
                        "name": "increase_parallelism",
                        "expected_speedup_min": 1.2,
                        "expected_speedup_max": 1.8,
                        "difficulty": "Medium",
                        "tokens_baseline": 400,
                        "tokens_optimized": 180,
                        "success_rate": 0.88,
                        "applicable_hardware": ["A100", "H100", "L40", "V100"],
                        "pseudocode": "Increase thread block size or grid dimensions"
                    }
                ]
            },
            "LAUNCH_OVERHEAD": {
                "conditions": "sm_utilization < 30",
                "techniques": [
                    {
                        "name": "kernel_fusion",
                        "expected_speedup_min": 1.3,
                        "expected_speedup_max": 2.0,
                        "difficulty": "Hard",
                        "tokens_baseline": 600,
                        "tokens_optimized": 250,
                        "success_rate": 0.80,
                        "applicable_hardware": ["A100", "H100", "L40", "V100"],
                        "pseudocode": "Combine multiple kernels into single kernel"
                    }
                ]
            }
        }
    
    @staticmethod
    def _default_hardware() -> Dict:
        """Initialize with common GPU hardware profiles."""
        return {
            "A100": {
                "sm_count": 108,
                "memory_bandwidth": 2039,
                "max_threads_per_block": 1024,
                "tensor_ops_per_cycle": 312,
                "common_bottlenecks": ["MEMORY_BOUND", "LAUNCH_OVERHEAD"],
                "effective_techniques": ["shared_memory", "tensor_cores"]
            },
            "H100": {
                "sm_count": 132,
                "memory_bandwidth": 3352,
                "max_threads_per_block": 1024,
                "tensor_ops_per_cycle": 756,
                "common_bottlenecks": ["COMPUTE_BOUND"],
                "effective_techniques": ["tensor_cores", "async_copy"]
            },
            "L40": {
                "sm_count": 142,
                "memory_bandwidth": 864,
                "max_threads_per_block": 1024,
                "tensor_ops_per_cycle": 568,
                "common_bottlenecks": ["MEMORY_BOUND"],
                "effective_techniques": ["shared_memory", "nvlink"]
            },
            "V100": {
                "sm_count": 80,
                "memory_bandwidth": 900,
                "max_threads_per_block": 1024,
                "tensor_ops_per_cycle": 125,
                "common_bottlenecks": ["COMPUTE_BOUND", "MEMORY_BOUND"],
                "effective_techniques": ["tensor_cores", "shared_memory"]
            }
        }


# Convenience functions for integration
def create_memory_system(storage_path: str = "/tmp/ml_pgo_memory") -> MemorySystem:
    """Factory function to create/load memory system."""
    return MemorySystem(storage_path)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    memory = MemorySystem()
    
    # Example: Register a memory-bound kernel
    metrics = KernelMetrics(
        sm_utilization=45,
        bandwidth_percent=85,
        runtime_ms=50.0,
        kernel_name="matmul_kernel"
    )
    
    sig = memory.register_kernel_signature(metrics)
    print(f"Signature: {sig}")
    
    # Get optimizations
    optimizations = memory.get_optimizations_for_bottleneck("MEMORY_BOUND")
    print(f"Found {len(optimizations)} optimizations")
    for opt in optimizations:
        print(f"  - {opt['name']}: {opt['expected_speedup_min']}-{opt['expected_speedup_max']}x")
