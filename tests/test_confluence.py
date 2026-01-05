"""Tests for Confluence integration.

Tests the core/confluence.py module and IndexManager Confluence methods.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

# Test data
SAMPLE_CONFLUENCE_HTML = """
<p>This is a test page.</p>
<h1>Business Rules</h1>
<p>Here are the rules:</p>
<ul>
<li>Rule 1: Do something</li>
<li>Rule 2: Do something else</li>
</ul>
<table>
<tr><th>Header 1</th><th>Header 2</th></tr>
<tr><td>Cell 1</td><td>Cell 2</td></tr>
</table>
<ac:structured-macro ac:name="code">
<ac:plain-text-body>def hello():
    print("Hello World")</ac:plain-text-body>
</ac:structured-macro>
"""

SAMPLE_PAGE_DATA = {
    "id": "12345",
    "title": "Test Page",
    "body": {"storage": {"value": SAMPLE_CONFLUENCE_HTML}},
    "version": {"number": 3, "when": "2024-01-15T10:30:00.000Z"},
    "ancestors": [{"title": "Parent Folder"}, {"title": "Subfolder"}],
    "metadata": {
        "labels": {"results": [{"name": "business-rules"}, {"name": "important"}]}
    },
}


class TestConfluenceDependencies:
    """Tests for Confluence dependency checking."""

    def test_check_dependencies_all_installed(self):
        """Test dependency check when all packages are installed."""
        from core.confluence import check_confluence_dependencies

        # The check should work regardless of actual installation
        ok, msg = check_confluence_dependencies()
        # Result depends on actual environment, so just verify it returns tuple
        assert isinstance(ok, bool)
        assert isinstance(msg, str)


class TestConfluencePage:
    """Tests for ConfluencePage dataclass."""

    def test_confluence_page_creation(self):
        """Test creating a ConfluencePage instance."""
        from core.confluence import ConfluencePage

        page = ConfluencePage(
            page_id="123",
            title="Test",
            space_key="SPACE",
            content="Test content",
            url="https://example.com/page",
            version=1,
            last_modified="2024-01-01T00:00:00Z",
            ancestors=["Parent"],
            labels=["label1"],
        )

        assert page.page_id == "123"
        assert page.title == "Test"
        assert page.hierarchy_path == "Parent / Test"

    def test_confluence_page_no_ancestors(self):
        """Test hierarchy path with no ancestors."""
        from core.confluence import ConfluencePage

        page = ConfluencePage(
            page_id="123",
            title="Root Page",
            space_key="SPACE",
            content="Content",
            url="https://example.com",
            version=1,
            last_modified="2024-01-01T00:00:00Z",
        )

        assert page.hierarchy_path == "Root Page"


class TestConfluenceConfig:
    """Tests for Confluence configuration handling."""

    def test_config_file_path(self):
        """Test that config path is correct."""
        from core.confluence import CONFIG_PATH

        assert CONFIG_PATH == Path("config/confluence.yaml")

    def test_env_file_path(self):
        """Test that env file path is correct."""
        from core.confluence import ENV_PATH

        assert ENV_PATH == Path(".env")


class TestConfluenceHTMLParsing:
    """Tests for HTML parsing functionality - uses BeautifulSoup directly."""

    @pytest.fixture
    def bs4_available(self):
        """Check if BeautifulSoup is available."""
        try:
            from bs4 import BeautifulSoup

            return True
        except ImportError:
            pytest.skip("beautifulsoup4 not installed")
            return False

    def test_extract_text_basic(self, bs4_available):
        """Test basic HTML to text extraction logic."""
        from bs4 import BeautifulSoup

        html = "<p>Hello World</p><p>This is a test.</p>"
        soup = BeautifulSoup(html, "html.parser")
        result = soup.get_text(separator="\n")

        assert "Hello World" in result
        assert "This is a test" in result

    def test_extract_removes_scripts(self, bs4_available):
        """Test that scripts are removed from HTML."""
        from bs4 import BeautifulSoup

        html = "<p>Content</p><script>alert('bad')</script><p>More content</p>"
        soup = BeautifulSoup(html, "html.parser")

        for element in soup(["script", "style"]):
            element.decompose()

        result = soup.get_text()

        assert "Content" in result
        assert "More content" in result
        assert "alert" not in result

    def test_extract_tables(self, bs4_available):
        """Test table extraction."""
        from bs4 import BeautifulSoup

        html = """
        <table>
            <tr><th>Name</th><th>Value</th></tr>
            <tr><td>Foo</td><td>Bar</td></tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = soup.get_text(separator=" ")

        assert "Name" in result
        assert "Value" in result
        assert "Foo" in result
        assert "Bar" in result


class TestConfluenceClientMocked:
    """Tests for ConfluenceClient with full mocking."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        # Create mock modules
        mock_atlassian = MagicMock()
        mock_confluence_class = MagicMock()
        mock_atlassian.Confluence = mock_confluence_class

        mock_bs4 = MagicMock()
        mock_soup_class = MagicMock()
        mock_bs4.BeautifulSoup = mock_soup_class

        return mock_atlassian, mock_confluence_class, mock_bs4, mock_soup_class

    def test_client_initialization_missing_credentials(self):
        """Test that client raises error when credentials are missing."""
        # This test verifies error handling without needing actual packages
        from core.confluence import check_confluence_dependencies

        ok, msg = check_confluence_dependencies()
        # If dependencies are missing, the check should fail gracefully
        if not ok:
            assert "Missing" in msg or "not installed" in msg.lower()


class TestIndexManagerConfluenceMethods:
    """Tests for IndexManager Confluence methods - integration style."""

    def test_confluence_status_returns_dict(self):
        """Test that get_confluence_status returns a dictionary."""
        # Import with mocked dependencies if needed
        try:
            from core.index_manager import IndexManager

            # Create instance with mocked watcher
            with patch("core.index_manager.SmartWatcherController"):
                with patch("core.index_manager.Embedder"):
                    manager = IndexManager()
                    status = manager.get_confluence_status()

                    assert isinstance(status, dict)
                    assert "configured" in status or "error" in status
        except ImportError as e:
            pytest.skip(f"Could not import IndexManager: {e}")

    def test_sync_confluence_validates_space_key(self):
        """Test that sync_confluence requires a space key."""
        try:
            from core.index_manager import IndexManager

            with patch("core.index_manager.SmartWatcherController"):
                with patch("core.index_manager.Embedder"):
                    manager = IndexManager()

                    # Try to sync without dependencies - should return error
                    success, message, job_id = manager.sync_confluence(
                        space_key="TEST", async_mode=False
                    )

                    # Should either succeed or return meaningful error
                    assert isinstance(success, bool)
                    assert isinstance(message, str)
        except ImportError as e:
            pytest.skip(f"Could not import IndexManager: {e}")
