"""CORE: database.py
Centralized SQLite database management for metadata operations.

Provides a single source of truth for all database operations,
eliminating duplicate connection code across modules.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, List, Optional, Tuple

from loguru import logger

from core.config import DATABASE_PATH


class DatabaseManager:
    """Manages SQLite database connections and operations."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize DatabaseManager.

        Args:
            db_path: Path to SQLite database. Defaults to DATABASE_PATH from config.
        """
        self.db_path = db_path or DATABASE_PATH

    @contextmanager
    def get_connection(self, read_only: bool = False) -> Iterator[sqlite3.Connection]:
        """
        Context manager for database connections.

        Args:
            read_only: If True, open connection in read-only mode.

        Yields:
            SQLite connection object.

        Example:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM meta")
        """
        conn = None
        try:
            if read_only:
                # Open in read-only mode
                conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            else:
                conn = sqlite3.connect(self.db_path)
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple[Any, ...]] = None,
        commit: bool = True,
    ) -> sqlite3.Cursor:
        """
        Execute a single query.

        Args:
            query: SQL query string
            params: Query parameters (optional)
            commit: Whether to commit after execution

        Returns:
            Cursor object with query results
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            if commit:
                conn.commit()
            return cursor

    def execute_many(
        self,
        query: str,
        params_list: List[Tuple[Any, ...]],
        commit: bool = True,
    ) -> int:
        """
        Execute query with multiple parameter sets.

        Args:
            query: SQL query string
            params_list: List of parameter tuples
            commit: Whether to commit after execution

        Returns:
            Number of rows affected
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            if commit:
                conn.commit()
            return cursor.rowcount

    def fetch_all(
        self, query: str, params: Optional[Tuple[Any, ...]] = None
    ) -> List[Tuple]:
        """
        Fetch all results from a query.

        Args:
            query: SQL query string
            params: Query parameters (optional)

        Returns:
            List of result tuples
        """
        with self.get_connection(read_only=True) as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()

    def fetch_one(
        self, query: str, params: Optional[Tuple[Any, ...]] = None
    ) -> Optional[Tuple]:
        """
        Fetch one result from a query.

        Args:
            query: SQL query string
            params: Query parameters (optional)

        Returns:
            Single result tuple or None
        """
        with self.get_connection(read_only=True) as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()

    def ensure_table_exists(self) -> None:
        """Ensure the meta table exists with correct schema."""
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS meta (
                id INTEGER PRIMARY KEY,
                file TEXT,
                chunk TEXT,
                doc_chunk_id INTEGER
            )
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()
        logger.debug("Ensured meta table exists")

    def clear_all(self) -> int:
        """
        Delete all records from meta table.

        Returns:
            Number of rows deleted
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM meta")
            rowcount = cursor.rowcount
            conn.commit()
        logger.info(f"Cleared {rowcount} records from database")
        return rowcount

    def get_record_count(self) -> int:
        """Get total number of records in meta table."""
        result = self.fetch_one("SELECT COUNT(*) FROM meta")
        return result[0] if result else 0

    def get_unique_file_count(self) -> int:
        """Get number of unique files in meta table."""
        result = self.fetch_one("SELECT COUNT(DISTINCT file) FROM meta")
        return result[0] if result else 0

    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file path exists in the database.

        Args:
            file_path: File path to check

        Returns:
            True if file exists in database
        """
        result = self.fetch_one(
            "SELECT 1 FROM meta WHERE file = ? LIMIT 1", (file_path,)
        )
        return result is not None

    def get_file_ids(self, file_path: str) -> List[int]:
        """
        Get all chunk IDs for a given file.

        Args:
            file_path: File path to lookup

        Returns:
            List of chunk IDs
        """
        results = self.fetch_all("SELECT id FROM meta WHERE file = ?", (file_path,))
        return [row[0] for row in results]

    def delete_file_records(self, file_path: str) -> int:
        """
        Delete all records for a given file.

        Args:
            file_path: File path to delete

        Returns:
            Number of records deleted
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM meta WHERE file = ?", (file_path,))
            rowcount = cursor.rowcount
            conn.commit()
        return rowcount


# Singleton instance for common usage
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get singleton DatabaseManager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
