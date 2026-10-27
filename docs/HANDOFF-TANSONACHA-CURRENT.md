# HANDOFF TẦN SỐ NACHA — CURRENT

**Cập nhật:** 10/07/2026 22:20 CEST  
**Mục đích:** Chuyển sang box/session mới và tiếp tục chính xác, không làm lại từ đầu.

## 1. Đọc bắt buộc theo thứ tự

1. `/root/.openclaw/workspace/TangKinhCac/HANDOFF-TANSONACHA-CURRENT.md` — trạng thái thi công hiện tại, nguồn ưu tiên cao nhất.
2. `/root/.openclaw/workspace/TangKinhCac/HANDOFF-TANSONACHA.md` — yêu cầu gốc/kiến trúc/plan.
3. `/root/.openclaw/workspace/TangKinhCac/HANDOFF.md` — hạ tầng VPS, PM2, Caddy, backend, DB.
4. Reports/evidence:
   - `state/social-m5-prod-report.json`
   - `state/social-m5-acceptance.json`
   - `state/social-m6-prod-report.json`
   - `state/social-m6-acceptance.json`
   - `state/social-m8-prod-report.json`
   - `state/social-m8-acceptance.json`
   - `state/m9-authoritative-20260710-214951/`
   - `state/social-m9-prod-report.json` (cũ, có thể còn ghi FAIL; phải reconcile với evidence mới)
   - `state/social-m9-acceptance.json` (cũ, có thể xung đột; không tin mù quáng)

## 2. Milestone đã hoàn thành

- **M0–M4:** migration/public ID, Profile/Bảng Công Đức, posts/replies/reactions, Bảng Nhân Duyên feed, Chuông Duyên.
- **M5:** Radio presence/chat — PASS và production.
- **M6:** Farm Công Đức proof-bound — PASS; radio thưởng duy nhất qua proof sau presence >=180 giây; chống duplicate/cap/legacy abuse.
- **M7:** Mobile nav 5 mục — Nhân Duyên · Âm Kinh · Gieo · Phước Phiếu · Cõi Ta; badge Chuông Duyên.
- **M8:** Adaptive Art — PASS và production; tier 0/1/2, reduced-motion/saveData/device/WebGL governor.

## 3. Trạng thái M9 chính xác

M9 Chứng Duyên đã trải qua nhiều lượt sửa/audit. Source hiện đã có:

- UI applicant: `website/src/pages/moi.astro`
- UI inviter: `website/src/pages/chung-duyen.astro`
- Opaque invite + request/receipt status APIs trong `backend/phuocphieu.mjs`
- Migration invite tables trong `backend/migrate-social.mjs`
- Login hỗ trợ cả token legacy và `phapdanh + matma` bằng verify constant-time.
- Self-invite check đã đặt trước duplicate-name generic.
- Harness ledger đã dùng đúng `ledger.token` và timestamp `ledger.ts`.

**Authoritative M9 E2E mới nhất:** `state/m9-authoritative-20260710-214951/`

Worker báo PASS:
- fresh copied production DB;
- migration 2 lần;
- create/list/cap 5/ngày;
- pending receipt;
- reject nhẹ nhàng trước khi có account;
- approve tạo account;
- login Pháp Danh + Mật Mã HTTP 200;
- +30 Phước đúng một lần;
- duplicate/self 409; invalid/expired 410;
- integrity OK, FK=0.

Production backend đã backup/migrate/restart tại:
- `backups/social-m9-deploy-20260710-215004/`

**External smoke đã được parent kiểm trực tiếp sau đó:**
- `https://tangkinhcac.62.146.238.213.sslip.io/pp-api/health` → HTTP 200
- `/moi/` → 200
- `/chung-duyen/` → 200
- `/pp/`, `/radio/`, `/bang-nhan-duyen/`, `/nguoi/` → 200
- PM2 `tangkinhcac` + `phuocphieu-api` online
- production DB integrity `ok`, FK 0

Lưu ý: route đúng là `/pp-api/*`; worker từng kiểm nhầm `/api/pp/*` nên nhận 404. Domain canonical là sslip ở trên, không phải `tangkinhcac.vn`.

**Việc cần làm đầu tiên ở box mới:**
1. Reconcile/ghi đè `state/social-m9-prod-report.json` và `state/social-m9-acceptance.json` thành một bộ authoritative thống nhất, dựa trên evidence `state/m9-authoritative-20260710-214951/` + external smoke đúng `/pp-api/health`.
2. Chạy secret/raw-token scan cuối cho M9. `ChauNacha` có thể xuất hiện trong admin frontend và không tự động là token leak; phải phân biệt literal admin token/credential với label/copy.
3. Nếu tất cả PASS, chốt M9 PASS rồi chạy Final Gate.

## 4. Final Gate chưa hoàn thành

Hai lượt Final Gate trước đều dừng vì M9 lúc đó chưa authoritative PASS hoặc hết timeout. Không được coi final.

Backup release candidate đã có:
- `/root/.openclaw/workspace/backups/TangKinhCac-final-rc-20260710-210435.tar.gz`

Final Gate cần kiểm:
- migration idempotence, DB integrity/FK;
- voucher activation/login/account/inbox;
- radio/autoplay/presence/chat;
- social profile/feed/post/reply/reaction/notification;
- merit proof/dedupe/cap;
- M9 invite/request/receipt/approve/reject/login/+30/idempotence;
- auth/permissions/privacy/blocking/rate/input/secret scan;
- Astro build, key routes local + canonical sslip;
- PM2/logs, responsive/accessibility, Adaptive Art low-device/reduced/no-WebGL;
- exact test cleanup + rollback readiness.

Bắt buộc tạo:
- `state/tansonacha-final-acceptance.json`
- `state/tansonacha-final-report.json`

Chỉ khi report Final = PASS mới được báo hoàn thành và cập nhật handoff/memory.

## 5. Watchdog

Cron: **Tần Số Nacha Worker Watchdog**  
Job ID: `705c004d-01bd-4484-9deb-486a56d6f888`  
Chu kỳ: **20 phút** (`everyMs=1200000`) — user yêu cầu mọi cron/watchdog tương tự sau này mặc định 20 phút.  
Anti-loop: 1 worker/scope; event dedupe; tối đa 2 retry/milestone; không thay đổi thì NO_REPLY; Final PASS thì tự xóa cron.

State: `state/tansonacha-watchdog.json`

## 6. Quy tắc thi công

- Model: `gptplus4/cx/gpt-5.6-sol`.
- Backup trước sửa/deploy.
- Không tin report cũ nếu xung đột evidence mới; reconcile theo timestamp + test artifact + production smoke.
- Không báo “đang chạy” nếu không có run ID/status active thật.
- Không báo PASS nếu thiếu report/evidence.
- Không spawn trùng scope; dùng watchdog 20 phút, không poll loop.
- Không làm lại M0–M8.
- Không đổi route Caddy/config nếu `/pp-api/*` đang 200.

## 7. Final Gate authoritative — 10/07/2026 22:28 CEST

- **M9: PASS**, reconciled from `state/m9-authoritative-20260710-214951/` and canonical `/pp-api/health` HTTP 200.
- **Final Gate: PASS**. Authoritative files: `state/tansonacha-final-acceptance.json`, `state/tansonacha-final-report.json`.
- Evidence directory: `state/final-gate-20260710-222741/`; Astro build 375 pages, local/canonical smoke PASS, production DB integrity `ok`, FK 0, PM2 web/API online.
- Secret scan completed; `ChauNacha` / `Cháu Nacha` occurrences classified as label/admin identity unless a credential value is present. No raw credential copied into reports.
- Caddy unchanged. Final gate made no production DB writes; isolated M9 evidence used copied DB. Backup before report/handoff edits: `backups/final-gate-20260710-222741/`.
- Watchdog intentionally retained for parent confirmation/cleanup.
