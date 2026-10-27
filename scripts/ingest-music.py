#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# TẦN SỐ NACHA — INGEST 3 KHO NHẠC → /var/www/tansonacha-media/nhac
# Artist = Tiểu Tâm. Album theo thể loại folder. Khử trùng md5.
# Output: website/src/data/amkinh-tieutam.gen.json
# ─────────────────────────────────────────────────────────────
import json, os, re, shutil, subprocess, sys, unicodedata, hashlib, random

WS = '/root/.openclaw/workspace'
MEDIA = '/var/www/tansonacha-media/nhac'
COVERS = '/var/www/tansonacha-media/covers'
OUT_JSON = f'{WS}/TangKinhCac/website/src/data/amkinh-tieutam.gen.json'
os.makedirs(MEDIA, exist_ok=True); os.makedirs(COVERS, exist_ok=True)

def slug(s):
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace('đ','d').replace('Đ','D').replace('ą','a').replace('Ą','A')
    s = re.sub(r'[^A-Za-z0-9]+', '-', s).strip('-').lower()
    return s or 'x'

def md5(p, cache={}):
    if p not in cache:
        h = hashlib.md5()
        with open(p,'rb') as f:
            for chunk in iter(lambda: f.read(1<<20), b''): h.update(chunk)
        cache[p] = h.hexdigest()
    return cache[p]

def dur(p):
    try:
        r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',p],capture_output=True,text=True,timeout=30)
        s = float(r.stdout.strip())
        return f'{int(s//60)}:{int(s%60):02d}'
    except Exception: return None

seen_md5 = set()
albums = []  # {slug,title,cn,desc,genre,cover,tracks:[{slug,title,src,cover,duration,tag}]}
stats = {'copied':0,'skipped_dupe':0,'missing':0}

def add_track(album, title, src_path, cover_src, tag):
    if not os.path.isfile(src_path):
        stats['missing'] += 1; return
    h = md5(src_path)
    if h in seen_md5:
        stats['skipped_dupe'] += 1; return
    seen_md5.add(h)
    tslug = slug(title)
    # tránh trùng slug trong album
    base = tslug; i = 2
    while any(t['slug']==tslug for t in album['tracks']):
        tslug = f'{base}-{i}'; i += 1
    adir = os.path.join(MEDIA, album['slug']); os.makedirs(adir, exist_ok=True)
    dst = os.path.join(adir, f'{tslug}.mp3')
    if not os.path.isfile(dst): shutil.copy2(src_path, dst)
    cover_url = None
    if cover_src and os.path.isfile(cover_src):
        cdst = os.path.join(COVERS, f'{album["slug"]}--{tslug}.jpg')
        if not os.path.isfile(cdst): shutil.copy2(cover_src, cdst)
        cover_url = f'/media/covers/{album["slug"]}--{tslug}.jpg'
    album['tracks'].append({
        'slug': tslug, 'title': title, 'author': 'Tiểu Tâm',
        'src': f'/media/nhac/{album["slug"]}/{tslug}.mp3',
        'cover': cover_url, 'duration': dur(dst), 'tag': tag, 'ready': True,
        'src_path': src_path, 'md5': h,
    })
    stats['copied'] += 1

def new_album(aslug, title, desc, genre, cn=None, cover=None):
    a = {'slug': aslug, 'title': title, 'cn': cn or '', 'desc': desc, 'genre': genre, 'cover': cover, 'tracks': []}
    albums.append(a); return a

# ══════════ KHO 2 — 108 PHẬT TƯỞNG (ưu tiên, album Phật Pháp) ══════════
K2 = f'{WS}/suno-out/108-phat-tuong/ALBUMS'
K2_META = {
 'Nacha':        ('da-nacha','Dạ Nacha','那 迦','108 mảnh chuyện Như Lai — mỗi bài một tần số, mỗi tần số một hơi thở tỉnh thức.'),
 'Minh-Tue':     ('da-sifu-minh-tue','Dą Sifu Minh Tuệ','明 慧','Hành trạng, buông bỏ, khất thực, thiểu dục tri túc — mạch Thầy Minh Tuệ.'),
 'Vo-Dien-Phat': ('da-vo-dien-phat','Dạ Vô Diện Phật','無 面 佛','Thiền định, vô tướng — Phật không mặt, khắp muôn nơi.'),
 'Sam-Hoi':      ('da-sam-hoi','Dạ Sám Hối','懺 悔','Nhìn lỗi rồi buông — sám hối theo hướng tỉnh thức, nhẹ nhàng, hướng sáng.'),
 'Tinh-Do':      ('da-tinh-do','Dạ Tịnh Độ','淨 土','Cõi lành trong tâm — niệm Phật, an trú, thanh lương.'),
 'Vo-Thuong':    ('da-vo-thuong','Dạ Vô Thường','無 常','Mọi thứ trôi qua — nghe để thương cái đang còn.'),
 'Tu-Bi':        ('da-tu-bi','Dạ Từ Bi','慈 悲','Trái tim mở rộng — từ bi với người, với mình, với muôn loài.'),
 'Bo-Tat-Hanh':  ('da-bo-tat-hanh','Dạ Bồ Tát Hạnh','菩 薩 行','Hạnh nguyện giữa đời — đôi tay Bồ Tát trong việc nhỏ mỗi ngày.'),
 'Hoi-Huong':    ('da-hoi-huong','Dạ Hồi Hướng','回 向','Bao nhiêu phước lành, xin gửi về khắp pháp giới.'),
}
for folder, (aslug, title, cn, desc) in K2_META.items():
    d = os.path.join(K2, folder)
    if not os.path.isdir(d): continue
    al = new_album(aslug, title, desc, 'Phật Pháp', cn)
    for f in sorted(os.listdir(d)):
        if not f.lower().endswith('.mp3'): continue
        # 01-Da-Tan-So-Nacha.mp3 → "Dạ Tần Số Nacha" (không dấu trong filename → giữ dạng Title Case có Dạ)
        name = re.sub(r'^\d+-', '', f[:-4]).replace('-', ' ')
        name = re.sub(r'^Da ', 'Dạ ', name)
        add_track(al, name, os.path.join(d, f), None, 'Phật Pháp')

# ══════════ KHO 1 — AUTOMATO LIBRARY (22 album manifest theo genre) ══════════
K1 = f'{WS}/suno-automato-cli/suno-library/_albums'
GENRE_VI = {
 'Ballad':'Ballad','Bolero':'Bolero','Cai-Luong':'Cải Lương','Cinematic':'Cinematic','Cinematic-MaxMax':'Cinematic',
 'EDM':'EDM','Experimental':'Experimental','Instrumental':'Không Lời','Lofi':'Lofi','Opera':'Opera','Other':'Đa Sắc',
 'Phat-Phap':'Phật Pháp','Pop':'Pop','Rap':'Rap','Relax-Sleep':'Thư Giãn','Remix-Cover':'Remix',
 'Restaurant-Jazz-Instrument':'Jazz','Rock':'Rock','Thien':'Thiền','Thieu-Nhi':'Thiếu Nhi','Wedding':'Wedding'}
for adir in sorted(os.listdir(K1)):
    mf = os.path.join(K1, adir, 'album.json')
    if not os.path.isfile(mf): continue
    m = json.load(open(mf))
    genre = GENRE_VI.get(m.get('genre',''), m.get('genre','Đa Sắc'))
    aslug = slug(m['name'])
    al = new_album(aslug, m['name'], m.get('description','') or f'Album {genre} — Tiểu Tâm.', genre)
    if al['desc'].startswith('Auto-generated'):
        al['desc'] = f'Tuyển tập {genre} — Tiểu Tâm dệt thanh âm.'
    for t in m.get('tracks', []):
        add_track(al, t['title'], t.get('audio_path',''), t.get('cover_path'), genre)
    if al['tracks'] and al['tracks'][0].get('cover'): al['cover'] = al['tracks'][0]['cover']

# ══════════ KHO 3 — BẤT KHÔNG + ĐẠI TÁN THÁN (khử trùng, tên đẹp) ══════════
def nice_name(fn):
    b = os.path.splitext(os.path.basename(fn))[0]
    b = re.sub(r'-[0-9a-f]{8}$', '', b)
    return b
al_bk = new_album('bat-khong', 'Bất Không', 'Tuyển tập tán thán Đức Bổn Sư — nhiều sắc thái: sacred pop, cinematic EDM, bolero-world, opera, bedroom pop.', 'Phật Pháp', '不 空')
K3 = f'{WS}/suno-out/bat-khong'
pref = []
for root, _, files in os.walk(K3):
    for f in files:
        if f.lower().endswith('.mp3'): pref.append(os.path.join(root, f))
# ưu tiên file tên ASCII đẹp trước để bản giữ lại có tên đẹp
pref.sort(key=lambda p: (0 if re.match(r'^[A-Za-z0-9_\-\.]+$', os.path.basename(p)) else 1, p))
for p in pref:
    n = nice_name(p)
    if re.match(r'^[A-Za-z]', n):
        title = re.sub(r'[-_]+', ' ', n)
    else:
        title = 'Dạ Đại Tán Thán Đức Bổn Sư Thích Ca Mâu Ni Phật'
    add_track(al_bk, title, p, None, 'Phật Pháp')
K3B = f'{WS}/suno-out/da-dai-tan-than'
prefb = sorted((os.path.join(K3B,f) for f in os.listdir(K3B) if f.lower().endswith('.mp3')),
               key=lambda p: (0 if re.match(r'^[A-Za-z0-9_\-\.]+$', os.path.basename(p)) else 1, p))
for p in prefb:
    n = nice_name(p)
    title = re.sub(r'[-_]+',' ',n) if re.match(r'^[A-Za-z]', n) else 'Dạ Đại Tán Thán Đức Bổn Sư Thích Ca Mâu Ni Phật'
    add_track(al_bk, title, p, None, 'Phật Pháp')

albums = [a for a in albums if a['tracks']]
json.dump({'albums': albums, 'stats': stats}, open(OUT_JSON,'w',encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(stats, ensure_ascii=False))
print('albums:', len(albums), 'tracks:', sum(len(a["tracks"]) for a in albums))
for a in albums: print(f'  {a["genre"]:12s} {a["slug"]:42s} {len(a["tracks"])} bài')
