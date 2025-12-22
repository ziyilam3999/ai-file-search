"""CORE: path_utils.py
Purpose: Utilities for path validation, normalization, and statistics.
"""

import os
import platform
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from loguru import logger

# Default supported extensions if config is unavailable
DEFAULT_EXTENSIONS = {".txt", ".pdf", ".docx", ".md", ".markdown"}

# System paths to block (simple heuristic)
BLOCKED_PATHS_WINDOWS = {"C:\\Windows", "C:\\Program Files", "C:\\Program Files (x86)"}
BLOCKED_PATHS_UNIX = {
    "/",
    "/usr",
    "/bin",
    "/sbin",
    "/etc",
    "/var",
    "/sys",
    "/proc",
    "/dev",
}


def normalize_path(path: str) -> str:
    """
    Convert path to absolute, normalized form.
    Handles Windows/Unix differences.
    """
    try:
        # Expand user (~/...) and vars ($HOME/...)
        expanded = os.path.expanduser(os.path.expandvars(path))
        # Resolve absolute path
        absolute = os.path.abspath(expanded)
        # Normalize separators
        return os.path.normpath(absolute)
    except Exception as e:
        logger.error(f"Error normalizing path {path}: {e}")
        return path


def is_system_path(path: str) -> bool:
    """Check if path is a critical system directory."""
    norm_path = normalize_path(path)
    system = platform.system()

    if system == "Windows":
        # Check exact match for root drives
        if len(norm_path) <= 3 and norm_path.endswith(":\\"):
            return True

        # Check blocked system folders
        for blocked in BLOCKED_PATHS_WINDOWS:
            if norm_path.lower().startswith(blocked.lower()):
                return True
    else:
        if norm_path == "/":
            return True
        for blocked in BLOCKED_PATHS_UNIX:
            if norm_path == blocked or norm_path.startswith(blocked + "/"):
                return True

    return False


def validate_watch_path(path: str) -> Tuple[bool, str]:
    """
    Validate a path is suitable for watching.
    Returns (is_valid, error_message).
    """
    if not path:
        return False, "Path cannot be empty"

    norm_path = normalize_path(path)
    path_obj = Path(norm_path)

    if not path_obj.exists():
        return False, f"Path does not exist: {path}"

    if not path_obj.is_dir():
        return False, f"Path is not a directory: {path}"

    if is_system_path(norm_path):
        return False, "Cannot watch system directories for security reasons"

    # Check permissions
    if not os.access(norm_path, os.R_OK):
        return False, f"Permission denied: Cannot read {path}"

    return True, ""


def get_supported_files(path: str, extensions: Optional[Set[str]] = None) -> List[Path]:
    """
    Recursively find all indexable files in a path.
    """
    if extensions is None:
        extensions = DEFAULT_EXTENSIONS

    found_files = []
    path_obj = Path(path)

    if not path_obj.exists():
        return []

    try:
        for root, _, files in os.walk(path_obj):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in extensions:
                    found_files.append(file_path)
    except Exception as e:
        logger.error(f"Error scanning {path}: {e}")

    return found_files


def estimate_folder_stats(
    path: str, extensions: Optional[Set[str]] = None
) -> Dict[str, Any]:
    """
    Quick scan to estimate folder statistics.
    """
    if extensions is None:
        extensions = DEFAULT_EXTENSIONS

    stats = {
        "file_count": 0,
        "total_size_mb": 0.0,
        "supported_files": 0,
        "estimated_time_min": 0.0,
    }

    path_obj = Path(path)
    if not path_obj.exists():
        return stats

    try:
        file_count = 0
        supported_count = 0
        total_size = 0

        # Walk with a limit? For estimation we might want to be fast.
        # But os.walk is reasonably fast.
        for root, _, files in os.walk(path_obj):
            file_count += len(files)
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in extensions:
                    supported_count += 1
                    try:
                        total_size += file_path.stat().st_size
                    except OSError:
                        pass

        stats["file_count"] = file_count
        stats["supported_files"] = supported_count
        stats["total_size_mb"] = round(total_size / (1024 * 1024), 2)

        # Rough estimate: 2 seconds per file for extraction + embedding
        # This is conservative.
        stats["estimated_time_min"] = round((supported_count * 2) / 60, 1)

    except Exception as e:
        logger.error(f"Error estimating stats for {path}: {e}")

    return stats
