"""
Version management and update checking for AI File Search.

Provides version constants and checks for updates from a remote source.
Designed for Google Drive distribution with non-blocking, fail-silent behavior.
"""

import threading
from pathlib import Path
from typing import Callable, Optional, Tuple

from loguru import logger

# Version file location
VERSION_FILE = Path(__file__).parent.parent / "VERSION"

# Remote version check URL (Google Drive direct download link)
# To set up: Upload a text file with just the version number to Google Drive,
# then get a shareable link and convert to direct download format.
# Format: https://drive.google.com/uc?export=download&id=FILE_ID
REMOTE_VERSION_URL: Optional[str] = (
    "https://drive.google.com/uc?export=download&id=1je9zcc3uje51mn32bnBfMcTaFANHGRON"
)

# Download URL for new versions
DOWNLOAD_URL: Optional[str] = (
    "https://drive.google.com/uc?export=download&id=1l-3oulawRXgGHaHbwRIeSta4cQ6CsOMc"
)

# Cached version info
_cached_local_version: Optional[str] = None
_cached_update_info: Optional[dict] = None


def get_local_version() -> str:
    """
    Get the current local version from VERSION file.

    Returns:
        Version string (e.g., "1.0.0") or "unknown" if file not found.
    """
    global _cached_local_version

    if _cached_local_version is not None:
        return _cached_local_version

    try:
        if VERSION_FILE.exists():
            _cached_local_version = VERSION_FILE.read_text().strip()
            return _cached_local_version
    except Exception as e:
        logger.warning(f"Could not read VERSION file: {e}")

    return "unknown"


def parse_version(version_str: str) -> Tuple[int, int, int]:
    """
    Parse a semantic version string into a tuple.

    Args:
        version_str: Version string like "1.2.3"

    Returns:
        Tuple of (major, minor, patch)
    """
    try:
        parts = version_str.strip().split(".")
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        return (major, minor, patch)
    except (ValueError, IndexError):
        return (0, 0, 0)


def is_newer_version(remote: str, local: str) -> bool:
    """
    Check if remote version is newer than local version.

    Args:
        remote: Remote version string
        local: Local version string

    Returns:
        True if remote is newer than local
    """
    remote_tuple = parse_version(remote)
    local_tuple = parse_version(local)
    return remote_tuple > local_tuple


def configure_update_check(version_url: str, download_url: str) -> None:
    """
    Configure the remote URLs for update checking.

    Args:
        version_url: URL to fetch latest version number (text file)
        download_url: URL where users can download the new version
    """
    global REMOTE_VERSION_URL, DOWNLOAD_URL
    REMOTE_VERSION_URL = version_url
    DOWNLOAD_URL = download_url
    logger.info(f"Update check configured: {version_url}")


def check_for_updates(timeout: float = 5.0) -> Optional[dict]:
    """
    Check for updates synchronously.

    Args:
        timeout: Request timeout in seconds

    Returns:
        Dict with update info if available, None otherwise.
        {
            "update_available": bool,
            "local_version": str,
            "remote_version": str,
            "download_url": str
        }
    """
    global _cached_update_info

    if REMOTE_VERSION_URL is None:
        return None

    try:
        import requests

        local_version = get_local_version()

        response = requests.get(REMOTE_VERSION_URL, timeout=timeout)
        response.raise_for_status()

        remote_version = response.text.strip()

        _cached_update_info = {
            "update_available": is_newer_version(remote_version, local_version),
            "local_version": local_version,
            "remote_version": remote_version,
            "download_url": DOWNLOAD_URL or "",
        }

        if _cached_update_info["update_available"]:
            logger.info(f"Update available: {local_version} → {remote_version}")

        return _cached_update_info

    except Exception as e:
        logger.debug(f"Update check failed (non-critical): {e}")
        return None


def check_for_updates_async(
    callback: Optional[Callable[[Optional[dict]], None]] = None,
) -> None:
    """
    Check for updates in a background thread (non-blocking).

    Args:
        callback: Optional function to call with update info when done.
    """

    def _check():
        result = check_for_updates()
        if callback:
            callback(result)

    thread = threading.Thread(target=_check, daemon=True)
    thread.start()


def get_cached_update_info() -> Optional[dict]:
    """
    Get cached update info from previous check.

    Returns:
        Cached update info dict, or None if not checked yet.
    """
    return _cached_update_info


def get_version_info() -> dict:
    """
    Get complete version information for API responses.

    Returns:
        Dict with version info:
        {
            "version": str,
            "update_available": bool,
            "latest_version": str | None,
            "download_url": str | None
        }
    """
    local = get_local_version()
    update = get_cached_update_info()

    return {
        "version": local,
        "update_available": update.get("update_available", False) if update else False,
        "latest_version": update.get("remote_version") if update else None,
        "download_url": update.get("download_url") if update else None,
    }
