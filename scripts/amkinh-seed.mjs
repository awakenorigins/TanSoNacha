#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { DatabaseSync } from 'node:sqlite';

const ROOT = path.resolve(import.meta.dirname, '..');
const db = new DatabaseSync(path.join(ROOT, 'backend/data/amkinh.db'));
const dataText = fs.readFileSync(path.join(ROOT, 'website/src/data/amkinh-gen.ts'), 'utf8') + '\n' + fs.readFileSync(path.join(ROOT, 'website/src/data/amkinh.ts'), 'utf8');
const personas = JSON.parse(fs.readFileSync(path.join(ROOT, 'scripts/amkinh-personas.json'), 'utf8'));
const args = new Set(process.argv.slice(2));
const dry = args.has('--dry-run');
const limitArg = process.argv.find(a => a.startsWith('--limit='));
const limit = limitArg ? Number(limitArg.split('=')[1]) : 45;

function slugify(s){return String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/đ/g,'d').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');}
const albumBlocks = [...dataText.matchAll(/slug:\s*['"]([^'"]+)['"][\s\S]{0,1800}?tracks:\s*\[([\s\S]*?)\n\s*\]/g)];
const tracks=[];
for (const [, albumSlug, block] of albumBlocks) {
  for (const m of block.matchAll(/slug:\s*['"]([^'"]+)['"][\s\S]{0,500}?title:\s*['"]([^'"]+)['"][\s\S]{0,700}?ready:\s*true/g)) {
    tracks.push({tid:`tieu-tam:${albumSlug}:${m[1]}`, title:m[2].replace(/\\'/g,"'")});
  }
}
// fallback: include existing counter tracks
for (const r of db.prepare('select distinct track tid from counters where track like ?').all('tieu-tam:%')) if(!tracks.find(t=>t.tid===r.tid)) tracks.push({tid:r.tid,title:r.tid.split(':').pop().replace(/-/g,' ')});

const getStats = db.prepare(`select metric,count from counters where track=?`);
const upsertCounter = db.prepare(`insert into counters(track,metric,count) values(?,?,?) on conflict(track,metric) do update set count=excluded.count`);
const getCommentCount = db.prepare(`select count(*) n from comments where track=?`);
const getBodies = db.prepare(`select body from comments where track=?`);
const insertComment = db.prepare(`insert into comments(track,parent,name,body,ts) values(?,0,?,?,?)`);
function stats(tid){ const s={play:0,like:0}; for(const r of getStats.all(tid)) s[r.metric]=r.count; s.comment=getCommentCount.get(tid).n; return s; }
function hash(s){let h=2166136261; for(const c of s) h=(h^c.charCodeAt(0))*16777619>>>0; return h;}
function rnd(seed){let x=seed>>>0; return ()=>((x=(1664525*x+1013904223)>>>0)/4294967296);}
const templates=[
  t=>`Nghe ${t} thấy lòng chậm lại hẳn. Cảm ơn Âm Kinh.`,
  t=>`${t} bản này có cái nền rất an, nghe ban đêm hợp lắm.`,
  t=>`Con nghe xong tự nhiên muốn ngồi yên thêm vài phút.`,
  t=>`Nam mô, bài này chạm đúng lúc cần buông bớt.`,
  t=>`Giọng và nhịp vào rất nhẹ, không bị phô. Mình thích đoạn giữa.`,
  t=>`Sáng mở ${t} thấy ngày dịu hơn nhiều.`,
  t=>`cám ơn nha, nghe mà bớt rối trong đầu`,
  t=>`Bài này nên để repeat lúc tụng xong, rất hợp.`,
  t=>`Mẹ mình nghe cũng khen êm, không bị ồn.`,
  t=>`Có một cảm giác rất sạch, như dọn lại trong tâm.`
];
const batch = tracks.sort((a,b)=>hash(a.tid)-hash(b.tid)).slice(0, Math.max(1, limit));
let changed=0;
for (const tr of batch) {
  const r=rnd(hash(tr.tid)); const st=stats(tr.tid); const play=Math.max(st.play||0, 120+Math.floor(r()*1600));
  const targetLike=Math.floor(play*(0.08+r()*0.05)); const targetComment=Math.floor(play*(0.03+r()*0.03));
  const newLike=Math.min(targetLike, (st.like||0)+Math.max(1, Math.ceil((targetLike-(st.like||0))*0.22)));
  const existing=new Set(getBodies.all(tr.tid).map(x=>x.body));
  const addComments=Math.max(0, Math.min(4, targetComment-(st.comment||0)));
  if (!dry) {
    if ((st.play||0)<play) upsertCounter.run(tr.tid,'play',play);
    if ((st.like||0)<newLike) upsertCounter.run(tr.tid,'like',newLike);
    for(let i=0;i<addComments;i++){
      const p=personas[Math.floor(r()*personas.length)]; let body=templates[Math.floor(r()*templates.length)](tr.title.replace(/\s*\([^)]*\)/g,'').trim());
      if(existing.has(body)) body += ` ${['🙏','ạ','nhé','...'][Math.floor(r()*4)]}`;
      existing.add(body); const ts=Date.now()-Math.floor((r()*72*3600+r()*3600)*1000);
      insertComment.run(tr.tid,p.name.slice(0,40),body,ts);
    }
  }
  changed++;
}
console.log(JSON.stringify({ok:true,dry,tracks:tracks.length,processed:batch.length,changed},null,2));
db.close();
