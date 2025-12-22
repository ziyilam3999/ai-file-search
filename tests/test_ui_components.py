"""Tests for ui/components.py"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock streamlit before importing ui.components
sys.modules["streamlit"] = MagicMock()
import streamlit as st

from ui.components import (
    format_citations,
    format_citations_streaming,
    load_welcome_text,
    render_interactive_citations,
)


def test_load_welcome_text():
    """Test loading welcome text."""
    # Mock file opening
    with patch("builtins.open", new_callable=MagicMock) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = "# Welcome"
        text = load_welcome_text()
        assert text == "# Welcome"


def test_format_citations():
    """Test formatting citations."""
    citations = [
        {"id": 1, "file": "test.txt", "page": 1, "chunk": "Content", "score": 0.9}
    ]
    result = format_citations(citations)
    assert "SOURCE 1" in result
    assert "test.txt" in result
    assert "Content" in result


def test_format_citations_streaming():
    """Test streaming citation formatting."""
    citations = [{"id": 1, "file": "test.txt", "page": 1, "chunk": "Content"}]
    found = {1}
    new = {1}

    result = format_citations_streaming(citations, found, new)
    assert "test.txt" in result
    assert "Content" in result
    assert "animation: pulse" in result  # Check for new citation highlighting


def test_render_interactive_citations():
    """Test rendering interactive citations."""
    citations = [
        {"id": 1, "file": "test.txt", "page": 1, "chunk": "Content", "score": 0.9}
    ]

    # Reset mocks
    st.markdown.reset_mock()
    st.columns.reset_mock()
    st.button.reset_mock()

    # Mock columns to return two mocks
    col1 = MagicMock()
    col2 = MagicMock()
    st.columns.return_value = [col1, col2]

    # Mock button to return True (clicked)
    st.button.return_value = True

    with patch("ui.components.open_local_file") as mock_open:
        render_interactive_citations(citations)

        # Check if markdown was called (for header and card)
        assert st.markdown.called

        # Check if columns were created
        st.columns.assert_called_with([5, 1])

        # Check if button was created
        assert st.button.called

        # Check if open_local_file was called (since button returned True)
        mock_open.assert_called_with("test.txt")
