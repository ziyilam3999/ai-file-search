"""CORE: core/embedding.py
Purpose : Chunk plain text, convert to embeddings, save to FAISS.
Inputs  : extracts/<file>.txt
Outputs : index.faiss  +  meta.sqlite
"""

from pathlib import Path
from typing import Optional

from .config import EMBEDDING_CONFIG

# Get chunk settings from config (single source of truth)
CHUNK_SIZE = EMBEDDING_CONFIG["chunk_size"]
CHUNK_OVERLAP = EMBEDDING_CONFIG["chunk_overlap"]


class Embedder:
    """Optimized embedder with cached model and connection."""

    def __init__(self):
        self._model = None
        self._index = None
        self._conn = None

    def _get_model(self):
        """Lazy load and cache the model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._model

    def _get_index(self):
        """Lazy load and cache the FAISS index."""
        if self._index is None:
            import faiss

            self._index = faiss.read_index("index.faiss")
        return self._index

    def _get_connection(self):
        """Lazy load and cache the database connection."""
        if self._conn is None:
            import sqlite3

            self._conn = sqlite3.connect("meta.sqlite")
        return self._conn

    def build_index(self, extracts_path=Path("extracts")):
        """Build FAISS index with maximum performance optimizations."""
        import sqlite3
        import time

        import faiss
        import numpy as np
        from loguru import logger
        from sentence_transformers import SentenceTransformer

        # Start timing the entire process
        total_start_time = time.time()
        logger.info("STARTING: FAISS index build process...")

        # Model loading phase
        model_start_time = time.time()
        logger.info("LOADING: lightweight model...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        model.max_seq_length = 96
        model_load_time = time.time() - model_start_time
        logger.success(f"SUCCESS: Model loaded in {model_load_time:.2f} seconds")

        # Database setup phase
        db_start_time = time.time()
        index = faiss.IndexFlatL2(384)
        conn = sqlite3.connect("meta.sqlite")
        cursor = conn.cursor()
        # Drop and recreate table to ensure correct schema
        cursor.execute("DROP TABLE IF EXISTS meta")
        cursor.execute(
            "CREATE TABLE meta "
            "(id INTEGER PRIMARY KEY, file TEXT, chunk TEXT, doc_chunk_id INTEGER)"
        )
        cursor.execute("DELETE FROM meta")
        db_setup_time = time.time() - db_start_time
        logger.info(f"DATABASE: setup completed in {db_setup_time:.3f}s")

        # Text processing phase
        chunk_start_time = time.time()
        all_chunks = []
        chunk_metadata = []
        chunk_id = 1
        file_count = 0

        logger.info("PROCESSING: files and creating chunks...")

        # Process all text files in extracts directory (PDF/DOCX already converted to TXT)
        supported_extensions = ["*.txt", "*.md"]
        for extension in supported_extensions:
            for file in extracts_path.glob(f"**/{extension}"):
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        text = f.read()

                    if not text.strip():
                        continue

                    # Get relative path from extracts
                    rel_path = str(file.relative_to(extracts_path)).replace("\\", "/")

                    # Map back to original file in sample_docs for citation
                    original_file_path = self._map_to_original_file(rel_path)

                    # Skip files that don't have original counterparts
                    if original_file_path is None:
                        continue

                    # Split into chunks
                    chunks = self._chunk_text(text)
                    file_count += 1

                    # Track progress
                    for doc_chunk_id, chunk in enumerate(chunks, 1):
                        all_chunks.append(chunk)
                        # Store original file path for citations
                        chunk_metadata.append(
                            (chunk_id, original_file_path, chunk, doc_chunk_id)
                        )
                        chunk_id += 1

                    if file_count % 5 == 0:
                        logger.info(
                            f"PROGRESS: {file_count} files processed, {len(all_chunks)} chunks created"
                        )

                except Exception as e:
                    logger.error(f"Error processing file {file}: {e}")
                    continue

        chunk_time = time.time() - chunk_start_time
        logger.success(
            f"SUCCESS: {len(all_chunks)} chunks from {file_count} files in {chunk_time:.2f}s"
        )

        if not all_chunks:
            logger.error("ERROR: No chunks created - no files to index")
            return

        # Embedding generation phase
        embed_start_time = time.time()
        logger.info("GENERATING: embeddings...")

        # Process in batches for better memory management
        batch_size = 100
        embeddings = []

        for i in range(0, len(all_chunks), batch_size):
            batch_chunks = all_chunks[i : i + batch_size]
            batch_embeddings = model.encode(
                batch_chunks,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            embeddings.extend(batch_embeddings)

            if (i // batch_size + 1) % 10 == 0:
                logger.info(
                    f"PROGRESS: {i + len(batch_chunks)}/{len(all_chunks)} embeddings generated"
                )

        embeddings = np.array(embeddings, dtype=np.float32)
        embed_time = time.time() - embed_start_time
        logger.success(f"SUCCESS: {len(embeddings)} embeddings in {embed_time:.2f}s")

        # Index building phase
        index_start_time = time.time()
        logger.info("BUILDING: FAISS index...")
        index.add(embeddings)
        index_time = time.time() - index_start_time
        logger.success(f"SUCCESS: FAISS index built in {index_time:.3f}s")

        # Database insertion phase
        db_insert_start = time.time()
        logger.info("INSERTING: metadata into database...")
        cursor.executemany(
            "INSERT INTO meta (id, file, chunk, doc_chunk_id) VALUES (?, ?, ?, ?)",
            chunk_metadata,
        )
        conn.commit()
        conn.close()
        db_insert_time = time.time() - db_insert_start
        logger.success(f"SUCCESS: Database insert in {db_insert_time:.3f}s")

        # Save index to disk
        save_start_time = time.time()
        logger.info("SAVING: index to disk...")
        faiss.write_index(index, "index.faiss")
        save_time = time.time() - save_start_time
        logger.success(f"SUCCESS: Index saved in {save_time:.3f}s")

        # Final statistics
        total_time = time.time() - total_start_time
        logger.success(f"INDEX BUILD COMPLETE: {total_time:.2f}s total")
        logger.info(
            f"STATS: {file_count} files, {len(all_chunks)} chunks, {len(embeddings)} embeddings"
        )

        # Store the built index
        self._index = index

    def query(self, query: str, k: int = 5):
        """Optimized query with cached model and batch database access.

        CRITICAL: This method MUST return 5-tuple format (chunk_text, file_path, chunk_id, doc_chunk_id, score)
        for UI compatibility and test suite validation. See docs/EMBEDDER_API_SPECIFICATION.md
        for complete format requirements and troubleshooting guide.
        """
        import numpy as np

        # Use cached model and index (no reloading!)
        model = self._get_model()
        index = self._get_index()
        conn = self._get_connection()
        cursor = conn.cursor()

        # Encode query (fast with cached model)
        embedding = model.encode(query, convert_to_numpy=True)
        distances, indices = index.search(np.array([embedding], dtype=np.float32), k)

        # Batch database query for better performance
        target_ids = [int(i + 1) for i in indices[0]]
        placeholders = ",".join("?" for _ in target_ids)
        sql_query = f"SELECT id, file, chunk, doc_chunk_id FROM meta WHERE id IN ({placeholders})"
        cursor.execute(sql_query, target_ids)
        rows = cursor.fetchall()

        # Create id->row mapping with document chunk info
        id_to_row = {
            row[0]: (row[1], row[2], row[3]) for row in rows
        }  # file, chunk, doc_chunk_id

        # Return results in 5-tuple format: (chunk_text, file_path, chunk_id, doc_chunk_id, score)
        results = []
        for i, target_id in enumerate(target_ids):
            if target_id in id_to_row:
                file_path, chunk_text, doc_chunk_id = id_to_row[target_id]
                score = float(distances[0][i])
                results.append((chunk_text, file_path, target_id, doc_chunk_id, score))
            else:
                results.append((None, None, target_id, 1, float("inf")))

        return results

    def _chunk_text(self, text):
        """Split text into overlapping chunks of CHUNK_SIZE tokens."""
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = start + CHUNK_SIZE
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            start += CHUNK_SIZE - CHUNK_OVERLAP
        return chunks

    def _map_to_original_file(self, extracts_rel_path: str) -> Optional[str]:
        """Map extracted file path back to original file in sample_docs.

        Args:
            extracts_rel_path: Relative path from extracts/ (e.g., 'business_rules/file.txt')

        Returns:
            Original file path in sample_docs (e.g., 'sample_docs/business_rules/file.pdf')
            Returns None if no original file exists.
        """
        from pathlib import Path

        # Parse the extracts path
        path_parts = extracts_rel_path.split("/")
        if len(path_parts) < 2:
            # Root level file - check if original exists before mapping
            potential_original = f"sample_docs/{extracts_rel_path}"
            if Path(potential_original).exists():
                return potential_original
            else:
                # Skip files that don't have originals (like extracted README.txt)
                return None

        category = path_parts[0]  # e.g., 'business_rules'
        filename_txt = path_parts[-1]  # e.g., 'file.txt'

        # Remove .txt extension to get base name
        if filename_txt.endswith(".txt"):
            base_name = filename_txt[:-4]
        elif filename_txt.endswith(".md"):
            base_name = filename_txt[:-3]
        else:
            base_name = filename_txt

        # Check what original file exists in sample_docs
        sample_docs_category = Path(f"sample_docs/{category}")
        if sample_docs_category.exists():
            # Look for PDF first, then DOCX, then TXT, then MD
            for ext in [".pdf", ".docx", ".txt", ".md"]:
                original_file = sample_docs_category / f"{base_name}{ext}"
                if original_file.exists():
                    return str(original_file).replace("\\", "/")

        # No original file found - return None to skip indexing this file
        return None
