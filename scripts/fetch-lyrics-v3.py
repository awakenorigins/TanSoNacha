#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# FETCH LYRICS v3 — dùng SUNO PLAYLIST API: mỗi album Phật Pháp có playlist
# → lấy toàn bộ clip (id + title) → match title (bỏ dấu, chuẩn hoá) với track
# → timed-lyrics. Giải nốt các bài STILL.
# ─────────────────────────────────────────────────────────────
import json, os, re, subprocess, time, unicodedata, urllib.request

WS = '/root/.openclaw/workspace'
SUNO = f'{WS}/suno-cli/target/release/suno'
GEN = f'{WS}/TangKinhCac/website/src/data/amkinh-tieutam.gen.json'
CACHE = f'{WS}/TangKinhCac/radio/lyrics-cache'

PLAYLISTS = {  # album slug → playlist id
 'da-hoi-huong':    'bbf78ac3-3100-4f62-830c-f291c63cac55',
 'da-bo-tat-hanh':  '090438a2',
 'da-tu-bi':        'fd8840ce',
 'da-vo-thuong':    '884ee410',
 'da-tinh-do':      'd09646a4',
 'da-sam-hoi':      'c6acaaa6',
 'da-nacha':        '356ea3a8',
 'da-vo-dien-phat': '87649d7d',
 'da-sifu-minh-tue':'642ac29f',
 'bat-khong':       '18deecdd',
}

def sh(args, timeout=90):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout).stdout

# refresh JWT
sh([SUNO, 'auth', '--refresh'], 120)
JWT = json.load(open('/root/.config/suno-cli/auth.json')).get('jwt','')
HDRS = {'Authorization': f'Bearer {JWT}', 'Origin': 'https://suno.com',
        'Referer': 'https://suno.com/', 'User-Agent': 'Chrome/144'}

def api(url):
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

# resolve full playlist ids (8-char prefixes → full id via /playlist/me)
me = api('https://studio-api.prod.suno.com/api/playlist/me?page=0')
full_ids = {}
for p in me.get('playlists', []):
    full_ids[p['id'][:8]] = p['id']
for k, v in list(PLAYLISTS.items()):
    PLAYLISTS[k] = full_ids.get(v[:8], v)

def strip_vn(s):
    s = unicodedata.normalize('NFD', str(s).lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace('đ','d').replace('ą','a')
    return re.sub(r'[^a-z0-9]+',' ', s).strip()

def playlist_clips(pid):
    clips = []
    for page in range(0, 10):
        try:
            d = api(f'https://studio-api.prod.suno.com/api/playlist/{pid}?page={page}')
        except Exception as e:
            print('  playlist page err', page, e); break
        items = d.get('playlist_clips') or []
        if not items: break
        for it in items:
            c = it.get('clip') or it
            if c.get('id'): clips.append({'id': c['id'], 'title': c.get('title','')})
        if len(items) < 20: break
        time.sleep(0.3)
    return clips

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

gen = json.load(open(GEN))
stats = {'ok':0,'still':0}
for al in gen['albums']:
    todo = [t for t in al['tracks'] if not t.get('lyrics')]
    if not todo: continue
    pid = PLAYLISTS.get(al['slug'])
    if not pid: stats['still'] += len(todo); continue
    clips = playlist_clips(pid)
    print(al['slug'], '→ playlist clips:', len(clips), '| cần:', len(todo))
    by_title = {}
    for c in clips:
        by_title.setdefault(strip_vn(c['title']), []).append(c['id'])
    for t in todo:
        key = strip_vn(t['title'])
        ids = by_title.get(key) or []
        if not ids:
            # thử match chứa nhau (title file có thể thiếu/thừa 1 từ)
            for k, v in by_title.items():
                if k and (k in key or key in k): ids = v; break
        got = False
        for cid in ids:
            cf = f'{CACHE}/{cid}.json'
            if not os.path.isfile(cf):
                try:
                    out = sh([SUNO, 'timed-lyrics', cid, '--json'], 90)
                    d = json.loads(out)
                    if d.get('status') != 'success': continue
                    open(cf,'w').write(json.dumps(d['data'], ensure_ascii=False))
                    time.sleep(0.4)
                except Exception: continue
            lines = words_to_lines(json.load(open(cf)))
            if lines:
                t['lyrics'] = lines; t['suno_id'] = cid; stats['ok'] += 1; got = True
                # cập nhật title chuẩn có dấu từ Suno nếu title đang mất dấu
                cur_no_vn = not any(unicodedata.category(c)=='Mn' for c in unicodedata.normalize('NFD', t['title']))
                if cur_no_vn:
                    st = next((c['title'] for c in clips if c['id']==cid), None)
                    if st: t['title'] = st
                break
        if not got:
            stats['still'] += 1
            print('  STILL:', al['slug'], t['title'])
    json.dump(gen, open(GEN,'w'), ensure_ascii=False, indent=1)
json.dump(gen, open(GEN,'w'), ensure_ascii=False, indent=1)
print(json.dumps(stats, ensure_ascii=False))
