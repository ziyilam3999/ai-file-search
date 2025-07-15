"""⚙️  core/embedding.py
Purpose : Chunk plain text, convert to embeddings, save to FAISS.
Inputs  : extracts/<file>.txt
Outputs : index.faiss  +  meta.sqlite
"""

from pathlib import Path

# Update the constants to create fewer chunks
CHUNK_SIZE = 400  # Increased back up (fewer total chunks)
CHUNK_OVERLAP = 25  # Much smaller overlap (fewer overlapping chunks)


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
        logger.info("🚀 Starting FAISS index build process...")

        # Model loading phase
        model_start_time = time.time()
        logger.info("📚 Loading lightweight model...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        model.max_seq_length = 96
        model_load_time = time.time() - model_start_time
        logger.success(f"✅ Model loaded in {model_load_time:.2f} seconds")

        # Database setup phase
        db_start_time = time.time()
        index = faiss.IndexFlatL2(384)
        conn = sqlite3.connect("meta.sqlite")
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS meta "
            "(id INTEGER PRIMARY KEY, file TEXT, chunk TEXT)"
        )
        cursor.execute("DELETE FROM meta")
        db_setup_time = time.time() - db_start_time
        logger.info(f"🗄️ Database setup completed in {db_setup_time:.3f}s")

        # Text processing phase
        chunk_start_time = time.time()
        all_chunks = []
        chunk_metadata = []
        chunk_id = 1
        file_count = 0

        logger.info("📄 Processing files and creating chunks...")
        for file in extracts_path.glob("*.txt"):
            with open(file, "r", encoding="utf-8") as f:
                text = f.read()
            chunks = self._chunk_text(text)
            file_count += 1

            for chunk in chunks:
                if len(chunk.strip()) < 20:
                    continue
                all_chunks.append(chunk if chunk.strip() else "empty")
                chunk_metadata.append((chunk_id, file.name, chunk))
                chunk_id += 1

        chunk_processing_time = time.time() - chunk_start_time
        logger.success(
            f"📝 Processed {file_count} files into {len(all_chunks)} "
            f"chunks in {chunk_processing_time:.2f} seconds"
        )
        avg_chunks = len(all_chunks) / file_count
        logger.info(f"📊 Average chunks per file: {avg_chunks:.1f}")

        # Embedding generation phase
        embed_start_time = time.time()
        logger.info(f"🧠 Encoding {len(all_chunks)} chunks in batches...")

        batch_size = 512
        embeddings = []
        batches_processed = 0

        for i in range(0, len(all_chunks), batch_size):
            batch_start_time = time.time()
            batch = all_chunks[i : i + batch_size]
            batch = [chunk[:256] for chunk in batch]

            batch_embeddings = model.encode(
                batch,
                show_progress_bar=False,
                batch_size=batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True,
                device="cpu",
            )
            embeddings.extend(batch_embeddings)
            batches_processed += 1
            batch_time = time.time() - batch_start_time

            if i % (batch_size * 2) == 0:
                chunks_per_second = len(batch) / batch_time
                logger.info(
                    f"⚡ Processed batch {batches_processed}: "
                    f"{len(batch)} chunks in {batch_time:.2f}s "
                    f"({chunks_per_second:.1f} chunks/sec)"
                )
                progress_pct = 100 * (i + batch_size) / len(all_chunks)
                progress_chunks = min(i + batch_size, len(all_chunks))
                logger.info(
                    f"📈 Progress: {progress_chunks}/{len(all_chunks)} "
                    f"chunks ({progress_pct:.1f}%)"
                )

        embed_time = time.time() - embed_start_time
        chunks_per_second = len(all_chunks) / embed_time
        logger.success(
            f"🎯 Embedding generation completed in {embed_time:.2f} "
            f"seconds ({chunks_per_second:.1f} chunks/sec)"
        )

        # FAISS index building phase
        faiss_start_time = time.time()
        logger.info("🔍 Building FAISS index...")
        embeddings_array = np.array(embeddings, dtype=np.float32)
        index.add(embeddings_array)
        faiss_time = time.time() - faiss_start_time
        logger.success(f"🏗️ FAISS index built in {faiss_time:.3f} seconds")

        # Database insertion phase
        db_insert_start_time = time.time()
        logger.info("💾 Inserting metadata to database...")
        cursor.executemany(
            "INSERT INTO meta (id, file, chunk) VALUES (?, ?, ?)",
            chunk_metadata,
        )
        conn.commit()
        conn.close()
        db_insert_time = time.time() - db_insert_start_time
        logger.success(f"📝 Database insertion completed in {db_insert_time:.3f}s")

        # File saving phase
        save_start_time = time.time()
        faiss.write_index(index, "index.faiss")
        save_time = time.time() - save_start_time
        logger.success(f"💽 Index saved to disk in {save_time:.3f} seconds")

        # Final summary
        total_time = time.time() - total_start_time
        logger.success("🎉 Index build completed successfully!")
        logger.info("📊 Performance Summary:")

        model_pct = 100 * model_load_time / total_time
        logger.info(
            f"   📚 Model loading: {model_load_time:.2f}s " f"({model_pct:.1f}%)"
        )

        chunk_pct = 100 * chunk_processing_time / total_time
        logger.info(
            f"   📄 Text processing: {chunk_processing_time:.2f}s "
            f"({chunk_pct:.1f}%)"
        )

        embed_pct = 100 * embed_time / total_time
        logger.info(
            f"   🧠 Embedding generation: {embed_time:.2f}s " f"({embed_pct:.1f}%)"
        )

        faiss_pct = 100 * faiss_time / total_time
        logger.info(f"   🏗️ FAISS indexing: {faiss_time:.3f}s " f"({faiss_pct:.1f}%)")

        db_pct = 100 * db_insert_time / total_time
        logger.info(f"   💾 Database ops: {db_insert_time:.3f}s " f"({db_pct:.1f}%)")

        save_pct = 100 * save_time / total_time
        logger.info(f"   💽 File saving: {save_time:.3f}s " f"({save_pct:.1f}%)")

        logger.info(f"   ⏱️ Total time: {total_time:.2f}s")

        processing_rate = len(all_chunks) / total_time
        logger.info(f"   📈 Processing rate: {processing_rate:.1f} chunks/s")

        if total_time < 60:
            target_msg = f"✅ Performance target met! ({total_time:.2f}s < 60s)"
            logger.success(target_msg)
        else:
            target_msg = f"⚠️ Performance target missed ({total_time:.2f}s > 60s)"
            logger.warning(target_msg)

        chunk_count = len(all_chunks)
        print(f"Index built successfully: {chunk_count} chunks processed")

    def query(self, query: str, k: int = 5):
        """Optimized query with cached model and batch database access."""
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
        sql_query = f"SELECT id, file, chunk FROM meta WHERE id IN ({placeholders})"
        cursor.execute(sql_query, target_ids)
        rows = cursor.fetchall()

        # Create id->row mapping for fast lookup
        id_to_row = {row[0]: (row[1], row[2]) for row in rows}

        # Return results in the same order as FAISS indices
        # Format: (chunk_text, file_path, chunk_id, score)
        results = []
        for i, target_id in enumerate(target_ids):
            if target_id in id_to_row:
                file_path, chunk_text = id_to_row[target_id]
                score = float(distances[0][i])  # Convert to Python float
                results.append((chunk_text, file_path, target_id, score))
            else:
                # Handle missing chunks gracefully
                results.append(("", "unknown", target_id, 999.0))

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
