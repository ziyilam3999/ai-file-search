"""Unit tests for IndexManager class.

Tests watch path management: add, remove, duplicate detection, reindex.
Uses temporary directories for full test isolation.

Refactored: 2026-01-05 to use temp directories and conftest.py cleanup
"""

import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import yaml

# Note: conftest.py's cleanup_mocked_modules fixture automatically ensures
# we have real modules, not mocks from other tests


class TestIndexManager(unittest.TestCase):
    """Tests for IndexManager watch path operations."""

    def setUp(self):
        # Import here to ensure conftest cleanup has run (validates module is real)
        from core.index_manager import IndexManager  # noqa: F401

        # Create a unique temp directory for this test to avoid cross-test pollution
        self.test_temp_dir = tempfile.mkdtemp(prefix="test_index_manager_")

        # Scope third-party module mocks to this test case only.
        self._sys_modules_patcher = patch.dict(
            sys.modules,
            {
                "faiss": MagicMock(),
                "sentence_transformers": MagicMock(),
                "llama_cpp": MagicMock(),
            },
            clear=False,
        )
        self._sys_modules_patcher.start()

        self.config_path = os.path.join(self.test_temp_dir, "test_config_manager.yaml")
        self.db_path = os.path.join(self.test_temp_dir, "test_meta_manager.sqlite")

        # Create dummy config
        with open(self.config_path, "w") as f:
            yaml.dump({"watch_paths": []}, f)

        # Patch paths
        self.patcher1 = patch("core.index_manager.CONFIG_PATH", self.config_path)
        self.patcher2 = patch("core.index_manager.DATABASE_PATH", self.db_path)
        self.patcher1.start()
        self.patcher2.start()

        # Mock dependencies
        self.mock_watcher = MagicMock()
        self.mock_embedder = MagicMock()

        # We need to patch SmartWatcherController and Embedder instantiation in __init__
        # or just overwrite them after init if we can't patch easily.
        # Since we are testing methods that use self.watcher_controller, overwriting is fine.

        with (
            patch("core.index_manager.SmartWatcherController"),
            patch("core.index_manager.Embedder"),
        ):
            # Import inside patch context; use alias to avoid F811 warning
            from core.index_manager import IndexManager as IM

            self.manager = IM()
            self.manager.watcher_controller = self.mock_watcher
            self.manager.embedder = self.mock_embedder

    def tearDown(self):
        self.patcher1.stop()
        self.patcher2.stop()
        self._sys_modules_patcher.stop()
        # Clean up temp directory
        if os.path.exists(self.test_temp_dir):
            shutil.rmtree(self.test_temp_dir, ignore_errors=True)

    def test_add_watch_path(self):
        # Test adding a valid path
        # Create a dummy directory for testing within our temp dir
        test_dir = os.path.join(self.test_temp_dir, "watch_dir")
        os.makedirs(test_dir, exist_ok=True)

        try:
            # Use sync mode for predictable testing
            result = self.manager.add_watch_path(test_dir, async_mode=False)
            # Handle both 2-tuple (legacy) and 3-tuple (new) returns
            if len(result) == 3:
                success, msg, job_id = result
            else:
                success, msg = result
            self.assertTrue(success, f"Failed to add path: {msg}")
            self.assertIn("added", msg.lower())

            # Verify config updated
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
                # Normalize path for comparison as add_watch_path normalizes it
                from core.path_utils import normalize_path

                norm_path = normalize_path(test_dir)
                self.assertIn(norm_path, config["watch_paths"])

        finally:
            if os.path.exists(test_dir):
                os.rmdir(test_dir)

    def test_add_duplicate_path(self):
        test_dir = os.path.join(self.test_temp_dir, "watch_dir")
        os.makedirs(test_dir, exist_ok=True)

        try:
            self.manager.add_watch_path(test_dir, async_mode=False)
            result = self.manager.add_watch_path(test_dir, async_mode=False)
            # Handle both 2-tuple (legacy) and 3-tuple (new) returns
            if len(result) == 3:
                success, msg, job_id = result
            else:
                success, msg = result
            self.assertFalse(success)
            self.assertIn("already being watched", msg)
        finally:
            if os.path.exists(test_dir):
                os.rmdir(test_dir)

    def test_remove_watch_path(self):
        test_dir = os.path.join(self.test_temp_dir, "watch_dir")
        os.makedirs(test_dir, exist_ok=True)

        try:
            self.manager.add_watch_path(test_dir, async_mode=False)

            # Reset mock to clear any calls from add_watch_path
            self.mock_watcher.reset_mock()

            result = self.manager.remove_watch_path(test_dir, async_mode=False)
            # Handle both 2-tuple (legacy) and 3-tuple (new) returns
            if len(result) == 3:
                success, msg, job_id = result
            else:
                success, msg = result
            self.assertTrue(success, f"Failed to remove path: {msg}")
            self.assertIn("removed", msg.lower())

            # Verify config updated
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
                from core.path_utils import normalize_path

                norm_path = normalize_path(test_dir)
                self.assertNotIn(norm_path, config["watch_paths"])

        finally:
            if os.path.exists(test_dir):
                os.rmdir(test_dir)

    def test_trigger_reindex(self):
        result = self.manager.trigger_reindex()
        # Handle tuple return
        self.assertIsInstance(result, tuple, f"Expected tuple, got {type(result)}")
        self.assertEqual(len(result), 2, f"Expected 2-tuple, got {len(result)}-tuple")
        success, msg = result
        self.assertTrue(success)
        self.mock_watcher.stop_watcher.assert_called_once()
        self.mock_watcher.start_watcher.assert_called_once()


if __name__ == "__main__":
    unittest.main()
