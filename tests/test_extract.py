"""Tests Extractor against 20 sample files."""

import pathlib
import sys

import pytest

from core.extract import Extractor

# Add the project root to the path
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))


@pytest.mark.parametrize(
    "doc_name",
    [
        "A Christmas Carol in Prose; Being a Ghost Story of Christmas.pdf",
        "Alice's Adventures in Wonderland.pdf",
        "Anne of Green Gables.pdf",
        "Baseball ABC.pdf",
        "Black Beauty.pdf",
        "Frankenstein; Or, The Modern Prometheus.pdf",
        "Gulliver's Travels.pdf",
        "Heidi.pdf",
        "Little Women.pdf",
        "Peter Pan.pdf",
        "Pride and Prejudice.pdf",
        "Rose in Bloom.pdf",
        "The Adventures of Tom Sawyer.pdf",
        "The Good-Naughty Book.pdf",
        "The Night Before Christmas.pdf",
        "The Secret Garden.pdf",
        "The Wind in the Willows.pdf",
        "The Wonderful Wizard of Oz.pdf",
        "Through the Looking-Glass.pdf",
        "Treasure Island.pdf",
    ],
)
def test_extractor_handles_sample_documents(doc_name):
    """Test that Extractor can handle each sample document."""
    extractor = Extractor()
    doc_path = pathlib.Path("samples") / doc_name

    if not doc_path.exists():
        pytest.skip(f"Sample file {doc_name} not found")

    # Extract text
    text = extractor.extract(doc_path)

    # Basic validation
    assert text is not None, f"Failed to extract text from {doc_name}"
    assert len(text.strip()) > 0, f"Empty text extracted from {doc_name}"
    assert len(text) > 100, f"Text too short from {doc_name}"

    # Check for reasonable content
    assert any(char.isalpha() for char in text), f"No alphabetic content in {doc_name}"
