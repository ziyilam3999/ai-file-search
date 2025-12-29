"""🔧 debug_llm.py
Purpose: Debug LLM generation issues
Usage: python debug_llm.py
"""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.llm import get_llm


def test_simple_generation():
    """Test very simple generation."""
    print("🧪 Testing simple LLM generation...")

    llm = get_llm()

    # Very simple prompt
    simple_prompt = "The capital of France is"

    print(f"Prompt: '{simple_prompt}'")

    response = llm.generate_answer(
        prompt=simple_prompt,
        max_tokens=10,
        temperature=0.0,
    )

    print(f"Response: '{response}'")
    return response


def test_chat_format():
    """Test with explicit chat format."""
    print("\n🧪 Testing chat format...")

    llm = get_llm()

    # Test the raw llama.cpp chat completion
    try:
        response = llm.llm.create_chat_completion(
            messages=[
                {
                    "role": "user",
                    "content": "What is the capital of France? Answer briefly.",
                }
            ],
            max_tokens=20,
            temperature=0.0,
        )

        answer = response["choices"][0]["message"]["content"]
        print(f"Chat response: '{answer}'")
        return answer

    except Exception as e:
        print(f"Chat format failed: {e}")
        return None


def test_without_chat_format():
    """Test direct text completion."""
    print("\n🧪 Testing direct completion...")

    llm = get_llm()

    try:
        response = llm.llm.create_completion(
            prompt="Question: What is the capital of France?\nAnswer:",
            max_tokens=20,
            temperature=0.0,
            stop=["\n"],
        )

        answer = response["choices"][0]["text"]
        print(f"Direct completion: '{answer}'")
        return answer

    except Exception as e:
        print(f"Direct completion failed: {e}")
        return None


def test_rag_context():
    """Test with a shorter RAG-style prompt."""
    print("\n🧪 Testing RAG-style prompt...")

    llm = get_llm()

    short_prompt = """Answer this question based on the context:

Context: Alice is the main character in Lewis Carroll's "Alice's Adventures in Wonderland." She is a curious young girl who falls down a rabbit hole.

Question: Who is Alice?

Answer:"""

    try:
        response = llm.generate_answer(
            prompt=short_prompt,
            max_tokens=100,
            temperature=0.1,
        )

        print(f"RAG response: '{response}'")
        return response

    except Exception as e:
        print(f"RAG test failed: {e}")
        return None


def main():
    print("🔧 LLM Debug Tool")
    print("=" * 50)

    # Test 1: Simple generation
    simple_result = test_simple_generation()

    # Test 2: Chat format
    chat_result = test_chat_format()

    # Test 3: Direct completion
    direct_result = test_without_chat_format()

    # Test 4: RAG-style prompt
    rag_result = test_rag_context()

    print(f"\n{'='*50}")
    print("🏁 Debug Summary")
    print(f"{'='*50}")
    print(
        f"Simple generation: {'✅' if simple_result and 'Paris' in simple_result else '❌'} - '{simple_result}'"
    )
    print(
        f"Chat format: {'✅' if chat_result and 'Paris' in chat_result else '❌'} - '{chat_result}'"
    )
    print(
        f"Direct completion: {'✅' if direct_result and 'Paris' in direct_result else '❌'} - '{direct_result}'"
    )
    print(
        f"RAG test: {'✅' if rag_result and 'Alice' in rag_result else '❌'} - First 100 chars: '{rag_result[:100] if rag_result else None}'"
    )


if __name__ == "__main__":
    main()
