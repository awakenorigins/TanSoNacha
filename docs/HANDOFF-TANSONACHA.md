# TẦN SỐ NACHA — HANDOFF (Nâng cấp nền tảng xã hội Phật giáo)
> Cập nhật: 2026-07-10 05:50 CET · Bàn giao từ session topic 348 (Om Hạnh Duyên Om) sang session mới.
> ĐỌC FILE NÀY + `TangKinhCac/HANDOFF.md` (hạ tầng chi tiết) TRƯỚC KHI LÀM.

## 0. TÓM TẮT 1 DÒNG
Anh Nấng chỉ thị đổi **Tàng Kinh Các → TẦN SỐ NACHA**, nâng cấp thành nền tảng xã hội Phật giáo (wall, feed, radio, referral, admin). Đã audit + gửi Master Plan 7 đợt (PDF msg #842, topic 348). **Anh chưa chốt 3 câu hỏi — hỏi lại nếu chưa có trả lời, hoặc nếu anh bảo "ok/bắt đầu" thì khởi công Đợt 1.**

## 1. NGUỒN SỰ THẬT
- Plan đầy đủ: `TangKinhCac/TanSoNacha-Superbrainstorm.html` (+ .pdf đã gửi anh)
- Hạ tầng/spec cũ: `TangKinhCac/HANDOFF.md` (VPS, PM2, Caddy, backend, DB, QR, 15 Phẩm)
- Memory: `memory/2026-07-10.md` (mục "Tần Số Nacha — SUPERBRAINSTORM") + `memory/2026-07-09.md`
- Code: website `TangKinhCac/website/` (Astro, build → pm2 restart tangkinhcac) · backend `TangKinhCac/backend/phuocphieu.mjs` (port 4214, 23 endpoint, DB `backend/data/phuocphieu.db`: users, vouchers, ledger, contributions, im_threads, im_messages)

## 2. YÊU CẦU ANH NẤNG (nguyên gốc, msg #839)
1. Đổi tên site → **Tần Số Nacha** (nền tảng xã hội đạo Phật, Phật tử giao lưu phát triển)
2. Inbox phải thuận tiện (audit: thiếu nút Soạn tin mới, tìm người, auto-refresh)
3. Radio kiểu podcast phát CỐ ĐỊNH theo giờ (audit: chưa phát được âm thanh, chỉ hiện khung 7h/21h)
4. Wall cá nhân kiểu Facebook cho mỗi nick — đăng bài
5. Feed hiện bài random khi login (kiểu MXH)
6. Mọi người reply/nói chuyện trên bảng của nhau
7. Hoạt động gieo duyên/cộng duyên AUTO hiện lên Bảng Công Đức mỗi người
8. Rà toàn bộ từ ngữ cho tinh tế
9. Mở hết 15 Phẩm; user thường chỉ đăng ký được qua: (a) QR Phước Phiếu, hoặc (b) link giới thiệu — người mời thấy có người đăng ký từ link mình, BẤM ĐỒNG Ý mới khởi tạo nick; mọi nick qua link đều bắt đầu ở **Trúc Duyên**
10. Nick **Cháu Nacha** (đã có trong DB, phapdanh 'Cháu Nacha', pham truc-duyen) = nick anh = ADMIN: vào được cả 15 Phẩm + full quyền tuỳ chỉnh MỌI endpoint (server-side, không client-side)
11. Breakdown nhỏ, chính xác, cực hạn art + logic. Superbrainstorm/plan trước, **anh OK mới bắt đầu** ✅ đã làm

## 3. PLAN 7 ĐỢT ĐÃ GỬI (chờ duyệt)
1. **Rebrand** → Tần Số Nacha toàn site; khu nhạc gọn thành 「Âm Kinh」; alias domain tansonacha.*
2. **Admin gốc** — cột `role` trong users, Cháu Nacha = admin server-side, middleware, vào 15 cõi, Cửa Quán Chiếu 5 tab
3. **Bảng Công Đức** — trang `/nguoi/<phapdanh>`: bài đăng + duyên tích auto từ ledger + Kết Duyên 🪷
4. **Tương tác** — lời ghé bảng + đáp lời (reply luồng), thông báo về inbox
5. **Dòng Duyên** — feed random: trộn 4 nguồn, điểm mới+tương tác+nhiễu ngẫu nhiên, trang chủ sau login
6. **Radio pseudo-live** (server giữ lịch+playlist, client seek theo giờ server → nghe cùng khoảnh khắc, Tần Số 7h/21h VN) + inbox nâng (soạn tin, tìm Pháp Danh, auto-refresh 20-30s)
7. **15 Phẩm mở hết + Mời Duyên**: link `/moi/<mã>` → người mới điền Pháp Danh → người mời nhận inbox → bấm 「Chứng Duyên」 → nick khởi tạo ở Trúc Duyên; thưởng dẫn duyên

## 4. TỪ NGỮ ĐÃ ĐỀ XUẤT (chờ anh ưng)
Feed=「Dòng Duyên」· Wall=「Bảng Công Đức」· Like=「Kết Duyên」🪷 · Referral=「Mời Duyên」→「Chứng Duyên」· Referrer=「Người Dẫn Duyên」· Comment=「Lời Ghé Bảng / Đáp Lời」· Radio=「Tần Số 7h · Tần Số 21h」. Lưu ý cũ: "Đóng Góp"→"GÓP DUYÊN" (không dùng "Cộng Duyên" cho việc đóng góp vì trùng tên gộp phiếu — xem memory 09/07).

## 5. ANH ĐÃ CHỐT (msg #853, 10/07 06:53) — ✅ ĐƯỢC PHÉP TIẾN HÀNH
- **Radio:** podcast Trọng Sinh Tam Tạng (Drive) — ĐÃ TẢI về `TangKinhCac/radio/media/podcast/` (15 tập mp3, slug ASCII, 213MB). **Chạy LIÊN TỤC 24/7**: hết 1 podcast → nghỉ bằng 1 bài nhạc → podcast kế. Bài nhạc xen kẽ tạm: `website/public/audio/da-nam-mo-bon-su-thich-ca-mau-ni-phat.mp3` ("Dạ Nam Mô Bổn Sư Thích Ca Mâu Ni Phật"). Anh sẽ hướng dẫn up nhạc thêm sau. → Radio = pseudo-live loop toàn playlist (anchor epoch + duration từng track, client seek theo giờ server).
- Tên gọi + số Phước dẫn duyên: anh không phản đối → dùng đề xuất (Dòng Duyên / Bảng Công Đức / Kết Duyên / Mời Duyên–Chứng Duyên / +30 Phước / 5 mời/ngày), có thể chỉnh khi anh góp ý.
- Output báo cáo: group Tàng Kinh Các -1003628743472 topic 348.
- Chỉ đạo: cẩn trọng, audit kỹ, cực hạn tinh tế/logic/art — "siêu nền tảng xã hội mới cho Phật giáo, nơi mọi người an tịnh tâm tu duyên cộng phước, lôi cuốn, bền vững".

## 6. QUY TẮC THI CÔNG
- Mỗi đợt: build → test thật (curl backend + browser check) → báo anh → anh gật mới sang đợt kế
- Build web: `cd TangKinhCac/website && npm run build && pm2 restart tangkinhcac`
- Backend sửa xong: `pm2 restart phuocphieu-api`; backup file trước khi sửa (.bak)
- Từ ngữ Phật ngữ tinh tế, KHÔNG thuật ngữ kỹ thuật với user; art cực hạn theo hue từng Phẩm, bảng màu #F5F0EB/#C9A96E/#2C2C2C
- Gửi file Telegram: PDF/HTML→PDF (attach .html đang bị chặn bởi hostReadCapability — dùng weasyprint), filename ASCII
- Group đích: Tàng Kinh Các -1003628743472, topic 846 (session thi công hiện tại — chuyển từ topic 348 ngày 10/07/2026)
