#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# FIX TITLES — thay title mất dấu bằng title chuẩn từ Suno playlist.
# Nguồn: playlist API (9 album Phật Pháp + Bất Không). Match strip-vn.
# Sau khi chạy: chạy lại merge-amkinh.py (chỉ regen amkinh-gen.ts) + build.
# ─────────────────────────────────────────────────────────────
import json, re, unicodedata, urllib.request, subprocess, time

WS = '/root/.openclaw/workspace'
GEN = f'{WS}/TangKinhCac/website/src/data/amkinh-tieutam.gen.json'
SUNO = f'{WS}/suno-cli/target/release/suno'

subprocess.run([SUNO,'auth','--refresh'],capture_output=True,timeout=120)
JWT = json.load(open('/root/.config/suno-cli/auth.json')).get('jwt','')
def api(u):
    r = urllib.request.Request(u, headers={'Authorization':f'Bearer {JWT}','Origin':'https://suno.com','Referer':'https://suno.com/','User-Agent':'Chrome/144'})
    return json.loads(urllib.request.urlopen(r, timeout=60).read())

def strip_vn(s):
    s = unicodedata.normalize('NFD', str(s).lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace('đ','d').replace('ą','a')
    return re.sub(r'[^a-z0-9]+',' ', s).strip()

def has_marks(s):
    return sum(1 for c in unicodedata.normalize('NFD', s) if unicodedata.category(c)=='Mn') > 1

PL_PREFIX = {'da-hoi-huong':'bbf78ac3','da-bo-tat-hanh':'090438a2','da-tu-bi':'fd8840ce',
 'da-vo-thuong':'884ee410','da-tinh-do':'d09646a4','da-sam-hoi':'c6acaaa6','da-nacha':'356ea3a8',
 'da-vo-dien-phat':'87649d7d','da-sifu-minh-tue':'642ac29f','bat-khong':'18deecdd'}

me = api('https://studio-api.prod.suno.com/api/playlist/me?page=0')
full = {p['id'][:8]: p['id'] for p in me.get('playlists',[])}

gen = json.load(open(GEN))
fixed = 0; left = 0
for al in gen['albums']:
    pid = full.get(PL_PREFIX.get(al['slug'],'')[:8])
    if not pid: continue
    clips = []
    for page in range(0,5):
        d = api(f'https://studio-api.prod.suno.com/api/playlist/{pid}?page={page}')
        items = d.get('playlist_clips') or []
        if not items: break
        for it in items:
            c = it.get('clip') or it
            clips.append({'id': c.get('id'), 'title': c.get('title','')})
        if len(items) < 20: break
        time.sleep(0.25)
    by_id = {c['id']: c['title'] for c in clips if c['id']}
    by_key = {}
    for c in clips: by_key.setdefault(strip_vn(c['title']), c['title'])
    for t in al['tracks']:
        if has_marks(t['title']): continue
        nt = None
        if t.get('suno_id') and t['suno_id'] in by_id: nt = by_id[t['suno_id']]
        if not nt: nt = by_key.get(strip_vn(t['title']))
        if not nt:
            key = strip_vn(t['title'])
            for k, v in by_key.items():
                if k and (k in key or key in k): nt = v; break
        if nt and has_marks(nt):
            t['title'] = nt; fixed += 1
        else:
            left += 1; print('LEFT:', al['slug'], t['title'])
json.dump(gen, open(GEN,'w'), ensure_ascii=False, indent=1)
print(json.dumps({'fixed': fixed, 'left': left}, ensure_ascii=False))
