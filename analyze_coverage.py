#!/usr/bin/env python3
"""
Analyze Coverage - Deep dive into why coverage is not 100%

This script provides detailed analysis of:
- Which files are indexed vs not indexed
- File type breakdown
- Duplicate analysis
- Path format issues
"""

import sqlite3
from collections import Counter, defaultdict
from pathlib import Path


def analyze_coverage():
    """Detailed coverage analysis to understand the 73.7% issue."""

    print("🔍 Deep Coverage Analysis")
    print("=" * 60)

    # Get indexed files from database
    print("\n📊 STEP 1: Database Analysis")
    conn = sqlite3.connect("meta.sqlite")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT file FROM meta ORDER BY file")
    indexed_files = [row[0] for row in cursor.fetchall()]
    conn.close()

    print(f"   Database contains: {len(indexed_files)} files")

    # Get indexed filenames (without path)
    indexed_basenames = set()
    for file in indexed_files:
        basename = Path(file).name
        indexed_basenames.add(basename)

    print(f"   Unique filenames in database: {len(indexed_basenames)}")

    # Get filesystem files
    print("\n📁 STEP 2: Filesystem Analysis")
    filesystem_files = []
    filesystem_basenames = set()
    file_types = Counter()

    for watch_dir in ["sample_docs", "extracts"]:
        if Path(watch_dir).exists():
            print(f"\n   Scanning {watch_dir}/:")
            dir_files = []
            for pattern in ["*.txt", "*.pdf", "*.docx", "*.md"]:
                for file_path in Path(watch_dir).rglob(pattern):
                    rel_path = str(file_path)
                    basename = file_path.name
                    extension = file_path.suffix.lower()

                    filesystem_files.append(rel_path)
                    filesystem_basenames.add(basename)
                    file_types[extension] += 1
                    dir_files.append(basename)

            print(f"      Files found: {len(dir_files)}")
            if len(dir_files) <= 10:
                for f in sorted(dir_files):
                    indexed_mark = "✅" if f in indexed_basenames else "❌"
                    print(f"         {indexed_mark} {f}")
            else:
                indexed_count = len([f for f in dir_files if f in indexed_basenames])
                print(f"         ✅ Indexed: {indexed_count}")
                print(f"         ❌ Not indexed: {len(dir_files) - indexed_count}")

    print(f"\n   Total filesystem files: {len(filesystem_files)}")
    print(f"   Unique filesystem filenames: {len(filesystem_basenames)}")

    # File type breakdown
    print(f"\n📋 STEP 3: File Type Breakdown")
    for ext, count in file_types.most_common():
        print(f"   {ext}: {count} files")

    # Find matches and misses
    print(f"\n🎯 STEP 4: Match Analysis")
    matches = indexed_basenames & filesystem_basenames
    missing_from_index = filesystem_basenames - indexed_basenames
    extra_in_index = indexed_basenames - filesystem_basenames

    print(f"   ✅ Matched files: {len(matches)}")
    print(f"   ❌ Missing from index: {len(missing_from_index)}")
    print(f"   🔍 Extra in index: {len(extra_in_index)}")

    # Calculate actual coverage
    total_unique = len(filesystem_basenames)
    indexed_unique = len(matches)
    coverage = (indexed_unique / total_unique * 100) if total_unique > 0 else 0

    print(f"\n📈 STEP 5: Coverage Calculation")
    print(
        f"   Formula: {indexed_unique} matched / {total_unique} total = {coverage:.1f}%"
    )

    # Show missing files
    if missing_from_index:
        print(f"\n❌ FILES NOT INDEXED ({len(missing_from_index)} files):")
        for i, filename in enumerate(sorted(missing_from_index), 1):
            # Find the full path for this file
            full_paths = [f for f in filesystem_files if Path(f).name == filename]
            print(f"   {i:2d}. {filename}")
            for path in full_paths[:2]:  # Show first 2 paths if multiple
                print(f"       → {path}")

    # Show extra files (in index but not in filesystem)
    if extra_in_index:
        print(
            f"\n🔍 FILES IN INDEX BUT NOT IN FILESYSTEM ({len(extra_in_index)} files):"
        )
        for i, filename in enumerate(sorted(extra_in_index), 1):
            # Find the database path for this file
            db_paths = [f for f in indexed_files if Path(f).name == filename]
            print(f"   {i:2d}. {filename}")
            for path in db_paths[:2]:  # Show first 2 paths if multiple
                print(f"       → {path}")

    # Duplicate analysis
    print(f"\n🔄 STEP 6: Duplicate Analysis")

    # Find filesystem duplicates (same filename, different extensions)
    basename_to_paths = defaultdict(list)
    for file_path in filesystem_files:
        basename_no_ext = Path(file_path).stem
        basename_to_paths[basename_no_ext].append(file_path)

    duplicates = {k: v for k, v in basename_to_paths.items() if len(v) > 1}

    if duplicates:
        print(f"   Found {len(duplicates)} sets of files with same base name:")
        for basename, paths in list(duplicates.items())[:5]:  # Show first 5
            print(f"      '{basename}':")
            for path in paths:
                ext = Path(path).suffix
                indexed_mark = "✅" if Path(path).name in indexed_basenames else "❌"
                print(f"         {indexed_mark} {path} ({ext})")
    else:
        print("   No duplicate base names found")

    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")

    if len(missing_from_index) > 0:
        print(
            f"   1. {len(missing_from_index)} files are not indexed - check file watcher logs"
        )
        print("   2. Try restarting the watcher: python smart_watcher.py restart")
        print("   3. Check if these files have processing errors")

    if len(extra_in_index) > 0:
        print(
            f"   4. {len(extra_in_index)} files in index may be from old locations or deleted files"
        )
        print("   5. Consider rebuilding the index if this number is high")

    if duplicates:
        print(f"   6. Consider choosing one format per document to improve clarity")
        print("   7. .txt files are processed fastest, .pdf/.docx may take longer")

    print(f"\n🎯 SUMMARY:")
    print(f"   Current coverage: {coverage:.1f}%")
    print(f"   Target: 100% (index all {total_unique} unique files)")
    print(f"   Gap: {len(missing_from_index)} files need to be indexed")


if __name__ == "__main__":
    analyze_coverage()
