import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from pathlib import Path

import pytest

from core.embedding import Embedder

pytestmark = (
    pytest.mark.slow
)  # Mark all tests in this module as slow (loads embedding model)


@pytest.fixture(scope="module", autouse=True)
def setup_index():
    """Build the index just once before running queries in this module."""
    Embedder().build_index(pathlib.Path("extracts"))


def test_build_index_performance():
    """Test that build_index completes within 60 seconds"""
    extracts_path = Path("extracts")

    start_time = time.time()
    embedder = Embedder()
    embedder.build_index(extracts_path)
    elapsed_time = time.time() - start_time

    print(f"build_index() took {elapsed_time:.2f} seconds")
    assert (
        elapsed_time < 600
    ), f"build_index() took {elapsed_time:.2f}s, requirement is < 600s"

    # Verify the index was actually built
    assert Path("index.faiss").exists(), "FAISS index file not created"
    assert Path("meta.sqlite").exists(), "SQLite database not created"


@pytest.mark.parametrize(
    "q",
    [
        "Who is Ebenezer Scrooge?",
        "Summarize the main lesson in Black Beauty.",
        "Who are the main characters in Alice’s Adventures in Wonderland?",
        "What happens to Peter Pan in Neverland?",
        "Describe the garden in The Secret Garden.",
        "What is the moral of Treasure Island?",
        "What is Pooh’s favorite food?",
        "Describe the events of Christmas Eve in The Night Before Christmas.",
        "What makes the story ‘The Good-Naughty Book’ unique?",
        "Who is the main villain in The Wonderful Wizard of Oz?",
        "List three sports from Baseball ABC.",
        "Summarize the story of Rose in Bloom.",
    ],
)
def test_query_returns_result(q):
    hits = Embedder().query(q, k=3)
    # Print the result for manual inspection (optional)
    print(f"Q: {q}\nA: {hits[0] if hits else 'No answer found.'}\n")
    assert hits, f"No results returned for: {q}"
