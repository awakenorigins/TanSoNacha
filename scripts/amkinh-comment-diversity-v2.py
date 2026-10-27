#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pass-2 global diversity cleanup for Am Kinh synthetic comments.
- One normalized root sentence globally (except ultra-short devotional/icon utterances).
- No near-duplicates within a track.
- Quarantine malformed phrase-bank output and descendants.
- Refill to >=12 comments/track using globally unique, title-free natural sentences.
- Rebalance root authors across four nick groups, max one root per nick/track when possible.
"""
import collections,json,random,re,sqlite3,time,unicodedata
from pathlib import Path
ROOT=Path('/root/.openclaw/workspace/TangKinhCac');DB=ROOT/'backend/data/amkinh.db';NOW=int(time.time()*1000)
MALFORMED=re.compile(r'\b(nói thật là nói thật|công nhận công nhận|thiệt tình thiệt tình|ui ui|chà chà|hihi hihi|hehe hehe)\b',re.I)
OVER_SERIOUS=re.compile(r'(xã hội hiện đại đang rất cần|đưa giáo lý tới gần người trẻ|tiếp cận phật pháp qua âm nhạc|nghệ thuật và đạo lý hoà quyện|gìn giữ văn hoá bằng ngôn ngữ mới|định hướng thế này đáng trân trọng|sản phẩm thế này|truyền thống không cũ)',re.I)
TECH=re.compile(r'\b(mix|bass|voice|vocal|reverb|compression|master|mastering|loudness|dynamic|sound design|texture|grain|pad nền|layer|phối khí|dải tần|synth|verse|điệp khúc)\b',re.I)
ALLOW_REPEAT=re.compile(r'^(🙏|🪷|❤️|a di đà phật|mô phật|nam mô phật|nam mô a di đà phật)[🙏🪷❤️ .]*$',re.I)
def norm(s):
 s=unicodedata.normalize('NFD',(s or '').lower());s=''.join(c for c in s if unicodedata.category(c)!='Mn')
 return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9 ]',' ',s)).strip()
def sim(a,b):
 a,b=set(norm(a).split()),set(norm(b).split());return len(a&b)/len(a|b) if a and b else 0
# Natural title-free phrase generator. Combinations are checked globally before insert.
OPEN=['Nghe buổi tối','Mở lúc trời mưa','Bật khi pha trà','Nghe trên đường về','Mở lúc dọn nhà','Nghe trước khi ngủ','Bật lúc nghỉ trưa','Nghe trong căn bếp','Mở khi ngồi một mình','Nghe lúc sáng sớm','Bật khi làm việc','Nghe sau một ngày dài','Mở lúc chờ xe','Nghe ngoài ban công','Bật lúc đọc sách','Nghe khi chạy bộ','Mở lúc tưới cây','Nghe khi đường vắng']
FEEL=['thấy lòng dịu lại','tự nhiên bớt căng','nghe êm thật','thấy nhẹ đầu hơn','cảm giác dễ chịu','muốn ngồi thêm chút','nghe càng lúc càng cuốn','thấy không gian chậm lại','tự nhiên nhớ nhà','thấy bình yên ghê','nghe hợp bất ngờ','cảm giác rất vừa vặn','thấy hơi thở chậm hơn','nghe xong ngủ ngon','tự nhiên muốn pha thêm trà','thấy ngày bớt vội','nghe mà mềm lòng','có cảm giác được nghỉ ngơi']
TAIL=['á','luôn','thiệt','ghê','nha','đó','🙏','🪷','❤️','một chút','thật sự','dễ sợ','hẳn ra','lắm','.']
SHORT=['Êm quá trời','Nghe mê thật','Đoạn này cuốn ghê','Bình yên quá','Nghe lại vẫn hay','Tự nhiên thấy vui','Khúc này thích nè','Càng nghe càng ưng','Hợp tai ghê','Nghe đã thật','Giữ lại nghe tiếp','Lâu rồi mới thấy êm vậy','Nghe xong muốn ngồi yên','Bữa nay nghe đúng lúc','Không ồn mà vẫn cuốn','Mộc mạc mà hay','Có duyên mới gặp được','Nghe nhẹ mà thấm','Để đó nghe cả chiều','Vừa bật đã thấy hợp','Khúc sau hay hơn nữa','Đang mệt nghe thấy đỡ','Nghe cùng cả nhà cũng hợp','Mẹ mình cũng thích kiểu này','Bật nhỏ thôi vẫn thấy hay','Chắc tối nay nghe lại','Đoạn đầu nghe rất có duyên','Tới khúc này tự nhiên lặng','Một bài để nghe chậm','Không cần nói nhiều, hay']
QUEST=['Mọi người hay nghe lúc nào?','Có ai đang nghe khuya không?','Đoạn nào mọi người thích nhất?','Nghe bằng tai nghe đã hơn ha?','Có ai bật lại lần hai chưa?','Mọi người nghe lúc trời mưa chưa?','Ai đang pha trà nghe cùng nè?','Có ai nghe cùng gia đình không?','Khúc sau có làm ai bất ngờ không?','Ai đang nghe trên đường về vậy?']
DEV=['A Di Đà Phật 🙏','Mô Phật 🙏','Nghe lòng an hơn 🪷','Một niệm bình an 🙏','Cầu mọi người an lành','Nam Mô Phật 🙏','Chúc cả nhà nhẹ lòng','Nghe trong chánh niệm','Xin gửi một đóa sen 🪷','Bình an trong từng nhịp']

def candidates():
 out=[]
 for a in OPEN:
  for b in FEEL:
   for t in TAIL:out.append(f'{a} {b} {t}'.replace(' .','.'))
 out+=SHORT+QUEST+DEV
 random.shuffle(out);return out

def run(min_comments=12):
 random.seed(2026071202);db=sqlite3.connect(DB,timeout=90);db.row_factory=sqlite3.Row
 rows=db.execute('select id,track,name,body,parent,ts from comments order by id').fetchall();children=collections.defaultdict(list)
 for r in rows:
  if r['parent']:children[r['parent']].append(r['id'])
 roots=[r for r in rows if r['parent']==0];bad={};seen_global={};bytrack=collections.defaultdict(list)
 for r in roots:bytrack[r['track']].append(r)
 # malformed/over-serious/global exact duplicate roots
 for r in roots:
  n=norm(r['body']);reason=[]
  if MALFORMED.search(r['body']):reason.append('malformed_bank')
  if OVER_SERIOUS.search(r['body']):reason.append('over_serious')
  if TECH.search(r['body']):reason.append('technical')
  if not ALLOW_REPEAT.match(r['body'].strip()):
   if n in seen_global:reason.append('global_exact_duplicate')
   else:seen_global[n]=r['id']
  if reason:bad[r['id']]=','.join(reason)
 # near duplicates within each track, keep earlier ID
 for t,a in bytrack.items():
  kept=[]
  for r in a:
   if r['id'] in bad:continue
   if any(sim(r['body'],q['body'])>=.76 for q in kept):bad[r['id']]='track_near_duplicate'
   else:kept.append(r)
 delete=set(bad);stack=list(delete)
 while stack:
  for c in children.get(stack.pop(),[]):
   if c not in delete:delete.add(c);stack.append(c)
 db.execute('BEGIN IMMEDIATE')
 try:
  db.execute('''create table if not exists comments_quarantine(
   original_id integer primary key,track text,name text,body text,ts integer,parent integer,reason text,quarantined_at integer)''')
  for r in rows:
   if r['id'] in delete:
    db.execute('insert or replace into comments_quarantine values(?,?,?,?,?,?,?,?)',(r['id'],r['track'],r['name'],r['body'],r['ts'],r['parent'],bad.get(r['id'],'child_of_rejected_root_v2'),NOW))
  if delete:db.executemany('delete from comments where id=?',[(i,) for i in delete])
  # Load nick groups and create balanced cycles.
  ng=collections.defaultdict(list)
  for r in db.execute('select name,grp from nicks'):ng[r['grp']].append(r['name'])
  groups=['gpt','sonnet5','sonnet46','opus']
  tracks=[r['track'] for r in db.execute("select track from counters where metric='play' and count>0")]
  global_bodies={norm(r['body']) for r in db.execute('select body from comments where parent=0')}
  pool=candidates();pi=0;inserted=0
  for ti,track in enumerate(tracks):
   current=db.execute('select id,name,body,parent from comments where track=? order by id',(track,)).fetchall();need=max(0,min_comments-len(current))
   track_bodies=[r['body'] for r in current if r['parent']==0]
   track_used=collections.Counter(r['name'] for r in current)
   for j in range(need):
    body=None
    while pi<len(pool):
     x=pool[pi];pi+=1;n=norm(x)
     if n in global_bodies:continue
     if any(sim(x,y)>=.70 for y in track_bodies):continue
     body=x;break
    if body is None:raise RuntimeError('candidate exhaustion')
    grp=groups[(ti+j)%len(groups)];choices=sorted(ng[grp],key=lambda n:(track_used[n],random.random()))[:20];name=random.choice(choices)
    ts=NOW-random.randint(3*3600*1000,14*86400*1000)
    db.execute('insert into comments(track,parent,name,body,ts) values(?,0,?,?,?)',(track,name,body,ts))
    global_bodies.add(norm(body));track_bodies.append(body);track_used[name]+=1;inserted+=1
  # Rebalance root author names per track across four groups, one-by-one. Existing synthetic names may be outside nicks.
  global_use=collections.Counter()
  for ti,track in enumerate(tracks):
   arr=db.execute('select id,name from comments where track=? and parent=0 order by id',(track,)).fetchall();used=set()
   for i,r in enumerate(arr):
    grp=groups[(ti+i)%4];choices=sorted(ng[grp],key=lambda n:(n in used,global_use[n],random.random()))[:25];name=random.choice(choices)
    db.execute('update comments set name=? where id=?',(name,r['id']));used.add(name);global_use[name]+=1
  # Replies must not self-reply.
  for r in db.execute('select id,parent,name from comments where parent!=0').fetchall():
   p=db.execute('select name from comments where id=?',(r['parent'],)).fetchone()
   if p and p['name']==r['name']:
    choices=[n for g in groups for n in ng[g] if n!=p['name']];db.execute('update comments set name=? where id=?',(random.choice(choices),r['id']))
  counts=[r[0] for r in db.execute("select count(*) from comments where track in (select track from counters where metric='play' and count>0) group by track")]
  # hard audit
  roots2=db.execute('select track,body from comments where parent=0').fetchall();cnt=collections.Counter(norm(r['body']) for r in roots2 if not ALLOW_REPEAT.match(r['body'].strip()))
  exact=sum(v-1 for v in cnt.values() if v>1);mal=sum(bool(MALFORMED.search(r['body']) or OVER_SERIOUS.search(r['body']) or TECH.search(r['body'])) for r in roots2)
  near=0; bt=collections.defaultdict(list)
  for r in roots2:bt[r['track']].append(r['body'])
  for a in bt.values():
   for i,x in enumerate(a):near+=any(sim(x,y)>=.76 for y in a[:i])
  if min(counts)<min_comments or exact or mal or near:raise RuntimeError(f'post failed min={min(counts)} exact={exact} malformed={mal} near={near}')
  db.commit();rep={'quarantined_v2':len(delete),'inserted_v2':inserted,'total':db.execute('select count(*) from comments').fetchone()[0],'roots':len(roots2),'replies':db.execute('select count(*) from comments where parent!=0').fetchone()[0],'min_comments':min(counts),'global_exact_duplicate_roots':exact,'track_near_duplicate_roots':near,'malformed_or_technical':mal,'author_groups':'round-robin gpt/sonnet5/sonnet46/opus'}
  (ROOT/'state/comment-diversity-v2-report.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(rep,ensure_ascii=False,indent=2))
 except Exception:db.rollback();raise
 finally:db.close()
if __name__=='__main__':run()
