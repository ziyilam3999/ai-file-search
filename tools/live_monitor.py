#!/usr/bin/env python3
"""
Live Monitor - Real-time AI File Search System Monitoring
==========================================================
This script provides live monitoring of the AI file search system
to verify it's working correctly when new files are added.

Usage: python live_monitor.py
"""

import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path


def get_file_counts():
    """Get current file counts from filesystem and database"""
    base_path = Path(__file__).parent

    # Count files in ai_search_docs
    ai_search_docs_path = base_path / "ai_search_docs"
    sample_count = len([f for f in ai_search_docs_path.rglob("*") if f.is_file()])

    # Count files in extracts
    extracts_path = base_path / "extracts"
    extracts_count = len([f for f in extracts_path.rglob("*") if f.is_file()])

    # Count indexed files
    try:
        conn = sqlite3.connect("meta.sqlite")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT file) FROM meta")
        indexed_count = cursor.fetchone()[0]
        conn.close()
    except Exception as e:
        indexed_count = f"Error: {e}"

    return sample_count, extracts_count, indexed_count


def get_latest_files():
    """Get the most recently added files"""
    base_path = Path(__file__).parent

    # Latest in ai_search_docs
    ai_search_docs_path = base_path / "ai_search_docs"
    sample_files = [
        (f, f.stat().st_mtime) for f in ai_search_docs_path.rglob("*") if f.is_file()
    ]
    latest_sample = max(sample_files, key=lambda x: x[1]) if sample_files else None

    # Latest in extracts
    extracts_path = base_path / "extracts"
    extract_files = [
        (f, f.stat().st_mtime) for f in extracts_path.rglob("*") if f.is_file()
    ]
    latest_extract = max(extract_files, key=lambda x: x[1]) if extract_files else None

    return latest_sample, latest_extract


def check_watcher_status():
    """Check if watcher is running"""
    try:
        with open("logs/watcher_status.json", "r") as f:
            import json

            status = json.load(f)
            return status.get("status", "unknown")
    except Exception:
        print("❌ Watcher Status: UNKNOWN (check logs/watcher_status.json)")


def check_for_misplaced_files():
    """Check for files in wrong locations"""
    base_path = Path(__file__).parent
    extracts_root = base_path / "extracts"

    misplaced = []
    for item in extracts_root.iterdir():
        if item.is_file() and item.suffix == ".txt":
            misplaced.append(item.name)

    return misplaced


def main():
    print("🔍 AI File Search - Live Monitor")
    print("=" * 50)
    print("💡 Add a PDF to ai_search_docs/ and watch the magic happen!")
    print("📋 Press Ctrl+C to stop monitoring\n")

    prev_counts = None

    try:
        while True:
            current_time = datetime.now().strftime("%H:%M:%S")
            sample_count, extracts_count, indexed_count = get_file_counts()
            latest_sample, latest_extract = get_latest_files()
            watcher_status = check_watcher_status()
            misplaced = check_for_misplaced_files()

            # Clear screen and show current status
            os.system("cls" if os.name == "nt" else "clear")

            print("🔍 AI File Search - Live Monitor")
            print("=" * 50)
            print(f"⏰ Time: {current_time}")
            print(f"🟢 Watcher: {watcher_status.upper()}")
            print()

            print("📊 File Counts:")
            print(f"   📁 ai_search_docs: {sample_count} files")
            print(f"   📁 extracts:    {extracts_count} files")
            print(f"   📄 indexed:     {indexed_count} files")

            # Show changes
            if prev_counts:
                prev_sample, prev_extracts, prev_indexed = prev_counts
                if sample_count > prev_sample:
                    print(
                        f"   🆕 NEW FILE DETECTED in ai_search_docs! (+{sample_count - prev_sample})"
                    )
                if extracts_count > prev_extracts:
                    print(f"   ✅ EXTRACTED! (+{extracts_count - prev_extracts})")
                if indexed_count > prev_indexed:
                    print(f"   🎯 INDEXED! (+{indexed_count - prev_indexed})")

            # Show misplaced files warning
            if misplaced:
                print(
                    f"   ⚠️  MISPLACED FILES: {len(misplaced)} files in extracts/ root"
                )
                for file in misplaced[:3]:  # Show first 3
                    print(f"      - {file}")
                if len(misplaced) > 3:
                    print(f"      ... and {len(misplaced) - 3} more")

            print()
            print("📋 Latest Files:")
            if latest_sample:
                sample_time = datetime.fromtimestamp(latest_sample[1]).strftime(
                    "%H:%M:%S"
                )
                rel_path = latest_sample[0].relative_to(Path(__file__).parent)
                print(f"   📁 ai_search_docs: {rel_path} ({sample_time})")

            if latest_extract:
                extract_time = datetime.fromtimestamp(latest_extract[1]).strftime(
                    "%H:%M:%S"
                )
                rel_path = latest_extract[0].relative_to(Path(__file__).parent)
                print(f"   📁 extracts:    {rel_path} ({extract_time})")

            print()
            print("💡 Expected Flow (Option 1):")
            print("   1. Add PDF to ai_search_docs/folder/")
            print("   2. Watcher detects file (within 5 seconds)")
            print("   3. PDF extracted to extracts/folder/file.txt")
            print("   4. TXT file indexed (within 30 seconds)")
            print("   5. All counts increment by 1")
            print()
            if misplaced:
                print("⚠️  Fix misplaced files to avoid duplicates")
            print("📋 Press Ctrl+C to stop monitoring")

            prev_counts = (sample_count, extracts_count, indexed_count)
            time.sleep(2)  # Update every 2 seconds

    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped. Happy searching!")


if __name__ == "__main__":
    main()
