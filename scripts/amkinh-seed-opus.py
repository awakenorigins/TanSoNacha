#!/usr/bin/env python3
"""
Âm Kinh Seeding Script — Đội A (Opus)
Applies pre-generated comments JSON + upserts likes into amkinh.db
Handles: even-index tracks, dedupe, parent/reply validation, ts ordering.
"""
import sqlite3
import json
import sys
import os
import time

DB_PATH = "/root/.openclaw/workspace/TangKinhCac/backend/data/amkinh.db"
MAX_RETRIES = 5
RETRY_DELAY = 0.5

def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn

def upsert_like(conn, track, target_likes):
    """Upsert like count — never decrease existing value."""
    cur = conn.execute("SELECT count FROM counters WHERE track=? AND metric='like'", (track,))
    row = cur.fetchone()
    current = row[0] if row else 0
    new_val = max(current, target_likes)
    conn.execute(
        "INSERT INTO counters (track, metric, count) VALUES (?, 'like', ?) "
        "ON CONFLICT(track, metric) DO UPDATE SET count=MAX(count, excluded.count)",
        (track, new_val)
    )
    return new_val

def get_existing_comments(conn, track):
    """Get existing comment count and bodies for a track."""
    cur = conn.execute("SELECT id, body FROM comments WHERE track=?", (track,))
    rows = cur.fetchall()
    return {r[1] for r in rows}, len(rows)

def insert_comments(conn, track, comments_data):
    """
    Insert comments with deduplication and parent validation.
    comments_data: list of {name, body, ts, parent_idx} 
    parent_idx: -1 for root, or index in THIS batch to reply to
    Returns: number inserted
    """
    existing_bodies, existing_count = get_existing_comments(conn, track)
    
    inserted = 0
    # Map from batch index to actual DB id
    idx_to_id = {}
    
    # Sort: roots first (parent_idx == -1), then replies
    roots = [(i, c) for i, c in enumerate(comments_data) if c.get("parent_idx", -1) == -1]
    replies = [(i, c) for i, c in enumerate(comments_data) if c.get("parent_idx", -1) != -1]
    
    for i, c in roots:
        body = c["body"].strip()
        if body in existing_bodies:
            continue
        cur = conn.execute(
            "INSERT INTO comments (track, name, body, ts, parent) VALUES (?, ?, ?, ?, 0)",
            (track, c["name"], body, c["ts"])
        )
        idx_to_id[i] = cur.lastrowid
        existing_bodies.add(body)
        inserted += 1
    
    for i, c in replies:
        body = c["body"].strip()
        if body in existing_bodies:
            continue
        parent_idx = c["parent_idx"]
        parent_id = idx_to_id.get(parent_idx, 0)
        if parent_id == 0:
            # Parent wasn't inserted (maybe deduped), insert as root
            parent_id = 0
        cur = conn.execute(
            "INSERT INTO comments (track, name, body, ts, parent) VALUES (?, ?, ?, ?, ?)",
            (track, c["name"], body, c["ts"], parent_id)
        )
        idx_to_id[i] = cur.lastrowid
        existing_bodies.add(body)
        inserted += 1
    
    return inserted

def apply_batch(json_path):
    """Apply a batch JSON file to the database."""
    with open(json_path, 'r') as f:
        batch = json.load(f)
    
    conn = get_conn()
    total_comments = 0
    total_likes = 0
    
    try:
        for item in batch:
            track = item["track"]
            target_likes = item["target_likes"]
            comments = item["comments"]
            
            for attempt in range(MAX_RETRIES):
                try:
                    conn.execute("BEGIN IMMEDIATE")
                    upsert_like(conn, track, target_likes)
                    n = insert_comments(conn, track, comments)
                    conn.commit()
                    total_comments += n
                    total_likes += 1
                    break
                except sqlite3.OperationalError as e:
                    conn.rollback()
                    if "locked" in str(e).lower() and attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY * (attempt + 1))
                    else:
                        raise
    finally:
        conn.close()
    
    return total_likes, total_comments

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 amkinh-seed-opus.py <batch.json>")
        sys.exit(1)
    
    json_path = sys.argv[1]
    likes, comments = apply_batch(json_path)
    print(json.dumps({"likes_upserted": likes, "comments_inserted": comments}))
