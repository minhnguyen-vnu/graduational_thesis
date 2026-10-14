# Airflow, hai lượt chẩn đoán — 2026-09-23/24

Không phải nhánh đo. Mỗi lượt đổi đúng jar; còn lại giống lượt debug 09-20 (`../airflow-debug-20260920/`):
spec ghép `airflow-merged-nodelete.json`, seed 1, `--maxTime 600s`, `--ratePerMinute 60`, cờ D1 tắt,
log `RestSecurityBuilder` ở mức `DEBUG`. Lệnh: `run.sh`. Airflow bản dính (provider FAB 3.8.1), cổng 8082.

| Lượt | Jar | Transition chọn | Ứng viên xét | Bộ ba | Đăng nhập hỏng |
|---|---|---|---|---|---|
| 09-20 06:53 | `2c343573`, 8 từ cứng | không có | 0 | 0 | — |
| 23:00 | `2ec4b921`, lexicon + field-gate + local-harvest | `PATCH /auth/fab/v1/roles/{name}` | 1 | 0 | 22 |
| 00:02 | `7f9d977e`, thêm patch role-field + log | `PATCH /auth/fab/v1/users/{username}` | 2 | 0 | 22 |

## Lượt 00:02, log builder

```
candidate PATCH:/auth/fab/v1/roles/{name} score 0.3 userParam true reducedRoleValues 0
candidate PATCH:/auth/fab/v1/users/{username} score 0.3 userParam true reducedRoleValues 5
chosen: PATCH:/auth/fab/v1/users/{username}
reduced role values: [user, viewer, guest, member, basic]
guarded source candidates: 1 [PATCH:/auth/fab/v1/roles/{name}]
source PATCH:/auth/fab/v1/roles/{name} victims []
sources exhausted after 0 triple attempts
```

- Lượt 23:00 chọn `PATCH /roles/{name}`: thân `RoleBody{name, actions}` không có trường role, giá trị duy nhất
  thu được là content type. Patch role-field loại nó (0 giá trị) và vòng ứng viên đi tới endpoint hạ quyền thật.
- Builder dừng ở bước chọn nguồn. Nguồn phải là PUT/PATCH có một 403 trong archive; chỉ khi danh sách đó rỗng
  mới xét POST (`RestSecurityBuilder.kt`, `guardedCandidatesFor(...).ifEmpty`). `PATCH /roles/{name}` lọt vào
  danh sách nhưng không tài khoản nào từng nhận 2xx trên nó, nên 0 lần thử.
- `POST /api/v2/variables`, thao tác ghi dùng trong kiểm tay, không được xét: danh sách PUT/PATCH không rỗng, và
  cả `admin` lẫn `victim` (Op) đều ghi được nên không có 403 nào trên nó.

## Chưa làm, cần duyệt

1. Tài khoản thứ ba vai trò Viewer trong `airflow-auth.yaml` và `reset.sh`, để archive có 403 trên thao tác ghi.
   Không sửa mã.
2. Xét POST khi không nguồn PUT/PATCH nào có nạn nhân, thay cho khi danh sách PUT/PATCH rỗng. Sửa mã, đổi cách
   dựng trên ba target.
3. Giá trị role: tên role FAB là `Viewer`, danh sách chữ thường `stringRoleCandidates` không có nó; trường
   `roles` là mảng object `{name}`, chưa biết `setRoleFieldToReduced` đặt được vào đó không. Lấy tên role từ
   response (`GET /auth/fab/v1/roles`) là nguồn giá trị đã ghi trong kế hoạch.

Đường A của Airflow không phải lỗi 970 (cache 30 s, token mới cũng ghi được: `../../analysis/cve-survey/airflow-handcheck-20260920.md` §3).
Khi dựng được bộ ba, kết quả đúng là D1 không nâng 970: một kết quả âm đúng trên mã bên thứ ba.
