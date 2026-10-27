// ─────────────────────────────────────────────────────────────
// TÀNG KINH CÁC — Âm Kinh Backend API  (v2)
// Zero-dependency: Node built-in http + node:sqlite
// Public: lượt nghe (play), reactions (kinh/like/... nhiều loại), comment + reply
// Data shared across ALL visitors (real backend on VPS).
// ─────────────────────────────────────────────────────────────
import { createServer } from 'node:http';
import { DatabaseSync } from 'node:sqlite';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { mkdirSync } from 'node:fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DATA_DIR = join(__dirname, 'data');
mkdirSync(DATA_DIR, { recursive: true });

const PORT = process.env.PORT || 4213;
const db = new DatabaseSync(join(DATA_DIR, 'amkinh.db'));

db.exec(`
  CREATE TABLE IF NOT EXISTS counters (
    track TEXT NOT NULL,
    metric TEXT NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (track, metric)
  );
  CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track TEXT NOT NULL,
    parent INTEGER NOT NULL DEFAULT 0,
    name TEXT NOT NULL DEFAULT 'Ẩn danh',
    body TEXT NOT NULL,
    ts INTEGER NOT NULL
  );
  CREATE INDEX IF NOT EXISTS idx_comments_track ON comments(track, id);
`);

// migrate: add parent column if DB was created by v1
try {
  const cols = db.prepare("PRAGMA table_info(comments)").all().map((c) => c.name);
  if (!cols.includes('parent')) db.exec("ALTER TABLE comments ADD COLUMN parent INTEGER NOT NULL DEFAULT 0");
} catch {}

// ── prepared statements ──
const upsertInc = db.prepare(`
  INSERT INTO counters (track, metric, count) VALUES (?, ?, ?)
  ON CONFLICT(track, metric) DO UPDATE SET count = count + excluded.count
`);
const allCountersForTrack = db.prepare('SELECT metric, count FROM counters WHERE track=?');
const insertComment = db.prepare('INSERT INTO comments (track, parent, name, body, ts) VALUES (?, ?, ?, ?, ?)');
const listComments = db.prepare('SELECT id, parent, name, body, ts FROM comments WHERE track=? ORDER BY id ASC LIMIT ?');
const countComments = db.prepare('SELECT COUNT(*) AS n FROM comments WHERE track=?');
const commentExists = db.prepare('SELECT 1 FROM comments WHERE id=? AND track=?');

// Reactions: kính là chính; các icon "đè để chọn" — tất cả gộp vào 1 nhóm reaction.
// metric play = lượt nghe. Các reaction: kinh, like, sen(🪷), sang(✨), tue(🕉️), tam(❤️‍🩹)...
const REACTIONS = new Set(['kinh', 'like', 'sen', 'sang', 'tue', 'cuoi', 'khoc', 'tym']);
const METRICS = new Set(['play', ...REACTIONS]);

// ── simple per-IP rate limit ──
const hits = new Map();
function rateOk(ip, bucket, max, windowMs) {
  const key = ip + ':' + bucket;
  const now = Date.now();
  const arr = (hits.get(key) || []).filter((t) => now - t < windowMs);
  if (arr.length >= max) { hits.set(key, arr); return false; }
  arr.push(now); hits.set(key, arr); return true;
}
setInterval(() => { if (hits.size > 5000) hits.clear(); }, 10 * 60 * 1000);

function snapshot(track) {
  const c = { play: 0 };
  for (const m of REACTIONS) c[m] = 0;
  for (const row of allCountersForTrack.all(track)) {
    if (row.metric in c) c[row.metric] = row.count;
  }
  // tổng reaction (cho hiển thị gọn nút chính)
  let totalReact = 0;
  for (const m of REACTIONS) totalReact += c[m];
  c.react = totalReact;
  c.comment = countComments.get(track).n;
  return c;
}

function clean(s, max) {
  return String(s ?? '').replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '').trim().slice(0, max);
}

function send(res, code, obj) {
  res.writeHead(code, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Cache-Control': 'no-store',
  });
  res.end(JSON.stringify(obj));
}

function readBody(req) {
  return new Promise((resolve) => {
    let data = ''; let tooBig = false;
    req.on('data', (ch) => { data += ch; if (data.length > 8000) { tooBig = true; req.destroy(); } });
    req.on('end', () => { if (tooBig) return resolve(null); try { resolve(JSON.parse(data || '{}')); } catch { resolve({}); } });
    req.on('error', () => resolve(null));
  });
}

// ── LƯỢT NGHE TỰ NHẢY (anh Nấng chỉ thị 10/07): MỖI TRACK có lịch RIÊNG —
// cứ sau random 2-9 phút tự tăng random 1-3 lượt nghe. Áp dụng mọi track đã có play>0.
const autoNext = new Map(); // track → timestamp lần tăng kế
const likeCredit = new Map(); // track → tín dụng like tích lũy (auto-like theo % view tăng)
function nextDelay() { return (2 + Math.random() * 7) * 60 * 1000; } // 2..9 phút
setInterval(() => {
  try {
    const now = Date.now();
    const rows = db.prepare("SELECT track FROM counters WHERE metric='play' AND count > 0").all();
    for (const r of rows) {
      let due = autoNext.get(r.track);
      if (due === undefined) { autoNext.set(r.track, now + nextDelay()); continue; }
      if (now >= due) {
        const inc = 1 + Math.floor(Math.random() * 3); // 1..3
        upsertInc.run(r.track, 'play', inc);
        // AUTO LIKE (anh Nấng 11/07): mỗi lượt view tăng, cộng dồn "tín dụng" like
        // = 4–13% (random) của số view vừa tăng; đủ 1 thì bung thành reaction thật,
        // loại cảm xúc chọn ngẫu nhiên có trọng số → tăng trưởng tự nhiên theo view.
        likeCredit.set(r.track, (likeCredit.get(r.track) || 0) + inc * (0.04 + Math.random() * 0.09));
        const cr = likeCredit.get(r.track);
        if (cr >= 1) {
          const n = Math.floor(cr);
          likeCredit.set(r.track, cr - n);
          for (let i = 0; i < n; i++) {
            const w = Math.random();
            const m = w < 0.34 ? 'like' : w < 0.58 ? 'kinh' : w < 0.74 ? 'tym' : w < 0.87 ? 'sen' : w < 0.95 ? 'sang' : 'tue';
            upsertInc.run(r.track, m, 1);
          }
        }
        autoNext.set(r.track, now + nextDelay());
      }
    }
    // dọn track không còn tồn tại khỏi lịch
    if (autoNext.size > rows.length * 2) {
      const alive = new Set(rows.map((x) => x.track));
      for (const k of autoNext.keys()) if (!alive.has(k)) autoNext.delete(k);
    }
  } catch {}
}, 30 * 1000);

// ── SNAPSHOTS cho Bảng Xếp Hạng (ngày/tuần/tháng) ──
db.exec(`CREATE TABLE IF NOT EXISTS snapshots (
  ts INTEGER NOT NULL,
  track TEXT NOT NULL,
  play INTEGER NOT NULL DEFAULT 0,
  react INTEGER NOT NULL DEFAULT 0,
  comment INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (ts, track)
)`);
db.exec('CREATE INDEX IF NOT EXISTS idx_snap_track ON snapshots(track, ts)');
const snapIns = db.prepare('INSERT OR REPLACE INTO snapshots(ts,track,play,react,comment) VALUES (?,?,?,?,?)');
const REACT_SUM_SQL = "SELECT track, SUM(CASE WHEN metric='play' THEN count ELSE 0 END) play, SUM(CASE WHEN metric!='play' THEN count ELSE 0 END) react FROM counters GROUP BY track";
function takeSnapshot() {
  try {
    const ts = Date.now();
    const cmap = new Map();
    for (const r of db.prepare('SELECT track, COUNT(*) n FROM comments GROUP BY track').all()) cmap.set(r.track, r.n);
    for (const r of db.prepare(REACT_SUM_SQL).all()) snapIns.run(ts, r.track, r.play || 0, r.react || 0, cmap.get(r.track) || 0);
    // giữ 40 ngày snapshot
    db.prepare('DELETE FROM snapshots WHERE ts < ?').run(ts - 40 * 86400000);
  } catch {}
}
const lastSnap = db.prepare('SELECT MAX(ts) t FROM snapshots').get();
if (!lastSnap.t || Date.now() - lastSnap.t > 55 * 60 * 1000) takeSnapshot();
setInterval(takeSnapshot, 60 * 60 * 1000);

function topList(periodMs, limit) {
  const now = Date.now();
  let base = db.prepare('SELECT MAX(ts) t FROM snapshots WHERE ts <= ?').get(now - periodMs).t;
  if (!base) base = db.prepare('SELECT MIN(ts) t FROM snapshots').get().t;
  const baseMap = new Map();
  if (base) for (const r of db.prepare('SELECT track, play, react, comment FROM snapshots WHERE ts = ?').all(base)) baseMap.set(r.track, r);
  const cmap = new Map();
  for (const r of db.prepare('SELECT track, COUNT(*) n FROM comments GROUP BY track').all()) cmap.set(r.track, r.n);
  const rows = [];
  for (const r of db.prepare(REACT_SUM_SQL).all()) {
    const b = baseMap.get(r.track) || { play: 0, react: 0, comment: 0 };
    const cm = cmap.get(r.track) || 0;
    rows.push({ tid: r.track, play: r.play || 0, like: r.react || 0, comment: cm,
      dPlay: Math.max(0, (r.play || 0) - b.play), dLike: Math.max(0, (r.react || 0) - b.react), dComment: Math.max(0, cm - b.comment) });
  }
  rows.sort((a, z) => z.dPlay - a.dPlay || z.dLike - a.dLike || z.play - a.play);
  return rows.slice(0, limit);
}

const server = createServer(async (req, res) => {
  const ip = (req.headers['x-forwarded-for'] || '').split(',')[0].trim() || req.socket.remoteAddress || 'unknown';
  const url = new URL(req.url, 'http://localhost');
  const path = url.pathname.replace(/^\/api/, '') || '/';

  if (req.method === 'OPTIONS') return send(res, 204, {});

  try {
    if (req.method === 'GET' && path === '/stats') {
      const track = clean(url.searchParams.get('track'), 200) || 'default';
      return send(res, 200, { ok: true, track, stats: snapshot(track) });
    }

    if (req.method === 'GET' && path === '/top') {
      const p = clean(url.searchParams.get('period'), 10) || 'day';
      const periodMs = p === 'month' ? 30 * 86400000 : p === 'week' ? 7 * 86400000 : 86400000;
      const limit = Math.min(50, Math.max(1, parseInt(url.searchParams.get('limit') || '20', 10) || 20));
      return send(res, 200, { ok: true, period: p, items: topList(periodMs, limit) });
    }

    if (req.method === 'GET' && path === '/comments') {
      const track = clean(url.searchParams.get('track'), 200) || 'default';
      let limit = parseInt(url.searchParams.get('limit') || '200', 10);
      if (!Number.isFinite(limit) || limit < 1) limit = 200;
      limit = Math.min(limit, 500);
      const rows = listComments.all(track, limit);
      return send(res, 200, { ok: true, track, comments: rows });
    }

    // POST /hit { track, metric }
    if (req.method === 'POST' && path === '/hit') {
      const b = await readBody(req);
      if (!b) return send(res, 413, { ok: false, error: 'bad body' });
      const track = clean(b.track, 200) || 'default';
      const metric = clean(b.metric, 20);
      if (!METRICS.has(metric)) return send(res, 400, { ok: false, error: 'bad metric' });
      if (!rateOk(ip, 'hit-' + metric, 40, 10000)) {
        return send(res, 429, { ok: false, error: 'too fast', stats: snapshot(track) });
      }
      upsertInc.run(track, metric, 1);
      return send(res, 200, { ok: true, track, stats: snapshot(track) });
    }

    // POST /comment { track, name, body, parent? }
    if (req.method === 'POST' && path === '/comment') {
      const b = await readBody(req);
      if (!b) return send(res, 413, { ok: false, error: 'bad body' });
      const track = clean(b.track, 200) || 'default';
      const name = clean(b.name, 40) || 'Ẩn danh';
      const text = clean(b.body, 800);
      let parent = parseInt(b.parent || '0', 10);
      if (!Number.isFinite(parent) || parent < 0) parent = 0;
      if (!text) return send(res, 400, { ok: false, error: 'empty comment' });
      if (parent > 0 && !commentExists.get(parent, track)) parent = 0; // reply tới comment không tồn tại → top-level
      if (!rateOk(ip, 'comment', 6, 60000)) {
        return send(res, 429, { ok: false, error: 'Bạn gửi hơi nhanh, xin chờ chút.' });
      }
      insertComment.run(track, parent, name, text, Date.now());
      const rows = listComments.all(track, 500);
      return send(res, 200, { ok: true, track, comments: rows, stats: snapshot(track) });
    }

    if (path === '/health') return send(res, 200, { ok: true, service: 'amkinh-backend', v: 2, ts: Date.now() });
    return send(res, 404, { ok: false, error: 'not found' });
  } catch (e) {
    return send(res, 500, { ok: false, error: 'server error' });
  }
});

server.listen(PORT, () => {
  console.log(`[amkinh] v2 backend listening on :${PORT} — db=${join(DATA_DIR, 'amkinh.db')}`);
});
