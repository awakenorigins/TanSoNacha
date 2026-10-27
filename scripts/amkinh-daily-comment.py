#!/usr/bin/env python3
# COMMENT DẠO HẰNG NGÀY (v2) — dùng bank comment_pool + 280 nick trong bảng nicks.
# Mỗi bài: comment mới = random 1-3% LIKE của bài. Nick theo khung giờ VN, tone-map theo nhóm nick.
# Không self-reply, dedupe body per-track (normalized), ts = vừa xong (không backdate).
import sqlite3, random, json, time, unicodedata, re, sys
from pathlib import Path
DB='/root/.openclaw/workspace/TangKinhCac/backend/data/amkinh.db'
STATE='/root/.openclaw/workspace/TangKinhCac/state/daily-comment-log.json'
TITLEMAP='/root/.openclaw/workspace/TangKinhCac/state/tid-title-map.json'
random.seed()

TECH=re.compile(r'\b(mix|bass|voice|vocal|reverb|compression|master|mastering|loudness|dynamic|sound design|texture|grain|pad nền|layer|phối khí|dải tần|synth|verse|điệp khúc)\b',re.I)
FORMAL=re.compile(r'(cho thấy cách|ví dụ tốt|cái hay của|ngôn ngữ âm nhạc|chất liệu phật giáo|hướng đi mới|dung hòa yếu tố|bố cục âm nhạc|âm nhạc đương đại|đưa giáo lý tới gần người trẻ|xã hội hiện đại đang rất cần)',re.I)
MALFORMED=re.compile(r'\b(nói thật là nói thật|công nhận công nhận|thiệt tình thiệt tình|ui ui|chà chà|hihi hihi|hehe hehe)\b',re.I)

def norm(x):
    x=unicodedata.normalize('NFD',x.lower()); x=''.join(c for c in x if unicodedata.category(c)!='Mn')
    return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9 ]','',x)).strip()

def similarity(a,b):
    a,b=set(norm(a).split()),set(norm(b).split())
    return len(a&b)/len(a|b) if a and b else 0.0

def load_titles():
    try: return json.load(open(TITLEMAP,encoding='utf-8'))
    except Exception: return {}

def track_title(titles,tid):
    return titles.get(tid,{}).get('title') or tid.split(':')[-1].replace('-',' ').title()

def clean_for_track(body,title,track_bodies,global_norms):
    nb,nt=norm(body),norm(title)
    if not nb or nb in global_norms: return False
    if nt and len(nt)>3 and nt in nb: return False
    if TECH.search(body) or FORMAL.search(body) or MALFORMED.search(body): return False
    if len(body)>180: return False
    if any(similarity(body,x)>=.70 for x in track_bodies): return False
    return True

def main(cap_override=None, dry=False):
    db=sqlite3.connect(DB, timeout=30); c=db.cursor()
    titles=load_titles()
    hour_vn=(time.gmtime().tm_hour+7)%24
    # nick đang trong khung giờ (khung có thể vượt 24 = qua đêm)
    nicks=[]
    for name,a,b,tones in c.execute("select name,khung_a,khung_b,tones from nicks"):
        active = (a<=hour_vn<=b) or (a<=hour_vn+24<=b)
        if active: nicks.append((name,tones.split(',')))
    if not nicks:
        nicks=[(r[0],r[1].split(',')) for r in c.execute("select name,tones from nicks")]
    by_tone={}; by_group={}
    for nm,ts in nicks:
        for t in ts: by_tone.setdefault(t,[]).append(nm)
    for nm,grp in c.execute('select name,grp from nicks'):
        by_group.setdefault(grp,[]).append(nm)
    alln=[n[0] for n in nicks]
    groups=['gpt','sonnet5','sonnet46','opus']
    global_norms={norm(r[0]) for r in c.execute('select body from comments where parent=0')}
    tracks=c.execute("select track,count from counters where metric='play' and count>0").fetchall()
    random.shuffle(tracks)
    total=0; log=[]
    for tid,play in tracks:
        likes=c.execute("select coalesce(sum(count),0) from counters where track=? and metric!='play'",(tid,)).fetchone()[0]
        if likes<=0: continue
        n=min(4, int(likes*random.uniform(0.01,0.03)))
        if cap_override is not None and total>=cap_override: break
        if n==0: continue
        track_rows=c.execute("select body,name from comments where track=?",(tid,)).fetchall()
        track_bodies=[r[0] for r in track_rows]
        seen=set(norm(r[0]) for r in track_rows)
        used_nicks={r[1] for r in track_rows}
        title=track_title(titles,tid)
        for _ in range(n):
            tone=random.choices(['tanthan','thienvi','doithuong','nhinho','quandiem','nhanxet','hook','reply','niem','iconly','lulu','loibaihat'],
                                weights=[20,13,13,12,6,7,5,7,5,4,4,4])[0]
            row=None
            for _try in range(250):
                candrow=c.execute("select id,body from comment_pool where used=0 and tone=? order by random() limit 1",(tone,)).fetchone()
                if not candrow: candrow=c.execute("select id,body from comment_pool where used=0 order by random() limit 1").fetchone()
                if not candrow: break
                if clean_for_track(candrow[1],title,track_bodies,global_norms): row=candrow; break
            if not row: continue
            pid,body=row
            grp=groups[(total+_)%len(groups)]
            cand=by_group.get(grp) or by_tone.get(tone) or alln
            fresh=[x for x in cand if x not in used_nicks]
            nick=random.choice(fresh or cand)
            parent=0
            if tone in ('reply','loibaihat') or random.random()<0.18:
                pr=c.execute("select id from comments where track=? and parent=0 and name!=? order by random() limit 1",(tid,nick)).fetchone()
                if pr: parent=pr[0]
            ts=int(time.time()*1000)-random.randint(0,3600*1000)
            if not dry:
                c.execute("insert into comments(track,parent,name,body,ts) values(?,?,?,?,?)",(tid,parent,nick,body,ts))
                c.execute("update comment_pool set used=1,used_by=?,used_track=?,used_at=? where id=?",(nick,tid,ts,pid))
            seen.add(norm(body));global_norms.add(norm(body));track_bodies.append(body);used_nicks.add(nick);total+=1
    if not dry: db.commit()
    left=c.execute("select count(*) from comment_pool where used=0").fetchone()[0]
    res={'ts':time.strftime('%Y-%m-%d %H:%M'),'hour_vn':hour_vn,'inserted':total,'pool_left':left,'dry':dry}
    try: hist=json.load(open(STATE))
    except Exception: hist=[]
    hist.append(res); json.dump(hist[-60:],open(STATE,'w'))
    print(json.dumps(res,ensure_ascii=False))

if __name__=='__main__':
    dry='--dry' in sys.argv; cap=None
    for a in sys.argv:
        if a.startswith('--cap='): cap=int(a.split('=')[1])
    main(cap,dry)
