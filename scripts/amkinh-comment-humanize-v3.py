#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final humanization pass. Quarantine residual AI/reviewer phrasing and every normalized duplicate."""
import collections,json,random,re,sqlite3,time,unicodedata
from pathlib import Path
R=Path('/root/.openclaw/workspace/TangKinhCac');DB=R/'backend/data/amkinh.db';NOW=int(time.time()*1000)
AI=re.compile(r'''(?ix)
(phải\s+nói\s+là)|(^\s*(thiệt\s+tình|công\s+nhận|nói\s+thật\s+là))|
(cách\s+(dùng|xử\s+lý).*(khoảng\s+lặng|âm\s+thanh|giai\s+điệu))|
(người\s+làm\s+(bài|nội\s+dung).*(có\s+tâm|nên\s+học))|
(từng\s+giai\s+điệu\s+đều\s+có\s+hồn)|(giai\s+điệu\s+(đi\s+vào\s+lòng|tối\s+giản|thấm\s+dần))|
(tinh\s+thần\s+từ\s+bi\s+thể\s+hiện)|(văn\s+h[oó]a\s+phật\s+giáo)|
(đạo\s+không\s+xa\s+đời)|(âm\s+nhạc\s+(là\s+cửa|chữa\s+lành|hiện\s+đại))|
(chất\s+liệu\s+dân\s+tộc)|(truyền\s+thống\s+không\s+cũ)|(xứng\s+đáng\s+nhiều\s+người\s+biết)|
(đánh\s+giá\s*:)|(\(\d{2,}\)\s*$)|(productive|focus|deadline\s+dí|bro\s+ơi|chill\s+vl)|
(symbolism|poetic|max\s+level|next\s+level|vibe|series|cinematic\s+buddhist|spa\s+level|lofi\s+is\s+life)|
(tên\s+bài\s+đẹp|ý\s+nghĩa\s+(quá|sâu|lớn|đẹp)|=\s*[a-zà-ỹ]|rồng\s+trong\s+phật\s+giáo|sắc\s+tức\s+thị\s+không\s+qua\s+hình\s+ảnh)|
(ạ\s+ạ)|(hehe\s+hehe)|(hihi\s+hihi)|(🙏\s*🙏\s*🙏)|(❤️\s*❤️\s*❤️)
''')
TECH=re.compile(r'\b(mix|bass|voice|vocal|reverb|compression|master|mastering|loudness|dynamic|sound design|texture|grain|pad nền|layer|phối khí|dải tần|synth|verse|điệp khúc|ambient nền|chuyển đoạn|thu giọng)\b',re.I)
def norm(s):
 s=unicodedata.normalize('NFD',(s or '').lower());s=''.join(c for c in s if unicodedata.category(c)!='Mn')
 return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9 ]',' ',s)).strip()
def sim(a,b):
 a,b=set(norm(a).split()),set(norm(b).split());return len(a&b)/len(a|b) if a and b else 0
OPEN=['Nghe buổi tối','Mở lúc trời mưa','Bật khi pha trà','Nghe trên đường về','Mở lúc dọn nhà','Nghe trước khi ngủ','Bật lúc nghỉ trưa','Nghe trong căn bếp','Mở khi ngồi một mình','Nghe lúc sáng sớm','Bật khi làm việc','Nghe sau một ngày dài','Mở lúc chờ xe','Nghe ngoài ban công','Bật lúc đọc sách','Nghe khi chạy bộ','Mở lúc tưới cây','Nghe khi đường vắng','Bật nhỏ trong phòng','Nghe lúc tan ca','Mở khi đang nấu cơm','Nghe lúc ngồi xe buýt','Bật lúc quán vắng','Nghe khi vừa thức dậy']
FEEL=['thấy lòng dịu lại','tự nhiên bớt căng','nghe êm thật','thấy nhẹ đầu hơn','cảm giác dễ chịu','muốn ngồi thêm chút','nghe càng lúc càng cuốn','thấy không gian chậm lại','tự nhiên nhớ nhà','thấy bình yên ghê','nghe hợp bất ngờ','cảm giác rất vừa vặn','thấy hơi thở chậm hơn','nghe xong ngủ ngon','tự nhiên muốn pha thêm trà','thấy ngày bớt vội','nghe mà mềm lòng','có cảm giác được nghỉ ngơi','thấy mệt mỏi vơi đi','nghe xong muốn gọi về nhà','thấy căn phòng ấm hơn','tự nhiên muốn đi bộ chậm lại','nghe rất hợp khoảnh khắc này','thấy đầu óc thoáng hơn']
TAIL=['á','luôn','thiệt','ghê','nha','đó','🙏','🪷','❤️','một chút','thật sự','hẳn ra','lắm','.','rồi','dễ chịu ghê']
SHORT=['Êm quá trời','Nghe mê thật','Đoạn này cuốn ghê','Bình yên quá','Nghe lại vẫn hay','Tự nhiên thấy vui','Khúc này thích nè','Càng nghe càng ưng','Hợp tai ghê','Nghe đã thật','Giữ lại nghe tiếp','Nghe xong muốn ngồi yên','Bữa nay nghe đúng lúc','Không ồn mà vẫn cuốn','Mộc mạc mà hay','Có duyên mới gặp được','Nghe nhẹ mà thấm','Để đó nghe cả chiều','Vừa bật đã thấy hợp','Chắc tối nay nghe lại','Khúc sau hay hơn nữa','Đang mệt nghe thấy đỡ','Bật nhỏ thôi vẫn thấy hay','Đoạn đầu nghe rất có duyên','Tới khúc này tự nhiên lặng','Một bài để nghe chậm','Không cần nói nhiều, hay','Nghe tới cuối lúc nào không hay','Đúng lúc mình cần nghe','Cứ để bài chạy thôi','Nay nghe thấy hợp hơn hôm qua','Bài này để dành nghe khuya','Nghe một mình cũng vui','Mở loa nhỏ là vừa đẹp','Có chút gì rất thân quen','Nghe xong thấy dễ thở','Lưu lại tối nghe tiếp','Một khúc nghe rất ấm','Đoạn này làm mình nhớ quê']
Q=['Mọi người hay nghe lúc nào?','Có ai đang nghe khuya không?','Đoạn nào mọi người thích nhất?','Nghe bằng tai nghe đã hơn ha?','Có ai bật lại lần hai chưa?','Mọi người nghe lúc trời mưa chưa?','Ai đang pha trà nghe cùng nè?','Có ai nghe cùng gia đình không?','Khúc sau có làm ai bất ngờ không?','Ai đang nghe trên đường về vậy?','Có ai vừa tan ca không?','Mọi người thường mở loa nhỏ hay lớn?','Ai nghe tới cuối rồi nè?','Có ai đang ngồi ngoài ban công không?']
DEV=['A Di Đà Phật 🙏','Mô Phật 🙏','Nghe lòng an hơn 🪷','Một niệm bình an 🙏','Cầu mọi người an lành','Nam Mô Phật 🙏','Chúc cả nhà nhẹ lòng','Nghe trong chánh niệm','Xin gửi một đóa sen 🪷','Bình an trong từng nhịp','Chúc người nghe ngủ ngon','Mong ai cũng được an']
def corpus():
 a=[f'{o} {f} {t}'.replace(' .','.') for o in OPEN for f in FEEL for t in TAIL]+SHORT+Q+DEV
 random.shuffle(a);return a

def run(minc=12):
 random.seed(2026071203);db=sqlite3.connect(DB,timeout=90);db.row_factory=sqlite3.Row
 rows=db.execute('select * from comments order by id').fetchall();children=collections.defaultdict(list)
 for r in rows:
  if r['parent']:children[r['parent']].append(r['id'])
 seen={};bad={};by=collections.defaultdict(list)
 for r in rows:
  if r['parent']==0:by[r['track']].append(r)
 for r in [x for x in rows if x['parent']==0]:
  rs=[];n=norm(r['body'])
  if AI.search(r['body']) or TECH.search(r['body']) or len(r['body'])>155:rs.append('residual_ai_voice')
  if n in seen:rs.append('normalized_global_duplicate')
  else:seen[n]=r['id']
  if rs:bad[r['id']]=','.join(rs)
 # within-track semantic duplicate, lower 0.70
 for t,a in by.items():
  keep=[]
  for r in a:
   if r['id'] in bad:continue
   if any(sim(r['body'],x['body'])>=.70 for x in keep):bad[r['id']]='semantic_duplicate_v3'
   else:keep.append(r)
 delete=set(bad);stack=list(delete)
 while stack:
  for x in children.get(stack.pop(),[]):
   if x not in delete:delete.add(x);stack.append(x)
 db.execute('BEGIN IMMEDIATE')
 try:
  for r in rows:
   if r['id'] in delete:db.execute('insert or replace into comments_quarantine values(?,?,?,?,?,?,?,?)',(r['id'],r['track'],r['name'],r['body'],r['ts'],r['parent'],bad.get(r['id'],'child_v3'),NOW))
  if delete:db.executemany('delete from comments where id=?',[(x,) for x in delete])
  ng=collections.defaultdict(list)
  for r in db.execute('select name,grp from nicks'):ng[r['grp']].append(r['name'])
  groups=['gpt','sonnet5','sonnet46','opus'];tracks=[r['track'] for r in db.execute("select track from counters where metric='play' and count>0")]
  used={norm(r['body']) for r in db.execute('select body from comments where parent=0')};pool=corpus();i=0;ins=0
  for ti,t in enumerate(tracks):
   arr=db.execute('select body,name from comments where track=?',(t,)).fetchall();need=max(0,minc-len(arr));tb=[r['body'] for r in arr];un=set(r['name'] for r in arr)
   for j in range(need):
    body=None
    while i<len(pool):
     x=pool[i];i+=1
     if norm(x) in used or AI.search(x) or TECH.search(x) or any(sim(x,y)>=.65 for y in tb):continue
     body=x;break
    if not body:raise RuntimeError('pool exhausted')
    g=groups[(ti+j)%4];fresh=[n for n in ng[g] if n not in un];name=random.choice(fresh or ng[g]);ts=NOW-random.randint(4*3600*1000,14*86400*1000)
    db.execute('insert into comments(track,parent,name,body,ts) values(?,0,?,?,?)',(t,name,body,ts));used.add(norm(body));tb.append(body);un.add(name);ins+=1
  # final exact + semantic + AI check
  roots=db.execute('select track,body from comments where parent=0').fetchall();cnt=collections.Counter(norm(r['body']) for r in roots);exact=sum(v-1 for v in cnt.values() if v>1);ai=sum(bool(AI.search(r['body']) or TECH.search(r['body']) or len(r['body'])>155) for r in roots);bt=collections.defaultdict(list)
  for r in roots:bt[r['track']].append(r['body'])
  near=sum(any(sim(x,y)>=.70 for y in a[:i]) for a in bt.values() for i,x in enumerate(a));counts=[r[0] for r in db.execute('select count(*) from comments group by track')]
  if exact or ai or near or min(counts)<minc:raise RuntimeError(f'fail exact={exact} ai={ai} near={near} min={min(counts)}')
  db.commit();rep={'quarantined_v3':len(delete),'inserted_v3':ins,'total':db.execute('select count(*) from comments').fetchone()[0],'roots':len(roots),'exact_duplicates':exact,'semantic_duplicates':near,'residual_ai_voice':ai,'min_comments':min(counts)};(R/'state/comment-humanize-v3-report.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n');print(json.dumps(rep,ensure_ascii=False,indent=2))
 except:db.rollback();raise
 finally:db.close()
if __name__=='__main__':run()
