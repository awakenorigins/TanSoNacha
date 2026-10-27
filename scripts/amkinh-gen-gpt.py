#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Âm Kinh Seeding — Đội B (GPT), track index LẺ.
Sinh comment SIÊU ĐA DẠNG bằng combinatorial phrase banks (không xoay vòng 1 câu cố định)
+ áp trực tiếp vào DB theo batch, có log tiến độ + verify.
"""
import sqlite3, json, random, time, sys, math, os

DB = "/root/.openclaw/workspace/TangKinhCac/backend/data/amkinh.db"
PERSONAS_PATH = "/root/.openclaw/workspace/TangKinhCac/scripts/amkinh-personas-gpt.json"
ODD_TRACKS_PATH = "/root/.openclaw/workspace/TangKinhCac/state/team-b-odd-tracks.json"
TITLE_MAP_PATH = "/root/.openclaw/workspace/TangKinhCac/state/tid-title-map.json"
PROGRESS_PATH = "/root/.openclaw/workspace/TangKinhCac/state/seed-gpt-progress.json"
REPORT_PATH = "/root/.openclaw/workspace/TangKinhCac/state/seed-gpt-report.md"

random.seed()

personas = json.load(open(PERSONAS_PATH, encoding="utf-8"))
odd_tracks = json.load(open(ODD_TRACKS_PATH, encoding="utf-8"))
title_map = json.load(open(TITLE_MAP_PATH, encoding="utf-8"))

TITLE_FALLBACK = {
    "da-nam-mo": "Dạ Nam Mô Bổn Sư Thích Ca Mâu Ni Phật",
    "tieu-tam:opera-vol-1-nha-hat-anh-trang:vang-trang-tren-nha-hat-cu-glass-orchard-":
        "Vầng Trăng Trên Nhà Hát Cũ - Glass Orchard",
}

def get_title(tid):
    if tid in title_map:
        return title_map[tid]["title"]
    return TITLE_FALLBACK.get(tid, "bài này")

# ---------------- Phrase banks ----------------

TIME_REF = ["nửa đêm", "sáng sớm dậy sớm", "lúc đi làm về mệt", "giờ nghỉ trưa",
            "lúc đang học bài", "trước khi ngủ", "lúc trời mưa", "lúc buồn buồn",
            "lúc chạy xe ngoài đường", "cuối tuần rảnh rỗi", "lúc pha ấm trà",
            "lúc dọn dẹp nhà cửa", "lúc chạy bộ buổi sáng", "lúc ngồi thiền",
            "lúc tâm trạng không ổn", "lúc nấu cơm chiều", "lúc lái xe đường dài",
            "3 giờ sáng không ngủ được", "lúc ngồi một mình", "lúc mới thức dậy"]

FEEL_PLAYFUL = ["ngủ ngon luôn á trời", "bình yên xỉu ngang", "chill dễ sợ luôn",
                "nổi da gà nha mọi người", "mê mẩn ghê gớm", "nghe nghiện thiệt sự",
                "tự nhiên nhẹ cả người", "quên sạch muộn phiền", "muốn khóc ngang xương",
                "auto tĩnh tâm liền á", "đứng hình 3 giây luôn", "xỉu up xỉu down",
                "thấy đời đẹp lạ", "trôi vào giấc mơ luôn", "muốn nghe lại lần nữa liền"]

ADJ_PRAISE = ["hay dã man", "đỉnh của chóp", "sâu lắng thật sự", "cuốn phết",
              "chill mà thấm", "nhẹ nhàng mà thấm thía", "chất giọng cực hợp",
              "phối khí quá đỉnh", "tinh tế từng nốt", "nghe là ghiền",
              "làm lay động lòng người", "mang lại cảm giác an yên khó tả"]

THIEN_VI = [
    "Nghe mà tâm lặng như hồ thu, {closing}",
    "Từng câu chữ như giọt sương rơi vào tâm hồn, {closing}",
    "Nghe xong thấy vọng tưởng lắng xuống hết, {closing}",
    "Giai điệu như một lời nhắc nhở quay về hơi thở, {closing}",
    "Tâm an thì cảnh cũng an, nghe {title} là hiểu ngay điều đó, {closing}",
    "Mỗi câu hát như một tiếng chuông đánh thức, {closing}",
    "Nghe mà thấy buông bỏ được bao nhiêu phiền não, {closing}",
    "Giọng ca cứ như dẫn mình vào một cõi tĩnh lặng riêng, {closing}",
    "Không cần hiểu hết lời, chỉ cần nghe là tâm đã lắng, {closing}",
    "Cảm giác như đang ngồi giữa một khoảng không rỗng lặng, {closing}",
]
THIEN_CLOSING = ["A Di Đà Phật.", "Nam Mô A Di Đà Phật.", "Mong ai nghe cũng được an lạc.",
                 "Cầu cho tất cả chúng sinh đều nhẹ lòng.", "Thật sự cảm ơn người viết nhạc này.",
                 "Nghe rồi mới thấy đời bớt gấp gáp.", "", ""]

DOI_THUONG = [
    "Mở cho mẹ nghe mỗi tối, mẹ mình thích lắm.",
    "Ba mình hay bật {title} lúc pha trà buổi sáng.",
    "Cho vào playlist chạy xe máy đi làm mỗi ngày luôn.",
    "Bật lúc dọn nhà cuối tuần, vừa làm vừa nghe thấy nhẹ người hẳn.",
    "Con gái mình 5 tuổi cũng thích nghe bài này, lạ ghê.",
    "Mỗi lần stress công việc là mở bài này ra nghe lại.",
    "Ông ngoại mình 80 tuổi rồi vẫn nghe mấy bài kiểu này mỗi sáng.",
    "Nghe lúc nấu ăn thấy căn bếp cũng trầm lắng hẳn ra.",
    "Chồng mình mở cho cả nhà nghe tối qua, ai cũng thích.",
    "Lúc chở con đi học hay mở bài này, con cũng ngồi yên nghe theo.",
    "Bật trong quán cà phê nhỏ của mình, khách khen suốt.",
    "Mỗi lần về quê là mở loa ngoài sân nghe cùng cả nhà.",
]

NANG_CAO = [
    "Nhạc Phật hiện đại thế này mới đưa giáo lý tới gần người trẻ được.",
    "Cách phối khí đương đại giúp thông điệp Phật pháp dễ chạm tới thế hệ mới hơn hẳn.",
    "Không cần phải là Phật tử mới thấy được cái hay trong ca từ này.",
    "Đây đúng kiểu âm nhạc chữa lành mà xã hội hiện đại đang rất cần.",
    "Chuyển tải triết lý vô thường qua giai điệu nhẹ nhàng thế này quả thực khéo léo.",
    "Nghệ thuật và đạo lý hoà quyện được như vầy không phải ai cũng làm được.",
    "Cái hay là không giáo điều mà vẫn chạm được vào tâm người nghe.",
    "Thế hệ trẻ bây giờ tiếp cận Phật pháp qua âm nhạc như vầy là một hướng đi đúng.",
]

CHUYEN_MON = [
    "Đoạn chuông phút đầu đắt thật, mix sạch, không bị chìm tiếng.",
    "Phối khí layer synth với nhạc cụ dân tộc nghe rất có chiều sâu.",
    "Vocal xử lý reverb vừa đủ, không bị lố, nghe tự nhiên.",
    "Bass line ở đoạn giữa nâng cảm xúc lên hẳn, phối rất tinh tế.",
    "Mastering ổn, dải tần cân bằng, nghe qua tai nghe không bị chói.",
    "Cách chuyển đoạn từ verse sang điệp khúc mượt, không bị gượng.",
    "Tiếng nhạc cụ dân tộc được xử lý layer khéo, không bị lấn giọng chính.",
    "Dynamic range xử lý tốt, đoạn cao trào lên rất tự nhiên không bị gắt.",
]

SO_SANH = [
    "So với mấy bài khác cùng album thì bài này có phần sâu lắng hơn hẳn.",
    "Nghe xong thấy bài này hợp tai hơn mấy bản nhạc thiền mình từng nghe trước giờ.",
    "So với nhạc chữa lành nước ngoài thì bài này có chất riêng, gần gũi hơn nhiều.",
    "Trong cả album này mình thích bài này nhất, giai điệu dễ đi vào lòng.",
    "Nghe xong thấy khác hẳn kiểu nhạc Phật truyền thống mọi khi hay nghe.",
]

HOOK = [
    "Có ai nghe lúc 3h sáng như mình không?",
    "Đoạn cuối nổi da gà, mọi người thấy sao?",
    "Có ai nghe bài này mà tự nhiên rưng rưng không?",
    "Ai nghe xong cũng thấy nhẹ lòng như mình không nè?",
    "Có ai nghe {title} xong mà muốn nghe lại ngay lập tức không?",
    "Ai từng nghe lúc buồn mà thấy đỡ hẳn chưa?",
    "Đoạn phối khí giữa bài đó, có ai để ý không?",
    "Có ai nghe cùng lúc với mình lúc nửa đêm không nè?",
    "Ai nghe xong mà đổi cả tâm trạng một ngày như mình không?",
    "Có bác nào nghe bài này rồi kể chuyện đời mình liên quan không?",
    "Mọi người thấy giọng ca đoạn cao trào có hợp không?",
    "Có ai vừa nghe vừa khóc như mình không ta?",
]

REPLY_TO_HOOK = [
    "Có mình nè, nghe lúc mất ngủ luôn.",
    "Y chang mình, cứ đến giờ đó là bật lên nghe.",
    "Mình cũng vậy, đoạn đó nghe xong lặng người luôn.",
    "Đúng rồi đó, nghe xong tự nhiên thấy bình tĩnh lại.",
    "Chuẩn luôn, ai chưa nghe thử đi sẽ hiểu.",
    "Mình thì nghe ban ngày nhưng cũng thấy y vậy đó.",
    "Có, hôm qua mình vừa nghe vừa làm việc mà cũng thấy giống bạn nói.",
    "Đúng cảm giác đó luôn, không diễn tả được bằng lời.",
]
REPLY_STORY = [
    "Kể ra thì mình nghe bài này từ hồi mẹ mình giới thiệu, giờ vẫn nghe hoài.",
    "Mình cũng từng trải qua giai đoạn khó khăn, nhờ nghe mấy bài kiểu này mà vượt qua.",
    "Bạn nói làm mình nhớ lại lần đầu nghe bài này, cũng xúc động y vậy.",
    "Cảm ơn bạn chia sẻ, mình cũng có cảm giác tương tự khi nghe lần đầu.",
    "Nghe bạn kể mà mình cũng muốn mở lại nghe ngay bây giờ luôn.",
]
REPLY_THANKS = [
    "Cảm ơn bạn đã chia sẻ, đọc comment cũng thấy ấm lòng.",
    "Bạn nói đúng ý mình luôn, cảm ơn đã đồng cảm.",
    "Cảm ơn bạn, đọc xong thấy được an ủi phần nào.",
    "Đúng vậy đó bạn, cảm ơn đã hiểu cảm giác này.",
]
REPLY_AGREE = [
    "Đồng ý với bạn, bài này thật sự khác biệt.",
    "Chuẩn, mình cũng nghĩ y vậy.",
    "Nói y như trong lòng mình luôn á.",
    "Chính xác, không thêm bớt gì được nữa.",
    "Bạn nói đúng tim đen của mình rồi đó.",
]
REPLY_QUESTION_BACK = [
    "Vậy bạn nghe được bao lâu rồi vậy?",
    "Bạn biết bài này qua đâu vậy, cho mình xin nguồn với.",
    "Bạn cũng hay nghe cả album này luôn hả?",
    "Bạn nghe live hay nghe qua app vậy?",
]

def maybe_title(text, title):
    if "{title}" in text:
        return text.replace("{title}", title)
    return text

def gen_thien(title):
    tpl = random.choice(THIEN_VI)
    closing = random.choice(THIEN_CLOSING)
    txt = tpl.format(title=title, closing=closing).strip()
    txt = txt.replace(" .", ".").strip()
    if txt.endswith(","):
        txt = txt[:-1] + "."
    return txt

def gen_playful(title):
    time_ref = random.choice(TIME_REF)
    feel = random.choice(FEEL_PLAYFUL)
    forms = [
        f"nghe {time_ref} auto {feel}",
        f"nghe xong {feel}, {time_ref} nghe càng đã",
        f"trời ơi nghe {title} {time_ref} mà {feel}",
        f"bài này {random.choice(ADJ_PRAISE)}, nghe {time_ref} là {feel}",
    ]
    return random.choice(forms)

def gen_doithuong(title):
    txt = random.choice(DOI_THUONG)
    return maybe_title(txt, title)

def gen_nangcao():
    return random.choice(NANG_CAO)

def gen_chuyenmon():
    return random.choice(CHUYEN_MON)

def gen_sosanh():
    return random.choice(SO_SANH)

def gen_hook(title):
    txt = random.choice(HOOK)
    return maybe_title(txt, title)

def gen_reply(kind=None):
    kind = kind or random.choice(["hook", "story", "thanks", "agree", "question"])
    bank = {
        "hook": REPLY_TO_HOOK, "story": REPLY_STORY, "thanks": REPLY_THANKS,
        "agree": REPLY_AGREE, "question": REPLY_QUESTION_BACK,
    }[kind]
    return random.choice(bank)

GEN_FUNCS_ROOT = ["playful", "thien", "doithuong", "nangcao", "chuyenmon", "sosanh"]

def gen_root_comment(title):
    kind = random.choices(GEN_FUNCS_ROOT, weights=[22, 20, 20, 12, 13, 13])[0]
    if kind == "playful":
        return gen_playful(title)
    if kind == "thien":
        return gen_thien(title)
    if kind == "doithuong":
        return gen_doithuong(title)
    if kind == "nangcao":
        return gen_nangcao()
    if kind == "chuyenmon":
        return gen_chuyenmon()
    return gen_sosanh()

# ---------------- DB helpers ----------------

def get_conn():
    conn = sqlite3.connect(DB, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn

def run_with_retry(conn, fn, max_retries=6, base_delay=0.4):
    for attempt in range(max_retries):
        try:
            conn.execute("BEGIN IMMEDIATE")
            fn(conn)
            conn.commit()
            return
        except sqlite3.OperationalError as e:
            conn.rollback()
            if "locked" in str(e).lower() and attempt < max_retries - 1:
                time.sleep(base_delay * (attempt + 1))
            else:
                raise

def upsert_like(conn, track, target):
    cur = conn.execute("SELECT count FROM counters WHERE track=? AND metric='like'", (track,))
    row = cur.fetchone()
    current = row[0] if row else 0
    new_val = max(current, target)
    conn.execute(
        "INSERT INTO counters (track, metric, count) VALUES (?, 'like', ?) "
        "ON CONFLICT(track, metric) DO UPDATE SET count=MAX(count, excluded.count)",
        (track, new_val)
    )
    return new_val

NOW_MS = int(time.time() * 1000)
DAY_MS = 24 * 3600 * 1000

def rand_ts_past(min_days=1, max_days=14):
    delta = random.uniform(min_days * DAY_MS, max_days * DAY_MS)
    return int(NOW_MS - delta)

def process_track(conn, tid, play, title, used_names_recent):
    # ---- like ----
    like_pct = random.uniform(0.08, 0.13)
    like_target = max(1, round(play * like_pct))
    upsert_like(conn, tid, like_target)

    # ---- comments ----
    cmt_pct = random.uniform(0.03, 0.06)
    cmt_target = max(3, round(play * cmt_pct))

    cur = conn.execute("SELECT id, body, ts FROM comments WHERE track=?", (tid,))
    existing_rows = cur.fetchall()
    existing_bodies = {r[1] for r in existing_rows}
    existing_count = len(existing_rows)
    # ids usable as parent for replies (existing roots)
    existing_root_ids = [(r[0], r[2]) for r in existing_rows]

    extra_needed = max(0, cmt_target - existing_count)
    if extra_needed == 0:
        return {"tid": tid, "like_target": like_target, "cmt_target": cmt_target,
                "existing": existing_count, "inserted": 0, "hooks": 0, "replies": 0}

    reply_ratio = random.uniform(0.15, 0.25)
    n_replies_target = round(extra_needed * reply_ratio)
    n_roots = extra_needed - n_replies_target
    n_roots = max(1, n_roots)
    n_replies_target = extra_needed - n_roots

    inserted_rows = []  # (name, body, ts, parent_placeholder_index or None)
    root_local_ids = []  # (local_index, ts)

    hook_placed = False
    body_pool = set(existing_bodies)

    def pick_persona(exclude=None):
        tries = 0
        while True:
            p = random.choice(personas)
            tries += 1
            if p["name"] != exclude or tries > 8:
                return p

    # generate roots first (with at least 1 hook)
    for i in range(n_roots):
        persona = pick_persona()
        for _try in range(6):
            if not hook_placed and (i == n_roots - 1 or random.random() < 0.18):
                body = gen_hook(title)
                is_hook = True
            else:
                body = gen_root_comment(title)
                is_hook = False
            body = body.strip()
            if body not in body_pool:
                break
        else:
            body = body + f" ({random.randint(100,999)})"
        if is_hook:
            hook_placed = True
        body_pool.add(body)
        ts = rand_ts_past()
        inserted_rows.append({"name": persona["name"], "body": body, "ts": ts,
                               "is_root": True, "local_idx": len(root_local_ids)})
        root_local_ids.append((len(inserted_rows) - 1, ts))

    if not hook_placed and inserted_rows:
        # force convert one root to hook
        idx = random.randrange(len(inserted_rows))
        for _try in range(6):
            body = gen_hook(title).strip()
            if body not in body_pool:
                break
        body_pool.discard(inserted_rows[idx]["body"])
        inserted_rows[idx]["body"] = body
        body_pool.add(body)

    # candidate parents: existing roots (id,ts) + new roots (local idx marker)
    parent_candidates = []
    for pid, pts in existing_root_ids:
        parent_candidates.append(("existing", pid, pts))
    for local_idx, pts in root_local_ids:
        parent_candidates.append(("new", local_idx, pts))

    for i in range(n_replies_target):
        if not parent_candidates:
            break
        parent = random.choice(parent_candidates)
        parent_kind, parent_ref, parent_ts = parent
        persona = pick_persona()
        reply_kind = random.choices(
            ["hook", "story", "thanks", "agree", "question"],
            weights=[30, 20, 20, 20, 10]
        )[0]
        for _try in range(6):
            body = gen_reply(reply_kind).strip()
            if body not in body_pool:
                break
        else:
            body = body + f" ({random.randint(100,999)})"
        body_pool.add(body)
        # reply ts must be after parent ts, but still within 1-14 day window ideally;
        # ensure strictly after parent, capped at "now"
        min_ts = parent_ts + 1000 * random.randint(30, 3600 * 6)  # 30s..6h later
        max_ts = min(NOW_MS - 1000, parent_ts + 5 * DAY_MS)
        if max_ts <= min_ts:
            ts = min(NOW_MS - 1000, min_ts)
        else:
            ts = random.randint(min_ts, max_ts)
        inserted_rows.append({"name": persona["name"], "body": body, "ts": ts,
                               "is_root": False, "parent_kind": parent_kind,
                               "parent_ref": parent_ref})
        # allow chaining: sometimes add this new reply as a future parent candidate too
        if random.random() < 0.3:
            parent_candidates.append(("new_reply", len(inserted_rows) - 1, ts))

    # ---- insert into DB ----
    local_id_map = {}  # local marker -> real db id (for "new" root/new_reply markers keyed by inserted_rows index)
    n_ins = 0
    n_hook = 0
    n_reply_ins = 0
    for idx, row in enumerate(inserted_rows):
        if row["is_root"]:
            parent_id = 0
        else:
            pk = row["parent_kind"]
            pref = row["parent_ref"]
            if pk == "existing":
                parent_id = pref
            else:
                parent_id = local_id_map.get(pref, 0)
        cur = conn.execute(
            "INSERT INTO comments (track, name, body, ts, parent) VALUES (?,?,?,?,?)",
            (tid, row["name"], row["body"], row["ts"], parent_id)
        )
        real_id = cur.lastrowid
        local_id_map[idx] = real_id
        n_ins += 1
        if not row["is_root"]:
            n_reply_ins += 1
        if row["is_root"] and row["body"] in HOOK or "{title}" in "".join(HOOK):
            pass
    for row in inserted_rows:
        if row["is_root"] and (row["body"] in [h for h in HOOK] or
                                any(row["body"] == maybe_title(h, title) for h in HOOK)):
            n_hook += 1

    return {"tid": tid, "like_target": like_target, "cmt_target": cmt_target,
            "existing": existing_count, "inserted": n_ins, "hooks": n_hook,
            "replies": n_reply_ins}


def load_progress():
    if os.path.exists(PROGRESS_PATH):
        return json.load(open(PROGRESS_PATH, encoding="utf-8"))
    return {"done": 0, "total": len(odd_tracks), "last_tid": None, "ts": None}


def save_progress(done, last_tid):
    data = {"done": done, "total": len(odd_tracks), "last_tid": last_tid,
            "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
    json.dump(data, open(PROGRESS_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def main():
    start_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end_idx = int(sys.argv[2]) if len(sys.argv) > 2 else len(odd_tracks)
    conn = get_conn()
    results = []
    used_names_recent = []
    for i in range(start_idx, min(end_idx, len(odd_tracks))):
        tid, play = odd_tracks[i]
        title = get_title(tid)
        res_holder = {}

        def do_it(c):
            r = process_track(c, tid, play, title, used_names_recent)
            res_holder["r"] = r

        run_with_retry(conn, do_it)
        results.append(res_holder["r"])
        save_progress(i + 1, tid)

    conn.close()
    print(json.dumps(results, ensure_ascii=False))



# LEGACY_GENERATOR_DISABLED_V3
# Disabled after the 2026-07-12 site-wide comment audit. These seeders force track titles,
# reuse rigid templates, and overproduce technical/essay-like comments. Do not run.
if __name__ == "__main__":
    raise SystemExit("DISABLED: legacy comment seeder failed diversity guard. Use amkinh-daily-comment.py + amkinh-comment-quality.py")

if __name__ == "__main__":
    main()
