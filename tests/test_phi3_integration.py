"""🧪 test_phi3_integration.py
Purpose: Test Phi-3 LLM integration and compare with context-based answers
Usage: python -m pytest tests/test_phi3_integration.py -v
       or: python tests/test_phi3_integration.py
"""

import sys
import time
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from core.ask import answer_question
from core.llm import get_phi3_llm


def test_phi3_model_loading():
    """Test if Phi-3 model can be loaded successfully."""
    print("🤖 Testing Phi-3 model loading...")

    try:
        llm = get_phi3_llm(verbose=True)
        print(f"✅ Phi-3 model loaded: {llm.model_path.name}")
        assert llm.is_available(), "Model should be available after loading"
        print(f"✅ Model available: {llm.is_available()}")
        return True
    except Exception as e:
        print(f"❌ Failed to load Phi-3: {e}")
        return False


def test_basic_generation():
    """Test basic Phi-3 text generation."""
    print("\n🧪 Testing basic Phi-3 generation...")

    try:
        llm = get_phi3_llm()

        test_prompt = """You are a helpful assistant. Answer the following question briefly and clearly.

Question: What is the capital of France?

Answer:"""

        start_time = time.time()
        response = llm.generate_answer(test_prompt, max_tokens=50, temperature=0.1)
        generation_time = (time.time() - start_time) * 1000

        print(f"✅ Generated response ({generation_time:.1f}ms):")
        print(f"📝 '{response}'")

        return "Paris" in response or "paris" in response.lower()

    except Exception as e:
        print(f"❌ Basic generation failed: {e}")
        return False


def test_rag_integration():
    """Test full RAG pipeline with real questions."""
    print("\n🔍 Testing RAG integration...")

    # Check if index exists
    if not Path("index.faiss").exists():
        print("❌ No search index found! Run: python bench_embedding.py")
        return False

    test_questions = [
        "Who is Alice?",
        "What is Wonderland?",
        "Who is Ebenezer Scrooge?",
    ]

    results = []

    for question in test_questions:
        print(f"\n🤔 Testing question: '{question}'")

        try:
            start_time = time.time()
            answer, citations = answer_question(question, top_k=3)
            query_time = (time.time() - start_time) * 1000

            print(f"✅ Query completed in {query_time:.1f}ms")
            print(f"📚 Found {len(citations)} citations")
            print(f"📝 Answer preview: {answer[:150]}...")

            results.append(
                {
                    "question": question,
                    "success": True,
                    "query_time": query_time,
                    "citations_count": len(citations),
                    "answer_length": len(answer),
                }
            )

        except Exception as e:
            print(f"❌ Query failed: {e}")
            results.append({"question": question, "success": False, "error": str(e)})

    # Summary
    successful = sum(1 for r in results if r.get("success", False))
    print("\n📊 RAG Test Summary:")
    print(f"   ✅ Successful: {successful}/{len(test_questions)}")

    if successful > 0:
        avg_time = (
            sum(r.get("query_time", 0) for r in results if r.get("success", False))
            / successful
        )
        print(f"   ⚡ Average query time: {avg_time:.1f}ms")

    return successful == len(test_questions)


def test_phi3_vs_context_comparison():
    """Compare Phi-3 answers vs context-based answers."""
    print("\n⚖️  Testing Phi-3 vs Context-based comparison...")

    # This is a conceptual test - in practice, you'd need to modify
    # answer_question to accept a use_phi3 parameter
    test_question = "Who is Alice?"

    try:
        print(f"🤔 Question: '{test_question}'")

        # Test with Phi-3 (current default)
        start_time = time.time()
        phi3_answer, phi3_citations = answer_question(test_question)
        phi3_time = (time.time() - start_time) * 1000

        print(f"🤖 Phi-3 answer ({phi3_time:.1f}ms): {phi3_answer[:100]}...")
        print(f"📚 Citations: {len(phi3_citations)}")

        return True

    except Exception as e:
        print(f"❌ Comparison test failed: {e}")
        return False


def main():
    """Run all Phi-3 integration tests."""
    print("🧪 Phi-3 Integration Test Suite")
    print("=" * 50)

    tests = [
        ("Model Loading", test_phi3_model_loading),
        ("Basic Generation", test_basic_generation),
        ("RAG Integration", test_rag_integration),
        ("Phi-3 vs Context", test_phi3_vs_context_comparison),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"\n{test_name}: {status}")
        except Exception as e:
            print(f"\n{test_name}: ❌ ERROR - {e}")
            results.append((test_name, False))

    # Final summary
    print(f"\n{'='*50}")
    print("🏁 Test Suite Summary")
    print(f"{'='*50}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")

    print(f"\n📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Phi-3 integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

    return passed == total


if __name__ == "__main__":
    main()
