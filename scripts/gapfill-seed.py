#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gapfill seeding — phủ like/comment thật cho các track Âm Kinh còn thiếu.
Đọc danh sách track thiếu, sinh like (8-13% play) + comment (3-6% play, 15-25% reply)
với persona đa dạng (60 nick), apply trực tiếp vào SQLite bằng transaction ngắn + retry.
"""
import sqlite3
import json
import random
import time
import os
import sys

DB_PATH = "/root/.openclaw/workspace/TangKinhCac/backend/data/amkinh.db"
PERSONAS_OPUS = "/root/.openclaw/workspace/TangKinhCac/scripts/amkinh-personas-opus.json"
PERSONAS_BASE = "/root/.openclaw/workspace/TangKinhCac/scripts/amkinh-personas.json"
TITLEMAP = "/root/.openclaw/workspace/TangKinhCac/state/tid-title-map.json"
MISSING_FILE = "/root/.openclaw/workspace/TangKinhCac/state/seed-gapfill-missing-tracks.txt"
PROGRESS_PATH = "/root/.openclaw/workspace/TangKinhCac/state/seed-gapfill-progress.json"

MAX_RETRIES = 6
RETRY_DELAY = 0.6

random.seed()  # true randomness per run, seeded by OS entropy


def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=8000")
    return conn


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_personas():
    a = load_json(PERSONAS_OPUS)
    b = load_json(PERSONAS_BASE)
    return a + b


def load_titlemap():
    return load_json(TITLEMAP)


def load_missing():
    out = []
    with open(MISSING_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            track, plays = line.split("|")
            out.append((track, int(plays)))
    return out


def humanize_slug(slug):
    return slug.replace("-", " ").strip().title()


def track_meta(track, titlemap):
    info = titlemap.get(track)
    if info:
        return info.get("title", humanize_slug(track.split(":")[-1])), info.get("album", "")
    parts = track.split(":")
    tslug = parts[-1] if parts else track
    tslug = tslug.rstrip("-")
    album_slug = parts[1] if len(parts) >= 3 else (parts[0] if parts else "")
    return humanize_slug(tslug), humanize_slug(album_slug)


def detect_genre(track):
    t = track.lower()
    if "bolero" in t:
        return "bolero"
    if "cai-luong" in t:
        return "cailuong"
    if "cinematic" in t:
        return "cinematic"
    if "bat-khong" in t:
        return "batkhong"
    if "lofi" in t or "chill" in t:
        return "lofi"
    if "edm" in t:
        return "edm"
    if "ballad" in t:
        return "ballad"
    if "pop" in t:
        return "pop"
    if "rap" in t or "hiphop" in t:
        return "rap"
    if "thieu-nhi" in t:
        return "thieunhi"
    if "wedding" in t:
        return "wedding"
    if "opera" in t:
        return "opera"
    if "jazz" in t or "lounge" in t:
        return "jazz"
    if "experimental" in t:
        return "experimental"
    if "da-" in t or t.startswith("da-"):
        return "da"
    return "general"


# ---------- Template banks (đa dạng giọng) ----------

TIME_TAGS = [
    "lúc 3h sáng", "giữa đêm khuya", "sáng sớm pha trà", "chiều tà lúc lái xe",
    "lúc dọn nhà", "giờ nghỉ trưa công ty", "lúc chạy bộ", "tối trước khi ngủ",
    "lúc học bài", "lúc code khuya", "lúc chở con đi học", "lúc nấu cơm",
]

PLAYFUL = [
    "Nghe {title} mà tự nhiên chill hẳn ra, add playlist ngủ liền 😌",
    "Ủa bài {title} nghe hay quá trời, sao giờ mới biết vậy trời",
    "Bài {title} này bro ơi nghe {time} là hết bài luôn á",
    "Nghe {title} xong tự nhiên muốn tắt đèn nằm im re",
    "Bài {title} chill vl, mình nghe 3 lần liên tục rồi đó",
    "Trời ơi {title} nghe {time} sao mà thấm dữ vậy",
    "Bài này {title} add vào playlist học bài của mình luôn, hay ghê",
    "Không ngờ {title} lại cuốn vậy, nghe xong định bụng ngủ mà tỉnh queo",
    "{title} nghe lần đầu mà nổi da gà á mọi người ơi",
    "Ai giống mình hay bật {title} lúc rửa chén không, thấy nhẹ cả người",
]

MEDITATIVE = [
    "Mỗi lần nghe {title} là mỗi lần lắng lại, tâm dịu hẳn xuống.",
    "{title} nghe xong thấy hơi thở tự chậm lại, an trong từng nốt.",
    "Ngồi thiền với {title} thấy vọng tưởng bớt hẳn, cảm ơn bài này.",
    "Nghe {title} tâm như lắng xuống một tầng, nhẹ mà sâu.",
    "{title} không ồn ào mà chạm tới chỗ tĩnh lặng nhất trong lòng.",
    "Nghe {title} rồi ngồi yên một lúc mới đứng dậy được, sâu quá.",
    "Có những bài như {title} không cần nghe kỹ lời, chỉ cần để tâm rơi vào.",
    "{title} là kiểu nhạc nghe xong không muốn nói gì thêm, chỉ muốn ngồi yên.",
]

DOISONG = [
    "Nghe {title} {time} thấy nhớ mẹ ghê, hồi nhỏ hay nghe kiểu nhạc này.",
    "Mở {title} trong lúc dọn nhà mà tự nhiên chậm tay lại, nghe cho trọn bài.",
    "{title} bật trong bếp lúc nấu ăn nghe rất hợp, cả nhà cùng nghe luôn.",
    "Đi làm về mệt, mở {title} nghe một lát là thấy nhẹ người hẳn.",
    "{title} mình hay mở cho ông bà nghe, cụ khen hay lắm.",
    "Chạy xe máy buổi tối mở {title} qua loa, đường vắng nghe càng thấm.",
    "{title} này mình để làm nhạc nền lúc pha trà buổi sáng, hợp cực.",
]

NANG_CAO = [
    "{title} cho thấy cách xử lý chất liệu Phật giáo trong âm nhạc hiện đại rất tinh tế, không gượng ép.",
    "Cái hay của {title} là không cố giảng đạo lý mà để âm thanh tự dẫn người nghe vào trạng thái tĩnh.",
    "Nghe {title} thấy rõ một hướng đi mới: đem tinh thần thiền vào bố cục âm nhạc đương đại.",
    "{title} là ví dụ tốt cho việc dung hòa yếu tố truyền thống và ngôn ngữ âm nhạc mới, không lai căng.",
    "Điểm mình thích ở {title} là sự tiết chế — biết khi nào nên im lặng, khi nào nên đầy lên.",
    "{title} cho thấy người làm nhạc hiểu rõ họ đang kể câu chuyện gì, không chỉ chạy theo giai điệu đẹp.",
]

CHUYEN_MON = [
    "Mix của {title} khá sạch, tầng bass không đè lên phần voice, nghe rõ từng lớp.",
    "Chuông trong {title} được xử lý reverb dài vừa đủ, không bị nhòe âm.",
    "Pad nền của {title} rất mượt, layer dưới hỗ trợ tốt cho phần giai điệu chính.",
    "Giọng hát trong {title} được xử lý compression nhẹ tay, giữ được chất mộc.",
    "Phối khí {title} có khoảng lặng dùng rất khéo, biết chỗ nào cần buông.",
    "Sound design của {title} có texture hạt (grain) rất tinh, nghe qua tai nghe tốt mới thấy rõ.",
    "Master của {title} loudness vừa phải, không bị nén chết dynamic như nhiều bài khác.",
]

SO_SANH = [
    "{title} nghe có màu gần với mấy bài lofi Phật giáo bên ngoài nhưng phần hòa âm đầu tư hơn hẳn.",
    "So với mấy bài trước trong album, {title} có tiết tấu chậm hơn, hợp nghe tối hơn.",
    "{title} khác hẳn phong cách quen thuộc, thử nghiệm mới nhưng vẫn giữ được chất riêng.",
    "Nghe {title} rồi quay lại nghe mấy bài cũ, thấy team này càng làm càng chắc tay.",
]

HOOK_QUESTION = [
    "Có ai nghe {title} lúc 3h sáng như mình không, sao thấy hợp thời điểm đó dữ vậy?",
    "Mọi người nghe {title} bằng tai nghe hay loa ngoài vậy, mình thấy tai nghe đã hơn nhiều.",
    "Ai cũng thấy đoạn giữa {title} hay nhất hay chỉ mình mình thấy vậy?",
    "Có ai add {title} vào playlist ngủ chưa, hiệu quả không mọi người?",
    "Nghe {title} xong ai còn nhớ nổi mình đang nghĩ gì trước đó không =))",
    "Bài {title} nghe được bao nhiêu lần rồi mọi người, mình chắc cỡ chục lần luôn.",
    "Có ai thấy {title} hợp nghe khi trời mưa không, mình thấy đúng bài luôn.",
]

REPLY_AGREE = [
    "Y chang mình luôn, đúng là thời điểm đó nghe thấm nhất.",
    "Mình cũng vậy nè, bài này cứ mở lên là dính.",
    "Đồng ý, mình nghe qua tai nghe cũng thấy hay hơn hẳn.",
    "Chuẩn luôn bạn, mình nghe cũng thấy giống vậy.",
    "Hihi mình cũng hay nghe giờ đó, trùng hợp ghê.",
    "Đúng rồi đó, đoạn đó mình cũng tua đi tua lại hoài.",
    "Cùng suy nghĩ luôn bạn ơi, bài này nghe hoài không chán.",
]

REPLY_ADD = [
    "Mình thì thấy đoạn cuối cũng hay không kém, bạn nghe kỹ lại xem.",
    "Ngoài ra mình còn hay nghe lúc học bài nữa, cũng hợp lắm.",
    "Bạn thử nghe thêm mấy bài cùng album xem, cũng chất giọng đó.",
    "Mình bổ sung thêm là phần nhạc nền cũng làm kỹ lắm đó bạn.",
    "Thêm nữa là bài này hợp nghe khi mưa, bạn thử coi.",
]

REPLY_SHORT = [
    "Đúng vậy đó bạn 🙏",
    "Hihi giống mình quá",
    "Cảm ơn bạn đã chia sẻ nha",
    "Mình cũng nghĩ vậy",
    "Chuẩn không cần chỉnh",
    "Nghe bạn nói mình lại muốn nghe lại lần nữa",
]

CATEGORY_POOLS = [PLAYFUL, MEDITATIVE, DOISONG, NANG_CAO, CHUYEN_MON, SO_SANH]
CATEGORY_WEIGHTS = [0.22, 0.20, 0.18, 0.14, 0.14, 0.12]


def pick_body(title):
    time_tag = random.choice(TIME_TAGS)
    pool = random.choices(CATEGORY_POOLS, weights=CATEGORY_WEIGHTS, k=1)[0]
    tmpl = random.choice(pool)
    return tmpl.format(title=title, time=time_tag)


def pick_hook(title):
    return random.choice(HOOK_QUESTION).format(title=title)


def pick_reply():
    r = random.random()
    if r < 0.45:
        return random.choice(REPLY_AGREE)
    elif r < 0.75:
        return random.choice(REPLY_SHORT)
    else:
        return random.choice(REPLY_ADD)


def random_ts_past_days(min_days=1, max_days=14):
    now = int(time.time() * 1000)
    offset = random.randint(min_days * 86400 * 1000, max_days * 86400 * 1000)
    return now - offset


def gen_comments_for_track(track, title, n_comments, personas, existing_bodies):
    """Generate n_comments dicts: {name, body, ts, parent_idx} (parent_idx=-1 root)."""
    comments = []
    used_bodies = set(existing_bodies)
    roots_idx = []

    n_roots = max(1, int(round(n_comments * random.uniform(0.75, 0.85))))
    n_roots = min(n_roots, n_comments)

    # ensure a hook question as one of the first roots (best-effort)
    hook_used = False

    attempts = 0
    while len(roots_idx) < n_roots and attempts < n_roots * 6 + 20:
        attempts += 1
        persona = random.choice(personas)
        if not hook_used and random.random() < 0.5:
            body = pick_hook(title)
            hook_used = True
        else:
            body = pick_body(title)
        if body in used_bodies:
            continue
        used_bodies.add(body)
        ts = random_ts_past_days()
        idx = len(comments)
        comments.append({"name": persona["name"], "body": body, "ts": ts, "parent_idx": -1})
        roots_idx.append(idx)

    # sort roots by ts ascending so replies can reference earlier ones with later ts
    roots_idx.sort(key=lambda i: comments[i]["ts"])

    n_replies_target = n_comments - len(roots_idx)
    reply_attempts = 0
    while len(comments) < n_comments and reply_attempts < n_replies_target * 6 + 20 and roots_idx:
        reply_attempts += 1
        parent_local_idx = random.choice(roots_idx)
        parent_ts = comments[parent_local_idx]["ts"]
        persona = random.choice(personas)
        body = pick_reply()
        if body in used_bodies:
            # allow repeated short replies but keep uniqueness for track-level dedupe requirement
            # use a small variation
            body = body + " 🙏" if not body.endswith("🙏") else body + "."
            if body in used_bodies:
                continue
        used_bodies.add(body)
        ts = parent_ts + random.randint(3600 * 1000, 3 * 86400 * 1000)  # sau cha vài giờ tới vài ngày
        comments.append({
            "name": persona["name"], "body": body, "ts": ts,
            "parent_idx": parent_local_idx,
        })

        # occasional 2nd-level reply (reply to a reply) for 3-tier conversation
        if random.random() < 0.25 and len(comments) < n_comments:
            persona2 = random.choice(personas)
            body2 = pick_reply()
            if body2 not in used_bodies:
                used_bodies.add(body2)
                ts2 = ts + random.randint(1800 * 1000, 2 * 86400 * 1000)
                comments.append({
                    "name": persona2["name"], "body": body2, "ts": ts2,
                    "parent_idx": len(comments) - 1,
                })

    return comments[:n_comments]


def upsert_like(conn, track, target_likes):
    conn.execute(
        "INSERT INTO counters (track, metric, count) VALUES (?, 'like', ?) "
        "ON CONFLICT(track, metric) DO UPDATE SET count=MAX(count, excluded.count)",
        (track, target_likes),
    )


def get_existing_comment_bodies(conn, track):
    cur = conn.execute("SELECT body FROM comments WHERE track=?", (track,))
    return {r[0] for r in cur.fetchall()}


def get_existing_comment_count(conn, track):
    cur = conn.execute("SELECT COUNT(*) FROM comments WHERE track=?", (track,))
    return cur.fetchone()[0]


def insert_comment(conn, track, name, body, ts, parent=0):
    cur = conn.execute(
        "INSERT INTO comments (track, name, body, ts, parent) VALUES (?, ?, ?, ?, ?)",
        (track, name, body, ts, parent),
    )
    return cur.lastrowid


def apply_track(conn, track, plays, title, personas):
    like_pct = random.uniform(0.08, 0.13)
    target_likes = max(1, int(round(plays * like_pct)))

    cmt_pct = random.uniform(0.03, 0.06)
    target_comments = max(1, int(round(plays * cmt_pct)))

    for attempt in range(MAX_RETRIES):
        try:
            conn.execute("BEGIN IMMEDIATE")
            upsert_like(conn, track, target_likes)

            existing_count = get_existing_comment_count(conn, track)
            need = max(0, target_comments - existing_count)

            inserted = 0
            replies_inserted = 0
            if need > 0:
                existing_bodies = get_existing_comment_bodies(conn, track)
                gen = gen_comments_for_track(track, title, need, personas, existing_bodies)

                local_idx_to_id = {}
                # insert roots first (parent_idx == -1), preserving generation order by ts within roots
                for i, c in enumerate(gen):
                    if c["parent_idx"] == -1:
                        cid = insert_comment(conn, track, c["name"], c["body"], c["ts"], 0)
                        local_idx_to_id[i] = cid
                        inserted += 1
                # then replies (may reference other replies too, so process in original order,
                # multiple passes not needed since parent_idx always points to earlier index)
                for i, c in enumerate(gen):
                    if c["parent_idx"] != -1:
                        parent_id = local_idx_to_id.get(c["parent_idx"], 0)
                        cid = insert_comment(conn, track, c["name"], c["body"], c["ts"], parent_id)
                        local_idx_to_id[i] = cid
                        inserted += 1
                        replies_inserted += 1

            conn.commit()
            return {
                "track": track, "target_likes": target_likes,
                "target_comments": target_comments, "existing_before": existing_count,
                "inserted": inserted, "replies_inserted": replies_inserted,
                "like_pct": round(like_pct * 100, 2), "cmt_pct": round(cmt_pct * 100, 2),
            }
        except sqlite3.OperationalError as e:
            try:
                conn.rollback()
            except Exception:
                pass
            if "locked" in str(e).lower() and attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                raise
    raise RuntimeError(f"Failed to apply track {track} after retries")


def load_progress():
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"done_tracks": [], "total": 0, "results": []}


def save_progress(prog):
    os.makedirs(os.path.dirname(PROGRESS_PATH), exist_ok=True)
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump(prog, f, indent=2, ensure_ascii=False)


def main():
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    max_batches = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    personas = load_personas()
    titlemap = load_titlemap()
    missing = load_missing()

    prog = load_progress()
    prog["total"] = len(missing)
    done_set = set(prog.get("done_tracks", []))

    remaining = [(t, p) for t, p in missing if t not in done_set]
    print(f"Remaining tracks to process: {len(remaining)} / {len(missing)}", flush=True)

    conn = get_conn()
    batches_done = 0
    try:
        for batch_start in range(0, len(remaining), batch_size):
            if batches_done >= max_batches:
                break
            batch = remaining[batch_start:batch_start + batch_size]
            if not batch:
                break
            batch_results = []
            for track, plays in batch:
                title, album = track_meta(track, titlemap)
                res = apply_track(conn, track, plays, title, personas)
                batch_results.append(res)
                prog["done_tracks"].append(track)
                done_set.add(track)
                print(f"OK {track} plays={plays} likes={res['target_likes']} "
                      f"cmts+={res['inserted']} (replies={res['replies_inserted']}) "
                      f"like%={res['like_pct']} cmt%={res['cmt_pct']}", flush=True)
            prog["results"].extend(batch_results)
            prog["last_batch_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            save_progress(prog)
            batches_done += 1
            print(f"--- batch {batches_done} done, {len(prog['done_tracks'])}/{len(missing)} total ---", flush=True)
    finally:
        conn.close()

    print(f"Session complete. Total done so far: {len(prog['done_tracks'])}/{len(missing)}", flush=True)



# LEGACY_GENERATOR_DISABLED_V3
# Disabled after the 2026-07-12 site-wide comment audit. These seeders force track titles,
# reuse rigid templates, and overproduce technical/essay-like comments. Do not run.
if __name__ == "__main__":
    raise SystemExit("DISABLED: legacy comment seeder failed diversity guard. Use amkinh-daily-comment.py + amkinh-comment-quality.py")

if __name__ == "__main__":
    main()
