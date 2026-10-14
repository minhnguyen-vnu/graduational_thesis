# Airflow, một lượt chẩn đoán — 2026-09-20 07:00

Mục đích: biết builder dừng ở bước nào trên Airflow, sau khi lượt 00:11 dựng được 0 bộ ba mà log không nói gì
(`../airflow-trial-20260920/`).

Đây không phải một nhánh đo. Hai biến đổi so với lượt 00:11:

- `-Dlogback.configurationFile=infra/em-config/logback-builder-debug.xml`: bản sao logback của EvoMaster, thêm
  hai logger `RestSecurityBuilder` và `RestSecurityOracle` ở mức `DEBUG`. Không sửa gì trong cây nguồn EvoMaster.
- `--ratePerMinute 60` thay cho 120, vì lượt trước có 42 lần đăng nhập hỏng do server không trả lời.

Còn lại giữ nguyên: jar `2c343573…`, spec ghép `airflow-merged-nodelete.json`, seed 1, `--maxTime 600s`,
`--extraPhaseBudgetPercentage 0.6`, cờ D1 tắt.
