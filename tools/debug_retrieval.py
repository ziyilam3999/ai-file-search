from core.embedding import Embedder
from core.path_utils import normalize_path


def debug_search():
    embedder = Embedder()
    query = "what is the year for the tenancy agreement"

    print(f"Query: {query}")
    print("-" * 50)

    # Search with k=10
    results = embedder.query(query, k=10)

    for i, result in enumerate(results):
        chunk_text, file_path, chunk_id, doc_chunk_id, score = result
        print(f"Result {i+1}:")
        print(f"  File: {file_path}")
        print(f"  Score: {score:.4f}")
        print(f"  Text: {chunk_text[:100]}...")
        print("-" * 50)


if __name__ == "__main__":
    debug_search()
