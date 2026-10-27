#!/usr/bin/env python3
"""
Mass seeding script for Opus team — generates diverse comments based on
track metadata and applies to DB. Uses curated comment templates with 
significant variation per track.
"""
import sqlite3
import json
import random
import time
import os
import re
import hashlib

DB_PATH = "/root/.openclaw/workspace/TangKinhCac/backend/data/amkinh.db"
PERSONAS_PATH = "/root/.openclaw/workspace/TangKinhCac/scripts/amkinh-personas-opus.json"
PROGRESS_PATH = "/root/.openclaw/workspace/TangKinhCac/state/seed-opus-progress.json"
TRACKS_PATH = "/tmp/opus_tracks.json"

MAX_RETRIES = 5
RETRY_DELAY = 0.5

def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn

def load_personas():
    with open(PERSONAS_PATH) as f:
        return json.load(f)

def load_tracks():
    with open(TRACKS_PATH) as f:
        return json.load(f)

def load_progress():
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH) as f:
            return json.load(f)
    return {"done": 0, "total": 155, "last_tid": "", "batches_applied": []}

def save_progress(prog):
    os.makedirs(os.path.dirname(PROGRESS_PATH), exist_ok=True)
    with open(PROGRESS_PATH, 'w') as f:
        json.dump(prog, f, indent=2, ensure_ascii=False)

def extract_track_info(tid):
    """Extract album and track name from tid for contextual comments."""
    parts = tid.split(':')
    if len(parts) >= 3:
        album_slug = parts[1]
        track_slug = parts[2]
    elif len(parts) == 2:
        album_slug = parts[0]
        track_slug = parts[1]
    else:
        album_slug = ""
        track_slug = tid
    
    # Humanize slugs
    track_name = track_slug.replace('-', ' ').title()
    album_name = album_slug.replace('-', ' ').title()
    
    # Detect genre from album
    genre = "general"
    if "bolero" in album_slug: genre = "bolero"
    elif "cai-luong" in album_slug: genre = "cailuong"
    elif "cinematic" in album_slug: genre = "cinematic"
    elif "bat-khong" in album_slug: genre = "batkhong"
    elif "lofi" in album_slug or "chill" in album_slug: genre = "lofi"
    elif "edm" in album_slug: genre = "edm"
    elif "ballad" in album_slug: genre = "ballad"
    elif "pop" in album_slug: genre = "pop"
    elif "rap" in album_slug or "hiphop" in album_slug: genre = "rap"
    elif "thieu-nhi" in album_slug: genre = "thieunhi"
    elif "wedding" in album_slug: genre = "wedding"
    elif "da-" in album_slug or "da-" in tid: genre = "da"
    elif "discovery" in album_slug: genre = "discovery"
    
    return {
        "tid": tid,
        "album_slug": album_slug,
        "track_slug": track_slug,
        "track_name": track_name,
        "album_name": album_name,
        "genre": genre
    }

def random_ts_past_14_days():
    """Random timestamp 1-14 days in the past (ms)."""
    now = int(time.time() * 1000)
    offset = random.randint(1 * 86400 * 1000, 14 * 86400 * 1000)
    return now - offset

def upsert_like(conn, track, target_likes):
    conn.execute(
        "INSERT INTO counters (track, metric, count) VALUES (?, 'like', ?) "
        "ON CONFLICT(track, metric) DO UPDATE SET count=MAX(count, excluded.count)",
        (track, target_likes)
    )

def get_existing_comments(conn, track):
    cur = conn.execute("SELECT body FROM comments WHERE track=?", (track,))
    return {r[0] for r in cur.fetchall()}

def get_existing_comment_count(conn, track):
    cur = conn.execute("SELECT COUNT(*) FROM comments WHERE track=?", (track,))
    return cur.fetchone()[0]

def insert_comment(conn, track, name, body, ts, parent=0):
    cur = conn.execute(
        "INSERT INTO comments (track, name, body, ts, parent) VALUES (?, ?, ?, ?, ?)",
        (track, name, body, ts, parent)
    )
    return cur.lastrowid

def apply_pregenerated_batch(json_path):
    """Apply a pre-generated JSON batch from the agent."""
    with open(json_path) as f:
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
                    
                    existing_bodies = get_existing_comments(conn, track)
                    idx_to_id = {}
                    
                    # Roots first
                    roots = [(i, c) for i, c in enumerate(comments) if c.get("parent_idx", -1) == -1]
                    replies = [(i, c) for i, c in enumerate(comments) if c.get("parent_idx", -1) != -1]
                    
                    for i, c in roots:
                        body = c["body"].strip()
                        if body in existing_bodies:
                            continue
                        cid = insert_comment(conn, track, c["name"], body, c["ts"], 0)
                        idx_to_id[i] = cid
                        existing_bodies.add(body)
                        total_comments += 1
                    
                    for i, c in replies:
                        body = c["body"].strip()
                        if body in existing_bodies:
                            continue
                        parent_idx = c["parent_idx"]
                        parent_id = idx_to_id.get(parent_idx, 0)
                        cid = insert_comment(conn, track, c["name"], body, c["ts"], parent_id)
                        idx_to_id[i] = cid
                        existing_bodies.add(body)
                        total_comments += 1
                    
                    conn.commit()
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
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 opus-mass-seed.py <batch.json>")
        sys.exit(1)
    
    likes, comments = apply_pregenerated_batch(sys.argv[1])
    print(json.dumps({"likes_upserted": likes, "comments_inserted": comments}))
