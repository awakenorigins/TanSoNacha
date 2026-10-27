#!/usr/bin/env python3
"""
Generate comments for remaining tracks using curated persona styles and 
track-specific content. Outputs JSON batch files for application.
"""
import json
import random
import time
import os
import hashlib

PERSONAS_PATH = "/root/.openclaw/workspace/TangKinhCac/scripts/amkinh-personas-opus.json"
TRACKS_PATH = "/tmp/opus_tracks.json"

def load_personas():
    with open(PERSONAS_PATH) as f:
        return json.load(f)

def load_tracks():
    with open(TRACKS_PATH) as f:
        return json.load(f)

def random_ts_past_14_days():
    now = int(time.time() * 1000)
    offset = random.randint(1 * 86400 * 1000, 14 * 86400 * 1000)
    return now - offset

def get_genre(tid):
    if "bolero" in tid: return "bolero"
    if "cai-luong" in tid: return "cailuong"  
    if "cinematic" in tid: return "cinematic"
    if "bat-khong" in tid: return "batkhong"
    if "lofi" in tid or "chill" in tid: return "lofi"
    if "edm" in tid: return "edm"
    if "ballad" in tid: return "ballad"
    if "pop" in tid: return "pop"
    if "rap" in tid or "hiphop" in tid: return "rap"
    if "thieu-nhi" in tid: return "thieunhi"
    if "wedding" in tid: return "wedding"
    if "da-" in tid: return "da"
    if "discovery" in tid: return "discovery"
    return "general"

def get_track_title_vn(slug):
    """Convert slug to readable Vietnamese-ish title."""
    return slug.replace('-', ' ').replace('da ', 'đà ').title()

def calc_targets(play):
    like_pct = random.uniform(0.08, 0.13)
    comment_pct = random.uniform(0.03, 0.06)
    return max(1, int(play * like_pct)), max(2, int(play * comment_pct))

# Genre-specific comment templates with {title} placeholder
# These will be customized per track
COMMENT_POOLS = {
    "da": {
        "general": [
            "Bài Đà series nghe powerful lắm, energy khác biệt",
            "Series Đà mỗi bài mỗi hay, không bài nào giống bài nào",
            "Nghe bài này mà thấy tinh tấn, muốn cố gắng hơn",
        ],
        "hook": [
            "có ai nghe hết series Đà chưa? bài nào hay nhất?",
            "mọi người nghe bài này lúc nào trong ngày?",
            "ai cũng thấy bài này motivational không?",
        ]
    }
}


# LEGACY_GENERATOR_DISABLED_V3
# Disabled after the 2026-07-12 site-wide comment audit. These seeders force track titles,
# reuse rigid templates, and overproduce technical/essay-like comments. Do not run.
if __name__ == "__main__":
    raise SystemExit("DISABLED: legacy comment seeder failed diversity guard. Use amkinh-daily-comment.py + amkinh-comment-quality.py")

if __name__ == "__main__":
    personas = load_personas()
    tracks = load_tracks()
    
    # Show stats
    print(f"Personas: {len(personas)}")
    print(f"Total tracks: {len(tracks)}")
    print(f"Tracks 45-64: {[t['track'].split(':')[-1] for t in tracks[45:65]]}")
