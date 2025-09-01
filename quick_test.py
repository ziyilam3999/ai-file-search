#!/usr/bin/env python3
"""
Quick Test - Validate AI File Search System Before Adding New Files
===================================================================
Run this before adding a new PDF to establish baseline metrics.
"""

import json
import sqlite3
from pathlib import Path


def main():
    print("🧪 Pre-Test System Validation")
    print("=" * 40)

    # Check watcher status
    try:
        with open("logs/watcher_status.json", "r") as f:
            status = json.load(f)
            print(f"🟢 Watcher Status: {status.get('status', 'unknown').upper()}")
            print(f"📅 Last Update: {status.get('last_update', 'unknown')}")
    except Exception:
        print("❌ Watcher Status: UNKNOWN (check logs/watcher_status.json)")

    # File counts
    base_path = Path(__file__).parent
    sample_count = len(
        [f for f in (base_path / "sample_docs").rglob("*") if f.is_file()]
    )
    extracts_count = len(
        [f for f in (base_path / "extracts").rglob("*") if f.is_file()]
    )

    print(f"\n📊 Current File Counts:")
    print(f"   📁 sample_docs: {sample_count} files")
    print(f"   📁 extracts:    {extracts_count} files")

    # Database stats
    try:
        conn = sqlite3.connect("meta.sqlite")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT file) FROM meta")
        indexed_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM meta")
        chunk_count = cursor.fetchone()[0]
        conn.close()

        print(f"   📄 indexed:     {indexed_count} files")
        print(f"   📄 chunks:      {chunk_count} chunks")
    except Exception as e:
        print(f"   ❌ Database: Error - {e}")

    # Check PDF files in sample_docs
    pdf_files = list((base_path / "sample_docs").rglob("*.pdf"))
    docx_files = list((base_path / "sample_docs").rglob("*.docx"))

    print(f"\n📄 Source Files to be Extracted:")
    print(f"   🔴 PDF files:  {len(pdf_files)}")
    print(f"   🔵 DOCX files: {len(docx_files)}")

    # Show PDF files
    if pdf_files:
        print(f"\n📋 Current PDF Files:")
        for i, pdf in enumerate(pdf_files, 1):
            rel_path = pdf.relative_to(base_path)
            print(f"   {i}. {rel_path}")

    print(f"\n✅ System Ready for Testing!")
    print(f"💡 Now add a PDF to any sample_docs/ subfolder")
    print(f"🔍 Run: python live_monitor.py (to watch live)")
    print(f"📊 Or run: python monitor_file_processing.py (for summary)")


if __name__ == "__main__":
    main()
