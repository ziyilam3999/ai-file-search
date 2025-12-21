"""CORE: embedding.py
Purpose : Generate and search embeddings for document chunks using FAISS.
Inputs  : text chunks from extracted documents
Outputs : FAISS index, SQLite metadata, search results
Uses    : sentence-transformers/all-MiniLM-L6-v2, FAISS, SQLite
"""

import sqlite3
import time
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Optional, Tuple

import faiss
import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer

from .config import DATABASE_PATH, EXTRACTS_DIR, INDEX_PATH

# Configuration
CHUNK_SIZE = 200  # words per chunk
CHUNK_OVERLAP = 50  # word overlap between chunks


class Embedder:
    """Handles document embedding and similarity search using FAISS."""

    def __init__(self):
        self.model_name = "all-MiniLM-L6-v2"
        self.index_path = INDEX_PATH
        self.db_path = DATABASE_PATH

    def build_index(self, extracts_dir: str = EXTRACTS_DIR) -> None:
        """
        Build FAISS index from all extracted text files.

        Args:
            extracts_dir: Directory containing extracted text files

        Side Effects:
            - Creates index.faiss file
            - Creates meta.sqlite database with file metadata
        """
        logger.info("BUILDING: document embeddings index...")
        start_time = time.time()

        # Initialize model
        logger.info("LOADING: sentence transformer model...")
        model = SentenceTransformer(self.model_name)
        logger.success("SUCCESS: model loaded")

        # Initialize FAISS index
        index = faiss.IndexFlatL2(384)  # all-MiniLM-L6-v2 has 384 dimensions

        # Initialize database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS meta (
                id INTEGER PRIMARY KEY,
                file TEXT,
                chunk TEXT,
                doc_chunk_id INTEGER
            )
        """
        )

        # Process all text files
        all_chunks = []
        chunk_metadata = []
        chunk_id = 0

        extracts_path = Path(extracts_dir)
        if not extracts_path.exists():
            logger.error(f"ERROR: {extracts_dir} directory not found")
            return

        # Walk through all text files in extracts directory
        for file_path in extracts_path.rglob("*.txt"):
            logger.info(f"PROCESSING: {file_path}")
            # CRITICAL FIX: Ensure forward slashes for cross-platform compatibility
            rel_path = str(file_path.relative_to(extracts_path)).replace("\\", "/")

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                chunks = self._chunk_text(content)
                if chunks:
                    # CRITICAL FIX: Map back to original file in ai_search_docs for citation
                    original_file_path = self._map_to_original_file(rel_path)

                    # ONLY index if we have a valid original file mapping
                    if original_file_path is None:
                        logger.warning(
                            f"SKIPPING: {rel_path} - no original file found in ai_search_docs"
                        )
                        continue

                    logger.success(f"MAPPING: {rel_path} → {original_file_path}")

                    for doc_chunk_id, chunk in enumerate(chunks):
                        all_chunks.append(chunk)
                        # Store original file path for citations
                        chunk_metadata.append(
                            (chunk_id, original_file_path, chunk, doc_chunk_id)
                        )
                        chunk_id += 1

                    logger.info(f"ADDED: {len(chunks)} chunks from {rel_path}")

            except Exception as e:
                logger.error(f"ERROR: processing {file_path}: {e}")

        if not all_chunks:
            logger.error("ERROR: No chunks found to index")
            return

        logger.info(f"TOTAL: {len(all_chunks)} chunks to embed")

        # Generate embeddings in batches
        logger.info("GENERATING: embeddings...")
        embed_start_time = time.time()

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
        total_time = time.time() - start_time
        logger.success(
            f"COMPLETE: Index built in {total_time:.2f}s total ({len(all_chunks)} chunks)"
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
        if not Path(self.index_path).exists() or not Path(self.db_path).exists():
            logger.error("ERROR: Index or database not found. Run build_index() first.")
            return []

        try:
            # Load model and index
            model = SentenceTransformer(self.model_name)
            index = faiss.read_index(self.index_path)

            # Generate query embedding
            query_embedding = model.encode(
                [query_text], convert_to_numpy=True, normalize_embeddings=True
            )

            # Search
            scores, indices = index.search(query_embedding.astype(np.float32), k)

            # Get metadata from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, file, chunk, doc_chunk_id FROM meta")
            metadata = cursor.fetchall()
            conn.close()

            # Create lookup dictionary
            id_to_row = {row[0]: (row[1], row[2], row[3]) for row in metadata}

            results = []
            # Return results in 5-tuple format: (chunk_text, file_path, chunk_id, doc_chunk_id, score)
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(metadata):
                    target_id = idx
                    file_path, chunk_text, doc_chunk_id = id_to_row[target_id]
                    # 5-tuple format required by ask.py
                    results.append(
                        (chunk_text, file_path, target_id, doc_chunk_id, score)
                    )

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

    def _map_to_original_file(self, extracts_rel_path: str) -> Optional[str]:
        """Map extracted file path back to original file in ai_search_docs with robust Unicode handling.

        CRITICAL: This function MUST return ai_search_docs/ paths for correct citations.
        NEVER return extracts/ paths in citations.

        Args:
            extracts_rel_path: Relative path from extracts/ (e.g., 'business_rules/file.txt')

        Returns:
            Original file path in ai_search_docs (e.g., 'ai_search_docs/business_rules/file.pdf')
            Returns None if no original file exists - this will SKIP indexing the file.
        """

        def normalize_filename(name: str) -> str:
            """Normalize filename for robust comparison by handling Unicode and extensions."""
            # Remove common extensions
            if name.endswith((".txt", ".pdf", ".docx", ".md")):
                name = name.rsplit(".", 1)[0]

            # Normalize Unicode characters (NFKC handles compatibility characters)
            normalized = unicodedata.normalize("NFKC", name)

            # Strip whitespace and normalize internal spaces
            return " ".join(normalized.split())

        def fuzzy_match_file(
            base_name: str, directory: Path, threshold: float = 0.85
        ) -> Optional[Path]:
            """Find best matching file using fuzzy string matching."""
            if not directory.exists():
                return None

            best_match = None
            best_score = threshold
            normalized_base = normalize_filename(base_name)

            logger.info(f"FUZZY SEARCH: Looking for '{normalized_base}' in {directory}")

            for file_path in directory.iterdir():
                if file_path.is_file():
                    normalized_file = normalize_filename(file_path.stem)

                    # Calculate similarity ratio
                    similarity = SequenceMatcher(
                        None, normalized_base, normalized_file
                    ).ratio()

                    logger.debug(
                        f"COMPARE: '{normalized_base}' vs '{normalized_file}' = {similarity:.3f}"
                    )

                    if similarity > best_score:
                        best_match = file_path
                        best_score = similarity
                        logger.info(
                            f"NEW BEST: {file_path.name} (score: {similarity:.3f})"
                        )

            if best_match:
                logger.success(
                    f"FUZZY MATCH: '{base_name}' → '{best_match.name}' (score: {best_score:.3f})"
                )

            return best_match

        # Parse the extracts path
        path_parts = extracts_rel_path.split("/")
        if len(path_parts) < 2:
            # Single file at root level
            potential_original = f"ai_search_docs/{extracts_rel_path}"
            return potential_original if Path(potential_original).exists() else None

        category = path_parts[0]  # e.g., 'business_rules'
        filename_txt = path_parts[-1]  # e.g., 'file.txt'

        # Normalize the filename for robust matching
        base_name = normalize_filename(filename_txt)

        logger.info(f"MAPPING: {extracts_rel_path}")
        logger.info(f"  Category: {category}")
        logger.info(f"  Original filename: '{filename_txt}'")
        logger.info(f"  Normalized base: '{base_name}'")

        # Check what original file exists in ai_search_docs
        ai_docs_category = Path(f"ai_search_docs/{category}")
        if not ai_docs_category.exists():
            logger.warning(
                f"CATEGORY MISSING: ai_search_docs/{category} does not exist"
            )
            return None

        # PHASE 1: Try exact matching with normalized names
        logger.info("PHASE 1: Exact matching with extensions")
        for ext in [".pdf", ".docx", ".txt", ".md"]:
            # Try with normalized base name
            test_filename = f"{base_name}{ext}"
            original_file = ai_docs_category / test_filename

            logger.debug(f"  Testing exact: {test_filename}")

            if original_file.exists():
                result_path = str(original_file).replace("\\", "/")
                logger.success(f"EXACT MATCH: {extracts_rel_path} → {result_path}")
                return result_path

        # PHASE 2: Try fuzzy matching as fallback
        logger.info("PHASE 2: Fuzzy matching fallback")
        matched_file = fuzzy_match_file(base_name, ai_docs_category)

        if matched_file:
            result_path = str(matched_file).replace("\\", "/")
            logger.success(f"FUZZY SUCCESS: {extracts_rel_path} → {result_path}")
            return result_path

        # PHASE 3: Last resort - try original filename without normalization
        logger.info("PHASE 3: Last resort with original filename")
        original_base = (
            filename_txt[:-4]
            if filename_txt.endswith(".txt")
            else filename_txt[:-3] if filename_txt.endswith(".md") else filename_txt
        )

        for ext in [".pdf", ".docx", ".txt", ".md"]:
            test_filename = f"{original_base}{ext}"
            original_file = ai_docs_category / test_filename

            if original_file.exists():
                result_path = str(original_file).replace("\\", "/")
                logger.success(f"ORIGINAL MATCH: {extracts_rel_path} → {result_path}")
                return result_path

        # No original file found - return None to skip indexing this file
        logger.error(
            f"NO MATCH FOUND: {extracts_rel_path} - will be SKIPPED from indexing"
        )
        logger.info(f"  Available files in {ai_docs_category}:")
        if ai_docs_category.exists():
            for file in ai_docs_category.iterdir():
                if file.is_file():
                    logger.info(f"    - {file.name}")

        return None
