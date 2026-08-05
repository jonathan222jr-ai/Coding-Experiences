"""
Helper Utility: Automated Benchmark & Profile Runner

Runs benchmarking and profiling in sequence, generates comparison reports.

Usage:
    from benchmark_runner import run_benchmark_pair
    
    run_benchmark_pair(
        baseline_script='baseline.py',
        optimized_script='optimized.py',
        output_dir='results/',
        profile=True
    )
"""

import subprocess
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict


class BenchmarkRunner:
    """Orchestrates benchmarking and profiling workflow."""
    
    def __init__(self, output_dir: str = 'benchmark_results'):
        """
        Initialize benchmark runner.
        
        Args:
            output_dir: Directory to store results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create timestamped subdirectory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.run_dir = self.output_dir / timestamp
        self.run_dir.mkdir(exist_ok=True)
        
        self.results = {}
    
    def run_script(self, script_path: str, description: str = "Run") -> Dict:
        """
        Run a Python script and capture output.
        
        Args:
            script_path: Path to Python script
            description: Label for this run
        
        Returns:
            dict with stdout and exit code
        """
        print(f"\n{'='*70}")
        print(f"{description}: {script_path}")
        print(f"{'='*70}")
        
        try:
            result = subprocess.run(
                ['python', script_path],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            return {
                'success': result.returncode == 0,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
            }
        
        except subprocess.TimeoutExpired:
            print(f"ERROR: Script timed out after 600 seconds")
            return {
                'success': False,
                'return_code': -1,
                'error': 'Timeout'
            }
        
        except Exception as e:
            print(f"ERROR: {e}")
            return {
                'success': False,
                'return_code': -1,
                'error': str(e)
            }
    
    def profile_script(self, script_path: str, output_csv: str, 
                      description: str = "Profile") -> Dict:
        """
        Profile a script using DrGPUM.
        
        Args:
            script_path: Path to Python script
            output_csv: Output CSV filename
            description: Label for this profile
        
        Returns:
            dict with profiling results
        """
        print(f"\n{'='*70}")
        print(f"{description}: {script_path}")
        print(f"{'='*70}")
        
        output_path = self.run_dir / output_csv
        
        try:
            # Check if drg is available
            subprocess.run(['drg', '--version'], 
                         capture_output=True, 
                         timeout=10,
                         check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("WARNING: DrGPUM (drg) not found. Skipping profiling.")
            print("To use profiling, ensure DrGPUM is installed and in PATH:")
            print("  export DrGPUM_PATH=<path-to-drgpum>/gvprof")
            print("  export PATH=${DrGPUM_PATH}/bin:$PATH")
            return {
                'success': False,
                'error': 'DrGPUM not available'
            }
        
        try:
            cmd = ['drg', '-o', str(output_path), 'python', script_path]
            print(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            if result.returncode == 0 and output_path.exists():
                print(f"\n✓ Profile saved to: {output_path}")
                return {
                    'success': True,
                    'output_path': str(output_path),
                    'stdout': result.stdout,
                }
            else:
                return {
                    'success': False,
                    'return_code': result.returncode,
                    'error': 'Profile generation failed'
                }
        
        except subprocess.TimeoutExpired:
            print(f"ERROR: Profiling timed out after 600 seconds")
            return {
                'success': False,
                'error': 'Timeout'
            }
        
        except Exception as e:
            print(f"ERROR: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def run_benchmark_pair(self, baseline_script: str, optimized_script: str,
                          profile: bool = True) -> Dict:
        """
        Run baseline and optimized benchmarks, optionally with profiling.
        
        Args:
            baseline_script: Path to baseline Python script
            optimized_script: Path to optimized Python script
            profile: Whether to run DrGPUM profiling
        
        Returns:
            dict with all results
        """
        print(f"\n{'#'*70}")
        print("BENCHMARK RUNNER: Baseline vs Optimized")
        print(f"{'#'*70}")
        print(f"Output directory: {self.run_dir}")
        
        # Run baseline
        print("\n" + "="*70)
        print("PHASE 1: BASELINE")
        print("="*70)
        baseline_result = self.run_script(baseline_script, "Run baseline")
        self.results['baseline_run'] = baseline_result
        
        # Profile baseline (if requested)
        if profile:
            profile_result = self.profile_script(
                baseline_script,
                'baseline_profile.csv',
                'Profile baseline'
            )
            self.results['baseline_profile'] = profile_result
        
        # Run optimized
        print("\n" + "="*70)
        print("PHASE 2: OPTIMIZED")
        print("="*70)
        optimized_result = self.run_script(optimized_script, "Run optimized")
        self.results['optimized_run'] = optimized_result
        
        # Profile optimized (if requested)
        if profile:
            profile_result = self.profile_script(
                optimized_script,
                'optimized_profile.csv',
                'Profile optimized'
            )
            self.results['optimized_profile'] = profile_result
        
        # Generate summary
        self._generate_summary()
        
        return self.results
    
    def _generate_summary(self):
        """Generate and save summary report."""
        summary_path = self.run_dir / 'summary.json'
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'output_dir': str(self.run_dir),
            'results': self.results,
        }
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n{'='*70}")
        print("BENCHMARK SUMMARY")
        print(f"{'='*70}")
        print(f"Results saved to: {summary_path}")
        print(f"\nTo compare profiles (if generated):")
        print(f"  python helpers/parse_drgpum_csv.py \\")
        print(f"    {self.run_dir}/baseline_profile.csv \\")
        print(f"    {self.run_dir}/optimized_profile.csv")


def run_benchmark_pair(baseline_script: str, optimized_script: str,
                      output_dir: str = 'benchmark_results',
                      profile: bool = True) -> Dict:
    """
    Convenience function to run a benchmark pair.
    
    Args:
        baseline_script: Path to baseline script
        optimized_script: Path to optimized script
        output_dir: Output directory for results
        profile: Whether to use DrGPUM profiling
    
    Returns:
        dict with all results
    
    Example:
        results = run_benchmark_pair(
            'baseline_matmul.py',
            'optimized_matmul.py',
            profile=True
        )
    """
    runner = BenchmarkRunner(output_dir=output_dir)
    return runner.run_benchmark_pair(baseline_script, optimized_script, profile=profile)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python benchmark_runner.py baseline.py optimized.py [--no-profile]")
        sys.exit(1)
    
    baseline = sys.argv[1]
    optimized = sys.argv[2]
    profile = '--no-profile' not in sys.argv
    
    results = run_benchmark_pair(baseline, optimized, profile=profile)
    
    print(f"\n{'='*70}")
    print("RESULTS SAVED")
    print(f"{'='*70}")
    print(f"Success: Baseline={results['baseline_run']['success']}, "
          f"Optimized={results['optimized_run']['success']}")
