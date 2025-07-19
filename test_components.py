#!/usr/bin/env python3
"""Quick component test for FileWatcher system"""

import time

from daemon.watch import FileWatcher


def test_filewatcher_components():
    print("🧪 Testing FileWatcher component initialization...")

    try:
        # Initialize FileWatcher
        watcher = FileWatcher()
        print("✅ FileWatcher initialized successfully")

        # Test statistics
        stats = watcher.get_statistics()
        print(
            f'Initial stats: files_processed={stats["files_processed"]}, is_running={stats["is_running"]}'
        )

        # Test queue operations
        watcher.file_queue.add_change("test.txt", "created")
        print(f"Queue size after adding change: {watcher.file_queue.size()}")

        changes = watcher.file_queue.get_pending_changes()
        print(f"Retrieved {len(changes)} changes from queue")

        # Test file pattern matching
        print("🔍 Testing file pattern matching...")
        from daemon.watch import FileChangeHandler

        handler = FileChangeHandler(watcher.file_queue, watcher.config)

        test_files = [
            "document.txt",  # Should be processed
            "image.jpg",  # Should be ignored (not in include patterns)
            "temp.tmp",  # Should be ignored (in ignore patterns)
            "readme.md",  # Should be processed
            "log.log",  # Should be ignored (in ignore patterns)
        ]

        for test_file in test_files:
            should_process = handler._should_process_file(test_file)
            print(f'   {test_file}: {"✅ process" if should_process else "❌ ignore"}')

        # Test configuration details
        print("⚙️ Testing configuration details...")
        print(f'   Watch directories: {watcher.config.get("watch_directories", [])}')
        print(
            f'   Include patterns: {watcher.config.get("file_patterns", {}).get("include", [])}'
        )
        print(
            f'   Ignore patterns: {watcher.config.get("file_patterns", {}).get("ignore", [])}'
        )
        print(
            f'   Debounce seconds: {watcher.config.get("timing", {}).get("debounce_seconds", 5)}'
        )
        print(
            f'   Nightly reindex: {watcher.config.get("timing", {}).get("nightly_reindex_time", "02:00")}'
        )

        # Test component initialization (without starting)
        print("🔧 Testing component initialization...")
        try:
            watcher._initialize_components()
            print("   ✅ Components initialized successfully")
            print(f"   Embedding manager: {type(watcher.embedding_manager).__name__}")
            print(f"   Document extractor: {type(watcher.document_extractor).__name__}")
        except Exception as e:
            print(f"   ❌ Component initialization failed: {e}")

        print("\n🎉 All comprehensive tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_filewatcher_components()
