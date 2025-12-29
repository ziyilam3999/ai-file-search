"""Benchmark GPU layer offloading performance using llama-cpp-python.

This script tests different n_gpu_layers values to find the optimal setting
for your hardware. Unlike benchmark_models.py (which uses Ollama to compare
different models), this script uses llama-cpp-python directly to tune
hardware-specific settings.

Usage:
    poetry run python tools/benchmark_gpu_layers.py
    poetry run python tools/benchmark_gpu_layers.py --layers 0,10,35,99
    poetry run python tools/benchmark_gpu_layers.py --model ai_models/qwen2.5-1.5b.gguf

Options:
    --layers LAYERS       Comma-separated GPU layer values to test (default: 0,10,20,35,50,99)
    --model PATH          Path to GGUF model file (default: from config)
    --queries N           Number of queries to run (1-5, default: 3)
    --output FILE         Save results to JSON file
    --help                Show this help message

Requirements:
    - llama-cpp-python installed with GPU support
    - GGUF model file in ai_models/

Notes:
    - Model must be reloaded for each n_gpu_layers value
    - Fewer queries recommended (3-5) since each config requires full reload
    - Intel iGPU users: CPU and GPU often perform similarly due to shared memory
"""

import argparse
import gc
import json
import platform
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import AI_MODELS_DIR, DEFAULT_MODEL_NAME, LLM_CONFIG
from core.embedding import Embedder

BENCHMARK_OUTPUT_DIR = project_root / "benchmark_results"

# Default GPU layer values to test
DEFAULT_GPU_LAYERS = [0, 10, 20, 35, 50, 99]

# Qwen2.5-1.5B specific layer suggestions (28 transformer layers)
# Fine-grained testing around common optimal points
QWEN_LAYER_PRESETS = {
    "coarse": [0, 8, 16, 24, 32, 40, 48, 56, 64, 99],  # Wide scan
    "fine": [0, 4, 8, 12, 16, 20, 24, 28, 32],  # Narrow scan
    "minimal": [0, 16, 32, 99],  # Quick test
}

# Subset of queries for GPU benchmarking (fewer since model reloads are slow)
GPU_BENCHMARK_QUERIES = [
    {
        "query": "How many credits does a new user receive during onboarding?",
        "type": "extraction",
        "description": "Simple fact extraction",
    },
    {
        "query": "What is the difference between Premium and Freemium users for platform fees?",
        "type": "comparison",
        "description": "Complex comparison requiring reasoning",
    },
    {
        "query": "What is the weather forecast for tomorrow?",
        "type": "hallucination_test",
        "description": "Should say 'not found' (tests instruction following)",
    },
]


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Benchmark GPU layer offloading for llama-cpp-python",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--layers",
        type=str,
        default="0,10,20,35,50,99",
        help="Comma-separated GPU layer values to test (default: 0,10,20,35,50,99)",
    )
    parser.add_argument(
        "--preset",
        type=str,
        choices=["coarse", "fine", "minimal"],
        help="Use Qwen2.5 layer preset (overrides --layers): coarse, fine, or minimal",
    )
    parser.add_argument(
        "--model", type=str, help="Path to GGUF model file (default: from config)"
    )
    parser.add_argument(
        "--queries",
        type=int,
        choices=[1, 2, 3, 4, 5],
        default=3,
        help="Number of queries to run (default: 3)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        choices=[1, 2, 3, 4, 5],
        help="Number of iterations per config for statistical validity (default: 1)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Save results to JSON file (default: auto-generated filename)",
    )
    return parser.parse_args()


def get_memory_usage() -> dict:
    """Get current memory usage."""
    try:
        import psutil

        process = psutil.Process()
        mem_info = process.memory_info()
        return {
            "rss_mb": round(mem_info.rss / 1024 / 1024, 1),
            "vms_mb": round(mem_info.vms / 1024 / 1024, 1),
        }
    except ImportError:
        return {"rss_mb": None, "vms_mb": None, "note": "psutil not installed"}


def get_system_info() -> dict:
    """Get comprehensive system information."""
    info = {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }

    try:
        import psutil

        info["cpu_count_physical"] = psutil.cpu_count(logical=False)
        info["cpu_count_logical"] = psutil.cpu_count(logical=True)
        mem = psutil.virtual_memory()
        info["ram_total_gb"] = round(mem.total / 1024 / 1024 / 1024, 1)
        info["ram_available_gb"] = round(mem.available / 1024 / 1024 / 1024, 1)
    except ImportError:
        info["note"] = "psutil not installed - limited system info"

    return info


def calculate_statistics(values: list) -> dict:
    """Calculate statistics for a list of values."""
    if not values or len(values) == 0:
        return {"mean": None, "std": None, "min": None, "max": None, "count": 0}

    if len(values) == 1:
        return {
            "mean": round(values[0], 3),
            "std": 0.0,
            "min": round(values[0], 3),
            "max": round(values[0], 3),
            "count": 1,
        }

    return {
        "mean": round(statistics.mean(values), 3),
        "std": round(statistics.stdev(values), 3),
        "min": round(min(values), 3),
        "max": round(max(values), 3),
        "count": len(values),
    }


def get_gpu_info() -> dict:
    """Get GPU information if available."""
    info: dict = {"detected": False, "device": None}

    # Try to detect Vulkan (used by llama.cpp on Windows)
    try:
        import subprocess

        result = subprocess.run(
            ["vulkaninfo", "--summary"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            info["vulkan"] = True
            # Parse GPU name from output
            for line in result.stdout.split("\n"):
                if "deviceName" in line:
                    info["device"] = line.split("=")[-1].strip()
                    info["detected"] = True
                    break
    except Exception:
        info["vulkan"] = False

    return info


def get_real_context(query: str, top_k: int = 3) -> str:
    """Fetch real context chunks from the project's database."""
    try:
        embedder = Embedder()
        results = embedder.query(query, k=top_k)

        context_parts = []
        for i, result in enumerate(results, 1):
            chunk_text, file_path, chunk_id, doc_chunk_id, score = result
            context_parts.append(f"[Document {i}: {file_path}]\n{chunk_text}")

        return "\n\n".join(context_parts)
    except Exception as e:
        print(f"Warning: Could not load real context: {e}")
        return "[Placeholder context - ensure FAISS index exists]"


def build_prompt(query: str, context: str) -> str:
    """Build the prompt format matching production."""
    return f"""<CONTEXT>
{context}
</CONTEXT>

<QUESTION>
{query}
</QUESTION>

<INSTRUCTIONS>
Answer the question using ONLY the context provided above.
Be direct and concise. If the answer is not in the context, say "Not found in documents."
</INSTRUCTIONS>"""


def load_model(model_path: str, n_gpu_layers: int) -> tuple:
    """
    Load the LLM with specified GPU layers.

    Returns:
        Tuple of (llm_instance, load_time_seconds)
    """
    try:
        from llama_cpp import Llama
    except ImportError:
        raise ImportError(
            "llama-cpp-python not found. Install with: pip install llama-cpp-python"
        )

    print(f"  Loading model with n_gpu_layers={n_gpu_layers}...", end=" ", flush=True)

    start = time.time()
    llm = Llama(
        model_path=model_path,
        n_ctx=LLM_CONFIG["n_ctx"],
        n_threads=LLM_CONFIG["n_threads"],
        n_batch=LLM_CONFIG["n_batch"],
        n_gpu_layers=n_gpu_layers,
        use_mmap=True,
        use_mlock=True,
        verbose=False,
    )
    load_time = time.time() - start

    print(f"OK ({load_time:.1f}s)")
    return llm, load_time


def unload_model(llm) -> None:
    """Explicitly unload model and free memory."""
    del llm
    gc.collect()
    # Give system time to reclaim memory
    time.sleep(1)


def benchmark_single_query(llm, prompt: str, query_info: dict) -> dict:
    """Run a single query and measure performance."""
    query = query_info["query"]

    start = time.time()
    first_token_time = None
    tokens = 0
    response_text = ""

    try:
        # Use streaming to measure first token time
        stream = llm.create_completion(
            prompt=prompt,
            max_tokens=int(LLM_CONFIG["max_tokens"]),
            temperature=float(LLM_CONFIG["temperature"]),
            stream=True,
            stop=["Question:", "Context:", "\n\n\n", "References:"],
        )

        for chunk in stream:
            if "choices" in chunk and len(chunk["choices"]) > 0:
                token = chunk["choices"][0].get("text", "")
                if token:
                    if first_token_time is None:
                        first_token_time = time.time() - start
                    tokens += 1
                    response_text += token

        total_time = time.time() - start
        tok_per_sec = tokens / total_time if total_time > 0 else 0

        return {
            "query": query,
            "query_type": query_info["type"],
            "first_token": round(first_token_time, 2) if first_token_time else None,
            "total_time": round(total_time, 2),
            "tokens": tokens,
            "tok_per_sec": round(tok_per_sec, 2),
            "response_preview": response_text[:100],
            "status": "success",
        }

    except Exception as e:
        return {
            "query": query,
            "query_type": query_info["type"],
            "status": "error",
            "error": str(e),
        }


def benchmark_gpu_config(
    model_path: str, n_gpu_layers: int, queries: list, iterations: int = 1
) -> dict:
    """Benchmark a single GPU layer configuration with multiple iterations."""
    print(f"\n{'='*70}")
    print(f"TESTING: n_gpu_layers = {n_gpu_layers} ({iterations} iteration(s))")
    print(f"{'='*70}")

    all_first_tokens = []
    all_total_times = []
    all_tok_per_sec = []
    all_load_times = []
    all_query_results = []
    mem_snapshots = []

    for iteration in range(1, iterations + 1):
        if iterations > 1:
            print(f"\n  --- Iteration {iteration}/{iterations} ---")

        mem_before = get_memory_usage()

        # Load model
        try:
            llm, load_time = load_model(model_path, n_gpu_layers)
            all_load_times.append(load_time)
        except Exception as e:
            print(f"  FAILED to load: {e}")
            return {
                "n_gpu_layers": n_gpu_layers,
                "status": "error",
                "error": str(e),
            }

        mem_after_load = get_memory_usage()

        # Warm-up run (prime the model)
        print("  Warm-up run...", end=" ", flush=True)
        try:
            llm.create_completion(
                prompt="Say hello",
                max_tokens=5,
                temperature=0.0,
                stream=False,
            )
            print("OK")
        except Exception as e:
            print(f"WARN ({e})")

        # Run queries
        query_results = []
        for i, query_info in enumerate(queries, 1):
            print(f"  Query {i}/{len(queries)}: {query_info['query'][:50]}...")

            # Get context and build prompt
            context = get_real_context(query_info["query"], top_k=3)
            prompt = build_prompt(query_info["query"], context)

            result = benchmark_single_query(llm, prompt, query_info)
            query_results.append(result)

            if result["status"] == "success":
                print(
                    f"    First token: {result['first_token']:.2f}s, Total: {result['total_time']:.2f}s"
                )
                all_first_tokens.append(result["first_token"])
                all_total_times.append(result["total_time"])
                all_tok_per_sec.append(result["tok_per_sec"])
            else:
                print(f"    ERROR: {result.get('error', 'Unknown')}")

        all_query_results.extend(query_results)

        # Unload model
        print("  Unloading model...")
        unload_model(llm)

        mem_after_unload = get_memory_usage()
        mem_snapshots.append(
            {
                "iteration": iteration,
                "before_load": mem_before,
                "after_load": mem_after_load,
                "after_unload": mem_after_unload,
            }
        )

    # Calculate statistics across all iterations
    first_token_stats = calculate_statistics(all_first_tokens)
    total_time_stats = calculate_statistics(all_total_times)
    tok_per_sec_stats = calculate_statistics(all_tok_per_sec)
    load_time_stats = calculate_statistics(all_load_times)

    successful_count = len([r for r in all_query_results if r["status"] == "success"])

    return {
        "n_gpu_layers": n_gpu_layers,
        "status": "success",
        "iterations": iterations,
        "model_load_time": load_time_stats,
        "first_token": first_token_stats,
        "total_time": total_time_stats,
        "tok_per_sec": tok_per_sec_stats,
        "queries_run": len(queries) * iterations,
        "queries_successful": successful_count,
        "memory_snapshots": mem_snapshots,
        "query_results": all_query_results,
    }


def print_summary(results: list, iterations: int):
    """Print comparison summary across all GPU layer configurations."""
    print("\n" + "=" * 90)
    print(
        f"GPU LAYER BENCHMARK SUMMARY (Qwen2.5-1.5B, {iterations} iteration(s) per config)"
    )
    print("=" * 90)

    if iterations > 1:
        print(
            f"{'Layers':>8} {'Load(s)':>10} {'1st Tok(s)':>12} {'±Std':>8} "
            f"{'Total(s)':>10} {'Tok/s':>8} {'Status':>8}"
        )
        print("-" * 90)
        for r in results:
            if r["status"] == "success":
                ft = r["first_token"]
                print(
                    f"{r['n_gpu_layers']:>8} "
                    f"{r['model_load_time']['mean']:>9.1f} "
                    f"{ft['mean']:>11.2f} "
                    f"±{ft['std']:>6.2f} "
                    f"{r['total_time']['mean']:>9.2f} "
                    f"{r['tok_per_sec']['mean']:>7.1f} "
                    f"{'OK':>8}"
                )
            else:
                print(
                    f"{r['n_gpu_layers']:>8} "
                    f"{'-':>10} {'-':>12} {'-':>8} {'-':>10} {'-':>8} {'FAIL':>8}"
                )
    else:
        print(
            f"{'Layers':>8} {'Load(s)':>10} {'1st Tok(s)':>14} "
            f"{'Total(s)':>12} {'Tok/s':>10} {'Status':>10}"
        )
        print("-" * 90)
        for r in results:
            if r["status"] == "success":
                print(
                    f"{r['n_gpu_layers']:>8} "
                    f"{r['model_load_time']['mean']:>9.1f} "
                    f"{r['first_token']['mean']:>13.2f} "
                    f"{r['total_time']['mean']:>11.2f} "
                    f"{r['tok_per_sec']['mean']:>9.1f} "
                    f"{'OK':>10}"
                )
            else:
                print(
                    f"{r['n_gpu_layers']:>8} "
                    f"{'-':>10} {'-':>14} {'-':>12} {'-':>10} {'FAILED':>10}"
                )

    print("=" * 90)

    # Find best configuration
    successful = [r for r in results if r["status"] == "success"]
    if successful:
        fastest = min(successful, key=lambda x: x["first_token"]["mean"])
        baseline = next(
            (r for r in successful if r["n_gpu_layers"] == 0), successful[0]
        )

        print(f"\n🏆 FASTEST FIRST TOKEN: n_gpu_layers={fastest['n_gpu_layers']}")
        print(f"   Mean: {fastest['first_token']['mean']:.2f}s")
        if iterations > 1:
            print(f"   Std Dev: ±{fastest['first_token']['std']:.2f}s")
            print(
                f"   Range: {fastest['first_token']['min']:.2f}s - {fastest['first_token']['max']:.2f}s"
            )

        # Check if differences are significant
        times = [r["first_token"]["mean"] for r in successful]
        time_range = max(times) - min(times)

        if time_range < 2.0:
            print("\n⚠️  NOTE: Performance difference is minimal (<2s).")
            print("   This is common on Intel iGPU (shared memory architecture).")
            print("   Recommendation: Use n_gpu_layers=0 (CPU) for stability.")
        else:
            if baseline["first_token"]["mean"] > 0:
                improvement = (
                    (baseline["first_token"]["mean"] - fastest["first_token"]["mean"])
                    / baseline["first_token"]["mean"]
                    * 100
                )
                if improvement > 0:
                    print(
                        f"\n   📈 {improvement:.0f}% faster than CPU-only (n_gpu_layers=0)"
                    )
                elif improvement < -10:
                    print(
                        f"\n   📉 CPU is {-improvement:.0f}% faster - GPU offload not beneficial"
                    )

        # Recommendation
        print("\n" + "-" * 50)
        print("RECOMMENDATION:")
        if fastest["n_gpu_layers"] == 0:
            print(f"   ✅ Use n_gpu_layers=0 (CPU-only is optimal)")
        else:
            print(f"   ✅ Use n_gpu_layers={fastest['n_gpu_layers']}")
        print(
            f"   Set in config or: GPU_LAYERS={fastest['n_gpu_layers']} poetry run python run_app.py"
        )


def save_results(
    results: list,
    output_path: str,
    model_path: str,
    gpu_info: dict,
    system_info: dict,
    iterations: int,
):
    """Save benchmark results to JSON file."""
    # Find optimal config for quick reference
    successful = [r for r in results if r["status"] == "success"]
    optimal = (
        min(successful, key=lambda x: x["first_token"]["mean"]) if successful else None
    )

    output = {
        "timestamp": datetime.now().isoformat(),
        "benchmark_type": "gpu_layers_qwen25",
        "model_path": model_path,
        "model_name": Path(model_path).name,
        "iterations_per_config": iterations,
        "system_info": system_info,
        "gpu_info": gpu_info,
        "llm_config": {
            "n_ctx": LLM_CONFIG["n_ctx"],
            "n_threads": LLM_CONFIG["n_threads"],
            "n_batch": LLM_CONFIG["n_batch"],
            "max_tokens": LLM_CONFIG["max_tokens"],
            "temperature": LLM_CONFIG["temperature"],
        },
        "optimal_config": {
            "n_gpu_layers": optimal["n_gpu_layers"] if optimal else None,
            "first_token_mean": optimal["first_token"]["mean"] if optimal else None,
            "tok_per_sec_mean": optimal["tok_per_sec"]["mean"] if optimal else None,
        },
        "results": results,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_path}")


def main():
    args = parse_args()

    print("=" * 80)
    print("GPU LAYER BENCHMARK - Qwen2.5-1.5B Optimization")
    print("=" * 80)

    # Determine model path - default to Qwen2.5
    if args.model:
        model_path = args.model
    else:
        model_path = str(
            project_root / AI_MODELS_DIR / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
        )

    # Verify model exists
    if not Path(model_path).exists():
        print(f"ERROR: Model not found: {model_path}")
        print("\nEither:")
        print("  1. Place qwen2.5-1.5b-instruct-q4_k_m.gguf in ai_models/")
        print("  2. Specify path with --model PATH")
        return

    print(f"\nModel: {Path(model_path).name}")
    print(f"Size: {Path(model_path).stat().st_size / 1024 / 1024:.1f} MB")

    # Get system info
    system_info = get_system_info()
    print(f"System: {system_info.get('processor', 'Unknown')}")
    if "ram_total_gb" in system_info:
        print(
            f"RAM: {system_info['ram_available_gb']:.1f} GB available / {system_info['ram_total_gb']:.1f} GB total"
        )

    # Parse GPU layers to test - preset overrides manual
    if args.preset:
        gpu_layers = QWEN_LAYER_PRESETS[args.preset]
        print(f"Using preset '{args.preset}': {gpu_layers}")
    else:
        gpu_layers = [int(x.strip()) for x in args.layers.split(",")]
        print(f"GPU Layers to test: {gpu_layers}")

    # Get GPU info
    gpu_info = get_gpu_info()
    if gpu_info["detected"]:
        print(f"GPU Detected: {gpu_info.get('device', 'Unknown')}")
    else:
        print("GPU: Not detected (will use CPU)")

    # Select queries
    queries = GPU_BENCHMARK_QUERIES[: args.queries]
    iterations = args.iterations
    print(
        f"Queries: {len(queries)} x {iterations} iteration(s) = {len(queries) * iterations} runs per config"
    )

    # Estimate time
    runs_per_config = len(queries) * iterations
    estimated_time = len(gpu_layers) * (15 + runs_per_config * 25)  # rough estimate
    print(f"Estimated time: {estimated_time // 60}m {estimated_time % 60}s")

    print("\n" + "-" * 80)
    start_time = time.time()

    # Run benchmarks
    all_results = []
    for i, n_gpu_layers in enumerate(gpu_layers, 1):
        print(f"\n[{i}/{len(gpu_layers)}] Progress: {(i-1)/len(gpu_layers)*100:.0f}%")
        result = benchmark_gpu_config(model_path, n_gpu_layers, queries, iterations)
        all_results.append(result)

        # Show running time
        elapsed = time.time() - start_time
        remaining = (elapsed / i) * (len(gpu_layers) - i)
        print(f"  Elapsed: {elapsed/60:.1f}m, Remaining: ~{remaining/60:.1f}m")

    total_time = time.time() - start_time
    print(f"\n\nTotal benchmark time: {total_time/60:.1f} minutes")

    # Print summary
    print_summary(all_results, iterations)

    # Save results
    BENCHMARK_OUTPUT_DIR.mkdir(exist_ok=True)
    if args.output:
        output_path = BENCHMARK_OUTPUT_DIR / args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = BENCHMARK_OUTPUT_DIR / f"qwen25_gpu_layers_{timestamp}.json"

    save_results(
        all_results, str(output_path), model_path, gpu_info, system_info, iterations
    )

    print("\n" + "=" * 50)
    print("NEXT STEPS:")
    print("=" * 50)
    print("1. Review the summary above")
    print("2. For fine-grained testing around optimal value, run:")
    print("   poetry run python tools/benchmark_gpu_layers.py --preset fine")
    print("3. For statistical validation with multiple iterations:")
    print(
        "   poetry run python tools/benchmark_gpu_layers.py --layers <optimal> --iterations 3"
    )
    print("4. Apply optimal setting:")
    print("   - Edit core/config.py: LLM_CONFIG['n_gpu_layers'] = <value>")
    print("   - Or: GPU_LAYERS=<value> poetry run python run_app.py")


if __name__ == "__main__":
    main()
