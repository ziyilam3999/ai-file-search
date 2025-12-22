"""CORE: index_manager.py
Purpose: Manage index configuration and lifecycle.
"""

import os
import sqlite3
from pathlib import Path
from typing import List, Tuple

import yaml

from core.config import CONFIG_PATH, DATABASE_PATH, INDEX_PATH
from core.embedding import Embedder
from core.path_utils import normalize_path, validate_watch_path
from smart_watcher import SmartWatcherController


class IndexManager:
    """Manages index configuration and lifecycle."""

    def __init__(self):
        self.watcher_controller = SmartWatcherController()
        self.embedder = Embedder()

    def get_watch_paths(self) -> List[str]:
        """Get current watch paths."""
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config.get("watch_paths", [])
        except Exception:
            return []

    def add_watch_path(self, path: str) -> Tuple[bool, str]:
        """Add a new watch path."""
        is_valid, error = validate_watch_path(path)
        if not is_valid:
            return False, error

        norm_path = normalize_path(path)

        try:
            # Load config
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}

            paths = config.get("watch_paths", [])
            if norm_path in paths:
                return False, "Path is already being watched"

            paths.append(norm_path)
            config["watch_paths"] = paths

            # Save config
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False)

            # Restart watcher to pick up changes
            self.watcher_controller.restart_watcher()

            return True, "Path added successfully"

        except Exception as e:
            return False, str(e)

    def remove_watch_path(self, path: str) -> Tuple[bool, str]:
        """Remove a watch path and clean up index."""
        norm_path = normalize_path(path)

        try:
            # Load config
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}

            paths = config.get("watch_paths", [])
            if norm_path not in paths:
                return False, "Path is not being watched"

            paths.remove(norm_path)
            config["watch_paths"] = paths

            # Save config
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False)

            # Remove from index metadata
            if os.path.exists(DATABASE_PATH):
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                # Use forward slashes for consistency in DB
                search_path = norm_path.replace("\\", "/") + "%"
                cursor.execute("DELETE FROM meta WHERE file LIKE ?", (search_path,))
                deleted_count = cursor.rowcount
                conn.commit()
                conn.close()
            else:
                deleted_count = 0

            # Restart watcher
            self.watcher_controller.restart_watcher()

            return (
                True,
                f"Path removed successfully. {deleted_count} chunks removed from metadata.",
            )

        except Exception as e:
            return False, str(e)

    def trigger_reindex(self) -> Tuple[bool, str]:
        """Trigger a full reindex."""
        try:
            # Stop watcher
            self.watcher_controller.stop_watcher()

            # Clear index files
            if os.path.exists(INDEX_PATH):
                os.remove(INDEX_PATH)
            if os.path.exists(DATABASE_PATH):
                os.remove(DATABASE_PATH)

            # Start watcher (it will auto-reindex if index is missing)
            self.watcher_controller.start_watcher()

            return True, "Reindex triggered successfully"

        except Exception as e:
            return False, str(e)
