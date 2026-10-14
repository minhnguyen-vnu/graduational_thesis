# Chuỗi transition-trim lần 2 — 2026-09-27

Jar `3072fec2d13d59d5` (`EvoMaster/evomaster-TT-3072fec2.jar`), cây `d046b141`. Self-test 00:22–00:55: 6/7, dừng,
không chạy gate và seeds.

| Kiểm | Kết quả |
|---|---|
| `gg-baseline-422`, `airflow-exit-0`, `airflow-fields-removed` | PASS |
| `airflow-sent-roles-only` | PASS: 9 PATCH users sau 00:40:32, thân chỉ có `roles`, không query |
| `airflow-no-empty-restore` | FAIL: jar mới vẫn 3 dòng `Privilege-restore`, cả ba 200 với thân `{"roles":[]}` |
| `tier1-970`, `tier1-nothing-removed`, `tier1-fixed-no-970` | PASS |

Bộ ba đúng cặp vẫn `403/200/403`, như lần 1.

Vì sao bản sửa lần 2 không ăn: spec khai `roles` là `anyOf [array of Role, null]`
(`airflow-merged-nodelete.json`, `UserPatchBody`). EvoMaster bọc mảng trong một gene wrapper, rồi trong
`OptionalGene`. `setAllRoleFieldsTo` gặp gene wrapper tên `roles` trước, gene đó không phải `ArrayGene`, nên điều
kiện `g is ArrayGene<*>` không chặn, và việc gán lan xuống mảng. Sửa lần 3: bỏ qua mọi gene mà `flatView()` chứa
một `ArrayGene` có template `ObjectGene` (`wip/transition-trim-20260927b.patch`), chạy ở
`../transitiontrim-chain-20260927b/`.
