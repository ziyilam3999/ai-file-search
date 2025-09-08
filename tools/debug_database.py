#!/usr/bin/env python3
"""
Database Debug Tool

Comprehensive tool for debugging the search index database.
Helps analyze file indexing issues and verify watcher functionality.
"""
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


def get_database_stats():
    """Get overall database statistics."""
    try:
        conn = sqlite3.connect("meta.sqlite")
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM meta")
        total_chunks = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT file) FROM meta")
        total_files = cursor.fetchone()[0]

        conn.close()
        return total_files, total_chunks
    except Exception as e:
        print(f"❌ Error accessing database: {e}")
        return 0, 0


def analyze_business_rules():
    """Analyze business rules category in detail."""
    try:
        conn = sqlite3.connect("meta.sqlite")
        cursor = conn.cursor()

        # Get all business rules entries
        cursor.execute(
            """
            SELECT file, COUNT(*) as chunks
            FROM meta
            WHERE file LIKE '%business_rules%'
            GROUP BY file
            ORDER BY file
        """
        )
        db_results = cursor.fetchall()

        # Get total chunks for business rules
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM meta
            WHERE file LIKE '%business_rules%'
        """
        )
        total_br_chunks = cursor.fetchone()[0]

        conn.close()

        print(f"🏢 BUSINESS RULES DATABASE ANALYSIS")
        print(f"{'='*60}")
        print(f"Files indexed: {len(db_results)}")
        print(f"Total chunks: {total_br_chunks}")
        print()

        if db_results:
            print("📋 INDEXED FILES:")
            for file, chunks in db_results:
                filename = file.split("/")[-1]
                print(f"  📄 {filename[:55]:<55} | {chunks:>3} chunks")
        else:
            print("❌ No business rules files found in database!")

        return db_results

    except Exception as e:
        print(f"❌ Error analyzing business rules: {e}")
        return []


def check_filesystem_vs_database():
    """Compare filesystem files with database entries."""
    print(f"\n🔍 FILESYSTEM vs DATABASE COMPARISON")
    print(f"{'='*60}")

    # Check filesystem
    folder_path = Path("ai_search_docs/business_rules")
    if not folder_path.exists():
        print("❌ business_rules folder does not exist!")
        return

    # Get all supported file types
    fs_files = []
    for pattern in ["*.pdf", "*.docx", "*.txt", "*.md"]:
        fs_files.extend(folder_path.glob(pattern))

    fs_filenames = {f.name for f in fs_files}

    # Get database files
    try:
        conn = sqlite3.connect("meta.sqlite")
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT file
            FROM meta
            WHERE file LIKE '%business_rules%'
        """
        )
        db_files = cursor.fetchall()
        db_filenames = {f[0].split("/")[-1] for f in db_files}
        conn.close()
    except Exception as e:
        print(f"❌ Database error: {e}")
        return

    print(f"📁 Files in folder: {len(fs_filenames)}")
    print(f"📊 Files in database: {len(db_filenames)}")

    # Find discrepancies
    missing_from_db = fs_filenames - db_filenames
    missing_from_fs = db_filenames - fs_filenames

    if missing_from_db:
        print(f"\n⚠️  FILES IN FOLDER BUT NOT INDEXED ({len(missing_from_db)}):")
        for filename in sorted(missing_from_db):
            file_path = folder_path / filename
            size_kb = file_path.stat().st_size / 1024 if file_path.exists() else 0
            print(f"  📄 {filename[:50]:<50} | {size_kb:>6.1f} KB")

    if missing_from_fs:
        print(f"\n⚠️  FILES INDEXED BUT NOT IN FOLDER ({len(missing_from_fs)}):")
        for filename in sorted(missing_from_fs):
            print(f"  📄 {filename}")

    if not missing_from_db and not missing_from_fs and fs_filenames:
        print(f"\n✅ Perfect sync! All {len(fs_filenames)} files properly indexed")
    elif not fs_filenames:
        print(f"\n🗂️  Folder is empty - no files to index")


def show_recent_entries(limit=20):
    """Show most recent database entries."""
    try:
        conn = sqlite3.connect("meta.sqlite")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, file, doc_chunk_id FROM meta ORDER BY id DESC LIMIT ?", (limit,)
        )
        recent = cursor.fetchall()

        conn.close()

        print(f"\n📋 RECENT DATABASE ENTRIES (last {limit})")
        print(f"{'='*60}")

        if recent:
            for id, file, doc_chunk_id in recent:
                filename = file.split("/")[-1][:45]
                category = file.split("/")[1] if "/" in file else "unknown"
                print(
                    f"  {id:>4} | {category:<15} | {filename:<45} | chunk {doc_chunk_id}"
                )
        else:
            print("❌ No entries found in database!")

    except Exception as e:
        print(f"❌ Error getting recent entries: {e}")


def analyze_category_distribution():
    """Show distribution of files across categories."""
    try:
        conn = sqlite3.connect("meta.sqlite")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                CASE
                    WHEN file LIKE '%/%' THEN
                        SUBSTR(file, 1, INSTR(file, '/') - 1) || '/' ||
                        SUBSTR(file, INSTR(file, '/') + 1, INSTR(SUBSTR(file, INSTR(file, '/') + 1), '/') - 1)
                    ELSE 'root'
                END as category,
                COUNT(DISTINCT file) as files,
                COUNT(*) as chunks
            FROM meta
            GROUP BY category
            ORDER BY files DESC
        """
        )

        results = cursor.fetchall()
        conn.close()

        print(f"\n📊 CATEGORY DISTRIBUTION")
        print(f"{'='*60}")
        print(f"{'Category':<25} | {'Files':<6} | {'Chunks':<8}")
        print(f"{'-'*25} | {'-'*6} | {'-'*8}")

        for category, files, chunks in results:
            print(f"{category:<25} | {files:>6} | {chunks:>8}")

    except Exception as e:
        print(f"❌ Error analyzing categories: {e}")


def full_diagnosis():
    """Run complete database diagnosis."""
    print(f"\n{'='*70}")
    print(f"🔬 COMPLETE DATABASE DIAGNOSIS")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")

    # Overall stats
    total_files, total_chunks = get_database_stats()
    print(f"\n🌐 OVERALL DATABASE STATS:")
    print(f"  📁 Total files: {total_files}")
    print(f"  📄 Total chunks: {total_chunks:,}")

    # Category distribution
    analyze_category_distribution()

    # Business rules analysis
    analyze_business_rules()

    # Filesystem comparison
    check_filesystem_vs_database()

    # Recent entries
    show_recent_entries(15)

    print(f"\n{'='*70}")


def main():
    """Main function with command line options."""
    if not Path("meta.sqlite").exists():
        print("❌ meta.sqlite database not found!")
        print("Make sure you're in the project root directory and have built an index.")
        return

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "stats":
            total_files, total_chunks = get_database_stats()
            print(f"📊 Database Stats: {total_files} files, {total_chunks:,} chunks")

        elif command == "business":
            analyze_business_rules()

        elif command == "compare":
            check_filesystem_vs_database()

        elif command == "recent":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            show_recent_entries(limit)

        elif command == "categories":
            analyze_category_distribution()

        elif command == "full":
            full_diagnosis()

        else:
            print("❌ Unknown command")
            print_usage()
    else:
        # Default: run business rules analysis
        analyze_business_rules()


def print_usage():
    """Print usage information."""
    print(
        """
🔬 Database Debug Tool

USAGE:
    python tools/debug_database.py [command] [options]

COMMANDS:
    stats                   Show basic database statistics
    business               Analyze business_rules category
    compare                Compare filesystem vs database
    recent [limit]         Show recent entries (default: 20)
    categories             Show category distribution
    full                   Complete diagnosis (recommended)

EXAMPLES:
    python tools/debug_database.py business
    python tools/debug_database.py recent 50
    python tools/debug_database.py full
    """
    )


if __name__ == "__main__":
    main()
