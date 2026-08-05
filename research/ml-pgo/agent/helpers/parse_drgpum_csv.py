"""
Helper Utility: Parse DrGPUM CSV Output

Converts DrGPUM CSV profiling output into structured Python objects
for easier processing and analysis.

Usage:
    from parse_drgpum_csv import parse_profile, find_bottlenecks
    
    profile = parse_profile('baseline_profile.csv')
    bottlenecks = find_bottlenecks(profile)
    print(bottlenecks)
"""

import csv
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class Kernel:
    """Represents a single kernel from profile output."""
    name: str
    runtime_ms: float
    sm_utilization: float  # percentage
    memory_bandwidth: float  # percentage
    
    def __str__(self):
        return (f"Kernel({self.name}): "
                f"time={self.runtime_ms:.1f}ms, "
                f"SM={self.sm_utilization:.0f}%, "
                f"BW={self.memory_bandwidth:.0f}%")
    
    def classify_bottleneck(self) -> str:
        """Classify kernel bottleneck type based on metrics."""
        if self.memory_bandwidth > 70 and self.sm_utilization < 60:
            return "MEMORY_BOUND"
        elif self.memory_bandwidth < 50 and self.sm_utilization < 50:
            return "COMPUTE_BOUND"
        elif self.sm_utilization < 30:
            return "LAUNCH_OVERHEAD"
        else:
            return "BALANCED"


@dataclass
class Profile:
    """Represents complete profiling data."""
    kernels: List[Kernel]
    
    def total_runtime(self) -> float:
        """Total runtime across all kernels."""
        return sum(k.runtime_ms for k in self.kernels)
    
    def get_top_kernels(self, n: int = 5) -> List[Kernel]:
        """Get top N slowest kernels."""
        return sorted(self.kernels, key=lambda k: k.runtime_ms, reverse=True)[:n]
    
    def get_bottleneck_summary(self) -> Dict[str, int]:
        """Count kernels by bottleneck type."""
        summary = {}
        for kernel in self.kernels:
            bottleneck_type = kernel.classify_bottleneck()
            summary[bottleneck_type] = summary.get(bottleneck_type, 0) + 1
        return summary


def parse_profile(csv_filename: str) -> Profile:
    """
    Parse DrGPUM CSV output file.
    
    Expected CSV format:
        kernel_name,runtime_ms,sm_utilization_%,memory_bandwidth_%
        matmul_kernel,50.0,45,85
        softmax_kernel,25.0,30,20
    
    Args:
        csv_filename: Path to DrGPUM output CSV
    
    Returns:
        Profile object with parsed kernels
    """
    kernels = []
    
    try:
        with open(csv_filename, 'r') as f:
            reader = csv.DictReader(f)
            
            if reader.fieldnames is None:
                raise ValueError(f"Empty file: {csv_filename}")
            
            for row in reader:
                try:
                    kernel = Kernel(
                        name=row['kernel_name'].strip(),
                        runtime_ms=float(row['runtime_ms']),
                        sm_utilization=float(row['sm_utilization_%']),
                        memory_bandwidth=float(row['memory_bandwidth_%'])
                    )
                    kernels.append(kernel)
                except (ValueError, KeyError) as e:
                    print(f"Warning: Skipping row {row} - {e}")
                    continue
    
    except FileNotFoundError:
        raise FileNotFoundError(f"Profile file not found: {csv_filename}")
    
    if not kernels:
        raise ValueError(f"No valid kernels found in {csv_filename}")
    
    return Profile(kernels=kernels)


def find_bottlenecks(profile: Profile) -> List[Tuple[Kernel, str]]:
    """
    Identify bottleneck kernels in profile.
    
    Returns:
        List of (kernel, bottleneck_type) tuples, sorted by runtime
    """
    bottlenecks = []
    
    for kernel in profile.kernels:
        bottleneck_type = kernel.classify_bottleneck()
        bottlenecks.append((kernel, bottleneck_type))
    
    # Sort by runtime (most critical first)
    bottlenecks.sort(key=lambda x: x[0].runtime_ms, reverse=True)
    
    return bottlenecks


def compare_profiles(baseline_csv: str, optimized_csv: str) -> Dict:
    """
    Compare baseline and optimized profiles.
    
    Args:
        baseline_csv: Path to baseline profile
        optimized_csv: Path to optimized profile
    
    Returns:
        Comparison report with metrics
    """
    baseline = parse_profile(baseline_csv)
    optimized = parse_profile(optimized_csv)
    
    # Find matching kernels
    baseline_by_name = {k.name: k for k in baseline.kernels}
    optimized_by_name = {k.name: k for k in optimized.kernels}
    
    comparison = {
        'kernels': {},
        'overall': {}
    }
    
    # Compare each kernel
    for kernel_name in baseline_by_name:
        if kernel_name in optimized_by_name:
            b_kernel = baseline_by_name[kernel_name]
            o_kernel = optimized_by_name[kernel_name]
            
            speedup = b_kernel.runtime_ms / o_kernel.runtime_ms
            sm_change = o_kernel.sm_utilization - b_kernel.sm_utilization
            bw_change = o_kernel.memory_bandwidth - b_kernel.memory_bandwidth
            
            comparison['kernels'][kernel_name] = {
                'baseline_time_ms': b_kernel.runtime_ms,
                'optimized_time_ms': o_kernel.runtime_ms,
                'speedup': speedup,
                'baseline_bottleneck': b_kernel.classify_bottleneck(),
                'optimized_bottleneck': o_kernel.classify_bottleneck(),
                'sm_utilization_change': sm_change,
                'memory_bandwidth_change': bw_change,
            }
    
    # Overall stats
    comparison['overall'] = {
        'baseline_total_time_ms': baseline.total_runtime(),
        'optimized_total_time_ms': optimized.total_runtime(),
        'overall_speedup': baseline.total_runtime() / optimized.total_runtime(),
    }
    
    return comparison


def print_profile(profile: Profile, verbose: bool = False):
    """Pretty-print profile summary."""
    print("\n" + "=" * 70)
    print("PROFILING SUMMARY")
    print("=" * 70)
    
    print(f"\nTotal Runtime: {profile.total_runtime():.2f} ms")
    print(f"Total Kernels: {len(profile.kernels)}")
    
    print("\nBottleneck Types:")
    for bottleneck_type, count in profile.get_bottleneck_summary().items():
        print(f"  • {bottleneck_type}: {count}")
    
    print("\nTop 5 Slowest Kernels:")
    for i, kernel in enumerate(profile.get_top_kernels(5), 1):
        bottleneck = kernel.classify_bottleneck()
        pct = (kernel.runtime_ms / profile.total_runtime()) * 100
        print(f"  {i}. {kernel.name:30s} | {kernel.runtime_ms:6.1f}ms ({pct:5.1f}%) | {bottleneck}")
    
    if verbose:
        print("\nDetailed Metrics:")
        for kernel in profile.kernels:
            print(f"\n  {kernel.name}:")
            print(f"    • Runtime: {kernel.runtime_ms:.2f} ms")
            print(f"    • SM Utilization: {kernel.sm_utilization:.1f}%")
            print(f"    • Memory Bandwidth: {kernel.memory_bandwidth:.1f}%")
            print(f"    • Bottleneck: {kernel.classify_bottleneck()}")


def print_comparison(comparison: Dict):
    """Pretty-print comparison report."""
    print("\n" + "=" * 70)
    print("OPTIMIZATION COMPARISON REPORT")
    print("=" * 70)
    
    print(f"\nOverall Application Speedup: {comparison['overall']['overall_speedup']:.2f}x")
    print(f"  Baseline: {comparison['overall']['baseline_total_time_ms']:.2f} ms")
    print(f"  Optimized: {comparison['overall']['optimized_total_time_ms']:.2f} ms")
    
    print("\nPer-Kernel Analysis:")
    print("-" * 70)
    print(f"{'Kernel':<30s} | {'Baseline':>10s} | {'Optimized':>10s} | {'Speedup':>8s}")
    print("-" * 70)
    
    for kernel_name, metrics in comparison['kernels'].items():
        baseline_time = metrics['baseline_time_ms']
        optimized_time = metrics['optimized_time_ms']
        speedup = metrics['speedup']
        
        print(f"{kernel_name:<30s} | {baseline_time:>9.2f}ms | {optimized_time:>9.2f}ms | {speedup:>7.2f}x")
    
    print("\nBottleneck Reclassification:")
    print("-" * 70)
    for kernel_name, metrics in comparison['kernels'].items():
        baseline_type = metrics['baseline_bottleneck']
        optimized_type = metrics['optimized_bottleneck']
        changed = "✓ FIXED" if baseline_type != optimized_type else ""
        
        print(f"{kernel_name:<30s}: {baseline_type:15s} → {optimized_type:15s} {changed}")
    
    print("\nMetric Changes:")
    print("-" * 70)
    for kernel_name, metrics in comparison['kernels'].items():
        sm_change = metrics['sm_utilization_change']
        bw_change = metrics['memory_bandwidth_change']
        
        sm_str = f"+{sm_change:.0f}pp" if sm_change > 0 else f"{sm_change:.0f}pp"
        bw_str = f"+{bw_change:.0f}pp" if bw_change > 0 else f"{bw_change:.0f}pp"
        
        print(f"{kernel_name:<30s}: SM {sm_str:>6s}, BW {bw_str:>6s}")


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python parse_drgpum_csv.py baseline.csv")
        print("  python parse_drgpum_csv.py baseline.csv optimized.csv")
        sys.exit(1)
    
    if len(sys.argv) == 2:
        # Single profile
        baseline_file = sys.argv[1]
        profile = parse_profile(baseline_file)
        print_profile(profile, verbose=True)
        
        bottlenecks = find_bottlenecks(profile)
        print("\nBottlenecks (sorted by impact):")
        for kernel, bottleneck_type in bottlenecks:
            print(f"  • {kernel.name}: {bottleneck_type}")
    
    else:
        # Compare two profiles
        baseline_file = sys.argv[1]
        optimized_file = sys.argv[2]
        
        comparison = compare_profiles(baseline_file, optimized_file)
        print_comparison(comparison)
