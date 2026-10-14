# Airflow, ba tài khoản — 2026-09-24 15:43

Một biến so với lượt 00:02 của `../airflow-lexicon-20260923/`: thêm tài khoản `viewer` vai trò Viewer
(`infra/em-config/airflow-auth-3users.yaml`, `infra/airflow-target/reset-3users.sh`). Diff `run.sh`: chỉ thư mục,
script reset và file cấu hình. Jar `7f9d977e`, seed 1, `--maxTime 600s`, `--ratePerMinute 60`, cờ D1 tắt.

Kiểm trước khi chạy: `viewer` `POST /api/v2/variables` 403, `victim` 201.

Sửa 2026-09-25 00:00: dòng reset trong `run.sh` không chạy. `reset-3users.sh` thiếu quyền thực thi, lỗi đi ra
stderr và không vào `progress.log` (không có dòng `victim roles`). Lượt 15:43 chạy trên hai user `victim` (Op) và
`viewer` (Viewer) đã có trước lượt chạy (dòng kiểm ở trên), cộng thêm mọi trạng thái Airflow còn lại từ
các lượt trước.

| | Lượt 00:02, 2 tài khoản | Lượt 15:43, 3 tài khoản |
|---|---|---|
| Transition | `PATCH /auth/fab/v1/users/{username}` | như cũ |
| Nguồn PUT/PATCH được canh | 1 | 18 |
| Nguồn có nạn nhân 2xx | 0 | 0 |
| Bộ ba | 0 | 0 |
| Đăng nhập hỏng | 22 | 22 |

Log: `sources exhausted after 0 triple attempts`; cả 18 nguồn PUT/PATCH in `victims []`.

Trong bộ test sinh ra (bộ đã rút gọn, không phải toàn bộ archive), lệnh ghi 2xx chỉ có `PATCH /api/v2/connections`
(200) và `POST /api/v2/connections/defaults` (204). `POST /api/v2/connections/defaults` cũng có 403. Nó là một
nguồn POST hợp lệ, nhưng không được xét vì danh sách PUT/PATCH không rỗng (`RestSecurityBuilder.kt:543`).
PUT/PATCH trên Airflow cần tài nguyên có sẵn (DAG, pool, variable theo khoá); instance không nạp DAG mẫu
(`LOAD_EXAMPLES=False`), nên fuzzer không có 2xx trên các nguồn đó.

Tài khoản thứ ba gỡ được việc thiếu 403. Chỗ kẹt còn lại là luật chỉ xét POST khi danh sách PUT/PATCH rỗng.

## Kiểm hai trở ngại còn lại, 2026-09-24 22:45 (curl và đọc code, không chạy EvoMaster)

Curl trên user thử `probe` (tạo mới vai trò Op, xoá sau khi kiểm), `PATCH /auth/fab/v1/users/probe`:

| Body | Mã | Vai trò sau đó |
|---|---|---|
| `{"roles":[{"name":"viewer"}]}` | 400 `Unknown roles: 'viewer'` | `['Op']` |
| `{"roles":[{"name":"Viewer"}]}` | 200 | `['Viewer']` |
| `{"roles":[]}` | 200 | `[]` |
| `{"roles":[]}` kèm username, email, tên, không `update_mask` | 200 | `[]` |

Đọc code (jar `RF`, chưa kiểm lúc chạy): `setRoleFieldToReduced` (`RestSecurityBuilder.kt:993`) gọi
`setFromStringValue` trên gene đầu tiên có tên chứa `role`, tức gene `roles`. `ArrayGene.unsafeSetFromStringValue`
(`ArrayGene.kt:298`) xoá hết phần tử, gặp template `ObjectGene` thì chỉ log warn
`ObjectGene type is not supported in ArrayGene yet.` rồi trả `true`. Nếu đúng như đọc, transition gửi
`roles: []`, Airflow nhận 200 và gỡ mọi vai trò: vẫn là một lần hạ quyền, và giá trị viết thường không còn quan
trọng. `roles` khai `anyOf [array, null]`, nên còn một lớp `ChoiceGene` (`ChoiceGene.kt:252`, thử lần lượt từng
lựa chọn); lớp này chưa được đọc hết. Rủi ro khác: body còn trường `username` do fuzzer sinh, không có
`update_mask` thì PATCH có thể đổi tên tài khoản nạn nhân.
