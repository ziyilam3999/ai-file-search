import os
import platform
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from core.path_utils import (
    BLOCKED_PATHS_UNIX,
    BLOCKED_PATHS_WINDOWS,
    estimate_folder_stats,
    get_supported_files,
    is_system_path,
    normalize_path,
    validate_watch_path,
)


class TestPathUtils(unittest.TestCase):

    def test_normalize_path(self):
        # Test basic normalization
        path = "folder/subfolder"
        norm = normalize_path(path)
        self.assertTrue(os.path.isabs(norm))
        self.assertTrue(norm.endswith(os.path.join("folder", "subfolder")))

        # Test user expansion (mocking expanduser)
        with patch("os.path.expanduser") as mock_expand:
            mock_expand.return_value = "/home/user/docs"
            norm = normalize_path("~/docs")
            self.assertEqual(norm, os.path.normpath(os.path.abspath("/home/user/docs")))

    def test_is_system_path_windows(self):
        with patch("platform.system", return_value="Windows"):
            # Blocked paths
            self.assertTrue(is_system_path("C:\\Windows"))
            self.assertTrue(is_system_path("C:\\Windows\\System32"))
            self.assertTrue(is_system_path("c:\\windows\\system32"))  # Case insensitive
            self.assertTrue(is_system_path("C:\\"))

            # Allowed paths
            self.assertFalse(is_system_path("C:\\Users\\User\\Documents"))
            self.assertFalse(is_system_path("D:\\Data"))

            # Partial match edge case (should be allowed)
            self.assertFalse(is_system_path("C:\\WindowsProject"))

    def test_is_system_path_unix(self):
        with patch("platform.system", return_value="Linux"):
            # We must mock normalize_path because os.path.abspath on Windows
            # will convert "/" to "C:\" which breaks the Unix logic test
            with patch("core.path_utils.normalize_path", side_effect=lambda x: x):
                # Blocked paths
                self.assertTrue(is_system_path("/"))
                self.assertTrue(is_system_path("/usr"))
                self.assertTrue(is_system_path("/usr/bin"))

                # Allowed paths
                self.assertFalse(is_system_path("/home/user"))
                self.assertFalse(is_system_path("/opt/myapp"))

    def test_validate_watch_path(self):
        # Mock existence and is_dir
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_dir", return_value=True),
            patch("os.access", return_value=True),
            patch("core.path_utils.is_system_path", return_value=False),
        ):

            valid, msg = validate_watch_path("/some/path")
            self.assertTrue(valid)
            self.assertEqual(msg, "")

        # Test non-existent
        with patch("pathlib.Path.exists", return_value=False):
            valid, msg = validate_watch_path("/bad/path")
            self.assertFalse(valid)
            self.assertIn("does not exist", msg)

        # Test not a directory
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_dir", return_value=False),
        ):
            valid, msg = validate_watch_path("/some/file.txt")
            self.assertFalse(valid)
            self.assertIn("not a directory", msg)

        # Test system path
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_dir", return_value=True),
            patch("core.path_utils.is_system_path", return_value=True),
        ):
            valid, msg = validate_watch_path("C:\\Windows")
            self.assertFalse(valid)
            self.assertIn("security reasons", msg)

    def test_get_supported_files(self):
        # Create a temporary directory structure
        import shutil
        import tempfile

        temp_dir = tempfile.mkdtemp()
        try:
            # Create some files
            Path(temp_dir, "doc1.txt").touch()
            Path(temp_dir, "doc2.pdf").touch()
            Path(temp_dir, "image.png").touch()  # Should be ignored
            os.makedirs(os.path.join(temp_dir, "sub"))
            Path(temp_dir, "sub", "doc3.md").touch()

            files = get_supported_files(temp_dir)
            filenames = [f.name for f in files]

            self.assertIn("doc1.txt", filenames)
            self.assertIn("doc2.pdf", filenames)
            self.assertIn("doc3.md", filenames)
            self.assertNotIn("image.png", filenames)

        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
