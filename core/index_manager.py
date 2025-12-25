"""CORE: index_manager.py
Purpose: Manage index configuration and lifecycle.
"""

import os
import sqlite3
from pathlib import Path
from typing import List, Tuple

import faiss
import numpy as np
import yaml
from loguru import logger

from core.config import CONFIG_PATH, DATABASE_PATH, INDEX_PATH
from core.embedding import Embedder
from core.path_utils import normalize_path, validate_watch_path
from daemon.embedding_adapter import EmbeddingAdapter
from smart_watcher import SmartWatcherController


class IndexManager:
    """Manages index configuration and lifecycle."""

    def __init__(self):
        self.watcher_controller = SmartWatcherController()
        # Tests expect an `embedder` attribute and patch `core.index_manager.Embedder`.
        # Keep this lightweight: avoid initializing the embedding adapter (which pre-warms
        # models) unless we actually need to index files immediately.
        self.embedder = Embedder()
        self.embedding_adapter = None

    def _load_config(self) -> dict:
        """Load configuration from file."""
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _save_config(self, config: dict) -> None:
        """Save configuration to file."""
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False)

    def get_watch_paths(self) -> List[str]:
        """Get current watch paths."""
        config = self._load_config()
        return config.get("watch_paths", [])

    def add_watch_path(self, path: str) -> Tuple[bool, str]:
        """Add a new watch path."""
        is_valid, error = validate_watch_path(path)
        if not is_valid:
            return False, error

        norm_path = normalize_path(path)

        try:
            config = self._load_config()
            paths = config.get("watch_paths", [])

            if norm_path in paths:
                return False, "Path is already being watched"

            paths.append(norm_path)
            config["watch_paths"] = paths

            self._save_config(config)

            # Restart watcher to pick up changes
            self.watcher_controller.restart_watcher()

            # Trigger immediate scan of new path
            logger.info(f"Triggering immediate scan of new path: {norm_path}")
            files_found = self._scan_new_path(norm_path)

            return (
                True,
                f"Path added successfully. Found {files_found} files to index.",
            )

        except Exception as e:
            return False, str(e)

    def _scan_new_path(self, path: str) -> int:
        """
        Scan a newly added path and immediately index its files.

        Args:
            path: The path to scan

        Returns:
            Number of files found and queued for indexing
        """
        from core.extract import Extractor
        from core.path_utils import get_supported_files

        try:
            path_obj = Path(path)
            if not path_obj.exists():
                logger.warning(f"Path does not exist: {path}")
                return 0

            # Get all supported files in new path
            files = get_supported_files(str(path_obj))

            if not files:
                logger.info(f"No supported files found in {path}")
                return 0

            logger.info(f"Found {len(files)} files to index in {path}")

            # Lazily create the embedding adapter only when we have work to do.
            if self.embedding_adapter is None:
                self.embedding_adapter = EmbeddingAdapter()

            # Index files immediately
            extractor = Extractor()
            indexed_count = 0

            for file_path in files:
                try:
                    abs_path = str(file_path.resolve()).replace("\\", "/")

                    # Extract text
                    text = extractor.run(file_path)

                    if text and len(text.strip()) >= 10:
                        # Use embedding adapter to add document (has add_document method)
                        success = self.embedding_adapter.add_document(abs_path, text)
                        if success:
                            indexed_count += 1
                            logger.info(f"Indexed: {file_path.name}")
                        else:
                            logger.warning(f"Failed to index: {file_path.name}")

                except Exception as e:
                    logger.error(f"Error indexing {file_path}: {e}")

            logger.success(f"Indexed {indexed_count}/{len(files)} files from {path}")
            return len(files)

        except Exception as e:
            logger.error(f"Error scanning new path {path}: {e}")
            return 0

    def remove_watch_path(self, path: str) -> Tuple[bool, str]:
        """Remove a watch path and clean up index."""
        norm_path = normalize_path(path)

        try:
            config = self._load_config()
            paths = config.get("watch_paths", [])

            if norm_path not in paths:
                return False, "Path is not being watched"

            paths.remove(norm_path)
            config["watch_paths"] = paths

            self._save_config(config)

            # Remove from index metadata AND FAISS index
            deleted_count = 0
            if os.path.exists(DATABASE_PATH):
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()

                # Use forward slashes for consistency in DB
                search_path = norm_path.replace("\\", "/") + "%"

                # CRITICAL: Get IDs BEFORE deleting from DB (for FAISS removal)
                cursor.execute("SELECT id FROM meta WHERE file LIKE ?", (search_path,))
                ids_to_remove = [row[0] for row in cursor.fetchall()]

                # Remove from FAISS index first
                if ids_to_remove and os.path.exists(INDEX_PATH):
                    try:
                        logger.info(
                            f"Removing {len(ids_to_remove)} vectors from FAISS index..."
                        )
                        index = faiss.read_index(INDEX_PATH)
                        ids_array = np.array(ids_to_remove, dtype=np.int64)
                        index.remove_ids(ids_array)
                        faiss.write_index(index, INDEX_PATH)
                        logger.success(
                            f"Removed {len(ids_to_remove)} vectors from FAISS index"
                        )
                    except Exception as e:
                        logger.error(f"Failed to remove vectors from FAISS index: {e}")
                        # Continue anyway - we'll still clean up the database

                # Now delete from database
                cursor.execute("DELETE FROM meta WHERE file LIKE ?", (search_path,))
                deleted_count = cursor.rowcount
                conn.commit()
                conn.close()

                # Clear embedding cache to force reload (if adapter has been used)
                if self.embedding_adapter is not None:
                    self.embedding_adapter.embedder.clear_cache()
                    logger.info("Cleared embedding cache after path removal")

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

            # Start watcher; it will rebuild the index as needed.
            self.watcher_controller.start_watcher()

            return True, "Reindex triggered successfully"

        except Exception as e:
            return False, str(e)
