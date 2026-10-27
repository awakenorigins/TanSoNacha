# 700 Phước Phiếu — QR Print Master

> **Trạng thái:** LOCKED / IMMUTABLE AFTER PRINT

Bộ 700 mã QR Phước Phiếu đã gửi in được lưu tại kho riêng tư:

- Repository: `NachaFromMars/700qrPhuocPhieu` (PRIVATE)
- Canonical release: `v1.0.1-exact-print-files`
- Canonical commit: `817b9020dbd406fa8c317c431f717587f72e0a5b`
- Release URL (cần quyền truy cập): <https://github.com/NachaFromMars/700qrPhuocPhieu/releases/tag/v1.0.1-exact-print-files>

## Phân phối

- 400 Trúc Duyên (`TD`, seq 0001–0400)
- 200 Kim Tâm (`KT`, seq 0001–0200)
- 100 Nguyên Niệm (`NN`, seq 0001–0100)

## Invariants

1. Không tái sinh, chỉnh sửa, resize hoặc thay thế PNG QR đã gửi in.
2. Không đổi short code và domain QR `https://qr.62.146.238.213.sslip.io`.
3. Chỉ được đổi destination/long URL trên Shlink khi website đổi đường dẫn.
4. Không tái sử dụng mã QR cho phiếu khác.
5. Trước mọi thay đổi, đối chiếu release chuẩn, `manifest.csv` và `SHA256SUMS.txt` trong kho private.

## Security boundary

Repo `TanSoNacha` là PUBLIC. Vì 700 QR chứa các mã kích hoạt chưa phát hành, ảnh QR và manifest đầy đủ **không được commit vào repo public này**. Tài liệu này chỉ đóng vai trò con trỏ khóa tới print master private.

## Superseded artifact

Release `v1.0.0-print-master` của kho QR đã bị superseded và không được dùng để đối chiếu file đã in. Chỉ `v1.0.1-exact-print-files` là chuẩn.
