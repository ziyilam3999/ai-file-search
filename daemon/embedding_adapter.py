"""DAEMON: embedding_adapter.py
Enhanced adapter with real incremental updates to the FAISS index.
"""

import os
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np
from loguru import logger

from core.config import DATABASE_PATH
from core.embedding import Embedder


class EmbeddingAdapter:
    """Enhanced adapter with real incremental updates to the FAISS index."""

    def __init__(self) -> None:
        self.embedder = Embedder()
        self._stats: Dict[str, Any] = {
            "documents_added": 0,
            "documents_removed": 0,
            "operations_failed": 0,
            "last_operation_time": 0,
            "index_size": 0,
        }
        self._pending_operations: List[Tuple[str, str, Optional[str]]] = []
        self._operation_lock = threading.Lock()

        # Ensure index and DB exist
        self._ensure_index_exists()

        # Pre-warm the model to avoid first-operation delay
        self._pre_warm_model()

    def _ensure_index_exists(self) -> None:
        """Ensure FAISS index and SQLite DB exist and are initialized."""
        try:
            # Check/Create FAISS index
            if not os.path.exists(self.embedder.index_path):
                logger.info("Index missing. Initializing empty FAISS index...")
                # Use IndexIDMap to support add_with_ids and remove_ids
                index = faiss.IndexIDMap(faiss.IndexFlatL2(384))
                faiss.write_index(index, self.embedder.index_path)
                logger.info("INDEX: Created new IndexIDMap(IndexFlatL2)")

            # Check/Create SQLite DB
            # We always connect to ensure table exists even if file exists
            from core.database import get_db_manager

            db = get_db_manager()
            db.ensure_table_exists()

        except Exception as e:
            logger.error(f"Failed to initialize index/DB: {e}")

    def _pre_warm_model(self) -> None:
        """Pre-warm the embedding model to avoid delays on first use."""
        try:
            logger.debug("Pre-warming embedding model...")
            # Use the embedder's cached model instead of creating a new instance
            model = self.embedder._get_model()
            # Generate a dummy embedding to initialize everything
            model.encode(["initialization"], show_progress_bar=False)
            logger.debug("Model pre-warming completed")
        except Exception as e:
            logger.warning(f"Model pre-warming failed: {e}")

    def add_document(self, file_path: str, text: str) -> bool:
        """Add a document to the index with real incremental updates."""
        operation_start = time.time()

        try:
            with self._operation_lock:
                logger.debug(f"Adding document to index: {file_path}")

                # Step 1: Remove existing document if it exists (for updates)
                self._remove_existing_document(file_path)

                # Step 2: Process the text into chunks
                chunks = self._process_text_to_chunks(text)
                if not chunks:
                    logger.warning(f"No valid chunks generated for {file_path}")
                    return False

                # Step 3: Generate embeddings for chunks
                embeddings = self._generate_embeddings(chunks)
                if not embeddings:
                    logger.error(f"Failed to generate embeddings for {file_path}")
                    self._stats["operations_failed"] += 1
                    return False

                # Step 4: Add to FAISS index and database
                success = self._add_to_faiss_and_db(file_path, chunks, embeddings)

                if success:
                    self._stats["documents_added"] += 1
                    self._stats["index_size"] = self._get_current_index_size()
                    logger.info(
                        f"Successfully added document: {file_path} ({len(chunks)} chunks)"
                    )
                else:
                    self._stats["operations_failed"] += 1
                    logger.error(f"Failed to add document: {file_path}")

                self._stats["last_operation_time"] = time.time()
                processing_time = time.time() - operation_start
                logger.debug(f"Document processing took {processing_time:.3f} seconds")

                return success

        except Exception as e:
            self._stats["operations_failed"] += 1
            logger.error(f"Error adding document {file_path}: {e}")
            return False

    def remove_document(self, file_path: str) -> bool:
        """Remove a document from the index."""
        try:
            with self._operation_lock:
                logger.debug(f"Removing document from index: {file_path}")

                success = self._remove_existing_document(file_path)

                if success:
                    self._stats["documents_removed"] += 1
                    self._stats["index_size"] = self._get_current_index_size()
                    logger.info(f"Successfully removed document: {file_path}")
                else:
                    logger.warning(f"Document not found in index: {file_path}")

                self._stats["last_operation_time"] = time.time()
                return success

        except Exception as e:
            self._stats["operations_failed"] += 1
            logger.error(f"Error removing document {file_path}: {e}")
            return False

    def save_index(self) -> bool:
        """Save the current index state to disk."""
        try:
            # Load current index from disk to save it (no direct access to private methods)
            if os.path.exists(self.embedder.index_path):
                index = faiss.read_index(self.embedder.index_path)
                faiss.write_index(index, self.embedder.index_path)
                logger.info("Index successfully saved to disk")
                return True
            else:
                logger.warning("No index file found to save")
                return False
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            return False

    def clear_index(self) -> bool:
        """Clear the entire index (used for full reindex)."""
        try:
            with self._operation_lock:
                logger.info("Clearing entire index")

                # Clear database
                from core.database import get_db_manager

                db = get_db_manager()
                db.clear_all()

                # Remove index files to clear
                if os.path.exists(self.embedder.index_path):
                    os.remove(self.embedder.index_path)

                # Reset stats
                self._stats["index_size"] = 0
                self._stats["last_operation_time"] = time.time()

                logger.info("Index cleared successfully")
                return True

        except Exception as e:
            logger.error(f"Error clearing index: {e}")
            self._stats["operations_failed"] += 1
            return False

    def build_index(self, watch_paths: List[str]) -> None:
        """Delegate to the underlying Embedder's build_index method."""
        self.embedder.build_index(watch_paths=watch_paths)

    def get_adapter_stats(self) -> Dict[str, Any]:
        """Get detailed statistics about adapter operations."""
        stats = self._stats.copy()
        stats["pending_operations"] = len(self._pending_operations)
        return stats

    def _process_text_to_chunks(self, text: str) -> List[str]:
        """Process text into chunks using the embedder's chunking logic."""
        try:
            chunks = self.embedder._chunk_text(text)
            # Filter out very short chunks
            valid_chunks = [chunk for chunk in chunks if len(chunk.strip()) >= 20]
            return valid_chunks
        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            return []

    def _generate_embeddings(self, chunks: List[str]) -> Optional[List]:
        """Generate embeddings for a list of chunks."""
        try:
            # Use the embedder's cached model instead of creating a new instance
            model = self.embedder._get_model()

            # Truncate chunks to model's max length
            processed_chunks = [chunk[:256] for chunk in chunks]

            embeddings = model.encode(
                processed_chunks,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )

            return embeddings.tolist()

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return None

    def _add_to_faiss_and_db(
        self, file_path: str, chunks: List[str], embeddings: List
    ) -> bool:
        """Add chunks and embeddings to FAISS index and metadata database."""
        try:
            from core.database import get_db_manager

            # Get current index and database
            index = faiss.read_index(self.embedder.index_path)
            db = get_db_manager()

            # Get next available ID
            result = db.fetch_one("SELECT MAX(id) FROM meta")
            max_id = result[0] if result else None
            next_id = (max_id or 0) + 1

            # Prepare IDs for the new chunks
            num_chunks = len(chunks)
            ids = np.arange(next_id, next_id + num_chunks, dtype=np.int64)

            # Add embeddings to FAISS with IDs
            embeddings_array = np.array(embeddings, dtype=np.float32)
            index.add_with_ids(embeddings_array, ids)

            # Save updated index to disk
            faiss.write_index(index, self.embedder.index_path)

            # Invalidate Embedder cache so next query reloads it
            if hasattr(self.embedder, "clear_cache"):
                self.embedder.clear_cache()

            # Add metadata to database
            metadata_entries = [
                (next_id + i, file_path, chunk) for i, chunk in enumerate(chunks)
            ]

            db.execute_many(
                "INSERT INTO meta (id, file, chunk) VALUES (?, ?, ?)", metadata_entries
            )

            return True

        except Exception as e:
            logger.error(f"Error adding to FAISS and DB: {e}")
            return False

    def _remove_existing_document(self, file_path: str) -> bool:
        """Remove existing document chunks from index (for updates)."""
        try:
            from core.database import get_db_manager

            db = get_db_manager()

            existing_ids_result = db.fetch_all(
                "SELECT id FROM meta WHERE file = ?", (file_path,)
            )
            existing_ids = [row[0] for row in existing_ids_result]

            if existing_ids:
                # Remove from FAISS index first
                if os.path.exists(self.embedder.index_path):
                    try:
                        index = faiss.read_index(self.embedder.index_path)
                        ids_to_remove = np.array(existing_ids, dtype=np.int64)
                        index.remove_ids(ids_to_remove)
                        faiss.write_index(index, self.embedder.index_path)
                    except Exception as e:
                        logger.error(f"Failed to remove IDs from FAISS index: {e}")

                # Remove from database
                placeholders = ",".join("?" for _ in existing_ids)
                db.execute_query(
                    f"DELETE FROM meta WHERE id IN ({placeholders})",
                    tuple(existing_ids),
                )
                logger.debug(
                    f"Removed {len(existing_ids)} existing chunks for {file_path}"
                )

            return len(existing_ids) > 0

        except Exception as e:
            logger.error(f"Error removing existing document: {e}")
            return False

    def _get_current_index_size(self) -> int:
        """Get the current number of vectors in the index."""
        try:
            if os.path.exists(self.embedder.index_path):
                index = faiss.read_index(self.embedder.index_path)
                return index.ntotal
            return 0
        except Exception:
            return 0

    def search(self, query: str) -> List[Dict[str, Optional[str]]]:
        """Search the index for the given query."""
        try:
            results = self.embedder.query(query)
            formatted = []
            for r in results:
                if len(r) == 5:
                    chunk, file_path, _, _, _ = r
                elif len(r) == 3:
                    _, file_path, chunk = r
                elif len(r) == 2:
                    file_path, chunk = r
                else:
                    file_path, chunk = None, None
                formatted.append(
                    {
                        "path": file_path,
                        "chunk": chunk,
                    }
                )
            return formatted
        except Exception as e:
            logger.error(f"Error in search: {e}")
            return []
