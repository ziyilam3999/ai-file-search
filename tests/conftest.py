"""
Shared pytest fixtures for test isolation and mock management.

This conftest.py provides:
1. Automatic cleanup of mocked modules before each test
2. Isolated IndexManager fixture with temp config/db
3. Shared test utilities

Created: 2026-01-05
Purpose: Eliminate test pollution from module-level mocking
"""

import importlib
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

# =============================================================================
# MOCK MANAGEMENT
# =============================================================================

# Modules that may be mocked by some tests and need cleanup
POTENTIALLY_MOCKED_MODULES = [
    "faiss",
    "llama_cpp",
    "sentence_transformers",
    "core.embedding",
    "core.ask",
    "core.llm",
    "core.index_manager",
    "core.monitoring",
    "core.utils",
    "smart_watcher",
    "streamlit",
]


def _is_mocked(module_name: str) -> bool:
    """Check if a module in sys.modules is a MagicMock."""
    module = sys.modules.get(module_name)
    return module is not None and isinstance(module, MagicMock)


def _restore_real_module(module_name: str) -> None:
    """Remove mocked module from sys.modules to allow real import."""
    if _is_mocked(module_name):
        del sys.modules[module_name]
        # Also remove any submodules
        for key in list(sys.modules.keys()):
            if key.startswith(f"{module_name}.") and _is_mocked(key):
                del sys.modules[key]


@pytest.fixture(autouse=True)
def cleanup_mocked_modules():
    """
    Automatically clean up mocked modules before and after each test.

    This fixture runs for EVERY test (autouse=True) and ensures that
    mocked modules from previous tests don't pollute subsequent tests.
    """
    # Before test: clean up any leftover mocks
    for module_name in POTENTIALLY_MOCKED_MODULES:
        _restore_real_module(module_name)

    yield  # Test runs here

    # After test: clean up again for safety
    for module_name in POTENTIALLY_MOCKED_MODULES:
        _restore_real_module(module_name)


# =============================================================================
# INDEX MANAGER FIXTURES
# =============================================================================


@pytest.fixture
def temp_config_dir(tmp_path):
    """
    Provides a temporary directory with empty config and database paths.

    Returns:
        dict with keys: 'config_path', 'db_path', 'dir'
    """
    config_path = tmp_path / "test_config.yaml"
    db_path = tmp_path / "test_meta.sqlite"

    # Create empty config
    config_path.write_text(yaml.dump({"watch_paths": []}))

    return {
        "config_path": str(config_path),
        "db_path": str(db_path),
        "dir": tmp_path,
    }


@pytest.fixture
def isolated_index_manager(temp_config_dir):
    """
    Provides a fully isolated IndexManager instance.

    - Uses temporary config and database files
    - Mocks SmartWatcherController and Embedder to avoid heavy dependencies
    - Cleans up after test completes

    Usage:
        def test_something(isolated_index_manager):
            manager = isolated_index_manager
            result = manager.add_watch_path("/some/path")
    """
    config_path = temp_config_dir["config_path"]
    db_path = temp_config_dir["db_path"]

    # Ensure we have the real module
    _restore_real_module("core.index_manager")

    # Patch paths and dependencies
    with patch("core.index_manager.CONFIG_PATH", config_path):
        with patch("core.index_manager.DATABASE_PATH", db_path):
            with patch("core.index_manager.SmartWatcherController"):
                with patch("core.index_manager.Embedder"):
                    # Force reimport to pick up patched values
                    if "core.index_manager" in sys.modules:
                        importlib.reload(sys.modules["core.index_manager"])

                    from core.index_manager import IndexManager

                    manager = IndexManager()
                    manager.watcher_controller = MagicMock()
                    manager.embedder = MagicMock()

                    yield manager


@pytest.fixture
def temp_watch_dir(tmp_path):
    """
    Provides a temporary directory suitable for watch path testing.

    The directory is created fresh for each test and cleaned up after.
    """
    watch_dir = tmp_path / "watch_dir"
    watch_dir.mkdir()
    return watch_dir


# =============================================================================
# CLI TESTING FIXTURES
# =============================================================================


@pytest.fixture
def mock_heavy_deps():
    """
    Context manager that mocks heavy dependencies for CLI testing.

    Use this instead of module-level mocking in test_cli.py.

    Usage:
        def test_cli_function(mock_heavy_deps):
            with mock_heavy_deps:
                from cli import some_function
                result = some_function()
    """
    mocks = {}
    original_modules = {}

    modules_to_mock = [
        "faiss",
        "llama_cpp",
        "sentence_transformers",
        "core.embedding",
        "core.ask",
        "core.llm",
        "core.index_manager",
        "smart_watcher",
    ]

    class MockContext:
        def __enter__(self):
            for name in modules_to_mock:
                original_modules[name] = sys.modules.get(name)
                if name not in sys.modules:
                    mocks[name] = MagicMock()
                    sys.modules[name] = mocks[name]
            return mocks

        def __exit__(self, *args):
            for name, original in original_modules.items():
                if original is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = original

    return MockContext()


# =============================================================================
# UI TESTING FIXTURES
# =============================================================================


@pytest.fixture
def flask_test_client():
    """
    Provides a Flask test client with mocked dependencies.

    Usage:
        def test_api_endpoint(flask_test_client):
            client = flask_test_client
            response = client.get('/api/status')
    """
    # Save original modules
    modules_to_mock = [
        "smart_watcher",
        "core.ask",
        "core.monitoring",
        "core.utils",
        "core.index_manager",
    ]

    original_modules = {name: sys.modules.get(name) for name in modules_to_mock}

    try:
        # Set up mocks
        for name in modules_to_mock:
            sys.modules[name] = MagicMock()

        # Mock IndexManager class
        mock_index_manager = MagicMock()
        sys.modules["core.index_manager"].IndexManager = mock_index_manager

        # Import app with mocks in place
        from ui.flask_app import app

        app.config["TESTING"] = True
        client = app.test_client()

        yield client

    finally:
        # Restore original modules
        for name, original in original_modules.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


# =============================================================================
# UTILITY FIXTURES
# =============================================================================


@pytest.fixture
def sample_yaml_config(tmp_path):
    """Provides a sample YAML config file path."""
    config = {
        "watch_paths": ["/path/one", "/path/two"],
        "settings": {"option": True},
    }
    path = tmp_path / "sample_config.yaml"
    path.write_text(yaml.dump(config))
    return path
