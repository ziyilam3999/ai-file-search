#!/usr/bin/env python3
"""Check path differences between database and filesystem."""

import sqlite3
from pathlib import Path

from core.config import DATABASE_PATH

print("=== DATABASE PATHS (first 10) ===")
conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()
cursor.execute("SELECT DISTINCT file FROM meta ORDER BY file")
indexed_files = [row[0] for row in cursor.fetchall()]
conn.close()

for i, file in enumerate(indexed_files[:10], 1):
    print(f'{i:2d}. "{file}"')

print("\n=== FILESYSTEM PATHS (ai_search_docs, first 10) ===")
filesystem_files = []
for file_path in Path("ai_search_docs").rglob("*.txt"):
    filesystem_files.append(str(file_path))

for i, file in enumerate(sorted(filesystem_files)[:10], 1):
    print(f'{i:2d}. "{file}"')

print("\n=== PATH ANALYSIS ===")
print(f"Database files: {len(indexed_files)}")
print(f"Filesystem files (txt only): {len(filesystem_files)}")

# Check if database paths match filesystem
db_basenames = {Path(f).name for f in indexed_files}
fs_basenames = {Path(f).name for f in filesystem_files}

print(f"\nMatching filenames: {len(db_basenames & fs_basenames)}")
print(f"Database only: {len(db_basenames - fs_basenames)}")
print(f"Filesystem only: {len(fs_basenames - db_basenames)}")

print("\nSample paths comparison:")
if indexed_files:
    print(f"DB path format: '{indexed_files[0]}'")
if filesystem_files:
    print(f"FS path format: '{filesystem_files[0]}'")

print("\n=== THE 58.2% COVERAGE ISSUE ===")
print("The issue is likely a PATH MISMATCH:")
print("- Database stores paths like: 'classic_literature\\file.txt'")
print("- File system has paths like: 'ai_search_docs\\classic_literature\\file.txt'")
print("- The watcher might be indexing from a different base directory")
print("\nTo fix this, you need to:")
print("1. Check watcher configuration for correct base paths")
print("2. Possibly re-index files with correct paths")
print("3. Or update the monitoring script to handle path differences")
