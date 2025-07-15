"""🧪 test_ui.py
Purpose: Smoke tests for Streamlit UI functionality
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))


def test_ui_imports():
    """Test that UI module can be imported without errors"""
    try:
        from ui.app import format_citations, load_welcome_text, main

        assert callable(main)
        assert callable(load_welcome_text)
        assert callable(format_citations)
    except ImportError as e:
        pytest.fail(f"Failed to import UI components: {e}")


def test_welcome_text_loading():
    """Test that welcome text can be loaded"""
    from ui.app import load_welcome_text

    welcome = load_welcome_text()
    assert isinstance(welcome, str)
    assert len(welcome) > 0
    assert "AI File Search" in welcome


def test_citation_formatting():
    """Test citation formatting function"""
    from ui.app import format_citations

    # Test empty citations
    result = format_citations([])
    assert "No citations available" in result

    # Test with sample citations
    citations = [
        {
            "id": 1,
            "file": "test.txt",
            "page": 1,
            "chunk": "Sample text chunk",
            "score": 0.85,
        }
    ]

    result = format_citations(citations)
    assert "[1]" in result
    assert "test.txt" in result
    assert "page 1" in result
    assert "Sample text chunk" in result


def test_streamlit_availability():
    """Test that Streamlit is available"""
    try:
        import streamlit as st

        # Basic Streamlit functionality test
        assert hasattr(st, "title")
        assert hasattr(st, "button")
        assert hasattr(st, "text_input")
    except ImportError:
        pytest.fail("Streamlit is not installed or available")


def test_core_integration():
    """Test that UI can import core functionality"""
    try:
        from core.ask import answer_question

        assert callable(answer_question)
    except ImportError as e:
        pytest.fail(f"Failed to import core.ask: {e}")
