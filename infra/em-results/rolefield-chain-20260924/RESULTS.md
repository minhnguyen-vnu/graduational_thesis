# Chuỗi role-field + log chẩn đoán — 2026-09-24

Jar `7f9d977e4849080a` (giữ ở `EvoMaster/evomaster-RF-7f9d977e.jar`), cây làm việc `d5a9b00de2af8811`
(`infra/evomaster-ext/wip/d1-lexicon-field-harvest-rolefield-20260923.patch`; phần tăng dần và mô tả:
`wip/rolefield-diagnostics-20260923.{patch,md}`). `chain.sh` chạy 00:08–08:32, cờ D1 tắt, cùng lệnh với
`../field-harvest-chain-20260923/chain.sh`.

## Kết quả

| Bước | Kết quả |
|---|---|
| Self-test mới `rolefield-diagnostics.sh` (chạy trước chuỗi) | 12/12 đạt, `selftest-rolefield.txt` |
| Self-test cũ `field-gate.sh` | 7/7 đạt |
| Self-test cũ `local-harvest.sh` | 6/7 đạt; `content-type-is-a-value` hỏng, đúng lỗi patch sửa |
| Cổng hồi quy | 21 dòng, lệch 0 |
| Tier-1 bản lỗi, seeds 1–10 | 970 nổ 10/10 |
| Tier-2 bản lỗi, seeds 1–10 | 3/10: seed 1, 5, 10 |
| pyLoad bản lỗi, seeds 1–10 | 10/10 |
| Tier-1 bản đã vá, 10 lần | 0 báo động giả |
| Tier-2 bản đã vá, 10 lần (chạy lại) | 0 báo động giả |

## Sự cố

- Container `vampi-seeded-fixed` bị OOM lúc 03:53:53 (`OOMKilled=true`, exit 247, đã chạy 6 tuần). Mười lần
  Tier-2 bản đã vá trong chuỗi không nạp được spec: 10 dòng `ERR` trong `runs.csv`, giữ nguyên. Container được
  khởi động lại lúc 05:24 và mười lần đó chạy lại bằng `rerun-t2-fixed.sh`, 08:33–09:27, cùng jar và cùng lệnh:
  `runs-t2fixed-rerun.csv`.
- Tier-2 bản lỗi seed 3 (xong 03:53:34) và seed 4 là hai lần duy nhất của cả hai chuỗi có pha `MINIMIZATION`
  hết giờ; hai dòng đó mất mã 209 và 205. Chạy lại bằng `rerun-t2-vuln-34.sh` lúc 09:29: không hết giờ, tập mã
  trùng jar trước (`100|101|209`, `100|101|205|209`), 970 vẫn 0: `runs-t2vuln34-rerun.csv`.
  `runs-merged.csv` dùng hai dòng của chuỗi, không dùng lần chạy lại này.

## Ghép từng seed

`runs-merged.csv` = `runs.csv` bỏ 10 dòng Tier-2 bản đã vá, thêm 10 dòng chạy lại.

| So với | Cặp | 970 mất | 970 thêm | 970 trên bản đã vá | Đổi tập mã lỗi |
|---|---|---|---|---|---|
| jar `2ec4b921` (`pairing-vs-FH.txt`) | 50 | 0 | 0 | 0 | 2, seed 3 và 4 Tier-2 bản lỗi, ở trên |
| jar `L` (`pairing-vs-L.txt`) | 50 | 0 | 0 | 0 | 2, cùng hai dòng |

Patch không đổi phát hiện 970 nào trên ba target. Phần nó thêm được đo ở self-test và trên Airflow
(`../airflow-lexicon-20260923/RESULTS.md`): builder chọn `PATCH /auth/fab/v1/users/{username}` mà không cần khai.

Sao lưu: `~/thesis-backups/thesis-full-20260924-0830.tar.gz` (trước hai lượt chạy lại) và bản sau RESULTS này.
