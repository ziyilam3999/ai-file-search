"""🔧 test_simple_rag.py
Purpose: Test simplified RAG with Phi-3
Usage: python test_simple_rag.py
"""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.ask import answer_question
from core.llm import get_phi3_llm


def test_simplified_prompt():
    """Test with a much simpler prompt format."""
    print("🧪 Testing simplified prompt...")

    llm = get_phi3_llm()

    # Much simpler prompt - no markdown formatting
    simple_prompt = """Based on the following information, answer the question:

Information: Alice is the main character in Lewis Carroll's Alice's Adventures in Wonderland. She is a curious young girl who falls down a rabbit hole and discovers a fantastical world filled with peculiar creatures.

Question: Who is Alice?

Answer: Alice is"""

    try:
        response = llm.generate_answer(
            prompt=simple_prompt,
            max_tokens=100,
            temperature=0.1,
            stop_sequences=["\n\n", "Question:", "Information:"],
        )

        print(f"✅ Simplified prompt response: '{response}'")
        return response

    except Exception as e:
        print(f"❌ Simplified prompt failed: {e}")
        return None


def test_without_chatml():
    """Test by creating a new LLM instance without ChatML format."""
    print("\n🧪 Testing without ChatML format...")

    try:
        from llama_cpp import Llama

        model_path = (
            Path(__file__).parent / "ai_models" / "Phi-3-mini-4k-instruct-q4.gguf"
        )

        # Create Llama instance without chat_format
        llm_raw = Llama(
            model_path=str(model_path),
            n_ctx=4096,
            n_threads=4,
            verbose=False,
            # No chat_format specified
        )

        prompt = "Question: Who is Alice from Alice in Wonderland?\nAnswer:"

        response = llm_raw.create_completion(
            prompt=prompt, max_tokens=50, temperature=0.1, stop=["\n", "Question:"]
        )

        answer = response["choices"][0]["text"].strip()
        print(f"✅ Raw completion: '{answer}'")
        return answer

    except Exception as e:
        print(f"❌ Raw completion failed: {e}")
        return None


def test_current_rag():
    """Test current RAG system for comparison."""
    print("\n🧪 Testing current RAG system...")

    try:
        answer, citations = answer_question("Who is Alice?", top_k=2)
        print(f"RAG answer preview: '{answer[:200]}...'")
        print(f"Citations count: {len(citations)}")
        return answer

    except Exception as e:
        print(f"❌ Current RAG failed: {e}")
        return None


def test_very_short_context():
    """Test with minimal context to isolate the issue."""
    print("\n🧪 Testing with very short context...")

    llm = get_phi3_llm()

    # Extremely short prompt
    short_prompt = "Who is Alice? Answer:"

    try:
        response = llm.generate_answer(
            prompt=short_prompt,
            max_tokens=50,
            temperature=0.1,
            stop_sequences=["\n", "?"],
        )

        print(f"✅ Very short response: '{response}'")
        return response

    except Exception as e:
        print(f"❌ Very short test failed: {e}")
        return None


def main():
    print("🔧 Simple RAG Test Tool")
    print("=" * 50)

    # Test 1: Very short context first
    very_short_result = test_very_short_context()

    # Test 2: Simplified prompt
    simple_result = test_simplified_prompt()

    # Test 3: Without ChatML
    raw_result = test_without_chatml()

    # Test 4: Current RAG for comparison
    rag_result = test_current_rag()

    print(f"\n{'='*50}")
    print("🏁 Test Summary")
    print(f"{'='*50}")
    print(
        f"Very short test: {'✅' if very_short_result and len(very_short_result) > 3 else '❌'}"
    )
    print(
        f"Simplified prompt: {'✅' if simple_result and len(simple_result) > 10 else '❌'}"
    )
    print(f"Raw completion: {'✅' if raw_result and len(raw_result) > 5 else '❌'}")
    print(
        f"Current RAG: {'❌' if rag_result and ('context' in rag_result.lower() or len(rag_result) < 50) else '✅'}"
    )

    # Analysis
    print("\n🔍 Analysis:")
    if very_short_result and len(very_short_result) > 3:
        print("✅ Basic generation works - issue is with long prompts")
    else:
        print("❌ Basic generation fails - fundamental model issue")

    if raw_result and "Alice" in raw_result:
        print("✅ Raw completion works - ChatML might be the issue")
    else:
        print("❌ Raw completion fails - not a ChatML issue")


if __name__ == "__main__":
    main()
