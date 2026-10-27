#!/usr/bin/env node
// TẦN SỐ NACHA — Social Milestone 1 migration (additive, idempotent)
// Usage: node --experimental-sqlite migrate-social.mjs [db-path]
import { DatabaseSync } from 'node:sqlite';
import { resolve } from 'node:path';

const dbPath = resolve(process.argv[2] || new URL('./data/phuocphieu.db', import.meta.url).pathname);
const db = new DatabaseSync(dbPath);
db.exec('PRAGMA foreign_keys=ON; PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000;');

function cols(table) { return new Set(db.prepare(`PRAGMA table_info(${table})`).all().map(c => c.name)); }
function add(table, name, sqlType) {
  if (!cols(table).has(name)) db.exec(`ALTER TABLE ${table} ADD COLUMN ${name} ${sqlType}`);
}

// Profile — additive only; auth/token model intentionally unchanged.
add('users', 'public_id', 'TEXT');
add('users', 'avatar_url', 'TEXT');
add('users', 'avatar_seed', 'TEXT');
add('users', 'cover_url', 'TEXT');
add('users', 'bio', 'TEXT');
add('users', 'vow', 'TEXT');
add('users', 'profile_tags', "TEXT NOT NULL DEFAULT '[]'");
add('users', 'profile_visibility', "TEXT NOT NULL DEFAULT 'public'");
add('users', 'profile_updated', 'INTEGER');

// Fill stable public ids without exposing voucher/login tokens.
const missing = db.prepare("SELECT token FROM users WHERE public_id IS NULL OR public_id='' ORDER BY created,token").all();
const hasId = db.prepare('SELECT 1 FROM users WHERE public_id=?');
const setId = db.prepare('UPDATE users SET public_id=? WHERE token=?');
function hashId(s) {
  // Node sqlite migration stays zero-dep; deterministic FNV-1a64-ish public id.
  let h1=0x811c9dc5, h2=0x9e3779b9;
  for (let i=0;i<s.length;i++) { h1=Math.imul(h1^s.charCodeAt(i),0x01000193); h2=Math.imul(h2+s.charCodeAt(i),0x85ebca6b); }
  return `nacha_${(h1>>>0).toString(36)}${(h2>>>0).toString(36)}`;
}
for (const u of missing) {
  let id=hashId(u.token), n=2;
  while (hasId.get(id)) id=`${hashId(u.token)}_${n++}`;
  setId.run(id,u.token);
}

db.exec(`
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_public_id ON users(public_id);
CREATE INDEX IF NOT EXISTS idx_users_last_seen ON users(last_seen DESC);

CREATE TABLE IF NOT EXISTS social_posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  public_id TEXT NOT NULL UNIQUE,
  author_token TEXT NOT NULL,
  wall_token TEXT NOT NULL,
  kind TEXT NOT NULL DEFAULT 'post' CHECK(kind IN ('post','merit','music','scripture','practice','system')),
  body TEXT NOT NULL DEFAULT '',
  media_json TEXT NOT NULL DEFAULT '[]',
  link_url TEXT,
  visibility TEXT NOT NULL DEFAULT 'members' CHECK(visibility IN ('public','members','private')),
  status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','hidden','deleted','pending')),
  created INTEGER NOT NULL,
  updated INTEGER NOT NULL,
  reply_count INTEGER NOT NULL DEFAULT 0,
  reaction_count INTEGER NOT NULL DEFAULT 0,
  score REAL NOT NULL DEFAULT 0,
  FOREIGN KEY(author_token) REFERENCES users(token),
  FOREIGN KEY(wall_token) REFERENCES users(token)
);
CREATE INDEX IF NOT EXISTS idx_posts_feed ON social_posts(status,visibility,created DESC,id DESC);
CREATE INDEX IF NOT EXISTS idx_posts_wall ON social_posts(wall_token,status,created DESC,id DESC);
CREATE INDEX IF NOT EXISTS idx_posts_author ON social_posts(author_token,status,created DESC,id DESC);
CREATE INDEX IF NOT EXISTS idx_posts_kind ON social_posts(kind,status,created DESC);

CREATE TABLE IF NOT EXISTS social_replies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  public_id TEXT NOT NULL UNIQUE,
  post_id INTEGER NOT NULL,
  parent_id INTEGER,
  author_token TEXT NOT NULL,
  body TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','hidden','deleted','pending')),
  created INTEGER NOT NULL,
  updated INTEGER NOT NULL,
  FOREIGN KEY(post_id) REFERENCES social_posts(id) ON DELETE CASCADE,
  FOREIGN KEY(parent_id) REFERENCES social_replies(id) ON DELETE CASCADE,
  FOREIGN KEY(author_token) REFERENCES users(token)
);
CREATE INDEX IF NOT EXISTS idx_replies_post ON social_replies(post_id,status,created,id);
CREATE INDEX IF NOT EXISTS idx_replies_parent ON social_replies(parent_id,status,created,id);

CREATE TABLE IF NOT EXISTS social_reactions (
  post_id INTEGER NOT NULL,
  user_token TEXT NOT NULL,
  kind TEXT NOT NULL DEFAULT 'ket-duyen' CHECK(kind IN ('ket-duyen','sen','tri-an','tuy-hy')),
  created INTEGER NOT NULL,
  PRIMARY KEY(post_id,user_token,kind),
  FOREIGN KEY(post_id) REFERENCES social_posts(id) ON DELETE CASCADE,
  FOREIGN KEY(user_token) REFERENCES users(token)
);
CREATE INDEX IF NOT EXISTS idx_reactions_user ON social_reactions(user_token,created DESC);

CREATE TABLE IF NOT EXISTS social_notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  recipient_token TEXT NOT NULL,
  actor_token TEXT,
  kind TEXT NOT NULL,
  entity_type TEXT,
  entity_id TEXT,
  text TEXT NOT NULL DEFAULT '',
  read_at INTEGER,
  created INTEGER NOT NULL,
  dedupe_key TEXT,
  FOREIGN KEY(recipient_token) REFERENCES users(token),
  FOREIGN KEY(actor_token) REFERENCES users(token)
);
CREATE INDEX IF NOT EXISTS idx_notifications_inbox ON social_notifications(recipient_token,read_at,created DESC,id DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_notifications_dedupe ON social_notifications(recipient_token,dedupe_key) WHERE dedupe_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS social_follows (
  follower_token TEXT NOT NULL,
  followed_token TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','muted','blocked')),
  created INTEGER NOT NULL,
  PRIMARY KEY(follower_token,followed_token),
  CHECK(follower_token<>followed_token),
  FOREIGN KEY(follower_token) REFERENCES users(token),
  FOREIGN KEY(followed_token) REFERENCES users(token)
);
CREATE INDEX IF NOT EXISTS idx_follows_followed ON social_follows(followed_token,status,created DESC);

CREATE TABLE IF NOT EXISTS social_reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  reporter_token TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  reason TEXT NOT NULL,
  detail TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','reviewed','dismissed','actioned')),
  created INTEGER NOT NULL,
  reviewed INTEGER,
  reviewer TEXT,
  FOREIGN KEY(reporter_token) REFERENCES users(token)
);
CREATE INDEX IF NOT EXISTS idx_reports_queue ON social_reports(status,created,id);

CREATE TABLE IF NOT EXISTS merit_actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  public_id TEXT NOT NULL UNIQUE,
  user_token TEXT NOT NULL,
  kind TEXT NOT NULL,
  proof_type TEXT NOT NULL DEFAULT 'self',
  proof_json TEXT NOT NULL DEFAULT '{}',
  text TEXT NOT NULL DEFAULT '',
  phuoc_awarded INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'accepted' CHECK(status IN ('accepted','pending','rejected','revoked')),
  created INTEGER NOT NULL,
  reviewed INTEGER,
  reviewer TEXT,
  proof_key TEXT,
  FOREIGN KEY(user_token) REFERENCES users(token)
);
CREATE INDEX IF NOT EXISTS idx_merit_user ON merit_actions(user_token,status,created DESC,id DESC);
CREATE INDEX IF NOT EXISTS idx_merit_review ON merit_actions(status,created,id);

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
 id INTEGER PRIMARY KEY AUTOINCREMENT, invite_id INTEGER NOT NULL, inviter_token TEXT NOT NULL,
 phapdanh TEXT NOT NULL, phapdanh_key TEXT NOT NULL, matma_hash TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','accepted','rejected')),
 created INTEGER NOT NULL, decided INTEGER, created_token TEXT UNIQUE, receipt_hash TEXT UNIQUE,
 UNIQUE(invite_id), FOREIGN KEY(invite_id) REFERENCES invite_codes(id),
 FOREIGN KEY(inviter_token) REFERENCES users(token), FOREIGN KEY(created_token) REFERENCES users(token)
);
CREATE INDEX IF NOT EXISTS idx_invite_requests_inbox ON invite_requests(inviter_token,status,created DESC);

CREATE TABLE IF NOT EXISTS social_schema_migrations (
  version TEXT PRIMARY KEY,
  applied INTEGER NOT NULL,
  note TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS radio_presence (
  client_id TEXT PRIMARY KEY,
  user_token TEXT NOT NULL,
  item_key TEXT NOT NULL DEFAULT '',
  joined INTEGER NOT NULL,
  last_seen INTEGER NOT NULL,
  FOREIGN KEY(user_token) REFERENCES users(token) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_radio_presence_seen ON radio_presence(last_seen DESC);

CREATE TABLE IF NOT EXISTS radio_chat (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_token TEXT NOT NULL,
  body TEXT NOT NULL,
  created INTEGER NOT NULL,
  expires INTEGER NOT NULL,
  FOREIGN KEY(user_token) REFERENCES users(token) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_radio_chat_live ON radio_chat(expires,created DESC);
INSERT OR IGNORE INTO social_schema_migrations(version,applied,note)
VALUES('social-m1-v1',unixepoch()*1000,'Profile, Bảng Nhân Duyên, replies, reactions, Chuông Duyên, follows, reports, merit actions');
INSERT OR IGNORE INTO social_schema_migrations(version,applied,note) VALUES('social-m9-v1',unixepoch()*1000,'Opaque single-use Chứng Duyên invites');
`);

// Existing pre-M9 databases need the additive receipt column before its index.
add('invite_requests', 'receipt_hash', 'TEXT');
db.exec('CREATE UNIQUE INDEX IF NOT EXISTS idx_invite_receipt ON invite_requests(receipt_hash) WHERE receipt_hash IS NOT NULL');

const integrity = db.prepare('PRAGMA integrity_check').get();
const fk = db.prepare('PRAGMA foreign_key_check').all();
try { const c=db.prepare("PRAGMA table_info(merit_actions)").all().map(x=>x.name); if(!c.includes('proof_key')) db.exec("ALTER TABLE merit_actions ADD COLUMN proof_key TEXT"); db.exec("CREATE UNIQUE INDEX IF NOT EXISTS uniq_merit_proof_key ON merit_actions(proof_key) WHERE proof_key IS NOT NULL AND proof_key <> ''"); } catch(e) { console.error(e); process.exitCode=1; }

const tables = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE 'social_%' OR name='merit_actions') ORDER BY name").all().map(x=>x.name);
const indexes = db.prepare("SELECT count(*) n FROM sqlite_master WHERE type='index' AND (name LIKE 'idx_%')").get().n;
console.log(JSON.stringify({ok:integrity.integrity_check==='ok'&&fk.length===0,dbPath,users:db.prepare('SELECT count(*) n FROM users').get().n,publicIds:db.prepare("SELECT count(*) n FROM users WHERE public_id IS NOT NULL AND public_id<>''").get().n,tables,indexes,integrity:integrity.integrity_check,foreignKeyErrors:fk},null,2));
db.close();
