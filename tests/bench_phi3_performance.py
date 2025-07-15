"""⚡ bench_phi3_performance.py
Purpose: Benchmark Phi-3 performance and compare generation modes
Usage: python tests/bench_phi3_performance.py
"""

import sys
import time
from pathlib import Path
from statistics import mean, median
from typing import List

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ask import answer_question
from core.llm import get_phi3_llm


def benchmark_phi3_loading():
    """Benchmark Phi-3 model loading time."""
    print("🤖 Benchmarking Phi-3 model loading...")

    # Clear any existing instance
    from core import llm

    llm._phi3_instance = None

    start_time = time.time()
    get_phi3_llm()
    load_time = time.time() - start_time

    print(f"⚡ Model loading time: {load_time:.2f}s")
    return load_time


def benchmark_generation_speed(num_tests: int = 5):
    """Benchmark answer generation speed."""
    print(f"\n🧪 Benchmarking generation speed ({num_tests} tests)...")

    test_questions = [
        "Who is Alice?",
        "What is Wonderland?",
        "Who is Ebenezer Scrooge?",
        "What happens in the secret garden?",
        "Who is Peter Pan?",
    ]

    times = []

    for i in range(num_tests):
        question = test_questions[i % len(test_questions)]
        print(f"Test {i+1}/{num_tests}: '{question}'")

        start_time = time.time()
        try:
            answer, citations = answer_question(question)
            query_time = (time.time() - start_time) * 1000
            times.append(query_time)
            print(
                f"   ⚡ {query_time:.1f}ms ({len(answer)} chars, {len(citations)} citations)"
            )
        except Exception as e:
            print(f"   ❌ Failed: {e}")

    if times:
        print("\n📊 Generation Performance:")
        print(f"   Average: {mean(times):.1f}ms")
        print(f"   Median:  {median(times):.1f}ms")
        print(f"   Min:     {min(times):.1f}ms")
        print(f"   Max:     {max(times):.1f}ms")

    return times


def benchmark_token_generation():
    """Benchmark raw token generation speed."""
    print("\n🔤 Benchmarking token generation...")

    try:
        llm = get_phi3_llm()

        test_prompt = """Answer the following question in detail:

Question: Describe Alice's adventures in Wonderland.

Answer:"""

        start_time = time.time()
        response = llm.generate_answer(
            prompt=test_prompt, max_tokens=200, temperature=0.1
        )
        generation_time = time.time() - start_time

        token_count = len(response.split())  # Rough token estimate
        tokens_per_second = token_count / generation_time if generation_time > 0 else 0

        print(f"⚡ Generated {token_count} tokens in {generation_time:.2f}s")
        print(f"📈 Speed: {tokens_per_second:.1f} tokens/second")

        return tokens_per_second

    except Exception as e:
        print(f"❌ Token generation benchmark failed: {e}")
        return 0


def main():
    """Run performance benchmarks."""
    print("⚡ Phi-3 Performance Benchmark")
    print("=" * 50)

    # 1. Model loading
    load_time = benchmark_phi3_loading()

    # 2. Generation speed
    generation_times = benchmark_generation_speed(3)

    # 3. Token generation speed
    token_speed = benchmark_token_generation()

    # Summary
    print(f"\n{'='*50}")
    print("🏁 Performance Summary")
    print(f"{'='*50}")
    print(f"🤖 Model loading:     {load_time:.2f}s")

    if generation_times:
        avg_gen_time = mean(generation_times)
        print(f"🔍 Average query:     {avg_gen_time:.1f}ms")

    if token_speed > 0:
        print(f"🔤 Token generation:  {token_speed:.1f} tokens/s")

    # Performance targets
    print("\n🎯 Performance Assessment:")
    if load_time < 10:
        print("✅ Model loading: Excellent (< 10s)")
    elif load_time < 30:
        print("⚠️  Model loading: Acceptable (< 30s)")
    else:
        print("❌ Model loading: Slow (> 30s)")

    # Industry benchmarks for local LLM RAG systems:
    if generation_times and mean(generation_times) < 60000:  # 60s
        print("✅ Query speed: Excellent (< 60s)")
    elif generation_times and mean(generation_times) < 120000:  # 120s
        print("⚠️  Query speed: Good (< 120s)")
    elif generation_times and mean(generation_times) < 300000:  # 300s
        print("⚠️  Query speed: Acceptable (< 300s)")
    else:
        print("❌ Query speed: Slow (> 300s)")


if __name__ == "__main__":
    main()
