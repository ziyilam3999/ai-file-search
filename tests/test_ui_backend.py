import json
import sys
import unittest
from unittest.mock import MagicMock, patch

_MOCK_MODULE_NAMES = [
    "smart_watcher",
    "core.ask",
    "core.monitoring",
    "core.utils",
    "core.index_manager",
]

_ORIGINAL_MODULES = {name: sys.modules.get(name) for name in _MOCK_MODULE_NAMES}

try:
    # Mock dependencies (only for importing ui.flask_app)
    sys.modules["smart_watcher"] = MagicMock()
    sys.modules["core.ask"] = MagicMock()
    sys.modules["core.monitoring"] = MagicMock()
    sys.modules["core.utils"] = MagicMock()
    sys.modules["core.index_manager"] = MagicMock()

    # Mock IndexManager class
    MockIndexManager = MagicMock()
    sys.modules["core.index_manager"].IndexManager = MockIndexManager  # type: ignore

    # We need to import app AFTER mocking
    # But ui.flask_app imports core.index_manager, so our mock in sys.modules should work
    from ui.flask_app import app
finally:
    # IMPORTANT: Restore sys.modules to avoid leaking mocks to other tests.
    for name, original in _ORIGINAL_MODULES.items():
        if original is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = original


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


if __name__ == "__main__":
    unittest.main()
