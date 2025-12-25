"""
AI File Search - Quick Smoke Test
=================================

A lightweight test script for quick validation of core functionality.
Perfect for daily development and CI/CD pipelines.

Usage:
    python test_quick.py
"""

import sys
import time
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ask import answer_question
from core.embedding import Embedder

pytestmark = pytest.mark.slow  # Mark all tests in this module as slow


def test_core_functionality():
    """Quick smoke test of core AI search functionality."""
    print("🔍 AI File Search - Quick Smoke Test")
    print("=" * 40)

    # Test 1: System files exist
    print("1️⃣  Checking system files...")
    required_files = ["index.faiss", "meta.sqlite", "core/ask.py"]
    missing = [f for f in required_files if not Path(f).exists()]
    if missing:
        print(f"❌ Missing files: {missing}")
        return False
    print("✅ System files OK")

    # Test 2: Embedder works
    print("2️⃣  Testing embedder...")
    try:
        embedder = Embedder()
        results = embedder.query("test", k=1)
        if not results or len(results[0]) != 5:
            print("❌ Embedder failed")
            return False
        print(f"✅ Embedder OK (score: {results[0][4]:.3f})")
    except Exception as e:
        print(f"❌ Embedder error: {e}")
        return False

    # Test 3: Relevant query with citations
    print("3️⃣  Testing relevant query...")
    try:
        start_time = time.time()
        answer, citations = answer_question("parking hosting", top_k=1)
        query_time = time.time() - start_time

        if not citations or len(citations) == 0:
            print("❌ No citations for relevant query")
            return False

        if "business_rules" not in citations[0].get("file", ""):
            print("❌ Wrong citation file")
            return False

        print(f"✅ Relevant query OK ({len(citations)} citations, {query_time:.1f}s)")
    except Exception as e:
        print(f"❌ Relevant query error: {e}")
        return False

    # Test 4: Irrelevant query filtering
    print("4️⃣  Testing irrelevant query...")
    try:
        answer, citations = answer_question("cryptocurrency blockchain", top_k=1)
        expected_msg = "I couldn't find relevant information"

        if expected_msg not in answer:
            print(f"❌ Irrelevant query not filtered: {answer[:50]}...")
            return False

        if citations:
            print(f"❌ Irrelevant query has citations: {len(citations)}")
            return False

        print("✅ Irrelevant query filtered OK")
    except Exception as e:
        print(f"❌ Irrelevant query error: {e}")
        return False

    # Test 5: No hallucinated citations
    print("5️⃣  Testing citation authenticity...")
    try:
        answer, citations = answer_question("token economy", top_k=1)

        # Check for hallucination indicators
        hallucination_signs = ["Investopedia", "Wikipedia", "Retrieved", "www.", ".com"]
        for sign in hallucination_signs:
            if sign in answer:
                print(f"❌ Possible hallucination detected: {sign}")
                return False

        # Check citation files exist
        for citation in citations:
            file_path = citation.get("file", "")
            if not Path(file_path).exists():
                print(f"❌ Citation file doesn't exist: {file_path}")
                return False

        print("✅ Citations authentic OK")
    except Exception as e:
        print(f"❌ Citation test error: {e}")
        return False

    print("=" * 40)
    print("🎉 ALL SMOKE TESTS PASSED!")
    return True


if __name__ == "__main__":
    success = test_core_functionality()
    exit(0 if success else 1)
