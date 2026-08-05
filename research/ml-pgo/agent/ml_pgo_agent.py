#!/usr/bin/env python3
"""
ML-PGO Agent with Claude API Integration

Main orchestrator for the three-skill pipeline:
1. Profile Analysis (understand bottlenecks)
2. Optimization Suggestion (recommend fixes)
3. Benchmark Validation (measure improvements)

Usage:
    python ml_pgo_agent.py --api-key <YOUR_API_KEY> --baseline profile.csv
    python ml_pgo_agent.py --api-key <YOUR_API_KEY> --baseline baseline.csv --optimized optimized.csv
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import anthropic

# Import helper modules
sys.path.insert(0, str(Path(__file__).parent))
from helpers.parse_drgpum_csv import parse_profile, find_bottlenecks, compare_profiles, print_profile, print_comparison


class MLPGOAgent:
    """
    ML-PGO Agent powered by Claude API.
    
    Orchestrates the complete workflow:
    1. Parse profiling data
    2. Analyze with Claude to identify bottlenecks
    3. Get optimization suggestions from Claude
    4. Validate improvements (if before/after profiles available)
    """
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        """
        Initialize the agent with Claude API credentials.
        
        Args:
            api_key: Anthropic API key
            model: Claude model to use (default: Sonnet 4.6)
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.conversation_history = []
    
    def _query_claude(self, user_message: str, system_prompt: str = None) -> str:
        """
        Send a message to Claude and get a response.
        
        Args:
            user_message: The user's message/query
            system_prompt: Optional system prompt to override default
        
        Returns:
            Claude's response text
        """
        messages = self.conversation_history + [{"role": "user", "content": user_message}]
        
        system = system_prompt or """You are an expert GPU optimization engineer specializing in 
ML-PGO (Profile-Guided Optimization). You analyze profiling data, identify bottlenecks, and 
provide actionable optimization recommendations. Be specific, cite metrics from the data, 
and rank suggestions by impact/effort ratio. Keep responses concise but thorough."""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=system,
            messages=messages
        )
        
        assistant_message = response.content[0].text
        
        # Store in conversation history for context
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": assistant_message})
        
        return assistant_message
    
    def analyze_profile(self, csv_path: str) -> Dict[str, Any]:
        """
        SKILL 1: Analyze GPU profile using Claude.
        
        Args:
            csv_path: Path to DrGPUM CSV output
        
        Returns:
            Dictionary with analysis results
        """
        print("\n" + "="*70)
        print("SKILL 1: PROFILE ANALYSIS")
        print("="*70)
        
        # Parse the profile locally
        profile = parse_profile(csv_path)
        print_profile(profile, verbose=True)
        
        # Get bottlenecks
        bottlenecks = find_bottlenecks(profile)
        
        # Prepare data for Claude
        profile_summary = {
            "total_runtime_ms": profile.total_runtime(),
            "num_kernels": len(profile.kernels),
            "top_kernels": [
                {
                    "name": k.name,
                    "runtime_ms": k.runtime_ms,
                    "sm_utilization": k.sm_utilization,
                    "memory_bandwidth": k.memory_bandwidth,
                    "bottleneck_type": k.classify_bottleneck()
                }
                for k, _ in bottlenecks[:5]
            ],
            "bottleneck_summary": profile.get_bottleneck_summary()
        }
        
        # Query Claude for analysis
        analysis_prompt = f"""
Analyze this GPU profiling data and provide a detailed diagnosis:

Profile Data:
{json.dumps(profile_summary, indent=2)}

Please provide:
1. Summary of main bottlenecks
2. Kernel-by-kernel analysis of top 5 slowest kernels
3. Root cause diagnosis for each bottleneck type
4. Critical observations that should guide optimization
5. Any red flags or unusual patterns in the data

Be specific and cite the metrics that support your conclusions.
"""
        
        analysis = self._query_claude(analysis_prompt)
        
        print("\n" + "-"*70)
        print("CLAUDE'S ANALYSIS:")
        print("-"*70)
        print(analysis)
        
        return {
            "profile_summary": profile_summary,
            "claude_analysis": analysis,
            "profile_object": profile
        }
    
    def suggest_optimizations(self, analysis_result: Dict[str, Any], focus_kernel: Optional[str] = None) -> Dict[str, str]:
        """
        SKILL 2: Suggest optimizations using Claude.
        
        Args:
            analysis_result: Output from analyze_profile()
            focus_kernel: Optional specific kernel to focus on
        
        Returns:
            Dictionary with optimization suggestions
        """
        print("\n" + "="*70)
        print("SKILL 2: OPTIMIZATION SUGGESTIONS")
        print("="*70)
        
        profile_summary = analysis_result["profile_summary"]
        
        suggestion_prompt = f"""
Based on the profile analysis, provide specific optimization recommendations.

Profile Summary:
{json.dumps(profile_summary, indent=2)}

For each major bottleneck:
1. Identify the SPECIFIC optimization technique
2. Estimate the expected speedup (x% or x.x times)
3. Rate difficulty (Easy/Medium/Hard)
4. Explain why this optimization targets the root cause
5. Provide pseudocode or example kernel pattern if applicable

Focus on high-impact, implementable optimizations that address the actual bottlenecks.
{f'Focus particularly on: {focus_kernel}' if focus_kernel else ''}

Rank suggestions by Impact/Effort ratio (highest first).
"""
        
        suggestions = self._query_claude(suggestion_prompt)
        
        print("\n" + "-"*70)
        print("CLAUDE'S OPTIMIZATION SUGGESTIONS:")
        print("-"*70)
        print(suggestions)
        
        return {
            "suggestions": suggestions,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }
    
    def validate_results(self, baseline_csv: str, optimized_csv: str) -> Dict[str, Any]:
        """
        SKILL 3: Validate optimization results using Claude.
        
        Args:
            baseline_csv: Path to baseline profile
            optimized_csv: Path to optimized profile
        
        Returns:
            Dictionary with validation results and Claude's assessment
        """
        print("\n" + "="*70)
        print("SKILL 3: BENCHMARK VALIDATION")
        print("="*70)
        
        # Compare profiles
        comparison = compare_profiles(baseline_csv, optimized_csv)
        print_comparison(comparison)
        
        # Prepare comparison data for Claude
        comparison_summary = {
            "overall_speedup": comparison["overall"]["overall_speedup"],
            "baseline_total_ms": comparison["overall"]["baseline_total_time_ms"],
            "optimized_total_ms": comparison["overall"]["optimized_total_time_ms"],
            "kernel_results": []
        }
        
        for kernel_name, metrics in comparison["kernels"].items():
            comparison_summary["kernel_results"].append({
                "kernel": kernel_name,
                "speedup": metrics["speedup"],
                "baseline_ms": metrics["baseline_time_ms"],
                "optimized_ms": metrics["optimized_time_ms"],
                "baseline_bottleneck": metrics["baseline_bottleneck"],
                "optimized_bottleneck": metrics["optimized_bottleneck"],
                "bottleneck_changed": metrics["baseline_bottleneck"] != metrics["optimized_bottleneck"]
            })
        
        # Query Claude for validation assessment
        validation_prompt = f"""
Analyze the optimization results and validate the improvements:

Comparison Data:
{json.dumps(comparison_summary, indent=2)}

Please provide:
1. Overall Assessment: Was the optimization successful?
2. Speedup Evaluation: Is the speedup meaningful (>5% is usually worth it)?
3. Bottleneck Shift Analysis: Did we successfully shift bottleneck types?
4. Per-Kernel Review: Which kernels improved the most? Any regressions?
5. Recommendations: 
   - Should we stop and consider the optimization complete?
   - Are there opportunities for further optimization?
   - Any signs of diminishing returns?
6. Quality Metrics: Are the improvements stable and reproducible?

Be critical but fair in your assessment. Cite specific numbers.
"""
        
        assessment = self._query_claude(validation_prompt)
        
        print("\n" + "-"*70)
        print("CLAUDE'S VALIDATION ASSESSMENT:")
        print("-"*70)
        print(assessment)
        
        return {
            "comparison": comparison,
            "comparison_summary": comparison_summary,
            "claude_assessment": assessment,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }
    
    def run_full_pipeline(self, baseline_csv: str, optimized_csv: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the complete ML-PGO pipeline.
        
        Args:
            baseline_csv: Path to baseline profile
            optimized_csv: Optional path to optimized profile
        
        Returns:
            Complete pipeline results
        """
        results = {}
        
        # Step 1: Analyze baseline profile
        print("\n" + "█"*70)
        print("█  STEP 1: ANALYZING BASELINE PROFILE")
        print("█"*70)
        analysis = self.analyze_profile(baseline_csv)
        results["analysis"] = analysis
        
        # Step 2: Suggest optimizations
        print("\n" + "█"*70)
        print("█  STEP 2: GENERATING OPTIMIZATION SUGGESTIONS")
        print("█"*70)
        suggestions = self.suggest_optimizations(analysis)
        results["suggestions"] = suggestions
        
        # Step 3: Validate if optimized profile provided
        if optimized_csv:
            print("\n" + "█"*70)
            print("█  STEP 3: VALIDATING OPTIMIZED PROFILE")
            print("█"*70)
            validation = self.validate_results(baseline_csv, optimized_csv)
            results["validation"] = validation
        else:
            print("\n" + "█"*70)
            print("█  No optimized profile provided - skipping validation step")
            print("█"*70)
        
        # Save results to JSON
        self._save_results(results)
        
        return results
    
    def _save_results(self, results: Dict[str, Any], output_file: str = "pgo_results.json"):
        """Save pipeline results to JSON file."""
        output_path = Path(output_file)
        
        # Make results JSON-serializable
        serializable_results = {}
        for key, value in results.items():
            if key == "analysis":
                serializable_results[key] = {
                    "profile_summary": value["profile_summary"],
                    "claude_analysis": value["claude_analysis"]
                }
            elif key == "suggestions":
                serializable_results[key] = value
            elif key == "validation":
                serializable_results[key] = {
                    "comparison_summary": value["comparison_summary"],
                    "claude_assessment": value["claude_assessment"],
                    "timestamp": value["timestamp"]
                }
        
        with open(output_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"\n✓ Results saved to: {output_path.absolute()}")


def main():
    parser = argparse.ArgumentParser(
        description="ML-PGO Agent: AI-powered GPU optimization pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a baseline profile
  python ml_pgo_agent.py --api-key sk-... --baseline profile.csv
  
  # Analyze baseline and validate optimized version
  python ml_pgo_agent.py --api-key sk-... --baseline baseline.csv --optimized optimized.csv
  
  # Use API key from environment variable
  export ANTHROPIC_API_KEY=sk-...
  python ml_pgo_agent.py --baseline profile.csv
        """
    )
    
    parser.add_argument(
        "--api-key",
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)"
    )
    parser.add_argument(
        "--baseline",
        required=True,
        help="Path to baseline DrGPUM profile CSV"
    )
    parser.add_argument(
        "--optimized",
        help="Path to optimized profile CSV (optional, for validation)"
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-6",
        help="Claude model to use (default: claude-3-5-sonnet-20241022)"
    )
    parser.add_argument(
        "--output",
        default="pgo_results.json",
        help="Output JSON file for results (default: pgo_results.json)"
    )
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: No API key provided.")
        print("   Use --api-key or set ANTHROPIC_API_KEY environment variable")
        sys.exit(1)
    
    # Validate input files
    if not Path(args.baseline).exists():
        print(f"❌ Error: Baseline file not found: {args.baseline}")
        sys.exit(1)
    
    if args.optimized and not Path(args.optimized).exists():
        print(f"❌ Error: Optimized file not found: {args.optimized}")
        sys.exit(1)
    
    # Create agent and run pipeline
    print("🚀 Initializing ML-PGO Agent with Claude API...")
    agent = MLPGOAgent(api_key=api_key, model=args.model)
    
    results = agent.run_full_pipeline(
        baseline_csv=args.baseline,
        optimized_csv=args.optimized
    )
    
    print("\n" + "█"*70)
    print("█  PIPELINE COMPLETE")
    print("█"*70)


if __name__ == "__main__":
    main()
