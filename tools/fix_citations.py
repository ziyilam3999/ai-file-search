#!/usr/bin/env python3
"""
Fix Citation Mapping

Script to fix incorrect citations in the database that point to extracted .txt files
instead of original PDF files in sample_docs.

This tool ensures ALL citations point to sample_docs/ files, never to extracts/.
"""
import sqlite3
import sys
from pathlib import Path


def fix_citation_mappings():
    """Fix citation mappings in the database."""
    conn = sqlite3.connect("meta.sqlite")
    cursor = conn.cursor()

    print("🔧 FIXING CITATION MAPPINGS")
    print("=" * 60)

    # Get all problematic files (those NOT starting with sample_docs/)
    cursor.execute('SELECT DISTINCT file FROM meta WHERE file NOT LIKE "sample_docs/%"')
    problematic_files = cursor.fetchall()

    if not problematic_files:
        print(
            "✅ No problematic files found! All citations already point to sample_docs/"
        )
        conn.close()
        return

    print(f"📊 Found {len(problematic_files)} files to fix:")

    fixes_made = 0
    skipped_files = 0

    for i, (old_file,) in enumerate(problematic_files, 1):
        print(f"\n{i:2d}. FIXING: {old_file}")

        new_file = None

        # Handle different path formats
        if "\\" in old_file:
            # Format: business_rules\filename.txt
            parts = old_file.split("\\")
        elif "/" in old_file and not old_file.startswith("sample_docs/"):
            # Format: business_rules/filename.txt
            parts = old_file.split("/")
        else:
            # Single file or unknown format
            parts = [old_file]

        if len(parts) >= 2:
            category = parts[0]
            filename = parts[-1]

            # Remove file extensions to get base name
            base_name = filename
            if filename.endswith(".txt"):
                base_name = filename[:-4]
            elif filename.endswith(".md"):
                base_name = filename[:-3]

            # Look for original file in sample_docs
            sample_docs_category = Path(f"sample_docs/{category}")
            if sample_docs_category.exists():
                # Priority order: PDF > DOCX > TXT > MD
                for ext in [".pdf", ".docx", ".txt", ".md"]:
                    original_file = sample_docs_category / f"{base_name}{ext}"
                    if original_file.exists():
                        new_file = str(original_file).replace("\\", "/")
                        break

        elif len(parts) == 1:
            # Root level file - check if it exists in sample_docs root
            root_file = Path(f"sample_docs/{parts[0]}")
            if root_file.exists():
                new_file = str(root_file).replace("\\", "/")

        if new_file:
            print(f"    ✅ MAPPING: {old_file} → {new_file}")

            # Update the database
            cursor.execute(
                "UPDATE meta SET file = ? WHERE file = ?", (new_file, old_file)
            )
            rows_updated = cursor.rowcount
            fixes_made += rows_updated
            print(f"    📊 Updated {rows_updated} database records")

        else:
            print(f"    ❌ NO ORIGINAL FOUND - keeping as is")
            skipped_files += 1

    if fixes_made > 0:
        conn.commit()
        print(f"\n🎉 SUCCESS: Fixed {fixes_made} database records")
        print("💾 Changes saved to database")

        if skipped_files > 0:
            print(f"⚠️  Skipped {skipped_files} files (no originals found)")
    else:
        print(f"\n⚠️  No fixes were made")

    conn.close()


def preview_fixes():
    """Preview what fixes would be made without changing the database."""
    conn = sqlite3.connect("meta.sqlite")
    cursor = conn.cursor()

    print("👀 PREVIEW CITATION FIXES")
    print("=" * 60)

    # Get all problematic files
    cursor.execute('SELECT DISTINCT file FROM meta WHERE file NOT LIKE "sample_docs/%"')
    problematic_files = cursor.fetchall()

    if not problematic_files:
        print(
            "✅ No problematic files found! All citations already point to sample_docs/"
        )
        conn.close()
        return

    print(f"📊 Would fix {len(problematic_files)} files:")

    fixes_count = 0
    skips_count = 0

    for i, (old_file,) in enumerate(problematic_files, 1):
        print(f"\n{i:2d}. {old_file}")

        new_file = None

        # Handle different path formats
        if "\\" in old_file:
            parts = old_file.split("\\")
        elif "/" in old_file and not old_file.startswith("sample_docs/"):
            parts = old_file.split("/")
        else:
            parts = [old_file]

        if len(parts) >= 2:
            category = parts[0]
            filename = parts[-1]

            # Remove extensions
            base_name = filename
            if filename.endswith(".txt"):
                base_name = filename[:-4]
            elif filename.endswith(".md"):
                base_name = filename[:-3]

            # Look for original file
            sample_docs_category = Path(f"sample_docs/{category}")
            if sample_docs_category.exists():
                for ext in [".pdf", ".docx", ".txt", ".md"]:
                    original_file = sample_docs_category / f"{base_name}{ext}"
                    if original_file.exists():
                        new_file = str(original_file).replace("\\", "/")
                        break

        elif len(parts) == 1:
            root_file = Path(f"sample_docs/{parts[0]}")
            if root_file.exists():
                new_file = str(root_file).replace("\\", "/")

        if new_file:
            print(f"    → {new_file} ✅")
            fixes_count += 1
        else:
            print(f"    → ❌ No original found (will skip)")
            skips_count += 1

    print(f"\n📈 PREVIEW SUMMARY:")
    print(f"  ✅ Files that can be fixed: {fixes_count}")
    print(f"  ❌ Files that will be skipped: {skips_count}")

    conn.close()


def verify_fixes():
    """Verify that citation fixes were applied correctly."""
    conn = sqlite3.connect("meta.sqlite")
    cursor = conn.cursor()

    print("✅ VERIFYING CITATION FIXES")
    print("=" * 60)

    # Check for remaining problematic files
    cursor.execute('SELECT DISTINCT file FROM meta WHERE file NOT LIKE "sample_docs/%"')
    remaining_problems = cursor.fetchall()

    if remaining_problems:
        print(f"⚠️  Still have {len(remaining_problems)} non-sample_docs files:")
        for (file,) in remaining_problems:
            print(f"  - {file}")
    else:
        print("🎉 All citations now point to sample_docs/ files!")

    # Show business rules files specifically
    cursor.execute(
        'SELECT DISTINCT file FROM meta WHERE file LIKE "%business_rules%" ORDER BY file'
    )
    business_files = cursor.fetchall()

    print(f"\n📊 CURRENT BUSINESS RULES FILES IN DATABASE:")
    sample_docs_count = 0
    other_count = 0

    for (file,) in business_files:
        if file.startswith("sample_docs/"):
            sample_docs_count += 1
            print(f"  ✅ {file}")
        else:
            other_count += 1
            print(f"  ⚠️  {file}")

    # Overall database stats
    cursor.execute("SELECT COUNT(DISTINCT file) FROM meta")
    total_files = cursor.fetchone()[0]

    cursor.execute(
        'SELECT COUNT(DISTINCT file) FROM meta WHERE file LIKE "sample_docs/%"'
    )
    sample_docs_files = cursor.fetchone()[0]

    other_files = total_files - sample_docs_files

    print(f"\n📈 OVERALL DATABASE SUMMARY:")
    print(f"  📁 Total unique files: {total_files}")
    print(f"  ✅ Correct citations (sample_docs/): {sample_docs_files}")
    print(f"  ⚠️  Other citations: {other_files}")

    if other_files == 0:
        print(f"\n🎉 PERFECT! All citations point to sample_docs/ files!")
    else:
        print(f"\n⚠️  {other_files} files still need fixing")

    conn.close()


def show_citation_stats():
    """Show detailed citation statistics."""
    conn = sqlite3.connect("meta.sqlite")
    cursor = conn.cursor()

    print("📊 CITATION STATISTICS")
    print("=" * 60)

    # Get all file patterns
    cursor.execute(
        """
        SELECT
            CASE
                WHEN file LIKE 'sample_docs/%' THEN 'sample_docs (correct)'
                WHEN file LIKE '%\\%' THEN 'backslash_paths'
                WHEN file LIKE '%/%' AND file NOT LIKE 'sample_docs/%' THEN 'forward_slash_paths'
                ELSE 'other'
            END as category,
            COUNT(DISTINCT file) as files,
            COUNT(*) as chunks
        FROM meta
        GROUP BY category
        ORDER BY files DESC
    """
    )

    results = cursor.fetchall()

    print(f"📋 CITATION BREAKDOWN:")
    total_files = 0
    total_chunks = 0

    for category, files, chunks in results:
        print(f"  {category:20} | {files:3} files | {chunks:4} chunks")
        total_files += files
        total_chunks += chunks

    print(f'  {"-"*20} | {"-"*9} | {"-"*11}')
    print(f'  {"TOTAL":20} | {total_files:3} files | {total_chunks:4} chunks')

    conn.close()


def main():
    """Main function with command options."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "preview":
            preview_fixes()
        elif command == "fix":
            fix_citation_mappings()
        elif command == "verify":
            verify_fixes()
        elif command == "stats":
            show_citation_stats()
        else:
            print("❌ Unknown command")
            print_usage()
    else:
        print_usage()


def print_usage():
    """Print usage information."""
    print(
        """
🔧 Fix Citation Mapping Tool

DESCRIPTION:
    Ensures ALL citations point to sample_docs/ files, never to extracts/.
    Fixes database records that incorrectly point to extracted .txt files.

USAGE:
    python tools/fix_citations.py [command]

COMMANDS:
    preview             Preview fixes without making changes
    fix                 Apply citation fixes to database
    verify              Verify that fixes were applied correctly
    stats               Show detailed citation statistics

EXAMPLES:
    python tools/fix_citations.py stats
    python tools/fix_citations.py preview
    python tools/fix_citations.py fix
    python tools/fix_citations.py verify

WORKFLOW:
    1. Run 'stats' to see current citation breakdown
    2. Run 'preview' to see what would be fixed
    3. Run 'fix' to apply the fixes
    4. Run 'verify' to confirm all citations are correct
    """
    )


if __name__ == "__main__":
    main()
