# TÀNG KINH CÁC — HANDOFF (Phước Phiếu + Âm Kinh)
> Cập nhật: 2026-07-09 · Bàn giao context sang session mới để tiếp tục. Đọc kỹ file này trước khi làm.

## 0. TÓM TẮT 1 DÒNG
Đang xây hệ **Phước Phiếu** (Tần Số Nacha) cho website Tàng Kinh Các: 15 Phẩm, QR có dấu ∞, backend acc thật trên VPS. GĐ1 (mặt tiền) + GĐ2 (backend + 700 QR + luồng quét) ĐÃ XONG. Còn GĐ3/GĐ4 + nối data thật vào trang Cõi.

## 1. HẠ TẦNG (VPS)
- Website: Astro static, dir `~/.openclaw/workspace/TangKinhCac/website/`, build `npm run build` → `dist/`
- Serve qua PM2 `tangkinhcac` (`serve dist -l 4201`). Sau build phải `pm2 restart tangkinhcac`.
- Domain: **https://tangkinhcac.62.146.238.213.sslip.io** (Caddy auto-HTTPS)
- Caddy: `/etc/caddy/Caddyfile` block `tangkinhcac.*`:
  - `/pp-api/*` → localhost:4214 (backend Phước Phiếu)
  - `/api/*` → localhost:4213 (backend Âm Kinh reaction/comment)
  - `/pp/*` → rewrite→/pp/ → 4201 (trang kích hoạt QR)
  - còn lại → 4201 (site tĩnh)
  - Reload: `systemctl reload caddy`. Backup trước khi sửa.

## 2. BACKEND (PM2, zero-dep Node + node:sqlite --experimental-sqlite)
- `amkinh-api` port 4213 — reaction/comment Âm Kinh. File `backend/server.mjs`. DB `backend/data/amkinh.db`.
- `phuocphieu-api` port 4214 — acc Phước Phiếu. File `backend/phuocphieu.mjs`. DB `backend/data/phuocphieu.db`.
  - Tables: users(token,phapdanh,email,pham,rank,phuoc,duyen), vouchers(code,pham,prefix,seq,status,owner), ledger(Sổ Duyên), 
  - Endpoints (prefix /pp-api): GET /voucher?code= · POST /activate{code,phapdanh} · POST /login{token} · GET /account?token= · POST /email{token,email} · GET /admin/stats (header X-Admin-Token: ChauNacha)
  - Activate: token = mã phiếu; tặng Phước khởi = rank*100; ghi Sổ Duyên.
- `pm2 save` đã chạy. Restart: `pm2 restart phuocphieu-api`.

## 3. PHƯỚC PHIẾU — SPEC ĐÃ KHÓA (anh Nấng chốt)
- **15 Phẩm = 15 Phước Phiếu**. 3 phẩm đầu đã mở: Trúc Duyên(P1,TD) · Kim Tâm(P2,KT) · Nguyên Niệm(P3,NN). 12 phẩm sau "còn ẩn trong sương".
- Data 15 phẩm: `website/src/data/phuocphieu.ts` (rank, slug, han, hue màu mỗi cấp, poetic, path tu-than/phung-su/song-dinh).
- **Số lượng phát hành:** 400 TD + 200 KT + 100 NN = 700 phiếu. + 3 mã master đuôi -0000 (của anh Nấng test): TD-FEHWFKTEX2X77-0000, KT-5FR4X7YY43NG9-0000, NN-NCJQH5N5EFMZY-0000. Tổng DB 703.
- **Mã/Token:** `TD/KT/NN-[13 ký tự chữ+số]-[số thứ tự 4 số]`. Token = mã phiếu, dùng login mãi. QR không đốt — quét lại = login thẳng vào acc.
- **Cấp lên bằng mua phiếu = gieo Phước.** Quét phiếu = vào thẳng cấp đó.
- **Từ ngữ:** Phật ngữ tinh tế — "Pháp Danh" (không "username"), "Khai Duyên", "Sổ Duyên", "chìa khoá phiếu". KHÔNG thuật ngữ kỹ thuật.
- **Art:** cực hạn tinh tế, mỗi cấp tông màu riêng (hue trong data), đồng bộ bảng màu Tiểu Tâm (#F5F0EB nền, #C9A96E bronze, #2C2C2C ink), chữ Hán trang trí, divider ornament.

## 4. QR (có dấu VÔ CỰC ∞) — ĐÃ SINH XONG
- Sinh QR: `backend/gen-qr-infinity.py` (venv `~/.openclaw/workspace/deploy/shlink/venv/bin/python`, qrcode+PIL). RoundedModuleDrawer, ink #2C2C2C, vòng tròn trắng + ∞ liền nét (lemniscate of Gerono), error correction H, logo 22%. Decode OK (pyzbar).
- Sinh voucher+shlink: `backend/gen-vouchers.mjs` (Shlink API tạo short-url, findIfExists). Lưu ý: Shlink POST customSlug đôi khi timeout thoáng → retry.
- QR files: `backend/vouchers-out/{truc-duyen,kim-tam,nguyen-niem}/*.png` + 3 zip `PhuocPhieu-QR-<cấp>.zip` + `manifest.csv`. Master: `TangKinhCac/pp-qr-master/`.
- **Hệ QR = Shlink** trên VPS: domain qr.62.146.238.213.sslip.io, API key trong `~/.openclaw/workspace/deploy/shlink/CREDENTIALS.md`. Short-url qr.../<code> → tangkinhcac.../pp/<code>. QR không đổi, đổi đích qua API được.

## 5. TRANG ĐÃ DỰNG (Astro, live 200)
- `/phuoc-phieu` — tổng: Duyên Khởi + 3 cách dùng (Gieo Duyên 緣/Ấn Tống 印/Ưu Đãi 惠) + Thang 15 Phẩm.
- `/phuoc-phieu/[pham]` — 3 trang phẩm, art riêng, board concept, ô chìa khoá.
- `/coi/[pham]` — trang Cõi (acc): stat Phước/Duyên/Mảnh/Phẩm, Kho Tàng 108 mảnh, Sổ Duyên, Con Đường, gieo hạt. **⚠️ SỐ LIỆU CÒN DEMO — chưa nối token thật.**
- `/coi/[pham]/event` — Pháp Hội: đặt Pháp Danh, 2 khung giờ vàng 7h/21h, Pháp Bảo hôm nay.
- `/pp/index.astro` (trang đích QR /pp/<mã>): client đọc mã→pp-api. new→Khai Duyên; activated→login thẳng→/coi/<pham>/event; lỗi→báo. LUỒNG NÀY ĐÃ THẬT.
- `/coi-admin` — Cửa Quán Chiếu (token ChauNacha, CLIENT-SIDE tạm, cần làm backend gate).
- Board hình: `website/public/images/phuoc-phieu/*.jpg` (đã nén 27MB→2.6MB).
- Tab bar dưới + menu tổng + footer: đã thêm "Phước Phiếu" (giữ "Mượn Kinh").

## 6. LUỒNG QUÉT (đã test PASS end-to-end, users=1)
Quét QR → /pp/<mã> → backend /voucher. **Mới**: Khai Duyên→nhập Pháp Danh→/activate→tạo acc(token=mã, +Phước, Sổ Duyên)→vào /coi/<pham>/event. **Đã có chủ**: chào→login→event. Token lưu localStorage `pp-token`.

## 7. CÒN LÀM (ưu tiên)
1. **Nối trang Cõi + Pháp Hội đọc data THẬT** (đọc localStorage `pp-token` → GET /pp-api/account → hiển thị Phước/Duyên/Sổ Duyên/mảnh thật thay demo). ← QUAN TRỌNG NHẤT
2. Cổng admin "Cửa Quán Chiếu" bảo mật backend (token ChauNacha giấu server, hiện đang client-side).
3. GĐ3: rút 108 Mảnh Chuyện Như Lai + Điểm Duyên ngẫu nhiên + quà số (audio/podcast) khi dự pháp hội. Event 2 khung giờ 7h/21h cập nhật thật.
4. GĐ4: Trao Duyên — tặng quà/phiếu cho người khác qua QR/chạm-quét (NFC web hạn chế iPhone → dùng QR trước).
5. Đóng bộ 700 QR đã gửi anh in (3 zip đã giao). Khi có domain tansonacha.com thật → đổi Shlink domain (xem CREDENTIALS.md).

## 8. BLUEPRINT NGUỒN
`TangKinhCac/phuoc-phieu-blueprint/BluePrint/blueprint.pdf` + `.html` + 9 board PNG. Nội dung: Phước Phiếu = ghi nhận gieo tử tế (không bán phước); 3 bậc vật lý Hạt/Hoa/Vô Cực; Thang 15 Phẩm; 2 điểm 福Phước(đếm, chỉ cộng khi trao)/緣Duyên(ngẫu nhiên); 108 Mảnh Chuyện Như Lai; pháp lý không chứng khoán/không đa cấp/không may rủi.

## 9. ÂM KINH (song song, đã xong trước đó)
Hệ nhạc Phật: `/am-kinh` (thư viện artist) → `/am-kinh/tieu-tam` (artist) → `/am-kinh/tieu-tam/da-nacha` (album) → track. Data `website/src/data/amkinh.ts`. Backend reaction/comment `amkinh-api` 4213. 24 bài Nacha có sẵn trong `~/.openclaw/workspace/suno-out/108-phat-tuong/nacha/` CHƯA đổ lên (anh Nấng dặn khoan). 3 album: Dạ Nacha/Dą Sifu Minh Tuệ/Dạ Vô Diện Phật.

## 10. GHI CHÚ VẬN HÀNH
- VPS load hay cao (~6), gateway gửi media/text đôi khi timeout → retry sau, đừng spam.
- Telegram: gửi file dài tiếng Việt = HTML/PDF (weasyprint), không .md. Filename ASCII.
- Memory chi tiết: `~/.openclaw/workspace/memory/2026-07-08.md` + `2026-07-09.md` (tìm "Phước Phiếu").
