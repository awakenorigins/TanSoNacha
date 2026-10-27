# TASK MUSIC LYRICS REPORT — Âm Kinh merge/build/seed

Thời điểm: 2026-07-10 12:xx Europe/Berlin

## Kết quả chính
- Merge: PASS — đã chạy `python3 scripts/merge-amkinh.py`.
- File sinh: `website/src/data/amkinh-gen.ts` — 32 album / 307 track.
- File vá: `website/src/data/amkinh.ts` — import `tieuTamGenAlbums`, giữ nguyên bài gốc `da-nam-mo` đứng đầu album `da-nacha`.
- Lyrics trong source gen: 266/307; thiếu 41 track, đúng cập nhật 11:40: chủ yếu nhạc không lời + vài clip không còn trên account.
- Build: PASS — `cd website && npm run build` hoàn tất 0 error.
- PM2: PASS — `pm2 restart tangkinhcac`, process online.
- Seed plays: PASS — `node --experimental-sqlite scripts/seed-plays.mjs` trả `{"seeded":307,"existed":0}`.

## Verify URL
- `http://localhost:4201/am-kinh` → 200
- `http://localhost:4201/am-kinh/tieu-tam` → 200
- `http://localhost:4201/am-kinh/tieu-tam/da-sam-hoi` → 200
- `http://localhost:4201/am-kinh/tieu-tam/da-tinh-do` → 200
- `http://localhost:4201/am-kinh/tieu-tam/da-sam-hoi/da-quay-dau-la-bo` → 200, HTML có lyrics/text “Dạ…”
- `http://localhost:4201/am-kinh/tieu-tam/da-sam-hoi/da-loi-xin-loi-me-cha` → 200
- `http://localhost:4201/am-kinh/tieu-tam/da-tinh-do/da-ben-sen-vang` → 200

## Verify stats
- `http://localhost:4213/stats?track=tieu-tam:da-sam-hoi:da-quay-dau-la-bo` → `{"ok":true,"track":"tieu-tam:da-sam-hoi:da-quay-dau-la-bo","stats":{"play":350,"kinh":0,"like":0,"sen":0,"sang":0,"tue":0,"cuoi":0,"khoc":0,"tym":0,"react":0,"comment":0}}`
- Kết luận: play > 0, cơ chế auto tăng có dữ liệu khởi tạo.

## Ghi chú
- Không đụng `backend/phuocphieu.mjs`.
- Không phá album/bài gốc `da-nam-mo`; bài gốc vẫn nằm trong `amkinh.ts` và merge chỉ append track gen sau nó.
- Có thử nhầm URL `/da-chua-kip-xin-loi` và `/da-nuoc-mat-tren-ao-cu` nhưng hai slug đó không tồn tại trong album `da-sam-hoi`; verify cuối dùng slug thật từ JSON gen.
