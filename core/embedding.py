"""CORE: embedding.py
Purpose : Generate and search embeddings for document chunks using FAISS.
Inputs  : text chunks from extracted documents
Outputs : FAISS index, SQLite metadata, search results
Uses    : sentence-transformers/all-MiniLM-L6-v2, FAISS, SQLite
"""

import time
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Optional, Tuple

import faiss
import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer

from core.extract import Extractor
from core.path_utils import get_supported_files

from .config import DATABASE_PATH, EXTRACTS_DIR, INDEX_PATH

# Configuration
CHUNK_SIZE = 200  # words per chunk
CHUNK_OVERLAP = 50  # word overlap between chunks

_MODEL_CACHE = None
_INDEX_CACHE = None
_METADATA_CACHE = None
_INDEX_MTIME = 0.0
_METADATA_MTIME = 0.0


class Embedder:
    """Handles document embedding and similarity search using FAISS."""

    def __init__(self):
        self.model_name = "all-MiniLM-L6-v2"
        self.index_path = INDEX_PATH
        self.db_path = DATABASE_PATH

    def _get_model(self):
        global _MODEL_CACHE
        if _MODEL_CACHE is None:
            logger.info("LOADING: sentence transformer model...")
            _MODEL_CACHE = SentenceTransformer(self.model_name)
            logger.success("SUCCESS: model loaded")
        return _MODEL_CACHE

    def _get_index(self):
        global _INDEX_CACHE, _INDEX_MTIME

        if not Path(self.index_path).exists():
            return None

        current_mtime = Path(self.index_path).stat().st_mtime

        if _INDEX_CACHE is None or current_mtime > _INDEX_MTIME:
            logger.info("LOADING: FAISS index (updated)...")
            _INDEX_CACHE = faiss.read_index(self.index_path)
            _INDEX_MTIME = current_mtime
            logger.info(
                f"INDEX: Type={type(_INDEX_CACHE).__name__}, Total Vectors={_INDEX_CACHE.ntotal}"
            )
            logger.success("SUCCESS: FAISS index loaded")

        return _INDEX_CACHE

    def _get_metadata(self):
        global _METADATA_CACHE, _METADATA_MTIME

        if not Path(self.db_path).exists():
            return None

        current_mtime = Path(self.db_path).stat().st_mtime

        if _METADATA_CACHE is None or current_mtime > _METADATA_MTIME:
            logger.info("LOADING: metadata cache (updated)...")
            try:
                from core.database import get_db_manager

                db = get_db_manager()
                metadata = db.fetch_all(
                    "SELECT id, file, chunk, doc_chunk_id FROM meta"
                )
                # Create lookup dictionary: id -> (file, chunk, doc_chunk_id)
                _METADATA_CACHE = {row[0]: (row[1], row[2], row[3]) for row in metadata}
                _METADATA_MTIME = current_mtime

                if _METADATA_CACHE:
                    min_id = min(_METADATA_CACHE.keys())
                    max_id = max(_METADATA_CACHE.keys())
                    logger.info(
                        f"METADATA: ID Range=[{min_id}, {max_id}], Count={len(_METADATA_CACHE)}"
                    )
                else:
                    logger.info("METADATA: Empty")

                logger.success(
                    f"SUCCESS: metadata loaded ({len(_METADATA_CACHE)} entries)"
                )
            except Exception as e:
                logger.error(f"ERROR: Database corrupted or missing table 'meta': {e}")
                return None
        return _METADATA_CACHE

    def clear_cache(self):
        """Clear all in-memory caches to force reload from disk."""
        global _INDEX_CACHE, _METADATA_CACHE
        _INDEX_CACHE = None
        _METADATA_CACHE = None
        logger.info("CACHE: Cleared index and metadata caches")

    def build_index(self, watch_paths: Optional[List[str]] = None) -> None:
        """
        Build FAISS index from source documents in watch_paths.

        Args:
            watch_paths: List of directory paths to index. If None, loads from config.

        Side Effects:
            - Creates index.faiss file
            - Creates meta.sqlite database with file metadata
        """
        from core.config import load_watch_paths

        if watch_paths is None:
            watch_paths = load_watch_paths()

        logger.info(
            f"BUILDING: document embeddings index from {len(watch_paths)} paths..."
        )
        start_time = time.time()

        # Clear existing caches
        self.clear_cache()

        # Initialize model
        model = self._get_model()

        # Initialize FAISS index
        # Use IndexIDMap to support add_with_ids and remove_ids
        index = faiss.IndexIDMap(faiss.IndexFlatL2(384))

        # Initialize database
        from core.database import get_db_manager

        db = get_db_manager()
        db.execute_query("DROP TABLE IF EXISTS meta")
        db.execute_query(
            """
            CREATE TABLE meta (
                id INTEGER PRIMARY KEY,
                file TEXT,
                chunk TEXT,
                doc_chunk_id INTEGER
            )
        """
        )

        # Process all files
        all_chunks = []
        chunk_metadata = []
        chunk_id = 0
        extractor = Extractor()

        for watch_path in watch_paths:
            logger.info(f"SCANNING: {watch_path}")
            files = get_supported_files(watch_path)

            for file_path in files:
                logger.info(f"PROCESSING: {file_path}")
                try:
                    content = extractor.run(file_path)
                    if not content:
                        continue

                    chunks = self._chunk_text(content)
                    if chunks:
                        # Store absolute path
                        abs_path = str(file_path.resolve()).replace("\\", "/")

                        for i, chunk in enumerate(chunks):
                            all_chunks.append(chunk)
                            chunk_metadata.append((chunk_id, abs_path, chunk, i))
                            chunk_id += 1

                            # Batch insert to keep memory usage low
                            if len(all_chunks) >= 1000:
                                self._batch_insert(
                                    index, model, db, all_chunks, chunk_metadata
                                )
                                all_chunks = []
                                chunk_metadata = []

                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")

        # Process remaining chunks
        if all_chunks:
            self._batch_insert(index, model, db, all_chunks, chunk_metadata)

        # Save index
        faiss.write_index(index, self.index_path)

        elapsed = time.time() - start_time
        logger.success(f"INDEXING COMPLETE: {chunk_id} chunks in {elapsed:.2f}s")

    def _batch_insert(self, index, model, db, chunks, metadata):
        """Helper to insert a batch of chunks."""
        embeddings = model.encode(
            chunks, convert_to_numpy=True, normalize_embeddings=True
        )
        index.add(embeddings)
        db.execute_many(
            "INSERT INTO meta (id, file, chunk, doc_chunk_id) VALUES (?, ?, ?, ?)",
            metadata,
        )

    def query(self, query_text: str, k: int = 5) -> List[Tuple]:
        """
        Search for similar chunks using the FAISS index.

        Args:
            query_text: Search query
            k: Number of top results to return

        Returns:
            List of tuples: (chunk_text, file_path, chunk_id, doc_chunk_id, similarity_score)

        CRITICAL: This method MUST return 5-tuple format (chunk_text, file_path, chunk_id, doc_chunk_id, score)
        for compatibility with ask.py citation generation.
        """
        # Use cached index and metadata
        index = self._get_index()
        id_to_row = self._get_metadata()

        if index is None or id_to_row is None:
            logger.error("ERROR: Index or database not found. Run build_index() first.")
            return []

        try:
            # Load model (cached)
            model = self._get_model()

            # Generate query embedding
            query_embedding = model.encode(
                [query_text], convert_to_numpy=True, normalize_embeddings=True
            )

            # Search
            scores, indices = index.search(query_embedding.astype(np.float32), k)

            results = []
            # Return results in 5-tuple format: (chunk_text, file_path, chunk_id, doc_chunk_id, score)
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:
                    continue

                target_id = int(idx)

                # Check if idx exists in metadata
                if target_id not in id_to_row:
                    # Cache miss! Try forcing a reload of metadata
                    logger.warning(
                        f"Index ID {target_id} not found in metadata cache. Forcing reload..."
                    )
                    # Force reload by resetting mtime
                    global _METADATA_MTIME
                    _METADATA_MTIME = 0
                    id_to_row = self._get_metadata()

                    if id_to_row is None or target_id not in id_to_row:
                        logger.error(
                            f"Index ID {target_id} still missing after reload. Index/DB out of sync."
                        )
                        continue

                file_path, chunk_text, doc_chunk_id = id_to_row[target_id]
                # 5-tuple format required by ask.py
                results.append((chunk_text, file_path, target_id, doc_chunk_id, score))

            return results

        except Exception as e:
            logger.error(f"ERROR: Query failed: {e}")
            return []

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks by word count."""
        words = text.split()
        if len(words) <= CHUNK_SIZE:
            return [text] if text.strip() else []

        chunks = []
        start = 0
        while start < len(words):
            end = min(start + CHUNK_SIZE, len(words))
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            start += CHUNK_SIZE - CHUNK_OVERLAP
        return chunks
