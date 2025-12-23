#!/usr/bin/env python3
"""
Verification and repair tool for FAISS/Database synchronization.

Purpose: Detect and fix orphaned vectors in FAISS index that don't exist in metadata database.
Usage:
    python tools/verify_index_sync.py check       # Check for sync issues
    python tools/verify_index_sync.py repair      # Fix sync issues
    python tools/verify_index_sync.py stats       # Show detailed statistics
"""

import argparse
import sqlite3
import sys
from pathlib import Path

import faiss
import numpy as np
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import DATABASE_PATH, INDEX_PATH


def get_database_ids() -> set:
    """Get all IDs from the metadata database."""
    if not Path(DATABASE_PATH).exists():
        logger.error(f"Database not found: {DATABASE_PATH}")
        return set()

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM meta")
    db_ids = {row[0] for row in cursor.fetchall()}
    conn.close()

    return db_ids


def get_faiss_ids() -> set:
    """Get all IDs from the FAISS index."""
    if not Path(INDEX_PATH).exists():
        logger.error(f"Index not found: {INDEX_PATH}")
        return set()

    try:
        index = faiss.read_index(INDEX_PATH)

        if not isinstance(index, faiss.IndexIDMap):
            logger.error("Index is not an IndexIDMap - cannot retrieve IDs")
            return set()

        # For IndexIDMap, we can get IDs via the id_map attribute
        # However, FAISS SWIG doesn't expose this directly in Python
        # Best approach: use search to find nearest neighbors, which returns IDs

        logger.info(f"Extracting IDs from {index.ntotal} vectors...")

        # Get all vectors by searching each vector against itself
        # This is more efficient than scanning all possible IDs
        faiss_ids = set()

        # Most reliable approach: try to access the internal id_map
        # Cast to proper type to access id_map
        try:
            # Access the underlying IndexIDMap's id_map using SWIG
            # The id_map is a vector of int64
            faiss_ids_list = faiss.vector_to_array(index.id_map)
            faiss_ids = set(faiss_ids_list.tolist())
            logger.success(f"Extracted {len(faiss_ids)} IDs from index")
            return faiss_ids
        except AttributeError:
            # Fallback: reconstruct each vector by internal index
            logger.warning("Cannot access id_map directly, using reconstruction method")
            pass

        # Fallback method: For each internal index, try to find its external ID
        # by searching for the vector itself
        for i in range(min(index.ntotal, 10000)):  # Limit to avoid timeout
            try:
                # Reconstruct vector by internal index
                vector = index.reconstruct(i)
                # Search for this vector to get its external ID
                distances, indices = index.search(vector.reshape(1, -1), 1)
                external_id = indices[0][0]
                faiss_ids.add(int(external_id))
            except Exception as e:
                if i < 10:  # Log first few errors
                    logger.debug(f"Failed to process index {i}: {e}")
                pass

            if i % 1000 == 0 and i > 0:
                logger.info(f"Processed {i}/{index.ntotal} vectors...")

        if len(faiss_ids) < index.ntotal:
            logger.warning(
                f"Only extracted {len(faiss_ids)}/{index.ntotal} IDs (limitation of method)"
            )

        return faiss_ids

    except Exception as e:
        logger.error(f"Error reading FAISS index: {e}")
        return set()


def check_sync() -> dict:
    """Check synchronization between FAISS and database."""
    logger.info("Checking FAISS/Database synchronization...")

    db_ids = get_database_ids()
    faiss_ids = get_faiss_ids()

    if not db_ids or not faiss_ids:
        logger.error("Cannot perform sync check - missing data")
        return {
            "status": "error",
            "db_count": len(db_ids),
            "faiss_count": len(faiss_ids),
        }

    # Find mismatches
    orphaned_in_faiss = faiss_ids - db_ids  # In FAISS but not in DB
    missing_in_faiss = db_ids - faiss_ids  # In DB but not in FAISS

    result = {
        "status": (
            "synced" if not (orphaned_in_faiss or missing_in_faiss) else "out_of_sync"
        ),
        "db_count": len(db_ids),
        "faiss_count": len(faiss_ids),
        "orphaned_in_faiss": sorted(orphaned_in_faiss),
        "missing_in_faiss": sorted(missing_in_faiss),
    }

    return result


def repair_sync() -> bool:
    """Repair synchronization by removing orphaned vectors from FAISS."""
    logger.info("Starting synchronization repair...")

    result = check_sync()

    if result["status"] == "error":
        logger.error("Cannot repair - check failed")
        return False

    if result["status"] == "synced":
        logger.success("Index is already synchronized!")
        return True

    orphaned = result["orphaned_in_faiss"]

    if orphaned:
        logger.warning(f"Found {len(orphaned)} orphaned vectors in FAISS")
        logger.info(
            f"Orphaned IDs: {orphaned[:10]}{'...' if len(orphaned) > 10 else ''}"
        )

        try:
            # Load index
            index = faiss.read_index(INDEX_PATH)

            # Remove orphaned IDs
            ids_to_remove = np.array(orphaned, dtype=np.int64)
            logger.info(f"Removing {len(ids_to_remove)} orphaned vectors...")
            index.remove_ids(ids_to_remove)

            # Save repaired index
            faiss.write_index(index, INDEX_PATH)
            logger.success(f"Removed {len(ids_to_remove)} orphaned vectors from FAISS")

        except Exception as e:
            logger.error(f"Failed to repair index: {e}")
            return False

    missing = result["missing_in_faiss"]
    if missing:
        logger.warning(f"Found {len(missing)} vectors in DB but missing in FAISS")
        logger.warning("These require re-extraction. Consider running a full reindex.")
        logger.info(f"Missing IDs: {missing[:10]}{'...' if len(missing) > 10 else ''}")

    return True


def show_stats() -> None:
    """Show detailed statistics about index and database."""
    logger.info("Gathering statistics...")

    # Database stats
    if Path(DATABASE_PATH).exists():
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM meta")
        total_chunks = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT file) FROM meta")
        total_files = cursor.fetchone()[0]

        cursor.execute("SELECT MIN(id), MAX(id) FROM meta")
        db_min, db_max = cursor.fetchone()

        conn.close()

        print("\n📊 Database Statistics:")
        print(f"  Total chunks: {total_chunks}")
        print(f"  Total files: {total_files}")
        print(f"  ID range: [{db_min}, {db_max}]")
    else:
        print("\n❌ Database not found")

    # FAISS stats
    if Path(INDEX_PATH).exists():
        index = faiss.read_index(INDEX_PATH)
        print(f"\n🔍 FAISS Index Statistics:")
        print(f"  Total vectors: {index.ntotal}")
        print(f"  Index type: {type(index).__name__}")
        print(f"  Dimension: {index.d}")
    else:
        print("\n❌ Index not found")

    # Sync check
    result = check_sync()
    print(f"\n🔄 Synchronization Status: {result['status'].upper()}")

    if result["status"] == "out_of_sync":
        print(f"  ⚠️  Orphaned in FAISS: {len(result['orphaned_in_faiss'])} vectors")
        print(f"  ⚠️  Missing in FAISS: {len(result['missing_in_faiss'])} vectors")
    else:
        print("  ✅ Index and database are synchronized")


def main():
    parser = argparse.ArgumentParser(
        description="Verify and repair FAISS/Database synchronization"
    )
    parser.add_argument(
        "command",
        choices=["check", "repair", "stats"],
        help="Command to execute: check=verify sync, repair=fix issues, stats=show details",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.remove()
        logger.add(sys.stderr, level="INFO")

    # Execute command
    if args.command == "check":
        result = check_sync()
        print(f"\n{'='*60}")
        print(f"Synchronization Check Results")
        print(f"{'='*60}")
        print(f"Status: {result['status'].upper()}")
        print(f"Database records: {result['db_count']}")
        print(f"FAISS vectors: {result['faiss_count']}")

        if result["status"] == "out_of_sync":
            if result["orphaned_in_faiss"]:
                print(
                    f"\n⚠️  Found {len(result['orphaned_in_faiss'])} orphaned vectors in FAISS"
                )
                print(f"   IDs: {result['orphaned_in_faiss'][:20]}")
                if len(result["orphaned_in_faiss"]) > 20:
                    print(f"   ... and {len(result['orphaned_in_faiss']) - 20} more")

            if result["missing_in_faiss"]:
                print(
                    f"\n⚠️  Found {len(result['missing_in_faiss'])} vectors in DB but missing in FAISS"
                )
                print(f"   IDs: {result['missing_in_faiss'][:20]}")
                if len(result["missing_in_faiss"]) > 20:
                    print(f"   ... and {len(result['missing_in_faiss']) - 20} more")

            print(
                "\n💡 Run 'python tools/verify_index_sync.py repair' to fix orphaned vectors"
            )
        else:
            print("\n✅ Index and database are perfectly synchronized!")

        print(f"{'='*60}\n")

        return 0 if result["status"] == "synced" else 1

    elif args.command == "repair":
        success = repair_sync()
        if success:
            print("\n✅ Synchronization repair completed successfully!")
            return 0
        else:
            print("\n❌ Repair failed - check logs for details")
            return 1

    elif args.command == "stats":
        show_stats()
        return 0


if __name__ == "__main__":
    sys.exit(main())
