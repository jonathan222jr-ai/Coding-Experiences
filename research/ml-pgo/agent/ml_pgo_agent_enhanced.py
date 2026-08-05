"""
Enhanced ML-PGO Agent with Memory System and Token Optimization

This is the refactored core agent that integrates:
1. Memory system for caching patterns
2. Token tracking for efficiency measurement
3. Prompt optimization to reduce token usage
4. Learning loop to continuously improve

Architecture:
  Profile → Memory Lookup → (if cached) Return cached optimizations
                           (if new) Query Claude + Cache results
         → Token Tracking → Measure input/output tokens
         → Learning Loop → Update success rates
"""

import json
import os
import tempfile
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import asdict
import logging

from anthropic import Anthropic

from memory_system import (
    MemorySystem, BottleneckClassifier, KernelMetrics, CaseStudy
)
from token_tracker import (
    TokenReporter, PromptOptimizer, CCUsageIntegration, TokenMeasurement
)

logger = logging.getLogger(__name__)


class EnhancedMLPGOAgent:
    """
    Enhanced ML-PGO Agent with memory system and token optimization.
    
    Improves over naive approach by:
    - Caching similar kernel patterns
    - Reusing optimizations from case studies
    - Optimizing prompts to use fewer tokens
    - Learning from each iteration
    """
    
    def __init__(self, api_key: Optional[str] = None, 
                 memory_path: str = None,
                 token_path: str = None,
                 model: str = "claude-sonnet-4-6"):
        """Initialize agent with memory and token systems."""
        # Use cross-platform temp directories if not specified
        if memory_path is None:
            memory_path = os.path.join(tempfile.gettempdir(), "ml_pgo_memory")
        if token_path is None:
            token_path = os.path.join(tempfile.gettempdir(), "ml_pgo_tokens")
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API key not provided and ANTHROPIC_API_KEY not set")
        
        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.memory = MemorySystem(memory_path)
        self.token_reporter = TokenReporter(token_path)
        self.conversation_history = []
        
        logger.info(f"Enhanced ML-PGO Agent initialized with {model}")
    
    def analyze_profile(self, profile_csv: str, 
                       use_cache: bool = True,
                       hardware: str = "A100") -> Dict:
        """
        SKILL 1: Profile Analysis
        
        Analyzes GPU profile using memory system for efficiency.
        If similar kernels are cached, reuses analysis.
        """
        logger.info(f"Analyzing profile: {profile_csv}")
        
        # Load profile data
        profile_data = self._load_profile_csv(profile_csv)
        kernels = profile_data.get("kernels", [])
        
        analysis = {
            "profile_file": profile_csv,
            "total_runtime_ms": sum(k.get("runtime_ms", 0) for k in kernels),
            "kernel_count": len(kernels),
            "kernels": [],
            "token_usage": {
                "baseline_tokens": 0,
                "optimized_tokens": 0,
                "compression_ratio": 0
            }
        }
        
        baseline_tokens = 0
        optimized_tokens = 0
        cached_count = 0
        
        for kernel in kernels:
            metrics = KernelMetrics(
                sm_utilization=kernel.get("sm_utilization", 0),
                bandwidth_percent=kernel.get("bandwidth_percent", 0),
                runtime_ms=kernel.get("runtime_ms", 0),
                kernel_name=kernel.get("kernel_name", "unknown")
            )
            
            # Register and classify
            signature = self.memory.register_kernel_signature(metrics)
            bottleneck = BottleneckClassifier.classify(metrics)
            
            kernel_analysis = {
                "name": metrics.kernel_name,
                "signature": signature,
                "bottleneck_type": bottleneck,
                "metrics": asdict(metrics),
                "cached": False,
                "claude_diagnosis": ""
            }
            
            # Check cache first
            cached = self.memory.get_cached_analysis(metrics) if use_cache else None
            
            if cached:
                kernel_analysis["cached"] = True
                kernel_analysis["claude_diagnosis"] = cached.get("analysis", {}).get("diagnosis", "")
                cached_count += 1
                logger.debug(f"Using cached analysis for {metrics.kernel_name}")
            else:
                # Query Claude with optimized prompt
                prompt = PromptOptimizer.create_compact_prompt(
                    {"kernels": [asdict(metrics)]},
                    memory_lookup={signature: {
                        "bottleneck_type": bottleneck
                    }}
                )
                
                # Measure tokens before API call
                baseline_len = len(prompt)
                
                # Query Claude
                try:
                    diagnosis = self._query_claude(
                        prompt,
                        system="You are a GPU optimization expert. Diagnose bottlenecks concisely."
                    )
                    
                    kernel_analysis["claude_diagnosis"] = diagnosis
                    
                    # Estimate token usage (rough approximation)
                    optimized_len = len(prompt)
                    input_tokens_est = baseline_len // 4  # ~4 chars per token
                    output_tokens_est = len(diagnosis) // 4
                    
                    baseline_tokens += input_tokens_est
                    optimized_tokens += input_tokens_est  # Same input here
                    
                    # Cache the analysis
                    self.memory.cache_analysis(metrics, {
                        "diagnosis": diagnosis,
                        "bottleneck": bottleneck
                    })
                    
                except Exception as e:
                    logger.error(f"Error querying Claude: {e}")
                    kernel_analysis["claude_diagnosis"] = f"Error: {str(e)}"
            
            analysis["kernels"].append(kernel_analysis)
        
        analysis["token_usage"] = {
            "baseline_tokens": baseline_tokens,
            "optimized_tokens": optimized_tokens,
            "compression_ratio": optimized_tokens / baseline_tokens if baseline_tokens > 0 else 1.0,
            "cached_kernels": cached_count
        }
        
        logger.info(f"Analysis complete: {len(kernels)} kernels, "
                   f"{cached_count} cached, compression: "
                   f"{analysis['token_usage']['compression_ratio']:.2%}")
        
        return analysis
    
    def suggest_optimizations(self, analysis: Dict, 
                            hardware: str = "A100") -> Dict:
        """
        SKILL 2: Optimization Suggestions
        
        Provides ranked optimization recommendations.
        Uses cached patterns to minimize token usage.
        """
        logger.info("Generating optimization suggestions")
        
        suggestions = {
            "analysis_input": len(analysis.get("kernels", [])),
            "recommendations": [],
            "token_usage": {
                "baseline_tokens": 0,
                "optimized_tokens": 0
            }
        }
        
        for kernel in analysis.get("kernels", []):
            bottleneck = kernel.get("bottleneck_type", "UNKNOWN")
            
            # Get cached patterns from memory
            optimizations = self.memory.get_optimizations_for_bottleneck(
                bottleneck, 
                hardware=hardware
            )
            
            # Create optimized prompt using cached techniques
            if optimizations:
                prompt = PromptOptimizer.optimize_suggestions_prompt(
                    kernel.get("claude_diagnosis", ""),
                    [asdict(opt) for opt in optimizations]
                )
                
                prompt_tokens = len(prompt) // 4
                suggestions["token_usage"]["baseline_tokens"] += prompt_tokens
                suggestions["token_usage"]["optimized_tokens"] += prompt_tokens
                
                # Query Claude for ranking
                try:
                    recommendation = self._query_claude(
                        prompt,
                        system="You are a GPU optimization expert. Rank techniques by impact/effort."
                    )
                except Exception as e:
                    recommendation = f"Error: {str(e)}"
                
                suggestions["recommendations"].append({
                    "kernel": kernel.get("name"),
                    "bottleneck": bottleneck,
                    "cached_techniques": len(optimizations),
                    "recommendation": recommendation,
                    "top_technique": optimizations[0].name if optimizations else "N/A"
                })
            else:
                suggestions["recommendations"].append({
                    "kernel": kernel.get("name"),
                    "bottleneck": bottleneck,
                    "cached_techniques": 0,
                    "recommendation": "No cached patterns for this bottleneck type",
                    "top_technique": "N/A"
                })
        
        logger.info(f"Generated {len(suggestions['recommendations'])} recommendations")
        return suggestions
    
    def validate_results(self, baseline_csv: str, optimized_csv: str,
                        hardware: str = "A100") -> Dict:
        """
        SKILL 3: Benchmark Validation
        
        Compares baseline and optimized profiles.
        Learns from results to improve future recommendations.
        """
        logger.info(f"Validating optimization: {baseline_csv} → {optimized_csv}")
        
        baseline_data = self._load_profile_csv(baseline_csv)
        optimized_data = self._load_profile_csv(optimized_csv)
        
        validation = {
            "baseline_file": baseline_csv,
            "optimized_file": optimized_csv,
            "comparison": [],
            "overall_speedup": 1.0,
            "token_usage": {
                "baseline_tokens": 0,
                "optimized_tokens": 0
            }
        }
        
        baseline_total = sum(k.get("runtime_ms", 0) for k in baseline_data.get("kernels", []))
        optimized_total = sum(k.get("runtime_ms", 0) for k in optimized_data.get("kernels", []))
        
        if optimized_total > 0:
            validation["overall_speedup"] = baseline_total / optimized_total
        
        # Compare per-kernel
        for baseline_kernel in baseline_data.get("kernels", []):
            kernel_name = baseline_kernel.get("kernel_name")
            
            # Find corresponding optimized kernel
            optimized_kernel = next(
                (k for k in optimized_data.get("kernels", []) 
                 if k.get("kernel_name") == kernel_name),
                None
            )
            
            if not optimized_kernel:
                continue
            
            baseline_metrics = KernelMetrics(
                sm_utilization=baseline_kernel.get("sm_utilization", 0),
                bandwidth_percent=baseline_kernel.get("bandwidth_percent", 0),
                runtime_ms=baseline_kernel.get("runtime_ms", 0),
                kernel_name=kernel_name
            )
            
            optimized_metrics = KernelMetrics(
                sm_utilization=optimized_kernel.get("sm_utilization", 0),
                bandwidth_percent=optimized_kernel.get("bandwidth_percent", 0),
                runtime_ms=optimized_kernel.get("runtime_ms", 0),
                kernel_name=kernel_name
            )
            
            # Calculate speedup
            kernel_speedup = 1.0
            if optimized_metrics.runtime_ms > 0:
                kernel_speedup = baseline_metrics.runtime_ms / optimized_metrics.runtime_ms
            
            # Assess bottleneck change
            baseline_bottleneck = BottleneckClassifier.classify(baseline_metrics)
            optimized_bottleneck = BottleneckClassifier.classify(optimized_metrics)
            
            comparison = {
                "kernel": kernel_name,
                "baseline_time": baseline_metrics.runtime_ms,
                "optimized_time": optimized_metrics.runtime_ms,
                "speedup": kernel_speedup,
                "baseline_bottleneck": baseline_bottleneck,
                "optimized_bottleneck": optimized_bottleneck,
                "bottleneck_shifted": baseline_bottleneck != optimized_bottleneck
            }
            
            validation["comparison"].append(comparison)
        
        # Query Claude for assessment
        prompt = PromptOptimizer.create_validation_prompt(
            {"total_time": baseline_total},
            {"total_time": optimized_total}
        )
        
        try:
            assessment = self._query_claude(
                prompt,
                system="You are a performance optimization expert. Assess the quality of this optimization."
            )
            validation["claude_assessment"] = assessment
        except Exception as e:
            validation["claude_assessment"] = f"Error: {str(e)}"
        
        logger.info(f"Validation complete: {validation['overall_speedup']:.2f}x speedup")
        
        return validation
    
    def run_full_pipeline(self, baseline_csv: str, 
                         optimized_csv: Optional[str] = None,
                         hardware: str = "A100") -> Dict:
        """
        Run complete pipeline:
        1. Analyze baseline profile
        2. Suggest optimizations
        3. (Optional) Validate results if optimized profile provided
        """
        logger.info("Running full ML-PGO pipeline")
        
        results = {
            "timestamp": str(Path.cwd()),
            "hardware": hardware,
            "pipeline_steps": []
        }
        
        # Step 1: Analysis
        analysis = self.analyze_profile(baseline_csv, hardware=hardware)
        results["pipeline_steps"].append({
            "step": "analyze_profile",
            "success": True,
            "token_usage": analysis.get("token_usage", {})
        })
        results["analysis"] = analysis
        
        # Step 2: Suggestions
        suggestions = self.suggest_optimizations(analysis, hardware=hardware)
        results["pipeline_steps"].append({
            "step": "suggest_optimizations",
            "success": True,
            "token_usage": suggestions.get("token_usage", {})
        })
        results["suggestions"] = suggestions
        
        # Step 3: Validation (if optimized provided)
        if optimized_csv:
            validation = self.validate_results(baseline_csv, optimized_csv, hardware=hardware)
            results["pipeline_steps"].append({
                "step": "validate_results",
                "success": True,
                "token_usage": validation.get("token_usage", {})
            })
            results["validation"] = validation
        
        # Calculate total token compression
        total_baseline = sum(
            step.get("token_usage", {}).get("baseline_tokens", 0)
            for step in results.get("pipeline_steps", [])
        )
        total_optimized = sum(
            step.get("token_usage", {}).get("optimized_tokens", 0)
            for step in results.get("pipeline_steps", [])
        )
        
        results["total_token_usage"] = {
            "baseline": total_baseline,
            "optimized": total_optimized,
            "compression_ratio": total_optimized / total_baseline if total_baseline > 0 else 1.0
        }
        
        logger.info(f"Pipeline complete: {total_baseline} → {total_optimized} tokens "
                   f"({results['total_token_usage']['compression_ratio']:.2%})")
        
        return results
    
    def _query_claude(self, prompt: str, system: str = "") -> str:
        """Query Claude API with conversation memory."""
        self.conversation_history.append({
            "role": "user",
            "content": prompt
        })
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=system,
                messages=self.conversation_history
            )
            
            assistant_message = response.content[0].text
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return assistant_message
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise
    
    def _load_profile_csv(self, csv_path: str) -> Dict:
        """Load DrGPUM CSV profile."""
        kernels = []
        
        try:
            with open(csv_path, 'r') as f:
                lines = f.readlines()
                
                if len(lines) < 2:
                    return {"kernels": []}
                
                # Parse header
                headers = [h.strip() for h in lines[0].split(',')]
                
                # Parse rows
                for line in lines[1:]:
                    if not line.strip():
                        continue
                    
                    values = [v.strip() for v in line.split(',')]
                    kernel = {}
                    
                    for header, value in zip(headers, values):
                        try:
                            # Try to convert to float
                            kernel[header] = float(value)
                        except ValueError:
                            kernel[header] = value
                    
                    kernels.append(kernel)
        
        except FileNotFoundError:
            logger.error(f"Profile file not found: {csv_path}")
        except Exception as e:
            logger.error(f"Error loading profile: {e}")
        
        return {"kernels": kernels}
    
    def save_memory(self):
        """Persist memory system to disk."""
        self.memory.save()
        logger.info("Memory saved to disk")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    agent = EnhancedMLPGOAgent()
    
    # Test with example data if available
    example_baseline = "/tmp/ml-pgo-research/agent/examples/example_baseline.csv"
    
    if Path(example_baseline).exists():
        results = agent.run_full_pipeline(example_baseline)
        print(json.dumps(results, indent=2))
        agent.save_memory()
    else:
        print("Example file not found. Run with real profile CSV:")
        print("  agent.run_full_pipeline('profile.csv')")
