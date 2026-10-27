# Tần Số Nacha — Full Nền Tảng (TanSoNacha)

Toàn bộ nền tảng web **Tần Số Nacha** (Tàng Kinh Các): trang chủ, **Âm Kinh** (nhạc Phật), **Phước Phiếu** (voucher/QR vô cực), **Bảng Nhân Duyên** (social feed), **Radio/Cõi**, và **hệ auto-engagement** (view/like/comment tự động).

Domain: `tangkinhcac.62.146.238.213.sslip.io` · `tansonacha.62.146.238.213.sslip.io`

> Đây là repo FULL nền tảng. Repo con chỉ-Âm-Kinh + auto comment: `autocommenttanso`.

---

## Kiến trúc

```
website/            Astro static — toàn site
  src/pages/
    index, menu, about, story, floors, contact ...   trang tĩnh/giới thiệu
    am-kinh/         Âm Kinh: music home, artist/album/track, BXH, player, lyric, reaction, comment
    phuoc-phieu/     Phước Phiếu: 15 Phẩm, art từng cấp
    coi/             Cõi Của Ta (acc), Pháp Hội/event
    pp/              trang đích QR /pp/<mã>
    bang-nhan-duyen, chung-duyen, moi, nguoi, inbox, chuong-duyen, vao-coi, radio, dong-gop ...
  src/data/          amkinh.ts (+ amkinh-gen.ts auto — KHÔNG sửa tay), phuocphieu.ts
  src/layouts/       BaseLayout, LobbyLayout (nav gộp có expand)
backend/
  server.mjs         API Âm Kinh (4213): stats/hit/comment + auto view + auto like + snapshot BXH (/top)
  phuocphieu.mjs     API Phước Phiếu (4214): voucher/activate/login/account/admin
  migrate-social.mjs Migration social (profile/feed/reaction/invite tables)
  gen-vouchers.mjs   Sinh voucher + shortlink (Shlink)
  gen-qr-infinity.py QR có dấu vô cực ∞ (qrcode + PIL)
scripts/             Hệ auto comment: daily runner, refill guard, pool gen, 280-nick pool, personas
docs/                Quy trình comment + handoff + brainstorm
```

## Build & Run
```bash
cd website && npm install && npm run build      # → dist/  (PM2: tangkinhcac, serve dist -l 4201)
node backend/server.mjs                          # PM2: amkinh-api (4213)
node backend/phuocphieu.mjs                      # PM2: phuocphieu-api (4214)
```
Caddy route: `/api/*`→4213 (Âm Kinh), `/pp-api/*`→4214 (Phước Phiếu), `/pp/*` + còn lại→4201.

## Backend Âm Kinh — auto engagement (`backend/server.mjs`)
- **Auto view**: mỗi track lịch riêng, sau 2–9 phút tăng 1–3 view.
- **Auto like theo view**: mỗi view mới cộng "tín dụng like" = 4–13% view vừa tăng → bung reaction thật (random emotion có trọng số).
- **Snapshot BXH** mỗi giờ → `/top?period=day|week|month`.
- DB `amkinh.db`: `counters`, `comments`, `snapshots`, `comment_pool`, `nicks`.

## Hệ Comment Dạo (scripts/) — chi tiết: `docs/COMMENT-SYSTEM-PROCESS.md`
- `amkinh-daily-comment.py` — cron 1 lần/ngày, mỗi bài comment mới = 1–3% like của bài, dùng bank + 280 nick, ~18% reply, **không cần model**.
- `amkinh-refill-guard.py` — refill khi kho < 30% chưa dùng; câu mới không trùng câu đã dùng (trừ tone `niem` được na ná).
- `amkinh-pool-gen*.py` — sinh kho 12 tone (tán thán/thiền vị/đời thường/nhí nhố/quan điểm/nhận xét/hook/reply/niệm/icon-only/lú lú/bình lời bài hát).
- `amkinh-nick-pool.json` — 280 nick chia 4 nhóm/model (Opus 4.6 / Sonnet 5 / Sonnet 4.6 / GPT-5.5), mỗi nhóm 1 giọng.
- Guard chống lộ: câu dùng-ẩn-vĩnh-viễn · chặn self-reply · dedupe per-track · nick theo khung giờ · timestamp thật.

## Phước Phiếu
15 Phẩm = 15 phiếu; token = mã phiếu (login mãi); QR ∞ không đốt (quét lại = login). Backend `phuocphieu.mjs` (users/vouchers/ledger). Blueprint: `docs/`.

## Bảo mật (đã chặn trong .gitignore)
KHÔNG commit: `node_modules`, `dist`, DB thật + backup (`*.db`, `*.bak-*`), media nặng (images/audio/lyrics-cache), token/secret/log.
`amkinh-gen.ts` là file sinh tự động — không sửa tay.

> Tần Số Nacha 那迦頻 — Nơi mỗi duyên lành ngân thành tần số.
