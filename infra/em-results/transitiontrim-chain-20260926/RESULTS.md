# Chuỗi transition-trim lần 1 — 2026-09-26/27

Jar `0b6f3c31651da3fb` (`EvoMaster/evomaster-TT-0b6f3c31.jar`), cây `eb741b80`
(`wip/d1-lexicon-field-harvest-rolefield-postfallback-geneguard-transtrim-20260926.patch`). Build 23:47–23:48,
self-test 23:48–00:21. Dừng sau self-test: 5/6, không chạy gate và seeds.

| Kiểm | Kết quả |
|---|---|
| `gg-baseline-422` | PASS |
| `airflow-exit-0` | PASS |
| `airflow-fields-removed` | PASS |
| `airflow-sent-roles-only` | FAIL: 14 PATCH, 5 sai |
| `tier1-970`, `tier1-nothing-removed`, `tier1-fixed-no-970` | PASS |

## Vì sao `airflow-sent-roles-only` hỏng

Lỗi nằm ở kiểm. Lượt Airflow chạy 23:48–00:07. Kiểm lọc request theo giờ `HH:MM:SS` dạng chuỗi, lấy mọi request
có giờ `>= 00:06:28` (lúc builder chọn transition). Các request 23:48–23:58 của pha search thoả điều kiện chuỗi đó,
nên 5 PATCH ngẫu nhiên của search bị tính vào. Chín PATCH từ 00:06:30 đến 00:07:04, đều do builder gửi, có thân
đúng `{"roles":[]}` (`selftest-transtrim/airflow-seed1-traffic.jsonl`). Kiểm đã sửa: proxy ghi thêm `ts` (epoch),
kiểm quy giờ của log EvoMaster về epoch trước khi so.

## Lỗi thật mà lượt này lộ ra

Ba lần `Privilege-restore accepted for 'victim' by 'admin'` (vai trò `admin`, `administrator`, `owner`) gửi
`{"roles":[]}`, 200, thân response `"roles":[]`: khôi phục quyền đã gỡ mọi vai trò của `victim`. Bộ ba đúng cặp sau
đó (nạn nhân `victim`, người thao tác `admin`) có mã `403/200/403`: transition lần đầu 2xx, nhưng nguồn đã 403
vì `victim` không còn vai trò. Sửa ở `wip/transition-trim-20260926.md`, mục "Sửa lần 2"; chạy lại ở
`../transitiontrim-chain-20260927/`.
