"""DAEMON: file_queue.py
Thread-safe queue and event handler for managing file change events.
"""

import fnmatch
import os
import threading
import time
from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple

from watchdog.events import FileSystemEventHandler


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

    def _should_process_file(self, file_path: str) -> bool:
        """Check if a file should be processed based on include/ignore patterns."""
        filename = os.path.basename(file_path)

        # Check ignore patterns first
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(
                file_path, pattern
            ):
                return False

        # Check include patterns
        if not self.include_patterns:
            return True

        for pattern in self.include_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True

        return False

    def on_modified(self, event) -> None:
        """Handle file modification events."""
        if not event.is_directory and self._should_process_file(event.src_path):
            self.file_queue.add_change(event.src_path, "modified")

    def on_created(self, event) -> None:
        """Handle file creation events."""
        if not event.is_directory and self._should_process_file(event.src_path):
            self.file_queue.add_change(event.src_path, "created")

    def on_deleted(self, event) -> None:
        """Handle file deletion events."""
        if not event.is_directory and self._should_process_file(event.src_path):
            self.file_queue.add_change(event.src_path, "deleted")
