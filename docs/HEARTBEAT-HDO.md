# HEARTBEAT — Hạnh Duyên Om Website Build

## Task
Tiếp tục build website Hạnh Duyên Om từ Beat 5 đến Beat 13.
Kiểm tra progress.json → resume beat đang running/queued.

## Check
1. Đọc HanhDuyenOm/progress.json
2. Nếu có beat running mà agent không active → resume
3. Nếu beat done → chuyển sang beat tiếp
4. Khi tất cả 13 beat done → ZIP final + gửi group -1003628743472 + xóa cron

## Group
-1003628743472 (Om Hạnh Duyên Om, topic 1)

## Rules
- Không gửi tin cập nhật tiến trình — chỉ gửi file cuối
- Mỗi beat: polish code → build test → verify → next
- Beat 8: Telegram Bot integration
- Beat 13: Deploy VPS
