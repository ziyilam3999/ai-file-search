#!/usr/bin/env python3
"""
Debug filename mapping between extracts/ and ai_search_docs/
Helps identify why some files aren't being indexed correctly.
"""

import unicodedata
from difflib import SequenceMatcher
from pathlib import Path


def normalize_filename(name: str) -> str:
    """Normalize filename for robust comparison."""
    # Remove extensions
    if name.endswith((".txt", ".pdf", ".docx", ".md")):
        name = name.rsplit(".", 1)[0]

    # Normalize Unicode characters
    normalized = unicodedata.normalize("NFKC", name)

    # Strip whitespace and normalize internal spaces
    return " ".join(normalized.split())


def fuzzy_match_file(base_name: str, directory: Path, threshold: float = 0.85) -> str:
    """Find best matching file using fuzzy string matching."""
    if not directory.exists():
        return "Directory does not exist"

    best_match = None
    best_score = threshold
    normalized_base = normalize_filename(base_name)

    print(f"Looking for '{normalized_base}' in {directory}")

    for file_path in directory.iterdir():
        if file_path.is_file():
            normalized_file = normalize_filename(file_path.stem)
            similarity = SequenceMatcher(None, normalized_base, normalized_file).ratio()

            print(
                f"  Compare: '{normalized_base}' vs '{normalized_file}' = {similarity:.3f}"
            )

            if similarity > best_score:
                best_match = file_path
                best_score = similarity

    if best_match:
        return f"MATCH: {best_match.name} (score: {best_score:.3f})"
    else:
        return f"NO MATCH found above threshold {threshold}"


def debug_filename_mapping():
    """Debug the filename mapping process."""
    print("🔍 DEBUGGING FILENAME MAPPING")
    print("=" * 60)

    # Test the problematic file
    test_file = "business_rules/Acceptance Criteria for MVP Performance .txt"
    print(f"\n📋 Testing: {test_file}")

    # Parse path
    path_parts = test_file.split("/")
    category = path_parts[0]
    filename_txt = path_parts[-1]

    print(f"  Category: {category}")
    print(f"  Filename: '{filename_txt}'")

    # Check character-by-character
    print(f"\n🔤 Character Analysis:")
    for i, char in enumerate(filename_txt):
        print(
            f"  [{i:2d}] '{char}' (U+{ord(char):04X}) {unicodedata.name(char, 'UNNAMED')}"
        )

    # Normalize
    normalized = normalize_filename(filename_txt)
    print(f"\n✨ Normalized: '{normalized}'")

    # Check what exists in ai_search_docs
    ai_search_docs_dir = Path("ai_search_docs/business_rules")
    print(f"\n📁 Files in {ai_search_docs_dir}:")

    if ai_search_docs_dir.exists():
        for file_path in ai_search_docs_dir.iterdir():
            if file_path.is_file():
                normalized_existing = normalize_filename(file_path.stem)
                print(f"  📄 {file_path.name}")
                print(f"     Normalized: '{normalized_existing}'")
                print(
                    f"     Match score: {SequenceMatcher(None, normalized, normalized_existing).ratio():.3f}"
                )
                print()

    # Test fuzzy matching
    print(f"\n🎯 Fuzzy Match Result:")
    result = fuzzy_match_file(filename_txt, ai_search_docs_dir)
    print(f"  {result}")


def test_all_business_rules():
    """Test mapping for all business rules files."""
    print("\n🏢 TESTING ALL BUSINESS RULES FILES")
    print("=" * 60)

    extracts_dir = Path("extracts/business_rules")
    if not extracts_dir.exists():
        print("❌ extracts/business_rules directory not found")
        return

    ai_search_docs_dir = Path("ai_search_docs/business_rules")
    if not ai_search_docs_dir.exists():
        print("❌ ai_search_docs/business_rules directory not found")
        return

    # Test each extract file
    for extract_file in extracts_dir.glob("*.txt"):
        filename = extract_file.name
        print(f"\n📋 Testing: {filename}")

        normalized = normalize_filename(filename)
        print(f"  Normalized: '{normalized}'")

        # Find best match
        best_match = None
        best_score = 0

        for sample_file in ai_search_docs_dir.iterdir():
            if sample_file.is_file():
                sample_normalized = normalize_filename(sample_file.stem)
                score = SequenceMatcher(None, normalized, sample_normalized).ratio()

                if score > best_score:
                    best_match = sample_file
                    best_score = score

        if best_match and best_score > 0.85:
            print(f"  ✅ MATCH: {best_match.name} (score: {best_score:.3f})")
        else:
            print(f"  ❌ NO MATCH (best score: {best_score:.3f})")


def detailed_comparison():
    """Detailed comparison of the problematic file."""
    print("\n🔬 DETAILED COMPARISON")
    print("=" * 60)

    extract_name = "Acceptance Criteria for MVP Performance .txt"
    sample_name = "Acceptance Criteria for MVP Performance .pdf"

    print(f"Extract: '{extract_name}'")
    print(f"Sample:  '{sample_name}'")

    # Character by character comparison
    print(f"\nCharacter-by-character comparison:")
    extract_base = extract_name.replace(".txt", "")
    sample_base = sample_name.replace(".pdf", "")

    print(f"Extract base: '{extract_base}' (len: {len(extract_base)})")
    print(f"Sample base:  '{sample_base}' (len: {len(sample_base)})")

    # Normalize both
    extract_norm = normalize_filename(extract_name)
    sample_norm = normalize_filename(sample_name)

    print(f"\nNormalized:")
    print(f"Extract: '{extract_norm}' (len: {len(extract_norm)})")
    print(f"Sample:  '{sample_norm}' (len: {len(sample_norm)})")

    # Compare
    similarity = SequenceMatcher(None, extract_norm, sample_norm).ratio()
    print(f"\nSimilarity: {similarity:.6f}")

    # Test exact match
    if extract_norm == sample_norm:
        print("✅ EXACT MATCH after normalization")
    else:
        print("❌ NO EXACT MATCH")
        # Show differences
        for i, (c1, c2) in enumerate(zip(extract_norm, sample_norm)):
            if c1 != c2:
                print(f"  Diff at pos {i}: '{c1}' vs '{c2}'")


if __name__ == "__main__":
    debug_filename_mapping()
    test_all_business_rules()
    detailed_comparison()

    print("\n" + "=" * 60)

    # Simulate the exact logic from embedding.py
    def test_map_to_original_file(extracts_rel_path: str) -> str:
        """Test version of the mapping function with proper return type."""
        print(f"Input: {extracts_rel_path}")

        # Parse the extracts path
        path_parts = extracts_rel_path.split("/")
        if len(path_parts) < 2:
            potential_original = f"ai_search_docs/{extracts_rel_path}"
            return (
                potential_original
                if Path(potential_original).exists()
                else "No match found"
            )

        category = path_parts[0]  # e.g., 'business_rules'
        filename_txt = path_parts[-1]  # e.g., 'file.txt'

        print(f"  Category: {category}")
        print(f"  Filename: {filename_txt}")

        # Remove .txt extension to get base name
        if filename_txt.endswith(".txt"):
            base_name = filename_txt[:-4]
        elif filename_txt.endswith(".md"):
            base_name = filename_txt[:-3]
        else:
            base_name = filename_txt

        print(f'  Base name: "{base_name}"')

        # Check what original file exists in ai_search_docs
        ai_search_docs_category = Path(f"ai_search_docs/{category}")
        print(f"  Checking: {ai_search_docs_category}")

        if ai_search_docs_category.exists():
            # Look for PDF first, then DOCX, then TXT, then MD
            for ext in [".pdf", ".docx", ".txt", ".md"]:
                original_file = ai_search_docs_category / f"{base_name}{ext}"
                print(
                    f"    Testing: {original_file} | Exists: {original_file.exists()}"
                )
                if original_file.exists():
                    return str(original_file).replace("\\", "/")

        return "No match found"

    # Test problematic files
    test_files = [
        "business_rules/Acceptance Criteria for MVP Performance .txt",
        "business_rules/Backend System Business Rules for Admin, Production Support, and Customer Support (2).txt",
        "business_rules/Communication, Rating, and Dispute Reporting.txt",
    ]

    print("\n🧪 TESTING MAP FUNCTION:")
    for test_file in test_files:
        print(f"\n📋 {test_file}")
        result = test_map_to_original_file(test_file)
        print(f"  ➤ Result: {result}")
