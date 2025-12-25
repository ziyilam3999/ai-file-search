"""CORE: index_manager.py
Purpose: Manage index configuration and lifecycle.
"""

import os
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypedDict

import faiss
import numpy as np
import yaml
from loguru import logger

from core.config import CONFIG_PATH, DATABASE_PATH, INDEX_PATH
from core.embedding import Embedder
from core.path_utils import normalize_path, validate_watch_path
from daemon.embedding_adapter import EmbeddingAdapter
from smart_watcher import SmartWatcherController


class JobProgress(TypedDict):
    """Type-safe structure for job progress."""

    files_found: int
    files_indexed: int
    current_file: Optional[str]
    percent_complete: float


class JobStatus(TypedDict):
    """Type-safe structure for job status."""

    job_id: str
    status: str  # "queued", "in_progress", "completed", "failed"
    operation: str  # "add_path", "remove_path", "reindex"
    path: Optional[str]
    progress: JobProgress
    message: Optional[str]
    started_at: float
    completed_at: Optional[float]


class IndexManager:
    """Manages index configuration and lifecycle with async job support."""

    def __init__(self):
        self.watcher_controller = SmartWatcherController()
        # Tests expect an `embedder` attribute and patch `core.index_manager.Embedder`.
        self.embedder = Embedder()

        # Eagerly initialize embedding adapter to avoid first-use delay
        # This pre-warms the model during startup instead of during first request
        self._embedding_adapter: Optional[EmbeddingAdapter] = None
        self._adapter_lock = threading.Lock()

        # Background job management
        self._jobs: Dict[str, JobStatus] = {}
        self._job_lock = threading.Lock()
        self._worker_threads: Dict[str, threading.Thread] = {}

    @property
    def embedding_adapter(self) -> EmbeddingAdapter:
        """Lazy-init embedding adapter with thread safety."""
        if self._embedding_adapter is None:
            with self._adapter_lock:
                if self._embedding_adapter is None:
                    logger.info("Initializing EmbeddingAdapter (pre-warming model)...")
                    self._embedding_adapter = EmbeddingAdapter()
        return self._embedding_adapter

    @embedding_adapter.setter
    def embedding_adapter(self, value: Optional[EmbeddingAdapter]) -> None:
        """Allow setting embedding_adapter for test compatibility."""
        self._embedding_adapter = value

    def warm_up(self) -> None:
        """Pre-warm the embedding adapter. Call this at app startup."""
        _ = self.embedding_adapter  # Trigger lazy initialization

    def _create_job(self, operation: str, path: Optional[str] = None) -> str:
        """Create a new background job and return its ID."""
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        with self._job_lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "status": "queued",
                "operation": operation,
                "path": path,
                "progress": {
                    "files_found": 0,
                    "files_indexed": 0,
                    "current_file": None,
                    "percent_complete": 0.0,
                },
                "message": None,
                "started_at": time.time(),
                "completed_at": None,
            }
        return job_id

    def _update_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        progress: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
    ) -> None:
        """Update job status."""
        with self._job_lock:
            if job_id in self._jobs:
                if status:
                    self._jobs[job_id]["status"] = status
                    if status in ("completed", "failed"):
                        self._jobs[job_id]["completed_at"] = time.time()
                if progress:
                    # Update progress fields individually to satisfy type checker
                    job_progress = self._jobs[job_id]["progress"]
                    if "files_found" in progress:
                        job_progress["files_found"] = progress["files_found"]
                    if "files_indexed" in progress:
                        job_progress["files_indexed"] = progress["files_indexed"]
                    if "current_file" in progress:
                        job_progress["current_file"] = progress["current_file"]
                    if "percent_complete" in progress:
                        job_progress["percent_complete"] = progress["percent_complete"]
                if message:
                    self._jobs[job_id]["message"] = message

    def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """Get the status of a background job."""
        with self._job_lock:
            return self._jobs.get(job_id)

    def get_all_jobs(self) -> List[JobStatus]:
        """Get all job statuses."""
        with self._job_lock:
            return list(self._jobs.values())

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

    def add_watch_path(
        self, path: str, async_mode: bool = True
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Add a new watch path.

        Args:
            path: The path to watch
            async_mode: If True, return immediately and index in background

        Returns:
            Tuple of (success, message, job_id). job_id is None if sync mode.
        """
        is_valid, error = validate_watch_path(path)
        if not is_valid:
            return False, error, None

        norm_path = normalize_path(path)

        try:
            config = self._load_config()
            paths = config.get("watch_paths", [])

            if norm_path in paths:
                return False, "Path is already being watched", None

            paths.append(norm_path)
            config["watch_paths"] = paths
            self._save_config(config)

            # Signal watcher to reload config (if running) instead of full restart
            self._signal_watcher_reload()

            if async_mode:
                # Create background job and return immediately
                job_id = self._create_job("add_path", norm_path)

                # Start background indexing thread
                thread = threading.Thread(
                    target=self._background_index_path,
                    args=(job_id, norm_path),
                    daemon=True,
                )
                self._worker_threads[job_id] = thread
                thread.start()

                return True, "Path added. Indexing in background.", job_id
            else:
                # Synchronous mode (for backwards compatibility)
                files_found = self._scan_new_path_batch(norm_path)
                return (
                    True,
                    f"Path added successfully. Indexed {files_found} files.",
                    None,
                )

        except Exception as e:
            return False, str(e), None

    def _signal_watcher_reload(self) -> None:
        """Signal the watcher to reload its configuration without restart."""
        # Touch the config file to trigger watcher's config file watch
        # This is faster than a full restart
        try:
            if os.path.exists(CONFIG_PATH):
                os.utime(CONFIG_PATH, None)  # Update mtime
                logger.debug("Signaled watcher to reload config")
        except Exception as e:
            logger.warning(f"Could not signal watcher reload: {e}")

    def _background_index_path(self, job_id: str, path: str) -> None:
        """Background worker to index a new path."""
        try:
            self._update_job(job_id, status="in_progress")
            files_indexed = self._scan_new_path_batch(path, job_id=job_id)
            self._update_job(
                job_id,
                status="completed",
                message=f"Successfully indexed {files_indexed} files",
            )
        except Exception as e:
            logger.error(f"Background indexing failed for {path}: {e}")
            self._update_job(job_id, status="failed", message=str(e))

    def _scan_new_path_batch(self, path: str, job_id: Optional[str] = None) -> int:
        """
        Scan a newly added path and index files using batch processing.

        Args:
            path: The path to scan
            job_id: Optional job ID for progress updates

        Returns:
            Number of files successfully indexed
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
                if job_id:
                    self._update_job(job_id, progress={"files_found": 0})
                return 0

            logger.info(f"Found {len(files)} files to index in {path}")
            if job_id:
                self._update_job(job_id, progress={"files_found": len(files)})

            # Extract text from all files first
            extractor = Extractor()
            documents: List[Tuple[str, str]] = []

            for i, file_path in enumerate(files):
                try:
                    abs_path = str(file_path.resolve()).replace("\\", "/")
                    text = extractor.run(file_path)

                    if text and len(text.strip()) >= 10:
                        documents.append((abs_path, text))

                    if job_id:
                        self._update_job(
                            job_id,
                            progress={
                                "current_file": file_path.name,
                                "percent_complete": ((i + 1) / len(files))
                                * 50,  # 50% for extraction
                            },
                        )
                except Exception as e:
                    logger.error(f"Error extracting {file_path}: {e}")

            if not documents:
                logger.warning(f"No valid documents extracted from {path}")
                return 0

            # Batch index all documents
            def progress_callback(current: int, total: int, file_path: str) -> None:
                if job_id:
                    self._update_job(
                        job_id,
                        progress={
                            "files_indexed": current,
                            "current_file": Path(file_path).name,
                            "percent_complete": 50
                            + ((current / total) * 50),  # 50-100% for indexing
                        },
                    )

            successful, failed = self.embedding_adapter.add_documents_batch(
                documents, progress_callback=progress_callback
            )

            if job_id:
                self._update_job(
                    job_id,
                    progress={
                        "files_indexed": successful,
                        "percent_complete": 100.0,
                    },
                )

            logger.success(
                f"Batch indexed {successful}/{len(documents)} files from {path}"
            )
            return successful

        except Exception as e:
            logger.error(f"Error scanning new path {path}: {e}")
            return 0

    def _scan_new_path(self, path: str) -> int:
        """Legacy synchronous scan method for backwards compatibility."""
        return self._scan_new_path_batch(path)

    def remove_watch_path(
        self, path: str, async_mode: bool = True
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Remove a watch path and clean up index.

        Args:
            path: The path to remove
            async_mode: If True, return immediately and clean up in background

        Returns:
            Tuple of (success, message, job_id). job_id is None if sync mode.
        """
        norm_path = normalize_path(path)

        try:
            config = self._load_config()
            paths = config.get("watch_paths", [])

            if norm_path not in paths:
                return False, "Path is not being watched", None

            paths.remove(norm_path)
            config["watch_paths"] = paths
            self._save_config(config)

            # Signal watcher to reload config instead of full restart
            self._signal_watcher_reload()

            if async_mode:
                # Create background job and return immediately
                job_id = self._create_job("remove_path", norm_path)

                # Start background cleanup thread
                thread = threading.Thread(
                    target=self._background_remove_path,
                    args=(job_id, norm_path),
                    daemon=True,
                )
                self._worker_threads[job_id] = thread
                thread.start()

                return True, "Path removed. Cleaning up index in background.", job_id
            else:
                # Synchronous mode
                deleted_count = self._remove_path_from_index(norm_path)
                return (
                    True,
                    f"Path removed. {deleted_count} chunks cleaned up.",
                    None,
                )

        except Exception as e:
            return False, str(e), None

    def _background_remove_path(self, job_id: str, path: str) -> None:
        """Background worker to clean up removed path from index."""
        try:
            self._update_job(job_id, status="in_progress")
            deleted_count = self._remove_path_from_index(path)
            self._update_job(
                job_id,
                status="completed",
                message=f"Removed {deleted_count} chunks from index",
            )
        except Exception as e:
            logger.error(f"Background cleanup failed for {path}: {e}")
            self._update_job(job_id, status="failed", message=str(e))

    def _remove_path_from_index(self, path: str) -> int:
        """
        Remove all indexed content for a path from FAISS and database.

        Args:
            path: The normalized path to remove

        Returns:
            Number of chunks removed
        """
        deleted_count = 0

        if not os.path.exists(DATABASE_PATH):
            return 0

        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Use forward slashes for consistency in DB
            search_path = path.replace("\\", "/") + "%"

            # Get IDs BEFORE deleting from DB (for FAISS removal)
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

            # Delete from database
            cursor.execute("DELETE FROM meta WHERE file LIKE ?", (search_path,))
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            # Clear embedding cache
            if self._embedding_adapter is not None:
                self._embedding_adapter.embedder.clear_cache()
                logger.info("Cleared embedding cache after path removal")

            return deleted_count

        except Exception as e:
            logger.error(f"Error removing path from index: {e}")
            return 0

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
