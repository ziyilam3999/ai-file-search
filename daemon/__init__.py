"""
File watching daemon for AI File Search.

This package contains the file watcher daemon that monitors directories
for changes and automatically indexes files for semantic search.
"""

from daemon.embedding_adapter import EmbeddingAdapter
from daemon.file_queue import FileChangeHandler, FileChangeQueue
from daemon.watch import FileWatcher

__version__ = "0.1.0"

__all__ = [
    "EmbeddingAdapter",
    "FileChangeHandler",
    "FileChangeQueue",
    "FileWatcher",
]
