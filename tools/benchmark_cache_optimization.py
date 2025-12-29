#!/usr/bin/env python3
"""
LLaMA Cache Optimization Benchmark

This script tests different KV cache configurations to determine the optimal
settings for your AI File Search system. It compares:

1. Current configuration (flash_attn=False, offload_kqv=True)
2. Optimized configuration (flash_attn=True, offload_kqv=True)
3. Alternative configurations for comparison

Usage:
    python benchmark_cache_optimization.py
"""

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import LLM_CONFIG


class CacheBenchmark:
    """Benchmark different KV cache configurations."""

    def __init__(self):
        self.model_path = Path("ai_models/qwen2.5-1.5b-instruct-q4_k_m.gguf")
        self.test_prompts = [
            "The capital of France is",
            "Artificial intelligence is defined as",
            "Machine learning algorithms work by",
        ]
        self.results = []

    def test_configuration(
        self,
        config_name: str,
        use_cache: bool,
        preload_model: bool,
        additional_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:  # Changed from Dict[str, float] to Dict[str, Any]
        """Test a specific cache configuration."""
        print(f"\n🧪 Testing {config_name}...")
        print(f"   flash_attn={use_cache}, offload_kqv={preload_model}")

        if additional_params:
            print(f"   Additional params: {additional_params}")

        try:
            from llama_cpp import Llama

            # Model initialization timing
            init_start = time.time()

            llm_params = {
                "model_path": str(self.model_path),
                "n_ctx": LLM_CONFIG["n_ctx"],
                "n_threads": LLM_CONFIG["n_threads"],
                "n_batch": LLM_CONFIG["n_batch"],
                "flash_attn": use_cache,
                "offload_kqv": preload_model,
                "verbose": False,
            }

            # Add any additional parameters
            if additional_params:
                llm_params.update(additional_params)

            llm = Llama(**llm_params)
            init_time = time.time() - init_start

            # Test inference timing
            inference_times = []
            total_tokens = 0

            for prompt in self.test_prompts:
                start_time = time.time()

                result = llm.create_completion(
                    prompt=prompt,
                    max_tokens=20,  # Short for benchmarking
                    temperature=0.1,
                    stop=["\n"],
                )

                inference_time = time.time() - start_time
                tokens_generated = len(result["choices"][0]["text"].split())

                inference_times.append(inference_time)
                total_tokens += tokens_generated

                print(
                    f"     Prompt {len(inference_times)}: {inference_time:.2f}s ({tokens_generated} tokens)"
                )

            # Calculate statistics
            avg_inference_time = sum(inference_times) / len(inference_times)
            tokens_per_second = (
                total_tokens / sum(inference_times) if sum(inference_times) > 0 else 0
            )

            # Memory usage (approximate)
            try:
                import psutil

                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
            except ImportError:
                memory_mb = 0

            result = {
                "config_name": config_name,
                "flash_attn": use_cache,
                "offload_kqv": preload_model,
                "init_time": init_time,
                "avg_inference_time": avg_inference_time,
                "tokens_per_second": tokens_per_second,
                "memory_mb": memory_mb,
                "success": True,
                "error": None,
            }

            print(
                f"   ✅ Success: {avg_inference_time:.2f}s avg, {tokens_per_second:.1f} tokens/sec"
            )

            # Clean up
            del llm

            return result

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return {
                "config_name": config_name,
                "flash_attn": use_cache,
                "offload_kqv": preload_model,
                "init_time": 0.0,
                "avg_inference_time": float("inf"),
                "tokens_per_second": 0.0,
                "memory_mb": 0.0,
                "success": False,
                "error": str(e),
            }

    def run_benchmark(self) -> List[Dict]:
        """Run comprehensive cache configuration benchmark."""
        print("🚀 LLaMA Cache Optimization Benchmark")
        print("=" * 60)

        if not self.model_path.exists():
            print(f"❌ Model not found: {self.model_path}")
            print("Please ensure the LLM model is downloaded.")
            return []

        # Test configurations
        configs = [
            {
                "name": "Current (Default)",
                "flash_attn": False,
                "offload_kqv": True,
                "additional": None,
            },
            {
                "name": "Flash Attention Enabled",
                "flash_attn": True,
                "offload_kqv": True,
                "additional": None,
            },
            {
                "name": "Flash + No KQV Offload",
                "flash_attn": True,
                "offload_kqv": False,
                "additional": None,
            },
            {
                "name": "No Flash + No Offload",
                "flash_attn": False,
                "offload_kqv": False,
                "additional": None,
            },
        ]

        results = []

        for config in configs:
            config_name = str(config["name"])
            use_cache = bool(config["flash_attn"])
            preload_model = bool(config["offload_kqv"])
            additional_params = (
                config["additional"] if isinstance(config["additional"], dict) else None
            )

            result = self.test_configuration(
                config_name,
                use_cache,
                preload_model,
                additional_params,
            )
            results.append(result)

            # Brief pause between tests
            time.sleep(1)

        self.results = results
        return results

    def analyze_results(self) -> Dict:
        """Analyze benchmark results and provide recommendations."""
        if not self.results:
            return {"error": "No results to analyze"}

        print("\n📊 Benchmark Results Analysis")
        print("=" * 60)

        # Find successful configurations
        successful = [r for r in self.results if r["success"]]

        if not successful:
            print("❌ No configurations succeeded")
            return {"error": "All configurations failed"}

        # Sort by performance metrics
        by_speed = sorted(successful, key=lambda x: x["avg_inference_time"])
        by_tokens_per_sec = sorted(
            successful, key=lambda x: x["tokens_per_second"], reverse=True
        )
        by_init_time = sorted(successful, key=lambda x: x["init_time"])

        print("\n🏆 Performance Rankings:")
        print("\n1️⃣ Fastest Inference:")
        for i, result in enumerate(by_speed[:3], 1):
            print(
                f"   {i}. {result['config_name']}: {result['avg_inference_time']:.2f}s avg"
            )

        print("\n2️⃣ Highest Throughput:")
        for i, result in enumerate(by_tokens_per_sec[:3], 1):
            print(
                f"   {i}. {result['config_name']}: {result['tokens_per_second']:.1f} tokens/sec"
            )

        print("\n3️⃣ Fastest Model Loading:")
        for i, result in enumerate(by_init_time[:3], 1):
            print(f"   {i}. {result['config_name']}: {result['init_time']:.2f}s init")

        # Find best overall configuration
        best_config = by_speed[0]  # Prioritize inference speed
        current_config = next(
            (r for r in self.results if "Current" in r["config_name"]), None
        )

        print(f"\n🎯 Recommended Configuration:")
        print(f"   Best: {best_config['config_name']}")
        print(f"   flash_attn = {best_config['flash_attn']}")
        print(f"   offload_kqv = {best_config['offload_kqv']}")

        if current_config and best_config != current_config:
            speed_improvement = (
                (
                    current_config["avg_inference_time"]
                    - best_config["avg_inference_time"]
                )
                / current_config["avg_inference_time"]
                * 100
            )
            print(f"\n📈 Potential Improvement:")
            print(f"   Speed: {speed_improvement:.1f}% faster inference")

            if speed_improvement > 5:  # More than 5% improvement
                print(f"   ✅ Recommendation: UPGRADE to optimized cache settings")
            else:
                print(f"   ℹ️  Recommendation: Current settings are adequate")
        else:
            print(f"\n✅ Current configuration is already optimal!")

        return {
            "best_config": best_config,
            "current_config": current_config,
            "all_results": successful,
        }

    def show_detailed_results(self):
        """Show detailed benchmark results table."""
        if not self.results:
            return

        print("\n📋 Detailed Results Table:")
        print("=" * 100)
        print(
            f"{'Configuration':<25} {'Init':<8} {'Avg Inf':<10} {'Tokens/s':<10} {'Memory':<10} {'Status':<10}"
        )
        print("-" * 100)

        for result in self.results:
            status = "✅ OK" if result["success"] else "❌ FAIL"
            init_time = f"{result['init_time']:.2f}s" if result["success"] else "N/A"
            avg_time = (
                f"{result['avg_inference_time']:.2f}s" if result["success"] else "N/A"
            )
            tokens_sec = (
                f"{result['tokens_per_second']:.1f}" if result["success"] else "N/A"
            )
            memory = (
                f"{result['memory_mb']:.0f}MB" if result["memory_mb"] > 0 else "N/A"
            )

            print(
                f"{result['config_name']:<25} {init_time:<8} {avg_time:<10} {tokens_sec:<10} {memory:<10} {status:<10}"
            )

        print("-" * 100)


def main():
    """Main benchmark execution."""
    benchmark = CacheBenchmark()

    print("This benchmark will test different KV cache configurations.")
    print("Each test may take 1-2 minutes to complete.\n")

    # Run the benchmark
    results = benchmark.run_benchmark()

    if results:
        # Show detailed results
        benchmark.show_detailed_results()

        # Analyze and provide recommendations
        analysis = benchmark.analyze_results()

        if "best_config" in analysis:
            print(f"\n🔧 To implement the recommended settings:")
            print(f"   Update core/llm.py in the Llama() initialization:")
            print(f"   flash_attn={analysis['best_config']['flash_attn']}")
            print(f"   offload_kqv={analysis['best_config']['offload_kqv']}")
    else:
        print("❌ Benchmark failed to run. Check model availability and dependencies.")


if __name__ == "__main__":
    main()
