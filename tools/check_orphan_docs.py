#!/usr/bin/env python3
"""Check for orphaned documents in the index that don't belong to any watch path."""

import sqlite3
from pathlib import Path

import yaml

# Load config
config_path = Path("prompts/watcher_config.yaml")
with open(config_path) as f:
    config = yaml.safe_load(f)

watch_paths = config.get("watch_paths", [])
print(f"Current watch paths: {watch_paths}")

# Connect to DB
conn = sqlite3.connect("meta.sqlite")
cursor = conn.cursor()

# Get all unique file paths
cursor.execute("SELECT DISTINCT file FROM meta")
all_files = [row[0] for row in cursor.fetchall()]
print(f"\nTotal unique files in index: {len(all_files)}")

# Normalize watch paths for comparison
normalized_watch = []
for wp in watch_paths:
    # Convert to forward slashes and resolve
    norm = wp.replace("\\", "/")
    if not norm.startswith("C:/") and not norm.startswith("/"):
        # Relative path
        norm = str(Path(wp).resolve()).replace("\\", "/")
    normalized_watch.append(norm)

print(f"Normalized watch paths: {normalized_watch}")

# Find orphaned files
orphaned = []
for file_path in all_files:
    # Skip confluence URLs
    if file_path.startswith("confluence://"):
        continue

    is_watched = False
    for wp in normalized_watch:
        if file_path.startswith(wp):
            is_watched = True
            break

    if not is_watched:
        orphaned.append(file_path)

print(f"\nOrphaned files (not in any watch path): {len(orphaned)}")
if orphaned:
    print("\nSample orphaned files:")
    for f in orphaned[:10]:
        print(f"  - {f}")

# Count chunks for orphaned files
if orphaned:
    cursor.execute("SELECT COUNT(*) FROM meta WHERE file NOT LIKE 'confluence://%'")
    total_non_confluence = cursor.fetchone()[0]

    # Count orphaned chunks
    orphan_count = 0
    for f in orphaned:
        cursor.execute("SELECT COUNT(*) FROM meta WHERE file = ?", (f,))
        orphan_count += cursor.fetchone()[0]

    print(f"\nTotal non-confluence chunks: {total_non_confluence}")
    print(f"Orphaned chunks: {orphan_count}")

conn.close()
