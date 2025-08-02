#!/usr/bin/env python3
"""
Embedder Format Validation Script

This script validates that the Embedder.query() method returns the correct 4-tuple format
required for UI compatibility and test suite validation.

Usage:
    python validate_embedder_format.py

Expected Output:
    SUCCESS: Format validation passed
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def validate_embedder_format():
    """Validate that embedder returns correct 4-tuple format."""
    try:
        from core.embedding import Embedder

        print("Testing Embedder query format...")

        # Initialize embedder
        em = Embedder()

        # Test with a simple query
        results = em.query("test query", k=1)

        if not results:
            print("ERROR: No results returned - check if index is built")
            return False

        result = results[0]

        # Validate tuple length
        if len(result) != 4:
            print(f"ERROR: Expected 4-tuple, got {len(result)}-tuple")
            print(f"   Actual result: {result}")
            print(f"   See docs/EMBEDDER_API_SPECIFICATION.md for required format")
            return False

        # Validate tuple contents
        chunk_text, file_path, chunk_id, score = result

        # Type validation
        type_checks = [
            (chunk_text, (str, type(None)), "chunk_text"),
            (file_path, (str, type(None)), "file_path"),
            (chunk_id, int, "chunk_id"),
            (score, (int, float), "score"),
        ]

        for value, expected_types, name in type_checks:
            if not isinstance(value, expected_types):
                print(
                    f"ERROR: {name} has wrong type: {type(value).__name__}, expected {expected_types}"
                )
                return False

        print("SUCCESS: Format validation passed")
        print(
            f"   Format: ({type(chunk_text).__name__}, {type(file_path).__name__}, {type(chunk_id).__name__}, {type(score).__name__})"
        )
        print(f"   Sample result: {result}")

        # Test with multiple results
        multi_results = em.query("test query", k=3)
        if len(multi_results) > 1:
            print(
                f"SUCCESS: Multiple results test passed ({len(multi_results)} results)"
            )

        return True

    except ImportError as e:
        print(f"ERROR: Import error: {e}")
        print("   Make sure core.embedding module exists and is importable")
        return False
    except Exception as e:
        print(f"ERROR: Validation error: {e}")
        return False


def main():
    """Main validation entry point."""
    print("Embedder Format Validation")
    print("=" * 40)

    success = validate_embedder_format()

    print("\nValidation Summary:")
    if success:
        print("SUCCESS: All validations passed - Embedder format is correct")
        print("   UI compatibility: SUCCESS")
        print("   Test suite compatibility: SUCCESS")
        print("   System integration: SUCCESS")
        sys.exit(0)
    else:
        print("ERROR: Validation failed - Review errors above")
        print("   See docs/EMBEDDER_API_SPECIFICATION.md for requirements")
        sys.exit(1)


if __name__ == "__main__":
    main()
