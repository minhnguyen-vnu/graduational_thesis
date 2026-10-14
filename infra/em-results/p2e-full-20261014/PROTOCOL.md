# P2e đo đầy đủ, 2026-10-14

Chưa chạy. User chọn tạm dùng bộ gộp `p2e-continue-20261013/` (2026-10-14); lượt này để sau.

Jar `EvoMaster/evomaster-P2e-6ae8277b.jar` = commit `a544c996ac`; harness dừng nếu sha256 khác `6ae8277bef229574`.

Mục đích: số §4 và phán quyết cổng hồi quy trên một jar. 180 hàng, cùng arm, seed và cờ với
`af2-full-remeasure-20261003/`: hàm `t1`, `t2`, `t2b` của `p2e_full.sh` trùng từng byte `af2_full_remeasure.sh`.

## Thứ tự

| Pha | Hàng | Nội dung |
|---|---|---|
| 1 | 21 | hàng cổng, thứ tự của `regression-check/regression_check.sh`; kỳ vọng đọc bằng `expected_of` chép từ script cổng, so `statuses` và det970 bằng đúng lệnh trích của cổng; ra `gate.csv` |
| 2 | 159 | các hàng còn lại, thứ tự AF2: reports, vampi, pyLoad; hàng đã chạy ở pha 1 bị bỏ qua |

Cờ của 21 hàng cổng trùng cờ hàng cùng (tier, arm, seed, reset) trong lượt đầy đủ, nên mỗi hàng chạy một lần và nằm
trong cả hai bộ. Thời gian: khoảng 20 h (AF2: 2026-10-03 09:57 tới 10-04 06:01).

## Luật dừng (viết trước lượt chạy)

Kiểm sau mỗi hàng; luật nổ thì harness dừng và ghi `STOPPED` vào `progress.log`.

- Hàng cổng `MISMATCH`. Trước khi chạy tiếp: chạy lại hàng đó xen kẽ với AF2 (`reproducibility/interleave.sh`).
- Hàng fixed có det970 = 1.
- 2 hàng liên tiếp det970 = ERR.
- Arm vuln: 3 hàng đầu của arm theo thứ tự chạy đều assembled = 0.
- Có `Entering Sleep` mới trong `pmset -g log`.

## Sau batch

Harness tự chạy:
- `compare.py` (`compare.out`): từng arm so với AF2, seed lệch hai chiều, McNemar chính xác hai phía, tổng assembled, FP, 970 không có bộ ba, hàng ERR, số hàng cổng MATCH.
- `audit970_seeded.py` trên các lượt reports và vampi (`audit970.out`).

Chờ user: replay các test 970, soát tay pyLoad, snapshot, cập nhật `docs/results.md` và `CLAUDE.md` §4/§5.

## Lệch luật đã khai

1. Cổng không chạy bằng `regression_check.sh`. 21 hàng cổng nằm trong lượt đầy đủ; phần so sánh chép từ script cổng.
   Script cổng đọc `core/target/evomaster.jar`; lượt này dùng bản sao cùng sha256 `6ae8277b…`.
2. Thứ tự hàng khác AF2: 21 hàng cổng chạy trước. Mỗi hàng reset target trước khi chạy.
3. Chạy qua đêm không người trông (CLAUDE §6), nếu user đồng ý.
