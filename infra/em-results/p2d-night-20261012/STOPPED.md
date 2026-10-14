# Dừng remeasure giữa chừng — lệch luật

Remeasure dừng 2026-10-13 11:27:30 sau 114 hàng, theo quyết định của user (phương án 1). Không luật dừng nào trong
`PROTOCOL.md` nổ. Hàng vampi fixed không reset seed 15 bị giết giữa lượt, không có hàng.

Hàng đã có: reports 80/80, vampi vuln không reset 20/20, vampi fixed không reset seeds 1–14.

Lý do: vampi vuln không reset seed 11 nổ trên AF2, không nổ trên P2d. Theo log
(`remeasure/logs/t2-ours-vuln-seed11-r0.log`, `af2-full-remeasure-20261003/logs/t2-ours-vuln-seed11-r0.log`):
- danh sách giá trị nâng quyền của P2d cho trường enum `role` là `admin`, `EVOMASTER`, …;
  `EVOMASTER` là giá trị EvoMaster tự chèn vào enum;
- vòng restore thử hết giá trị của một operator rồi mới sang operator kế, nên 3 lượt thành admin/admin 404,
  admin/`EVOMASTER` 400, name1/admin 404, không tới name2;
- AF2 chỉ thử `admin` cho mỗi operator, tới name2 → 200, dựng bộ ba, nổ.

Cùng mẫu ở vampi fixed không reset: seed 3 và 11 restore hết 3 lượt (AF2 nâng được name2 ở lượt 3); seed 11
AF2 dựng một bộ ba 200/200/403, P2d không dựng. Seeds 5 và 9 tốn thêm một lượt `EVOMASTER`.

Jar sửa lỗi này sẽ thay P2d, nên 114 hàng trong `remeasure/runs.csv` không dùng để trích số. Bước tiếp:
chạy P2d trên các hàng AF2 nổ còn lại để tìm lỗi khác (`p2d-af2fired-probe-20261013/`).
