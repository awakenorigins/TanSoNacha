#!/usr/bin/env python3
# REFILL GUARD — kiểm tra bank, quyết định có cần refill không.
# Rule anh Nấng: refill khi unused < 30% tổng. Câu mới KHÔNG được trùng câu ĐÃ DÙNG
# (used=1) lẫn câu chưa dùng — TRỪ tone 'niem' (Nam mô, A Di Đà...) được phép na ná.
import sqlite3, sys, unicodedata, re
DB='/root/.openclaw/workspace/TangKinhCac/backend/data/amkinh.db'
PROHIBITED=re.compile(r'''(?ix)
    (phải\s+nói\s+là|nói\s+thật\s+là\s+nói\s+thật|công\s+nhận\s+công\s+nhận|thiệt\s+tình\s+thiệt\s+tình)|
    \b(mix|bass|voice|vocal|reverb|compression|master|mastering|loudness|dynamic|sound\s+design|texture|grain|pad\s+nền|layer|phối\s+khí|dải\s+tần|synth|verse|điệp\s+khúc)\b|
    (xã\s+hội\s+hiện\s+đại\s+đang\s+rất\s+cần|đưa\s+giáo\s+lý\s+tới\s+gần\s+người\s+trẻ|ngôn\s+ngữ\s+âm\s+nhạc|bố\s+cục\s+âm\s+nhạc)|
    (symbolism|poetic|max\s+level|next\s+level|cinematic\s+buddhist|spa\s+level|lofi\s+is\s+life)
''')
def norm(s):
    s=unicodedata.normalize('NFD',s.lower()); s=''.join(c for c in s if unicodedata.category(c)!='Mn')
    return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9 ]','',s)).strip()

def similarity(a,b):
    a,b=set(norm(a).split()),set(norm(b).split())
    return len(a&b)/len(a|b) if a and b else 0.0

def status():
    db=sqlite3.connect(DB); c=db.cursor()
    tot=c.execute("select count(*) from comment_pool").fetchone()[0]
    unused=c.execute("select count(*) from comment_pool where used=0").fetchone()[0]
    pct=100*unused/tot if tot else 0
    need = pct < 30
    return {'total':tot,'unused':unused,'pct':round(pct,1),'need_refill':need}

def dedupe_check(candidates, allow_niem=True):
    """Admission gate: exact + semantic dedupe and AI-voice rejection.

    Even devotional lines may repeat only when genuinely short; long niệm variants
    still pass semantic review so the refill cannot flood the site with paraphrases.
    """
    db=sqlite3.connect(DB); c=db.cursor()
    # Admission must compare against both the phrase bank and every sentence
    # already published on the site. Otherwise a previously used sentence can
    # be reintroduced as a "new" pool row and later appear again.
    existing_bodies=[r[0] for r in c.execute("select body from comment_pool")]
    existing_bodies += [r[0] for r in c.execute("select body from comments")]
    existing=set(norm(x) for x in existing_bodies)
    ok=[]; seen=set()
    for tone,body in candidates:
        body=(body or '').strip()
        if not body or len(body)>180 or PROHIBITED.search(body): continue
        n=norm(body)
        if n in existing or n in seen: continue
        threshold=.82 if tone=='niem' and len(n.split())<=6 else .72
        if any(similarity(body,x)>=threshold for x in existing_bodies): continue
        if any(similarity(body,x)>=threshold for x in ok): continue
        try:
            c.execute("insert into comment_pool(tone,body) values(?,?)",(tone,body)); ok.append(body); seen.add(n); existing_bodies.append(body); existing.add(n)
        except sqlite3.IntegrityError: pass
    db.commit()
    return ok

if __name__=='__main__':
    import json
    print(json.dumps(status(),ensure_ascii=False))
