#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# FETCH LYRICS v2 — giải 128 bài NO-ID + 24 FAIL:
# Kho2/3 downloads có file twin tên tiếng Việt CÙNG hex8 (= 8 ký tự đầu clip UUID)
# → lấy title chuẩn từ twin → suno search → match id.startswith(hex8) → timed-lyrics.
# ─────────────────────────────────────────────────────────────
import json, os, re, subprocess, time, hashlib, glob, unicodedata

WS = '/root/.openclaw/workspace'
SUNO = f'{WS}/suno-cli/target/release/suno'
GEN = f'{WS}/TangKinhCac/website/src/data/amkinh-tieutam.gen.json'
CACHE = f'{WS}/TangKinhCac/radio/lyrics-cache'

def run(args, timeout=90):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout).stdout

def md5(p, cache={}):
    if p not in cache:
        h = hashlib.md5()
        with open(p,'rb') as f:
            for c in iter(lambda: f.read(1<<20), b''): h.update(c)
        cache[p] = h.hexdigest()
    return cache[p]

def words_to_lines(words):
    lines = []; cur = []; start = None
    for w in words:
        txt = w.get('word','')
        if start is None and txt.strip(): start = w.get('start_s', 0)
        parts = txt.split('\n')
        for i, seg in enumerate(parts):
            if i > 0:
                line = re.sub(r'\[[^\]]*\]', '', ''.join(cur)).strip()
                if line: lines.append({'t': round(start or 0, 2), 'text': line})
                cur = []; start = w.get('start_s', 0) if seg.strip() else None
            if seg: cur.append(seg + (' ' if not seg.endswith(' ') else ''))
    line = re.sub(r'\[[^\]]*\]', '', ''.join(cur)).strip()
    if line: lines.append({'t': round(start or 0, 2), 'text': line})
    return lines

# ── map md5 → hex8 và hex8 → tên tiếng Việt đẹp nhất ──
hex_by_md5 = {}
vn_by_hex = {}
roots = [f'{WS}/suno-out/108-phat-tuong', f'{WS}/suno-out/bat-khong', f'{WS}/suno-out/da-dai-tan-than']
for root in roots:
    for p in glob.glob(f'{root}/**/*.mp3', recursive=True) + glob.glob(f'{root}/**/*.MP3', recursive=True):
        b = os.path.splitext(os.path.basename(p))[0]
        m = re.search(r'([0-9a-f]{8})$', b)
        if not m: continue
        hx = m.group(1)
        try: hex_by_md5.setdefault(md5(p), hx)
        except Exception: continue
        name = re.sub(r'-[0-9a-f]{8}$', '', b)
        has_vn = any(unicodedata.category(c) == 'Mn' for c in unicodedata.normalize('NFD', name))
        if has_vn or hx not in vn_by_hex:
            if has_vn or not vn_by_hex.get(hx,{}).get('vn'):
                vn_by_hex[hx] = {'name': re.sub(r'[-_]+',' ',name).strip(), 'vn': has_vn}

def search_clip(query, hex8):
    try:
        out = run([SUNO,'search',query,'--json'], 90)
        d = json.loads(out); data = d.get('data') or []
        if isinstance(data, dict): data = data.get('clips') or data.get('results') or []
        for c in data:
            if c.get('id','').startswith(hex8): return c['id']
    except Exception: pass
    return None

gen = json.load(open(GEN))
stats = {'ok':0,'still':0}
pending_save = 0
for al in gen['albums']:
    for t in al['tracks']:
        if t.get('lyrics'): continue
        h = t.get('md5'); hx = hex_by_md5.get(h)
        cid = None
        if hx:
            info = vn_by_hex.get(hx, {})
            q = info.get('name') or t['title']
            cid = search_clip(q, hx)
            if not cid:
                cid = search_clip(' '.join(q.split()[:4]), hx)
        if not cid:
            print('STILL:', al['slug'], t['title']); stats['still'] += 1; continue
        cf = f'{CACHE}/{cid}.json'
        if not os.path.isfile(cf):
            try:
                out = run([SUNO,'timed-lyrics',cid,'--json'], 90)
                d = json.loads(out)
                if d.get('status') != 'success': raise RuntimeError('api')
                open(cf,'w').write(json.dumps(d['data'], ensure_ascii=False))
                time.sleep(0.4)
            except Exception as e:
                print('STILL(fetch):', t['title'], cid[:8]); stats['still'] += 1; continue
        lines = words_to_lines(json.load(open(cf)))
        if lines:
            t['lyrics'] = lines; t['suno_id'] = cid; stats['ok'] += 1
            # dùng luôn tên tiếng Việt chuẩn nếu title hiện tại mất dấu
            info = vn_by_hex.get(hx, {})
            cur_no_vn = not any(unicodedata.category(c)=='Mn' for c in unicodedata.normalize('NFD', t['title']))
            if info.get('vn') and cur_no_vn:
                nm = info['name']
                nm = ' '.join(w.capitalize() if i==0 or len(w)>1 else w for i,w in enumerate(nm.split()))
                t['title'] = nm
            pending_save += 1
            if pending_save >= 15:
                json.dump(gen, open(GEN,'w'), ensure_ascii=False, indent=1); pending_save = 0
        else:
            stats['still'] += 1
json.dump(gen, open(GEN,'w'), ensure_ascii=False, indent=1)
print(json.dumps(stats, ensure_ascii=False))
