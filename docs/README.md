# Tàng Kinh Các 藏經閣

Thư viện kinh điển — clone & rebrand từ HanhDuyenOm.

## Live
- **Public:** https://tangkinhcac.62.146.238.213.sslip.io/
- **Local:** http://localhost:4201/

## Stack
- Astro 5 + Tailwind (static SSG)
- Served via `serve -s dist -l 4201` (pm2 process `tangkinhcac`)
- Caddy reverse proxy: `tangkinhcac.62.146.238.213.sslip.io → :4201`

## Pages
- `/` — Sảnh Chính (homepage + Tứ Đại Bảo Điện + Kinh Điển Tinh Tuyển)
- `/menu` — Kinh Tạng (4 mảng: Phật / Đạo / Nho / Bí Tịch, mỗi mảng 6 quyển)
- `/story` — Pháp Bảo (6 trấn các chi bảo + Tứ Pháp Đọc Kinh)
- `/about` — Bí Sử (khởi duyên + tam đại thệ nguyện + ngũ tầng lâu các)
- `/booking` — Mượn Kinh (lệ + form đăng ký)
- `/contact` — Liên Lạc Thủ Các

## Palette
- `parchment` `#F2E8D5` — giấy ngà
- `bronze` `#8B6F2E` — đồng cổ
- `sandalwood` `#6B4226` — gỗ đàn hương
- `ink` `#1F1A14` — mực đen
- `red-seal` `#8B1A1F` — chu sa
- `jade` `#4A6B5C` — ngọc xanh

## Rebuild
```bash
cd website
npm run build
pm2 restart tangkinhcac
```

## Notes
- Giữ nguyên `HanhDuyenOm/` site cũ — không ảnh hưởng.
- PM2 saved → tự khởi động khi VPS reboot.
- Cert Let's Encrypt tự gia hạn qua Caddy.

## Image assets added 2026-06-25
- `public/images/hero-tang-kinh-cac.jpg` — derived/cropped from Wikimedia Commons `Buddhism_library.jpg`, Nanputuo temple 南普陀寺藏经阁, author Gisling, open license with attribution.
- `public/images/manuscript-library-hero.jpg` — derived/cropped from Wikimedia Commons `Chiang-Mai_Thailand_Buddhist-Manuscript-Library-and-Museum-01.jpg`, Photo by CEphoto, Uwe Aranas, open license with attribution.
