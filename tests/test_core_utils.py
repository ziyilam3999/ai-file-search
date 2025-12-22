"""Tests for core/utils.py"""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.utils import format_citations


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
