import importlib
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Ensure real modules are imported (not mocked from other tests like test_cli.py)
_MODULES_TO_CHECK = ["faiss", "core.embedding", "sentence_transformers"]
for mod_name in _MODULES_TO_CHECK:
    if mod_name in sys.modules and isinstance(sys.modules[mod_name], MagicMock):
        del sys.modules[mod_name]
        # Force reimport of core.embedding if it was mocked
        if mod_name == "core.embedding":
            # Also need to reimport dependent modules
            for key in list(sys.modules.keys()):
                if key.startswith("core.") or key.startswith("daemon."):
                    del sys.modules[key]

import faiss
import numpy as np

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from daemon.watch import EmbeddingAdapter


class TestFaissSync(unittest.TestCase):
    def setUp(self):
        # Create temp directory
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "meta.sqlite")
        self.index_path = os.path.join(self.test_dir, "index.faiss")

        # Initialize DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Schema based on daemon/watch.py usage and core/embedding.py
        cursor.execute(
            """
            CREATE TABLE meta (
                id INTEGER PRIMARY KEY,
                file TEXT,
                chunk TEXT,
                doc_chunk_id TEXT
            )
        """
        )
        conn.commit()
        conn.close()

        # Initialize FAISS index (IndexIDMap over IndexFlatL2)
        d = 384
        index = faiss.IndexFlatL2(d)
        index = faiss.IndexIDMap(index)
        faiss.write_index(index, self.index_path)

        # Mock SentenceTransformer to avoid loading model
        self.st_patcher = patch("daemon.watch.SentenceTransformer")
        self.mock_st_class = self.st_patcher.start()
        self.mock_model = MagicMock()
        self.mock_st_class.return_value = self.mock_model

        # Mock encode to return dummy embeddings
        def side_effect_encode(sentences, **kwargs):
            # Return random vectors
            return np.random.rand(len(sentences), 384).astype(np.float32)

        self.mock_model.encode.side_effect = side_effect_encode

    def tearDown(self):
        self.st_patcher.stop()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_sync_add_remove(self):
        """Test synchronization between FAISS index and SQLite metadata."""

        # Initialize Adapter
        # This will trigger _pre_warm_model which uses our mocked SentenceTransformer
        adapter = EmbeddingAdapter()

        # Override paths to use our temp environment
        adapter.embedder.index_path = self.index_path
        adapter.embedder.db_path = self.db_path

        # Create dummy file
        dummy_file = os.path.join(self.test_dir, "test_doc.txt")
        with open(dummy_file, "w") as f:
            f.write("This is a test document.")

        # 1. Add document
        # Mock _process_text_to_chunks to return deterministic chunks
        with patch.object(
            adapter, "_process_text_to_chunks", return_value=["chunk1", "chunk2"]
        ):
            success = adapter.add_document(dummy_file, "content")
            self.assertTrue(success, "Failed to add document")

        # 2. Verify DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, file, chunk FROM meta ORDER BY id")
        rows = cursor.fetchall()
        conn.close()

        self.assertEqual(len(rows), 2, "Should have 2 chunks in DB")
        self.assertEqual(rows[0][1], dummy_file)
        self.assertEqual(rows[0][2], "chunk1")
        id1, id2 = rows[0][0], rows[1][0]

        # 3. Verify FAISS
        index = faiss.read_index(self.index_path)
        self.assertEqual(index.ntotal, 2, "FAISS should have 2 vectors")

        # 4. Add another document to ensure IDs increment and don't clash
        dummy_file_2 = os.path.join(self.test_dir, "test_doc_2.txt")
        with patch.object(adapter, "_process_text_to_chunks", return_value=["chunk3"]):
            adapter.add_document(dummy_file_2, "content2")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM meta WHERE file=?", (dummy_file_2,))
        rows_2 = cursor.fetchall()
        conn.close()
        self.assertEqual(len(rows_2), 1)
        id3 = rows_2[0][0]

        # Ensure IDs are distinct
        self.assertNotIn(id3, [id1, id2])

        # 5. Remove first document
        success = adapter.remove_document(dummy_file)
        self.assertTrue(success, "Failed to remove document")

        # 6. Verify DB empty for doc 1
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM meta WHERE file=?", (dummy_file,))
        rows = cursor.fetchall()
        conn.close()
        self.assertEqual(len(rows), 0, "DB should be empty for removed file")

        # 7. Verify FAISS size
        index = faiss.read_index(self.index_path)
        self.assertEqual(index.ntotal, 1, "FAISS should have 1 vector left")

        # 8. Add document 1 again
        with patch.object(
            adapter, "_process_text_to_chunks", return_value=["chunk1", "chunk2"]
        ):
            adapter.add_document(dummy_file, "content")

        # 9. Verify new IDs
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM meta WHERE file=? ORDER BY id", (dummy_file,))
        rows_new = cursor.fetchall()
        conn.close()

        self.assertEqual(len(rows_new), 2)
        new_id1 = rows_new[0][0]

        # New IDs should be greater than the max existing ID (id3)
        self.assertGreater(new_id1, id3, "New IDs should be strictly increasing")

        # Verify FAISS has correct total
        index = faiss.read_index(self.index_path)
        self.assertEqual(
            index.ntotal, 3, "FAISS should have 3 vectors (1 from doc2 + 2 from doc1)"
        )


if __name__ == "__main__":
    unittest.main()
