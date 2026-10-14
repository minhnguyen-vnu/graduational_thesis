# P1 trên reports-api — protocol

Viết 2026-10-11, trước lượt chạy. User quyết (2026-10-11): làm P1 trước, không đo lại đầy đủ, chỉ chạy reports-api;
đo đầy đủ để sau P2. Không qua cổng hồi quy, nên không trích con số nào từ thư mục này vào luận văn hay `docs/results.md`.

## Jar

Jar P1 (đặt tên và sha256 ghi ở `progress.log` lúc chạy): commit `8d6cf8431f` cộng bản vá
`infra/evomaster-ext/wip/candidate-iteration-20261011.patch` (duyệt nhiều op, trần 20, trần 5 cho op chưa chứng minh,
α, S1, S2, S3, log mới). Self-test: `infra/evomaster-ext/selftest/candidate-iteration.sh`.

## Đo gì

Bảng reports-api của §4 trên seeds 1–10, bốn arm như `af2-full-remeasure-20261003/`: vuln·không reset, fixed·không reset,
vuln·reset, fixed·reset. Cờ chép nguyên từ `af2_full_remeasure.sh` hàm `t1`; chỉ jar khác. So từng seed với hàng tương ứng
của `af2-full-remeasure-20261003/runs.csv`.

Thêm cột: `attempts` (số dòng VOID + UNCONFIRMED + Assembled), `cut5` (số dòng "not proven after"), `refused` (số dòng
"refused or rejected every attempt"), `revoked` (số dòng REVOKED), `proven` (số dòng "proven by an attempt").

## Luật dừng sớm

Đọc từng hàng trong `progress.log` khi nó rơi xuống.
- Arm vuln: 3 seed đầu đều `assembled=0` thì dừng, ghi lệch luật, tìm nguyên nhân trong log.
- Arm fixed: bất kỳ `det970=1` nào là FP; dừng và tìm nguyên nhân.
- `statuses=NA` hoặc `faults=ERR` hai hàng liền trên cùng arm thì dừng.

## Máy

Chạy dưới `caffeinate -dims`, nắp mở. `pmset -g log` có `Entering Sleep` sau giờ bắt đầu trong lúc một hàng đang chạy thì
mọi hàng nó chạm vào là hỏng.

## Thời gian

40 hàng × khoảng 5 phút ≈ 3,3 giờ.
