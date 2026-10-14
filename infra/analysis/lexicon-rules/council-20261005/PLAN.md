# Kế hoạch sau vòng 2 (user giao 2026-10-05 ~22:15, chạy không người trông)

Yêu cầu của user: sau khi có quyết định, gán nhãn lại, rút danh sách, so với hardcode như vòng 2. Không sửa mã EvoMaster.
Làm mọi việc có thể; ưu tiên cái tốt nhất cho luận văn.

Trigger: `scratchpad/council/round2-at.sh` chạy nền (caffeinate), chờ tới 2026-10-06 01:55, chạy vòng 2 cho A và B,
thử lại mỗi 15 phút tới 06:00. Xong thì phiên chính được đánh thức.

Các bước, theo thứ tự; hết quota thì dừng ở bước đang làm và ghi chỗ dừng vào file này:

1. Đọc `A/round2.md`, `B/round2.md` (bản gốc ở scratchpad `council/A|B/`; chép vào đây).
2. Phân xử: `DECISION.md`. Mỗi bất đồng: hai phía, bằng chứng, lựa chọn, lý do; nêu lập luận chống lại lựa chọn.
3. Chốt `PROTOCOL-r3.md` trước khi gán dòng nào: định nghĩa nhãn mới, đơn vị đo, luật rút, chỉ số chính, kiểm định
   (bootstrap theo nhà cung cấp, so ghép đôi mức API), luật dừng sớm. Không ghi kết quả mong đợi.
4. Gán lại theo protocol: L1 phiên chính, L2 một agent `claude -p --safe-mode` cô lập, mù với L1. Phân xử ghi lý do.
5. Rút và đo; so với hardcode; viết `RESULTS-r3.md` trung lập, nêu rõ tập đo đã từng bị nhìn (nếu đúng vậy).
6. Báo user ngắn: file nào, mục nào.

## Trạng thái 2026-10-06

Xong bước 1–5. Kết quả: `../field-labelling-r3-20261006/RESULTS.md`.
