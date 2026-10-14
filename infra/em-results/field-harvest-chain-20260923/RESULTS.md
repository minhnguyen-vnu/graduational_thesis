# Chuỗi field-gate + local-harvest — 2026-09-23

Jar `2ec4b9214b1b808f` (giữ ở `EvoMaster/evomaster-FH-2ec4b921.jar`), cây làm việc `7f85c6af1098be10`
(`infra/evomaster-ext/wip/d1-lexicon-field-harvest-20260923.patch`). Chạy 13:44–22:59, `chain.sh`, cờ D1 tắt.

## Kết quả

| Bước | Kết quả |
|---|---|
| Self-test `field-gate.sh` | 7/7 đạt |
| Self-test `local-harvest.sh` | 7/7 đạt |
| Cổng hồi quy | 21 dòng, lệch 0 |
| Tier-1 bản lỗi, seeds 1–10 | 970 nổ 10/10 |
| Tier-2 bản lỗi, seeds 1–10 | 3/10: seed 1, 5, 10 |
| pyLoad bản lỗi, seeds 1–10 | 10/10 |
| Tier-1 + Tier-2 bản đã vá, 20 lần | 0 báo động giả |

## Ghép từng seed với jar `L`

`pairing-vs-L.txt`, sinh bởi `../pair_runs.py ../lexicon-chain-20260921/runs.csv runs.csv`.
50 cặp, 0 phát hiện mất, 0 phát hiện thêm, 0 dòng đổi tập mã lỗi.

Hai patch không đổi phát hiện nào trên ba target. Phần chúng thêm vào được đo ở self-test:
`loop-advances` cho thấy vòng ứng viên đi qua ứng viên hạng 1 khi nó không thu được giá trị role.

Sao lưu: `~/thesis-backups/thesis-full-20260923-2257.tar.gz`.
