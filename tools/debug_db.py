#!/usr/bin/env python3
"""Debug script to check what's actually in the database."""

import sqlite3

from core.config import DATABASE_PATH

# Connect to the database
conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

# Check the target IDs
target_ids = [113, 120, 147, 150, 149]

print("=== Database Debug Info ===")
cursor.execute("SELECT COUNT(*) FROM meta")
print(f"Total rows: {cursor.fetchone()[0]}")

cursor.execute("SELECT MIN(id), MAX(id) FROM meta")
min_id, max_id = cursor.fetchone()
print(f"ID range: {min_id} to {max_id}")

print("\n=== Checking target IDs ===")
for target_id in target_ids:
    cursor.execute(
        "SELECT id, file, LENGTH(chunk) FROM meta WHERE id = ?", (target_id,)
    )
    row = cursor.fetchone()
    if row:
        print(f"ID {target_id}: file='{row[1]}', chunk_length={row[2]}")
    else:
        print(f"ID {target_id}: NOT FOUND")

print("\n=== IDs around the target range ===")
cursor.execute("SELECT id FROM meta WHERE id BETWEEN 110 AND 155 ORDER BY id")
ids = [row[0] for row in cursor.fetchall()]
print(f"IDs 110-155: {ids}")

print("\n=== First few rows ===")
cursor.execute("SELECT id, file, LENGTH(chunk) FROM meta ORDER BY id LIMIT 5")
rows = cursor.fetchall()
for row in rows:
    print(f"ID {row[0]}: file='{row[1]}', chunk_length={row[2]}")

conn.close()
