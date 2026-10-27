# 🍜 Website Nhà Hàng Chay Hạnh Duyên Om — Kế Hoạch 13 Beats

**Ngày tạo:** 06/04/2026
**Concept:** Nhà hàng thuần chay, phong cách hiện đại cao cấp
**Địa chỉ:** 23 Khuông Việt
**Tech:** Next.js + TailwindCSS + hosted on VPS

---

## SuperBuild RPI là gì?

**RPI = Research → Plan → Implement** — quy trình 3 bước:
- **Research:** Nghiên cứu khả thi, tham khảo đối thủ, chọn tech stack
- **Plan:** Lên kế hoạch chi tiết, chia giai đoạn
- **Implement:** Triển khai từng bước, audit mỗi bước

**Chống over-prompt:** Mỗi beat là 1 task độc lập, sub-agent riêng biệt, không nhồi nhiều việc vào 1 prompt. Beat xong → audit → pass → beat tiếp.

---

## 13 Beats — Khung Sườn

### Phase 1: RESEARCH (Beat 1-2)

| Beat | Tên | Mô tả | Output | Est. |
|------|-----|-------|--------|------|
| 1 | **Research & Benchmark** | Crawl 5-10 website nhà hàng chay cao cấp (VN + quốc tế). Phân tích: layout, UX, menu presentation, booking flow, storytelling. | `research-benchmark.md` | 30 min |
| 2 | **Tech Stack & Architecture** | Chọn framework (Next.js vs Astro), DB (booking), hosting config VPS. Sitemap + wireframe. | `architecture.md` + `sitemap.svg` | 20 min |

### Phase 2: DESIGN (Beat 3-5)

| Beat | Tên | Mô tả | Output | Est. |
|------|-----|-------|--------|------|
| 3 | **Brand Identity** | Bảng màu (palette zen/luxury chay), typography, logo tạm (từ group avatar). Design tokens. | `brand-guide.md` + `design-tokens.css` | 20 min |
| 4 | **UI/UX Wireframe** | Wireframe chi tiết 6 trang: Home, Menu, Story, Booking, About, Contact. Mobile-first. | `wireframes/` (6 files) | 30 min |
| 5 | **Design System** | Component library: buttons, cards, nav, footer, menu item card, booking form. TailwindCSS config. | `tailwind.config.js` + components spec | 25 min |

### Phase 3: BUILD (Beat 6-11)

| Beat | Tên | Mô tả | Output | Est. |
|------|-----|-------|--------|------|
| 6 | **Project Scaffold** | Init Next.js project, cài dependencies, folder structure, global styles, layout component. | `/website/` project | 15 min |
| 7 | **Homepage** | Hero section (ảnh chay cao cấp), tagline, featured menu, CTA booking, story teaser. Animations. | `page.tsx` (home) | 30 min |
| 8 | **Menu Page** | Menu categories (khai vị, chính, tráng miệng, thức uống). Mỗi món: ảnh, tên, story ngắn, giá. Filter/search. | `menu/page.tsx` | 35 min |
| 9 | **Story Page** | Câu chuyện nhà hàng, triết lý "Om", hành trình chay, đội ngũ. Storytelling scroll. | `story/page.tsx` | 25 min |
| 10 | **Booking Page** | Form đặt bàn: ngày, giờ, số khách, ghi chú. Validation. Confirm page. (Backend simple API route) | `booking/page.tsx` + API | 35 min |
| 11 | **About + Contact** | Bản đồ (23 Khuông Việt), giờ mở cửa, liên hệ, social links. Footer component. | `about/` + `contact/` | 20 min |

### Phase 4: POLISH & DEPLOY (Beat 12-13)

| Beat | Tên | Mô tả | Output | Est. |
|------|-----|-------|--------|------|
| 12 | **SEO + Performance** | Meta tags, OG images, sitemap.xml, robots.txt. Lighthouse audit ≥90. Image optimization. Responsive test. | Audit report | 25 min |
| 13 | **Deploy to VPS** | Build production, deploy lên VPS, config nginx/domain, SSL. Smoke test. | Live website | 20 min |

---

## Quy tắc chống Over-Prompt

1. **Mỗi beat = 1 sub-agent hoặc 1 task trực tiếp** — KHÔNG gộp
2. **Timeout:** Research 600s, Build 900s, Deploy 600s
3. **Audit sau mỗi beat:** Chạy verify, check output tồn tại + đúng format
4. **Gate cứng:** Pass → beat tiếp. Fail → redo beat đó.
5. **Checkpoint:** Sau mỗi beat ghi progress vào `HanhDuyenOm/progress.json`

---

## Thông tin đầu vào

- [x] Concept: Thuần chay, hiện đại, cao cấp
- [ ] Menu: Đang load (anh Nấng cung cấp sau)
- [ ] Logo: Tạm dùng logo group
- [x] Booking online: Có
- [x] Hosting: VPS em
- [ ] Hình ảnh tham khảo: Anh Nấng đã gửi (cần check)
- [ ] Domain: Chưa xác nhận

---

## Trạng thái

| Beat | Status | Note |
|------|--------|------|
| 1 | ⏳ QUEUED | Chờ confirm anh Nấng |
| 2-13 | ⏳ QUEUED | — |

**Next action:** Anh Nấng confirm kế hoạch → em khởi động Beat 1.
