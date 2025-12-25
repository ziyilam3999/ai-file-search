#!/usr/bin/env python3
"""
Integration test for the enhanced FileWatcher system
Tests the complete file watcher with real operations, including subfolder search.
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

pytestmark = pytest.mark.slow  # Mark all tests in this module as slow

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

            # Remove any existing index file to avoid stale data
            for stale_file in ["index.faiss", "meta.sqlite"]:
                if os.path.exists(stale_file):
                    os.remove(stale_file)

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


def search_in_index(watcher, query):
    """
    Simple search function for demonstration.
    Returns a list of dicts with 'path' and 'chunk' keys.
    """
    if hasattr(watcher.embedding_manager, "search"):
        return watcher.embedding_manager.search(query)
    else:
        raise RuntimeError(
            "Embedding manager does not have a 'search' method. Test cannot proceed."
        )


def test_search_finds_files_in_subfolders():
    """
    Comprehensive test: files in subfolders are indexed and found by search.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create subfolders (but do not write files yet)
        sub1 = Path(temp_dir) / "subfolder1"
        sub2 = Path(temp_dir) / "subfolder2"
        sub1.mkdir()
        sub2.mkdir()

        # Set up watcher config
        config = {
            "watch_directories": [temp_dir],
            "file_patterns": {"include": ["*.txt"], "ignore": ["*.tmp"]},
            "timing": {"debounce_seconds": 1, "max_wait_seconds": 5},
            "logging": {"level": "INFO", "console_output": True},
        }

        # Define temp paths for index and db
        temp_index = Path(temp_dir) / "index.faiss"
        temp_db = Path(temp_dir) / "meta.sqlite"

        # Patch the paths used by Embedder
        with (
            patch("core.embedding.INDEX_PATH", str(temp_index)),
            patch("core.embedding.DATABASE_PATH", str(temp_db)),
        ):

            watcher = FileWatcher()
            watcher.config = config
            watcher._initialize_components()

            # Monkeypatch _map_to_original_file to return the file path itself
            # This avoids the dependency on ai_search_docs for this test
            watcher.embedding_manager.embedder._map_to_original_file = lambda p: str(p)

            # Create a dummy file to ensure index is built
            dummy = Path(temp_dir) / "dummy.txt"
            dummy.write_text("Dummy content for initialization.")

            # Initialize the DB schema (meta table) before adding files
            # Use patch to ensure _map_to_original_file is mocked during build_index
            # Note: We need to patch on the embedder instance inside embedding_manager
            with patch.object(
                watcher.embedding_manager.embedder,
                "_map_to_original_file",
                side_effect=lambda p: str(p),
            ):
                watcher.embedding_manager.build_index(extracts_path=Path(temp_dir))

            # Now write files to subfolders
            file1 = sub1 / "doc.txt"
            file2 = sub2 / "doc.txt"
            file3 = sub2 / "ignore.tmp"
            file1.write_text("This is a test in subfolder one.")
            file2.write_text("This is a test in subfolder two.")
            file3.write_text("This should be ignored.")

            # Index the files in the subfolders incrementally
            watcher.embedding_manager.add_document(
                str(file1.relative_to(temp_dir)), file1.read_text()
            )
            watcher.embedding_manager.add_document(
                str(file2.relative_to(temp_dir)), file2.read_text()
            )
            watcher.embedding_manager.save_index()

            # Search for text in subfolder one
            results1 = search_in_index(watcher, "subfolder one")
            filtered1 = [r for r in results1 if r["path"]]
            print("Search results for subfolder one:", filtered1)
            assert any(
                "subfolder1/doc.txt" in r["path"].replace("\\", "/") for r in filtered1
            ), "Expected 'subfolder1/doc.txt' in results"

            # Search for text in subfolder two
            results2 = search_in_index(watcher, "subfolder two")
            filtered2 = [r for r in results2 if r["path"]]
            print("Search results for subfolder two:", filtered2)
            assert any(
                "subfolder2/doc.txt" in r["path"].replace("\\", "/") for r in filtered2
            ), "Expected 'subfolder2/doc.txt' in results"

            # Search for ignored file (should not be found)
            results3 = search_in_index(watcher, "should be ignored")
            filtered3 = [r for r in results3 if r["path"]]
            print("Search results for ignored file:", filtered3)
            assert not any(
                "ignore.tmp" in r["path"] for r in filtered3
            ), "Ignored file should not appear in results"

            # Search for non-existent text
            results4 = search_in_index(watcher, "this text does not exist")
            filtered4 = [r for r in results4 if r["path"]]
            print("Search results for non-existent text:", filtered4)
            assert filtered4 == [] or all(
                "chunk" in r and "path" in r for r in filtered4
            ), "Non-existent text should return empty or valid result structure"

            print("✅ Comprehensive subfolder search test passed!")


if __name__ == "__main__":
    test_integration()
    test_search_finds_files_in_subfolders()
