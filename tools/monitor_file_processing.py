#!/usr/bin/env python3
"""
Monitor File Processing
Real-time monitoring of the AI File Search system to track:
- File processing status and statistics
- Index health and coverage metrics
- Recent activity and error monitoring
- System health indicators
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Union

import faiss
from loguru import logger

from core.config import DATABASE_PATH, INDEX_PATH


def get_watcher_status() -> Dict[str, Any]:
    """Get current watcher status from status file."""
    status_file = Path("logs/watcher_status.json")
    if status_file.exists():
        try:
            with open(status_file, "r") as f:
                status = json.load(f)
            return status
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    return {
        "status": "unknown",
        "last_update": None,
        "files_processed": 0,
        "errors": 0,
    }


def get_file_counts() -> Dict[str, int]:
    """Count files in ai_search_docs and extracts directories."""
    counts = {
        "ai_search_docs": 0,
        "extracts": 0,
        "total": 0,
    }

    # Count files in ai_search_docs
    ai_search_docs = Path("ai_search_docs")
    if ai_search_docs.exists():
        try:
            for pattern in ["*.txt", "*.pdf", "*.docx", "*.md"]:
                counts["ai_search_docs"] += len(list(ai_search_docs.rglob(pattern)))
        except sqlite3.Error:
            logger.warning("Could not access ai_search_docs directory")

    # Count files in extracts
    extracts = Path("extracts")
    if extracts.exists():
        for pattern in ["*.txt", "*.md"]:
            counts["extracts"] += len(list(extracts.rglob(pattern)))

    counts["total"] = counts["ai_search_docs"] + counts["extracts"]
    return counts


def get_index_statistics() -> Dict[str, Any]:
    """Get comprehensive index statistics."""
    stats: Dict[str, Any] = {
        "faiss_vectors": 0,
        "db_records": 0,
        "unique_files": 0,
        "last_updated": None,
        "recent_files": [],
        "index_size_mb": 0.0,
    }

    try:
        # FAISS index stats
        if Path(INDEX_PATH).exists():
            index = faiss.read_index(INDEX_PATH)
            stats["faiss_vectors"] = index.ntotal
            stats["index_size_mb"] = float(
                Path(INDEX_PATH).stat().st_size / (1024 * 1024)
            )
    except Exception as e:
        logger.error(f"Error reading FAISS index: {e}")

    try:
        # Database stats
        if Path(DATABASE_PATH).exists():
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Total records
            cursor.execute("SELECT COUNT(*) FROM meta")
            stats["db_records"] = cursor.fetchone()[0]

            # Unique files
            cursor.execute("SELECT COUNT(DISTINCT file) FROM meta")
            stats["unique_files"] = cursor.fetchone()[0]

            # Recent files (last 10)
            cursor.execute(
                """
                SELECT DISTINCT file
                FROM meta
                ORDER BY id DESC
                LIMIT 10
            """
            )
            stats["recent_files"] = [row[0] for row in cursor.fetchall()]

            conn.close()
    except Exception as e:
        logger.error(f"Error reading database: {e}")

    return stats


def monitor_system() -> None:
    """Monitor and display system status."""
    print("🔍 AI File Search - System Monitor")
    print("=" * 50)

    # Watcher status
    watcher_status = get_watcher_status()
    status_emoji = "✅" if watcher_status["status"] == "running" else "❌"
    print(f"\n{status_emoji} Watcher Status: {watcher_status['status'].upper()}")
    if watcher_status.get("last_update"):
        print(f"   Last update: {watcher_status['last_update']}")
    print(f"   Files processed: {watcher_status.get('files_processed', 0)}")
    print(f"   Errors: {watcher_status.get('errors', 0)}")

    # File counts
    file_counts = get_file_counts()
    print(f"\n📁 File Counts:")
    print(f"   Sample docs: {file_counts['ai_search_docs']}")
    print(f"   Extracts: {file_counts['extracts']}")
    print(f"   Total: {file_counts['total']}")

    # Index statistics
    index_stats = get_index_statistics()
    sync_emoji = (
        "✅" if index_stats["faiss_vectors"] == index_stats["db_records"] else "⚠️"
    )
    print(f"\n{sync_emoji} Index Health:")
    print(f"   FAISS vectors: {index_stats['faiss_vectors']:,}")
    print(f"   Database records: {index_stats['db_records']:,}")
    print(f"   Unique files: {index_stats['unique_files']:,}")
    print(f"   Index size: {index_stats['index_size_mb']:.1f} MB")

    if index_stats["last_updated"]:
        print(f"   Last updated: {index_stats['last_updated']}")

    # Coverage analysis - Option 1: Only count extracts for clean results
    try:
        import sqlite3

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT file FROM meta")
        indexed_files = {row[0] for row in cursor.fetchall()}
        conn.close()

        # OPTION 1: Only count extracts directory for clean coverage
        extracts_files = set()
        indexed_basenames = {Path(f).name for f in indexed_files}

        # Get files from extracts directory only
        extracts_dir = Path("extracts")
        if extracts_dir.exists():
            for pattern in ["*.txt", "*.md"]:
                for file_path in extracts_dir.rglob(pattern):
                    extracts_files.add(file_path.name)

        # Also count unique files that should be in extracts (including PDF/DOCX converted to TXT)
        sample_files = set()
        for watch_dir in ["ai_search_docs"]:
            if Path(watch_dir).exists():
                for pattern in ["*.txt", "*.pdf", "*.docx", "*.md"]:
                    for file_path in Path(watch_dir).rglob(pattern):
                        # Convert PDF/DOCX names to TXT equivalent
                        if file_path.suffix.lower() in [".pdf", ".docx"]:
                            txt_name = file_path.stem + ".txt"
                        else:
                            txt_name = file_path.name
                        sample_files.add(txt_name)

        # Calculate clean coverage based on Option 1 architecture
        total_expected = len(sample_files)
        actually_indexed = len(indexed_basenames & sample_files)

        if total_expected > 0:
            real_coverage = (actually_indexed / total_expected) * 100
            coverage_emoji = (
                "✅" if real_coverage > 95 else "⚠️" if real_coverage > 70 else "❌"
            )
            print(
                f"\n{coverage_emoji} Index Coverage (Option 1): {real_coverage:.1f}% ({actually_indexed}/{total_expected} files)"
            )
            print(f"   📁 Architecture: ai_search_docs → extracts → index")
            if real_coverage < 100:
                missing = sample_files - indexed_basenames
                print(f"   ⚠️  Missing: {len(missing)} files need extraction/indexing")
            else:
                print(f"   🎉 Perfect! All files properly indexed with no duplicates")
        else:
            print(f"\n❌ Index Coverage: 0% (no files found)")

    except Exception:
        # Fallback to original calculation
        coverage = (
            index_stats["unique_files"] / file_counts["total"] * 100
            if file_counts["total"] > 0
            else 0
        )
        coverage_emoji = "✅" if coverage > 90 else "⚠️" if coverage > 50 else "❌"
        print(f"\n{coverage_emoji} Index Coverage: {coverage:.1f}% (estimated)")

    # Recent files
    if index_stats["recent_files"]:
        print(f"\n📋 Recently Indexed Files:")
        for i, file_path in enumerate(index_stats["recent_files"][:5], 1):
            print(f"   {i}. {file_path}")


def get_log_summary() -> Dict[str, int]:
    """Get summary of recent log entries."""
    log_file = Path("logs/watcher.log")
    summary = {"INFO": 0, "ERROR": 0, "WARNING": 0, "SUCCESS": 0}

    if not log_file.exists():
        return summary

    try:
        # Read last 100 lines
        with open(log_file, "r") as f:
            lines = f.readlines()[-100:]

        for line in lines:
            if "ERROR" in line:
                summary["ERROR"] += 1
            elif "SUCCESS" in line:
                summary["SUCCESS"] += 1
            elif "WARNING" in line:
                summary["WARNING"] += 1
            elif "INFO" in line:
                summary["INFO"] += 1

    except Exception as e:
        logger.error(f"Error reading log file: {e}")

    return summary


def run_continuous_monitoring() -> None:
    """Run continuous monitoring with periodic updates."""
    print("Starting continuous monitoring... (Press Ctrl+C to stop)")

    try:
        while True:
            print("\033c", end="")  # Clear screen
            monitor_system()

            # Log summary
            log_summary = get_log_summary()
            print(f"\n📊 Recent Log Activity (last 100 entries):")
            for level, count in log_summary.items():
                emoji = {"INFO": "ℹ️", "ERROR": "❌", "WARNING": "⚠️", "SUCCESS": "✅"}
                print(f"   {emoji.get(level, '•')} {level}: {count}")

            print(f"\n🔄 Refreshing in 10 seconds... (Ctrl+C to stop)")
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped.")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Monitor AI File Search system")
    parser.add_argument(
        "--continuous", "-c", action="store_true", help="Run continuous monitoring"
    )

    args = parser.parse_args()

    if args.continuous:
        run_continuous_monitoring()
    else:
        monitor_system()


if __name__ == "__main__":
    main()
