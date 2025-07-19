#!/usr/bin/env python3
"""
Integration test for the enhanced FileWatcher system
Tests the complete file watcher with real operations
"""

import os
import sys
import tempfile
import time
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from daemon.watch import FileWatcher


def test_integration():
    """Test the complete FileWatcher system with enhanced EmbeddingAdapter."""
    print("🚀 Starting FileWatcher Integration Test...")
    print("=" * 60)

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Created test directory: {temp_dir}")

        # Create test config
        config = {
            "watch_directories": [temp_dir],
            "file_patterns": {"include": ["*.txt"], "ignore": ["*.tmp"]},
            "timing": {"debounce_seconds": 1, "max_wait_seconds": 5},
            "logging": {"level": "INFO", "console_output": True},
        }

        # Initialize FileWatcher
        print("🔧 Initializing FileWatcher...")
        watcher = FileWatcher()
        watcher.config = config

        try:
            # Initialize components
            print("📋 Initializing components...")
            watcher._initialize_components()

            # Test the embedding manager directly
            if watcher.embedding_manager:
                print("✅ EmbeddingAdapter initialized successfully")

                # Test document processing
                test_content = "This is a test document for integration testing. It contains multiple sentences to ensure proper chunking and embedding generation."

                print("📝 Testing document addition...")
                success = watcher.embedding_manager.add_document(
                    "test_integration.txt", test_content
                )

                if success:
                    print("✅ Document added successfully")

                    # Get statistics
                    stats = watcher.embedding_manager.get_adapter_stats()
                    print(f"📊 Statistics: {stats}")

                    # Test document removal
                    print("🗑️ Testing document removal...")
                    success = watcher.embedding_manager.remove_document(
                        "test_integration.txt"
                    )

                    if success:
                        print("✅ Document removed successfully")
                    else:
                        print("⚠️ Document removal had issues")

                    # Test index saving
                    print("💾 Testing index saving...")
                    success = watcher.embedding_manager.save_index()

                    if success:
                        print("✅ Index saved successfully")

                        # Check if index file exists
                        if os.path.exists("index.faiss"):
                            print("✅ Index file exists on disk")
                        else:
                            print("⚠️ Index file not found")
                    else:
                        print("❌ Index saving failed")

                else:
                    print("❌ Document addition failed")

            else:
                print("❌ EmbeddingAdapter initialization failed")

            # Test extractor
            if watcher.document_extractor:
                print("✅ ExtractorAdapter initialized successfully")
            else:
                print("❌ ExtractorAdapter initialization failed")

            print("\n🎉 Integration test completed!")
            print("=" * 60)

        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    test_integration()
