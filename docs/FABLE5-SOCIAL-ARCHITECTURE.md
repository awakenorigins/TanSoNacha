# FABLE 5 — KIẾN TRÚC TRIỂN KHAI XÃ HỘI TẦN SỐ NACHA

> Vai trò: Fable 5 — kiến trúc sư sản phẩm chủ lực  
> Phạm vi đọc: `HANDOFF-TANSONACHA.md`, `TanSoNacha-SOL-SuperAudit.html`, `backend/phuocphieu.mjs`, `backend/server.mjs`, `website/src/layouts/BaseLayout.astro`, các trang `vao-coi`, `coi/[pham]`, `coi/[pham]/event`, `inbox`, `radio`, `coi-admin`.  
> Quyết định mới của anh Nấng đã tích hợp: tập trung Pháp/tu tập/kiến thức; profile sinh động avatar/tag; Chuông Duyên OK; feed đổi tên **BẢNG NHÂN DUYÊN**; **Âm Kinh + Phước Phiếu phải hiện rõ mobile nav/thanh dưới**; radio có avatar người cùng nghe + Pháp Danh fallback + chat ngắn cạnh avatar; **cho farm công đức** nhưng hướng thiện/bền vững; auth giữ nguyên; được dùng Three/Galaxy/Hyperspeed với adaptive thiết bị.

---

## 0. Executive architecture

Tần Số Nacha nên tiến hóa thành **mạng xã hội hành trì** chứ không phải clone Facebook. Trục sản phẩm mới:

1. **BẢNG NHÂN DUYÊN** = feed trung tâm sau login, trộn bài đăng, hoạt động tu tập, Âm Kinh, Phước Phiếu, radio, mảnh kinh, lời mời hành thiện.
2. **Bảng Công Đức / Cõi Của Ta** = profile/wall có avatar, tag, nguyện, bài, sổ duyên, phản hồi, lịch sử công đức.
3. **Chuông Duyên** = notification hub, gom tương tác feed/wall/reply/radio/invite/inbox.
4. **Radio Tần Số** = pseudo-live hiện tại + presence/chat ngắn TTL để có “nghe chung”.
5. **Farm công đức có đạo đức** = không cấm farm, nhưng chuyển farm thành vòng lặp hướng thiện: đọc/nghe/ghi/chia sẻ/khích lệ/giúp người mới; reward theo chất lượng, cooldown mềm, diminishing returns, audit được.
6. **Art adaptive** = Sacred Social base CSS luôn chạy; Three/Galaxy/Hyperspeed chỉ ở layer progressive enhancement theo năng lực thiết bị.

Stack hiện tại Astro static + Node SQLite đủ làm MVP nếu giữ nguyên tắc:

- Mọi social state đi qua `backend/phuocphieu.mjs` DB `phuocphieu.db`.
- `backend/server.mjs` `amkinh.db` giữ Âm Kinh counters/comments hiện hữu, không trộn vội; chỉ mirror events quan trọng sang feed bằng job/API sau.
- Frontend Astro static render shell + JS client fetch `/pp-api/*`.
- SQLite WAL + indexes + cursor pagination + rate limit in-memory là đủ giai đoạn đầu; sau 5k–20k MAU mới tách service.

---

## 1. Hiện trạng kỹ thuật & xung đột cần nhận diện

### 1.1 Backend hiện tại

`phuocphieu.mjs` đang có:

- `users(token, phapdanh, phapdanh_key, matma_hash, email, pham, rank, phuoc, duyen, created, last_seen, role)`.
- `vouchers(code, pham, prefix, seq, status, owner, created, activated)`.
- `ledger(token, kind, text, phuoc, duyen, ts)`.
- `contributions(...)` cho nhạc/bài/podcast/video pending/approved/rejected.
- `im_threads`, `im_messages` cho inbox.
- `radio/now`, `tich-phuoc`, `contribute`, admin review.

`server.mjs` đang có Âm Kinh:

- `counters(track, metric, count)`.
- `comments(track, parent, name, body, ts)`.
- reaction/play/comment public by IP.

### 1.2 Frontend hiện tại

- `BaseLayout.astro` desktop nav quá nhiều mục; mobile bottom nav 4 mục: Sảnh, Kinh Tạng, Âm Kinh, Phước Phiếu.
- `vao-coi` auth bằng Pháp Danh + Mật Mã hoặc QR; token lưu localStorage.
- `coi/[pham]` là Cõi/Sổ Duyên nhưng chưa là social profile thật; có nút farm `tich-phuoc` trực tiếp.
- `inbox` đọc thread, chưa có compose/search/auto refresh đầy đủ.
- `radio` pseudo-live tự phát, chưa có presence/avatar/chat.

### 1.3 Xung đột với quyết định mới

1. Audit cũ đề xuất feed tên **Dòng Duyên**, quyết định mới đổi thành **BẢNG NHÂN DUYÊN**. Từ giờ dùng BẢNG NHÂN DUYÊN trong IA/UI/API naming có thể vẫn dùng `feed` nội bộ.
2. Audit cũ muốn mobile nav 5 mục và đưa Âm Kinh/Phước Phiếu vào Khám Phá; quyết định mới bắt buộc **Âm Kinh + Phước Phiếu hiện rõ trên mobile nav/thanh dưới**. Vì vậy bottom nav phải ưu tiên 5 mục: **Bảng Nhân Duyên, Âm Kinh, Gieo, Phước Phiếu, Cõi Ta** hoặc 6 mục nếu màn đủ rộng nhưng khuyến nghị 5.
3. Auth audit cảnh báo cần session token riêng, nhưng quyết định mới “auth giữ nguyên, bàn sau”. Do đó không đổi mô hình credential ở P0; chỉ bọc thêm endpoint auth guard và không làm vỡ localStorage token.
4. “Cho farm công đức” xung đột với tinh thần không leaderboard. Giải pháp: cho farm hành động lành, không công khai bảng đua Phước tổng; reward minh bạch, cap mềm, nhiệm vụ có chất lượng.
5. “Cho dùng Three/Galaxy/Hyperspeed” xung đột audit cũ cảnh báo WebGL nặng. Giải pháp: progressive enhancement, adaptive by device, off by default on low-end/reduced-motion/data-saver.

---

## 2. Data model: migrations SQLite

Tạo migration idempotent trong `phuocphieu.mjs` hoặc file migration runner riêng `backend/migrate-social.mjs` chạy một lần trước deploy. Với stack hiện tại, ưu tiên idempotent `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE` try/catch giống code hiện có.

### 2.1 Users profile extension

```sql
ALTER TABLE users ADD COLUMN avatar_url TEXT;
ALTER TABLE users ADD COLUMN avatar_seed TEXT;
ALTER TABLE users ADD COLUMN cover_url TEXT;
ALTER TABLE users ADD COLUMN bio TEXT;
ALTER TABLE users ADD COLUMN vow TEXT;
ALTER TABLE users ADD COLUMN location_text TEXT;
ALTER TABLE users ADD COLUMN profile_tags TEXT; -- JSON array short tags
ALTER TABLE users ADD COLUMN profile_visibility TEXT NOT NULL DEFAULT 'public'; -- public|members|private
ALTER TABLE users ADD COLUMN muted_until INTEGER NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN trust_score INTEGER NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN social_flags INTEGER NOT NULL DEFAULT 0;
```

Fallback avatar: if `avatar_url` empty, derive from `avatar_seed || token` to local `/media/avatar/tieutam-XX.jpg` or CSS mandala initials.

Indexes:

```sql
CREATE INDEX IF NOT EXISTS idx_users_last_seen ON users(last_seen);
CREATE INDEX IF NOT EXISTS idx_users_pham_rank ON users(pham, rank);
CREATE INDEX IF NOT EXISTS idx_users_trust ON users(trust_score, social_flags);
```

### 2.2 Posts / wall / Bảng Nhân Duyên

```sql
CREATE TABLE IF NOT EXISTS social_posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  token TEXT NOT NULL,
  phapdanh TEXT NOT NULL,
  type TEXT NOT NULL DEFAULT 'post', -- post|kinh-note|practice|question|share|system-duyen|radio-note
  title TEXT,
  body TEXT NOT NULL,
  media_json TEXT, -- JSON array: {kind,url,thumb,alt,width,height,dur}
  tags_json TEXT, -- JSON short tags
  visibility TEXT NOT NULL DEFAULT 'public', -- public|members|followers|private
  status TEXT NOT NULL DEFAULT 'published', -- draft|published|hidden|deleted|flagged|pending
  source_kind TEXT, -- ledger|contribution|amkinh|radio|manual
  source_id TEXT,
  reply_count INTEGER NOT NULL DEFAULT 0,
  reaction_count INTEGER NOT NULL DEFAULT 0,
  score_cache REAL NOT NULL DEFAULT 0,
  created INTEGER NOT NULL,
  updated INTEGER NOT NULL,
  edited INTEGER,
  deleted INTEGER
);

CREATE INDEX IF NOT EXISTS idx_posts_feed ON social_posts(status, visibility, created DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_posts_token ON social_posts(token, status, created DESC);
CREATE INDEX IF NOT EXISTS idx_posts_type_created ON social_posts(type, created DESC);
CREATE INDEX IF NOT EXISTS idx_posts_score ON social_posts(status, score_cache DESC, created DESC);
CREATE UNIQUE INDEX IF NOT EXISTS uniq_posts_source ON social_posts(source_kind, source_id) WHERE source_kind IS NOT NULL AND source_id IS NOT NULL;
```

Notes:

- Do not write every ledger entry to post. Only socially meaningful entries: approved contribution, first radio presence of day, vow/reflection shared, referral accepted, public milestone.
- `system-duyen` cards are auto-generated feed entries but owned by user token.

### 2.3 Replies: two-level only

```sql
CREATE TABLE IF NOT EXISTS social_replies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id INTEGER NOT NULL,
  parent_id INTEGER NOT NULL DEFAULT 0,
  token TEXT NOT NULL,
  phapdanh TEXT NOT NULL,
  body TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'published', -- published|hidden|deleted|flagged
  reaction_count INTEGER NOT NULL DEFAULT 0,
  created INTEGER NOT NULL,
  updated INTEGER NOT NULL,
  deleted INTEGER
);

CREATE INDEX IF NOT EXISTS idx_replies_post ON social_replies(post_id, status, id ASC);
CREATE INDEX IF NOT EXISTS idx_replies_parent ON social_replies(parent_id, status, id ASC);
CREATE INDEX IF NOT EXISTS idx_replies_token ON social_replies(token, created DESC);
```

Rule: `parent_id` can point only to top-level reply; if parent itself has parent, normalize to its parent to prevent infinite nesting.

### 2.4 Reactions

```sql
CREATE TABLE IF NOT EXISTS social_reactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  target_type TEXT NOT NULL, -- post|reply|radio-chat|amkinh-comment
  target_id INTEGER NOT NULL,
  token TEXT NOT NULL,
  kind TEXT NOT NULL, -- ket-duyen|sen|tri-an|lang-nghe|sang
  created INTEGER NOT NULL,
  UNIQUE(target_type, target_id, token, kind)
);

CREATE INDEX IF NOT EXISTS idx_react_target ON social_reactions(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_react_token ON social_reactions(token, created DESC);
```

Allow multiple reaction kinds? Product should allow one primary reaction per target for clarity. If one only: unique `(target_type,target_id,token)` instead. Recommendation P0: one reaction per target; UI label **Kết Duyên 🪷**.

### 2.5 Relations: Đồng Hành / mute / block

```sql
CREATE TABLE IF NOT EXISTS social_relations (
  from_token TEXT NOT NULL,
  to_token TEXT NOT NULL,
  kind TEXT NOT NULL, -- follow|mute|block
  created INTEGER NOT NULL,
  PRIMARY KEY(from_token, to_token, kind)
);

CREATE INDEX IF NOT EXISTS idx_rel_to ON social_relations(to_token, kind);
CREATE INDEX IF NOT EXISTS idx_rel_from ON social_relations(from_token, kind);
```

Block rules:

- If A blocks B: B cannot reply to A posts, DM A, mention A, appear in A feed except admin/moderation views.
- Mute: A stops seeing B in feed; B not notified.

### 2.6 Notifications: Chuông Duyên

```sql
CREATE TABLE IF NOT EXISTS notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  token TEXT NOT NULL, -- receiver
  actor_token TEXT,
  actor_name TEXT,
  kind TEXT NOT NULL, -- post_react|reply|reply_react|follow|mention|radio_chat|invite_pending|invite_accepted|contrib_review|system
  target_type TEXT,
  target_id TEXT,
  title TEXT NOT NULL,
  body TEXT,
  meta TEXT,
  seen INTEGER NOT NULL DEFAULT 0,
  read INTEGER NOT NULL DEFAULT 0,
  created INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_notif_token ON notifications(token, read, created DESC);
CREATE INDEX IF NOT EXISTS idx_notif_kind ON notifications(kind, created DESC);
CREATE INDEX IF NOT EXISTS idx_notif_target ON notifications(target_type, target_id);
```

Notification grouping at API level: same actor/kind/target in 10 minutes update/replace rather than spam.

### 2.7 Reports / moderation / audit log

```sql
CREATE TABLE IF NOT EXISTS moderation_reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  reporter_token TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  reason TEXT NOT NULL,
  note TEXT,
  status TEXT NOT NULL DEFAULT 'open', -- open|reviewing|resolved|rejected
  created INTEGER NOT NULL,
  resolved INTEGER,
  resolver_token TEXT,
  action TEXT
);

CREATE INDEX IF NOT EXISTS idx_reports_status ON moderation_reports(status, created ASC);
CREATE INDEX IF NOT EXISTS idx_reports_target ON moderation_reports(target_type, target_id);

CREATE TABLE IF NOT EXISTS admin_audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  admin_token TEXT,
  admin_name TEXT,
  action TEXT NOT NULL,
  target_type TEXT,
  target_id TEXT,
  before_json TEXT,
  after_json TEXT,
  ip TEXT,
  created INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_admin_audit_created ON admin_audit_log(created DESC);
```

### 2.8 Radio presence/chat TTL

SQLite can store TTL rows and delete expired opportunistically.

```sql
CREATE TABLE IF NOT EXISTS radio_presence (
  token TEXT PRIMARY KEY,
  phapdanh TEXT NOT NULL,
  avatar_url TEXT,
  avatar_seed TEXT,
  item_file TEXT,
  item_title TEXT,
  joined INTEGER NOT NULL,
  last_seen INTEGER NOT NULL,
  client_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_radio_presence_seen ON radio_presence(last_seen DESC);
CREATE INDEX IF NOT EXISTS idx_radio_presence_item ON radio_presence(item_file, last_seen DESC);

CREATE TABLE IF NOT EXISTS radio_chat (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  token TEXT NOT NULL,
  phapdanh TEXT NOT NULL,
  avatar_url TEXT,
  body TEXT NOT NULL,
  item_file TEXT,
  status TEXT NOT NULL DEFAULT 'live', -- live|hidden|deleted
  created INTEGER NOT NULL,
  expires INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_radio_chat_live ON radio_chat(status, expires, created DESC);
CREATE INDEX IF NOT EXISTS idx_radio_chat_item ON radio_chat(item_file, created DESC);
```

TTL policy:

- presence live if `Date.now() - last_seen <= 45s`.
- chat visible for 10 minutes or current item duration, whichever shorter? Recommendation: 12 minutes max, also keep last 50 per item.
- Delete expired rows during `/radio/ping` or `/radio/presence` if now > expires, bounded `DELETE LIMIT` not directly in SQLite; use `DELETE FROM radio_chat WHERE expires < ? AND id IN (SELECT id ... LIMIT 200)`.

### 2.9 Gamification / farm công đức ledger v2

Current `ledger` is sufficient as source of truth, but `tich-phuoc` needs anti-bot semantics and action proofs. Add:

```sql
CREATE TABLE IF NOT EXISTS merit_actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  token TEXT NOT NULL,
  kind TEXT NOT NULL,
  proof_type TEXT, -- radio_seconds|post_created|reply_quality|daily_reflection|amkinh_listen|manual
  proof_id TEXT,
  phuoc INTEGER NOT NULL DEFAULT 0,
  duyen INTEGER NOT NULL DEFAULT 0,
  quality_score INTEGER NOT NULL DEFAULT 0,
  farm_tier INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'counted', -- counted|capped|pending|rejected|reversed
  ip_hash TEXT,
  user_agent_hash TEXT,
  created INTEGER NOT NULL,
  UNIQUE(token, kind, proof_id)
);

CREATE INDEX IF NOT EXISTS idx_merit_token_kind_day ON merit_actions(token, kind, created DESC);
CREATE INDEX IF NOT EXISTS idx_merit_proof ON merit_actions(kind, proof_id);
```

Farm accepted model:

- Allow repeated good actions.
- Reward curve: full reward first N/day; 40% reward next M/day; 10% symbolic after; no public shame.
- Quality multipliers: approved content, replies with length/variety/no blocklist, radio listening duration, reactions from others.
- No rank-up solely from spammy low-quality farm: high ranks require `trust_score`, age, admin recognition.

### 2.10 Invite / referral approval

Existing `activate` auto rewards `ref`, but original handoff says via invite should require inviter approval. Add dedicated table; keep old `ref` behavior temporarily but migrate UI.

```sql
CREATE TABLE IF NOT EXISTS invite_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  inviter_token TEXT NOT NULL,
  invite_code TEXT NOT NULL,
  requested_phapdanh TEXT NOT NULL,
  requested_key TEXT NOT NULL,
  matma_hash TEXT NOT NULL,
  email TEXT,
  status TEXT NOT NULL DEFAULT 'pending', -- pending|approved|rejected|expired
  new_token TEXT,
  created INTEGER NOT NULL,
  reviewed INTEGER,
  UNIQUE(invite_code, requested_key)
);

CREATE INDEX IF NOT EXISTS idx_invite_inviter ON invite_requests(inviter_token, status, created DESC);
CREATE INDEX IF NOT EXISTS idx_invite_status ON invite_requests(status, created ASC);
```

For P0 social, this can be P1 because decision says auth bàn sau, but architecture must reserve it.

---

## 3. API endpoints

All endpoints under `/pp-api`. Auth rule for now: token in body/query/header `X-PP-Token`; do not break localStorage token. Admin: existing `adminFrom` with `X-Admin-Token` or user token role admin.

### 3.1 Shared helpers

- `requireUser(req,url,b)` returns user or 401.
- `requireAdmin(req,url)` returns admin or 403.
- `cleanText(s,max)` remove controls, trim, cap.
- `sanitizeHtml` not needed if API stores text and frontend escapes; if allow rich text later, whitelist.
- `isBlockedBy(from,to)` relation check.
- `notify(token, actor, kind, target, title, body, meta)` inserts notifications and maybe inbox system for legacy.
- `rateOkUser(token||ip,bucket,max,win)` combine IP + user.

### 3.2 Profile endpoints

#### GET `/profile?token=` or `/profile?phapdanh=`

Returns public profile:

```json
{ "ok": true, "profile": { "tokenPublic":"...", "phapdanh":"...", "avatarUrl":"...", "pham":"truc-duyen", "rank":1, "bio":"...", "vow":"...", "tags":["Nghe Kinh","Tập thở"], "stats":{"posts":12,"followers":5,"phuocPublic":"ẩn/summary"}, "isSelf": false, "relation":{"following":false,"muted":false,"blocked":false} } }
```

Security: expose `token`? Current system uses token as credential. Do **not** expose raw token publicly in profile/search. Add `public_id` would be better:

```sql
ALTER TABLE users ADD COLUMN public_id TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS uniq_users_public_id ON users(public_id) WHERE public_id IS NOT NULL;
```

Backfill `public_id = random 10 chars`. Until then, profile by `phapdanh_key` internally, but API must not return token unless `isSelf` or admin.

#### POST `/profile/update`

Body: `{ token, avatarUrl?, bio?, vow?, tags?, visibility? }`

Rules:

- bio max 300, vow max 120, tags max 8 tags x 18 chars.
- avatarUrl must be local allowed path or generated seed; no arbitrary remote image in P0 to prevent tracking/malware.
- rate: 20/hour.

#### GET `/profiles/search?q=`

For inbox compose/mentions. Return top 20 by `phapdanh LIKE`, rank/trust, no raw token; include `public_id`.

### 3.3 Posts / Bảng Nhân Duyên

#### GET `/feed?token=&cursor=&limit=&scope=`

UI name **BẢNG NHÂN DUYÊN**. Returns mixed cards.

Cursor format simple: base64 JSON `{score,created,id}` or `created:id`. For SQLite simplicity P0 can use `before=<created>` and ranking window.

Recommended implementation:

- For first page, select candidate posts from last 14 days + evergreen approved posts, limit 200, rank in JS.
- For older pages, chronological cursor.

Response:

```json
{ "ok": true, "items": [ { "id":1, "type":"post", "author":{...}, "body":"...", "tags":[], "created":..., "reactions":{"ket-duyen":3,"mine":false}, "replyCount":2, "source":null } ], "nextCursor":"..." }
```

#### GET `/posts/user?phapdanh=&cursor=&limit=`

For Bảng Công Đức wall.

#### GET `/post?id=`

Single post + replies preview.

#### POST `/post/create`

Body `{token,type,title,body,tags,visibility,media}`.

Rules:

- Body max 4000, title max 120.
- P0 text only + optional one image path from future upload; no arbitrary HTML.
- Blocklist immediate; suspicious links -> `pending` or `flagged`.
- Rate: normal user 8 posts/hour, 30/day; new user 3/day first 24h.
- Creates merit action `post_created`, maybe +Phước pending or small immediate.
- Creates feed card.

#### POST `/post/edit`

Only owner within 24h or admin; after 24h append edited timestamp. If post has reports, edit creates audit record.

#### POST `/post/delete`

Soft delete owner/admin. Do not hard delete for moderation; status `deleted`, body tombstone.

### 3.4 Replies

#### GET `/replies?postId=&cursor=&limit=`

Return top-level replies and one-level children.

#### POST `/reply/create`

Body `{token,postId,parentId?,body}`.

Rules:

- Body max 1000.
- Two-level only.
- Owner of post receives Chuông Duyên unless self.
- Parent author receives notification for direct reply unless same as post owner already notified.
- Merit action: reply quality. Full reward only if length > 12 chars, not duplicate, no repeated same target spam.

#### POST `/reply/delete`

Owner/admin soft delete.

### 3.5 Reactions

#### POST `/reaction/toggle`

Body `{token,targetType,targetId,kind}`.

Rules:

- kind P0: `ket-duyen` only; P1 add `tri-an`, `lang-nghe`, `sang`.
- Toggle inserts/deletes.
- One per target per user recommended.
- Notification to target owner, grouped per target.
- Merit: tiny or zero direct Phước to avoid reaction farming; value should go to receiver as social signal, not raw farm.

### 3.6 Notifications / Chuông Duyên

#### GET `/notifications?token=&cursor=&limit=&unreadOnly=`

#### GET `/notifications/unread?token=`

Should replace/augment inbox badge. Bottom nav Chuông Duyên can show combined unread = notifications unread + inbox unread.

#### POST `/notifications/mark-read`

Body `{token, ids? , all?}`.

### 3.7 Relations

#### POST `/relation/set`

Body `{token,toPublicId,kind,enabled}`.

Rules: cannot block admin/system? User can mute system categories but not critical account notices.

### 3.8 Reports / moderation

#### POST `/report`

Body `{token,targetType,targetId,reason,note}`.

Rate 10/day. Duplicate same reporter/target within 24h returns ok already.

#### GET `/admin/reports?status=open`

#### POST `/admin/moderate`

Body `{targetType,targetId,action,reason}` actions: hide, unhide, delete, restore, warn, mute_user, unmute, reject_report.

All admin actions write `admin_audit_log`.

### 3.9 Radio presence/chat

#### POST `/radio/ping`

Body `{token, clientId, itemFile?}`. Server should call `radioNow()` itself to avoid client lying; itemFile can be diagnostic only.

Behavior:

- Upsert `radio_presence` with current radio item, last_seen now.
- Clean expired presence older than 90s, expired chat.
- Return compact presence + recent chat.

Response:

```json
{ "ok":true, "listeners":[{"phapdanh":"An Tâm","avatarUrl":"...","initial":"A","lastSeen":...}], "count":12, "chat":[{"id":9,"phapdanh":"...","avatarUrl":"...","body":"Nam mô 🙏","created":...}] }
```

Privacy: only logged-in users show; guests count as anonymous number? P0 can not count guests. If token absent, allow read presence but not write.

#### GET `/radio/presence`

Read-only for guests. Limit avatar list 24, count total.

#### POST `/radio/chat`

Body `{token, body}`.

Rules:

- Max 80 chars, no links P0, no mentions P0.
- Rate 6/min, 30/hour; duplicate body cooldown 5 min.
- TTL 12 min, max last 50 live.
- Shows chat bubble next to avatar in UI for recent 20s.
- Blocklist -> hidden/blocked.
- Merit: can count `radio_chat` tiny reward with cap, but better not raw reward to avoid noisy chat; reward “lắng nghe 10 min” instead.

### 3.10 Merit/farm endpoints

Keep current `/tich-phuoc` but change semantics.

#### POST `/tich-phuoc`

Body `{token, kind, proofId?, durationSec?}`.

Kinds:

- `diem-danh`: once/day, +10.
- `radio`: require presence duration >= 180 seconds; full max 2/day, then symbolic.
- `amkinh-listen`: require track + listened seconds, cap 5/day.
- `reply`: called internally after reply create, not directly from UI.
- `post`: called internally after post create/approve, not direct farm button.
- `hoi-quang`: daily reflection private/public, +15.
- `gieo-duyen`: monetary/voucher path existing.

Current Cõi page has direct farm buttons for `comment`, `share-story`, `dang-bai`, `tao-nhac`, `stream`; these are abusable because no proof. In new architecture:

- Keep visible as “Gợi ý gieo duyên”, but buttons lead to actual action/composer, not direct reward.
- `/tich-phuoc` direct accepts only low-risk proofless actions: `diem-danh` and maybe `hoi-quang` with body.
- For compatibility, if old UI calls old kinds, return friendly “Hãy đăng bài/nghe/ghé lời thật để Phước tự kết lại” rather than giving points.

Farm model is allowed, but proof-bound.

---

## 4. Auth rules without changing auth

Decision: auth giữ nguyên.

### 4.1 Current risk

Current token equals voucher code and is stored in localStorage. It is also currently returned by APIs (`userPublic` includes token) and used in referral URLs. This is credential leakage risk.

### 4.2 P0-compatible rule

Do not replace auth, but reduce exposure:

1. For endpoints requiring auth: accept `token` exactly as now.
2. For public profile/search/feed author object: never return raw `token`; return `publicId` or `phapdanh`.
3. Add `public_id` to users and backfill.
4. Existing old frontend may still need token for self; `/account` returns token only because caller already has token.
5. Referral link still uses token for now if not touching auth; but new invite should use `invite_code` P1.
6. Admin endpoints must never rely on client-side gate only; use existing server-side `adminFrom`.

### 4.3 CSRF/CORS

Existing CORS `*` with token in body is acceptable for early static site but means any site can call API if it knows token. P1: restrict `Access-Control-Allow-Origin` to production host(s), still allow local during dev.

---

## 5. Feed ranking: BẢNG NHÂN DUYÊN

Goal: cuốn hút người dùng tập trung Pháp/tu tập/kiến thức, not outrage.

### 5.1 Candidate sources

- `social_posts` published public/members.
- Auto cards from approved `contributions`.
- Auto cards from meaningful `ledger` kinds: `khai-duyen`, `thang-cap`, approved `gop-duyen`, `hoi-quang` if shared.
- Âm Kinh cards from `amkinh.db` top listened/recent comments (P1 bridge).
- Radio now card pinned near top when active.
- Daily mảnh kinh static card generated server-side by day.

### 5.2 Ranking formula

For each candidate:

```
score = base_type
      + recency_score
      + relation_score
      + quality_score
      + interaction_score
      + practice_score
      + diversity_bonus
      + random_jitter
      - seen_penalty
      - spam_penalty
```

Suggested weights:

- `base_type`: mảnh kinh +8, radio live +7, practice/reflection +6, post +5, approved contribution +5, raw ledger +2.
- `recency_score`: `12 * exp(-age_hours / 36)`.
- `relation_score`: +8 following/Đồng Hành, +4 same Phẩm, +3 replied before, -999 block/mute.
- `quality_score`: +0..10 from length, tags, approved status, no reports, trust.
- `interaction_score`: `log(1 + reactions*2 + replies*3)` capped 10.
- `practice_score`: +5 for Pháp/tu tập/kiến thức tags; +3 for content with source quote.
- `diversity_bonus`: +4 if author not already in page, +3 if type underrepresented.
- `random_jitter`: deterministic seeded by `(userToken,date,postId)` range 0..3 to keep “duyên”.
- `seen_penalty`: later P1 with `feed_seen` table; P0 use localStorage seen ids.

### 5.3 Diversity hard rules

- Max 2 posts per author per page.
- Max 2 raw farm/ledger cards per page.
- Always include one Pháp/knowledge card in first 5 if available.
- Do not rank by Phước total.
- Do not show hidden/private/muted/blocked.

### 5.4 Cursor strategy

P0 simple:

- `/feed` first page: query last 14 days 200 rows, rank JS, return top 20 with cursor `{offsetIds}` not ideal.
- Better: compute `score_cache` periodically/on write and query `ORDER BY score_cache DESC, created DESC LIMIT`. But personalized relation needs JS.

Recommendation P0: rank per request from bounded candidate set; SQLite size early is fine.

P1 add `feed_seen(token, post_id, seen_ts)`.

---

## 6. Profile/avatar/tag architecture

### 6.1 Profile UI components

Bảng Công Đức should include:

- Avatar circle with sacred frequency ring.
- Pháp Danh + Phẩm badge + role/admin seal if applicable.
- Tags: max 8: “Nghe Kinh”, “Hồi Quang”, “Từ Bi”, “Ấn Tống”, “Sơ Tâm”, etc.
- One-line nguyện (`vow`) as emotional anchor.
- Stats: posts/replies/kết duyên, not public Phước leaderboard. Phước can show as personal on self; public show “Dấu duyên: Đang nở” tier, unless user opts in.
- Tabs: Bài Gieo, Sổ Duyên, Ghé Lời, Mảnh Cất Tâm.

### 6.2 Avatar sources

P0:

- Generated local avatar: `/media/avatar/tieutam-XX.jpg` or mandala initials with seed.
- User can choose from built-in avatar gallery.
- No upload yet to avoid media pipeline.

P1:

- Upload to local `website/public/uploads/avatar/` needs backend multipart or base64; not ideal in zero-dep. Prefer curated gallery until upload infra exists.

### 6.3 Tags

Store as JSON text. Validate against allowed list plus user custom? P0 allowed list only to keep tinh tế.

Allowed tag examples:

- Tu tập: `Niệm Phật`, `Nghe Kinh`, `Hồi Quang`, `Thiền thở`, `Chánh ngữ`.
- Pháp học: `Kinh Tạng`, `A-tỳ-đàm`, `Lịch sử Phật giáo`, `Pháp âm`.
- Duyên lành: `Ấn Tống`, `Góp Duyên`, `Dẫn Duyên`, `Chép Kinh`.

---

## 7. Post/reply/reaction product rules

### 7.1 Composer

“Gieo một duyên lành…” composer modes:

- Chia sẻ tâm niệm.
- Ghi chú Pháp học.
- Hỏi đạo hữu.
- Chia sẻ Âm Kinh/Radio/Mảnh Kinh.
- Hồi Quang hôm nay.

Default placeholder should guide quality:

> “Hôm nay bạn nghe/đọc/chiêm nghiệm điều gì muốn gieo lại cho người sau?”

### 7.2 Visibility

P0:

- `public`: everyone.
- `members`: logged-in users.
- `private`: only self (for Hồi Quang if saved, not feed).

P1:

- `followers` / Đồng Hành.

### 7.3 Replies

- Reply label: **Ghé Lời** for top-level, **Đáp Lời** for child.
- Two-level max, avoids debate spirals.
- OP can hide replies on own post? P1; admin always can.

### 7.4 Reactions

- P0 one: **Kết Duyên 🪷**.
- Reaction should not directly farm Phước for sender. It can contribute to receiver quality score once per unique user.
- Prevent self-reaction.

---

## 8. Notifications: Chuông Duyên

Chuông Duyên should unify:

- Ai Kết Duyên bài mình.
- Ai Ghé Lời/Đáp Lời.
- Ai Đồng Hành.
- Bài đóng góp được duyệt/từ chối.
- Người mới xin Chứng Duyên.
- Radio chat mentions/reactions later.
- System/admin notices.

### 8.1 IA

Mobile nav item **Chuông** can be absent if 5 slots must preserve Âm Kinh/Phước Phiếu; but user decision says Chuông Duyên OK, not necessarily bottom persistent. Best IA:

Bottom nav 5:

1. **Nhân Duyên** `/bang-nhan-duyen`
2. **Âm Kinh** `/nacha`
3. **Gieo** central compose button
4. **Phước Phiếu** `/phuoc-phieu`
5. **Cõi Ta** `/vao-coi` or profile

Chuông Duyên appears:

- Top-right bell floating/header on social pages.
- Inside Cõi Ta dashboard.
- Badge aggregated with Inbox.

If insist on bottom Chuông, use 6-item scrollable/dock on wide mobile, but usability worse. Recommendation: keep Âm Kinh + Phước Phiếu explicit; Chuông as floating bell.

### 8.2 Badge

`GET /notifications/unread` + `/inbox/unread` combine client-side.

---

## 9. Radio presence/chat UI

### 9.1 Visual design

Around current spinning disc:

- Avatar ring orbit: max 12 visible avatars; if more show `+N` bead.
- Each avatar: image if `avatar_url`; else initials/Pháp Danh fallback with generated background.
- Recent chat: small bubble adjacent to avatar for 5–8 seconds; text max 36 chars in bubble, full max 80 in side list.
- No large chat room feel; keep “thiền vị”.

### 9.2 Presence behavior

Client on `radio.astro`:

- When joined/on audio, every 20s POST `/radio/ping`.
- On page visibility hidden: ping every 45–60s if audio still playing; else stop.
- On unload optional `sendBeacon` `/radio/leave` P1; TTL enough P0.
- GET presence every 10s for guests or if ping response failed.

### 9.3 Chat short

- Input placeholder: “Gửi một niệm ngắn…”
- Suggested chips: `🙏`, `🪷`, `Nam mô`, `Đang nghe cùng bạn` to reduce noisy typing.
- Rate limit and no links.
- Chat TTL means it is not permanent feed unless user chooses “Cất vào Bảng”.

### 9.4 Edge cases

- Token exists but user deleted: ping returns 401; UI stays listener guest.
- Same user multiple tabs: `client_id`; store one row per token, update latest. Count user once.
- Radio item changes: presence updates item_file; old chat remains TTL but UI can group “vừa qua”.
- Autoplay blocked: no presence until user joins/audio plays, or show as “đang ở phòng” only after button? Recommendation only after actual play to avoid fake listeners.

---

## 10. Farm công đức: allowed but hướng thiện

### 10.1 Philosophy

Do not shame “farm”. Convert it into “lặp việc lành”. The system should say:

> “Muốn tích nhiều Phước? Rất tốt. Hãy tích bằng việc thật: nghe sâu, đọc kỹ, ghé lời tử tế, giúp người mới, cất một điều lành vào ngày.”

### 10.2 Reward tiers

For each kind per day:

- Tier A: full reward first N.
- Tier B: 40% reward next M.
- Tier C: symbolic +1 or +0 with kind message.
- Quality bonus from others/admin can exceed cap.

Example:

| Action | Proof | Full | Reduced | Symbolic | Notes |
|---|---|---:|---:|---:|---|
| Điểm danh | click once/day | 1 | 0 | 0 | low value |
| Radio listen | >=3 min presence | 2 | 3 | yes | no reward for chat spam |
| Âm Kinh listen | >=60s/track | 5 | 5 | yes | unique tracks |
| Ghé Lời | real reply | 10 | 10 | yes | duplicate/short no reward |
| Bài Pháp/tâm niệm | post | 3 | pending | yes | extra if reactions/replies |
| Hồi Quang | private/public reflection | 1 | 0 | 0 | encourages daily practice |
| Dẫn Duyên | approved invite | 5/day | pending | no | must be accepted/chứng duyên |

### 10.3 Anti-bot without banning farm

- Require proof id uniqueness.
- Diminishing returns.
- Duplicate text detection: same normalized reply/post within 24h gives no Phước.
- Minimum dwell time for audio/radio.
- IP/user-agent hash anomaly flag, not hard block: many accounts same IP farming -> put rewards `pending` after threshold.
- New account probation: first 24h lower caps.
- Trust score increases with age, approved contributions, low reports.
- Admin can reverse/reject merit with audit.

### 10.4 Rank-up guard

- Phước can raise rank 1–10 as current; but add `trust_score` gates for higher social privileges.
- Rank 11–15 admin recognition only (already current philosophy).
- Do not public leaderboard by Phước.

---

## 11. Moderation & rate-limit

### 11.1 Blocklist now, moderation queue later

Current `BLOCKLIST` exists. Expand to:

- profanity/scam/gambling/porn/drug/hate.
- suspicious finance links.
- repeated external links.

P0 actions:

- Block hard for obvious.
- Flag for review if link + new user + low trust.
- Hide after 3 unique reports until admin reviews? Use carefully: brigading risk. Recommendation: after 3 reports from trusted distinct users -> `flagged` not deleted, reduce feed visibility.

### 11.2 Rate limits

Current in-memory `hits` works but resets on restart. Good enough P0.

Suggested buckets:

- login: existing.
- post-create: 8/hour, 30/day per token; 20/hour per IP.
- reply-create: 20/hour, 80/day per token.
- reaction: 120/hour per token.
- radio-chat: 6/min, 30/hour.
- profile-update: 20/hour.
- report: 10/day.
- notification read: generous.

### 11.3 Shadow safety

Avoid public “you are banned” unless necessary. Use gentle language:

- “Nội dung này cần Thủ Các soi lại trước khi hiện ra cộng đồng.”
- “Hôm nay duyên này đã đủ, mai mình gieo tiếp nhé.”

### 11.4 Admin audit

Every admin moderation/reward/role/profile change logs before/after. This matters because admin has full power.

---

## 12. Mobile nav IA

### 12.1 Requirement

Feed renamed **BẢNG NHÂN DUYÊN**, but **Âm Kinh** and **Phước Phiếu** must remain clearly visible in mobile nav/bottom bar.

### 12.2 Recommended bottom nav 5

1. **Nhân Duyên** → `/bang-nhan-duyen`  
   Icon: interlinked nodes / lotus grid. Home after login.
2. **Âm Kinh** → `/nacha`  
   Icon: note/headphones. Must remain explicit.
3. **Gieo** → opens composer sheet  
   Icon: plus/lotus, central elevated action. If guest -> `/vao-coi`.
4. **Phước Phiếu** → `/phuoc-phieu`  
   Icon: talisman/QR. Must remain explicit.
5. **Cõi Ta** → logged-in `/coi/{pham}` else `/vao-coi`  
   Icon: avatar/temple.

Header/floating:

- Chuông Duyên bell with badge.
- Radio mini pill when live? On social pages, a small top pill “Radio đang ngân”.

### 12.3 Desktop nav

Reduce desktop top nav:

- Bảng Nhân Duyên
- Âm Kinh
- Phước Phiếu
- Radio
- Cõi Ta
- Khám Phá dropdown: Kinh Tạng, Pháp Bảo, Bí Sử, Ngũ Tầng, Liên Lạc.

This keeps knowledge core accessible without overwhelming.

---

## 13. Art architecture adaptive: Three/Galaxy/Hyperspeed

### 13.1 Layering model

1. **Core static sacred UI**: CSS gradients, parchment, typography, no JS dependency. Always.
2. **Motion light**: CSS ripple, glow border, IntersectionObserver. Use current style, respects `prefers-reduced-motion`.
3. **Canvas/WebGL hero**: Three/Galaxy/Hyperspeed only as optional component loaded dynamically.
4. **Device governor** decides art level.

### 13.2 Device governor

Client function `getArtTier()`:

- If `prefers-reduced-motion: reduce` -> tier 0.
- If `navigator.connection.saveData` -> tier 0.
- If `deviceMemory <= 2` or hardwareConcurrency <= 4 -> tier 1 max.
- If mobile and viewport < 390 -> tier 1.
- If WebGL unavailable -> tier 1.
- Else tier 2/3.

Tiers:

- Tier 0: static backgrounds.
- Tier 1: CSS particles/ripples only.
- Tier 2: lightweight canvas starfield/galaxy at capped DPR 1, 30fps.
- Tier 3: Hyperspeed/Three hero, desktop/high-end only, paused offscreen.

### 13.3 Implementation constraints Astro

- Do not import Three into base bundle. Use dynamic import only on pages needing it.
- Put art modules in `website/src/scripts/art/` or components island script.
- Use `<canvas data-art="galaxy">` placeholder; script loads after idle: `requestIdleCallback` fallback setTimeout.
- Pause animation on `visibilitychange` hidden and when IntersectionObserver offscreen.
- Cap DPR: `Math.min(devicePixelRatio, 1.5)` desktop; 1 mobile.

### 13.4 Where to use

P0 no WebGL needed for core social.

P1/P2:

- Landing `/` or `/bang-nhan-duyen` header: subtle galaxy frequency field.
- Radio: avatar orbit/ripple CSS, not heavy Three.
- Phước Phiếu activation: brief hyperspeed “enter cõi” if high-tier only.
- 15 Phẩm journey: Three/Galaxy “cõi map” later.

---

## 14. Milestones with acceptance tests & rollback

### M0 — Backup, migration harness, public_id, no UI change

**Goal:** prepare DB safely.

Tasks:

- Backup `backend/data/phuocphieu.db` and `amkinh.db`.
- Enable SQLite WAL if safe: `PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000;` at startup.
- Add idempotent migrations for profile/social/notification/radio tables.
- Add `public_id` to users and backfill.
- Ensure `userPublic` has option `self` vs public, stop exposing raw token in new social APIs.

Acceptance tests:

- `GET /pp-api/health` ok.
- Existing login `/login-pass`, `/account`, `/radio/now`, `/inbox/unread` unchanged.
- `PRAGMA table_info` shows new columns/tables.
- Existing pages load with no console fatal.

Rollback:

- Code rollback only. Added tables/columns are non-breaking.
- Restore DB backup only if migration corrupts DB (unlikely if idempotent).

### M1 — Profile/Bảng Công Đức v1

**Goal:** profile becomes social identity.

Tasks:

- Add `/profile`, `/profile/update`, `/profiles/search`.
- Update `coi/[pham]` header to use avatar/tags/vow.
- Add built-in avatar picker and tags editor.
- Public profile route alias `/nguoi/[phapdanh]` or client page `/nguoi?pd=` if static constraints; Astro dynamic static cannot know all users, so use a static shell page `/nguoi` with query or route fallback if server supports. Recommendation: `/nguoi/index.astro` shell reads `?p=`.

Acceptance tests:

- Logged-in user can set vow/tags/avatar.
- Guest can view public profile without seeing token/email/matma.
- Search finds Pháp Danh and returns public ids only.
- Mobile layout no overflow.

Rollback:

- Hide edit UI; endpoints/tables harmless.

### M2 — Posts/replies/reactions core

**Goal:** actual wall/social graph.

Tasks:

- Add post/reply/reaction endpoints.
- Add composer component.
- Add Bảng Công Đức posts tab.
- Add moderation blocklist checks.
- Notifications on reply/reaction.

Acceptance tests:

- User A creates post; User B sees it on A profile.
- User B replies; User A gets notification.
- User A deletes own post; it disappears from feed but DB status soft-deleted.
- User cannot edit/delete another user’s post.
- Blocked word is rejected/flagged.
- Rate limit returns 429 friendly.

Rollback:

- Disable composer and feed entry points; existing account/radio/inbox unaffected.

### M3 — BẢNG NHÂN DUYÊN feed

**Goal:** central feed after login.

Tasks:

- Create `/bang-nhan-duyen.astro` static shell.
- Implement `/feed` ranking.
- Add cards: post, system-duyen, radio-now, mảnh kinh.
- Redirect logged-in home? Soft: nav points there first; do not redirect `/` until tested.
- Rename UI from Dòng Duyên to BẢNG NHÂN DUYÊN.

Acceptance tests:

- Logged-in user sees feed with at least radio/daily card even no posts.
- Feed excludes blocked/muted/private/deleted.
- Diversity: no >2 same author in first page.
- Cursor/next page works.
- Mobile first content visible above fold.

Rollback:

- Nav points back to `/`; `/bang-nhan-duyen` can remain hidden.

### M4 — Chuông Duyên

**Goal:** notifications hub.

Tasks:

- Add notification APIs and page `/chuong-duyen` or drawer.
- Badge in BaseLayout from notifications + inbox.
- Mark read.
- Group repeated notifications.

Acceptance tests:

- Reply/reaction increments badge.
- Opening Chuông shows item; mark-read decrements badge.
- Inbox unread still works.
- No duplicate spam for 10 reactions same target in short window (grouped).

Rollback:

- Hide bell; notifications table harmless.

### M5 — Radio presence/chat

**Goal:** nghe chung visible.

Tasks:

- Add `/radio/ping`, `/radio/presence`, `/radio/chat`.
- Update `radio.astro` avatar orbit + chat bubbles.
- Add TTL cleanup.

Acceptance tests:

- Two logged-in browsers show each other avatars within 20s.
- No avatar -> initials/Pháp Danh fallback.
- Chat max length enforced; appears near avatar/list; expires.
- Closing tab removes presence within 90s.
- Autoplay blocked does not create fake listener before user joins.

Rollback:

- Feature flag `RADIO_SOCIAL=0` returns empty presence; UI hides orbit.

### M6 — Farm công đức v2

**Goal:** allow farming but make it proof-bound and wholesome.

Tasks:

- Add `merit_actions`.
- Refactor `/tich-phuoc` to proof-bound for high-value actions.
- Convert direct farm buttons on Cõi into action links/composer/radio/Âm Kinh.
- Add daily reflection/Hồi Quang endpoint.
- Add admin merit audit/reverse P1.

Acceptance tests:

- Repeated diem-danh caps politely.
- Radio reward requires duration/presence; immediate click does not farm repeatedly.
- Posting/replying creates merit action once per proof.
- Duplicate proof id cannot double count.
- Existing ledger still shows added Phước.

Rollback:

- Restore old `tich-phuoc` behavior if necessary, but keep merit table unused.

### M7 — Mobile IA/nav

**Goal:** navigation matches new decisions.

Tasks:

- BaseLayout desktop nav reduce.
- Bottom nav 5: Nhân Duyên, Âm Kinh, Gieo, Phước Phiếu, Cõi Ta.
- Floating Chuông bell.
- Ensure safe-area and keyboard composer behavior.

Acceptance tests:

- On 360px width, all 5 bottom items readable/tappable.
- Âm Kinh and Phước Phiếu always visible.
- Gieo opens composer if logged in, login if guest.
- Active states correct for `/nacha`, `/phuoc-phieu`, `/bang-nhan-duyen`, `/coi/*`.

Rollback:

- Revert BaseLayout only; no backend impact.

### M8 — Adaptive art enhancement

**Goal:** beautiful but not fragile.

Tasks:

- Add art governor.
- Add CSS sacred motion baseline.
- Add optional galaxy/hyperspeed modules dynamic import.
- Use on landing/feed hero only first.

Acceptance tests:

- `prefers-reduced-motion` disables heavy animation.
- Low memory/saveData disables WebGL.
- Lighthouse mobile no catastrophic bundle increase for social pages.
- Hidden tab pauses animation.
- No JS error if WebGL unavailable.

Rollback:

- Feature flag `localStorage.artTier=0` or config disables dynamic art; remove script include.

### M9 — Invite/Chứng Duyên P1

**Goal:** growth with human approval.

Tasks:

- Add invite request endpoints and UI.
- Inviter receives Chuông + inbox fallback.
- Approve creates user at Trúc Duyên and rewards inviter with caps.
- Deprecate raw token referral in UI.

Acceptance tests:

- New user via invite cannot login until approved.
- Inviter approves -> account created rank 1 Trúc Duyên.
- Inviter sees request and accepted history.
- Reject notifies gently.

Rollback:

- Keep existing QR activation path; hide invite link.

---

## 15. Edge cases checklist

### Identity/auth

- Duplicate Pháp Danh race: existing unique index catches; profile search must handle Unicode normalization consistently.
- `phapdanh_key` currently keeps accents (`normalize NFC`) not strip accents. Searching should use LIKE on lower NFC; accent-insensitive search P1 requires additional normalized column.
- Public profile must not expose raw token; current `userPublic` does. New social APIs need safer public mapper.
- Referral links currently can leak token; do not make them more prominent until invite_code exists.

### Feed

- Empty community: feed still needs daily mảnh kinh + radio + “hãy gieo lời đầu”.
- Spam from auto ledger: only meaningful ledger kinds become public.
- Deleted user/token: posts retain phapdanh snapshot; show “Đạo hữu đã ẩn danh” if needed.
- Private/members visibility with guest: do not show members/private.

### Replies

- Parent deleted: child replies can show under tombstone or be hidden; recommendation show “Lời đã ẩn” if children remain.
- Reply to deleted post rejected.
- Self-notification suppressed.

### Reactions

- Race double reaction: unique constraint; handle conflict by delete/toggle.
- Reaction count cache can drift; periodic recount admin endpoint or update in transaction.

### Notifications

- User with thousands of notifications: cursor pagination and indexes.
- Grouping can hide important moderation notices; do not group system/admin warnings.

### Radio

- Multiple tabs same token: count once, latest client wins.
- Clock drift: server radioNow authoritative.
- Presence cleanup after crash relies on TTL; fine.
- Chat during gap: attach to current next/last item; or reject “đài đang chuyển nhịp”. Simpler: allow chat with `item_file` null during gap.

### Merit/farm

- Users farm by many accounts: IP hash anomaly -> pending high-value rewards.
- Users post low-quality replies for Phước: duplicate/short/no-reaction/reported replies get no or reversed merit.
- Allow farm but avoid public leaderboard; otherwise incentives distort.
- Admin adding Phước must audit.

### Moderation

- Reports can be abused to hide others; require trust/unique threshold, admin review.
- Blocklist false positives for Dharma discussion words? Keep blocklist focused on obvious terms.
- External links in posts are high risk; P0 either disallow or pending review.

### Art/performance

- WebGL context loss: listen `webglcontextlost`, fallback static.
- Mobile battery: pause offscreen, cap FPS.
- Accessibility: reduced motion honored; color contrast on dark backgrounds.

### Static Astro constraints

- Dynamic user pages cannot be pre-rendered for every user. Use static shell pages with query params or configure SSR later. For now:
  - `/bang-nhan-duyen.astro` shell fetches feed.
  - `/nguoi.astro?p=phapdanh` shell fetches profile.
  - `/bai.astro?id=123` shell fetches post.
- Existing `/coi/[pham].astro` is static per Phẩm and can remain self-dashboard.

---

## 16. Practical implementation order recommendation

Do **not** start with Three/Galaxy or invite auth. Start with data + social primitives.

1. **M0 migrations/public_id/WAL** — safest foundation.
2. **M1 profile identity** — avatar/tag/vow makes people feel alive.
3. **M2 post/reply/reaction** — core social loop.
4. **M3 BẢNG NHÂN DUYÊN** — feed loop with Dharma/knowledge bias.
5. **M7 mobile nav** can be done alongside M3 because IA must expose feed + Âm Kinh + Phước Phiếu.
6. **M4 Chuông Duyên** — retention.
7. **M5 radio presence/chat** — wow differentiator.
8. **M6 farm v2** — convert current farm buttons before scale.
9. **M8 adaptive art** — beautify once core is stable.
10. **M9 invite approval** — growth gate after social graph works.

---

## 17. P0/P1/P2 priority map

### P0 — must do first

- SQLite migrations + indexes + public_id.
- Safer public user mapper, no raw token in public social APIs.
- Profile avatar/tag/vow.
- Post/reply/reaction tables and endpoints.
- BẢNG NHÂN DUYÊN feed endpoint and page.
- Mobile nav with **BẢNG NHÂN DUYÊN + Âm Kinh + Phước Phiếu** clearly visible.
- Basic Chuông Duyên notifications for reply/reaction/contribution review.
- Moderation blocklist, report table, basic rate limits.
- Keep auth unchanged but do not worsen token exposure.

### P1 — differentiators and sustainability

- Radio presence/avatar/chat TTL.
- Farm công đức v2 proof-bound; replace direct high-value farm buttons.
- Đồng Hành/mute/block.
- Inbox compose/search/auto refresh using profile search.
- Invite/Chứng Duyên approval flow.
- Feed diversity/quality tuning + seen tracking.
- Admin moderation dashboard + audit log.
- Hồi Quang daily reflection and Mảnh Như Lai cards.

### P2 — immersive scale

- Adaptive Three/Galaxy/Hyperspeed art.
- 15 Phẩm journey/cõi map.
- PWA/push/offline audio cache.
- Upload pipeline for avatars/media.
- Session-token/cookie auth redesign.
- Analytics dashboards for healthy community metrics.

---

## 18. Final product stance

Tần Số Nacha should reward returning not by anxiety, streak pressure, or public competition, but by **a feeling that each visit leaves the mind cleaner and the community warmer**.

Architecture principle:

> Every feature must answer: “Việc này có giúp người dùng gần Pháp hơn, tu tập đều hơn, hiểu biết sâu hơn, hoặc đối xử lành hơn không?”

If yes, put it into BẢNG NHÂN DUYÊN. If no, keep it out or make it private/admin-only.
