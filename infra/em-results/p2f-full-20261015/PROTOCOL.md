# P2f đo đầy đủ, 2026-10-15

Jar `EvoMaster/evomaster-P2f-64ee8ffc.jar` = P2e + bản vá `wip/setfield-leaf-activate-20261015.patch`
(`RestSecurityBuilder.kt:1360-1361`, neo `setField` vào lá `f.value`); harness dừng nếu sha256 khác `64ee8ffc78a9aad7`.

Mục đích: số §4 và phán quyết cổng hồi quy trên riêng P2f, để xét thay P2e làm jar trích số. Bản vá đổi construction
(serialize trường nullable present+value thay vì `null`), nên theo CLAUDE.md §5 phải đo lại các arm bị ảnh hưởng. 180
hàng, cùng arm, seed và cờ với `af2-full-remeasure-20261003/`: hàm `t1`, `t2`, `t2b` của `p2f_full.sh` trùng từng byte
`p2e_full.sh`, chỉ khác jar.

## Thứ tự

| Pha | Hàng | Nội dung |
|---|---|---|
| 1 | 21 | hàng cổng, thứ tự của `regression-check/regression_check.sh`; kỳ vọng đọc bằng `expected_of` chép từ script cổng, so `statuses` và det970 bằng đúng lệnh trích của cổng; ra `gate.csv` |
| 2 | 159 | các hàng còn lại, thứ tự AF2: reports, vampi, pyLoad; hàng đã chạy ở pha 1 bị bỏ qua |

Cờ của 21 hàng cổng trùng cờ hàng cùng (tier, arm, seed, reset) trong lượt đầy đủ, nên mỗi hàng chạy một lần và nằm
trong cả hai bộ. Thời gian: khoảng 20 h (AF2: 2026-10-03 09:57 tới 10-04 06:01).

## Luật dừng (viết trước lượt chạy)

Kiểm sau mỗi hàng (`check` trong `p2f_full.sh`); luật nổ thì harness dừng và ghi `STOPPED` vào `progress.log`.

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
   Script cổng đọc `core/target/evomaster.jar`; lượt này dùng bản sao cùng sha256 `64ee8ffc…`. P2f cũng đã qua cổng
   độc lập 21/21 ngày 2026-10-15 (`regression-check/archive-20261015-P2f-64ee8ffc/`).
2. Thứ tự hàng khác AF2: 21 hàng cổng chạy trước. Mỗi hàng reset target trước khi chạy.
3. Chạy qua đêm không người trông, theo yêu cầu user "đo lại luôn" (2026-10-15).
