"""DAEMON: watch.py
File Watcher Daemon for AI File Search

This module implements a sophisticated file watcher that monitors specified directories
for changes and automatically updates the search index. Features include:
- Real-time file change detection with debouncing
- Batch processing to optimize performance
- Nightly full re-indexing
- Comprehensive logging and error handling
- Graceful startup and shutdown
"""

import fnmatch
import glob
import json
import os
import shutil
import signal
import sqlite3
import sys
import threading
import time
import traceback
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, TypedDict

import faiss
import numpy as np
import yaml  # type: ignore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from watchdog.events import (
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

# Import our core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import (
    DATABASE_PATH,
    DOCUMENTS_DIR,
    EXTRACTS_DIR,
    INDEX_PATH,
    LOGS_DIR,
)
from core.embedding import Embedder
from core.extract import Extractor
from core.path_utils import get_supported_files, validate_watch_path

# Import daemon modules
# Import daemon modules
from daemon.embedding_adapter import EmbeddingAdapter
from daemon.file_queue import FileChangeHandler, FileChangeQueue, WatchConfig


class ProgressInfo(TypedDict):
    """Type-safe structure for indexing progress."""

    is_indexing: bool
    current_file: Optional[str]
    processed_count: int
    total_files: int
    percent_complete: float


class WatcherStats(TypedDict, total=False):
    """Type-safe structure for watcher statistics.

    Note: total=False allows optional fields for dynamic stats.
    """

    files_processed: int
    files_added: int
    files_updated: int
    files_deleted: int
    last_full_reindex: Optional[str]
    start_time: Optional[float]
    errors: int
    processing_time_seconds: float
    total_size_bytes: int
    last_processed_time: float
    queue_size: int
    is_running: bool
    progress: ProgressInfo
    uptime_seconds: float


class FileWatcher:
    """Main file watcher class that coordinates all watching activities."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config_path = config_path or "prompts/watcher_config.yaml"
        self.config = self._load_config()
        self._setup_logging()

        # Core components
        self.embedding_manager: Optional[EmbeddingAdapter] = None
        self.file_queue = FileChangeQueue()
        self.observer = Observer()
        self.scheduler = BackgroundScheduler()

        # State management
        self._running = False
        self._shutdown_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._stats: WatcherStats = {
            "files_processed": 0,
            "files_added": 0,
            "files_updated": 0,
            "files_deleted": 0,
            "last_full_reindex": None,
            "start_time": None,
            "errors": 0,
            "processing_time_seconds": 0.0,
            "total_size_bytes": 0,
            "last_processed_time": 0.0,
        }
        self._progress: ProgressInfo = {
            "is_indexing": False,
            "current_file": None,
            "processed_count": 0,
            "total_files": 0,
            "percent_complete": 0.0,
        }

        logger.info("FileWatcher initialized")

    def _save_status(self) -> None:
        """Save current status and progress to JSON file."""
        try:
            status_data = {
                "status": "running" if self._running else "stopped",
                "last_updated": datetime.now().isoformat(),
                "stats": self._stats,
                "progress": self._progress,
            }

            # Atomic write
            status_file = Path("logs/watcher_status.json")
            temp_file = Path("logs/watcher_status.json.tmp")

            # Ensure directory exists
            status_file.parent.mkdir(exist_ok=True)

            with open(temp_file, "w") as f:
                json.dump(status_data, f, indent=2)

            temp_file.replace(status_file)

        except Exception as e:
            logger.error(f"Failed to save status file: {e}")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            config_path = Path(self.config_path)
            if not config_path.exists():
                logger.warning(
                    f"Config file {self.config_path} not found, using defaults"
                )
                return self._default_config()

            with open(config_path, "r", encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f)

            # Merge YAML config with defaults
            config = self._default_config()

            # Merge top-level sections
            for section in ["timing", "indexing", "logging", "performance"]:
                if section in yaml_config:
                    config[section].update(yaml_config[section])

            # Load watch paths
            watch_paths = []
            if "watch_paths" in yaml_config:
                for path in yaml_config["watch_paths"]:
                    is_valid, error = validate_watch_path(path)
                    if is_valid:
                        watch_paths.append(path)
                    else:
                        logger.warning(f"Skipping invalid watch path '{path}': {error}")

            # Fallback to default if no valid paths found
            if not watch_paths:
                logger.warning("No valid watch paths found in config, using default")
                watch_paths = [DOCUMENTS_DIR]

            config["watch_paths"] = watch_paths

            # Override with any direct YAML settings
            if "file_patterns" in yaml_config:
                config["file_patterns"].update(yaml_config["file_patterns"])

            # Security check: allow_external_paths
            allow_external = yaml_config.get("allow_external_paths", False)
            config["allow_external_paths"] = allow_external

            logger.info(f"Configuration loaded from {self.config_path}")
            logger.info(f"Watching paths: {config['watch_paths']}")
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "watch_paths": [DOCUMENTS_DIR],
            "allow_external_paths": False,
            "file_patterns": {
                "include": ["*.txt", "*.pdf", "*.docx", "*.md"],
                "ignore": [
                    "*.tmp",
                    "*.log",
                    "*.pyc",
                    "__pycache__",
                    ".git",
                    "*.swp",
                    "*.bak",
                ],
            },
            "timing": {
                "debounce_seconds": 5,
                "max_wait_seconds": 30,
                "nightly_reindex_time": "02:00",
            },
            "indexing": {
                "incremental_updates": True,
                "backup_before_update": True,
                "batch_size": 50,
            },
            "logging": {
                "level": "INFO",
                "file": f"{LOGS_DIR}/watcher.log",
                "console_output": True,
            },
            "performance": {"max_memory_mb": 1024, "worker_threads": 2},
        }

    def _setup_logging(self) -> None:
        """Configure logging based on config settings."""
        log_config = self.config.get("logging", {})
        level = log_config.get("level", "INFO")

        # Remove default handler
        logger.remove()

        # Add console handler if enabled
        if log_config.get("console_output", True):
            logger.add(
                sys.stderr,
                level=level,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            )

        # Add file handler if specified
        log_file = log_config.get("file")
        if log_file:
            log_dir = Path(log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)

            logger.add(
                log_file,
                level=level,
                rotation=log_config.get("rotation", "1 day"),
                retention=log_config.get("retention", "1 week"),
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            )

    def _initialize_components(self) -> None:
        """Initialize core components."""
        try:
            logger.info("Initializing embedding manager...")
            self.embedding_manager = EmbeddingAdapter()
            logger.info("Core components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise

    def _setup_file_watching(self) -> None:
        """Set up file system watching."""
        handler = FileChangeHandler(self.file_queue, self.config)  # type: ignore[arg-type]

        watch_paths = self.config.get("watch_paths", [])
        for watch_path in watch_paths:
            if os.path.exists(watch_path):
                self.observer.schedule(handler, watch_path, recursive=True)
                logger.info(f"Watching directory: {watch_path}")
            else:
                logger.warning(f"Watch directory does not exist: {watch_path}")

        if not watch_paths:
            logger.warning("No watch directories configured")

    def _setup_scheduler(self) -> None:
        """Set up the nightly reindex scheduler."""
        nightly_time = self.config.get("timing", {}).get(
            "nightly_reindex_time", "02:00"
        )
        hour, minute = map(int, nightly_time.split(":"))

        self.scheduler.add_job(
            self._nightly_reindex,
            CronTrigger(hour=hour, minute=minute),
            id="nightly_reindex",
            name="Nightly Full Reindex",
        )

        logger.info(f"Scheduled nightly reindex at {nightly_time}")

    def _process_file_changes(self) -> None:
        """Process queued file changes with extraction pipeline."""
        logger.info("File processing worker started")

        while not self._shutdown_event.is_set():
            try:
                # Get pending changes (max 30 seconds old)
                changes = self.file_queue.get_pending_changes(max_age_seconds=30.0)

                if changes:
                    logger.debug(f"Processing {len(changes)} file changes")

                    # Group changes by operation type
                    batch_changes = defaultdict(list)
                    for file_path, event_type, timestamp in changes:
                        batch_changes[event_type].append(file_path)

                    # Process additions and modifications
                    files_to_process = (
                        batch_changes["created"] + batch_changes["modified"]
                    )
                    if files_to_process:
                        self._process_added_files(files_to_process)

                    # Process deletions
                    if "deleted" in batch_changes:
                        self._process_deleted_files(batch_changes["deleted"])

                # Clean up old queue entries
                removed_count = self.file_queue.cleanup_old_entries(
                    max_age_seconds=300.0
                )
                if removed_count > 0:
                    logger.debug(f"Cleaned up {removed_count} old queue entries")

                # Sleep briefly before next iteration
                time.sleep(2.0)

            except Exception as e:
                logger.error(f"Error in file processing worker: {e}")
                self._stats["errors"] += 1
                time.sleep(5.0)  # Longer sleep on error

        logger.info("File processing worker stopped")

    def _process_added_files(self, file_paths: List[str]) -> None:
        """Process added/modified files with direct extraction."""
        if not file_paths:
            return

        logger.info(f"Processing {len(file_paths)} added/modified files")

        # Update progress start
        self._progress.update(
            {
                "is_indexing": True,
                "total_files": len(file_paths),
                "processed_count": 0,
                "percent_complete": 0,
            }
        )
        self._save_status()

        batch_start_time = time.time()

        successful_extractions = []
        failed_extractions = []
        extractor = Extractor()

        for i, file_path in enumerate(file_paths):
            # Update progress current file
            self._progress["current_file"] = str(Path(file_path).name)
            self._progress["processed_count"] = i
            self._progress["percent_complete"] = int((i / len(file_paths)) * 100)

            # Save status periodically
            if i % 5 == 0:
                self._save_status()

            try:
                # Step 1: Extract text from source file
                logger.debug(f"Extracting text from: {file_path}")
                text = extractor.run(Path(file_path))

                if not text or len(text.strip()) < 10:
                    logger.warning(f"No meaningful text extracted from {file_path}")
                    failed_extractions.append(file_path)
                    continue

                # Step 2: Add to search index using absolute path
                if self.embedding_manager is None:
                    logger.error("Embedding manager not initialized")
                    failed_extractions.append(file_path)
                    continue

                # Use absolute path
                abs_path = str(Path(file_path).resolve()).replace("\\", "/")
                success = self.embedding_manager.add_document(abs_path, text)

                if success:
                    successful_extractions.append(file_path)
                    self._stats["files_processed"] += 1

                    # Update stats
                    file_size = (
                        Path(file_path).stat().st_size
                        if Path(file_path).exists()
                        else 0
                    )
                    self._stats["total_size_bytes"] += file_size

                    logger.info(f"Successfully processed: {file_path}")
                else:
                    failed_extractions.append(file_path)
                    logger.error(f"Failed to add to index: {file_path}")

            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                failed_extractions.append(file_path)
                self._stats["errors"] += 1

        # Batch completion
        processing_time = time.time() - batch_start_time
        self._stats["processing_time_seconds"] += processing_time

        # Reset progress
        self._progress.update(
            {
                "is_indexing": False,
                "current_file": None,
                "processed_count": len(file_paths),
                "total_files": len(file_paths),
                "percent_complete": 100,
            }
        )
        self._save_status()

        if successful_extractions:
            # Save index after successful batch
            if self.embedding_manager is not None:
                self.embedding_manager.save_index()
            logger.info(
                f"Batch processed: {len(successful_extractions)} added, 0 updated, 0 deleted"
            )

        if failed_extractions:
            logger.warning(
                f"Failed to process {len(failed_extractions)} files: {failed_extractions[:3]}"
            )

    def _process_deleted_files(self, file_paths: List[str]) -> None:
        """Process deleted files by removing from index."""
        if not file_paths:
            return

        logger.info(f"Processing {len(file_paths)} deleted files")

        for file_path in file_paths:
            try:
                # Remove from index using absolute path
                if self.embedding_manager is None:
                    logger.error("Embedding manager not initialized")
                    continue

                # We might not be able to resolve absolute path if file is deleted
                # But we should have stored it as absolute path
                # Try to resolve if possible, otherwise assume it was absolute or relative to cwd
                # Since we store absolute paths, we need to try to match that.
                # The file_path from watchdog is usually absolute or relative to cwd.
                abs_path = str(Path(file_path).resolve()).replace("\\", "/")

                success = self.embedding_manager.remove_document(abs_path)

                if success:
                    self._stats["files_deleted"] += 1
                    logger.info(f"Removed from index: {file_path}")

            except Exception as e:
                logger.error(f"Error processing deleted file {file_path}: {e}")
                self._stats["errors"] += 1

        # Save index after deletions
        if self.embedding_manager is not None:
            self.embedding_manager.save_index()

    def _nightly_reindex(self) -> None:
        """Perform a full reindex of all files."""
        logger.info("Starting nightly full reindex...")
        start_time = time.time()

        try:
            # Backup current index if configured
            if self.config.get("indexing", {}).get("backup_before_update", True):
                self._backup_index()

            # Clear the current index
            if self.embedding_manager is not None and hasattr(
                self.embedding_manager, "clear_index"
            ):
                self.embedding_manager.clear_index()
            else:
                self.embedding_manager = EmbeddingAdapter()

            # Rebuild index using watch paths
            watch_paths = self.config.get("watch_paths", [])
            if self.embedding_manager is not None:
                self.embedding_manager.build_index(watch_paths)

            # Update statistics
            self._stats["last_full_reindex"] = datetime.now().isoformat()

            duration = time.time() - start_time
            logger.info(f"Nightly reindex completed in {duration:.2f} seconds")

        except Exception as e:
            logger.error(f"Error during nightly reindex: {e}")
            logger.error(traceback.format_exc())
            self._stats["errors"] = (self._stats.get("errors") or 0) + 1

    def _backup_index(self) -> None:
        """Create a backup of the current index."""
        try:
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Backup FAISS index
            if os.path.exists(INDEX_PATH):
                shutil.copy2(INDEX_PATH, backup_dir / f"index_{timestamp}.faiss")

            # Backup metadata
            if os.path.exists(DATABASE_PATH):
                shutil.copy2(DATABASE_PATH, backup_dir / f"meta_{timestamp}.sqlite")

            logger.info(f"Index backed up with timestamp {timestamp}")

        except Exception as e:
            logger.error(f"Error creating backup: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get current statistics."""
        stats: Dict[str, Any] = dict(self._stats)
        stats["queue_size"] = self.file_queue.size()
        stats["is_running"] = self._running
        stats["progress"] = dict(self._progress)
        if stats["start_time"]:
            stats["uptime_seconds"] = time.time() - (stats["start_time"] or 0)
        return stats

    def _initial_scan(self) -> None:
        """Scan watched directories for files that are not yet indexed."""
        logger.info("Performing initial scan for missing files...")
        try:
            # Get all currently indexed files
            indexed_files = set()
            if os.path.exists(DATABASE_PATH):
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT file FROM meta")
                # Normalize paths for comparison
                indexed_files = {
                    str(Path(row[0]).resolve()).replace("\\", "/")
                    for row in cursor.fetchall()
                }
                conn.close()

            logger.info(f"Found {len(indexed_files)} files already in index")

            # Scan watch paths
            watch_paths = self.config.get("watch_paths", [])
            files_to_index = []

            for watch_path in watch_paths:
                if not os.path.exists(watch_path):
                    continue

                # Get all supported files
                found_files = get_supported_files(watch_path)

                for file_path in found_files:
                    # Normalize path
                    abs_path = str(file_path.resolve()).replace("\\", "/")

                    if abs_path not in indexed_files:
                        files_to_index.append(str(file_path))

            if files_to_index:
                logger.info(f"Found {len(files_to_index)} new files to index")
                # Add to queue as 'created' events
                for path_str in files_to_index:
                    self.file_queue.add_change(path_str, "created")
            else:
                logger.info("No new files found to index")

        except Exception as e:
            logger.error(f"Error during initial scan: {e}")

    def start(self) -> None:
        """Start the file watcher."""
        if self._running:
            logger.warning("File watcher is already running")
            return

        try:
            logger.info("Starting file watcher...")

            # Initialize components
            self._initialize_components()

            # Set up file watching
            self._setup_file_watching()

            # Perform initial scan for missing files
            self._initial_scan()

            # Set up scheduler
            self._setup_scheduler()

            # Start components
            self.observer.start()
            self.scheduler.start()

            # Start worker thread
            self._worker_thread = threading.Thread(
                target=self._process_file_changes, daemon=True
            )
            self._worker_thread.start()

            # Update state
            self._running = True
            self._stats["start_time"] = time.time()
            self._stats["last_processed_time"] = time.time()

            logger.info("File watcher started successfully")

        except Exception as e:
            logger.error(f"Failed to start file watcher: {e}")
            self.stop()
            raise

    def stop(self) -> None:
        """Stop the file watcher."""
        if not self._running:
            return

        logger.info("Stopping file watcher...")

        try:
            # Signal shutdown
            self._shutdown_event.set()
            self._running = False

            # Stop components
            if self.observer.is_alive():
                self.observer.stop()
                self.observer.join(timeout=5)

            # Wait for worker thread
            if self._worker_thread and self._worker_thread.is_alive():
                self._worker_thread.join(timeout=5)

            logger.info("File watcher stopped")

        except Exception as e:
            logger.error(f"Error stopping file watcher: {e}")
            time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            logger.error(traceback.format_exc())

    def run(self) -> None:
        """Start the watcher and keep it running until interrupted."""
        try:
            self.start()
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received. Stopping watcher...")
            self.stop()


def main() -> None:
    """Main entry point for the file watcher daemon."""
    import argparse

    parser = argparse.ArgumentParser(description="AI File Search Watcher Daemon")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show configuration and exit"
    )

    args = parser.parse_args()

    # Create watcher
    watcher = FileWatcher(config_path=args.config)

    if args.dry_run:
        print("Configuration:")
        print(yaml.dump(watcher.config, default_flow_style=False))
        return

    # Run the watcher
    watcher.run()


if __name__ == "__main__":
    main()
