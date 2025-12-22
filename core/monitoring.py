"""CORE: monitoring.py
Purpose: System monitoring utilities for file counts and watcher status.
"""

import os
import sqlite3
from pathlib import Path
from typing import List, Optional, Tuple

import psutil

from .config import DATABASE_PATH, DOCUMENTS_DIR, EXTRACTS_DIR, LOGS_DIR


def get_file_counts() -> Tuple[int, int, int, int, int]:
    """
    Get counts for ai_search_docs, extracts, and indexed files.

    Returns:
        Tuple containing:
        - sample_count (int): Number of files in ai_search_docs
        - extracts_count (int): Number of files in extracts
        - indexed_count (int): Number of indexed files in meta.sqlite
        - sample_folder_count (int): Number of folders in ai_search_docs
        - extracts_folder_count (int): Number of folders in extracts
    """
    sample_count = sum(1 for f in Path(DOCUMENTS_DIR).rglob("*") if f.is_file())
    extracts_count = sum(1 for f in Path(EXTRACTS_DIR).rglob("*") if f.is_file())
    sample_folder_count = sum(1 for f in Path(DOCUMENTS_DIR).rglob("*") if f.is_dir())
    extracts_folder_count = sum(1 for f in Path(EXTRACTS_DIR).rglob("*") if f.is_dir())

    # Count indexed files in meta.sqlite
    indexed_count = 0
    if Path(DATABASE_PATH).exists():
        try:
            conn = sqlite3.connect(str(DATABASE_PATH))
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM meta")
            result = cur.fetchone()
            if result:
                indexed_count = result[0]
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


def get_latest_files() -> (
    Tuple[Optional[Tuple[Path, float]], Optional[Tuple[Path, float]]]
):
    """
    Get the most recently added files in documents and extracts directories.

    Returns:
        Tuple containing:
        - latest_sample: (Path, timestamp) or None
        - latest_extract: (Path, timestamp) or None
    """
    # Latest in ai_search_docs
    sample_files = [
        (f, f.stat().st_mtime) for f in Path(DOCUMENTS_DIR).rglob("*") if f.is_file()
    ]
    latest_sample = max(sample_files, key=lambda x: x[1]) if sample_files else None

    # Latest in extracts
    extract_files = [
        (f, f.stat().st_mtime) for f in Path(EXTRACTS_DIR).rglob("*") if f.is_file()
    ]
    latest_extract = max(extract_files, key=lambda x: x[1]) if extract_files else None

    return latest_sample, latest_extract


def check_watcher_status() -> str:
    """
    Check if watcher is running by checking PID file and process existence.

    Returns:
        str: "running", "stopped", or "unknown"
    """
    try:
        pid_file = Path(LOGS_DIR) / "watcher.pid"
        if pid_file.exists():
            with open(pid_file, "r") as f:
                content = f.read().strip()
                if not content:
                    return "stopped"
                pid = int(content)

            if psutil.pid_exists(pid):
                return "running"
            else:
                return "stopped"
        else:
            return "stopped"
    except Exception:
        # print(f"❌ Watcher Status: UNKNOWN ({e})")
        return "unknown"


def check_for_misplaced_files() -> List[str]:
    """
    Check for files in wrong locations (e.g. root of extracts folder).

    Returns:
        List[str]: List of filenames found in the root of extracts folder.
    """
    misplaced = []
    if Path(EXTRACTS_DIR).exists():
        for item in Path(EXTRACTS_DIR).iterdir():
            if item.is_file() and item.suffix == ".txt":
                misplaced.append(item.name)
    return misplaced
