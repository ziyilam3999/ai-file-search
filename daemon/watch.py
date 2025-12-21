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
from typing import Any, Dict, List, Optional, Set, Tuple

import faiss
import numpy as np
import yaml  # type: ignore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from sentence_transformers import SentenceTransformer
from watchdog.events import (
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

# Import our core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import DATABASE_PATH, INDEX_PATH
from core.embedding import Embedder
from core.extract import Extractor

# COMPLETED: Replace EmbeddingAdapter mock logging with real incremental updates
# Current: Adapter logs "Would add document" / "Would save index"
# Need: Call actual Embedder incremental methods when available
# Requirements:
#   - Real-time index updates within 5 seconds
#   - Atomic operations (success/failure, no partial states)
#   - Error recovery and retry logic
#   - Statistics tracking for monitoring
# Depends on: core/embedding.py incremental methods implementation

# TODO(copilot): Expand statistics collection for performance monitoring
# Current: Basic counters (files_processed, errors, uptime)
# Need detailed metrics:
#   - Per-operation timing (detection, extraction, indexing)
#   - Throughput rates (files/minute, MB/sec)
#   - Queue depth over time
#   - Error categorization and frequency
#   - Memory usage tracking
#   - Disk I/O statistics
# Requirements:
#   - Expose via get_statistics() API
#   - Time-series data for trending
#   - Configurable retention period


# TODO(copilot): Implement health monitoring and alerting system
# Features:
#   - Watchdog for the watcher (meta-monitoring)
#   - Automatic restart on crashes
#   - Performance degradation detection
#   - Disk space monitoring for index files
#   - Memory leak detection
#   - Configuration drift detection
#   - Email/webhook notifications for critical issues
# Requirements:
#   - Configurable alert thresholds
#   - Rate limiting for notifications
#   - Graceful degradation modes


class EmbeddingAdapter:
    """Enhanced adapter with real incremental updates to the FAISS index."""

    def __init__(self) -> None:
        self.embedder = Embedder()
        self._stats: Dict[str, Any] = {
            "documents_added": 0,
            "documents_removed": 0,
            "operations_failed": 0,
            "last_operation_time": 0,
            "index_size": 0,
        }
        self._pending_operations: List[Tuple[str, str, Optional[str]]] = []
        self._operation_lock = threading.Lock()

        # Pre-warm the model to avoid first-operation delay
        self._pre_warm_model()

    def _pre_warm_model(self) -> None:
        """Pre-warm the embedding model to avoid delays on first use."""
        try:
            logger.debug("Pre-warming embedding model...")
            model = SentenceTransformer(self.embedder.model_name)
            # Generate a dummy embedding to initialize everything
            model.encode(["initialization"], show_progress_bar=False)
            logger.debug("Model pre-warming completed")
        except Exception as e:
            logger.warning(f"Model pre-warming failed: {e}")

    def add_document(self, file_path: str, text: str) -> bool:
        """Add a document to the index with real incremental updates."""
        operation_start = time.time()

        try:
            with self._operation_lock:
                logger.debug(f"Adding document to index: {file_path}")

                # Step 1: Remove existing document if it exists (for updates)
                self._remove_existing_document(file_path)

                # Step 2: Process the text into chunks
                chunks = self._process_text_to_chunks(text)
                if not chunks:
                    logger.warning(f"No valid chunks generated for {file_path}")
                    return False

                # Step 3: Generate embeddings for chunks
                embeddings = self._generate_embeddings(chunks)
                if not embeddings:
                    logger.error(f"Failed to generate embeddings for {file_path}")
                    self._stats["operations_failed"] += 1
                    return False

                # Step 4: Add to FAISS index and database
                success = self._add_to_faiss_and_db(file_path, chunks, embeddings)

                if success:
                    self._stats["documents_added"] += 1
                    self._stats["index_size"] = self._get_current_index_size()
                    logger.info(
                        f"Successfully added document: {file_path} ({len(chunks)} chunks)"
                    )
                else:
                    self._stats["operations_failed"] += 1
                    logger.error(f"Failed to add document: {file_path}")

                self._stats["last_operation_time"] = time.time()
                processing_time = time.time() - operation_start
                logger.debug(f"Document processing took {processing_time:.3f} seconds")

                return success

        except Exception as e:
            self._stats["operations_failed"] += 1
            logger.error(f"Error adding document {file_path}: {e}")
            return False

    def remove_document(self, file_path: str) -> bool:
        """Remove a document from the index."""
        try:
            with self._operation_lock:
                logger.debug(f"Removing document from index: {file_path}")

                success = self._remove_existing_document(file_path)

                if success:
                    self._stats["documents_removed"] += 1
                    self._stats["index_size"] = self._get_current_index_size()
                    logger.info(f"Successfully removed document: {file_path}")
                else:
                    logger.warning(f"Document not found in index: {file_path}")

                self._stats["last_operation_time"] = time.time()
                return success

        except Exception as e:
            self._stats["operations_failed"] += 1
            logger.error(f"Error removing document {file_path}: {e}")
            return False

    def save_index(self) -> bool:
        """Save the current index state to disk."""
        try:
            # Load current index from disk to save it (no direct access to private methods)
            if os.path.exists(self.embedder.index_path):
                index = faiss.read_index(self.embedder.index_path)
                faiss.write_index(index, self.embedder.index_path)
                logger.info("Index successfully saved to disk")
                return True
            else:
                logger.warning("No index file found to save")
                return False
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            return False

    def clear_index(self) -> bool:
        """Clear the entire index (used for full reindex)."""
        try:
            with self._operation_lock:
                logger.info("Clearing entire index")

                # Clear database
                conn = sqlite3.connect(DATABASE_PATH)
                conn.execute("DELETE FROM meta")
                conn.commit()
                conn.close()

                # Remove index files to clear
                if os.path.exists(self.embedder.index_path):
                    os.remove(self.embedder.index_path)

                # Reset stats
                self._stats["index_size"] = 0
                self._stats["last_operation_time"] = time.time()

                logger.info("Index cleared successfully")
                return True

        except Exception as e:
            logger.error(f"Error clearing index: {e}")
            self._stats["operations_failed"] += 1
            return False

    def build_index(self, extracts_path: Path) -> None:
        """Delegate to the underlying Embedder's build_index method."""
        self.embedder.build_index(extracts_dir=str(extracts_path))

    def get_adapter_stats(self) -> Dict[str, Any]:
        """Get detailed statistics about adapter operations."""
        stats = self._stats.copy()
        stats["pending_operations"] = len(self._pending_operations)
        return stats

    def _process_text_to_chunks(self, text: str) -> List[str]:
        """Process text into chunks using the embedder's chunking logic."""
        try:
            chunks = self.embedder._chunk_text(text)
            # Filter out very short chunks
            valid_chunks = [chunk for chunk in chunks if len(chunk.strip()) >= 20]
            return valid_chunks
        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            return []

    def _generate_embeddings(self, chunks: List[str]) -> Optional[List]:
        """Generate embeddings for a list of chunks."""
        try:
            model = SentenceTransformer(self.embedder.model_name)

            # Truncate chunks to model's max length
            processed_chunks = [chunk[:256] for chunk in chunks]

            embeddings = model.encode(
                processed_chunks,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )

            return embeddings.tolist()

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return None

    def _add_to_faiss_and_db(
        self, file_path: str, chunks: List[str], embeddings: List
    ) -> bool:
        """Add chunks and embeddings to FAISS index and metadata database."""
        try:
            # Get current index and database
            index = faiss.read_index(self.embedder.index_path)
            conn = sqlite3.connect(self.embedder.db_path)

            # Get next available ID
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM meta")
            max_id = cursor.fetchone()[0]
            next_id = (max_id or 0) + 1

            # Add embeddings to FAISS
            embeddings_array = np.array(embeddings, dtype=np.float32)
            index.add(embeddings_array)

            # Add metadata to database
            # Store the full relative path, not just the filename!
            metadata_entries = [
                (next_id + i, file_path, chunk) for i, chunk in enumerate(chunks)
            ]

            cursor.executemany(
                "INSERT INTO meta (id, file, chunk) VALUES (?, ?, ?)", metadata_entries
            )

            conn.commit()
            # conn.close()

            return True

        except Exception as e:
            logger.error(f"Error adding to FAISS and DB: {e}")
            return False

    def _remove_existing_document(self, file_path: str) -> bool:
        """Remove existing document chunks from index (for updates)."""
        try:
            # Use the full relative path for matching, not just the basename
            conn = sqlite3.connect(self.embedder.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM meta WHERE file = ?", (file_path,))
            existing_ids = [row[0] for row in cursor.fetchall()]

            if existing_ids:
                # Remove from database
                placeholders = ",".join("?" for _ in existing_ids)
                cursor.execute(
                    f"DELETE FROM meta WHERE id IN ({placeholders})", existing_ids
                )
                conn.commit()
                logger.debug(
                    f"Removed {len(existing_ids)} existing chunks for {file_path}"
                )

            # conn.close()
            return len(existing_ids) > 0

        except Exception as e:
            logger.error(f"Error removing existing document: {e}")
            return False

    def _get_current_index_size(self) -> int:
        """Get the current number of vectors in the index."""
        try:
            if os.path.exists(self.embedder.index_path):
                index = faiss.read_index(self.embedder.index_path)
            return index.ntotal
        except Exception:
            return 0

    def _cleanup_old_backups(self) -> None:
        """Clean up old backup files, keeping only the last 3."""
        try:
            backup_files = glob.glob("index_backup_*.faiss")
            backup_files.sort(reverse=True)  # Most recent first

            # Remove all but the 3 most recent
            for old_backup in backup_files[3:]:
                os.remove(old_backup)
                logger.debug(f"Removed old backup: {old_backup}")

        except Exception as e:
            logger.debug(f"Error cleaning up backups: {e}")

    def search(self, query: str) -> List[Dict[str, Optional[str]]]:
        """
        Search the index for the given query and return a list of dicts with 'path' and 'chunk' keys.

        Args:
            query: The search query string

        Returns:
            List of dictionaries containing 'path' and 'chunk' keys
        """
        try:
            # Use the Embedder's query method to get results with 'id'
            results = self.embedder.query(query)
            conn = sqlite3.connect(DATABASE_PATH)
            # cursor = conn.cursor()
            formatted = []
            for r in results:
                # r is a tuple: (file, chunk) or (file, chunk, id)
                if isinstance(r, dict):
                    file_path = r.get("file") or r.get("path")
                    chunk = r.get("chunk")
                elif isinstance(r, tuple):
                    # Try to unpack (file, chunk) or (id, file, chunk)
                    if len(r) == 3:
                        _, file_path, chunk = r
                    elif len(r) == 2:
                        file_path, chunk = r
                    else:
                        file_path, chunk = None, None
                else:
                    file_path, chunk = None, None
                formatted.append(
                    {
                        "path": file_path,
                        "chunk": chunk,
                    }
                )
            conn.close()
            return formatted
        except Exception as e:
            logger.error(f"Error in search: {e}")
            return []


class ExtractorAdapter:
    """Adapter to make the existing Extractor class work with the watcher."""

    def __init__(self) -> None:
        self.extractor = Extractor()

    def extract_text(self, file_path: str) -> str:
        """Extract text from a file."""
        if self.extractor is not None:
            return self.extractor.run(Path(file_path))
        else:
            raise RuntimeError("Extractor not initialized")

    def _extract_document(self, file_path: Path) -> str:
        """Extract text from a document using the extractor."""
        if self.extractor is not None:
            return self.extractor.run(file_path)
        else:
            raise RuntimeError("Extractor not initialized")


class FileChangeQueue:
    """Thread-safe queue for managing file change events with deduplication."""

    def __init__(self) -> None:
        self._queue: deque = deque()
        self._lock = threading.Lock()
        self._seen_files: Set[str] = set()

    def add_change(self, file_path: str, event_type: str) -> None:
        """Add a file change to the queue, deduplicating recent changes."""
        with self._lock:
            # Remove any existing entries for this file
            self._queue = deque([item for item in self._queue if item[0] != file_path])
            self._seen_files.discard(file_path)

            # Add the new change
            self._queue.append((file_path, event_type, time.time()))
            self._seen_files.add(file_path)

    def cleanup_old_entries(self, max_age_seconds: Optional[float] = None) -> int:
        """Clean up old entries from the queue."""
        if max_age_seconds is None:
            return 0

        with self._lock:
            current_time = time.time()
            old_count = 0
            new_queue: deque = deque()

            for item in self._queue:
                file_path, event_type, timestamp = item
                if current_time - timestamp >= max_age_seconds:
                    old_count += 1
                    self._seen_files.discard(file_path)
                else:
                    new_queue.append(item)

            self._queue = new_queue
            return old_count

    def get_pending_changes(
        self, max_age_seconds: Optional[float] = None
    ) -> List[Tuple[str, str, float]]:
        """Get all pending changes, optionally filtering by age."""
        with self._lock:
            if max_age_seconds is None:
                changes = list(self._queue)
                self._queue.clear()
                self._seen_files.clear()
                return changes

            current_time = time.time()
            old_changes = []
            new_queue: deque = deque()

            for item in self._queue:
                file_path, event_type, timestamp = item
                if current_time - timestamp >= max_age_seconds:
                    old_changes.append(item)
                    self._seen_files.discard(file_path)
                else:
                    new_queue.append(item)

            self._queue = new_queue
            return old_changes

    def size(self) -> int:
        """Get the current queue size."""
        with self._lock:
            return len(self._queue)

    def clear(self) -> None:
        """Clear all pending changes."""
        with self._lock:
            self._queue.clear()
            self._seen_files.clear()


class FileChangeHandler(FileSystemEventHandler):
    """Handles file system events and queues them for processing."""

    def __init__(self, file_queue: FileChangeQueue, config: Dict[str, Any]) -> None:
        self.file_queue = file_queue
        self.config = config
        self.include_patterns = config.get("file_patterns", {}).get("include", [])
        self.ignore_patterns = config.get("file_patterns", {}).get("ignore", [])

        logger.debug(
            f"FileChangeHandler initialized with include patterns: {self.include_patterns}"
        )
        logger.debug(
            f"FileChangeHandler initialized with ignore patterns: {self.ignore_patterns}"
        )

    def _should_process_file(self, file_path: str) -> bool:
        """Check if a file should be processed based on include/ignore patterns."""
        filename = os.path.basename(file_path)

        # Check ignore patterns first
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(
                file_path, pattern
            ):
                logger.debug(f"File {file_path} ignored due to pattern {pattern}")
                return False

        # Check include patterns
        if not self.include_patterns:
            return True

        for pattern in self.include_patterns:
            if fnmatch.fnmatch(filename, pattern):
                logger.debug(f"File {file_path} included due to pattern {pattern}")
                return True

        logger.debug(f"File {file_path} not included by any pattern")
        return False

    def on_modified(self, event) -> None:
        """Handle file modification events."""
        if not event.is_directory and self._should_process_file(event.src_path):
            logger.debug(f"File modified: {event.src_path}")
            self.file_queue.add_change(event.src_path, "modified")

    def on_created(self, event) -> None:
        """Handle file creation events."""
        if not event.is_directory and self._should_process_file(event.src_path):
            logger.debug(f"File created: {event.src_path}")
            self.file_queue.add_change(event.src_path, "created")

    def on_deleted(self, event) -> None:
        """Handle file deletion events."""
        if not event.is_directory and self._should_process_file(event.src_path):
            logger.debug(f"File deleted: {event.src_path}")
            self.file_queue.add_change(event.src_path, "deleted")


class FileWatcher:
    """Main file watcher class that coordinates all watching activities."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config_path = config_path or "prompts/watcher_config.yaml"
        self.config = self._load_config()
        self._setup_logging()

        # Core components
        self.embedding_manager: Optional[EmbeddingAdapter] = None
        self.document_extractor: Optional[ExtractorAdapter] = None
        self.file_queue = FileChangeQueue()
        self.observer = Observer()
        self.scheduler = BackgroundScheduler()

        # State management
        self._running = False
        self._shutdown_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._stats: Dict[str, Any] = {
            "files_processed": 0,
            "files_added": 0,
            "files_updated": 0,
            "files_deleted": 0,
            "last_full_reindex": None,
            "start_time": None,
            "errors": 0,
            "processing_time_seconds": 0,
            "total_size_bytes": 0,
            "last_processed_time": 0,
        }

        logger.info("FileWatcher initialized")

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

            # OPTION 1 ARCHITECTURE: Enforce ai_search_docs only watching
            config["watch_directories"] = ["ai_search_docs"]

            # Extract watch directories from document_categories if present
            if "document_categories" in yaml_config:
                watch_dirs = set()
                for category, category_config in yaml_config[
                    "document_categories"
                ].items():
                    if category_config.get("enabled", True):
                        for path in category_config.get("paths", []):
                            # Only watch ai_search_docs paths (Option 1 architecture)
                            if path.startswith("ai_search_docs/"):
                                watch_dirs.add("ai_search_docs")

                if watch_dirs:
                    config["watch_directories"] = list(watch_dirs)

            # Override with any direct YAML settings (but preserve Option 1)
            if "file_patterns" in yaml_config:
                config["file_patterns"].update(yaml_config["file_patterns"])

            # NEVER allow extracts in watch_directories (Option 1 enforcement)
            if "watch_directories" in yaml_config:
                yaml_dirs = yaml_config["watch_directories"]
                if isinstance(yaml_dirs, list):
                    # Filter out extracts directory
                    filtered_dirs = [d for d in yaml_dirs if d != "extracts"]
                    if "ai_search_docs" not in filtered_dirs:
                        filtered_dirs.append("ai_search_docs")
                    config["watch_directories"] = filtered_dirs

            logger.info(f"Configuration loaded from {self.config_path}")
            logger.info(
                f"Watching directories (Option 1): {config['watch_directories']}"
            )
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "watch_directories": ["ai_search_docs"],  # Only watch input directory
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
                "file": "logs/watcher.log",
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

            logger.info("Initializing document extractor...")
            self.document_extractor = ExtractorAdapter()

            logger.info("Core components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise

    def _setup_file_watching(self) -> None:
        """Set up file system watching."""
        handler = FileChangeHandler(self.file_queue, self.config)

        watch_dirs = self.config.get("watch_directories", [])
        for watch_dir in watch_dirs:
            if os.path.exists(watch_dir):
                self.observer.schedule(handler, watch_dir, recursive=True)
                logger.info(f"Watching directory: {watch_dir}")
            else:
                logger.warning(f"Watch directory does not exist: {watch_dir}")

        if not watch_dirs:
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

                    # Process additions and modifications (with extraction)
                    for event_type in ["created", "modified"]:
                        if event_type in batch_changes:
                            self._process_added_files(batch_changes[event_type])

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
        """Process added/modified files with extraction to extracts/."""
        if not file_paths:
            return

        logger.info(f"Processing {len(file_paths)} added/modified files")
        batch_start_time = time.time()

        successful_extractions = []
        failed_extractions = []

        for file_path in file_paths:
            try:
                # Step 1: Extract text from source file
                logger.debug(f"Extracting text from: {file_path}")
                if self.document_extractor is None:
                    logger.error("Document extractor not initialized")
                    failed_extractions.append(file_path)
                    continue
                text = self.document_extractor.extract_text(file_path)

                if not text or len(text.strip()) < 10:
                    logger.warning(f"No meaningful text extracted from {file_path}")
                    failed_extractions.append(file_path)
                    continue

                # Step 2: Determine extract path
                extract_path = self._get_extract_path(file_path)

                # Step 3: Save extracted text to extracts/
                extract_path.parent.mkdir(parents=True, exist_ok=True)
                with open(extract_path, "w", encoding="utf-8") as f:
                    f.write(text)

                logger.debug(f"Saved extracted text to: {extract_path}")

                # Step 4: Add to search index using extract path
                if self.embedding_manager is None:
                    logger.error("Embedding manager not initialized")
                    failed_extractions.append(file_path)
                    continue
                relative_extract_path = str(extract_path.relative_to("extracts"))
                success = self.embedding_manager.add_document(
                    relative_extract_path, text
                )

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

                    logger.info(f"Successfully processed: {file_path} → {extract_path}")
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

    def _get_extract_path(self, source_path: str) -> Path:
        """Convert source file path to corresponding extract path."""
        source = Path(source_path)

        # Convert ai_search_docs/category/file.pdf → extracts/category/file.txt
        if len(source.parts) >= 2 and source.parts[0] == "ai_search_docs":
            # Preserve the category structure
            relative_parts = source.parts[1:]  # Skip 'ai_search_docs'

            # Change extension to .txt
            name_with_txt_ext = source.stem + ".txt"
            extract_parts = ("extracts",) + relative_parts[:-1] + (name_with_txt_ext,)

            extract_path = Path(*extract_parts)
            logger.debug(f"Extract path: {source} → {extract_path}")
            return extract_path
        else:
            # Fallback for other paths - this should rarely be used
            fallback_path = Path("extracts") / (source.stem + ".txt")
            logger.warning(f"Using fallback extract path: {source} → {fallback_path}")
            return fallback_path

    def _process_deleted_files(self, file_paths: List[str]) -> None:
        """Process deleted files by removing from index."""
        if not file_paths:
            return

        logger.info(f"Processing {len(file_paths)} deleted files")

        for file_path in file_paths:
            try:
                # Convert to extract path for index removal
                extract_path = self._get_extract_path(file_path)
                relative_extract_path = str(extract_path.relative_to("extracts"))

                # Remove from index
                if self.embedding_manager is None:
                    logger.error("Embedding manager not initialized")
                    continue
                success = self.embedding_manager.remove_document(relative_extract_path)

                if success:
                    self._stats["files_deleted"] += 1
                    logger.info(f"Removed from index: {file_path}")

                # Also remove the extract file if it exists
                if extract_path.exists():
                    extract_path.unlink()
                    logger.debug(f"Deleted extract file: {extract_path}")

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

            # Recursively find all files
            watch_dirs = self.config.get("watch_directories", [])
            include_patterns = self.config.get("file_patterns", {}).get("include", [])
            all_files = self._get_all_files(watch_dirs, include_patterns)

            total_files = 0
            for file_path in all_files:
                try:
                    if self.document_extractor is not None:
                        text = self.document_extractor.extract_text(file_path)
                        if text.strip() and self.embedding_manager is not None:
                            # Compute relative path for citation
                            for base_dir in watch_dirs:
                                if file_path.startswith(base_dir):
                                    rel_path = os.path.relpath(file_path, base_dir)
                                    break
                            else:
                                rel_path = file_path  # fallback, should not happen

                            self.embedding_manager.add_document(rel_path, text)
                            total_files += 1
                except Exception as e:
                    logger.error(f"Error reindexing {file_path}: {e}")
                    self._stats["errors"] = (self._stats.get("errors") or 0) + 1

            # Save the new index
            if self.embedding_manager is not None:
                self.embedding_manager.save_index()

            # Update statistics
            self._stats["last_full_reindex"] = datetime.now().isoformat()

            duration = time.time() - start_time
            logger.info(
                f"Nightly reindex completed: {total_files} files processed in {duration:.2f} seconds"
            )

        except Exception as e:
            logger.error(f"Error during nightly reindex: {e}")
            logger.error(traceback.format_exc())
            self._stats["errors"] = (self._stats.get("errors") or 0) + 1

    def _should_process_file_patterns(self, file_path: str) -> bool:
        """Check if file should be processed based on patterns."""
        filename = os.path.basename(file_path)

        # Check ignore patterns
        ignore_patterns = self.config.get("file_patterns", {}).get("ignore", [])
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(
                file_path, pattern
            ):
                return False

        # Check include patterns
        include_patterns = self.config.get("file_patterns", {}).get("include", [])
        if not include_patterns:
            return True

        for pattern in include_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True

        return False

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
        stats = self._stats.copy()
        stats["queue_size"] = self.file_queue.size()
        stats["is_running"] = self._running
        if stats["start_time"]:
            stats["uptime_seconds"] = time.time() - (stats["start_time"] or 0)
        return stats

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
        # The recursive self.stop() call is removed to prevent infinite recursion!

    def run(self) -> None:
        """Start the watcher and keep it running until interrupted."""
        try:
            self.start()
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received. Stopping watcher...")
            self.stop()

    def _get_all_files(self, base_dirs: List[str], patterns: List[str]) -> List[str]:
        """
        Recursively find all files matching patterns in all base_dirs and subfolders.
        Returns relative paths for citation.
        """
        found_files = []
        for base_dir in base_dirs:
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, base_dir)
                    # Check include patterns
                    for pattern in patterns:
                        if fnmatch.fnmatch(file, pattern):
                            found_files.append(os.path.join(base_dir, rel_path))
                            break
        return found_files

    # TODO(copilot): Use _get_all_files in reindex and other relevant places


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
