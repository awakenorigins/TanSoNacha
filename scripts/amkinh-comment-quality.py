#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quality guard + transactional cleanup for Am Kinh comments.
Rules:
- A track title is optional and normally forbidden in generated comments.
- Reject fake production-analysis jargon and essay-like boilerplate.
- Reject exact and semantic near-duplicates per track.
- Limit repeated nick usage per track and globally in refill batches.
- Quarantine, never silently erase, rejected legacy rows.
"""
import argparse, collections, json, random, re, sqlite3, time, unicodedata
from pathlib import Path
ROOT=Path('/root/.openclaw/workspace/TangKinhCac')
DB=ROOT/'backend/data/amkinh.db'; TITLEMAP=ROOT/'state/tid-title-map.json'
TECH=re.compile(r'\b(mix|bass|voice|vocal|reverb|compression|master|mastering|loudness|dynamic range|sound design|texture hạt|grain|pad nền|layer|phối khí|dải tần|synth|verse|điệp khúc|tempo|stereo|frequency)\b',re.I)
FORMAL=re.compile(r'(cho thấy cách|cho thấy một|ví dụ tốt|cái hay của|không cố giảng|ngôn ngữ âm nhạc|chất liệu phật giáo|hướng đi mới|dung hòa yếu tố|không lai căng|bố cục âm nhạc|âm nhạc đương đại|phong cách quen thuộc|thử nghiệm mới nhưng|càng làm càng chắc tay)',re.I)
LEGACY=re.compile(r'(bài này .+ bro ơi|add vào playlist|chill vl|hết bài luôn á|nghe lần đầu mà nổi da gà|có ai thấy .+ hợp nghe|ai giống mình hay bật|nghe .+ rồi quay lại nghe|mình hay mở cho ông bà|không ồn ào mà chạm|không cần nghe kỹ lời|thấy vọng tưởng bớt)',re.I)
PREFERRED=['doithuong','nhinho','lulu','iconly','niem','tanthan','thienvi','reply','quandiem','nhanxet','loibaihat','hook']
WEIGHTS=[23,18,10,7,7,13,8,5,4,2,2,1]

def norm(s):
 s=unicodedata.normalize('NFD',(s or '').lower());s=''.join(c for c in s if unicodedata.category(c)!='Mn')
 return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9 ]',' ',s)).strip()
def toks(s): return set(norm(s).split())
def sim(a,b):
 a,b=toks(a),toks(b)
 return len(a&b)/len(a|b) if a and b else 0.0
def titles():
 try:return json.load(open(TITLEMAP,encoding='utf8'))
 except:return {}
def get_title(tm,track):return tm.get(track,{}).get('title') or track.split(':')[-1].replace('-',' ').title()
def reasons(body,title):
 out=[];nb,nt=norm(body),norm(title)
 if nt and len(nt)>3 and nt in nb:out.append('title_mention')
 if TECH.search(body):out.append('fake_technical')
 if FORMAL.search(body):out.append('essay_boilerplate')
 if LEGACY.search(body):out.append('legacy_template')
 return out

def audit(db):
 tm=titles(); rows=db.execute('select id,track,name,body,parent,ts from comments order by id').fetchall()
 roots=[r for r in rows if r[4]==0]; exact=collections.Counter(norm(r[3]) for r in roots)
 bad=collections.Counter(); mentions=tech=formal=legacy=0
 bytrack=collections.defaultdict(list)
 for r in roots:
  rs=reasons(r[3],get_title(tm,r[1])); bad.update(rs);bytrack[r[1]].append(r)
  mentions+='title_mention' in rs;tech+='fake_technical' in rs;formal+='essay_boilerplate' in rs;legacy+='legacy_template' in rs
 near=0
 for arr in bytrack.values():
  for i,r in enumerate(arr):
   if any(sim(r[3],q[3])>=.78 for q in arr[:i]):near+=1
 return {'total':len(rows),'roots':len(roots),'replies':len(rows)-len(roots),'title_mentions':mentions,'fake_technical':tech,'essay_boilerplate':formal,'legacy_template':legacy,'exact_duplicate_roots':sum(v-1 for v in exact.values() if v>1),'near_duplicate_roots':near,'tracks':len(bytrack)}

def cleanup(min_comments=12,seed=20260712):
 random.seed(seed);db=sqlite3.connect(DB,timeout=60);db.row_factory=sqlite3.Row;tm=titles();now=int(time.time()*1000)
 rows=db.execute('select id,track,name,body,parent,ts from comments order by id').fetchall(); roots={r['id']:r for r in rows if r['parent']==0};children=collections.defaultdict(list)
 for r in rows:
  if r['parent']:children[r['parent']].append(r['id'])
 badroots={};
 for i,r in roots.items():
  rs=reasons(r['body'],get_title(tm,r['track']))
  if rs:badroots[i]=','.join(rs)
 delete=set(badroots);stack=list(delete)
 while stack:
  p=stack.pop()
  for c in children.get(p,[]):
   if c not in delete:delete.add(c);stack.append(c)
 db.execute('BEGIN IMMEDIATE')
 try:
  db.execute('''create table if not exists comments_quarantine(
   original_id integer primary key,track text,name text,body text,ts integer,parent integer,reason text,quarantined_at integer)''')
  for r in rows:
   if r['id'] in delete:
    reason=badroots.get(r['id'],'child_of_rejected_root')
    db.execute('insert or replace into comments_quarantine values(?,?,?,?,?,?,?,?)',(r['id'],r['track'],r['name'],r['body'],r['ts'],r['parent'],reason,now))
  if delete: db.executemany('delete from comments where id=?',[(x,) for x in delete])
  tracks=[r['track'] for r in db.execute("select track from counters where metric='play' and count>0")]
  nick_rows=db.execute('select name from nicks order by name').fetchall();alln=[r['name'] for r in nick_rows]
  global_nick=collections.Counter(r['name'] for r in db.execute('select name from comments'))
  inserted=0; used_pool=[]
  for track in tracks:
   current=db.execute('select body,name from comments where track=?',(track,)).fetchall(); need=max(0,min_comments-len(current))
   if not need:continue
   seen=[r['body'] for r in current]; track_nicks=collections.Counter(r['name'] for r in current); title=get_title(tm,track)
   for _ in range(need):
    chosen=None
    # Try preferred tones with weighted randomness, then global unused pool.
    for attempt in range(300):
     tone=random.choices(PREFERRED,weights=WEIGHTS,k=1)[0]
     cand=db.execute('select id,tone,body from comment_pool where used=0 and tone=? order by random() limit 1',(tone,)).fetchone()
     if not cand:cand=db.execute('select id,tone,body from comment_pool where used=0 order by random() limit 1').fetchone()
     if not cand:break
     rs=reasons(cand['body'],title)
     too_sim=any(sim(cand['body'],x)>=.72 for x in seen)
     if rs or too_sim or len(cand['body'])>180:
      # Do not consume merely because unsuitable for this title; only skip selection.
      continue
     chosen=cand;break
    if not chosen:raise RuntimeError(f'No clean unique pool sentence for {track}; rollback')
    candidates=sorted(alln,key=lambda n:(track_nicks[n],global_nick[n],random.random()))[:30]
    nick=random.choice(candidates)
    ts=now-random.randint(2*3600*1000,12*86400*1000)
    db.execute('insert into comments(track,parent,name,body,ts) values(?,0,?,?,?)',(track,nick,chosen['body'],ts))
    db.execute("update comment_pool set used=1,used_by=?,used_track=?,used_at=? where id=?",(nick,track,ts,chosen['id']))
    seen.append(chosen['body']);track_nicks[nick]+=1;global_nick[nick]+=1;used_pool.append(chosen['id']);inserted+=1
  # hard postconditions within same transaction
  post=audit(db)
  counts=[r[0] for r in db.execute("select count(*) from comments where track in (select track from counters where metric='play' and count>0) group by track")]
  if len(counts)!=len(tracks) or min(counts)<min_comments:raise RuntimeError('postcondition min comments failed')
  if post['title_mentions'] or post['fake_technical'] or post['essay_boilerplate'] or post['legacy_template']:
   raise RuntimeError('postcondition prohibited content remains: '+json.dumps(post,ensure_ascii=False))
  db.commit()
  report={'deleted':len(delete),'deleted_roots':len(badroots),'quarantined':len(delete),'inserted':inserted,'min_comments':min(counts),'post':post}
  (ROOT/'state/comment-cleanup-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  return report
 except Exception:
  db.rollback();raise
 finally:db.close()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['audit','cleanup']);ap.add_argument('--min',type=int,default=12);a=ap.parse_args()
 db=sqlite3.connect(DB);db.row_factory=sqlite3.Row
 if a.action=='audit':print(json.dumps(audit(db),ensure_ascii=False,indent=2));db.close()
 else:db.close();print(json.dumps(cleanup(a.min),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
