# Dừng sau arm đầu — lệch luật

Batch dừng 2026-10-12 sau hàng 20 (reports vuln không reset, xong 17:49), theo quyết định của user. Không luật dừng
nào trong `PROTOCOL.md` nổ.

Lý do: arm này cho P2c 16/20, trượt seeds 10, 13, 16, 17. AF2 trượt seed 17 (19/20,
`af2-full-remeasure-20261003/runs.csv`). User chọn chạy interleave ba seed lệch trước khi đo tiếp:
AF2 9/9, P2c 0/9 (`p2c-interleave-seeds-20261012/`). Nguyên nhân tìm trong log debug
(`p2c-vs-af2-debug-20261012/`), sửa ở jar P2d (`p2d-night-20261012/`).

20 hàng trong `runs.csv` là của jar P2c (`b2ade764`), không dùng để trích số.
