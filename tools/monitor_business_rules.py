#!/usr/bin/env python3
"""
Monitor business rules category before and after file additions.
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from core.config import DATABASE_PATH


def get_file_count(category="business_rules"):
    """Get current file count for a category."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(DISTINCT file) FROM meta WHERE file LIKE ?",
            (f"%{category}%",),
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        print(f"Error accessing database: {e}")
        return 0, 0


def get_business_rules_status():
    """Get detailed business rules status from database and filesystem."""
    try:
        # Database check
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT file, COUNT(*) as chunks
            FROM meta
            WHERE file LIKE '%business_rules%'
            GROUP BY file
            ORDER BY file
        """
        )
        db_files = cursor.fetchall()
        conn.close()

        # Filesystem check
        folder_path = Path("ai_search_docs/business_rules")
        if not folder_path.exists():
            print(f"⚠️ Warning: {folder_path} does not exist")
            return [], []

        actual_files = list(folder_path.glob("*.pdf"))
        actual_files.extend(list(folder_path.glob("*.docx")))
        actual_files.extend(list(folder_path.glob("*.txt")))
        actual_files.extend(list(folder_path.glob("*.md")))

        return db_files, actual_files

    except Exception as e:
        print(f"❌ Error: {e}")
        return [], []


def monitor_before():
    """Monitor before adding files."""
    print("📊 BUSINESS RULES MONITORING - BEFORE")
    print("=" * 60)
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    db_files, actual_files = get_business_rules_status()

    print(f"\n🏢 BUSINESS RULES CATEGORY:")
    print(f"  📊 Files in database: {len(db_files)}")
    print(f"  📁 Files in folder: {len(actual_files)}")

    if db_files:
        total_br_chunks = sum(chunks for _, chunks in db_files)
        print(f"  📄 Total chunks: {total_br_chunks}")

        print(f"\n📋 INDEXED FILES:")
        for file, chunks in db_files:
            filename = file.split("/")[-1].split("\\")[-1]  # Handle both separators
            print(f"    📄 {filename[:50]:<50} | {chunks:>3} chunks")

    if actual_files:
        print(f"\n📁 FILES IN FOLDER:")
        for file in sorted(actual_files):
            file_size = file.stat().st_size / 1024  # KB
            print(f"    📄 {file.name[:50]:<50} | {file_size:>6.1f} KB")


def monitor_after():
    """Monitor after adding files."""
    print("📊 BUSINESS RULES MONITORING - AFTER")
    print("=" * 60)
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    db_files, actual_files = get_business_rules_status()

    print(f"\n🏢 BUSINESS RULES CATEGORY:")
    print(f"  📊 Files in database: {len(db_files)}")
    print(f"  📁 Files in folder: {len(actual_files)}")

    if db_files:
        total_br_chunks = sum(chunks for _, chunks in db_files)
        print(f"  📄 Total chunks: {total_br_chunks}")

        print(f"\n📋 INDEXED FILES:")
        for file, chunks in db_files:
            filename = file.split("/")[-1].split("\\")[-1]  # Handle both separators
            print(f"    📄 {filename[:50]:<50} | {chunks:>3} chunks")

    if actual_files:
        print(f"\n📁 FILES IN FOLDER:")
        for file in sorted(actual_files):
            file_size = file.stat().st_size / 1024  # KB
            print(f"    📄 {file.name[:50]:<50} | {file_size:>6.1f} KB")

    # Check for discrepancies
    db_filenames = {
        f.split("/")[-1].split("\\")[-1] for f, _ in db_files
    }  # Handle both separators
    folder_filenames = {f.name for f in actual_files}

    missing_from_db = folder_filenames - db_filenames
    missing_from_folder = db_filenames - folder_filenames

    if missing_from_db:
        print(f"\n⚠️  FILES IN FOLDER BUT NOT INDEXED:")
        for filename in sorted(missing_from_db):
            print(f"    📄 {filename}")

    if missing_from_folder:
        print(f"\n⚠️  FILES INDEXED BUT NOT IN FOLDER:")
        for filename in sorted(missing_from_folder):
            print(f"    📄 {filename}")

    if not missing_from_db and not missing_from_folder:
        print(f"\n✅ All folder files are properly indexed!")


def main():
    """Main function to run monitoring."""
    if len(sys.argv) != 2 or sys.argv[1] not in ["before", "after"]:
        print("Usage: python monitor_business_rules.py [before|after]")
        sys.exit(1)

    action = sys.argv[1]

    if action == "before":
        monitor_before()
    elif action == "after":
        monitor_after()


if __name__ == "__main__":
    main()
