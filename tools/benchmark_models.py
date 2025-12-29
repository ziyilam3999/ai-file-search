"""Benchmark different LLM models via Ollama for performance comparison.

Usage:
    1. Install Ollama: winget install Ollama.Ollama
    2. Pull models: ollama pull phi3.5, ollama pull qwen2.5:1.5b, etc.
    3. Run benchmark: poetry run python tools/benchmark_models.py

Options:
    --models MODEL1,MODEL2    Comma-separated list of models to test
    --queries N               Number of queries to run (1-5, default: all)
    --output FILE             Save results to JSON file
    --skip-warmup             Skip warm-up run (not recommended)
    --help                    Show this help message

Requirements:
    - Ollama service running
    - Models pulled (ollama pull <model>)
    - requests library (should be in dependencies)
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.embedding import Embedder

OLLAMA_URL = "http://localhost:11434/api/generate"
BENCHMARK_OUTPUT_DIR = project_root / "benchmark_results"

# Models to benchmark (must be pulled first: ollama pull <model>)
DEFAULT_MODELS = [
    "phi3.5",  # Legacy baseline model (3.8B, replaced by qwen2.5:1.5b)
    "qwen2.5:1.5b",  # Smaller alternative (1.5B)
    "qwen2.5:0.5b",  # Fastest option (0.5B)
    "gemma2:2b",  # Google's compact model (2B)
]

# Test queries covering different difficulty levels and criteria
# Categories: extraction, multi-fact, numeric, reasoning, summarization, comparison, hallucination_test
# Based on actual documents in ai_search_docs/business_rules/
TEST_QUERIES = [
    # === EXTRACTION (Simple fact retrieval) ===
    {
        "query": "What is the year for the tenancy agreement?",
        "type": "extraction",
        "expected_behavior": "answer",
        "weight": 1.0,
    },
    {
        "query": "How many credits does a new user receive during onboarding?",
        "type": "extraction",
        "expected_behavior": "answer",
        "weight": 1.0,
    },
    {
        "query": "How much does the GetSpace Premium subscription cost per month?",
        "type": "extraction",
        "expected_behavior": "answer",
        "weight": 1.0,
    },
    # === NUMERIC (Numbers, dates, amounts) ===
    {
        "query": "What is the maximum number of credits a user can borrow at any time?",
        "type": "numeric",
        "expected_behavior": "answer",
        "weight": 1.5,
    },
    {
        "query": "How many days do users have to repay borrowed tokens?",
        "type": "numeric",
        "expected_behavior": "answer",
        "weight": 1.5,
    },
    {
        "query": "What is the penalty amount for failing to repay borrowed tokens on time?",
        "type": "numeric",
        "expected_behavior": "answer",
        "weight": 1.5,
    },
    {
        "query": "How many vehicles can a user register on their GetSpace account?",
        "type": "numeric",
        "expected_behavior": "answer",
        "weight": 1.5,
    },
    {
        "query": "How many tokens does a user earn for hosting a parking spot?",
        "type": "numeric",
        "expected_behavior": "answer",
        "weight": 1.5,
    },
    # === MULTI-FACT (Multiple pieces of information) ===
    {
        "query": "What e-wallet platforms are supported for cash payouts?",
        "type": "multi-fact",
        "expected_behavior": "answer",
        "weight": 1.2,
    },
    {
        "query": "What vehicle sizes does GetSpace support?",
        "type": "multi-fact",
        "expected_behavior": "answer",
        "weight": 1.2,
    },
    {
        "query": "What are the requirements to become a beta user?",
        "type": "multi-fact",
        "expected_behavior": "answer",
        "weight": 1.2,
    },
    # === REASONING (Interpretation, inference) ===
    {
        "query": "What happens if a seeker's ETA is greater than 40 minutes?",
        "type": "reasoning",
        "expected_behavior": "answer",
        "weight": 2.0,
    },
    {
        "query": "Can users with unpaid penalties still borrow tokens?",
        "type": "reasoning",
        "expected_behavior": "answer",
        "weight": 2.0,
    },
    {
        "query": "Is there a penalty for hosts who cancel parking hosting?",
        "type": "reasoning",
        "expected_behavior": "answer",
        "weight": 2.0,
    },
    {
        "query": "What happens to the deposit token if a seeker accepts a no-show report?",
        "type": "reasoning",
        "expected_behavior": "answer",
        "weight": 2.0,
    },
    # === COMPARISON (Compare/contrast) ===
    {
        "query": "What is the difference between Premium and Freemium users for platform fees?",
        "type": "comparison",
        "expected_behavior": "answer",
        "weight": 1.8,
    },
    {
        "query": "What is the difference between Ready to Leave and Leaving Now hosting modes?",
        "type": "comparison",
        "expected_behavior": "answer",
        "weight": 1.8,
    },
    # === PROCESS/FLOW (How things work) ===
    {
        "query": "How does the points redemption system work for beta users?",
        "type": "summarization",
        "expected_behavior": "answer",
        "weight": 1.5,
    },
    {
        "query": "What approval workflow is used for admin configuration changes?",
        "type": "summarization",
        "expected_behavior": "answer",
        "weight": 1.5,
    },
    {
        "query": "How long does Ready to Leave hosting mode stay active?",
        "type": "extraction",
        "expected_behavior": "answer",
        "weight": 1.0,
    },
    # === EDGE CASES (Specific scenarios) ===
    {
        "query": "What is the maximum number of rematches allowed after a no-show?",
        "type": "numeric",
        "expected_behavior": "answer",
        "weight": 1.5,
    },
    {
        "query": "Do credits expire if a user is inactive?",
        "type": "reasoning",
        "expected_behavior": "answer",
        "weight": 2.0,
    },
    {
        "query": "What is the cash value of 10 reward points?",
        "type": "numeric",
        "expected_behavior": "answer",
        "weight": 1.5,
    },
    # === HALLUCINATION TESTS (Should say "not found") ===
    {
        "query": "What is the weather forecast for tomorrow?",
        "type": "hallucination_test",
        "expected_behavior": "not_found",
        "weight": 3.0,
    },
    {
        "query": "What is the stock price of Apple today?",
        "type": "hallucination_test",
        "expected_behavior": "not_found",
        "weight": 3.0,
    },
    {
        "query": "Who is the CEO of GetSpace?",
        "type": "hallucination_test",
        "expected_behavior": "not_found",
        "weight": 3.0,
    },
]

# Phrases indicating "not found" response
NOT_FOUND_PHRASES = [
    "not found",
    "not in the context",
    "not in the document",
    "no information",
    "cannot find",
    "don't have",
    "do not have",
    "unable to find",
    "not mentioned",
    "not available",
    "not provided",
]


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Benchmark LLM models via Ollama",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--models",
        type=str,
        help="Comma-separated list of models to test (default: all)",
    )
    parser.add_argument(
        "--queries",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Number of queries to run (1-5, default: all)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Save results to JSON file (default: auto-generated filename)",
    )
    parser.add_argument(
        "--skip-warmup", action="store_true", help="Skip warm-up run (not recommended)"
    )
    return parser.parse_args()


def check_ollama_running() -> bool:
    """Check if Ollama service is running."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def get_memory_usage() -> dict:
    """Get current memory usage (requires psutil)."""
    try:
        import psutil

        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return {
            "rss_mb": round(mem_info.rss / 1024 / 1024, 1),
            "vms_mb": round(mem_info.vms / 1024 / 1024, 1),
        }
    except ImportError:
        return {"rss_mb": None, "vms_mb": None, "note": "psutil not installed"}


def get_real_context(query: str, top_k: int = 3) -> str:
    """Fetch real context chunks from the project's database."""
    try:
        embedder = Embedder()
        results = embedder.query(query, k=top_k)

        context_parts = []
        # Results are 5-tuples: (chunk_text, file_path, chunk_id, doc_chunk_id, score)
        for i, result in enumerate(results, 1):
            chunk_text, file_path, chunk_id, doc_chunk_id, score = result
            context_parts.append(f"[Document {i}: {file_path}]\n{chunk_text}")

        return "\n\n".join(context_parts)
    except Exception as e:
        print(f"Warning: Could not load real context: {e}")
        print("Using placeholder context instead.")
        return "[Placeholder context - ensure FAISS index exists]"


def build_prompt(query: str, context: str) -> str:
    """Build the same prompt format as production app."""
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


def detect_not_found(response: str) -> bool:
    """Detect if response indicates 'not found in documents'."""
    response_lower = response.lower()
    return any(phrase in response_lower for phrase in NOT_FOUND_PHRASES)


def score_response(
    response: str, expected_behavior: str, context: str, query_type: str
) -> dict:
    """Score a response for quality metrics with comprehensive analysis."""
    response_lower = response.lower()
    context_lower = context.lower()

    # Hallucination detection
    says_not_found = detect_not_found(response)

    if expected_behavior == "not_found":
        # For hallucination test queries - CRITICAL: must say not found
        hallucination_detected = not says_not_found
        instruction_followed = says_not_found
    else:
        # For normal queries - check if answer seems grounded in context
        # Extract significant words from response (>4 chars, not common words)
        common_words = {
            "the",
            "and",
            "that",
            "this",
            "with",
            "from",
            "have",
            "been",
            "would",
            "could",
            "should",
            "about",
            "which",
            "there",
            "their",
            "what",
            "when",
            "where",
            "will",
            "were",
            "they",
            "your",
            "also",
            "into",
            "more",
            "some",
            "than",
            "them",
            "then",
            "these",
            "only",
            "other",
            "such",
            "after",
            "most",
            "make",
            "being",
            "well",
            "back",
            "much",
            "before",
        }
        response_words = set(
            w for w in response_lower.split() if len(w) > 4 and w not in common_words
        )

        # Check how many response words appear in context (grounding score)
        grounded_words = sum(1 for w in response_words if w in context_lower)
        grounding_ratio = grounded_words / len(response_words) if response_words else 0

        # Hallucination if response has many words not in context
        hallucination_detected = grounding_ratio < 0.3 and len(response_words) > 5
        instruction_followed = not says_not_found

    # Length appropriateness by query type
    response_length = len(response.split())
    if query_type == "extraction":
        length_appropriate = 3 <= response_length <= 50
    elif query_type == "multi-fact":
        length_appropriate = 10 <= response_length <= 100
    elif query_type == "summarization":
        length_appropriate = 20 <= response_length <= 150
    elif query_type == "comparison":
        length_appropriate = 15 <= response_length <= 150
    elif query_type == "hallucination_test":
        length_appropriate = 3 <= response_length <= 30  # Should be short "not found"
    else:
        length_appropriate = 5 <= response_length <= 150

    # Conciseness score (penalize overly verbose responses)
    conciseness = (
        min(1.0, 50 / max(response_length, 1))
        if query_type == "extraction"
        else min(1.0, 100 / max(response_length, 1))
    )

    return {
        "hallucination_detected": hallucination_detected,
        "instruction_followed": instruction_followed,
        "says_not_found": says_not_found,
        "response_length": response_length,
        "length_appropriate": length_appropriate,
        "grounding_ratio": (
            round(grounding_ratio, 2) if expected_behavior != "not_found" else None
        ),
        "conciseness": round(conciseness, 2),
    }


def run_warmup(models: list):
    """Run warm-up queries to load models into memory."""
    print("\n" + "=" * 60)
    print("WARM-UP RUN (loading models into memory)")
    print("=" * 60)

    warmup_prompt = "Say 'ready' in one word."

    for model in models:
        print(f"  Warming up {model}...", end=" ", flush=True)
        try:
            start = time.time()
            resp = requests.post(
                OLLAMA_URL,
                json={
                    "model": model,
                    "prompt": warmup_prompt,
                    "stream": False,
                    "options": {"num_predict": 5},
                },
                timeout=120,
            )
            elapsed = time.time() - start
            if resp.status_code == 200:
                print(f"OK ({elapsed:.1f}s)")
            else:
                print(f"WARN (HTTP {resp.status_code})")
        except Exception as e:
            print(f"FAIL ({str(e)[:30]})")

    print("Warm-up complete. Starting benchmark...\n")


def benchmark_model(model: str, prompt: str, query_info: dict, context: str) -> dict:
    """Benchmark a single model with timing and quality metrics."""
    query = query_info["query"]
    expected_behavior = query_info["expected_behavior"]
    query_type = query_info["type"]

    print(f"\n{'='*60}")
    print(f"Testing: {model}")
    print(f"Query: {query}")
    print(f"Type: {query_type}")
    print("=" * 60)

    start = time.time()
    first_token_time = None
    tokens = 0
    response_text = ""
    mem_before = get_memory_usage()

    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "num_predict": 150,  # Match production max_tokens
                    "temperature": 0.1,  # Match production temperature
                },
            },
            stream=True,
            timeout=300,  # 5 minute timeout
        )

        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}: {resp.text}")

        for line in resp.iter_lines():
            if line:
                chunk = json.loads(line)
                token = chunk.get("response", "")
                if token:
                    if first_token_time is None:
                        first_token_time = time.time() - start
                        print(f"First token: {first_token_time:.2f}s")
                    tokens += 1
                    response_text += token

                if chunk.get("done", False):
                    break

        total_time = time.time() - start
        tok_per_sec = tokens / total_time if total_time > 0 else 0
        mem_after = get_memory_usage()

        # Score the response
        quality_scores = score_response(
            response_text, expected_behavior, context, query_type
        )

        print(f"Total time: {total_time:.2f}s")
        print(f"Tokens: {tokens} ({tok_per_sec:.2f} tok/s)")
        print(
            f"Response: {response_text[:150]}{'...' if len(response_text) > 150 else ''}"
        )

        # Quality indicators
        if quality_scores["hallucination_detected"]:
            print("WARNING: Possible hallucination detected!")
        if not quality_scores["instruction_followed"]:
            print("WARNING: May not have followed instructions correctly")

        return {
            "query": query,
            "query_type": query_type,
            "expected_behavior": expected_behavior,
            "model": model,
            "first_token": round(first_token_time, 2) if first_token_time else None,
            "total_time": round(total_time, 2),
            "tokens": tokens,
            "tok_per_sec": round(tok_per_sec, 2),
            "response": response_text,
            "status": "success",
            "quality": quality_scores,
            "memory": {
                "before": mem_before,
                "after": mem_after,
            },
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "query": query,
            "query_type": query_type,
            "expected_behavior": expected_behavior,
            "model": model,
            "status": "error",
            "error": str(e),
        }


def print_query_summary(results: list, query: str):
    """Print comparison table for a single query."""
    print("\n" + "=" * 80)
    print(f"RESULTS FOR: {query}")
    print("=" * 80)
    print(
        f"{'Model':<20} {'First Token':>12} {'Total Time':>12} {'Tok/s':>8} {'Quality':>12}"
    )
    print("-" * 80)

    query_results = [r for r in results if r.get("query") == query]

    for r in query_results:
        if r["status"] == "success":
            # Quality indicator
            q = r.get("quality", {})
            if q.get("hallucination_detected"):
                quality_str = "HALLUCINATE"
            elif not q.get("instruction_followed"):
                quality_str = "OFF-TOPIC"
            else:
                quality_str = "OK"

            print(
                f"{r['model']:<20} "
                f"{r['first_token']:>11.2f}s "
                f"{r['total_time']:>11.2f}s "
                f"{r['tok_per_sec']:>8.2f} "
                f"{quality_str:>12}"
            )
        else:
            print(f"{r['model']:<20} {'-':>12} {'-':>12} {'-':>8} {'ERROR':>12}")

    # Show responses for quality comparison
    print("\n" + "-" * 80)
    print("RESPONSES (for quality comparison):")
    print("-" * 80)
    for r in query_results:
        if r["status"] == "success":
            q = r.get("quality", {})
            flag = ""
            if q.get("hallucination_detected"):
                flag = " [HALLUCINATION]"
            elif not q.get("instruction_followed"):
                flag = " [OFF-TOPIC]"
            print(f"\n{r['model']}{flag}:")
            print(f"  {r['response']}")


def print_overall_summary(results: list):
    """Print overall summary across all queries."""
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY (Average across all queries)")
    print("=" * 80)

    # Group by model
    models: dict[str, dict] = {}
    for r in results:
        if r["status"] == "success":
            model = r["model"]
            if model not in models:
                models[model] = {
                    "first_tokens": [],
                    "total_times": [],
                    "tok_per_secs": [],
                    "hallucinations": 0,
                    "instruction_failures": 0,
                    "total_queries": 0,
                }
            models[model]["first_tokens"].append(r["first_token"])
            models[model]["total_times"].append(r["total_time"])
            models[model]["tok_per_secs"].append(r["tok_per_sec"])
            models[model]["total_queries"] += 1

            q = r.get("quality", {})
            if q.get("hallucination_detected"):
                models[model]["hallucinations"] += 1
            if not q.get("instruction_followed"):
                models[model]["instruction_failures"] += 1

    print(
        f"{'Model':<20} {'Avg 1st Tok':>12} {'Avg Total':>12} {'Tok/s':>8} {'Halluc':>8} {'Quality':>10}"
    )
    print("-" * 80)

    for model, data in sorted(models.items()):
        avg_first = sum(data["first_tokens"]) / len(data["first_tokens"])
        avg_total = sum(data["total_times"]) / len(data["total_times"])
        avg_toks = sum(data["tok_per_secs"]) / len(data["tok_per_secs"])
        halluc_rate = f"{data['hallucinations']}/{data['total_queries']}"
        quality_pct = (
            (
                data["total_queries"]
                - data["hallucinations"]
                - data["instruction_failures"]
            )
            / data["total_queries"]
            * 100
        )

        print(
            f"{model:<20} {avg_first:>11.2f}s {avg_total:>11.2f}s {avg_toks:>8.2f} {halluc_rate:>8} {quality_pct:>9.0f}%"
        )

    print("=" * 80)

    # Decision guidance
    print("\nDECISION CRITERIA:")
    baseline = next((m for m in models.keys() if "phi3.5" in m), None)
    if baseline and baseline in models:
        baseline_first = sum(models[baseline]["first_tokens"]) / len(
            models[baseline]["first_tokens"]
        )
        baseline_quality = (
            (
                models[baseline]["total_queries"]
                - models[baseline]["hallucinations"]
                - models[baseline]["instruction_failures"]
            )
            / models[baseline]["total_queries"]
            * 100
        )
        print(
            f"\n   Baseline (phi3.5-legacy): {baseline_first:.1f}s avg first token, {baseline_quality:.0f}% quality"
        )

        for model, data in models.items():
            if model == baseline:
                continue
            avg_first = sum(data["first_tokens"]) / len(data["first_tokens"])
            speed_improvement = (baseline_first - avg_first) / baseline_first * 100
            quality_pct = (
                (
                    data["total_queries"]
                    - data["hallucinations"]
                    - data["instruction_failures"]
                )
                / data["total_queries"]
                * 100
            )

            # Comprehensive decision logic with weighted scoring
            speed_score = max(
                0, min(100, (60 - avg_first) / 60 * 100)
            )  # 0-60s maps to 100-0
            quality_score = quality_pct

            # Weighted final score: 40% speed, 60% quality
            final_score = (speed_score * 0.4) + (quality_score * 0.6)

            # Decision matrix
            if data["hallucinations"] > 0:
                if data["hallucinations"] >= 2:
                    verdict = "REJECT - Multiple hallucinations detected"
                else:
                    verdict = "CAUTION - Hallucination detected, review carefully"
            elif final_score >= 80 and speed_improvement > 30:
                verdict = "STRONG CANDIDATE - Excellent speed/quality balance"
            elif final_score >= 70 and speed_improvement > 20:
                verdict = "GOOD CANDIDATE - Worth considering"
            elif final_score >= 60:
                verdict = "MARGINAL - Minor improvements only"
            elif avg_first > 50:
                verdict = "TOO SLOW - No meaningful speed benefit"
            else:
                verdict = "NOT RECOMMENDED - Poor speed/quality trade-off"

            # Add score breakdown
            score_detail = f"Score: {final_score:.0f}/100 (speed:{speed_score:.0f} quality:{quality_score:.0f})"

            print(f"\n   {model}:")
            print(
                f"      Speed: {avg_first:.1f}s ({speed_improvement:+.0f}% vs baseline)"
            )
            print(
                f"      Quality: {quality_pct:.0f}% (baseline: {baseline_quality:.0f}%)"
            )
            print(f"      {score_detail}")
            print(f"      --> {verdict}")


def save_results(results: list, output_path: str):
    """Save benchmark results to JSON file."""
    output: dict = {
        "timestamp": datetime.now().isoformat(),
        "ollama_version": "unknown",
        "results": results,
        "summary": {},
    }

    # Calculate summary stats
    models: dict[str, dict] = {}
    for r in results:
        if r["status"] == "success":
            model = r["model"]
            if model not in models:
                models[model] = {
                    "first_tokens": [],
                    "total_times": [],
                    "tok_per_secs": [],
                }
            models[model]["first_tokens"].append(r["first_token"])
            models[model]["total_times"].append(r["total_time"])
            models[model]["tok_per_secs"].append(r["tok_per_sec"])

    for model, data in models.items():
        output["summary"][model] = {
            "avg_first_token": round(
                sum(data["first_tokens"]) / len(data["first_tokens"]), 2
            ),
            "avg_total_time": round(
                sum(data["total_times"]) / len(data["total_times"]), 2
            ),
            "avg_tok_per_sec": round(
                sum(data["tok_per_secs"]) / len(data["tok_per_secs"]), 2
            ),
        }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_path}")


def main():
    args = parse_args()

    print("=" * 80)
    print("LLM PERFORMANCE BENCHMARK (via Ollama)")
    print("=" * 80)

    # Determine models to test
    if args.models:
        models = [m.strip() for m in args.models.split(",")]
    else:
        models = DEFAULT_MODELS

    # Determine queries to run
    if args.queries:
        queries = TEST_QUERIES[: args.queries]
    else:
        queries = TEST_QUERIES

    print(f"\nModels: {', '.join(models)}")
    print(f"Queries: {len(queries)}")

    # Check Ollama is running
    print("\nChecking Ollama service...")
    if not check_ollama_running():
        print("Ollama is not running!")
        print("\nStart Ollama first:")
        print("  Windows: Ollama should auto-start after install")
        print("  Manual: Open Ollama app or run 'ollama serve'")
        return

    print("Ollama is running")

    # Warm-up run
    if not args.skip_warmup:
        run_warmup(models)
    else:
        print("\nSkipping warm-up (results may be skewed for first model)")

    # Benchmark each query
    all_results = []

    for query_info in queries:
        query = query_info["query"]
        print(f"\n{'='*80}")
        print(f"QUERY: {query}")
        print(
            f"Type: {query_info['type']} | Expected: {query_info['expected_behavior']}"
        )
        print("=" * 80)

        # Get real context from database
        print(f"Loading context...")
        context = get_real_context(query, top_k=3)
        prompt = build_prompt(query, context)

        print(f"Prompt size: {len(prompt)} characters")

        # Benchmark each model for this query
        for model in models:
            result = benchmark_model(model, prompt, query_info, context)
            all_results.append(result)

        # Print query-specific summary
        print_query_summary(all_results, query)

    # Print overall summary
    print_overall_summary(all_results)

    # Save results to dedicated folder
    BENCHMARK_OUTPUT_DIR.mkdir(exist_ok=True)

    if args.output:
        output_path = BENCHMARK_OUTPUT_DIR / args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = BENCHMARK_OUTPUT_DIR / f"benchmark_{timestamp}.json"

    save_results(all_results, str(output_path))

    print("\nNext steps:")
    print("   1. Review response quality above")
    print("   2. If a faster model has good quality, download its GGUF file")
    print("   3. Place in ai_models/ folder")
    print("   4. Update DEFAULT_MODEL_NAME in core/config.py")


if __name__ == "__main__":
    main()
