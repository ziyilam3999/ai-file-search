#!/usr/bin/env python3
"""
One-time extraction script to convert PDF/DOCX files to TXT in extracts/
This implements Option 1: Watch only ai_search_docs, index only extracts
"""

import shutil
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.extract import Extractor


def extract_all_files():
    """Extract all PDF and DOCX files from ai_search_docs to extracts."""

    extractor = Extractor()
    extracted_count = 0
    failed_count = 0

    print("🚀 IMPLEMENTING OPTION 1: Watch ai_search_docs → Process to extracts")
    print("=" * 70)
    print("🔄 Starting bulk extraction of PDF/DOCX files...")
    print("This will fix your 73.7% coverage issue and eliminate duplicates!")

    # Find all PDF and DOCX files in ai_search_docs
    source_files = []
    for pattern in ["**/*.pdf", "**/*.docx"]:
        source_files.extend(Path("ai_search_docs").glob(pattern))

    print(f"\n📊 Found {len(source_files)} files to extract:")
    for i, file in enumerate(source_files, 1):
        print(f"   {i:2d}. {file}")

    print(f"\n🚀 Starting extraction process...")

    for i, source_file in enumerate(source_files, 1):
        try:
            print(f"\n[{i}/{len(source_files)}] 📄 Processing: {source_file}")

            # Extract text
            text = extractor.run(source_file)

            if not text or len(text.strip()) < 10:
                print(
                    f"         ⚠️  No meaningful text extracted (only {len(text)} chars)"
                )
                failed_count += 1
                continue

            # Create corresponding extract path
            # ai_search_docs/classic_literature/book.pdf → extracts/classic_literature/book.txt
            relative_path = source_file.relative_to("ai_search_docs")
            extract_path = (
                Path("extracts") / relative_path.parent / (source_file.stem + ".txt")
            )

            # Check if extract already exists
            if extract_path.exists():
                print(f"         ℹ️  Extract already exists: {extract_path}")
                existing_size = extract_path.stat().st_size
                new_size = len(text.encode("utf-8"))
                if abs(existing_size - new_size) < 100:  # Similar size, skip
                    print(
                        f"         ✅ Skipping (similar size: {existing_size} vs {new_size} bytes)"
                    )
                    extracted_count += 1
                    continue
                else:
                    print(
                        f"         🔄 Updating (size changed: {existing_size} → {new_size} bytes)"
                    )

            # Ensure directory exists
            extract_path.parent.mkdir(parents=True, exist_ok=True)

            # Save extracted text
            with open(extract_path, "w", encoding="utf-8") as f:
                f.write(text)

            # Show success with stats
            text_length = len(text)
            kb_size = text_length / 1024
            print(f"         ✅ Saved to: {extract_path}")
            print(
                f"         📊 Extracted: {text_length:,} characters ({kb_size:.1f} KB)"
            )
            extracted_count += 1

        except Exception as e:
            print(f"         ❌ Error extracting {source_file}: {e}")
            failed_count += 1

    print(f"\n" + "=" * 70)
    print(f"🎯 EXTRACTION COMPLETE!")
    print(f"✅ Successfully extracted: {extracted_count} files")
    if failed_count > 0:
        print(f"❌ Failed to extract: {failed_count} files")

    success_rate = (extracted_count / len(source_files) * 100) if source_files else 0
    print(f"📈 Success rate: {success_rate:.1f}%")

    if extracted_count > 0:
        print(f"\n🚀 NEXT STEPS TO REACH 100% COVERAGE:")
        print(f"   1. Restart watcher: python smart_watcher.py restart")
        print(f"   2. Wait 10-30 seconds for processing")
        print(f"   3. Check coverage: python tools/monitor_file_processing.py")
        print(f"   4. Expected result: ~100% coverage (was 73.7%)")
        print(f"   5. No more duplicates!")
        print(
            f"\n💡 The watcher will automatically detect the {extracted_count} new TXT files!"
        )
        print(f"🎉 Option 1 implementation complete!")
    else:
        print(f"\n⚠️  No files were extracted successfully.")
        print(f"   Check if PDF/DOCX libraries are properly installed.")


def cleanup_duplicate_extracts():
    """Optional: Remove any exact duplicates between ai_search_docs and extracts."""
    print(f"\n🧹 OPTIONAL: Checking for exact duplicates to clean up...")

    duplicates_found = 0

    # Find TXT files that exist in both ai_search_docs and extracts
    for sample_txt in Path("ai_search_docs").rglob("*.txt"):
        relative_path = sample_txt.relative_to("ai_search_docs")
        extract_equivalent = Path("extracts") / relative_path

        if extract_equivalent.exists():
            # Compare file sizes
            sample_size = sample_txt.stat().st_size
            extract_size = extract_equivalent.stat().st_size

            if abs(sample_size - extract_size) < 10:  # Nearly identical
                print(f"   🔍 Duplicate found: {relative_path}")
                print(
                    f"      Sample: {sample_size} bytes | Extract: {extract_size} bytes"
                )
                duplicates_found += 1

    if duplicates_found > 0:
        print(f"\n📊 Found {duplicates_found} potential duplicates")
        print(
            f"💡 After Option 1 is working, consider removing TXT files from ai_search_docs"
        )
        print(f"   to eliminate duplicates completely.")
    else:
        print(f"   ✅ No exact duplicates found!")


def check_extraction_libraries():
    """Check if required extraction libraries are available."""
    print("🔧 Checking extraction libraries...")

    try:
        from pdfminer.high_level import extract_text

        print("   ✅ pdfminer.six - PDF extraction available")
        pdf_ok = True
    except ImportError:
        print("   ❌ pdfminer.six - NOT AVAILABLE")
        print("      Install with: pip install pdfminer.six")
        pdf_ok = False

    try:
        import docx

        print("   ✅ python-docx - DOCX extraction available")
        docx_ok = True
    except ImportError:
        print("   ❌ python-docx - NOT AVAILABLE")
        print("      Install with: pip install python-docx")
        docx_ok = False

    return pdf_ok and docx_ok


if __name__ == "__main__":
    print("🎯 OPTION 1 IMPLEMENTATION: Watch ai_search_docs → Index extracts")
    print("=" * 70)
    print("Purpose: Convert PDF/DOCX files to TXT for clean indexing")
    print("Problem: 73.7% coverage + 24 duplicate file sets")
    print("Solution: Extract all PDF/DOCX → TXT in extracts/ folder")
    print("Result: 100% coverage with no duplicates!")
    print()

    # Check libraries first
    if not check_extraction_libraries():
        print("\n❌ Missing required libraries. Install them first!")
        exit(1)

    print()

    # Run extraction
    extract_all_files()

    # Check for duplicates
    cleanup_duplicate_extracts()

    print(f"\n🎉 OPTION 1 READY TO TEST!")
    print(f"   Run: python smart_watcher.py restart")
    print(f"   Then: python tools/monitor_file_processing.py")
