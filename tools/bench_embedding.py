import pathlib
import sys
import time
from pathlib import Path

import psutil

from core.embedding import Embedder
from core.extract import Extractor  # Import your Extractor

extracts_path = Path("extracts")
if not any(extracts_path.glob("**/*.txt")):
    print("No .txt files found in extracts/. Running extractor...")
    # Example: process all files in ai_search_docs/ and save to extracts/
    ai_search_docs = Path("ai_search_docs")
    extracts_path.mkdir(exist_ok=True)
    for file in ai_search_docs.glob("*"):
        text = Extractor().run(file)
        if text:
            out_path = extracts_path / (file.stem + ".txt")
            out_path.write_text(text, encoding="utf-8")
    # Check again after extraction
    if not any(extracts_path.glob("**/*.txt")):
        print("Extractor did not produce any .txt files. Exiting.")
        sys.exit(1)

idx = Embedder()
idx.build_index(str(extracts_path))
start = time.time()
results = idx.query("Who Alice found in wonderland?")
for i, (chunk_text, file_path, chunk_id, doc_chunk_id, score) in enumerate(results):
    print(f"Result {i+1}:")
    print(f"File: {file_path}")
    print(f"Score: {score:.3f}")
    print(f"Chunk: {chunk_text[:200] if chunk_text else chunk_text}\n")

print(f"Search time: { (time.time() - start)*1000:.1f} ms")
print(f"RAM used: {psutil.virtual_memory().percent}%")
