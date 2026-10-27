# TASK — Âm Kinh: hoàn tất lyrics + gắn nhạc vào site (Tần Số Nacha)
> Chạy bởi sub-agent GPT-5.5 (anh Nấng chỉ định). Chủ quản: Tiểu Tâm main session.
> Working dir: /root/.openclaw/workspace/TangKinhCac

## BỐI CẢNH (đã làm xong, KHÔNG làm lại)
- 307 bài đã ingest vào /var/www/tansonacha-media/nhac/<album-slug>/<track-slug>.mp3 (32 album, khử trùng md5, 26 dupe bỏ). Covers: /var/www/tansonacha-media/covers/. Serve qua Caddy: https://tansonacha.62.146.238.213.sslip.io/media/... (đã test 206 OK).
- Data sinh sẵn: website/src/data/amkinh-tieutam.gen.json (32 albums; mỗi track: slug,title,author='Tiểu Tâm',src,cover,duration,tag,ready,src_path,md5; 155/307 đã có lyrics timed + suno_id).
- Suno CLI: /root/.openclaw/workspace/suno-cli/target/release/suno (đã auth OK). Lệnh quan trọng: `search "<title>" --json`, `timed-lyrics <clip-id> --json`.
- Lyrics cache: TangKinhCac/radio/lyrics-cache/<clipid>.json (word-level; ~180 file). Log lần 1: radio/fetch-lyrics.log (128 NO-ID + 24 FAIL cần giải).
- Script đã viết sẵn: scripts/fetch-lyrics-v2.py — dùng hex8 cuối tên file nguồn (= 8 ký tự đầu clip UUID) + twin file tên tiếng Việt cùng thư mục downloads-* → suno search → match id.startswith(hex8). CHẠY NÓ TRƯỚC, sửa nếu lỗi.
- Avatar dĩa xoay: /var/www/tansonacha-media/avatar/tieutam-01..45.jpg (600x600).
- Site Astro: TangKinhCac/website — build `npm run build` rồi `pm2 restart tangkinhcac`. Trang nhạc: src/pages/am-kinh/... + src/pages/nacha.astro. Data hiện tại: src/data/amkinh.ts (artist tieu-tam có sẵn 3 album: da-nacha [1 bài da-nam-mo + lyrics đầy đủ], da-sifu-minh-tue [rỗng], da-vo-dien-phat [rỗng]).
- Backend đếm lượt nghe: amkinh-api port 4213, DB TangKinhCac/backend/data/amkinh.db bảng counters(track,metric,count), track id = `tieu-tam:<album-slug>:<track-slug>`. Cơ chế tự tăng 2-9 phút +1-3 đã chạy cho MỌI track có play>0.

## VIỆC PHẢI LÀM (tuần tự)
1. **Hoàn tất lyrics:** chạy `python3 scripts/fetch-lyrics-v2.py` (từ TangKinhCac/). Mục tiêu ≥90% track có lyrics. Bài nào Suno không tìm được: thử lấy lyrics tĩnh từ file lyrics-*.txt cạnh nguồn (suno-out/108-phat-tuong/<mạch>/lyrics-*.txt) làm fallback (lyrics tĩnh = mảng 1 phần tử t:0 hoặc bỏ trống — KHÔNG bịa timing).
2. **Merge data vào site:** viết script node/python đọc amkinh-tieutam.gen.json → sinh file TypeScript `src/data/amkinh-gen.ts` export albums (đúng interface Track/Album trong amkinh.ts, BỎ field src_path/md5). Sửa amkinh.ts: artist tieu-tam.albums = [merge]: album da-nacha gen (12 bài) GỘP VÀO album da-nacha có sẵn (giữ bài da-nam-mo đứng ĐẦU, giữ nguyên lyrics của nó); da-sifu-minh-tue + da-vo-dien-phat thay tracks rỗng bằng tracks gen; các album gen còn lại append sau. Giữ nguyên helpers.
3. **Dĩa xoay avatar random:** trang track player ([track].astro + nacha.astro nếu có player) — ảnh dĩa xoay lấy random 1 trong 45 ảnh /media/avatar/tieutam-XX.jpg (random client-side mỗi lần load). Giữ hiệu ứng xoay có sẵn của player.
4. **Kiểm tra chạy chữ:** player đã có logic lyrics chạy theo t (bài Dạ Nam Mô). Đảm bảo track mới có lyrics cũng chạy chữ. KHÔNG phá bài mẫu.
5. **Seed lượt nghe:** với mỗi track mới, INSERT counters play = random 80-400 (node --experimental-sqlite hoặc sqlite3) để cơ chế tự tăng bắt đầu chạy. Track id đúng format `tieu-tam:<album-slug>:<track-slug>`.
6. **Build + verify:** npm run build (PHẢI 0 error), pm2 restart tangkinhcac. Verify: curl 200 cho /am-kinh, /am-kinh/tieu-tam, 2-3 trang album mới, 2-3 trang track mới; kiểm tra 1 track mới trả lyrics trong HTML; curl /api/stats?track=<1 track mới> có play>0.
7. **Báo cáo:** ghi kết quả (số bài lyrics ok/fallback/thiếu, số album, build status, URL mẫu) vào TangKinhCac/TASK-MUSIC-LYRICS-REPORT.md và trả lời tóm tắt.

## RÀNG BUỘC
- KHÔNG đụng backend phuocphieu.mjs, KHÔNG đổi cấu trúc URL cũ, KHÔNG xoá bài Dạ Nam Mô gốc.
- Title tiếng Việt phải giữ dấu (bài nào title đang mất dấu mà tìm được tên chuẩn từ Suno/twin file thì cập nhật lại có dấu).
- Backup file trước khi sửa: amkinh.ts đã có .bak-ingest.
- VPS load cao: chạy tuần tự, sleep nhẹ giữa call Suno (0.4s), không parallel bừa.

## CẬP NHẬT TIẾN ĐỘ (10/07 11:40 — main session đã làm thêm)
- Lyrics đã lên **266/307** (fetch-lyrics-v2 + fetch-lyrics-v3 dùng Suno playlist API). Còn thiếu chủ yếu:
  - instrumental-vol-1-khong-loi (0/8), relax-sleep-vol-1-dem-mem (0/8), restaurant-jazz-instrument (0/8) → NHẠC KHÔNG LỜI, KHÔNG CẦN lyrics, bỏ qua.
  - bat-khong (12/26 thiếu), rock (2), opera (1) → đã cố hết cách qua search + playlist, clip không còn trên account → CHẤP NHẬN không lyrics, bỏ qua.
  → Bước 1 coi như XONG, KHÔNG cần chạy lại fetch-lyrics.
- Bước 3 (dĩa xoay avatar random): ĐÃ SỬA XONG trong src/pages/am-kinh/[artist]/[album]/[track].astro (random 45 ảnh /media/avatar/). KHÔNG cần sửa lại.
- Script merge ĐÃ VIẾT SẴN: scripts/merge-amkinh.py (sinh src/data/amkinh-gen.ts + vá amkinh.ts). Script seed ĐÃ VIẾT SẴN: scripts/seed-plays.mjs (chạy `node --experimental-sqlite scripts/seed-plays.mjs`).
- VIỆC CÒN LẠI CHO SUB-AGENT: chạy merge-amkinh.py → kiểm tra amkinh-gen.ts + amkinh.ts hợp lệ → npm run build (0 error, sửa nếu lỗi TS) → pm2 restart tangkinhcac → chạy seed-plays.mjs → verify URL (bước 6) → viết report (bước 7).
