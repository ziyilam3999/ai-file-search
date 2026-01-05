"""Tests for core/utils.py"""

import os
import platform
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.utils import format_citations, open_local_file


def test_open_local_file_windows():
    """Test opening file on Windows."""
    with (
        patch("platform.system", return_value="Windows"),
        patch("os.startfile") as mock_startfile,
        patch("pathlib.Path.exists", return_value=True),
    ):

        open_local_file("test.txt")
        # On Windows, it calls os.startfile with the resolved path
        # We check if it was called. The exact path argument depends on resolution,
        # so we just check it was called.
        assert mock_startfile.called


def test_open_local_file_macos():
    """Test opening file on macOS."""
    with (
        patch("platform.system", return_value="Darwin"),
        patch("subprocess.call") as mock_call,
        patch("pathlib.Path.exists", return_value=True),
    ):

        open_local_file("test.txt")
        assert mock_call.called
        args = mock_call.call_args[0][0]
        assert args[0] == "open"


def test_open_local_file_linux():
    """Test opening file on Linux."""
    with (
        patch("platform.system", return_value="Linux"),
        patch("subprocess.call") as mock_call,
        patch("pathlib.Path.exists", return_value=True),
    ):

        open_local_file("test.txt")
        assert mock_call.called
        args = mock_call.call_args[0][0]
        assert args[0] == "xdg-open"


def test_open_local_file_not_found():
    """Test opening non-existent file."""
    with (
        patch("pathlib.Path.exists", return_value=False),
        patch("loguru.logger.error") as mock_log,
    ):

        open_local_file("nonexistent.txt")
        mock_log.assert_called()


def test_format_citations_empty():
    """Test formatting with empty citations list."""
    assert format_citations([]) == "No citations available."
    assert format_citations(None) == "No citations available."


def test_format_citations_basic():
    """Test formatting with a single basic citation."""
    citations = [
        {
            "file": "test_doc.txt",
            "chunk": "This is a test sentence.",
            "page": 1,
            "score": 0.9,
        }
    ]
    result = format_citations(citations)
    assert "test_doc.txt" in result
    assert "This is a test sentence." in result


def test_format_citations_path_normalization():
    """Test that backslashes in paths are converted to forward slashes."""
    citations = [
        {
            "file": "folder\\subfolder\\doc.pdf",
            "chunk": "Content",
        }
    ]
    result = format_citations(citations)
    assert "folder/subfolder/doc.pdf" in result


def test_format_citations_plain_text():
    """Test formatting with as_html=False."""
    citations = [
        {
            "file": "test_doc.txt",
            "chunk": "This is a test sentence.",
        }
    ]
    result = format_citations(citations, as_html=False)
    assert "test_doc.txt" in result
    assert "This is a test sentence." in result
    assert "<div" not in result
    assert "<button" not in result
    assert "SOURCE 1:" in result


def test_format_citations_html_structure():
    """Test that HTML output contains expected structure."""
    citations = [
        {
            "file": "test_doc.txt",
            "chunk": "Content",
        }
    ]
    result = format_citations(citations, as_html=True)
    assert "<div" in result
    assert "<button" in result
    assert "open-file-btn" in result
    assert 'data-file-path="test_doc.txt"' in result


def test_format_citations_bullet_points():
    """Test that content with multiple sentences is formatted as bullet points."""
    content = "First point. Second point. Third point."
    citations = [
        {
            "file": "notes.txt",
            "chunk": content,
        }
    ]
    result = format_citations(citations)

    # Check for bullet points
    assert "• First point." in result
    assert "• Second point." in result
    assert "• Third point." in result


def test_format_citations_dash_splitting():
    """Test that content with dashes is formatted as bullet points."""
    content = "Item 1 - Item 2 - Item 3"
    citations = [
        {
            "file": "list.txt",
            "chunk": content,
        }
    ]
    result = format_citations(citations)

    assert "• Item 1" in result
    assert "• Item 2" in result
    assert "• Item 3" in result


class TestOpenLocalFileConfluence:
    """Tests for Confluence URL handling in open_local_file (T3)."""

    def test_confluence_path_opens_browser(self):
        """Test that confluence:// paths open in browser."""
        with patch("core.confluence.get_confluence_url_for_path") as mock_get_url:
            mock_get_url.return_value = "https://test.atlassian.net/page"

            with patch("webbrowser.open") as mock_browser:
                from core.utils import open_local_file

                open_local_file("confluence://SPACE/Test Page")
                mock_browser.assert_called_once_with("https://test.atlassian.net/page")

    def test_confluence_path_does_not_check_file_exists(self):
        """Test that confluence:// paths don't trigger file existence check."""
        with (
            patch("webbrowser.open"),  # noqa: F841 - patch needed but not asserted
            patch("pathlib.Path.exists") as mock_exists,
            patch("pathlib.Path.resolve"),  # noqa: F841 - patch needed but not asserted
        ):
            import core.confluence

            core.confluence.get_confluence_url_for_path = MagicMock(
                return_value="https://test.atlassian.net/page"
            )

            open_local_file("confluence://SPACE/Test Page")

            # Path.exists should NOT be called for confluence:// paths
            mock_exists.assert_not_called()

    def test_confluence_path_returns_early(self):
        """Test that confluence:// paths return before local file handling."""
        with (
            patch("webbrowser.open"),  # noqa: F841 - patch needed but not asserted
            patch("os.startfile") as mock_startfile,
            patch("platform.system", return_value="Windows"),
        ):
            import core.confluence

            core.confluence.get_confluence_url_for_path = MagicMock(
                return_value="https://test.atlassian.net/page"
            )

            open_local_file("confluence://SPACE/Test Page")

            # os.startfile should NOT be called for confluence:// paths
            mock_startfile.assert_not_called()

    def test_confluence_path_logs_error_when_url_fails(self):
        """Test that error is logged when URL resolution fails."""
        with (
            patch("webbrowser.open") as mock_browser,
            patch("loguru.logger.error") as mock_log,
        ):
            import core.confluence

            core.confluence.get_confluence_url_for_path = MagicMock(return_value=None)

            open_local_file("confluence://SPACE/Test Page")

            mock_browser.assert_not_called()
            mock_log.assert_called()
