#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# TẦN SỐ NACHA — FETCH TIMED LYRICS TỪ SUNO cho 307 bài đã ingest
# Map clip-id: Kho1 = suno_id trong album.json · Kho2/3 = hex8 trong tên file
# nguồn cùng md5 · fallback = match title qua suno list index.
# Cache: radio/lyrics-cache/<clipid>.json · Resume-safe.
# ─────────────────────────────────────────────────────────────
import json, os, re, subprocess, sys, hashlib, glob, time, unicodedata

WS = '/root/.openclaw/workspace'
SUNO = f'{WS}/suno-cli/target/release/suno'
GEN = f'{WS}/TangKinhCac/website/src/data/amkinh-tieutam.gen.json'
CACHE = f'{WS}/TangKinhCac/radio/lyrics-cache'
INDEX = f'{CACHE}/_clip-index.json'
os.makedirs(CACHE, exist_ok=True)

def run(args, timeout=90):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return r.stdout

def md5(p, cache={}):
    if p not in cache:
        h = hashlib.md5()
        with open(p,'rb') as f:
            for c in iter(lambda: f.read(1<<20), b''): h.update(c)
        cache[p] = h.hexdigest()
    return cache[p]

def norm_title(s):
    s = unicodedata.normalize('NFC', str(s)).lower().strip()
    s = re.sub(r'\s+', ' ', s)
    return s

# ── 1. CLIP INDEX: tải toàn bộ list (cache 1 lần) ──
def load_clip_index():
    if os.path.isfile(INDEX):
        return json.load(open(INDEX))
    clips = []
    for page in range(0, 40):
        try:
            out = run([SUNO, 'list', '--page', str(page), '--json'], 120)
            d = json.loads(out)
            data = d.get('data') or []
            if isinstance(data, dict): data = data.get('clips') or []
            if not data: break
            clips.extend({'id': c['id'], 'title': c.get('title','')} for c in data if c.get('id'))
            time.sleep(0.4)
        except Exception as e:
            print('list page', page, 'err', e); break
    json.dump(clips, open(INDEX,'w'), ensure_ascii=False)
    return clips

# ── 2. MAP md5 → clip id ──
def build_md5_map():
    m = {}
    # Kho1: manifest suno_id
    for mf in glob.glob(f'{WS}/suno-automato-cli/suno-library/_albums/*/album.json'):
        d = json.load(open(mf))
        for t in d.get('tracks', []):
            p = t.get('audio_path',''); sid = t.get('suno_id')
            if sid and os.path.isfile(p): m[md5(p)] = sid
    # Kho2 + Kho3: file nguồn có hex trong tên (8+ hex cuối trước .mp3)
    src_roots = [f'{WS}/suno-out/108-phat-tuong', f'{WS}/suno-out/bat-khong', f'{WS}/suno-out/da-dai-tan-than']
    hex_map = {}  # md5 → hex8
    for root in src_roots:
        for p in glob.glob(f'{root}/**/*.mp3', recursive=True) + glob.glob(f'{root}/**/*.MP3', recursive=True):
            b = os.path.splitext(os.path.basename(p))[0]
            mm = re.search(r'([0-9a-f]{8})$', b)
            if mm:
                try: hex_map.setdefault(md5(p), mm.group(1))
                except Exception: pass
    return m, hex_map

def main():
    gen = json.load(open(GEN))
    clips = load_clip_index()
    by_prefix = {}
    by_title = {}
    for c in clips:
        by_prefix.setdefault(c['id'][:8], c['id'])
        by_title.setdefault(norm_title(c['title']), c['id'])
    full_map, hex_map = build_md5_map()
    print(f'clip index: {len(clips)} · md5→sid: {len(full_map)} · md5→hex8: {len(hex_map)}')

    stats = {'ok':0,'cached':0,'no_id':0,'fail':0}
    for al in gen['albums']:
        for t in al['tracks']:
            if t.get('lyrics'): stats['cached'] += 1; continue
            h = t.get('md5'); sp = t.get('src_path','')
            cid = full_map.get(h)
            if not cid and h in hex_map: cid = by_prefix.get(hex_map[h])
            if not cid: cid = by_title.get(norm_title(t['title']))
            if not cid:
                # thử title dạng "Dạ Tan So Nacha" → bỏ dấu so khớp không dấu
                tt = norm_title(t['title'])
                for k, v in by_title.items():
                    kk = unicodedata.normalize('NFD', k)
                    kk = ''.join(ch for ch in kk if unicodedata.category(ch) != 'Mn').replace('đ','d')
                    t2 = unicodedata.normalize('NFD', tt)
                    t2 = ''.join(ch for ch in t2 if unicodedata.category(ch) != 'Mn').replace('đ','d')
                    if kk == t2: cid = v; break
            if not cid:
                stats['no_id'] += 1
                print('NO-ID:', al['slug'], t['title'])
                continue
            cf = f'{CACHE}/{cid}.json'
            if not os.path.isfile(cf):
                try:
                    out = run([SUNO, 'timed-lyrics', cid, '--json'], 90)
                    d = json.loads(out)
                    if d.get('status') != 'success': raise RuntimeError(d.get('error',{}).get('message','?')[:80])
                    open(cf,'w').write(json.dumps(d['data'], ensure_ascii=False))
                    time.sleep(0.5)
                except Exception as e:
                    stats['fail'] += 1
                    print('FAIL:', t['title'], cid[:8], str(e)[:100])
                    continue
            words = json.load(open(cf))
            # word-level → line-level: gộp theo \n, bỏ [Section]
            lines = []; cur = []; start = None
            for w in words:
                txt = w.get('word','')
                if start is None and txt.strip(): start = w.get('start_s', 0)
                parts = txt.split('\n')
                for i, seg in enumerate(parts):
                    if i > 0:  # newline → chốt dòng
                        line = ''.join(cur).strip()
                        line = re.sub(r'\[[^\]]*\]', '', line).strip()
                        if line: lines.append({'t': round(start or 0, 2), 'text': line})
                        cur = []; start = w.get('start_s', 0) if seg.strip() else None
                    if seg: cur.append(seg + (' ' if not seg.endswith(' ') else ''))
            line = re.sub(r'\[[^\]]*\]', '', ''.join(cur)).strip()
            if line: lines.append({'t': round(start or 0, 2), 'text': line})
            if lines:
                t['lyrics'] = lines
                t['suno_id'] = cid
                stats['ok'] += 1
            else:
                stats['fail'] += 1
            if (stats['ok'] % 20) == 0:
                json.dump(gen, open(GEN,'w'), ensure_ascii=False, indent=1)
    json.dump(gen, open(GEN,'w'), ensure_ascii=False, indent=1)
    print(json.dumps(stats, ensure_ascii=False))

if __name__ == '__main__':
    main()
