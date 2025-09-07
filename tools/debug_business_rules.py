"""Debug business rules mapping issues in embedding.py"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unicodedata
from difflib import SequenceMatcher
from pathlib import Path


def debug_filename_issues():
    """Debug filename encoding and path issues for business rules"""
    print("🔍 DEBUGGING BUSINESS RULES FILENAME ISSUES")
    print("=" * 70)

    # Check if directories exist
    extracts_dir = Path("extracts/business_rules")
    sample_docs_dir = Path("sample_docs/business_rules")

    print(f"📂 Extracts directory exists: {extracts_dir.exists()}")
    print(f"📂 Sample docs directory exists: {sample_docs_dir.exists()}")

    if not extracts_dir.exists() or not sample_docs_dir.exists():
        print("❌ Required directories missing!")
        return

    # Get all files
    extract_files = list(extracts_dir.glob("*.txt"))
    sample_files = list(sample_docs_dir.glob("*.pdf"))

    print(
        f"\n📊 Found {len(extract_files)} extract files, {len(sample_files)} sample files"
    )

    # Test the problematic file specifically
    problem_file = "Acceptance Criteria for MVP Performance .txt"
    extract_path = extracts_dir / problem_file

    print(f"\n🎯 TESTING PROBLEMATIC FILE: {problem_file}")
    print(f"   Extract file exists: {extract_path.exists()}")

    if extract_path.exists():
        print(f"   Extract file size: {extract_path.stat().st_size} bytes")

        # Test Unicode normalization
        base_name = problem_file[:-4]  # Remove .txt
        normalized = unicodedata.normalize("NFKC", base_name).strip()
        cleaned = " ".join(normalized.split())

        print(f"   Original base: '{base_name}' (len: {len(base_name)})")
        print(f"   Normalized: '{normalized}' (len: {len(normalized)})")
        print(f"   Cleaned: '{cleaned}' (len: {len(cleaned)})")

        # Test against sample files
        print(f"\n🔎 TESTING AGAINST SAMPLE FILES:")
        for sample_file in sample_files:
            sample_base = sample_file.stem
            sample_normalized = unicodedata.normalize("NFKC", sample_base).strip()
            sample_cleaned = " ".join(sample_normalized.split())

            # Calculate similarity
            similarity = SequenceMatcher(None, cleaned, sample_cleaned).ratio()

            if "Acceptance Criteria" in sample_base:
                print(f"   🎯 MATCH CANDIDATE: {sample_file.name}")
                print(f"      Sample base: '{sample_base}' (len: {len(sample_base)})")
                print(
                    f"      Sample normalized: '{sample_normalized}' (len: {len(sample_normalized)})"
                )
                print(
                    f"      Sample cleaned: '{sample_cleaned}' (len: {len(sample_cleaned)})"
                )
                print(f"      Similarity: {similarity:.4f}")
                print(f"      Exact match: {cleaned == sample_cleaned}")

                # Byte comparison
                print(f"      Extract bytes: {cleaned.encode('utf-8')}")
                print(f"      Sample bytes: {sample_cleaned.encode('utf-8')}")

                # Test if the PDF file actually exists
                test_pdf = sample_docs_dir / f"{cleaned}.pdf"
                print(f"      Test path exists: {test_pdf.exists()}")


def test_direct_path_checks():
    """Test direct path existence checks"""
    print(f"\n🧪 DIRECT PATH EXISTENCE TESTS")
    print("=" * 50)

    sample_docs_dir = Path("sample_docs/business_rules")

    # Test variations of the problematic filename
    test_names = [
        "Acceptance Criteria for MVP Performance .pdf",
        "Acceptance Criteria for MVP Performance.pdf",  # No trailing space
        "Acceptance Criteria for MVP Performance .pdf",  # With space
    ]

    for name in test_names:
        test_path = sample_docs_dir / name
        print(f"Testing: '{name}' → Exists: {test_path.exists()}")

        if test_path.exists():
            print(f"   ✅ FOUND: {test_path}")
            print(f"   Size: {test_path.stat().st_size} bytes")


if __name__ == "__main__":
    debug_filename_issues()
    test_direct_path_checks()
