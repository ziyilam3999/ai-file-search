#!/usr/bin/env python3
"""
Integration test for the AI file search system
Tests both embedding.py and watch.py functionality
Location: tests/test_embedding_watch_integration.py
"""

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.slow  # Mark all tests in this module as slow

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.embedding import Embedder
from daemon.watch import EmbeddingAdapter, FileChangeQueue, FileWatcher


class TestEmbeddingSystem(unittest.TestCase):
    """Test suite for the core embedding functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.embedder = Embedder()

    def test_embedder_initialization(self):
        """Test basic embedder initialization"""
        self.assertEqual(self.embedder.model_name, "all-MiniLM-L6-v2")
        self.assertEqual(self.embedder.index_path, "index.faiss")
        self.assertEqual(self.embedder.db_path, "meta.sqlite")
        print("✅ Embedder initialization test passed")

    def test_configuration_accessibility(self):
        """Test that configuration attributes are accessible"""
        self.assertTrue(hasattr(self.embedder, "model_name"))
        self.assertTrue(hasattr(self.embedder, "index_path"))
        self.assertTrue(hasattr(self.embedder, "db_path"))
        print("✅ Configuration accessibility test passed")

    def test_query_functionality(self):
        """Test query functionality if index exists"""
        if os.path.exists("index.faiss") and os.path.exists("meta.sqlite"):
            results = self.embedder.query("business rules", 2)
            self.assertIsInstance(results, list)
            print(f"✅ Query test: Found {len(results)} results")

            if results:
                # Verify result format (should be 5-tuple)
                result = results[0]
                self.assertEqual(
                    len(result), 5, f"Expected 5-tuple, got {len(result)}-tuple"
                )
                chunk_text, file_path, chunk_id, doc_chunk_id, score = result

                # Verify types
                self.assertIsInstance(chunk_text, str)
                self.assertIsInstance(file_path, str)
                # Score can be Python float or numpy float
                import numpy as np

                self.assertTrue(
                    isinstance(score, (int, float, np.floating)),
                    f"Score should be numeric, got {type(score)}",
                )

                # Verify citation points to ai_search_docs
                self.assertTrue(
                    file_path.startswith("ai_search_docs/"),
                    f"Citation should start with 'ai_search_docs/', got: {file_path}",
                )
                print(f"✅ Result format and citation correct: {file_path}")
        else:
            print("⚠️  No index found - skipping query test")

    def test_filename_mapping(self):
        """Test filename mapping from extracts to ai_search_docs"""
        test_cases = [
            "business_rules/Reward System Business Rule V2.0.txt",
            "business_rules/Beta Users Campaign Business Rule 2.0.txt",
        ]

        for test_extract_path in test_cases:
            mapped_path = self.embedder._map_to_original_file(test_extract_path)
            if mapped_path:
                self.assertTrue(
                    mapped_path.startswith("ai_search_docs/"),
                    f"Mapped path should start with 'ai_search_docs/', got: {mapped_path}",
                )
                print(f"✅ Filename mapping works: {test_extract_path} → {mapped_path}")
            else:
                print(f"⚠️  No mapping found for: {test_extract_path}")

    def test_chunking_functionality(self):
        """Test text chunking functionality"""
        test_text = "This is a test document. " * 100  # Create a longer text
        chunks = self.embedder._chunk_text(test_text)

        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0, "Should produce at least one chunk")

        # Check that chunks are reasonable length
        for chunk in chunks:
            self.assertIsInstance(chunk, str)
            self.assertGreater(len(chunk.strip()), 0, "Chunks should not be empty")

        print(f"✅ Chunking test: Generated {len(chunks)} chunks")


class TestWatchSystem(unittest.TestCase):
    """Test suite for the file watcher system"""

    def setUp(self):
        """Set up test fixtures"""
        self.adapter = EmbeddingAdapter()
        self.watcher = FileWatcher()

    def test_embedding_adapter_initialization(self):
        """Test EmbeddingAdapter initialization"""
        self.assertIsNotNone(self.adapter.embedder)
        self.assertIsInstance(self.adapter._stats, dict)
        self.assertIn("documents_added", self.adapter._stats)
        self.assertIn("documents_removed", self.adapter._stats)
        print("✅ EmbeddingAdapter initialization test passed")

    def test_adapter_statistics_interface(self):
        """Test statistics interface"""
        stats = self.adapter.get_adapter_stats()
        expected_keys = {
            "documents_added",
            "documents_removed",
            "operations_failed",
            "last_operation_time",
            "index_size",
            "pending_operations",
        }

        self.assertTrue(
            expected_keys.issubset(stats.keys()),
            f"Missing stats keys: {expected_keys - stats.keys()}",
        )

        # Check that all stat values are reasonable
        for key, value in stats.items():
            self.assertIsInstance(value, (int, float, list))

        print("✅ Statistics interface test passed")

    def test_file_watcher_initialization(self):
        """Test FileWatcher initialization"""
        self.assertIsNotNone(self.watcher.config)
        self.assertIsInstance(self.watcher.config, dict)
        print("✅ FileWatcher initialization test passed")

    def test_watcher_configuration(self):
        """Test watcher configuration validation"""
        config = self.watcher.config

        # Check watch directories
        self.assertEqual(
            config["watch_directories"],
            ["ai_search_docs"],
            f"Expected ['ai_search_docs'], got {config['watch_directories']}",
        )

        # Check file patterns
        self.assertIn("include", config["file_patterns"])
        self.assertIn("ignore", config["file_patterns"])

        # Check that include patterns contain expected file types
        include_patterns = config["file_patterns"]["include"]
        self.assertIn("*.pdf", include_patterns)
        self.assertIn("*.txt", include_patterns)

        print("✅ Configuration validation test passed")

    def test_component_compatibility(self):
        """Test compatibility between components"""
        # Test that EmbeddingAdapter has access to embedder attributes
        self.assertTrue(hasattr(self.adapter.embedder, "model_name"))
        self.assertTrue(hasattr(self.adapter.embedder, "index_path"))
        self.assertTrue(hasattr(self.adapter.embedder, "db_path"))

        # Test that adapter can access configuration
        self.assertEqual(self.adapter.embedder.model_name, "all-MiniLM-L6-v2")
        self.assertEqual(self.adapter.embedder.index_path, "index.faiss")
        self.assertEqual(self.adapter.embedder.db_path, "meta.sqlite")

        print("✅ Component compatibility test passed")

    def test_file_change_queue(self):
        """Test file change queue functionality"""
        queue = FileChangeQueue()

        # Test adding changes
        queue.add_change("/test/file1.pdf", "created")
        queue.add_change("/test/file2.pdf", "modified")

        self.assertEqual(queue.size(), 2)

        # Test deduplication
        queue.add_change(
            "/test/file1.pdf", "modified"
        )  # Should replace the previous entry
        self.assertEqual(queue.size(), 2)

        # Test getting changes
        changes = queue.get_pending_changes()
        self.assertEqual(len(changes), 2)
        self.assertEqual(queue.size(), 0)  # Should be empty after getting changes

        print("✅ File change queue test passed")


class TestDatabaseIntegrity(unittest.TestCase):
    """Test suite for database and index integrity"""

    def test_database_structure(self):
        """Test database structure if it exists"""
        if not os.path.exists("meta.sqlite"):
            print("⚠️  No database found - skipping integrity test")
            return

        conn = sqlite3.connect("meta.sqlite")
        cursor = conn.cursor()

        # Check table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='meta'"
        )
        table_exists = cursor.fetchone()
        self.assertIsNotNone(table_exists, "meta table should exist")

        # Check table structure
        cursor.execute("PRAGMA table_info(meta)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        expected_columns = {"id", "file", "chunk", "doc_chunk_id"}

        self.assertTrue(
            expected_columns.issubset(column_names),
            f"Missing columns: {expected_columns - set(column_names)}",
        )

        conn.close()
        print("✅ Database structure test passed")

    def test_data_integrity(self):
        """Test data integrity if database exists"""
        if not os.path.exists("meta.sqlite"):
            print("⚠️  No database found - skipping data integrity test")
            return

        conn = sqlite3.connect("meta.sqlite")
        cursor = conn.cursor()

        # Check data consistency
        cursor.execute("SELECT COUNT(*) FROM meta")
        total_chunks = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT file) FROM meta")
        unique_files = cursor.fetchone()[0]

        self.assertGreater(total_chunks, 0, "Should have some chunks in database")
        self.assertGreater(unique_files, 0, "Should have some files in database")

        print(f"✅ Database stats: {total_chunks} chunks from {unique_files} files")

        # Check citation format
        cursor.execute(
            "SELECT DISTINCT file FROM meta WHERE file LIKE 'ai_search_docs/%' LIMIT 5"
        )
        sample_files = cursor.fetchall()

        if sample_files:
            print("✅ Citations properly formatted:")
            for file_row in sample_files:
                self.assertTrue(
                    file_row[0].startswith("ai_search_docs/"),
                    f"Citation should start with 'ai_search_docs/', got: {file_row[0]}",
                )
                print(f"   📄 {file_row[0]}")

        conn.close()
        print("✅ Data integrity test passed")


class TestErrorHandling(unittest.TestCase):
    """Test suite for error handling and edge cases"""

    def setUp(self):
        """Set up test fixtures"""
        self.embedder = Embedder()
        self.adapter = EmbeddingAdapter()

    def test_nonexistent_file_mapping(self):
        """Test filename mapping with non-existent files"""
        fake_path = "business_rules/NonExistentFile.txt"
        result = self.embedder._map_to_original_file(fake_path)
        self.assertIsNone(result, "Should return None for non-existent files")
        print("✅ Non-existent file mapping test passed")

    def test_empty_query(self):
        """Test query with empty string"""
        if os.path.exists("index.faiss") and os.path.exists("meta.sqlite"):
            results = self.embedder.query("", 5)
            self.assertIsInstance(results, list)
            print("✅ Empty query test passed")
        else:
            print("⚠️  No index found - skipping empty query test")

    def test_adapter_with_missing_index(self):
        """Test adapter behavior when index files are missing"""
        # This test checks that the adapter doesn't crash when files are missing
        stats = self.adapter.get_adapter_stats()
        self.assertIsInstance(stats, dict)
        print("✅ Missing index handling test passed")


def run_integration_tests():
    """Run all integration tests with detailed output"""
    print("🚀 AI File Search System Integration Tests")
    print("=" * 60)

    # Create test loader (modern approach instead of deprecated makeSuite)
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    # Add test cases using modern approach
    test_suite.addTests(loader.loadTestsFromTestCase(TestEmbeddingSystem))
    test_suite.addTests(loader.loadTestsFromTestCase(TestWatchSystem))
    test_suite.addTests(loader.loadTestsFromTestCase(TestDatabaseIntegrity))
    test_suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(test_suite)

    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("🎊 ALL INTEGRATION TESTS PASSED!")
        print("✨ System is working correctly!")
        return 0
    else:
        print(
            f"❌ TESTS FAILED: {len(result.failures)} failures, {len(result.errors)} errors"
        )
        return 1


if __name__ == "__main__":
    exit(run_integration_tests())
