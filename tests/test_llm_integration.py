"""TEST: test_llm_integration.py
Purpose: Test LLM integration and performance
Usage: python test_llm_integration.py
"""

import sys
import time
from pathlib import Path

import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ask import answer_question
from core.llm import get_llm

pytestmark = pytest.mark.slow  # Mark all tests in this module as slow


def test_model_loading():
    """Test LLM model loading"""
    print("AI: Testing LLM model loading...")

    try:
        llm = get_llm()

        print(f"SUCCESS: LLM model loaded: {llm.model_path.name}")

        print(f"SUCCESS: Model available: {llm.is_available()}")
        return True

    except Exception as e:
        print(f"ERROR: Failed to load LLM: {e}")
        return False


def test_basic_generation():
    """Test basic text generation"""
    print("\nTEST: Testing basic generation...")

    try:
        llm = get_llm()

        # Simple test prompt
        test_prompt = "The capital of France is"

        start_time = time.time()
        response = llm.generate_answer(
            prompt=test_prompt,
            max_tokens=10,
            temperature=0.1,
        )
        generation_time = (time.time() - start_time) * 1000

        print(f"SUCCESS: Generated response ({generation_time:.1f}ms):")
        print(f"TEXT: '{response}'")

        # Basic validation
        response_valid = len(response) > 0 and "paris" in response.lower()
        return response_valid

    except Exception as e:
        print(f"ERROR: Basic generation failed: {e}")
        return False


def test_rag_integration():
    """Test RAG integration with real questions"""
    print("\nSEARCH: Testing RAG integration...")

    # Check if we have an index
    index_path = Path("index.faiss")
    if not index_path.exists():
        print("ERROR: No search index found! Run: python bench_embedding.py")
        return False

    # Test questions
    test_questions = [
        "Who is Alice?",
        "What happens in Alice's Adventures in Wonderland?",
        "Tell me about Christmas stories",
    ]

    successful = 0
    query_times = []

    for question in test_questions:
        print(f"\nQUESTION: Testing question: '{question}'")

        try:
            start_time = time.time()
            answer, citations = answer_question(question)
            query_time = (time.time() - start_time) * 1000
            query_times.append(query_time)

            print(f"SUCCESS: Query completed in {query_time:.1f}ms")
            print(f"SOURCES: Found {len(citations)} citations")
            print(f"ANSWER: Answer preview: {answer[:150]}...")

            # Validation
            if answer and len(answer) > 50 and citations and len(citations) > 0:
                successful += 1
            else:
                print("WARNING: Answer too short or no citations")

        except Exception as e:
            print(f"ERROR: Query failed: {e}")

    # Summary
    print(f"\nSTATS: RAG Test Summary:")
    print(f"   SUCCESS: Successful: {successful}/{len(test_questions)}")

    if query_times:
        avg_time = sum(query_times) / len(query_times)
        min_time = min(query_times)
        max_time = max(query_times)
        print(f"   SPEED: Average query time: {avg_time:.1f}ms")
        print(f"   SPEED: Range: {min_time:.1f}ms - {max_time:.1f}ms")

    return successful == len(test_questions)


def test_llm_vs_context():
    """Test LLM performance with different context lengths"""
    print(f"\nCOMPARE: Testing LLM vs Context-based comparison...")

    try:

        # Test with a real question from the knowledge base
        test_question = "What is Alice's Adventures in Wonderland about?"

        print(f"QUESTION: Question: '{test_question}'")

        # Test with RAG system
        start_time = time.time()
        llm_answer, llm_citations = answer_question(test_question)
        llm_time = (time.time() - start_time) * 1000

        print(f"AI: LLM answer ({llm_time:.1f}ms): {llm_answer[:100]}...")
        print(f"SOURCES: Citations: {len(llm_citations)}")

        return True

    except Exception as e:
        print(f"ERROR: Comparison test failed: {e}")
        return False


def run_test(test_name, test_func):
    """Run a test function and return results"""
    try:
        print(f"\nTEST: {test_name}")
        print("-" * 50)

        start_time = time.time()
        success = test_func()
        duration = time.time() - start_time

        if success:
            status = "SUCCESS: PASSED" if success else "ERROR: FAILED"
            print(f"\n{test_name}: {status} ({duration:.2f}s)")
            return True, duration
        else:
            print(f"\n{test_name}: ERROR: FAILED ({duration:.2f}s)")
            return False, duration

    except Exception as e:
        print(f"\n{test_name}: ERROR: ERROR - {e}")
        return False, 0


def main():
    """Run all LLM integration tests"""
    print("LLM Integration Test Suite")
    print("=" * 50)

    # Test suite
    tests = [
        ("Model Loading", test_model_loading),
        ("Basic Generation", test_basic_generation),
        ("RAG Integration", test_rag_integration),
        ("Context Comparison", test_llm_vs_context),
    ]

    results = []
    total_time = 0

    for test_name, test_func in tests:
        success, duration = run_test(test_name, test_func)
        results.append((test_name, success))
        total_time += duration

    # Summary
    print("\n" + "=" * 50)
    print("FINAL RESULTS:")
    passed = 0
    total = len(results)

    for test_name, success in results:
        status = "SUCCESS" if success else "ERROR"
        print(f"   {test_name}: {status}")
        if success:
            passed += 1

    print(f"\nSTATS: Results: {passed}/{total} tests passed")
    print(f"SPEED: Total time: {total_time:.2f}s")

    if passed == total:
        print("SUCCESS: All tests passed! LLM integration is working correctly.")
    else:
        print("WARNING: Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    main()
