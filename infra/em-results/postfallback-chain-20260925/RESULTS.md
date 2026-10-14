# Chuỗi POST fallback — 2026-09-25

Jar `0607485b6286ab24` (`EvoMaster/evomaster-PF-0607485b.jar`), cây làm việc `00f98d290947d998`
(`infra/evomaster-ext/wip/d1-lexicon-field-harvest-rolefield-postfallback-20260924.patch`; mô tả
`wip/post-fallback-20260924.md`). `chain.sh` chạy 00:25–08:12, cờ D1 tắt; lệnh EvoMaster giống từng dòng
`../rolefield-chain-20260924/chain.sh`.

## Kết quả

| Bước | Kết quả |
|---|---|
| Self-test mới `post-fallback.sh` (chạy trước chuỗi, `../postfallback-selftest-20260925-b/`) | 5/6; `airflow-post-considered` hỏng vì EvoMaster exit 1, sửa ở `../genesetguard-chain-20260925/` |
| Self-test cũ `rolefield-diagnostics.sh` | 12/12 |
| Self-test cũ `field-gate.sh` | 7/7 |
| Cổng hồi quy | 21 dòng, lệch 0 |
| Tier-1 bản lỗi, seeds 1–10 | 970 nổ 10/10 |
| Tier-2 bản lỗi, seeds 1–10 | 3/10: seed 1, 5, 10 |
| pyLoad bản lỗi, seeds 1–10 (3–10 chạy lại) | 10/10 |
| Tier-1 bản đã vá, 10 lần | 0 báo động giả |
| Tier-2 bản đã vá, 10 lần | 0 báo động giả |
| Vikunja seed 1 (`../vikunja-postfallback-20260925/logs/pf-seed1.log`) | 9 nguồn POST, 0 nạn nhân, 0 bộ ba |

## Sự cố

pyLoad bản lỗi (`pyload-vuln`, cổng 8090) ngừng trả lời lúc 07:17 trong seed 3: dòng log cuối của pyLoad là
07:17:33, EvoMaster ghi `Read timed out` đầu tiên lúc 07:18:34, 29 lần tới 07:45. Container vẫn `Up`, CPU 0.24%.
Dòng cuối trong log pyLoad trước khi treo: `API error in 'set_config_value'` và `'service_call'`; nguyên nhân chưa
kiểm. `docker restart` lúc 07:46 làm container thoát mã 70 (`pyLoad already running with pid 1`: file
`/tmp/pyLoad/pyload.pid` còn lại, chứa `1`). Ghi `999999` vào file đó bằng `docker cp` rồi `docker start`: lên lại,
`/thesis/reset` 200. Trong phút container tắt, seed 3 kết thúc và seeds 4–10 hỏng ngay: 8 dòng `ERR` trong
`runs.csv`, giữ nguyên.

Tám seed đó chạy lại bằng `rerun-t2b-3-10.sh`, 11:34–14:03, sau `../genesetguard-chain-20260925/`: cùng jar
(bản giữ `evomaster-PF-0607485b.jar`, sha kiểm trước khi chạy), cờ giống từng dòng hàm `t2b` của `chain.sh`,
`runs-t2b-rerun.csv`. Cả 8 lần: 970, `200/200/200`, 0 `Read timed out`.

Chuỗi seeds 11–20 trên jar `RF` (`../rf-seeds11-20-20260925/`) dừng tay lúc 23:53 ngày 09-24 để làm chuỗi này:
4 dòng Tier-1 bản lỗi seeds 11–14 (cả 4 nổ 970), seed 15 bị ngắt, không có dòng.

## Ghép từng seed

`runs-merged.csv` = `runs.csv` bỏ 8 dòng pyLoad `ERR`, thêm 8 dòng chạy lại. `pairing-vs-RF.txt`, so với
`../rolefield-chain-20260924/runs-merged.csv` (jar `7f9d977e`): 50 cặp, 970 mất 0, thêm 0, 970 trên bản đã vá 0.
Số bộ ba VOID trùng jar `RF` ở cả 50 dòng. Tập mã lỗi đổi ở 2 dòng, Tier-2 bản lỗi
seed 3 và 4; đó là hai dòng chuỗi `RF` mất mã 209 và 205 vì `MINIMIZATION` hết giờ, và tập mã mới trùng lần chạy
lại `../rolefield-chain-20260924/runs-t2vuln34-rerun.csv`.

Patch không đổi phát hiện 970 nào trên ba target. Trên Airflow nó mở nguồn POST: 14 nguồn, bộ ba đầu tiên được
thực hiện (`../genesetguard-chain-20260925/RESULTS.md`).

Sao lưu: `~/thesis-backups/thesis-full-20260925-0809.tar.gz` (trước lần chạy lại) và bản do `rerun-t2b-3-10.sh` tạo.
