# Tàng Kinh Các — Superaudit & Fix Report

## User issues
1. Kim Cang Kinh card did not match the image → renamed to **Tần Số Nacha** and created `/menu#nacha` content.
2. Homepage cards/options looked clickable but had no destination → added anchors/links:
   - Tâm Kinh → `/menu#tam-kinh`
   - Tần Số Nacha → `/menu#nacha`
   - Đạo Đức Kinh → `/menu#dao-duc-kinh`
   - Dịch Kinh → `/menu#dich-kinh`
   - Tứ Đại Bảo Điện cards → `/menu` or `/floors` anchors.
3. Đêm Đọc text was unreadable on dark background → wrapped text in high-contrast dark panel and increased text contrast.
4. Some images were cropped too aggressively → mobile hero images now use `object-contain`, desktop uses `object-cover`; added `tkc-hero-art` object positioning.
5. Tam Đại Thệ Nguyện had no images → added visual cards with art images.
6. Ngũ Tầng was only an about-section concept → built new `/floors` page with 5 floor system, anchors, purpose, content and use-case for each floor.
7. Need to explain options → added practical explanations: what each floor/section is for.

## Root causes
- First art pass focused on visual placement, not interaction semantics.
- `serve -s dist` caused SPA fallback: `/menu`, `/story`, etc. served homepage. Fixed by restarting PM2 with `serve dist -l 4201`.
- Some mobile screenshots exposed object-cover crop issues; fixed with mobile contain mode.
- Dark prose section inherited low-contrast style; fixed with stronger panel.

## Added routes / anchors
- `/floors`
- `/floors#tang-mot`
- `/floors#tang-hai`
- `/floors#tang-ba`
- `/floors#tang-bon`
- `/floors#tang-nam`
- `/menu#nacha`
- `/menu#tam-kinh`
- `/menu#dao-duc-kinh`
- `/menu#dich-kinh`

## Verification
- Astro build: PASS, 7 pages.
- Routes verified HTTP 200:
  `/`, `/menu`, `/story`, `/about`, `/floors`, `/booking`, `/contact`.
- Screenshot audit files:
  - `screenshots/superaudit-mobile-sheet-v3.jpg`

## Still optional for Pass 2
- Add deeper subpages for every individual sutra/tome.
- Add animated floor-map SVG.
- Add modal/drawer descriptions for each card without leaving page.
- Manual crop per asset for all mobile breakpoints.
