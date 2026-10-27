// ─────────────────────────────────────────────────────────────
// PHƯỚC PHIẾU — Backend acc (Tần Số Nacha)
// Zero-dep: Node http + node:sqlite. Port 4214.
// Voucher (QR) → activate → user (Pháp Danh) → login by scan/token → Sổ Duyên.
// Token: TD/KT/NN-[13 ký tự]-[số thứ tự]
// ─────────────────────────────────────────────────────────────
import { createServer } from 'node:http';
import { DatabaseSync } from 'node:sqlite';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { mkdirSync } from 'node:fs';
import { randomBytes, createHash, timingSafeEqual } from 'node:crypto';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DATA_DIR = process.env.PP_DATA_DIR || join(__dirname, 'data');
mkdirSync(DATA_DIR, { recursive: true });
const DB_PATH = process.env.PP_DB_PATH || join(DATA_DIR, 'phuocphieu.db');
const PORT = process.env.PORT || 4214;
const ADMIN_TOKEN = process.env.PP_ADMIN || 'ChauNacha';
const SITE = 'https://tangkinhcac.62.146.238.213.sslip.io';

const db = new DatabaseSync(DB_PATH);
db.exec(`
  CREATE TABLE IF NOT EXISTS vouchers (
    code TEXT PRIMARY KEY,           -- mã QR đầy đủ: TD-XXXX...-0001
    pham TEXT NOT NULL,              -- truc-duyen / kim-tam / nguyen-niem
    prefix TEXT NOT NULL,           -- TD/KT/NN
    seq INTEGER NOT NULL,           -- số thứ tự
    status TEXT NOT NULL DEFAULT 'new',  -- new | activated
    owner TEXT,                     -- token user (khi đã kích hoạt)
    created INTEGER NOT NULL,
    activated INTEGER
  );
  CREATE TABLE IF NOT EXISTS users (
    token TEXT PRIMARY KEY,         -- = mã voucher (dùng làm token luôn)
    phapdanh TEXT NOT NULL,
    phapdanh_key TEXT,             -- pháp danh chuẩn hoá (lower, bỏ dấu cách) để login
    matma_hash TEXT,              -- hash mật mã (sha256+salt)
    email TEXT,
    pham TEXT NOT NULL,
    rank INTEGER NOT NULL,
    phuoc INTEGER NOT NULL DEFAULT 0,
    duyen INTEGER NOT NULL DEFAULT 0,
    created INTEGER NOT NULL,
    last_seen INTEGER
  );
  CREATE TABLE IF NOT EXISTS ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT NOT NULL,
    kind TEXT NOT NULL,             -- gieo-duyen | an-tong | rut-manh | ...
    text TEXT NOT NULL,
    phuoc INTEGER NOT NULL DEFAULT 0,
    duyen INTEGER NOT NULL DEFAULT 0,
    ts INTEGER NOT NULL
  );
  CREATE INDEX IF NOT EXISTS idx_ledger_token ON ledger(token, id);
  CREATE INDEX IF NOT EXISTS idx_vouchers_pham ON vouchers(pham, seq);

  -- M9 Chứng Duyên: opaque, single-use invite bound only on successful activation.
  CREATE TABLE IF NOT EXISTS invite_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    inviter_token TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','claimed','expired','revoked')),
    created INTEGER NOT NULL,
    expires INTEGER NOT NULL,
    claimed_by TEXT UNIQUE,
    claimed INTEGER,
    reward_ledger_id INTEGER UNIQUE,
    FOREIGN KEY(inviter_token) REFERENCES users(token),
    FOREIGN KEY(claimed_by) REFERENCES users(token),
    FOREIGN KEY(reward_ledger_id) REFERENCES ledger(id)
  );
  CREATE INDEX IF NOT EXISTS idx_invite_daily ON invite_codes(inviter_token,created);
  CREATE INDEX IF NOT EXISTS idx_invite_status_expiry ON invite_codes(status,expires);
  CREATE TABLE IF NOT EXISTS invite_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invite_id INTEGER NOT NULL,
    inviter_token TEXT NOT NULL,
    phapdanh TEXT NOT NULL,
    phapdanh_key TEXT NOT NULL,
    matma_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','accepted','rejected')),
    created INTEGER NOT NULL,
    decided INTEGER,
    created_token TEXT UNIQUE,
    receipt_hash TEXT UNIQUE,
    UNIQUE(invite_id),
    FOREIGN KEY(invite_id) REFERENCES invite_codes(id),
    FOREIGN KEY(inviter_token) REFERENCES users(token),
    FOREIGN KEY(created_token) REFERENCES users(token)
  );
  CREATE INDEX IF NOT EXISTS idx_invite_requests_inbox ON invite_requests(inviter_token,status,created DESC);

  -- ĐÓNG GÓP của user (nhạc/bài/podcast/video) — đăng thật → duyệt → +Phước + hiện công khai
  CREATE TABLE IF NOT EXISTS contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT NOT NULL,            -- ai đăng
    phapdanh TEXT NOT NULL,
    ctype TEXT NOT NULL,           -- track | post | podcast | video
    title TEXT NOT NULL,
    body TEXT,                     -- mô tả / nội dung bài viết
    media_kind TEXT,               -- upload | link
    media_url TEXT,                -- link ngoài (youtube/tiktok/fb/soundcloud) hoặc path file upload
    platform TEXT,                 -- youtube | tiktok | facebook | soundcloud | direct | none
    embed_url TEXT,                -- URL nhúng auto-play (suy ra từ media_url)
    cover TEXT,
    status TEXT NOT NULL DEFAULT 'pending', -- pending | approved | rejected | flagged
    phuoc_reward INTEGER NOT NULL DEFAULT 0,
    ai_verdict TEXT,               -- pass | reject | unsure (tổng hợp 2 model)
    ai_note TEXT,                  -- lý do AI
    ai_models TEXT,                -- JSON kết quả từng model
    reviewer TEXT,                 -- admin duyệt tay (nếu có)
    created INTEGER NOT NULL,
    reviewed INTEGER
  );
  CREATE INDEX IF NOT EXISTS idx_contrib_status ON contributions(status, id);
  CREATE INDEX IF NOT EXISTS idx_contrib_token ON contributions(token, id);

  -- INBOX (tin nhắn user↔user + thông báo từ Thủ Các) — tham khảo Telegram/Messenger
  CREATE TABLE IF NOT EXISTS im_threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    a_token TEXT NOT NULL,         -- 2 phía (system = 'SYSTEM')
    b_token TEXT NOT NULL,
    pair_key TEXT UNIQUE,          -- chuẩn hoá cặp để không tạo trùng thread
    last_ts INTEGER NOT NULL DEFAULT 0,
    last_body TEXT,
    created INTEGER NOT NULL
  );
  CREATE TABLE IF NOT EXISTS im_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id INTEGER NOT NULL,
    from_token TEXT NOT NULL,      -- 'SYSTEM' cho thông báo Thủ Các
    from_name TEXT NOT NULL,
    body TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'text', -- text | system | contrib-warn
    meta TEXT,                     -- JSON (ví dụ contribution id)
    read_a INTEGER NOT NULL DEFAULT 0, -- a đã đọc?
    read_b INTEGER NOT NULL DEFAULT 0,
    ts INTEGER NOT NULL
  );
  CREATE INDEX IF NOT EXISTS idx_im_thread ON im_messages(thread_id, id);
  CREATE INDEX IF NOT EXISTS idx_im_threads_a ON im_threads(a_token, last_ts);
  CREATE INDEX IF NOT EXISTS idx_im_threads_b ON im_threads(b_token, last_ts);
`);
try { db.exec('ALTER TABLE invite_requests ADD COLUMN receipt_hash TEXT'); } catch {}
db.exec('CREATE UNIQUE INDEX IF NOT EXISTS idx_invite_receipt ON invite_requests(receipt_hash) WHERE receipt_hash IS NOT NULL');

const PHAM = {
  TD: { pham: 'truc-duyen', name: 'Trúc Duyên', rank: 1 },
  KT: { pham: 'kim-tam', name: 'Kim Tâm', rank: 2 },
  NN: { pham: 'nguyen-niem', name: 'Nguyên Niệm', rank: 3 },
};

// ── THANG PHẨM theo điểm Phước (Phương án B: ×10 đường Tự Thân) ──
// Mỗi entry: ngưỡng Phước tối thiểu để đạt phẩm đó.
// Phẩm 1-6 leo bằng điểm; phẩm 7-10 ngưỡng cao (phiếu cao/góp lớn); phẩm 11-15 KHÔNG theo điểm (xét công nhận) → không tự lên.
const PHAM_THANG = [
  { rank: 1,  slug: 'truc-duyen',        name: 'Trúc Duyên',           nguong: 100 },
  { rank: 2,  slug: 'kim-tam',           name: 'Kim Tâm',              nguong: 1000 },
  { rank: 3,  slug: 'nguyen-niem',       name: 'Nguyên Niệm',          nguong: 10000 },
  { rank: 4,  slug: 'phuc-co-ky',        name: 'Phúc Cơ Kỳ',           nguong: 100000 },
  { rank: 5,  slug: 'thien-mong-ky',     name: 'Thiên Mông Kỳ',         nguong: 1000000 },
  { rank: 6,  slug: 'hop-dao-ky',        name: 'Hợp Đạo Kỳ',          nguong: 10000000 },
  { rank: 7,  slug: 'do-duyen-tien',     name: 'Độ Duyên Tiên',        nguong: 100000000 },
  { rank: 8,  slug: 'thien-duyen-tien',  name: 'Thiên Duyên Tiên',      nguong: 1000000000 },
  { rank: 9,  slug: 'kim-duyen-tien',    name: 'Kim Duyên Tiên',        nguong: 10000000000 },
  { rank: 10, slug: 'dai-dao-duyen-tien',name: 'Đại Đạo Duyên Tiên',  nguong: 100000000000 },
];
// Phẩm cao nhất đạt được bằng điểm = rank 10. Phẩm 11+ do admin trao (không qua hàm này).
const MAX_RANK_BY_POINTS = 10;
function phamTheoPhuoc(phuoc) {
  let cur = PHAM_THANG[0];
  for (const p of PHAM_THANG) { if (phuoc >= p.nguong) cur = p; else break; }
  return cur; // { rank, slug, name, nguong }
}

// ── BẢNG ĐIỂM HÀNH ĐỘNG (tích Phước) + trần/ngày chống farm ──
// M6: only low-risk self-service actions are accepted by /tich-phuoc.
// Valuable rewards are issued from server-observed, deduplicated proofs.
const PHUOC_ACTIONS = {
  'radio': { phuoc: 20, text: 'Nghe Radio đủ 3 phút', capDay: 1 },
  'diem-danh': { phuoc: 10, text: 'Điểm danh chuyên cần', capDay: 1 },
  'hoi-quang': { phuoc: 5, text: 'Hồi quang sau thời hành trì', capDay: 1 },
};
const PROOF_ACTIONS = {
  'radio': { phuoc: 20, text: 'Nghe Radio đủ 3 phút', capDay: 2 },
  'hoi-quang': { phuoc: 5, text: 'Hồi quang sau thời hành trì', capDay: 1 },
};
const LEGACY_PROOF_ONLY = new Set(['radio','comment','share-story','gioi-thieu','dang-bai','tao-nhac','stream','gieo-duyen']);

// merit_actions is created by the additive social migration; M6 extends it safely.
try { const c=db.prepare("PRAGMA table_info(merit_actions)").all().map(x=>x.name); if(!c.includes('proof_key')) db.exec('ALTER TABLE merit_actions ADD COLUMN proof_key TEXT'); } catch {}
db.exec(`CREATE UNIQUE INDEX IF NOT EXISTS uniq_merit_proof ON merit_actions(user_token,kind,proof_key) WHERE proof_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_merit_actions_daily ON merit_actions(user_token,kind,created);`);


// migrate: thêm cột matma_hash + phapdanh_key + role nếu DB cũ
try {
  const cols = db.prepare("PRAGMA table_info(users)").all().map((c) => c.name);
  if (!cols.includes('matma_hash')) db.exec("ALTER TABLE users ADD COLUMN matma_hash TEXT");
  if (!cols.includes('phapdanh_key')) db.exec("ALTER TABLE users ADD COLUMN phapdanh_key TEXT");
  if (!cols.includes('role')) db.exec("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'");
} catch {}

// ── ADMIN GỐC: Cháu Nacha = admin tối cao (server-side, không client-side) ──
try {
  db.prepare("UPDATE users SET role='admin' WHERE phapdanh_key=?").run('cháu nacha');
} catch (e) { console.error('[phuocphieu] set admin:', e.message); }

// Kiểm tra quyền admin: header X-Admin-Token = ADMIN_TOKEN (legacy cron/AI)
// HOẶC token của user có role='admin' (Cháu Nacha đăng nhập bình thường)
function adminFrom(req, url) {
  const t = req.headers['x-admin-token'] || url.searchParams.get('t') || '';
  if (t && t === ADMIN_TOKEN) return { via: 'key', name: 'Thủ Các' };
  const ut = clean(req.headers['x-pp-token'] || url.searchParams.get('token') || t, 40);
  if (ut) {
    const u = getUser.get(ut);
    if (u && u.role === 'admin') return { via: 'user', name: u.phapdanh, user: u };
  }
  return null;
}

// UNIQUE pháp danh (chặn trùng ở tầng DB). Dùng partial index bỏ null để không vỡ acc cũ chưa có key.
try { db.exec("CREATE UNIQUE INDEX IF NOT EXISTS uniq_phapdanh_key ON users(phapdanh_key) WHERE phapdanh_key IS NOT NULL AND phapdanh_key <> ''"); } catch (e) { console.error('[phuocphieu] uniq index:', e.message); }

// ── statements ──
const getVoucher = db.prepare('SELECT * FROM vouchers WHERE code=?');
const insVoucher = db.prepare('INSERT OR IGNORE INTO vouchers (code,pham,prefix,seq,status,created) VALUES (?,?,?,?,?,?)');
const setVoucherOwner = db.prepare("UPDATE vouchers SET status='activated', owner=?, activated=? WHERE code=?");
const getUser = db.prepare('SELECT * FROM users WHERE token=?');
const insUser = db.prepare('INSERT INTO users (token,phapdanh,phapdanh_key,matma_hash,email,pham,rank,phuoc,duyen,created,last_seen) VALUES (?,?,?,?,?,?,?,?,?,?,?)');
const touchUser = db.prepare('UPDATE users SET last_seen=? WHERE token=?');
const setEmail = db.prepare('UPDATE users SET email=? WHERE token=?');
const setMatma = db.prepare('UPDATE users SET matma_hash=? WHERE token=?');
const findByPhapdanh = db.prepare('SELECT * FROM users WHERE phapdanh_key=?');
const countPhapdanhKey = db.prepare('SELECT COUNT(*) n FROM users WHERE phapdanh_key=?');
const insLedger = db.prepare('INSERT INTO ledger (token,kind,text,phuoc,duyen,ts) VALUES (?,?,?,?,?,?)');
const listLedger = db.prepare('SELECT kind,text,phuoc,duyen,ts FROM ledger WHERE token=? ORDER BY id DESC LIMIT ?');
const countByPham = db.prepare("SELECT pham, COUNT(*) n, SUM(status='activated') act FROM vouchers GROUP BY pham");
// M9 opaque invite codes. Generation cap is five per local calendar day; each code expires after 7 days and is single-use.
const getInvite = db.prepare('SELECT * FROM invite_codes WHERE code=?');
const getInviteById = db.prepare('SELECT * FROM invite_codes WHERE id=?');
const insertInvite = db.prepare("INSERT INTO invite_codes(code,inviter_token,status,created,expires) VALUES(?,?,'active',?,?)");
const countInvitesSince = db.prepare('SELECT COUNT(*) n FROM invite_codes WHERE inviter_token=? AND created>=?');
const listInvites = db.prepare("SELECT code,status,created,expires,claimed FROM invite_codes WHERE inviter_token=? ORDER BY id DESC LIMIT 20");
const claimInvite = db.prepare("UPDATE invite_codes SET status='claimed',claimed_by=?,claimed=?,reward_ledger_id=? WHERE id=? AND status='active' AND claimed_by IS NULL");
const insertInviteRequest = db.prepare("INSERT INTO invite_requests(invite_id,inviter_token,phapdanh,phapdanh_key,matma_hash,status,created,receipt_hash) VALUES(?,?,?,?,?,'pending',?,?)");
const getInviteRequestByReceipt = db.prepare('SELECT status,created,decided FROM invite_requests WHERE receipt_hash=?');
const getInviteRequest = db.prepare('SELECT * FROM invite_requests WHERE id=?');
const listInviteRequests = db.prepare('SELECT id,phapdanh,status,created,decided,created_token FROM invite_requests WHERE inviter_token=? ORDER BY id DESC LIMIT 50');
const decideInviteRequest = db.prepare("UPDATE invite_requests SET status=?,decided=?,created_token=? WHERE id=? AND inviter_token=? AND status='pending'");

// ── SOCIAL M1: public profiles / Bảng Công Đức identity ──
const getUserByPublicId = db.prepare('SELECT * FROM users WHERE public_id=?');
const getUserByPhapdanhKey = db.prepare('SELECT * FROM users WHERE phapdanh_key=?');
const updateSocialProfile = db.prepare(`UPDATE users SET
  avatar_url=?, avatar_seed=?, cover_url=?, bio=?, vow=?, profile_tags=?, profile_visibility=?, profile_updated=?
  WHERE token=?`);
const searchSocialProfiles = db.prepare(`SELECT * FROM users
  WHERE profile_visibility<>'private' AND (lower(phapdanh) LIKE ? OR lower(COALESCE(bio,'')) LIKE ?)
  ORDER BY CASE WHEN lower(phapdanh)=? THEN 0 WHEN lower(phapdanh) LIKE ? THEN 1 ELSE 2 END,
           rank DESC, last_seen DESC LIMIT ?`);
const countProfilePosts = db.prepare("SELECT COUNT(*) n FROM social_posts WHERE author_token=? AND status='active'");
const countProfileFollowers = db.prepare("SELECT COUNT(*) n FROM social_follows WHERE followed_token=? AND status='active'");
const createSocialPost = db.prepare(`INSERT INTO social_posts
  (public_id,author_token,wall_token,kind,body,media_json,link_url,visibility,status,created,updated)
  VALUES (?,?,?,?,?,'[]',NULL,?,'active',?,?)`);
const getSocialPost = db.prepare('SELECT * FROM social_posts WHERE id=?');
const getSocialPostByPublicId = db.prepare('SELECT * FROM social_posts WHERE public_id=?');
const listWallPosts = db.prepare(`SELECT p.*,u.public_id author_public_id,u.phapdanh,u.avatar_url,u.avatar_seed,u.pham,u.rank
  FROM social_posts p JOIN users u ON u.token=p.author_token
  WHERE p.wall_token=? AND p.status='active' AND (p.visibility='public' OR (p.visibility='members' AND ?<>'') OR p.author_token=?)
  AND (?=0 OR p.created<?) ORDER BY p.created DESC,p.id DESC LIMIT ?`);
const listFeedPosts = db.prepare(`SELECT p.*,u.public_id author_public_id,u.phapdanh,u.avatar_url,u.avatar_seed,u.pham,u.rank
  FROM social_posts p JOIN users u ON u.token=p.author_token
  WHERE p.status='active' AND p.visibility IN ('public','members') AND (?=0 OR p.created<?)
  ORDER BY p.created DESC,p.id DESC LIMIT ?`);
const createSocialReply = db.prepare(`INSERT INTO social_replies(public_id,post_id,parent_id,author_token,body,status,created,updated)
  VALUES(?,?,?,?,?,'active',?,?)`);
const getSocialReply = db.prepare('SELECT * FROM social_replies WHERE id=?');
const listSocialReplies = db.prepare(`SELECT r.*,u.public_id author_public_id,u.phapdanh,u.avatar_url,u.avatar_seed,u.pham,u.rank
  FROM social_replies r JOIN users u ON u.token=r.author_token WHERE r.post_id=? AND r.status='active'
  AND (?=0 OR r.created>?) ORDER BY r.created ASC,r.id ASC LIMIT ?`);
const countSocialReply = db.prepare("SELECT COUNT(*) n FROM social_replies WHERE post_id=? AND status='active'");
const getSocialReaction = db.prepare('SELECT 1 ok FROM social_reactions WHERE post_id=? AND user_token=? AND kind=?');
const addSocialReaction = db.prepare('INSERT INTO social_reactions(post_id,user_token,kind,created) VALUES(?,?,?,?)');
const delSocialReaction = db.prepare('DELETE FROM social_reactions WHERE post_id=? AND user_token=? AND kind=?');
const reactionSummary = db.prepare('SELECT kind,COUNT(*) n FROM social_reactions WHERE post_id=? GROUP BY kind');
const softDeletePost = db.prepare("UPDATE social_posts SET status='deleted',body='',updated=? WHERE id=?");
const softDeleteReply = db.prepare("UPDATE social_replies SET status='deleted',body='',updated=? WHERE id=?");
const bumpPostReplies = db.prepare("UPDATE social_posts SET reply_count=(SELECT COUNT(*) FROM social_replies WHERE post_id=? AND status='active'),updated=? WHERE id=?");
const bumpPostReactions = db.prepare("UPDATE social_posts SET reaction_count=(SELECT COUNT(*) FROM social_reactions WHERE post_id=?),updated=? WHERE id=?");
const insertSocialNotification = db.prepare(`INSERT OR IGNORE INTO social_notifications
  (recipient_token,actor_token,kind,entity_type,entity_id,text,created,dedupe_key) VALUES(?,?,?,?,?,?,?,?)`);
const listSocialNotifications = db.prepare(`SELECT n.*,u.public_id actor_public_id,u.phapdanh actor_name,u.avatar_url actor_avatar
  FROM social_notifications n LEFT JOIN users u ON u.token=n.actor_token
  WHERE n.recipient_token=? AND (?=0 OR n.created<?) ORDER BY n.created DESC,n.id DESC LIMIT ?`);
const countUnreadSocialNotifications = db.prepare('SELECT COUNT(*) n FROM social_notifications WHERE recipient_token=? AND read_at IS NULL');
const markAllSocialNotifications = db.prepare('UPDATE social_notifications SET read_at=? WHERE recipient_token=? AND read_at IS NULL');

// ── SOCIAL M5: Radio presence + ephemeral chat ──
const upsertRadioPresence = db.prepare(`INSERT INTO radio_presence(client_id,user_token,item_key,joined,last_seen)
  VALUES(?,?,?,?,?) ON CONFLICT(client_id) DO UPDATE SET user_token=excluded.user_token,item_key=excluded.item_key,last_seen=excluded.last_seen`);
const listRadioPresence = db.prepare(`SELECT p.client_id,p.user_token,p.item_key,p.joined,p.last_seen,u.public_id,u.phapdanh,u.avatar_url,u.avatar_seed
  FROM radio_presence p JOIN users u ON u.token=p.user_token WHERE p.last_seen>=? ORDER BY p.joined ASC LIMIT ?`);
const deleteStaleRadioPresence = db.prepare('DELETE FROM radio_presence WHERE last_seen<?');
const insertRadioChat = db.prepare('INSERT INTO radio_chat(user_token,body,created,expires) VALUES(?,?,?,?)');
const listRadioChat = db.prepare(`SELECT c.id,c.user_token,c.body,c.created,c.expires,u.public_id,u.phapdanh,u.avatar_url,u.avatar_seed
  FROM radio_chat c JOIN users u ON u.token=c.user_token WHERE c.expires>? ORDER BY c.id DESC LIMIT ?`);
const deleteExpiredRadioChat = db.prepare('DELETE FROM radio_chat WHERE expires<?');
const blockedEitherWay = db.prepare(`SELECT 1 FROM social_follows WHERE status='blocked' AND ((follower_token=? AND followed_token=?) OR (follower_token=? AND followed_token=?)) LIMIT 1`);

const RADIO_PRESENCE_TTL = 45_000;
const RADIO_CHAT_TTL = 10 * 60_000;
function radioCleanup(now) { deleteStaleRadioPresence.run(now-RADIO_PRESENCE_TTL); deleteExpiredRadioChat.run(now); }
function radioPerson(r) { return { publicId:r.public_id, phapdanh:r.phapdanh || 'Bạn Đồng Nghe', avatarUrl:r.avatar_url||'', avatarSeed:r.avatar_seed||r.public_id||'', initials:(r.phapdanh||'BD').split(/\s+/).slice(-2).map(x=>x[0]).join('').toUpperCase() }; }

function postJson(row, viewerToken = '') {
  const reactions = Object.fromEntries(reactionSummary.all(row.id).map(x => [x.kind, x.n]));
  return {
    id: row.id, publicId: row.public_id, kind: row.kind, body: row.body,
    visibility: row.visibility, created: row.created, updated: row.updated,
    author: { publicId: row.author_public_id, phapdanh: row.phapdanh, avatarUrl: row.avatar_url || '', avatarSeed: row.avatar_seed || row.author_public_id || '', pham: row.pham, rank: row.rank },
    replyCount: row.reply_count || 0, reactionCount: row.reaction_count || 0, reactions,
    mine: !!viewerToken && row.author_token === viewerToken,
    reacted: !!viewerToken && !!getSocialReaction.get(row.id, viewerToken, 'ket-duyen'),
  };
}

function socialNotify(recipient, actor, kind, entityType, entityId, text, dedupeKey = null) {
  if (!recipient || recipient === actor) return;
  insertSocialNotification.run(recipient, actor || null, kind, entityType || null, String(entityId || ''), clean(text, 240), Date.now(), dedupeKey);
}

// ── CONTRIBUTIONS statements ──
const insContrib = db.prepare(`INSERT INTO contributions
  (token,phapdanh,ctype,title,body,media_kind,media_url,platform,embed_url,cover,status,phuoc_reward,ai_verdict,ai_note,ai_models,created)
  VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`);
const getContrib = db.prepare('SELECT * FROM contributions WHERE id=?');
const listApproved = db.prepare("SELECT id,phapdanh,ctype,title,body,platform,embed_url,media_url,cover,created FROM contributions WHERE status='approved' ORDER BY id DESC LIMIT ? OFFSET ?");
const listByToken = db.prepare('SELECT id,ctype,title,platform,status,phuoc_reward,ai_verdict,created FROM contributions WHERE token=? ORDER BY id DESC LIMIT ?');
const listQueue = db.prepare("SELECT * FROM contributions WHERE status IN ('pending','flagged') ORDER BY id ASC LIMIT ?");
const setContribStatus = db.prepare('UPDATE contributions SET status=?, phuoc_reward=?, reviewer=?, reviewed=? WHERE id=?');
const setContribAI = db.prepare('UPDATE contributions SET ai_verdict=?, ai_note=?, ai_models=?, status=? WHERE id=?');
const countPendingByToken = db.prepare("SELECT COUNT(*) n FROM contributions WHERE token=? AND status IN ('pending','flagged')");

// ── BLOCKLIST tầng 1 (chặn cứng, tức thì) — anh Nấng chỉnh danh sách này dễ ──
const BLOCKLIST = [
  // tục / thù ghét / lừa đảo / cờ bạc / khiêu dâm / thuốc
  'địt','đm','đũ','lồn','cặc','buồi','đĩ','fuck','shit','bitch','porn','sex','xxx','18+','đánh bạc','cá độ','casino','lô đề',
  'vay nóng','tín dụng đen','lừa đảo','scam','kiếm tiền nhanh','xịt lô','đánh đề','sextoy','ma túy','cần sa','hàng đá',
];
function hitBlocklist(text) {
  const low = String(text || '').toLowerCase();
  return BLOCKLIST.find((w) => low.includes(w)) || null;
}

// ── INBOX statements + helper ──
const getThreadByPair = db.prepare('SELECT * FROM im_threads WHERE pair_key=?');
const getThreadById = db.prepare('SELECT * FROM im_threads WHERE id=?');
const insThread = db.prepare('INSERT INTO im_threads (a_token,b_token,pair_key,last_ts,last_body,created) VALUES (?,?,?,?,?,?)');
const updThread = db.prepare('UPDATE im_threads SET last_ts=?, last_body=? WHERE id=?');
const insMsg = db.prepare('INSERT INTO im_messages (thread_id,from_token,from_name,body,kind,meta,read_a,read_b,ts) VALUES (?,?,?,?,?,?,?,?,?)');
const listThreadsForA = db.prepare('SELECT * FROM im_threads WHERE a_token=? OR b_token=? ORDER BY last_ts DESC LIMIT ?');
const listMsgs = db.prepare('SELECT id,from_token,from_name,body,kind,meta,ts FROM im_messages WHERE thread_id=? ORDER BY id ASC LIMIT ?');
const markReadA = db.prepare('UPDATE im_messages SET read_a=1 WHERE thread_id=? AND read_a=0');
const markReadB = db.prepare('UPDATE im_messages SET read_b=1 WHERE thread_id=? AND read_b=0');
const unreadForToken = db.prepare(`
  SELECT COALESCE(SUM(CASE
    WHEN t.a_token=?1 THEN (SELECT COUNT(*) FROM im_messages m WHERE m.thread_id=t.id AND m.read_a=0 AND m.from_token<>?1)
    WHEN t.b_token=?1 THEN (SELECT COUNT(*) FROM im_messages m WHERE m.thread_id=t.id AND m.read_b=0 AND m.from_token<>?1)
    ELSE 0 END),0) AS n
  FROM im_threads t WHERE t.a_token=?1 OR t.b_token=?1`);

function pairKey(x, y) { return [String(x), String(y)].sort().join('|'); }
// tạo/lấy thread giữa 2 token, trả về row thread
function ensureThread(t1, t2, now) {
  const pk = pairKey(t1, t2);
  let th = getThreadByPair.get(pk);
  if (!th) { insThread.run(t1, t2, pk, now, '', now); th = getThreadByPair.get(pk); }
  return th;
}
// gửi 1 tin vào thread
function sendMsg(th, fromToken, fromName, body, kind, meta, now) {
  // read flag: người gửi coi như đã đọc phía mình
  const readA = (th.a_token === fromToken) ? 1 : 0;
  const readB = (th.b_token === fromToken) ? 1 : 0;
  insMsg.run(th.id, fromToken, fromName, body, kind || 'text', meta ? JSON.stringify(meta) : null, readA, readB, now);
  updThread.run(now, body.slice(0, 120), th.id);
}
// thông báo hệ thống (Thủ Các) tới 1 user
function notifyUser(toToken, body, kind, meta) {
  const now = Date.now();
  const th = ensureThread('SYSTEM', toToken, now);
  sendMsg(th, 'SYSTEM', 'Thủ Các', body, kind || 'system', meta, now);
}
const existsPhapdanh = db.prepare('SELECT token FROM users WHERE phapdanh_key=?');
const addPhuoc = db.prepare('UPDATE users SET phuoc=phuoc+?, last_seen=? WHERE token=?');
const setPhamRank = db.prepare('UPDATE users SET pham=?, rank=? WHERE token=?');
const setVoucherMerged = db.prepare("UPDATE vouchers SET status='merged', owner=?, activated=? WHERE code=?");
const countActionToday = db.prepare("SELECT COUNT(*) n FROM ledger WHERE token=? AND kind=? AND ts>=?");
const getMeritProof = db.prepare('SELECT * FROM merit_actions WHERE proof_key=?');
const insertMeritProof = db.prepare(`INSERT INTO merit_actions(public_id,user_token,kind,proof_type,proof_json,text,phuoc_awarded,status,created,proof_key) VALUES(?,?,?,?,?,?,?,?,?,?)`);
const listMeritActions = db.prepare(`SELECT public_id,kind,proof_type,text,phuoc_awarded,status,created FROM merit_actions WHERE user_token=? ORDER BY id DESC LIMIT ?`);
const countMeritToday = db.prepare("SELECT COUNT(*) n FROM merit_actions WHERE user_token=? AND kind=? AND status='accepted' AND created>=?");
const insertMeritAction = db.prepare("INSERT OR IGNORE INTO merit_actions(public_id,user_token,kind,proof_key,proof_type,proof_json,text,phuoc_awarded,status,created) VALUES(?,?,?,?,?,?,?,?,'accepted',?)");

// cộng Phước + tự thăng cấp nếu đủ ngưỡng (không hạ cấp, không vượt rank do điểm)
function applyPhuoc(u, deltaPhuoc, kind, text, now) {
  addPhuoc.run(deltaPhuoc, now, u.token);
  insLedger.run(u.token, kind, text, deltaPhuoc, 0, now);
  const u2 = getUser.get(u.token);
  const target = phamTheoPhuoc(u2.phuoc);
  let leveledTo = null;
  // chỉ thăng khi phẩm mới cao hơn hiện tại, và trong phạm vi điểm (rank<=10)
  if (target.rank > u2.rank && target.rank <= MAX_RANK_BY_POINTS) {
    setPhamRank.run(target.slug, target.rank, u2.token);
    insLedger.run(u2.token, 'thang-cap', `Thăng lên phẩm ${target.name}`, 0, 0, now);
    leveledTo = target;
  }
  return { user: getUser.get(u.token), leveledTo };
}

// ── hash mật mã + chuẩn hoá pháp danh ──
const SALT = process.env.PP_SALT || 'nacha-phuoc-phieu-salt-v1';
function hashMatma(s) { return createHash('sha256').update(SALT + '|' + String(s)).digest('hex'); }
function verifyMatma(s, stored) {
  const actual = Buffer.from(hashMatma(s), 'hex');
  const expected = Buffer.from(String(stored || ''), 'hex');
  return actual.length === expected.length && timingSafeEqual(actual, expected);
}
function phapdanhKey(s) {
  return String(s || '').toLowerCase().normalize('NFC').replace(/\s+/g, ' ').trim();
}

// 13 ký tự chữ+số (không gồm ký tự dễ nhầm 0/O/1/I)
const ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
function gen13() {
  const b = randomBytes(13); let s = '';
  for (let i = 0; i < 13; i++) s += ALPHABET[b[i] % ALPHABET.length];
  return s;
}
function clean(s, max) { return String(s ?? '').replace(/[\u0000-\u001F]/g, '').trim().slice(0, max); }

// ── NHẬN DIỆN PLATFORM + SUY RA EMBED AUTO-PLAY từ 1 URL dán vào ──
function parseMedia(rawUrl) {
  const url = String(rawUrl || '').trim();
  if (!url) return { platform: 'none', embed: '' };
  let u;
  try { u = new URL(url); } catch { return { platform: 'invalid', embed: '' }; }
  const host = u.hostname.replace(/^www\./, '').toLowerCase();

  // YouTube (watch / youtu.be / shorts / embed)
  if (host === 'youtube.com' || host === 'm.youtube.com' || host === 'youtu.be' || host === 'youtube-nocookie.com') {
    let id = '';
    if (host === 'youtu.be') id = u.pathname.slice(1);
    else if (u.pathname.startsWith('/shorts/')) id = u.pathname.split('/')[2];
    else if (u.pathname.startsWith('/embed/')) id = u.pathname.split('/')[2];
    else id = u.searchParams.get('v') || '';
    id = (id || '').split(/[?&/]/)[0];
    if (/^[A-Za-z0-9_-]{6,20}$/.test(id))
      return { platform: 'youtube', embed: `https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0&playsinline=1` };
    return { platform: 'youtube', embed: '' };
  }
  // SoundCloud → dùng player oEmbed-style
  if (host === 'soundcloud.com' || host.endsWith('.soundcloud.com')) {
    return { platform: 'soundcloud', embed: `https://w.soundcloud.com/player/?url=${encodeURIComponent(url)}&auto_play=true&hide_related=true&show_comments=false` };
  }
  // TikTok (embed video id)
  if (host === 'tiktok.com' || host.endsWith('.tiktok.com')) {
    const m = u.pathname.match(/\/video\/(\d+)/);
    if (m) return { platform: 'tiktok', embed: `https://www.tiktok.com/embed/v2/${m[1]}` };
    return { platform: 'tiktok', embed: '' }; // link short (vt.tiktok) cần resolve → để admin
  }
  // Facebook video / watch / reel
  if (host === 'facebook.com' || host === 'fb.watch' || host.endsWith('.facebook.com')) {
    return { platform: 'facebook', embed: `https://www.facebook.com/plugins/video.php?href=${encodeURIComponent(url)}&autoplay=true&show_text=false` };
  }
  // Vimeo
  if (host === 'vimeo.com' || host.endsWith('.vimeo.com')) {
    const m = u.pathname.match(/\/(\d+)/);
    if (m) return { platform: 'vimeo', embed: `https://player.vimeo.com/video/${m[1]}?autoplay=1` };
  }
  // File nhạc trực tiếp (.mp3/.m4a/.ogg/.wav)
  if (/\.(mp3|m4a|ogg|oga|wav|aac|flac)(\?|$)/i.test(u.pathname))
    return { platform: 'direct', embed: url };
  // File video trực tiếp
  if (/\.(mp4|webm|mov)(\?|$)/i.test(u.pathname))
    return { platform: 'direct-video', embed: url };

  return { platform: 'other', embed: '' }; // không nhúng được tự động → để admin xem
}

// PHẦN THƯỞNG PHƯỚC theo loại đóng góp (khi được duyệt)
const CONTRIB_REWARD = { track: 80, podcast: 80, video: 60, post: 30 };

function send(res, code, obj) {
  res.writeHead(code, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type,X-Admin-Token,X-PP-Token',
    'Cache-Control': 'no-store',
  });
  res.end(JSON.stringify(obj));
}
function readBody(req) {
  return new Promise((resolve) => {
    let d = ''; let big = false;
    req.on('data', (c) => { d += c; if (d.length > 20000) { big = true; req.destroy(); } });
    req.on('end', () => { if (big) return resolve(null); try { resolve(JSON.parse(d || '{}')); } catch { resolve({}); } });
    req.on('error', () => resolve(null));
  });
}

const hits = new Map();
function rateOk(ip, bucket, max, win) {
  const k = ip + ':' + bucket, now = Date.now();
  const a = (hits.get(k) || []).filter((t) => now - t < win);
  if (a.length >= max) { hits.set(k, a); return false; }
  a.push(now); hits.set(k, a); return true;
}
setInterval(() => { if (hits.size > 5000) hits.clear(); }, 6e5);

function userPublic(u) {
  const cur = PHAM_THANG.find((p) => p.slug === u.pham);
  const next = PHAM_THANG.find((p) => p.rank === (u.rank + 1) && p.rank <= MAX_RANK_BY_POINTS);
  return {
    token: u.token, phapdanh: u.phapdanh, pham: u.pham, rank: u.rank,
    phamName: cur ? cur.name : u.pham,
    phuoc: u.phuoc, duyen: u.duyen,
    nextNguong: next ? next.nguong : null,
    nextPham: next ? next.name : null,
    hasEmail: !!u.email, hasMatma: !!u.matma_hash,
    role: u.role || 'user',
  };
}

// Public social identity: never expose voucher/login token, email, or password hash.
function socialProfile(u, viewerToken = '') {
  const self = !!viewerToken && viewerToken === u.token;
  let tags = [];
  try { const parsed = JSON.parse(u.profile_tags || '[]'); if (Array.isArray(parsed)) tags = parsed.slice(0, 8); } catch {}
  return {
    publicId: u.public_id,
    phapdanh: u.phapdanh,
    avatarUrl: u.avatar_url || '',
    avatarSeed: u.avatar_seed || u.public_id || '',
    coverUrl: u.cover_url || '',
    bio: u.bio || '',
    vow: u.vow || '',
    tags,
    pham: u.pham,
    rank: u.rank,
    role: u.role || 'user',
    visibility: u.profile_visibility || 'public',
    updated: u.profile_updated || null,
    isSelf: self,
  };
}

function authUser(req, url, body = null) {
  const token = clean(req.headers['x-pp-token'] || body?.token || url.searchParams.get('token'), 40);
  return token ? getUser.get(token) : null;
}

function validLocalAsset(value) {
  if (!value) return '';
  const v = clean(value, 240);
  return /^\/(images|avatars)\/[A-Za-z0-9_./-]+\.(png|jpe?g|webp|gif)$/i.test(v) && !v.includes('..') ? v : null;
}

function publicObjectId(prefix = 'n') {
  return `${prefix}_${Date.now().toString(36)}${randomBytes(6).toString('base64url').toLowerCase()}`;
}

function socialAuthor(u) {
  return { publicId: u.public_id, phapdanh: u.phapdanh, avatarUrl: u.avatar_url || '', avatarSeed: u.avatar_seed || u.public_id || '', pham: u.pham, rank: u.rank };
}

// ──────────────────────────────────────────────────────
// RADIO TẦN SỐ — PSEUDO-LIVE ENGINE
// Lịch phát deterministic từ epoch cố định: podcast[i] → nhạc random → podcast[i+1]...
// Random nhạc = seeded PRNG theo chỉ số chu kỳ → MỌI client tính ra CÙNG kết quả,
// không cần lưu state, không stream — client seek đúng giây đang phát.
// ──────────────────────────────────────────────────────
import { readFileSync } from 'node:fs';
const RADIO_EPOCH = 1783677600000; // 2026-07-10 12:00 CEST — mốc bắt đầu đài
const RADIO_GAP = 3; // giây lặng giữa các mục
let RADIO_PODS = [], RADIO_MUSIC = [];
try {
  RADIO_PODS = JSON.parse(readFileSync(join(__dirname, 'radio-podcast.json'), 'utf8'));
  RADIO_MUSIC = JSON.parse(readFileSync(join(__dirname, 'radio-music.json'), 'utf8'));
} catch (e) { console.error('[radio] load lists:', e.message); }

// seeded PRNG (mulberry32) — cùng seed → cùng chuỗi ở mọi nơi
function mulberry32(seed) {
  return function () {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
// chu kỳ n: podcast (n mod P) + 1 bài nhạc random seed n
function radioCycle(n) {
  if (!RADIO_PODS.length || !RADIO_MUSIC.length) return null;
  const pod = RADIO_PODS[((n % RADIO_PODS.length) + RADIO_PODS.length) % RADIO_PODS.length];
  const rnd = mulberry32(1234567 + n * 7919);
  const mus = RADIO_MUSIC[Math.floor(rnd() * RADIO_MUSIC.length)];
  return { pod, mus, len: pod.dur + RADIO_GAP + mus.dur + RADIO_GAP };
}
function radioNow() {
  if (!RADIO_PODS.length || !RADIO_MUSIC.length) return { ok: false, error: 'radio chưa có playlist' };
  let t = (Date.now() - RADIO_EPOCH) / 1000;
  if (t < 0) t = 0;
  // tìm chu kỳ hiện tại (mỗi chu kỳ dài khác nhau vì nhạc random — duyệt tuần tự từ 0,
  // tối đa vài nghìn vòng/năm → nhanh; cache offset từng mốc 1000 chu kỳ để khỏi duyệt lại)
  let n = 0, acc = 0;
  if (!radioNow._cache) radioNow._cache = [{ n: 0, acc: 0 }];
  const cache = radioNow._cache;
  const last = cache[cache.length - 1];
  if (t >= last.acc) { n = last.n; acc = last.acc; }
  for (;;) {
    const c = radioCycle(n);
    if (!c) return { ok: false, error: 'playlist rỗng' };
    if (acc + c.len > t) {
      const off = t - acc;
      let item, offset, next;
      if (off < c.pod.dur) {
        item = { kind: 'podcast', ...c.pod }; offset = off;
        next = { kind: 'music', title: c.mus.title, album: c.mus.album, inSec: Math.round(c.pod.dur + RADIO_GAP - off) };
      } else if (off < c.pod.dur + RADIO_GAP) {
        item = { kind: 'gap' }; offset = 0;
        next = { kind: 'music', title: c.mus.title, album: c.mus.album, inSec: Math.round(c.pod.dur + RADIO_GAP - off) };
      } else if (off < c.pod.dur + RADIO_GAP + c.mus.dur) {
        item = { kind: 'music', ...c.mus }; offset = off - c.pod.dur - RADIO_GAP;
        const nx = radioCycle(n + 1);
        next = { kind: 'podcast', title: nx.pod.title, inSec: Math.round(c.len - off) };
      } else {
        item = { kind: 'gap' }; offset = 0;
        const nx = radioCycle(n + 1);
        next = { kind: 'podcast', title: nx.pod.title, inSec: Math.round(c.len - off) };
      }
      return { ok: true, cycle: n, item, offset: Math.round(offset * 100) / 100, next, serverTime: Date.now() };
    }
    acc += c.len; n += 1;
    if (n % 1000 === 0 && (!cache.length || cache[cache.length - 1].n < n)) cache.push({ n, acc });
    if (n > 500000) return { ok: false, error: 'quá xa lịch' };
  }
}

const server = createServer(async (req, res) => {
  const ip = (req.headers['x-forwarded-for'] || '').split(',')[0].trim() || req.socket.remoteAddress || '?';
  const url = new URL(req.url, 'http://localhost');
  const path = url.pathname.replace(/^\/api\/pp/, '').replace(/^\/pp-api/, '') || '/';
  if (req.method === 'OPTIONS') return send(res, 204, {});

  try {
    if (path === '/health') return send(res, 200, { ok: true, service: 'phuocphieu', ts: Date.now() });

    // ── SOCIAL M1 — hồ sơ công khai, không bao giờ trả raw login token ──
    if (req.method === 'GET' && path === '/profile') {
      const viewer = authUser(req, url);
      const publicId = clean(url.searchParams.get('publicId'), 80);
      const phapdanh = clean(url.searchParams.get('phapdanh'), 30);
      let u = publicId ? getUserByPublicId.get(publicId) : (phapdanh ? getUserByPhapdanhKey.get(phapdanhKey(phapdanh)) : viewer);
      if (!u) return send(res, 404, { ok: false, error: 'Không tìm thấy Pháp Danh' });
      const isSelf = viewer?.token === u.token;
      if (u.profile_visibility === 'private' && !isSelf && viewer?.role !== 'admin') return send(res, 403, { ok: false, error: 'Bảng này đang tĩnh tu' });
      const profile = socialProfile(u, viewer?.token || '');
      profile.stats = { posts: countProfilePosts.get(u.token).n, followers: countProfileFollowers.get(u.token).n };
      return send(res, 200, { ok: true, profile });
    }

    if (req.method === 'POST' && path === '/profile/update') {
      const b = await readBody(req); if (!b) return send(res, 400, { ok: false });
      const u = authUser(req, url, b);
      if (!u) return send(res, 401, { ok: false, error: 'Xin vào cõi trước' });
      if (!rateOk(u.token, 'profile-update', 20, 3600000)) return send(res, 429, { ok: false, error: 'Xin chậm lại một chút' });
      const avatarUrl = validLocalAsset(b.avatarUrl);
      const coverUrl = validLocalAsset(b.coverUrl);
      if (avatarUrl === null || coverUrl === null) return send(res, 400, { ok: false, error: 'Ảnh cần thuộc kho Tần Số Nacha' });
      const avatarSeed = clean(b.avatarSeed || u.avatar_seed || u.public_id, 80);
      const bio = clean(b.bio, 300);
      const vow = clean(b.vow, 120);
      if (hitBlocklist(`${bio} ${vow}`)) return send(res, 400, { ok: false, error: 'Nội dung chưa phù hợp với tinh thần Tần Số Nacha' });
      const rawTags = Array.isArray(b.tags) ? b.tags : [];
      const tags = [...new Set(rawTags.map(x => clean(x, 18)).filter(Boolean))].slice(0, 8);
      if (tags.some(x => hitBlocklist(x))) return send(res, 400, { ok: false, error: 'Thẻ chưa phù hợp' });
      const visibility = ['public','members','private'].includes(b.visibility) ? b.visibility : (u.profile_visibility || 'public');
      updateSocialProfile.run(avatarUrl || '', avatarSeed, coverUrl || '', bio, vow, JSON.stringify(tags), visibility, Date.now(), u.token);
      return send(res, 200, { ok: true, profile: socialProfile(getUser.get(u.token), u.token) });
    }

    if (req.method === 'GET' && path === '/profiles/search') {
      const viewer = authUser(req, url);
      if (!viewer) return send(res, 401, { ok: false, error: 'Xin vào cõi trước' });
      if (!rateOk(viewer.token, 'profile-search', 60, 60000)) return send(res, 429, { ok: false, error: 'Xin chậm lại một chút' });
      const q = clean(url.searchParams.get('q'), 30).toLowerCase();
      if (q.length < 1) return send(res, 200, { ok: true, items: [] });
      const items = searchSocialProfiles.all(`%${q}%`, `%${q}%`, q, `${q}%`, 20).map(row => socialProfile(row, viewer.token));
      return send(res, 200, { ok: true, items });
    }

    // ── SOCIAL M2 — Bài trên Bảng, Lời Ghé Bảng, Kết Duyên ──
    if (req.method === 'POST' && path === '/post/create') {
      const b = await readBody(req); if (!b) return send(res, 400, { ok: false });
      const u = authUser(req, url, b); if (!u) return send(res, 401, { ok: false, error: 'Xin vào cõi trước' });
      if (!rateOk(u.token, 'social-post', 8, 3600000)) return send(res, 429, { ok: false, error: 'Hôm nay lời đã nhiều, xin thong thả một chút' });
      const body = clean(b.body, 4000);
      if (body.length < 2) return send(res, 400, { ok: false, error: 'Xin viết ít nhất một lời trọn ý' });
      if (hitBlocklist(body)) return send(res, 400, { ok: false, error: 'Lời này chưa phù hợp với tinh thần Tần Số Nacha' });
      const wall = b.wallPublicId ? getUserByPublicId.get(clean(b.wallPublicId, 80)) : u;
      if (!wall) return send(res, 404, { ok: false, error: 'Không tìm thấy Bảng muốn ghé' });
      const visibility = ['public','members','private'].includes(b.visibility) ? b.visibility : 'members';
      const now = Date.now();
      const r = createSocialPost.run(publicObjectId('post'), u.token, wall.token, 'post', body, visibility, now, now);
      if (wall.token !== u.token) socialNotify(wall.token, u.token, 'wall-post', 'post', r.lastInsertRowid, `${u.phapdanh} vừa để lại một lời trên Bảng của bạn`, `wall:${r.lastInsertRowid}`);
      const row = db.prepare(`SELECT p.*,u.public_id author_public_id,u.phapdanh,u.avatar_url,u.avatar_seed,u.pham,u.rank FROM social_posts p JOIN users u ON u.token=p.author_token WHERE p.id=?`).get(r.lastInsertRowid);
      return send(res, 201, { ok: true, post: postJson(row, u.token) });
    }

    if (req.method === 'GET' && path === '/posts/user') {
      const viewer = authUser(req, url);
      const owner = url.searchParams.get('publicId') ? getUserByPublicId.get(clean(url.searchParams.get('publicId'), 80)) : (url.searchParams.get('phapdanh') ? getUserByPhapdanhKey.get(phapdanhKey(clean(url.searchParams.get('phapdanh'), 30))) : viewer);
      if (!owner) return send(res, 404, { ok: false, error: 'Không tìm thấy Bảng' });
      if (owner.profile_visibility === 'private' && viewer?.token !== owner.token && viewer?.role !== 'admin') return send(res, 403, { ok: false, error: 'Bảng này đang tĩnh tu' });
      const before = Math.max(0, Number(url.searchParams.get('before')) || 0), limit = Math.min(30, Math.max(1, Number(url.searchParams.get('limit')) || 15));
      const vt = viewer?.token || '';
      const items = listWallPosts.all(owner.token, vt, vt, before, before, limit + 1);
      const more = items.length > limit; if (more) items.pop();
      return send(res, 200, { ok: true, items: items.map(x => postJson(x, vt)), nextCursor: more ? items.at(-1)?.created : null });
    }

    if (req.method === 'GET' && path === '/feed') {
      const viewer = authUser(req, url); if (!viewer) return send(res, 401, { ok: false, error: 'Xin vào cõi trước' });
      const before = Math.max(0, Number(url.searchParams.get('before')) || 0), limit = Math.min(30, Math.max(1, Number(url.searchParams.get('limit')) || 15));
      const items = listFeedPosts.all(before, before, limit + 1); const more = items.length > limit; if (more) items.pop();
      return send(res, 200, { ok: true, items: items.map(x => postJson(x, viewer.token)), nextCursor: more ? items.at(-1)?.created : null });
    }

    if (req.method === 'POST' && path === '/post/delete') {
      const b = await readBody(req); if (!b) return send(res, 400, { ok: false }); const u = authUser(req, url, b);
      if (!u) return send(res, 401, { ok: false }); const p = getSocialPost.get(Number(b.id)); if (!p) return send(res, 404, { ok: false });
      if (p.author_token !== u.token && u.role !== 'admin') return send(res, 403, { ok: false, error: 'Bạn không thể xoá lời của người khác' });
      softDeletePost.run(Date.now(), p.id); return send(res, 200, { ok: true });
    }

    if (req.method === 'POST' && path === '/reply/create') {
      const b = await readBody(req); if (!b) return send(res, 400, { ok: false }); const u = authUser(req, url, b);
      if (!u) return send(res, 401, { ok: false, error: 'Xin vào cõi trước' });
      if (!rateOk(u.token, 'social-reply', 30, 3600000)) return send(res, 429, { ok: false, error: 'Xin thong thả một chút' });
      const p = getSocialPost.get(Number(b.postId)); if (!p || p.status !== 'active') return send(res, 404, { ok: false, error: 'Bài đã không còn' });
      const body = clean(b.body, 1000); if (body.length < 1 || hitBlocklist(body)) return send(res, 400, { ok: false, error: 'Lời ghé chưa phù hợp' });
      let parentId = b.parentId ? Number(b.parentId) : null;
      if (parentId) { const parent = getSocialReply.get(parentId); if (!parent || parent.post_id !== p.id || parent.status !== 'active') return send(res, 400, { ok: false, error: 'Lời đáp không còn' }); if (parent.parent_id) parentId = parent.parent_id; }
      const now = Date.now(); const r = createSocialReply.run(publicObjectId('reply'), p.id, parentId, u.token, body, now, now);
      bumpPostReplies.run(p.id, now, p.id);
      socialNotify(p.author_token, u.token, 'reply', 'post', p.id, `${u.phapdanh} vừa ghé lời trên bài của bạn`, `reply:${r.lastInsertRowid}:owner`);
      if (parentId) { const parent = getSocialReply.get(parentId); socialNotify(parent.author_token, u.token, 'reply-to-reply', 'reply', parentId, `${u.phapdanh} vừa đáp lời bạn`, `reply:${r.lastInsertRowid}:parent`); }
      return send(res, 201, { ok: true, id: Number(r.lastInsertRowid), replyCount: countSocialReply.get(p.id).n });
    }

    if (req.method === 'GET' && path === '/replies') {
      const viewer = authUser(req, url); const postId = Number(url.searchParams.get('postId')); const p = getSocialPost.get(postId);
      if (!p || p.status !== 'active') return send(res, 404, { ok: false });
      const after = Math.max(0, Number(url.searchParams.get('after')) || 0), limit = Math.min(100, Math.max(1, Number(url.searchParams.get('limit')) || 50));
      const rows = listSocialReplies.all(postId, after, after, limit);
      return send(res, 200, { ok: true, items: rows.map(x => ({ id:x.id, publicId:x.public_id, parentId:x.parent_id, body:x.body, created:x.created, mine:viewer?.token===x.author_token, author:{publicId:x.author_public_id,phapdanh:x.phapdanh,avatarUrl:x.avatar_url||'',avatarSeed:x.avatar_seed||x.author_public_id||'',pham:x.pham,rank:x.rank} })) });
    }

    if (req.method === 'POST' && path === '/reply/delete') {
      const b = await readBody(req); if (!b) return send(res, 400, { ok: false }); const u = authUser(req,url,b); if (!u) return send(res,401,{ok:false});
      const r = getSocialReply.get(Number(b.id)); if (!r) return send(res,404,{ok:false}); if(r.author_token!==u.token&&u.role!=='admin')return send(res,403,{ok:false});
      softDeleteReply.run(Date.now(),r.id); bumpPostReplies.run(r.post_id,Date.now(),r.post_id); return send(res,200,{ok:true});
    }

    if (req.method === 'POST' && path === '/reaction/toggle') {
      const b=await readBody(req);if(!b)return send(res,400,{ok:false});const u=authUser(req,url,b);if(!u)return send(res,401,{ok:false,error:'Xin vào cõi trước'});
      const p=getSocialPost.get(Number(b.postId));if(!p||p.status!=='active')return send(res,404,{ok:false});const kind='ket-duyen';const on=!!getSocialReaction.get(p.id,u.token,kind);const now=Date.now();
      if(on)delSocialReaction.run(p.id,u.token,kind);else{addSocialReaction.run(p.id,u.token,kind,now);socialNotify(p.author_token,u.token,'reaction','post',p.id,`${u.phapdanh} vừa Kết Duyên với bài của bạn`,`reaction:${p.id}:${u.token}`)}
      bumpPostReactions.run(p.id,now,p.id);return send(res,200,{ok:true,active:!on,count:reactionSummary.all(p.id).reduce((n,x)=>n+x.n,0)});
    }

    // ── CHUÔNG DUYÊN M2 ──
    if (req.method === 'GET' && path === '/notifications/unread') { const u=authUser(req,url);if(!u)return send(res,401,{ok:false});return send(res,200,{ok:true,unread:countUnreadSocialNotifications.get(u.token).n}); }
    if (req.method === 'GET' && path === '/notifications') { const u=authUser(req,url);if(!u)return send(res,401,{ok:false});const before=Math.max(0,Number(url.searchParams.get('before'))||0),limit=Math.min(50,Math.max(1,Number(url.searchParams.get('limit'))||30));const rows=listSocialNotifications.all(u.token,before,before,limit);return send(res,200,{ok:true,items:rows.map(n=>({id:n.id,kind:n.kind,text:n.text,entityType:n.entity_type,entityId:n.entity_id,read:!!n.read_at,created:n.created,actor:n.actor_token?{publicId:n.actor_public_id,phapdanh:n.actor_name,avatarUrl:n.actor_avatar||''}:null}))}); }
    if (req.method === 'POST' && path === '/notifications/mark-read') { const b=await readBody(req);if(!b)return send(res,400,{ok:false});const u=authUser(req,url,b);if(!u)return send(res,401,{ok:false});markAllSocialNotifications.run(Date.now(),u.token);return send(res,200,{ok:true,unread:0}); }

    // ── RADIO TẦN SỐ (pseudo-live 24/7): podcast liên tục, xen 1 bài nhạc random giữa các tập ──
    // GET /radio/now → { item(kind,file,title,dur), offset, next, startedAgo }
    if (req.method === 'GET' && path === '/radio/now') {
      return send(res, 200, radioNow());
    }

    if (req.method === 'POST' && path === '/radio/ping') {
      const b=await readBody(req); if(!b)return send(res,400,{ok:false}); const u=authUser(req,url,b);
      if(!u)return send(res,401,{ok:false,error:'Xin vào cõi trước để hiện diện cùng mọi người'});
      if(!rateOk(`${u.token}:${ip}`,'radio-ping',20,60000))return send(res,429,{ok:false,error:'Xin chậm lại một chút'});
      const clientId=clean(b.clientId,80), itemKey=clean(b.itemKey,180); if(!/^[A-Za-z0-9_-]{12,80}$/.test(clientId))return send(res,400,{ok:false,error:'Phiên nghe chưa hợp lệ'});
      const now=Date.now(); radioCleanup(now); const old=db.prepare('SELECT joined FROM radio_presence WHERE client_id=?').get(clientId);
      const joined=old?.joined||now;
      upsertRadioPresence.run(clientId,u.token,itemKey,joined,now); touchUser.run(now,u.token);
      // Presence is observational only. Awarding is centralized in /merit/prove so a
      // qualifying ping followed by proof cannot create two rewards with different keys.
      const merit={awarded:false,remainingMs:Math.max(0,180000-(now-joined))};
      return send(res,200,{ok:true,serverTime:now,ttlMs:RADIO_PRESENCE_TTL,merit});
    }
    if (req.method === 'GET' && path === '/radio/presence') {
      const u=authUser(req,url); if(!u)return send(res,401,{ok:false,error:'Xin vào cõi trước'});
      if(!rateOk(`${u.token}:${ip}`,'radio-presence',30,60000))return send(res,429,{ok:false,error:'Xin chậm lại một chút'});
      const now=Date.now(); radioCleanup(now); const rows=listRadioPresence.all(now-RADIO_PRESENCE_TTL,40).filter(r=>!blockedEitherWay.get(u.token,r.user_token,r.user_token,u.token));
      return send(res,200,{ok:true,people:rows.map(r=>({...radioPerson(r),joined:r.joined,lastSeen:r.last_seen})),ttlMs:RADIO_PRESENCE_TTL});
    }
    if (req.method === 'GET' && path === '/radio/chat') {
      const u=authUser(req,url); if(!u)return send(res,401,{ok:false,error:'Xin vào cõi trước'});
      const now=Date.now(); radioCleanup(now); const rows=listRadioChat.all(now,50).filter(r=>!blockedEitherWay.get(u.token,r.user_token,r.user_token,u.token)).reverse();
      return send(res,200,{ok:true,messages:rows.map(r=>({id:r.id,body:r.body,created:r.created,expires:r.expires,author:radioPerson(r)})),ttlMs:RADIO_CHAT_TTL});
    }
    if (req.method === 'POST' && path === '/radio/chat') {
      const b=await readBody(req);if(!b)return send(res,400,{ok:false});const u=authUser(req,url,b);if(!u)return send(res,401,{ok:false,error:'Xin vào cõi trước'});
      if(!rateOk(`${u.token}:${ip}`,'radio-chat',6,60000))return send(res,429,{ok:false,error:'Xin thong thả giữa những lời đồng nghe'});
      const body=clean(b.body,160);if(body.length<1)return send(res,400,{ok:false,error:'Xin gửi một lời ngắn'});if(hitBlocklist(body))return send(res,400,{ok:false,error:'Lời này chưa phù hợp với không gian đồng nghe'});
      const now=Date.now();radioCleanup(now);const r=insertRadioChat.run(u.token,body,now,now+RADIO_CHAT_TTL);return send(res,201,{ok:true,id:Number(r.lastInsertRowid),expires:now+RADIO_CHAT_TTL});
    }

    // M9: create/list opaque Mời Duyên codes. Credentials never appear in links or payloads.
    if (req.method === 'POST' && path === '/invites') {
      const b=await readBody(req); if(!b)return send(res,400,{ok:false}); const u=authUser(req,url,b);
      if(!u)return send(res,401,{ok:false,error:'Xin vào cõi trước'});
      const now=Date.now(), day=new Date(now); day.setHours(0,0,0,0);
      if(countInvitesSince.get(u.token,day.getTime()).n>=5)return send(res,429,{ok:false,error:'Mỗi ngày chỉ mở tối đa 5 Mời Duyên'});
      let code=''; for(let i=0;i<5;i++){ code=randomBytes(18).toString('base64url'); try{insertInvite.run(code,u.token,now,now+7*86400000);break}catch{code=''} }
      if(!code)return send(res,500,{ok:false,error:'Chưa tạo được Mời Duyên'});
      return send(res,201,{ok:true,invite:{code,url:`${SITE}/moi?invite=${encodeURIComponent(code)}`,status:'active',expires:now+7*86400000}});
    }
    if (req.method === 'GET' && path === '/invites') {
      const u=authUser(req,url); if(!u)return send(res,401,{ok:false,error:'Xin vào cõi trước'});
      const now=Date.now(); db.prepare("UPDATE invite_codes SET status='expired' WHERE inviter_token=? AND status='active' AND expires<=?").run(u.token,now);
      return send(res,200,{ok:true,invites:listInvites.all(u.token).map(x=>({code:x.code,url:`${SITE}/moi?invite=${encodeURIComponent(x.code)}`,status:x.status,created:x.created,expires:x.expires,claimed:x.claimed}))});
    }
    if (req.method === 'POST' && path === '/invite/request') {
      const b=await readBody(req); if(!b)return send(res,400,{ok:false});
      if(!rateOk(ip,'invite-request',8,60000))return send(res,429,{ok:false,error:'Xin chậm lại một chút'});
      const code=clean(b.invite,80), phapdanh=clean(b.phapdanh,30), matma=clean(b.matma,60), now=Date.now();
      const inv=getInvite.get(code);
      if(!inv||inv.status!=='active'||inv.expires<=now)return send(res,410,{ok:false,error:'Mời Duyên này đã khép lại'});
      if(!phapdanh)return send(res,400,{ok:false,error:'Xin đặt Pháp Danh'});
      if(matma.length<4)return send(res,400,{ok:false,error:'Mật mã cần ít nhất 4 ký tự'});
      const pkey=phapdanhKey(phapdanh);
      const inviter=getUser.get(inv.inviter_token); if(inviter?.phapdanh_key===pkey)return send(res,409,{ok:false,error:'Bạn không thể tự Chứng Duyên cho chính mình'});
      if(existsPhapdanh.get(pkey))return send(res,409,{ok:false,error:'Pháp Danh này đã có người dùng'});
      const receipt=randomBytes(24).toString('base64url'), receiptHash=createHash('sha256').update(receipt).digest('hex');
      let r; try{r=insertInviteRequest.run(inv.id,inv.inviter_token,phapdanh,pkey,hashMatma(matma),now,receiptHash)}catch{return send(res,409,{ok:false,error:'Lời thỉnh này đã được gửi'});}
      socialNotify(inv.inviter_token,null,'invite-request','invite-request',Number(r.lastInsertRowid),`${phapdanh} đang chờ bạn Chứng Duyên`,`invite-request:${r.lastInsertRowid}`);
      notifyUser(inv.inviter_token,`${phapdanh} đang chờ bạn Chứng Duyên trong Cõi Ta.`,'invite-request',{requestId:Number(r.lastInsertRowid)});
      return send(res,202,{ok:true,pending:true,receipt,message:'Lời thỉnh đã gửi. Xin giữ mã tra cứu và chờ Người Dẫn Duyên chứng nhận.'});
    }
    if (req.method === 'POST' && path === '/invite/status') {
      const b=await readBody(req);if(!b)return send(res,400,{ok:false});if(!rateOk(ip,'invite-status',20,60000))return send(res,429,{ok:false,error:'Xin chậm lại một chút'});
      const receipt=clean(b.receipt,80);if(!receipt)return send(res,400,{ok:false,error:'Xin nhập mã tra cứu'});
      const q=getInviteRequestByReceipt.get(createHash('sha256').update(receipt).digest('hex'));if(!q)return send(res,404,{ok:false,error:'Không tìm thấy lời thỉnh với mã này'});
      const message=q.status==='rejected'?'Lời thỉnh chưa thể được chứng nhận lần này. Xin bạn an lòng; một nhân duyên khác có thể sẽ mở ra.':q.status==='accepted'?'Lời thỉnh đã được chứng nhận. Bạn có thể vào cõi bằng Pháp Danh và Mật Mã đã chọn.':'Lời thỉnh đang được Người Dẫn Duyên lắng nghe.';
      return send(res,200,{ok:true,status:q.status,message,decided:q.decided||null});
    }
    if (req.method === 'GET' && path === '/invite/requests') {
      const u=authUser(req,url);if(!u)return send(res,401,{ok:false,error:'Xin vào cõi trước'});
      return send(res,200,{ok:true,requests:listInviteRequests.all(u.token).map(x=>({id:x.id,phapdanh:x.phapdanh,status:x.status,created:x.created,decided:x.decided}))});
    }
    if (req.method === 'POST' && path === '/invite/decide') {
      const b=await readBody(req);if(!b)return send(res,400,{ok:false});const u=authUser(req,url,b);if(!u)return send(res,401,{ok:false});
      const q=getInviteRequest.get(Number(b.id));if(!q||q.inviter_token!==u.token)return send(res,404,{ok:false,error:'Không tìm thấy lời thỉnh'});
      if(q.status!=='pending')return send(res,409,{ok:false,error:'Lời thỉnh đã được hồi đáp'});
      const now=Date.now();
      if(b.decision==='reject') { decideInviteRequest.run('rejected',now,null,q.id,u.token); return send(res,200,{ok:true,status:'rejected',message:'Đã khép lời thỉnh một cách nhẹ nhàng'}); }
      if(b.decision!=='accept')return send(res,400,{ok:false,error:'Hồi đáp chưa hợp lệ'});
      if(existsPhapdanh.get(q.phapdanh_key))return send(res,409,{ok:false,error:'Pháp Danh này vừa có người dùng'});
      const token=`INV-${randomBytes(18).toString('base64url')}`, inv=getInviteById.get(q.invite_id);
      if(!inv||inv.status!=='active'||inv.expires<=now)return send(res,410,{ok:false,error:'Mời Duyên này đã khép lại'});
      db.exec('BEGIN IMMEDIATE');
      try{
        const fresh=getInviteRequest.get(q.id);if(!fresh||fresh.status!=='pending')throw new Error('already-decided');
        insUser.run(token,q.phapdanh,q.phapdanh_key,q.matma_hash,null,'truc-duyen',1,100,0,now,now);
        insLedger.run(token,'khai-duyen','Khai Duyên phẩm Trúc Duyên · +100 Phước',100,0,now);
        const lr=insLedger.run(u.token,'chung-duyen',`Chứng Duyên thành công: ${q.phapdanh} · +30 Phước`,30,0,now);
        if(claimInvite.run(token,now,Number(lr.lastInsertRowid),inv.id).changes!==1)throw new Error('invite-unavailable');
        addPhuoc.run(30,now,u.token); if(decideInviteRequest.run('accepted',now,token,q.id,u.token).changes!==1)throw new Error('already-decided');
        db.exec('COMMIT');
      }catch(e){db.exec('ROLLBACK');console.error('[invite decide]',e);return send(res,409,{ok:false,error:'Lời thỉnh vừa thay đổi, xin tải lại'});}
      return send(res,200,{ok:true,status:'accepted',created:{phapdanh:q.phapdanh,pham:'truc-duyen',rank:1},reward:30});
    }

    // GET /voucher?code=TD-...-0001 → trạng thái phiếu (để trang /pp/<code> biết new hay đã có chủ)
    if (req.method === 'GET' && path === '/voucher') {
      const code = clean(url.searchParams.get('code'), 40);
      const v = getVoucher.get(code);
      if (!v) return send(res, 404, { ok: false, error: 'Phiếu không tồn tại' });
      const info = PHAM[v.prefix] || {};
      if (v.status === 'activated' && v.owner) {
        const u = getUser.get(v.owner);
        return send(res, 200, { ok: true, status: 'activated', pham: v.pham, name: info.name, user: u ? userPublic(u) : null });
      }
      const startPhuoc = (PHAM_THANG.find((p) => p.slug === v.pham) || {}).nguong ?? (info.rank || 0) * 100;
      return send(res, 200, { ok: true, status: 'new', pham: v.pham, name: info.name, rank: info.rank, startPhuoc });
    }

    // POST /activate { code, phapdanh, matma } → tạo acc, token = code, vào cấp
    if (req.method === 'POST' && path === '/activate') {
      const b = await readBody(req); if (!b) return send(res, 400, { ok: false });
      if (!rateOk(ip, 'act', 20, 60000)) return send(res, 429, { ok: false, error: 'Chậm lại chút nhé' });
      const code = clean(b.code, 40);
      const phapdanh = clean(b.phapdanh, 30);
      const matma = clean(b.matma, 60);
      if (!phapdanh) return send(res, 400, { ok: false, error: 'Xin đặt Pháp Danh' });
      if (!matma || matma.length < 4) return send(res, 400, { ok: false, error: 'Mật mã cần ít nhất 4 ký tự' });
      const v = getVoucher.get(code);
      if (!v) return send(res, 404, { ok: false, error: 'Phiếu không tồn tại' });
      const info = PHAM[v.prefix] || { pham: v.pham, name: v.pham, rank: 0 };
      if (v.status === 'activated' && v.owner) {
        const u = getUser.get(v.owner);
        return send(res, 200, { ok: true, already: true, user: u ? userPublic(u) : null });
      }
      const pkey = phapdanhKey(phapdanh);
      // CHẶN TRÙNG pháp danh (nguyên tắc 2)
      if (existsPhapdanh.get(pkey)) {
        return send(res, 409, { ok: false, error: 'Pháp Danh này đã có người dùng, xin chọn tên khác', dupe: true });
      }
      const now = Date.now();
      // Phước khởi = ngưỡng phẩm của phiếu (TD=100 / KT=1000 / NN=10000)
      const startPhuoc = (PHAM_THANG.find((p) => p.slug === info.pham) || {}).nguong ?? info.rank * 100;
      try {
        insUser.run(code, phapdanh, pkey, hashMatma(matma), null, info.pham, info.rank, startPhuoc, 0, now, now);
      } catch (e) {
        // race: UNIQUE index bắt trùng đúng lúc
        if (String(e.message).includes('UNIQUE')) return send(res, 409, { ok: false, error: 'Pháp Danh vừa có người đặt, xin chọn tên khác', dupe: true });
        throw e;
      }
      setVoucherOwner.run(code, now, code);
      insLedger.run(code, 'khai-duyen', `Khai Duyên phẩm ${info.name} · +${startPhuoc} Phước`, startPhuoc, 0, now);
      const u = getUser.get(code);
      return send(res, 200, { ok: true, created: true, user: userPublic(u) });
    }

    // POST /login { token } → login bằng token/quét QR
    if (req.method === 'POST' && path === '/login') {
      const b = await readBody(req); if (!b) return send(res, 400, { ok: false });
      if (!rateOk(ip, 'login', 30, 60000)) return send(res, 429, { ok: false, error: 'Chậm lại chút nhé' });
      const token = clean(b.token, 40);
      const phapdanh = clean(b.phapdanh, 30), matma = clean(b.matma, 60);
      const u = token ? getUser.get(token) : findByPhapdanh.get(phapdanhKey(phapdanh));
      if (!u || (!token && !verifyMatma(matma, u.matma_hash))) return send(res, 401, { ok: false, error: 'Chìa khoá chưa đúng' });
      if (u.status && u.status !== 'active') return send(res, 403, { ok: false, error: 'Tài khoản chưa hoạt động' });
      touchUser.run(Date.now(), u.token);
      return send(res, 200, { ok: true, user: userPublic(getUser.get(u.token)) });
    }

    // POST /set-matma { token, phapdanh?, matma } → đặt/đổi mật mã (cho acc cũ chưa có, hoặc đổi)
    if (req.method === 'POST' && path === '/set-matma') {
      const b = await readBody(req); if (!b) return send(res, 400, { ok: false });
      const token = clean(b.token, 40);
      const matma = clean(b.matma, 60);
      const phapdanh = clean(b.phapdanh, 30);
      const u = getUser.get(token);
      if (!u) return send(res, 404, { ok: false, error: 'Không tìm thấy' });
      if (!matma || matma.length < 4) return send(res, 400, { ok: false, error: 'Mật mã cần ít nhất 4 ký tự' });
      setMatma.run(hashMatma(matma), token);
      // nếu cũ chưa có phapdanh_key (acc tạo trước khi có login-pass) → set luôn
      const pkey = phapdanhKey(phapdanh || u.phapdanh);
      db.prepare('UPDATE users SET phapdanh_key=? WHERE token=?').run(pkey, token);
      const u2 = getUser.get(token);
      return send(res, 200, { ok: true, user: userPublic(u2) });
    }

    // POST /login-pass { phapdanh, matma } → login bằng Pháp Danh + Mật Mã (không cần QR)
    if (req.method === 'POST' && path === '/login-pass') {
      const b = await readBody(req); if (!b) return send(res, 400, { ok: false });
      if (!rateOk(ip, 'loginpass', 15, 60000)) return send(res, 429, { ok: false, error: 'Chậm lại chút nhé' });
      const pkey = phapdanhKey(clean(b.phapdanh, 30));
      const matma = clean(b.matma, 60);
      if (!pkey || !matma) return send(res, 400, { ok: false, error: 'Xin nhập Pháp Danh và Mật Mã' });
      const u = findByPhapdanh.get(pkey);
      if (!u || !verifyMatma(matma, u.matma_hash)) return send(res, 404, { ok: false, error: 'Pháp Danh hoặc Mật Mã chưa đúng' });
      if (u.status && u.status !== 'active') return send(res, 403, { ok: false, error: 'Tài khoản chưa hoạt động' });
      touchUser.run(Date.now(), u.token);
      return send(res, 200, { ok: true, user: userPublic(u) });
    }

    // GET /account?token=... → thông tin + Sổ Duyên
    if (req.method === 'GET' && path === '/account') {
      const token = clean(url.searchParams.get('token'), 40);
      const u = getUser.get(token);
      if (!u) return send(res, 404, { ok: false, error: 'Không tìm thấy' });
      const so = listLedger.all(token, 50);
      return send(res, 200, { ok: true, user: userPublic(u), soDuyen: so });
    }

    // POST /email { token, email } → bổ sung email sau
    if (req.method === 'POST' && path === '/email') {
      const b = await readBody(req); if (!b) return send(res, 400, { ok: false });
      const token = clean(b.token, 40); const email = clean(b.email, 120);
      if (!getUser.get(token)) return send(res, 404, { ok: false });
      setEmail.run(email, token);
      return send(res, 200, { ok: true });
    }

    // POST /check-phapdanh { phapdanh } → tên còn trống không (để UI check trước)
    if (req.method === 'POST' && path === '/check-phapdanh') {
      const b = await readBody(req); if (!b) return send(res, 400, { ok: false });
      const pkey = phapdanhKey(clean(b.phapdanh, 30));
      if (!pkey) return send(res, 400, { ok: false, error: 'Xin nhập Pháp Danh' });
      const taken = !!existsPhapdanh.get(pkey);
      return send(res, 200, { ok: true, available: !taken, taken });
    }

    // POST /cong-duyen { token, code } → cộng Phước của phiếu vào acc đích, tự thăng cấp
    if (req.method === 'POST' && path === '/cong-duyen') {
      const b = await readBody(req); if (!b) return send(res, 400, { ok: false });
      if (!rateOk(ip, 'cong', 20, 60000)) return send(res, 429, { ok: false, error: 'Chậm lại chút nhé' });
      const token = clean(b.token, 40);
      const code = clean(b.code, 40);
      const u = getUser.get(token);
      if (!u) return send(res, 404, { ok: false, error: 'Không tìm thấy cõi đích' });
      const v = getVoucher.get(code);
      if (!v) return send(res, 404, { ok: false, error: 'Phiếu không tồn tại' });
      if (v.status === 'activated') return send(res, 409, { ok: false, error: 'Phiếu này đã khai duyên thành một cõi riêng, không cộng được' });
      if (v.status === 'merged') return send(res, 409, { ok: false, error: 'Phiếu này đã được cộng duyên trước đó rồi' });
      const info = PHAM[v.prefix] || { pham: v.pham, name: v.pham, rank: 0 };
      const themPhuoc = (PHAM_THANG.find((p) => p.slug === info.pham) || {}).nguong ?? info.rank * 100;
      const now = Date.now();
      const r = applyPhuoc(u, themPhuoc, 'nap-phieu', `Nạp phiếu ${info.name} vào cõi · +${themPhuoc} Phước`, now);
      setVoucherMerged.run(u.token, now, code);
      return send(res, 200, { ok: true, user: userPublic(r.user), added: themPhuoc, leveledTo: r.leveledTo ? { name: r.leveledTo.name, rank: r.leveledTo.rank, slug: r.leveledTo.slug } : null });
    }

    // M6: proof-bound merit. Direct endpoint is deliberately low-risk only.
    if (req.method === 'POST' && path === '/tich-phuoc') {
      const b=await readBody(req); if(!b)return send(res,400,{ok:false}); const u=authUser(req,url,b);
      if(!u)return send(res,401,{ok:false,error:'Xin vào cõi trước'}); if(!rateOk(`${u.token}:${ip}`,'tich',20,60000))return send(res,429,{ok:false,error:'Chậm lại chút nhé'});
      const kind=clean(b.kind,30); const direct={ 'diem-danh':PHUOC_ACTIONS['diem-danh'], 'hoi-quang':PHUOC_ACTIONS['hoi-quang'] };
      if(!direct[kind]) { const routes={radio:'/radio',comment:'/bang-nhan-duyen','share-story':'/bang-nhan-duyen','gioi-thieu':'/vao-coi','dang-bai':'/bang-nhan-duyen','tao-nhac':'/dong-gop/cong-dong',stream:'/dong-gop/cong-dong'}; return send(res,409,{ok:false,proofRequired:true,error:'Phước này chỉ kết khi hành động thật được máy chủ chứng thực.',actionUrl:routes[kind]||'/bang-nhan-duyen'}); }
      const day=new Date();day.setHours(0,0,0,0);const key=`${kind}:${u.token}:${day.getTime()}`;const old=getMeritProof.get(key);if(old)return send(res,200,{ok:true,duplicate:true,capped:true,added:0,user:userPublic(getUser.get(u.token)),message:'Hôm nay duyên này đã được ghi nhận.'});
      const text=kind==='hoi-quang'?clean(b.reflection,280):'';if(kind==='hoi-quang'&&text.length<12)return send(res,400,{ok:false,error:'Xin hồi quang ít nhất 12 ký tự.'});
      const now=Date.now(),act=direct[kind];let result;db.exec('BEGIN IMMEDIATE');try{insertMeritProof.run(`merit_${randomBytes(9).toString('hex')}`,u.token,kind,kind==='hoi-quang'?'reflection':'server-day',JSON.stringify(kind==='hoi-quang'?{length:text.length}:{}),act.text,act.phuoc,'accepted',now,key);result=applyPhuoc(u,act.phuoc,kind,`${act.text} · +${act.phuoc} Phước`,now);db.exec('COMMIT')}catch(e){db.exec('ROLLBACK');if(String(e).includes('UNIQUE'))return send(res,200,{ok:true,duplicate:true,capped:true,added:0,user:userPublic(getUser.get(u.token))});throw e}return send(res,200,{ok:true,added:act.phuoc,user:userPublic(result.user),leveledTo:result.leveledTo});
    }
    if(req.method==='POST'&&path==='/merit/prove'){
      const b=await readBody(req);if(!b)return send(res,400,{ok:false});const u=authUser(req,url,b);if(!u)return send(res,401,{ok:false});const kind=clean(b.kind,30);if(kind!=='radio')return send(res,400,{ok:false,error:'Loại minh chứng không hợp lệ'});const clientId=clean(b.clientId,80);const pr=db.prepare('SELECT joined,last_seen,item_key FROM radio_presence WHERE client_id=? AND user_token=?').get(clientId,u.token);const now=Date.now();if(!pr||now-pr.joined<180000||now-pr.last_seen>RADIO_PRESENCE_TTL)return send(res,200,{ok:true,qualified:false,added:0,remainingMs:Math.max(0,180000-(pr?now-pr.joined:0))});const day=new Date();day.setHours(0,0,0,0);const key=`radio:${u.token}:${day.getTime()}:${pr.item_key||'live'}`;if(getMeritProof.get(key))return send(res,200,{ok:true,duplicate:true,added:0,user:userPublic(getUser.get(u.token))});const act=PHUOC_ACTIONS.radio;let result;db.exec('BEGIN IMMEDIATE');try{insertMeritProof.run(`merit_${randomBytes(9).toString('hex')}`,u.token,'radio','server-presence',JSON.stringify({durationMs:now-pr.joined,itemKey:pr.item_key}),act.text,act.phuoc,'accepted',now,key);result=applyPhuoc(u,act.phuoc,'radio',`${act.text} · +${act.phuoc} Phước`,now);db.exec('COMMIT')}catch(e){db.exec('ROLLBACK');if(String(e).includes('UNIQUE'))return send(res,200,{ok:true,duplicate:true,added:0,user:userPublic(getUser.get(u.token))});throw e}return send(res,200,{ok:true,qualified:true,added:act.phuoc,user:userPublic(result.user),leveledTo:result.leveledTo});
    }
    if(req.method==='GET'&&path==='/merit/actions'){const u=authUser(req,url);if(!u)return send(res,401,{ok:false});return send(res,200,{ok:true,items:listMeritActions.all(u.token,30)});}

    // POST /contribute { token, ctype, title, body, mediaUrl } → user đăng đóng góp
    if (req.method === 'POST' && path === '/contribute') {
      const b = await readBody(req); if (!b) return send(res, 400, { ok: false });
      if (!rateOk(ip, 'contrib', 8, 60000)) return send(res, 429, { ok: false, error: 'Chậm lại chút nhé' });
      const token = clean(b.token, 40);
      const u = getUser.get(token);
      if (!u) return send(res, 404, { ok: false, error: 'Xin vào cõi trước' });
      const ctype = clean(b.ctype, 12);
      if (!['track', 'post', 'podcast', 'video'].includes(ctype)) return send(res, 400, { ok: false, error: 'Loại không hợp lệ' });
      const title = clean(b.title, 120);
      const body = clean(b.body, 2000);
      const mediaUrl = clean(b.mediaUrl, 500);
      if (!title) return send(res, 400, { ok: false, error: 'Xin đặt tiêu đề' });
      if (ctype !== 'post' && !mediaUrl) return send(res, 400, { ok: false, error: 'Xin dán link nhạc/video hoặc tải lên' });
      // giới hạn số bài đang chờ / user (chống spam hàng chờ)
      if (countPendingByToken.get(token).n >= 5) return send(res, 429, { ok: false, error: 'Bạn đang có nhiều bài chờ duyệt — xin đợi Thủ Các soát xong' });
      // TẦNG 1: blocklist chặn cứng
      const bad = hitBlocklist(title + ' ' + body);
      if (bad) return send(res, 200, { ok: false, blocked: true, error: 'Nội dung chưa phù hợp với tinh thần Tần Số Nacha.' });
      const { platform, embed } = parseMedia(mediaUrl);
      const reward = CONTRIB_REWARD[ctype] || 0;
      const now = Date.now();
      insContrib.run(token, u.phapdanh, ctype, title, body, mediaUrl ? 'link' : 'none', mediaUrl, platform, embed, '', 'pending', reward, null, null, null, now);
      return send(res, 200, { ok: true, pending: true, message: `Cảm ơn bạn đã góp một duyên lành tới Ta Bà 🙏 Thủ Các đang soi lại đôi chút — khi duyên ấy được khai mở, nó sẽ ngân giữa cộng đồng và kết thành Phước quay về với chính bạn.` });
    }

    // GET /contributions?limit=&offset= → danh sách đã duyệt (công khai, hiện trên Tần Số Nacha)
    if (req.method === 'GET' && path === '/contributions') {
      let limit = parseInt(url.searchParams.get('limit') || '30', 10); if (!Number.isFinite(limit) || limit < 1) limit = 30; limit = Math.min(limit, 100);
      let offset = parseInt(url.searchParams.get('offset') || '0', 10); if (!Number.isFinite(offset) || offset < 0) offset = 0;
      const rows = listApproved.all(limit, offset);
      return send(res, 200, { ok: true, items: rows });
    }

    // GET /my-contributions?token= → bài của tôi (mọi trạng thái)
    if (req.method === 'GET' && path === '/my-contributions') {
      const token = clean(url.searchParams.get('token'), 40);
      if (!getUser.get(token)) return send(res, 404, { ok: false });
      return send(res, 200, { ok: true, items: listByToken.all(token, 50) });
    }

    // ── INBOX (user↔user + thông báo Thủ Các) ──
    // GET /inbox/unread?token= → số tin chưa đọc
    if (req.method === 'GET' && path === '/inbox/unread') {
      const token = clean(url.searchParams.get('token'), 40);
      if (!getUser.get(token)) return send(res, 404, { ok: false });
      return send(res, 200, { ok: true, unread: unreadForToken.get(token).n });
    }

    // GET /inbox/threads?token= → danh sách hội thoại
    if (req.method === 'GET' && path === '/inbox/threads') {
      const token = clean(url.searchParams.get('token'), 40);
      if (!getUser.get(token)) return send(res, 404, { ok: false });
      const rows = listThreadsForA.all(token, token, 60);
      const items = rows.map((t) => {
        const otherTok = t.a_token === token ? t.b_token : t.a_token;
        let otherName = 'Thủ Các';
        if (otherTok !== 'SYSTEM') { const ou = getUser.get(otherTok); otherName = ou ? ou.phapdanh : 'đạo hữu'; }
        return { id: t.id, otherToken: otherTok, otherName, lastBody: t.last_body, lastTs: t.last_ts, system: otherTok === 'SYSTEM' };
      });
      return send(res, 200, { ok: true, threads: items });
    }

    // GET /inbox/thread?token=&id= → đọc tin + mark read
    if (req.method === 'GET' && path === '/inbox/thread') {
      const token = clean(url.searchParams.get('token'), 40);
      const id = parseInt(url.searchParams.get('id'), 10);
      if (!getUser.get(token)) return send(res, 404, { ok: false });
      const th = getThreadById.get(id);
      if (!th || (th.a_token !== token && th.b_token !== token)) return send(res, 403, { ok: false, error: 'không thuộc về bạn' });
      const msgs = listMsgs.all(id, 300);
      if (th.a_token === token) markReadA.run(id); else markReadB.run(id);
      return send(res, 200, { ok: true, messages: msgs, self: token });
    }

    // POST /inbox/send { token, toToken?, toPhapdanh?, id?, body } → gửi tin cho user khác
    if (req.method === 'POST' && path === '/inbox/send') {
      const b = await readBody(req); if (!b) return send(res, 400, { ok: false });
      if (!rateOk(ip, 'im', 20, 60000)) return send(res, 429, { ok: false, error: 'Chậm lại chút nhé' });
      const token = clean(b.token, 40);
      const u = getUser.get(token);
      if (!u) return send(res, 404, { ok: false, error: 'Xin vào cõi trước' });
      const body = clean(b.body, 1000);
      if (!body) return send(res, 400, { ok: false, error: 'Tin rỗng' });
      const bad = hitBlocklist(body);
      if (bad) return send(res, 200, { ok: false, blocked: true, error: 'Tin nhắn chưa phù hợp.' });
      // xác định người nhận: theo thread id, hoặc toToken, hoặc tìm theo pháp danh
      let toTok = clean(b.toToken, 40);
      const id = parseInt(b.id, 10);
      if (!toTok && Number.isFinite(id)) {
        const th0 = getThreadById.get(id);
        if (th0 && (th0.a_token === token || th0.b_token === token)) toTok = th0.a_token === token ? th0.b_token : th0.a_token;
      }
      if (!toTok && b.toPhapdanh) { const t = db.prepare('SELECT token FROM users WHERE phapdanh_key=?').get(phapdanhKey(clean(b.toPhapdanh, 30))); if (t) toTok = t.token; }
      if (!toTok || toTok === 'SYSTEM') return send(res, 404, { ok: false, error: 'Không tìm thấy người nhận' });
      if (toTok === token) return send(res, 400, { ok: false, error: 'Không thể tự gửi cho mình' });
      if (!getUser.get(toTok)) return send(res, 404, { ok: false, error: 'Người nhận không tồn tại' });
      const now = Date.now();
      const th = ensureThread(token, toTok, now);
      sendMsg(th, token, u.phapdanh, body, 'text', null, now);
      const msgs = listMsgs.all(th.id, 300);
      return send(res, 200, { ok: true, threadId: th.id, messages: msgs, self: token });
    }

    // ── ADMIN (X-Admin-Token = key legacy, HOẶC X-PP-Token của user role=admin) ──
    if (path === '/admin/stats') {
      if (!adminFrom(req, url)) return send(res, 403, { ok: false, error: 'forbidden' });
      const rows = countByPham.all();
      const totalUsers = db.prepare('SELECT COUNT(*) n FROM users').get().n;
      const pendingContrib = db.prepare("SELECT COUNT(*) n FROM contributions WHERE status IN ('pending','flagged')").get().n;
      return send(res, 200, { ok: true, vouchers: rows, totalUsers, pendingContrib });
    }

    // GET /admin/queue → hàng chờ duyệt (pending + flagged)
    if (req.method === 'GET' && path === '/admin/queue') {
      if (!adminFrom(req, url)) return send(res, 403, { ok: false, error: 'forbidden' });
      return send(res, 200, { ok: true, items: listQueue.all(100) });
    }

    // GET /admin/users → danh sách người trong cõi
    if (req.method === 'GET' && path === '/admin/users') {
      if (!adminFrom(req, url)) return send(res, 403, { ok: false, error: 'forbidden' });
      const rows = db.prepare('SELECT token,phapdanh,pham,rank,phuoc,duyen,role,created,last_seen FROM users ORDER BY created DESC LIMIT 500').all();
      return send(res, 200, { ok: true, users: rows });
    }

    // POST /admin/user-adjust { token, phuoc?, pham?, rank?, role?, note? } → admin tùy chỉnh user
    if (req.method === 'POST' && path === '/admin/user-adjust') {
      const adm = adminFrom(req, url);
      if (!adm) return send(res, 403, { ok: false, error: 'forbidden' });
      const b = await readBody(req); if (!b) return send(res, 400, { ok: false });
      const u = getUser.get(clean(b.token, 40));
      if (!u) return send(res, 404, { ok: false, error: 'không tìm thấy người này' });
      const now = Date.now();
      if (Number.isFinite(+b.phuoc) && +b.phuoc !== 0) {
        applyPhuoc(u, Math.trunc(+b.phuoc), 'an-dien', clean(b.note, 200) || `Thủ Các ân điển · ${adm.name}`, now);
      }
      if (b.pham && b.rank) {
        const r = Math.trunc(+b.rank);
        if (r >= 1 && r <= 15) {
          setPhamRank.run(clean(b.pham, 30), r, u.token);
          insLedger.run(u.token, 'thang-cap', `Thủ Các chứng nhận phẩm mới (rank ${r})`, 0, 0, now);
        }
      }
      if (b.role === 'admin' || b.role === 'user') {
        db.prepare('UPDATE users SET role=? WHERE token=?').run(b.role, u.token);
      }
      return send(res, 200, { ok: true, user: userPublic(getUser.get(u.token)) });
    }

    // POST /admin/review { id, action:'approve'|'reject', reviewer? } → duyệt tay + +Phước nếu approve
    if (req.method === 'POST' && path === '/admin/review') {
      const adm = adminFrom(req, url);
      if (!adm) return send(res, 403, { ok: false, error: 'forbidden' });
      const b = await readBody(req); if (!b) return send(res, 400, { ok: false });
      const id = parseInt(b.id, 10);
      const action = clean(b.action, 12);
      const reviewer = clean(b.reviewer, 40) || adm.name;
      const c = getContrib.get(id);
      if (!c) return send(res, 404, { ok: false, error: 'Không tìm thấy bài' });
      if (c.status === 'approved') return send(res, 200, { ok: true, already: true });
      const now = Date.now();
      if (action === 'approve') {
        setContribStatus.run('approved', c.phuoc_reward, reviewer, now, id);
        const u = getUser.get(c.token);
        if (u) applyPhuoc(u, c.phuoc_reward, 'gop-duyen', `Duyên lành “${c.title}” đã khai mở giữa Ta Bà · Phước quay về`, now);
        if (u) notifyUser(c.token, `Duyên lành “${c.title}” của bạn đã được khai mở, giờ ngân giữa cộng đồng Tần Số Nacha 🙏 Duyên bạn gieo ra Ta Bà đã kết thành Phước quay về với bạn.`, 'system', { contribId: id });
        return send(res, 200, { ok: true, approved: true });
      } else if (action === 'reject') {
        const reason = clean(b.reason, 300) || 'Chưa phù hợp với tinh thần Tần Số Nacha';
        setContribStatus.run('rejected', 0, reviewer, now, id);
        notifyUser(c.token, `Bài “${c.title}” của bạn đã được tạm ẩn. Lý do: ${reason}. Xin điều chỉnh và đăng lại — Tần Số Nacha luôn rộng cửa đón bạn 🙏`, 'contrib-warn', { contribId: id });
        return send(res, 200, { ok: true, rejected: true });
      }
      return send(res, 400, { ok: false, error: 'action không hợp lệ' });
    }

    // GET /admin/ai-next → lấy 1 bài pending chưa có AI verdict (cho cron AI chấm)
    if (req.method === 'GET' && path === '/admin/ai-next') {
      if (!adminFrom(req, url)) return send(res, 403, { ok: false, error: 'forbidden' });
      const c = db.prepare("SELECT id,token,phapdanh,ctype,title,body,platform,media_url FROM contributions WHERE status='pending' AND ai_verdict IS NULL ORDER BY id ASC LIMIT 1").get();
      return send(res, 200, { ok: true, item: c || null });
    }

    // POST /admin/ai-verdict { id, verdict:'pass'|'reject'|'unsure', note, models } → cron AI ghi kết quả
    if (req.method === 'POST' && path === '/admin/ai-verdict') {
      if (!adminFrom(req, url)) return send(res, 403, { ok: false, error: 'forbidden' });
      const b = await readBody(req); if (!b) return send(res, 400, { ok: false });
      const id = parseInt(b.id, 10);
      const verdict = clean(b.verdict, 10);
      const note = clean(b.note, 500);
      const models = clean(b.models, 1000);
      const c = getContrib.get(id);
      if (!c) return send(res, 404, { ok: false, error: 'không tìm thấy' });
      const now = Date.now();
      // 2 model đồng ý PASS → auto duyệt + +Phước; REJECT → từ chối; UNSURE/lệch → flagged cho người xem
      if (verdict === 'pass') {
        setContribAI.run('pass', note, models, 'approved', id);
        setContribStatus.run('approved', c.phuoc_reward, 'AI', now, id);
        const u = getUser.get(c.token);
        if (u) applyPhuoc(u, c.phuoc_reward, 'gop-duyen', `Duyên lành “${c.title}” đã khai mở giữa Ta Bà · Phước quay về`, now);
        if (u) notifyUser(c.token, `Duyên lành “${c.title}” của bạn đã được khai mở, giờ ngân giữa cộng đồng Tần Số Nacha 🙏 Duyên bạn gieo ra Ta Bà đã kết thành Phước quay về với bạn.`, 'system', { contribId: id });
        return send(res, 200, { ok: true, approved: true });
      } else if (verdict === 'reject') {
        setContribAI.run('reject', note, models, 'rejected', id);
        notifyUser(c.token, `Bài “${c.title}” của bạn đã được tạm ẩn sau khi soát. Lý do: ${note || 'chưa phù hợp tinh thần Tần Số Nacha'}. Xin điều chỉnh và đăng lại nhé 🙏`, 'contrib-warn', { contribId: id });
        return send(res, 200, { ok: true, rejected: true });
      } else {
        setContribAI.run('unsure', note, models, 'flagged', id); // flagged = chờ người duyệt tay
        return send(res, 200, { ok: true, flagged: true });
      }
    }

    return send(res, 404, { ok: false, error: 'not found' });
  } catch (e) {
    return send(res, 500, { ok: false, error: 'server error' });
  }
});

server.listen(PORT, () => console.log(`[phuocphieu] backend on :${PORT} db=${join(DATA_DIR,'phuocphieu.db')}`));
