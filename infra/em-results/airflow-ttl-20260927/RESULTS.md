# Airflow, hai nhánh `cache_ttl` — 2026-09-27

Jar `129a7a56fce83df8` (`EvoMaster/evomaster-TT-129a7a56.jar`). `run.sh` chạy 14:20–16:47. Hai nhánh khác nhau đúng
một biến là `fab.cache_ttl`: `airflow-vuln` cổng 8082 mặc định 30, `airflow-ttl0` cổng 8084 đặt
`AIRFLOW__FAB__CACHE_TTL=0`; cùng image `airflow-fab-vuln`, cùng lệnh khởi động, cùng tài khoản
(`reset-3users.sh` trước và sau mỗi lượt). `airflow config get-value fab cache_ttl` trả 30 và 0 (`progress.log`
14:20:54). Lệnh EvoMaster giống lượt Airflow của `selftest/transition-trim.sh`: spec
`airflow-merged-nodelete.json`, seed 1–3, `--maxTime 600s`, cờ D1 tắt, không khai transition, qua proxy ghi request.
`cache_ttl=0` là sai lệch cấu hình của ta, phải khai.

## Kết quả

| Seed | Nhánh | 970 | Bộ ba cặp đúng (nạn nhân `victim`, người thao tác `admin`) | Kết luận bộ ba |
|---|---|---|---|---|
| 1 | mặc định | 0 | `POST /api/v2/connections/defaults` 204/200/204 | UNCONFIRMED |
| 1 | `cache_ttl=0` | 0 | `POST /api/v2/connections/defaults` 204/200/**403** | hợp lệ, không 970 |
| 2 | mặc định | 0 | không dựng | — |
| 2 | `cache_ttl=0` | 0 | không dựng | — |
| 3 | mặc định | 0 | `PATCH /api/v2/dags` 200/200/200 | UNCONFIRMED |
| 3 | `cache_ttl=0` | 0 | `PATCH /api/v2/dags` 200/200/**403** | hợp lệ, không 970 |

Mọi bộ ba có nạn nhân `admin` (người thao tác `victim`, `viewer`) là VOID: transition 403, hai user này không có
quyền sửa user khác. `runs.csv`, `logs/*.log`, `traffic/*.jsonl`.

Khi tắt bộ đệm, hai bộ ba hợp lệ trên hai nguồn khác nhau đều có follow-up bằng token cũ bị chặn 403: Airflow
thu hồi quyền ngay với chứng chỉ cũ, và oracle không nâng 970. Đây là hai TN trên app bên thứ ba. Với bộ đệm mặc
định, cùng bộ ba cho follow-up 2xx và C4 loại; không nhánh nào có 970.

Giới hạn: Airflow là target phát triển từ 09-23; sáu sửa builder được viết khi chạy nó.

Sao lưu: `~/thesis-backups/thesis-full-20260927-1644.tar.gz`.
