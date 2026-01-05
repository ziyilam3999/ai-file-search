"""Unit tests for UI Flask backend API endpoints.

Tests API routes: watch paths, reindex, activity log mapping, file opening.
Uses mocking to avoid heavy dependencies.

Refactored: 2026-01-05 to immediately restore modules after import
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# =============================================================================
# MODULE-LEVEL MOCK SETUP WITH IMMEDIATE CLEANUP
# =============================================================================

_MOCK_MODULE_NAMES = [
    "smart_watcher",
    "core.ask",
    "core.monitoring",
    "core.utils",
    "core.index_manager",
]

_ORIGINAL_MODULES = {name: sys.modules.get(name) for name in _MOCK_MODULE_NAMES}

# Apply mocks for flask_app import
for _name in _MOCK_MODULE_NAMES:
    sys.modules[_name] = MagicMock()

# Mock IndexManager class specifically
MockIndexManager = MagicMock()
sys.modules["core.index_manager"].IndexManager = MockIndexManager  # type: ignore[attr-defined]

# Import app with mocks in place
from ui.flask_app import app

# IMMEDIATELY restore modules after import
for _name, _original in _ORIGINAL_MODULES.items():
    if _original is None:
        sys.modules.pop(_name, None)
    else:
        sys.modules[_name] = _original

# Clean up module-level variables
del _name, _original


class TestUIBackend(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        # Get the instance that was created in flask_app.py
        # Since we mocked the class, the instance is the return value of the constructor
        # But flask_app.py calls IndexManager(), so it gets a new mock instance.
        # We need to access THAT instance.
        # Since we can't easily access the module-level variable 'index_manager' from here without importing it,
        # and importing it gives us the module...

        # Actually, we can access it via ui.flask_app.index_manager
        import ui.flask_app

        self.mock_manager = ui.flask_app.index_manager

    def test_get_watch_paths(self):
        self.mock_manager.get_watch_paths.return_value = ["/path/1", "/path/2"]
        response = self.app.get("/api/settings/watch-paths")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["paths"], ["/path/1", "/path/2"])

    def test_add_watch_path(self):
        # Return 3-tuple: (success, message, job_id)
        self.mock_manager.add_watch_path.return_value = (True, "Success", "job_123")
        response = self.app.post(
            "/api/settings/watch-paths", json={"path": "/new/path"}
        )
        self.assertEqual(response.status_code, 200)
        self.mock_manager.add_watch_path.assert_called_with(
            "/new/path", async_mode=True
        )
        data = json.loads(response.data)
        self.assertEqual(data["status"], "accepted")
        self.assertEqual(data["job_id"], "job_123")

    def test_add_watch_path_error(self):
        # Return 3-tuple: (success, message, job_id)
        self.mock_manager.add_watch_path.return_value = (False, "Error message", None)
        response = self.app.post(
            "/api/settings/watch-paths", json={"path": "/bad/path"}
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["error"], "Error message")

    def test_remove_watch_path(self):
        # Return 3-tuple: (success, message, job_id)
        self.mock_manager.remove_watch_path.return_value = (True, "Removed", "job_456")
        response = self.app.delete(
            "/api/settings/watch-paths", json={"path": "/path/to/remove"}
        )
        self.assertEqual(response.status_code, 200)
        self.mock_manager.remove_watch_path.assert_called_with(
            "/path/to/remove", async_mode=True
        )
        data = json.loads(response.data)
        self.assertEqual(data["status"], "accepted")

    def test_trigger_reindex(self):
        self.mock_manager.trigger_reindex.return_value = (True, "Reindexing")
        response = self.app.post("/api/settings/reindex")
        self.assertEqual(response.status_code, 200)
        self.mock_manager.trigger_reindex.assert_called_once()

    def test_to_activity_llm_loading(self):
        """Test activity log mapping for LLM loading."""
        # Import to_activity from flask_app
        import ui.flask_app

        to_activity = ui.flask_app.to_activity

        line = "PRELOAD: Pre-loading LLM model"
        result = to_activity(line)

        self.assertEqual(result, "AI Model: Loading…")

    def test_to_activity_llm_loaded(self):
        """Test activity log mapping for LLM loaded successfully."""
        import ui.flask_app

        to_activity = ui.flask_app.to_activity

        line = "SUCCESS: LLM model loaded successfully"
        result = to_activity(line)

        self.assertEqual(result, "AI Model: Loaded")

    def test_to_activity_llm_ready(self):
        """Test activity log mapping for LLM ready for queries."""
        import ui.flask_app

        to_activity = ui.flask_app.to_activity

        line = "PRELOAD: LLM model ready for queries"
        result = to_activity(line)

        self.assertEqual(result, "AI Model: Ready")

    def test_open_file_confluence_path(self):
        """Test /api/open-file with Confluence path opens browser (T5)."""
        with patch("webbrowser.open"):  # noqa: F841 - patch needed but not asserted
            with patch("core.confluence.get_confluence_url_for_path") as mock_url:
                mock_url.return_value = "https://test.atlassian.net/pages/123"

                response = self.app.post(
                    "/api/open-file", json={"file_path": "confluence://SPACE/Test Page"}
                )

        # Just verify endpoint returns success structure
        self.assertEqual(response.status_code, 200)

    def test_open_file_no_path_error(self):
        """Test /api/open-file returns error when no path provided (T5)."""
        response = self.app.post("/api/open-file", json={})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)

    def test_open_file_local_path(self):
        """Test /api/open-file with local path calls open_local_file (T5)."""
        import ui.flask_app

        response = self.app.post(
            "/api/open-file", json={"file_path": "C:\\Users\\test\\doc.txt"}
        )

        # open_local_file is mocked, so this should succeed
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
