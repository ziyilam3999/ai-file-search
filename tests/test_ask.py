"""Test the ask.py RAG system"""

import sys
from pathlib import Path

import pytest

# Add the project root to Python path so we can import core
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.ask import answer_question

pytestmark = pytest.mark.slow  # Mark all tests in this module as slow


def test_basic_questions():
    """Test some basic questions"""

    questions = [
        "Who is Alice?",
        "What is Wonderland?",
        "Who is Ebenezer Scrooge?",
        "What happens in the secret garden?",
        "Who is Peter Pan?",
    ]

    print("🧪 Testing RAG System\n" + "=" * 50)

    for i, question in enumerate(questions, 1):
        print(f"\n📋 Test {i}: {question}")
        print("-" * 30)

        try:
            answer, citations = answer_question(question)

            print("🤖 Answer:")
            print(answer)

            print(f"\n📚 Citations ({len(citations)} found):")
            for citation in citations:
                print(
                    f"  [{citation['id']}] {citation['file']}, page {citation['page']} (score: {citation['score']:.3f})"
                )

        except Exception as e:
            print(f"❌ Error: {e}")

        print("\n" + "=" * 50)


def test_single_question():
    """Pytest-compatible test for a single question"""
    answer, citations = answer_question("Who is Alice?")

    # Basic assertions
    assert answer is not None
    assert len(answer) > 0
    assert isinstance(citations, list)
    assert len(citations) > 0

    # Check citation format
    first_citation = citations[0]
    assert "id" in first_citation
    assert "file" in first_citation
    assert "page" in first_citation
    assert "score" in first_citation


if __name__ == "__main__":
    test_basic_questions()
