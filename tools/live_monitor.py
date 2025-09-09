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
    """Get counts for ai_search_docs, extracts, and indexed files"""
    # Use project root as base path
    base_path = Path(__file__).parent.parent

    ai_search_docs_path = base_path / "ai_search_docs"
    extracts_path = base_path / "extracts"
    meta_db_path = base_path / "meta.sqlite"

    sample_count = sum(1 for f in ai_search_docs_path.rglob("*") if f.is_file())
    extracts_count = sum(1 for f in extracts_path.rglob("*") if f.is_file())
    sample_folder_count = sum(1 for f in ai_search_docs_path.rglob("*") if f.is_dir())
    extracts_folder_count = sum(1 for f in extracts_path.rglob("*") if f.is_dir())

    # Count indexed files in meta.sqlite
    indexed_count = 0
    if meta_db_path.exists():
        try:
            conn = sqlite3.connect(str(meta_db_path))
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM meta")
            indexed_count = cur.fetchone()[0]
            conn.close()
        except Exception:
            pass

    return (
        sample_count,
        extracts_count,
        indexed_count,
        sample_folder_count,
        extracts_folder_count,
    )


def get_latest_files():
    """Get the most recently added files"""
    base_path = Path(__file__).parent.parent

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
    """Check if watcher is running by checking PID"""
    try:
        import psutil

        base_path = Path(__file__).parent.parent
        pid_file = base_path / "logs" / "watcher.pid"
        if pid_file.exists():
            with open(pid_file, "r") as f:
                pid = int(f.read().strip())
            if psutil.pid_exists(pid):
                return "running"
            else:
                return "stopped"
        else:
            return "stopped"
    except Exception as e:
        print(f"❌ Watcher Status: UNKNOWN ({e})")
        return "unknown"


def check_for_misplaced_files():
    """Check for files in wrong locations"""
    base_path = Path(__file__).parent.parent
    extracts_root = base_path / "extracts"

    misplaced = []
    if extracts_root.exists():
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
            (
                sample_count,
                extracts_count,
                indexed_count,
                sample_folder_count,
                extracts_folder_count,
            ) = get_file_counts()
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

            # Alert if watcher is stopped
            if watcher_status == "stopped":
                print("🚨 ALERT: Watcher is stopped! New files won't be processed.")
                print("   Run: python smart_watcher.py start")
                print()

            print("📊 File Counts:")
            print(
                f"   📁 ai_search_docs: {sample_count} files, {sample_folder_count} folders"
            )
            print(
                f"   📁 extracts:    {extracts_count} files, {extracts_folder_count} folders"
            )
            print(f"   📄 indexed:     {indexed_count} files")

            # Show changes
            if prev_counts:
                (
                    prev_sample,
                    prev_extracts,
                    prev_indexed,
                    prev_sample_folders,
                    prev_extracts_folders,
                ) = prev_counts
                if sample_count > prev_sample:
                    print(
                        f"   🆕 NEW FILE DETECTED in ai_search_docs! (+{sample_count - prev_sample})"
                    )
                if extracts_count > prev_extracts:
                    print(f"   ✅ EXTRACTED! (+{extracts_count - prev_extracts})")
                if indexed_count > prev_indexed:
                    print(f"   🎯 INDEXED! (+{indexed_count - prev_indexed})")
                if sample_folder_count > prev_sample_folders:
                    print(
                        f"   📂 NEW FOLDER in ai_search_docs! (+{sample_folder_count - prev_sample_folders})"
                    )
                if extracts_folder_count > prev_extracts_folders:
                    print(
                        f"   📂 NEW FOLDER in extracts! (+{extracts_folder_count - prev_extracts_folders})"
                    )

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
                rel_path = latest_sample[0].relative_to(Path(__file__).parent.parent)
                print(f"   📁 ai_search_docs: {rel_path} ({sample_time})")

            if latest_extract:
                extract_time = datetime.fromtimestamp(latest_extract[1]).strftime(
                    "%H:%M:%S"
                )
                rel_path = latest_extract[0].relative_to(Path(__file__).parent.parent)
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

            prev_counts = (
                sample_count,
                extracts_count,
                indexed_count,
                sample_folder_count,
                extracts_folder_count,
            )
            time.sleep(2)  # Update every 2 seconds

    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped. Happy searching!")


if __name__ == "__main__":
    main()
