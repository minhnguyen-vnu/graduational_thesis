# pyLoad seeds 6–20, jar AF2, không reset — protocol 2026-10-04

Mục đích: đưa pyLoad lên 20 seed cho nhánh **không reset** (con số chính), ngang Tier-1/Tier-2. Hiện pyLoad mới có
seed 1–5 (`af2-full-remeasure-20261003/`). Nhánh có reset giữ nguyên 5 seed, không chạy đêm nay.

## Đo gì

- Jar `AF2` = `evomaster-AF2-6b5606d4.jar`, giống `af2-full-remeasure-20261003/`.
- Hai arm, mỗi arm seed 6–20 (15 lượt): `vuln` `:8090`, `fixed` `:8091`. Tổng 30 lượt.
- Lệnh trùng khít `t2b()` của `af2-full-remeasure-20261003/af2_full_remeasure.sh`, bỏ cờ
  `--statefulAuthzResetEndpoint` (không reset), `--maxTime 10m --ratePerMinute 200`,
  `--endpointExclude /api/kill,/api/restart`, spec `openapi-merged.json`.
- Mỗi lượt reset môi trường trước bằng `POST /thesis/reset` (chuẩn bị trạng thái seeded, không phải can thiệp logic).
- Ghi mỗi lượt một hàng vào `runs.csv`:
  `tier,arm,seed,reset,det970,assembled,void_count,resets,restores_ok,restores_no,statuses,faults`.

Không ghi kết quả mong đợi vào đây. Số chốt chỉ lấy sau khi chạy xong và gộp với seed 1–5.

## Luật dừng sớm (viết trước khi chạy)

- Chạy `vuln` seed 6,7,8 trước. Nếu cả ba có `assembled=0` (builder không dựng được bộ ba nào) → dừng batch, ghi
  một dòng lệch luật vào `progress.log`, tìm nguyên nhân (target/proxy/pyLoad chết) trước khi chạy tiếp. Đây là dừng
  vì nghi môi trường hỏng, không phải dừng theo kết quả 970.
- `fixed` arm: `det970=1` ở một seed là một phát hiện FP cần soát, không phải điều kiện dừng; giữ hàng và chạy tiếp.
- Máy ngủ: harness đếm `Entering Sleep` trong `pmset -g log`; nếu tăng trong lúc batch chạy → dừng, các hàng chạm
  giấc ngủ nghi ngờ.
- Một lượt `ERR` (report.json thiếu): giữ hàng ERR, chạy lại đúng lượt đó sau khi dựng lại target.

## Sau batch

- Audit test sinh ra, soát tính toàn vẹn (970 phải có bộ ba `assembled`), replay từ trạng thái sạch.
- Snapshot sang `~/thesis-backups/`.
- Gộp seed 1–5 (`af2-full-remeasure-20261003/`) + seed 6–20 (ở đây) → cập nhật `docs/results.md` và `CLAUDE.md` §4,
  nêu jar `AF2`.
