// SEED lượt nghe khởi điểm cho track mới (random 80-400) — node --experimental-sqlite
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';

const db = new DatabaseSync('/root/.openclaw/workspace/TangKinhCac/backend/data/amkinh.db');
const gen = JSON.parse(readFileSync('/root/.openclaw/workspace/TangKinhCac/website/src/data/amkinh-tieutam.gen.json', 'utf8'));
const get = db.prepare("SELECT count FROM counters WHERE track=? AND metric='play'");
const ins = db.prepare("INSERT INTO counters (track,metric,count) VALUES (?,?,?) ON CONFLICT(track,metric) DO NOTHING");
let seeded = 0, existed = 0;
for (const al of gen.albums) {
  for (const t of al.tracks) {
    const id = `tieu-tam:${al.slug}:${t.slug}`;
    const row = get.get(id);
    if (row && row.count > 0) { existed++; continue; }
    ins.run(id, 'play', 80 + Math.floor(Math.random() * 321));
    seeded++;
  }
}
console.log(JSON.stringify({ seeded, existed }));
