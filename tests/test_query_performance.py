# First, let's create a performance test
# tests/test_query_performance.py
import sys
import pathlib
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from core.embedding import Embedder


def test_query_performance():
    """Test that query() completes within 200ms"""

    # Build index once (if not exists)
    embedder = Embedder()
    if not pathlib.Path("index.faiss").exists():
        embedder.build_index(pathlib.Path("extracts"))

    # Test multiple queries to ensure consistent performance
    queries = [
        "Who is Ebenezer Scrooge?",
        "What happens to Alice in Wonderland?",
        "Describe the secret garden",
        "Who is Peter Pan?",
        "What is Pooh's favorite food?",
    ]

    # Warm up (first query loads model)
    embedder.query(queries[0], k=3)

    # Test actual performance
    total_time = 0
    for query in queries:
        start_time = time.time()
        results = embedder.query(query, k=3)
        elapsed_time = time.time() - start_time

        print(f"Query: '{query}' took {elapsed_time*1000:.1f}ms")
        assert results, f"No results for query: {query}"
        assert (
            elapsed_time < 0.2
        ), f"Query took {elapsed_time*1000:.1f}ms, should be < 200ms"

        total_time += elapsed_time

    avg_time = total_time / len(queries)
    print(f"Average query time: {avg_time*1000:.1f}ms")
    assert avg_time < 0.2, f"Average query time {avg_time*1000:.1f}ms > 200ms"


def test_query_performance_requirement():
    """Formal test that query() completes within 200ms"""
    embedder = Embedder()

    # Ensure index exists
    if not pathlib.Path("index.faiss").exists():
        embedder.build_index(pathlib.Path("extracts"))

    # Warm up the system
    embedder.query("test query", k=3)

    # Test the requirement
    start_time = time.time()
    results = embedder.query("Who is Ebenezer Scrooge?", k=5)
    elapsed_time = time.time() - start_time

    print(f"Query completed in {elapsed_time*1000:.1f}ms")
    assert elapsed_time < 0.2, f"Query took {elapsed_time*1000:.1f}ms > 200ms"
    assert len(results) > 0, "Query returned no results"


if __name__ == "__main__":
    test_query_performance()
    test_query_performance_requirement()
