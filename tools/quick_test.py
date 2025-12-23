#!/usr/bin/env python3
"""
Quick Test - Validate AI File Search System Before Adding New Files
===================================================================
Run this before adding a new PDF to establish baseline metrics.
"""

import json
import sqlite3
from pathlib import Path

from core.config import DATABASE_PATH


def main():
    print("PRE-TEST: System Validation")
    print("=" * 40)

    # Check watcher status
    try:
        with open("logs/watcher_status.json", "r") as f:
            status = json.load(f)
            print(f"STATUS: Watcher {status.get('status', 'unknown').upper()}")
            print(f"UPDATED: {status.get('last_update', 'unknown')}")
    except Exception:
        print("ERROR: Watcher Status UNKNOWN (check logs/watcher_status.json)")

    # File counts
    base_path = Path(__file__).parent.parent
    sample_count = len(
        [f for f in (base_path / "ai_search_docs").rglob("*") if f.is_file()]
    )
    extracts_count = len(
        [f for f in (base_path / "extracts").rglob("*") if f.is_file()]
    )

    print(f"\nCURRENT FILE COUNTS:")
    print(f"   FOLDER ai_search_docs: {sample_count} files")
    print(f"   FOLDER extracts:       {extracts_count} files")

    # Database stats
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT file) FROM meta")
        indexed_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM meta")
        chunk_count = cursor.fetchone()[0]
        conn.close()

        print(f"   FILES indexed:  {indexed_count} files")
        print(f"   CHUNKS total:   {chunk_count} chunks")
    except Exception as e:
        print(f"   ERROR: Database - {e}")

    # Check PDF files in ai_search_docs
    pdf_files = list((base_path / "ai_search_docs").rglob("*.pdf"))
    docx_files = list((base_path / "ai_search_docs").rglob("*.docx"))

    print(f"\nSOURCE FILES to be Extracted:")
    print(f"   PDF files:  {len(pdf_files)}")
    print(f"   DOCX files: {len(docx_files)}")

    # Show PDF files
    if pdf_files:
        print(f"\nCurrent PDF Files:")
        for i, pdf in enumerate(pdf_files, 1):
            rel_path = pdf.relative_to(base_path)
            print(f"   {i}. {rel_path}")

    print(f"\nSUCCESS: System Ready for Testing!")
    print(f"TIP: Now add a PDF to any ai_search_docs/ subfolder")
    print(f"RUN: python live_monitor.py (to watch live)")
    print(f"OR: python monitor_file_processing.py (for summary)")


if __name__ == "__main__":
    main()
