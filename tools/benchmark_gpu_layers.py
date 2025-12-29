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
        epilog=__doc__
    )
    parser.add_argument(
        "--layers",
        type=str,
        default="0,10,20,35,50,99",
        help="Comma-separated GPU layer values to test (default: 0,10,20,35,50,99)"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Path to GGUF model file (default: from config)"
    )
    parser.add_argument(
        "--queries",
        type=int,
        choices=[1, 2, 3, 4, 5],
        default=3,
        help="Number of queries to run (default: 3)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Save results to JSON file (default: auto-generated filename)"
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


def get_gpu_info() -> dict:
    """Get GPU information if available."""
    info = {"detected": False}
    
    # Try to detect Vulkan (used by llama.cpp on Windows)
    try:
        import subprocess
        result = subprocess.run(
            ["vulkaninfo", "--summary"],
            capture_output=True,
            text=True,
            timeout=5
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


def benchmark_gpu_config(model_path: str, n_gpu_layers: int, queries: list) -> dict:
    """Benchmark a single GPU layer configuration."""
    print(f"\n{'='*70}")
    print(f"TESTING: n_gpu_layers = {n_gpu_layers}")
    print(f"{'='*70}")
    
    mem_before = get_memory_usage()
    
    # Load model
    try:
        llm, load_time = load_model(model_path, n_gpu_layers)
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
            print(f"    First token: {result['first_token']:.2f}s, Total: {result['total_time']:.2f}s")
        else:
            print(f"    ERROR: {result.get('error', 'Unknown')}")
    
    # Calculate averages
    successful_results = [r for r in query_results if r["status"] == "success"]
    if successful_results:
        avg_first_token = sum(r["first_token"] for r in successful_results) / len(successful_results)
        avg_total_time = sum(r["total_time"] for r in successful_results) / len(successful_results)
        avg_tok_per_sec = sum(r["tok_per_sec"] for r in successful_results) / len(successful_results)
    else:
        avg_first_token = avg_total_time = avg_tok_per_sec = None
    
    # Unload model
    print("  Unloading model...")
    unload_model(llm)
    
    mem_after_unload = get_memory_usage()
    
    return {
        "n_gpu_layers": n_gpu_layers,
        "status": "success",
        "model_load_time": load_time,
        "avg_first_token": round(avg_first_token, 2) if avg_first_token else None,
        "avg_total_time": round(avg_total_time, 2) if avg_total_time else None,
        "avg_tok_per_sec": round(avg_tok_per_sec, 2) if avg_tok_per_sec else None,
        "queries_run": len(queries),
        "queries_successful": len(successful_results),
        "memory": {
            "before_load": mem_before,
            "after_load": mem_after_load,
            "after_unload": mem_after_unload,
        },
        "query_results": query_results,
    }


def print_summary(results: list):
    """Print comparison summary across all GPU layer configurations."""
    print("\n" + "="*80)
    print("GPU LAYER BENCHMARK SUMMARY")
    print("="*80)
    print(f"{'Layers':>8} {'Load Time':>12} {'Avg 1st Tok':>14} {'Avg Total':>12} {'Tok/s':>10} {'Status':>10}")
    print("-"*80)
    
    for r in results:
        if r["status"] == "success":
            print(
                f"{r['n_gpu_layers']:>8} "
                f"{r['model_load_time']:>11.1f}s "
                f"{r['avg_first_token']:>13.2f}s "
                f"{r['avg_total_time']:>11.2f}s "
                f"{r['avg_tok_per_sec']:>10.2f} "
                f"{'OK':>10}"
            )
        else:
            print(
                f"{r['n_gpu_layers']:>8} "
                f"{'-':>12} "
                f"{'-':>14} "
                f"{'-':>12} "
                f"{'-':>10} "
                f"{'FAILED':>10}"
            )
    
    print("="*80)
    
    # Find best configuration
    successful = [r for r in results if r["status"] == "success"]
    if successful:
        fastest = min(successful, key=lambda x: x["avg_first_token"])
        print(f"\nFASTEST FIRST TOKEN: n_gpu_layers={fastest['n_gpu_layers']} ({fastest['avg_first_token']:.2f}s)")
        
        # Check if differences are significant
        times = [r["avg_first_token"] for r in successful]
        if max(times) - min(times) < 2.0:
            print("\n⚠️  NOTE: Performance difference is minimal (<2s).")
            print("   This is common on Intel iGPU (shared memory architecture).")
            print("   Recommendation: Use n_gpu_layers=0 (CPU) for stability.")
        else:
            improvement = ((successful[0]["avg_first_token"] - fastest["avg_first_token"]) 
                          / successful[0]["avg_first_token"] * 100)
            if improvement > 10:
                print(f"   {improvement:.0f}% faster than CPU-only (n_gpu_layers=0)")


def save_results(results: list, output_path: str, model_path: str, gpu_info: dict):
    """Save benchmark results to JSON file."""
    output = {
        "timestamp": datetime.now().isoformat(),
        "benchmark_type": "gpu_layers",
        "model_path": model_path,
        "gpu_info": gpu_info,
        "llm_config": {
            "n_ctx": LLM_CONFIG["n_ctx"],
            "n_threads": LLM_CONFIG["n_threads"],
            "n_batch": LLM_CONFIG["n_batch"],
            "max_tokens": LLM_CONFIG["max_tokens"],
            "temperature": LLM_CONFIG["temperature"],
        },
        "results": results,
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_path}")


def main():
    args = parse_args()
    
    print("="*80)
    print("GPU LAYER BENCHMARK (llama-cpp-python)")
    print("="*80)
    
    # Determine model path
    if args.model:
        model_path = args.model
    else:
        model_path = str(project_root / AI_MODELS_DIR / DEFAULT_MODEL_NAME)
    
    # Verify model exists
    if not Path(model_path).exists():
        print(f"ERROR: Model not found: {model_path}")
        print("\nEither:")
        print("  1. Place a GGUF model in ai_models/")
        print("  2. Specify path with --model PATH")
        return
    
    print(f"\nModel: {Path(model_path).name}")
    print(f"Size: {Path(model_path).stat().st_size / 1024 / 1024:.1f} MB")
    
    # Parse GPU layers to test
    gpu_layers = [int(x.strip()) for x in args.layers.split(",")]
    print(f"GPU Layers to test: {gpu_layers}")
    
    # Get GPU info
    gpu_info = get_gpu_info()
    if gpu_info["detected"]:
        print(f"GPU Detected: {gpu_info.get('device', 'Unknown')}")
    else:
        print("GPU: Not detected (will use CPU)")
    
    # Select queries
    queries = GPU_BENCHMARK_QUERIES[:args.queries]
    print(f"Queries: {len(queries)}")
    
    # Estimate time
    estimated_time = len(gpu_layers) * (15 + len(queries) * 30)  # rough estimate
    print(f"Estimated time: {estimated_time // 60}m {estimated_time % 60}s")
    
    print("\n" + "-"*80)
    
    # Run benchmarks
    all_results = []
    for n_gpu_layers in gpu_layers:
        result = benchmark_gpu_config(model_path, n_gpu_layers, queries)
        all_results.append(result)
    
    # Print summary
    print_summary(all_results)
    
    # Save results
    BENCHMARK_OUTPUT_DIR.mkdir(exist_ok=True)
    if args.output:
        output_path = BENCHMARK_OUTPUT_DIR / args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = BENCHMARK_OUTPUT_DIR / f"gpu_layers_{timestamp}.json"
    
    save_results(all_results, str(output_path), model_path, gpu_info)
    
    print("\nNext steps:")
    print("   1. Review the summary above")
    print("   2. If a GPU layer setting is significantly faster, update core/config.py:")
    print(f"      LLM_CONFIG['n_gpu_layers'] = {gpu_layers[0]}  # or your optimal value")
    print("   3. Or set via environment: GPU_LAYERS=35 poetry run python run_app.py")


if __name__ == "__main__":
    main()
