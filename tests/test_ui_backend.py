import json
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock dependencies
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
        self.mock_manager.add_watch_path.return_value = (True, "Success")
        response = self.app.post(
            "/api/settings/watch-paths", json={"path": "/new/path"}
        )
        self.assertEqual(response.status_code, 200)
        self.mock_manager.add_watch_path.assert_called_with("/new/path")

    def test_add_watch_path_error(self):
        self.mock_manager.add_watch_path.return_value = (False, "Error message")
        response = self.app.post(
            "/api/settings/watch-paths", json={"path": "/bad/path"}
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["error"], "Error message")

    def test_remove_watch_path(self):
        self.mock_manager.remove_watch_path.return_value = (True, "Removed")
        response = self.app.delete(
            "/api/settings/watch-paths", json={"path": "/path/to/remove"}
        )
        self.assertEqual(response.status_code, 200)
        self.mock_manager.remove_watch_path.assert_called_with("/path/to/remove")

    def test_trigger_reindex(self):
        self.mock_manager.trigger_reindex.return_value = (True, "Reindexing")
        response = self.app.post("/api/settings/reindex")
        self.assertEqual(response.status_code, 200)
        self.mock_manager.trigger_reindex.assert_called_once()


if __name__ == "__main__":
    unittest.main()
