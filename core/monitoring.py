"""CORE: monitoring.py
Purpose: System monitoring utilities for file counts and watcher status.
"""

import os
import sqlite3
from pathlib import Path
from typing import List, Optional, Tuple

import psutil

from .config import (
    DATABASE_PATH,
    DOCUMENTS_DIR,
    EXTRACTS_DIR,
    LOGS_DIR,
    load_watch_paths,
)


def get_file_counts() -> Tuple[int, int, int, int, int]:
    """
    Get counts for watched files and indexed files.

    Returns:
        Tuple containing:
        - sample_count (int): Total number of files in all watch paths
        - extracts_count (int): Always 0 (deprecated)
        - indexed_count (int): Number of indexed chunks in meta.sqlite
        - sample_folder_count (int): Total number of folders in all watch paths
        - extracts_folder_count (int): Always 0 (deprecated)
    """
    watch_paths = load_watch_paths()

    sample_count = 0
    sample_folder_count = 0

    for path_str in watch_paths:
        path = Path(path_str)
        if path.exists():
            try:
                sample_count += sum(1 for f in path.rglob("*") if f.is_file())
                sample_folder_count += sum(1 for f in path.rglob("*") if f.is_dir())
            except Exception:
                pass

    extracts_count = 0
    extracts_folder_count = 0

    # Count indexed chunks in meta.sqlite
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
    Get the most recently added files in watched directories.

    Returns:
        Tuple containing:
        - latest_sample: (Path, timestamp) or None
        - latest_extract: None (deprecated)
    """
    watch_paths = load_watch_paths()
    all_files = []

    for path_str in watch_paths:
        path = Path(path_str)
        if path.exists():
            try:
                files = [(f, f.stat().st_mtime) for f in path.rglob("*") if f.is_file()]
                all_files.extend(files)
            except Exception:
                pass

    latest_sample = max(all_files, key=lambda x: x[1]) if all_files else None
    latest_extract = None

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
        List[str]: Always empty (deprecated).
    """
    return []
