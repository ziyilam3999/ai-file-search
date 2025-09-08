#!/usr/bin/env python3
"""
Citation Debug Tool

Debug tool to investigate citation mapping issues between database files
and original source files in ai_search_docs.
"""
import sqlite3
import sys
from pathlib import Path


def debug_backend_citation():
    """Debug the specific Backend System Business Rules citation issue."""
    conn = sqlite3.connect("meta.sqlite")
    cursor = conn.cursor()

    print("🔍 CITATION MAPPING DEBUG - Backend System Business Rules")
    print("=" * 70)

    # Get the specific file that's causing the issue
    cursor.execute(
        "SELECT DISTINCT file FROM meta WHERE file LIKE ?",
        ("%Backend System Business Rules%",),
    )
    results = cursor.fetchall()
    print('\n📊 FILES IN DATABASE matching "Backend System Business Rules":')
    for (file,) in results:
        print(f"  - {file}")

    # Check what files exist in the filesystem
    business_rules_path = Path("ai_search_docs/business_rules")
    if business_rules_path.exists():
        files = list(business_rules_path.glob("*Backend*"))
        print(f'\n📁 FILES IN FILESYSTEM matching "Backend":')
        for file in files:
            print(f"  - {file}")
    else:
        print(f"\n❌ Directory {business_rules_path} does not exist")

    # Also check extracts
    extracts_path = Path("extracts/business_rules")
    if extracts_path.exists():
        files = list(extracts_path.glob("*Backend*"))
        print(f'\n📄 FILES IN EXTRACTS matching "Backend":')
        for file in files:
            print(f"  - {file}")
    else:
        print(f"\n❌ Directory {extracts_path} does not exist")

    conn.close()


def debug_all_citation_mappings():
    """Debug all citation mappings to identify issues."""
    conn = sqlite3.connect("meta.sqlite")
    cursor = conn.cursor()

    print("🔍 COMPLETE CITATION MAPPING ANALYSIS")
    print("=" * 70)

    # Get all files in database
    cursor.execute("SELECT DISTINCT file FROM meta ORDER BY file")
    db_files = cursor.fetchall()

    print(f"\n📊 TOTAL FILES IN DATABASE: {len(db_files)}")

    # Categorize files
    ai_search_docs_files = []
    extract_files = []
    other_files = []

    for (file,) in db_files:
        if file.startswith("ai_search_docs/"):
            ai_search_docs_files.append(file)
        elif "\\" in file or not file.startswith("ai_search_docs/"):
            extract_files.append(file)
        else:
            other_files.append(file)

    print(f"\n📂 CITATION CATEGORIES:")
    print(
        f"  ✅ ai_search_docs/ files (correct citations): {len(ai_search_docs_files)}"
    )
    print(f"  ⚠️  extract files (incorrect citations): {len(extract_files)}")
    print(f"  ❓ other files: {len(other_files)}")

    if extract_files:
        print(f"\n⚠️  PROBLEMATIC EXTRACT FILES (should point to original PDFs):")
        for i, file in enumerate(extract_files, 1):
            print(f"  {i:2d}. {file}")

            # Try to find corresponding original file
            if "\\" in file:
                # Format: business_rules\filename.txt
                parts = file.split("\\")
                if len(parts) >= 2:
                    category = parts[0]
                    filename = parts[-1]
                    if filename.endswith(".txt"):
                        base_name = filename[:-4]

                        # Look for PDF version
                        pdf_path = Path(f"ai_search_docs/{category}/{base_name}.pdf")
                        docx_path = Path(f"ai_search_docs/{category}/{base_name}.docx")

                        if pdf_path.exists():
                            print(
                                f"      🔍 Should cite: ai_search_docs/{category}/{base_name}.pdf"
                            )
                        elif docx_path.exists():
                            print(
                                f"      🔍 Should cite: ai_search_docs/{category}/{base_name}.docx"
                            )
                        else:
                            print(
                                f"      ❌ No original found in ai_search_docs/{category}/"
                            )

    if ai_search_docs_files:
        print(f"\n✅ CORRECT CITATIONS (pointing to ai_search_docs):")
        for i, file in enumerate(ai_search_docs_files, 1):
            print(f"  {i:2d}. {file}")

    conn.close()


def test_citation_mapping_function():
    """Test the _map_to_original_file function logic."""
    from core.embedding import Embedder

    print("🧪 TESTING CITATION MAPPING FUNCTION")
    print("=" * 70)

    embedder = Embedder()

    # Test cases that should work
    test_cases = [
        "business_rules/Backend System Business Rules for Admin, Production Support, and Customer Support (2).txt",
        "business_rules/Communication, Rating, and Dispute Reporting.txt",
        "business_rules/Hosting, Finding and Swap Parking.txt",
    ]

    for test_case in test_cases:
        result = embedder._map_to_original_file(test_case)
        print(f"\n📝 INPUT:  {test_case}")
        print(f"📍 OUTPUT: {result}")

        if result:
            # Check if the mapped file actually exists
            mapped_path = Path(result)
            exists = mapped_path.exists()
            print(f"📁 EXISTS: {exists}")
        else:
            print("❌ FAILED: No mapping returned")


def main():
    """Main function with command options."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "backend":
            debug_backend_citation()
        elif command == "all":
            debug_all_citation_mappings()
        elif command == "test":
            test_citation_mapping_function()
        else:
            print("❌ Unknown command")
            print_usage()
    else:
        # Default: run backend debug
        debug_backend_citation()


def print_usage():
    """Print usage information."""
    print(
        """
🔍 Citation Debug Tool

USAGE:
    python tools/debug_citation.py [command]

COMMANDS:
    backend             Debug Backend System Business Rules citation issue
    all                 Analyze all citation mappings
    test                Test the citation mapping function

EXAMPLES:
    python tools/debug_citation.py backend
    python tools/debug_citation.py all
    python tools/debug_citation.py test
    """
    )


if __name__ == "__main__":
    main()
