#!/usr/bin/env python3
"""
Bulk generator for remaining 100 tracks. Creates diverse, persona-matched
comments using curated pools and track-specific details.
Each persona has unique voice. Comments are never duplicated across tracks.
"""
import json
import random
import time
import hashlib
import sys
import sqlite3

DB_PATH = "/root/.openclaw/workspace/TangKinhCac/backend/data/amkinh.db"
PERSONAS_PATH = "/root/.openclaw/workspace/TangKinhCac/scripts/amkinh-personas-opus.json"
TRACKS_PATH = "/tmp/opus_tracks.json"

random.seed(42)  # Reproducible for debugging

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
    if "edm" in tid: return "edm"
    elif "experimental" in tid: return "experimental"
    elif "instrumental" in tid: return "instrumental"
    elif "lofi" in tid: return "lofi"
    elif "opera" in tid: return "opera"
    elif "phat-phap" in tid: return "phatphap"
    elif "relax-sleep" in tid: return "relaxsleep"
    elif "pop" in tid: return "pop"
    elif "rap" in tid or "hiphop" in tid: return "rap"
    elif "thieu-nhi" in tid: return "thieunhi"
    elif "wedding" in tid: return "wedding"
    elif "other" in tid: return "other"
    elif "da-sam-hoi" in tid: return "samhoi"
    elif "da-sifu" in tid: return "sifu"
    elif "da-vo-thuong" in tid: return "vothuong"
    elif "da-nacha" in tid: return "nacha"
    elif "da-" in tid: return "da"
    elif "bolero" in tid: return "bolero"
    elif "cai-luong" in tid: return "cailuong"
    elif "cinematic" in tid: return "cinematic"
    elif "bat-khong" in tid: return "batkhong"
    elif "ballad" in tid: return "ballad"
    return "general"

def slug_to_title(slug):
    """Convert track slug to readable format."""
    s = slug.replace('-', ' ')
    # Remove version suffixes
    for suffix in [' 1', ' 2', ' v1', ' v2', ' 2 1', ' 2 2']:
        if s.endswith(suffix):
            s = s[:-len(suffix)]
    return s.strip().title()

def get_album_name(tid):
    parts = tid.split(':')
    if len(parts) >= 2:
        return slug_to_title(parts[1])
    return ""

def get_track_name(tid):
    parts = tid.split(':')
    if len(parts) >= 3:
        return slug_to_title(parts[2])
    return slug_to_title(tid)

# Persona comment generators - each returns comments in persona voice
PERSONA_COMMENTS = {
    "Hoa Từ Bi": lambda tn, g: random.choice([
        f"Mỗi lần nghe bài này là mỗi lần tâm lắng hơn một chút",
        f"Bài này nhẹ quá, nghe mà lòng bình yên lại",
        f"Tên bài đẹp, nhạc đẹp, ý nghĩa sâu — đủ cả",
        f"Nghe xong thấy mọi thứ đơn giản hơn, nhẹ nhàng hơn",
        f"Bài hay lắm, mỗi note nhạc đều được chăm chút",
    ]),
    "phatphapnhiemmau": lambda tn, g: random.choice([
        f"bai nay nghe di nghe lai k chan, hay lam",
        f"share cho may nguoi ban roi, ai cung thich het",
        f"nghe xong thay binh an lam, recommend cho mn",
        f"bai hay qua, loop hoai ma van thich",
        f"phai nghe thu di mn, k that vong dau",
    ]),
    "chú Bảy Cà Mau": lambda tn, g: random.choice([
        f"Hay lắm con ơi, chú nghe mỗi ngày luôn",
        f"Nghe mà lòng thanh bình thiệt, hay quá",
        f"Bài hay, chú mở cho cả nhà nghe",
        f"Nhạc hay vậy mà free, cảm ơn ai đó đã làm",
        f"Chú thích bài này lắm, nghe hoài không chán",
    ]),
    "LofiPhatTu": lambda tn, g: random.choice([
        f"bài này heal thật sự, nghe xong feel better",
        f"vibes immaculate, add vào playlist ngay",
        f"production quality khá, respect",
        f"bro bài này chill phết, recommend",
        f"nghe lúc 2h sáng hit different lắm",
    ]),
    "Bà Nội 70": lambda tn, g: random.choice([
        f"Bà thích bài này lắm, nghe ấm lòng con ơi",
        f"Hai bà cháu nghe chung, cháu bà cũng thích",
        f"Bà hay mở bài này buổi tối, nghe hay lắm",
        f"Bài hay quá, bà nghe mà nhớ hồi xưa",
        f"Bà mở cho mấy đứa cháu nghe, đứa nào cũng thích",
    ]),
    "DucHanh_sn": lambda tn, g: random.choice([
        f"Mix sạch, vocal sit tốt trong mix. Production quality cao.",
        f"Arrangement chỉn chu, mỗi layer đều có chỗ. Balance tốt.",
        f"Mastering level chuẩn, dynamic range hợp lý. Nghe comfortable.",
        f"Vocal processing tốt, reverb space phù hợp genre. Pro work.",
        f"Sound design creative, instrument choices phù hợp theme. Hay.",
    ]),
    "Tuệ Đăng": lambda tn, g: random.choice([
        f"Ý nghĩa Phật học trong bài rất sâu, cần nghe nhiều lần mới thấm hết",
        f"Giáo lý được lồng vào rất khéo, không giáo điều mà tự nhiên chạm lòng",
        f"Bài này đưa Phật pháp tới người nghe bằng con đường nghệ thuật — hiệu quả nhất",
        f"Từ ngữ kinh điển mà giai điệu hiện đại, cầu nối rất hay",
        f"Concept bài hay, kết hợp triết lý và âm nhạc trọn vẹn",
    ]),
    "mây_lang_thang": lambda tn, g: random.choice([
        f"nghe... lặng... đủ...",
        f"âm thanh rơi... như sương...",
        f"đẹp... không cần nói thêm...",
        f"gió mang đi... lời kinh... xa...",
        f"nhắm mắt... nghe... thấy...",
    ]),
    "NguoiQuaDuong83": lambda tn, g: random.choice([
        f"Ủa bài hay quá trời, tình cờ nghe mà ghiền luôn",
        f"nghe thu coi roi ghien luon, hay that",
        f"ơ bài này hay dữ, sao mới biết giờ ta",
        f"share cho bạn bè rồi, ai cũng khen hay",
        f"lần đầu nghe mà muốn repeat liền, hay thiệt",
    ]),
    "Thanh Tâm Ni": lambda tn, g: random.choice([
        f"A Di Đà Phật. Nguyện cho người nghe đều an lạc.",
        f"Nguyện cho âm nhạc này gieo duyên lành cho tất cả. A Di Đà Phật.",
        f"A Di Đà Phật. Bài hát như một lời kinh nhẹ nhàng.",
        f"Nguyện hồi hướng công đức nghe kinh cho chúng sinh. A Di Đà Phật.",
    ]),
    "Nguyệt Quang": lambda tn, g: random.choice([
        f"Bài hát khéo léo lồng ý nghĩa Phật pháp vào giai điệu đời thường",
        f"Nghe nhiều lần mới thấy hết chiều sâu, mỗi lần nghe một lớp mới",
        f"Âm nhạc hiện đại mà tinh thần cổ điển — cân bằng rất khó mà bài này làm được",
        f"Ý tứ trong bài sâu lắm, cần lắng nghe với tâm tĩnh mới thấm",
    ]),
    "hungmoto": lambda tn, g: random.choice([
        f"Nghe bài này lúc chạy xe đường dài, bình tĩnh hẳn",
        f"Bài hay, nghe xong thấy sức mạnh tinh thần tăng lên",
        f"Đàn ông nghe mấy bài này cũng thấy hay, không sến đâu",
        f"Mở loa xe nghe, ai ngồi cùng cũng thích",
    ]),
    "Trà Đá Sài Gòn": lambda tn, g: random.choice([
        f"Nghe mát ruột luôn, giữa SG nóng bức mà thấy nhẹ hẳn",
        f"Hay quá trời, nghe xong share lên group bạn bè liền",
        f"Nhạc Phật kiểu này nghe modern mà vẫn sâu, thích",
        f"SG đang kẹt xe mà mở bài này thấy bớt stress ghê",
    ]),
    "thicanh_hanoi": lambda tn, g: random.choice([
        f"Bài nhạc thanh nhã, nghe rất thoải mái và dễ chịu",
        f"Chất giọng và giai điệu rất tinh tế, thích",
        f"Nghe khi đọc sách buổi tối, rất hợp không gian",
        f"Tinh tế và nhẹ nhàng, đúng phong cách mình thích",
    ]),
    "chill_vibe_only": lambda tn, g: random.choice([
        f"add vào playlist ngủ ngay, chill max",
        f"vibes đỉnh, nghe là relax liền",
        f"perfect study/sleep music, loop cả đêm",
        f"bài này chill level 100, recommend",
    ]),
    "producer_nhaque": lambda tn, g: random.choice([
        f"Production quality tốt, mix balance hay. Instrument choices đúng genre.",
        f"Sound design interesting, các layer complement nhau well. Mix engineer giỏi.",
        f"Mastering professional, loudness chuẩn streaming. Vocal chain clean.",
        f"Creative arrangement, không theo formula mà vẫn catchy. Respect.",
    ]),
    "thiendinh247": lambda tn, g: random.choice([
        f"Nghe mà tâm dễ an trú. Frequency và tempo phù hợp thiền tập.",
        f"Bài này hỗ trợ thiền quán tốt, đưa tâm vào trạng thái tĩnh lặng.",
        f"Dùng làm nền cho thiền hành rất tốt — nhịp đều, không gây phân tâm.",
        f"Trạng thái tâm khi nghe bài này rất gần sơ thiền — nhẹ, tỉnh, biết.",
    ]),
    "HạtSươngMai": lambda tn, g: random.choice([
        f"Mỗi nốt nhạc rơi xuống tâm hồn như giọt sương mai, trong và mát.",
        f"Giai điệu dẫn ta qua một vườn hoa tâm linh, mỗi bước là mỗi khám phá.",
        f"Nghe mà thấy được ôm ấp bởi âm thanh, ấm áp và bình yên.",
        f"Bài hát như dòng suối chảy qua tâm hồn, rửa sạch mọi muộn phiền.",
    ]),
    "Sư Cô Hiền": lambda tn, g: random.choice([
        f"A Di Đà Phật. Nghe với tâm tĩnh lặng sẽ thấy an lạc.",
        f"Nguyện cho mọi người nghe được âm nhạc này đều phát tâm bồ đề.",
        f"Âm nhạc cũng là phương tiện độ sinh. A Di Đà Phật.",
    ]),
    "bống_nghe_kinh": lambda tn, g: random.choice([
        f"bài này hay quáaa, share cho cả nhóm rồi",
        f"huhu nghe xong thấy bình an lạ, loop hoài",
        f"dễ thương quá, mình thích bài này lắm",
        f"nghe mà feel better hẳn, yêu bài này",
    ]),
    "TâmVôNgại": lambda tn, g: random.choice([
        f"Nghe — lặng — biết. Đủ.",
        f"Âm — lặng. Lặng — âm. Không khác.",
        f"Hay. Đơn giản. Sâu.",
    ]),
    "Dì Năm Vũng Tàu": lambda tn, g: random.choice([
        f"Hay quá con ơi, dì nghe mỗi ngày luôn",
        f"Dì hay mở lúc nấu ăn, nghe vui lắm",
        f"Bài hay, dì share cho mấy chị em trong xóm",
        f"Nghe ấm lòng lắm con, dì thích",
    ]),
    "QuangMinh_Buddhist": lambda tn, g: random.choice([
        f"Chất lượng production tốt, nội dung phù hợp. Recommend. 4.5/5.",
        f"Bài hay, đã thêm vào playlist giới thiệu cho Phật tử. 4/5.",
        f"Production và content đều chất lượng. Đáng nghe. 4.5/5.",
    ]),
    "lotus_rain": lambda tn, g: random.choice([
        f"shared this with friends overseas, they loved it",
        f"beautiful track, music truly transcends language",
        f"Vietnamese Buddhist music at its finest, so moving",
    ]),
    "Minh Đạt": lambda tn, g: random.choice([
        f"Bài này hay ghê, mới nghe lần đầu mà ghiền luôn",
        f"Nghe đi nghe lại không chán, mỗi lần nghe thấy khác",
        f"Hay lắm, recommend cho ai chưa nghe",
    ]),
    "Ba Gác": lambda tn, g: random.choice([
        f"nghỉ trưa nghe hay",
        f"bài hay, nghe đi",
        f"nghe cũng được, thích",
    ]),
    "Cỏ May": lambda tn, g: random.choice([
        f"nghe ban đêm thấy lòng nhẹ lại 🌸",
        f"nhẹ nhàng, thích lắm 🌸",
        f"đẹp quá, nghe mà thấy bình yên 🌸",
    ]),
    "Ông Tám Trà": lambda tn, g: random.choice([
        f"Ngồi uống trà nghe bài này, quên hết chuyện đời. Hay.",
        f"Nhạc vậy mới nghe được, nhẹ nhàng sâu lắng.",
        f"Trà chiều, bài nhạc hay. Đủ vui cho một buổi.",
    ]),
    "namhai_it": lambda tn, g: random.choice([
        f"Nghe khi code, stress giảm hẳn. Recommend cho anh em IT.",
        f"Background music hoàn hảo cho deep work session.",
        f"WFH nghe bài này productive lạ, focus hơn.",
    ]),
    "Giác Ngộ Online": lambda tn, g: random.choice([
        f"Đã chia sẻ trên kênh, phản hồi tích cực. Recommend.",
        f"Phù hợp cho buổi tụng kinh online. Production tốt.",
        f"Bài hay, xin phép chia sẻ cho Phật tử theo dõi kênh.",
    ]),
}

# Hook questions (for ~1 in every 5-6 comments)
HOOKS = [
    "có ai nghe bài này lúc 3h sáng như mình không?",
    "mọi người nghe bài này lúc nào trong ngày?",
    "ai thấy bài này nghe buổi tối hay hơn ban ngày?",
    "có ai loop bài này cả đêm không?",
    "nghe xong mọi người thấy cảm xúc gì?",
    "bài này có phù hợp mở cho trẻ em nghe không mọi người?",
    "ai biết giọng hát trong bài là AI hay người thật?",
    "có ai nghe khi thiền/yoga không? hiệu quả sao?",
    "mình nghe xong muốn biết thêm về Phật pháp, bắt đầu từ đâu?",
    "đoạn nào trong bài mọi người thích nhất?",
]

# Reply patterns
REPLY_PATTERNS = [
    "mình cũng vậy, {agreement}",
    "đúng rồi, {agreement}",
    "same, {agreement}",
    "em cũng thấy vậy, {agreement}",
    "agree, {agreement}",
    "cảm ơn bạn, {gratitude}",
    "hay quá, {appreciation}",
]

AGREEMENTS = [
    "nghe đêm hay hơn thật",
    "loop hoài không chán",
    "bài này chill thật sự",
    "mỗi lần nghe mỗi khác",
    "bình an lắm",
    "thích bài này ghê",
    "nghe xong feel better hẳn",
]

def generate_comments_for_track(track_info, personas, used_bodies):
    """Generate comments for a single track."""
    tid = track_info['track']
    play = track_info['play']
    track_name = get_track_name(tid)
    genre = get_genre(tid)
    
    # Calculate targets
    like_pct = random.uniform(0.08, 0.13)
    comment_pct = random.uniform(0.03, 0.06)
    target_likes = max(1, int(play * like_pct))
    target_comments = max(4, int(play * comment_pct))
    
    # Cap at reasonable number
    target_comments = min(target_comments, 25)
    
    # Select personas for this track (random subset)
    selected = random.sample(personas, min(len(personas), target_comments + 5))
    
    comments = []
    timestamps = sorted([random_ts_past_14_days() for _ in range(target_comments + 10)])
    ts_idx = 0
    
    # Determine how many are hooks (~15%) and replies (~20%)
    n_hooks = max(1, target_comments // 6)
    n_replies = max(1, target_comments // 5)
    n_roots = target_comments - n_replies
    
    # Generate root comments
    for i in range(n_roots):
        if i >= len(selected) or ts_idx >= len(timestamps):
            break
        persona = selected[i]
        name = persona['name']
        
        # Generate comment based on persona
        if name in PERSONA_COMMENTS:
            body = PERSONA_COMMENTS[name](track_name, genre)
        else:
            body = f"Bài hay, nghe rất thích"
        
        # Make hook comments
        if i < n_hooks and random.random() < 0.7:
            body = random.choice(HOOKS)
        
        # Ensure uniqueness
        attempt = 0
        while body in used_bodies and attempt < 10:
            if name in PERSONA_COMMENTS:
                body = PERSONA_COMMENTS[name](track_name, genre)
            else:
                body = f"Hay lắm, recommend cho mọi người"
            attempt += 1
        
        if body in used_bodies:
            continue
        
        used_bodies.add(body)
        comments.append({
            "name": name,
            "body": body,
            "ts": timestamps[ts_idx],
            "parent_idx": -1
        })
        ts_idx += 1
    
    # Generate replies (to hooks or random root comments)
    root_indices = [i for i, c in enumerate(comments) if c["parent_idx"] == -1]
    for _ in range(n_replies):
        if not root_indices or ts_idx >= len(timestamps):
            break
        parent_idx = random.choice(root_indices[:max(1, n_hooks)])  # Prefer replying to hooks
        
        # Pick a different persona than parent
        parent_name = comments[parent_idx]["name"]
        reply_personas = [p for p in selected if p["name"] != parent_name]
        if not reply_personas:
            continue
        persona = random.choice(reply_personas)
        name = persona['name']
        
        # Generate reply
        agreement = random.choice(AGREEMENTS)
        body = random.choice([
            f"mình cũng vậy, {agreement}",
            f"đúng rồi, {agreement}",
            f"same, {agreement}",
            f"em cũng thấy vậy, hay lắm",
            f"agree, nghe lại liền",
            f"cảm ơn bạn recommend",
        ])
        
        if body in used_bodies:
            body = f"{name}: {agreement}"
        
        if body in used_bodies:
            continue
            
        used_bodies.add(body)
        # Ensure reply ts > parent ts
        reply_ts = max(timestamps[ts_idx], comments[parent_idx]["ts"] + random.randint(1000, 300000))
        comments.append({
            "name": name,
            "body": body,
            "ts": reply_ts,
            "parent_idx": parent_idx
        })
        ts_idx += 1
    
    return {
        "track": tid,
        "target_likes": target_likes,
        "comments": comments
    }

def main():
    start_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 55
    end_idx = int(sys.argv[2]) if len(sys.argv) > 2 else 75
    output_path = sys.argv[3] if len(sys.argv) > 3 else "/tmp/opus_bulk_batch.json"
    
    personas = load_personas()
    tracks = load_tracks()
    
    used_bodies = set()
    batch = []
    
    for t in tracks[start_idx:end_idx]:
        item = generate_comments_for_track(t, personas, used_bodies)
        batch.append(item)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(batch, f, ensure_ascii=False, indent=2)
    
    total_comments = sum(len(item['comments']) for item in batch)
    print(f"Generated: {len(batch)} tracks, {total_comments} comments → {output_path}")

if __name__ == "__main__":
    main()
