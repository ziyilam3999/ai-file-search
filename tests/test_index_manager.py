import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import yaml

from core.index_manager import IndexManager


class TestIndexManager(unittest.TestCase):
    def setUp(self):
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

        self.config_path = "tests/test_config_manager.yaml"
        self.db_path = "tests/test_meta_manager.sqlite"

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
            self.manager = IndexManager()
            self.manager.watcher_controller = self.mock_watcher
            self.manager.embedder = self.mock_embedder

    def tearDown(self):
        self.patcher1.stop()
        self.patcher2.stop()
        self._sys_modules_patcher.stop()
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

    def test_add_watch_path(self):
        # Test adding a valid path
        # Create a dummy directory for testing
        test_dir = os.path.join(os.getcwd(), "tests", "dummy_watch_dir")
        os.makedirs(test_dir, exist_ok=True)

        try:
            success, msg = self.manager.add_watch_path(test_dir)
            self.assertTrue(success, f"Failed to add path: {msg}")
            self.assertIn("added successfully", msg)

            # Verify config updated
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
                # Normalize path for comparison as add_watch_path normalizes it
                from core.path_utils import normalize_path

                norm_path = normalize_path(test_dir)
                self.assertIn(norm_path, config["watch_paths"])

            # Verify watcher restarted
            self.mock_watcher.restart_watcher.assert_called_once()
        finally:
            if os.path.exists(test_dir):
                os.rmdir(test_dir)

    def test_add_duplicate_path(self):
        test_dir = os.path.join(os.getcwd(), "tests", "dummy_watch_dir")
        os.makedirs(test_dir, exist_ok=True)

        try:
            self.manager.add_watch_path(test_dir)
            success, msg = self.manager.add_watch_path(test_dir)
            self.assertFalse(success)
            self.assertIn("already being watched", msg)
        finally:
            if os.path.exists(test_dir):
                os.rmdir(test_dir)

    def test_remove_watch_path(self):
        test_dir = os.path.join(os.getcwd(), "tests", "dummy_watch_dir")
        os.makedirs(test_dir, exist_ok=True)

        try:
            self.manager.add_watch_path(test_dir)

            # Reset mock to clear the restart call from add_watch_path
            self.mock_watcher.reset_mock()

            success, msg = self.manager.remove_watch_path(test_dir)
            self.assertTrue(success, f"Failed to remove path: {msg}")
            self.assertIn("removed successfully", msg)

            # Verify config updated
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
                from core.path_utils import normalize_path

                norm_path = normalize_path(test_dir)
                self.assertNotIn(norm_path, config["watch_paths"])

            # Verify watcher restarted
            self.mock_watcher.restart_watcher.assert_called_once()
        finally:
            if os.path.exists(test_dir):
                os.rmdir(test_dir)

    def test_trigger_reindex(self):
        success, msg = self.manager.trigger_reindex()
        self.assertTrue(success)
        self.mock_watcher.stop_watcher.assert_called_once()
        self.mock_watcher.start_watcher.assert_called_once()


if __name__ == "__main__":
    unittest.main()
