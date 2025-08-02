"""TEST: test_simple_rag.py
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
    print("TESTING: simplified prompt...")

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

        print(f"SUCCESS: Simplified prompt response: '{response}'")
        return response

    except Exception as e:
        print(f"ERROR: Simplified prompt failed: {e}")
        return None


def test_without_chatml():
    """Test by creating a new LLM instance without ChatML format."""
    print("\nTESTING: without ChatML format...")

    try:
        from llama_cpp import Llama

        model_path = (
            Path(__file__).parent.parent
            / "ai_models"
            / "Phi-3-mini-4k-instruct-q4.gguf"
        )

        if not model_path.exists():
            print("ERROR: Model file not found")
            return None

        # Create LLM instance without chat_format
        llm = Llama(
            model_path=str(model_path),
            n_ctx=512,
            n_threads=4,
            verbose=False,
        )

        # Simple text completion
        simple_text = "The capital of France is"

        result = llm.create_completion(
            prompt=simple_text,
            max_tokens=10,
            temperature=0.1,
            stop=["\n"],
        )

        answer = result["choices"][0]["text"].strip()
        print(f"SUCCESS: Raw completion: '{answer}'")
        return answer

    except Exception as e:
        print(f"ERROR: Raw completion failed: {e}")
        return None


def test_current_rag():
    """Test current RAG system."""
    print("\nTESTING: current RAG system...")

    try:
        answer, citations = answer_question("Who is Alice?")
        print(f"RAG Answer: {answer[:100]}...")
        return answer
    except Exception as e:
        print(f"ERROR: Current RAG failed: {e}")
        return None


def test_very_short():
    """Test with very short max_tokens."""
    print("\nTESTING: very short generation...")

    try:
        llm = get_phi3_llm()

        # Extremely short prompt
        prompt = "Paris is"

        response = llm.generate_answer(
            prompt=prompt,
            max_tokens=5,
            temperature=0.0,
        )

        print(f"SUCCESS: Very short response: '{response}'")
        return response

    except Exception as e:
        print(f"ERROR: Very short test failed: {e}")
        return None


def main():
    print("TEST: Simple RAG Test Tool")
    print("=" * 40)

    # Run all tests
    simple_result = test_simplified_prompt()
    raw_result = test_without_chatml()
    rag_result = test_current_rag()
    very_short_result = test_very_short()

    # Summary
    print("\n" + "=" * 40)
    print("TEST RESULTS:")
    print(
        f"Very short test: {'SUCCESS' if very_short_result and len(very_short_result) > 3 else 'ERROR'}"
    )
    print(
        f"Simplified prompt: {'SUCCESS' if simple_result and len(simple_result) > 10 else 'ERROR'}"
    )
    print(
        f"Raw completion: {'SUCCESS' if raw_result and len(raw_result) > 5 else 'ERROR'}"
    )
    print(
        f"Current RAG: {'ERROR' if rag_result and ('context' in rag_result.lower() or len(rag_result) < 50) else 'SUCCESS'}"
    )

    print("\nANALYSIS:")
    if simple_result or raw_result:
        print("SUCCESS: Basic generation works - issue is with long prompts")
    else:
        print("ERROR: Basic generation fails - fundamental model issue")

    if raw_result:
        print("SUCCESS: Raw completion works - ChatML might be the issue")
    else:
        print("ERROR: Raw completion fails - not a ChatML issue")


if __name__ == "__main__":
    main()
