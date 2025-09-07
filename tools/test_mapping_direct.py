"""Test the current embedding.py mapping function directly"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.embedding import Embedder


def test_mapping():
    """Test the embedding mapping function with business rules files"""
    print("🧪 TESTING EMBEDDING.PY MAPPING FUNCTION")
    print("=" * 60)

    embedder = Embedder()

    # Test the specific problematic file
    test_files = [
        "business_rules/Acceptance Criteria for MVP Performance .txt",
        "business_rules/Backend System Business Rules for Admin, Production Support, and Customer Support (2).txt",
        "business_rules/Communication, Rating, and Dispute Reporting.txt",
    ]

    for test_path in test_files:
        print(f"\n🔍 Testing: {test_path}")
        result = embedder._map_to_original_file(test_path)
        if result:
            print(f"✅ SUCCESS: {result}")
        else:
            print(f"❌ FAILED: No mapping found")


if __name__ == "__main__":
    test_mapping()
