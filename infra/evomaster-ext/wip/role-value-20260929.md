# Giá trị vai trò khác vai trò hiện tại, giữ tên nạn nhân — 2026-09-29

Cây trước: `cc178c8d` (jar `VI-d2325da7`), lưu ở `pre-rolevalue-20260929.patch`. Self-test: `selftest/role-value.sh`.
Nguồn lỗi: `em-results/aicc-heldout-20260929b/RESULTS.md`.

## Lỗi

Callcenter, seed 1. Transition `PUT /api/v1/users/{userId}`, giá trị `[ADMIN, AGENT, EVOMASTER, SUPERVISOR, ACTIVE,
SUSPENDED]`. Nạn nhân `admin` có vai trò `ADMIN`. Body gửi đi `{"username":"T9","role":"ADMIN","status":"ACTIVE"}`:
1. `role` là giá trị đầu, trùng vai trò hiện tại. Vòng giá trị trong `buildStatefulAuthzTriple` dừng sau lần thử
   đầu đã chạy, nên không thử `AGENT`.
2. `username` bắt buộc, nhận chuỗi ngẫu nhiên `T9`. Tài khoản bị đổi tên.

## Sửa

| Hàm | Làm gì |
|---|---|
| `victimObjects` | Gom các object JSON trong body 2xx của archive có trường tên (`login`, `username`, `userName`, `user_name`, `name`) bằng tên nạn nhân. Tách ra từ `victimIdentifiers`, kết quả của hàm đó không đổi. |
| `victimRoleValues` | Từ các object đó, lấy giá trị các trường có tên khớp `roleFieldSignals`. |
| `buildStatefulAuthzTriple` | Khi không có transition khai báo, bỏ khỏi danh sách giá trị những giá trị bằng vai trò hiện tại (không phân biệt hoa thường). Cả vòng khôi phục dùng danh sách đã lọc. |
| `setUserNameFieldsToVictim` | Sau `keepOnlyTargetFields`, gán tên nạn nhân vào trường body `login`, `username`, `user_name` còn đang gửi. Gọi ở transition và ở `restorePrivilege`. |

Chạy tay trên dữ liệu lượt 2: `GET /api/v1/users` trả `{"role":"ADMIN",…,"username":"admin"}`, nên
`victimRoleValues("admin") = [ADMIN]`, danh sách còn `[AGENT, EVOMASTER, SUPERVISOR, ACTIVE, SUSPENDED]`, body
thành `{"username":"admin","role":"AGENT","status":…}`.

## Giới hạn

- Không thấy body nào nêu nạn nhân thì danh sách không đổi.
- `status` bắt buộc vẫn nhận giá trị ngẫu nhiên từ enum.
- Tên nạn nhân là tên tài khoản trong file auth, như `setUserTargetToVictim` đã giả định.

## Jar và self-test

Cây `ef3690d3` (`rolevalue-20260929.patch`), jar `EvoMaster/evomaster-RV-44254256.jar`, build 19:12.

Self-test lần 1 (`em-results/rolevalue-selftest-20260929-191319/`): 8/9. `aicc-transition-role-not-current` trượt
vì 1/8 PUT gửi `role=ADMIN` cho `victim` lúc 19:21:25. Log cùng lượt: `Privilege-restore accepted for 'victim' by
'admin' with role 'ADMIN'`. Đó là lệnh khôi phục, cố ý gửi vai trò cao; check viết sai kỳ vọng. Sửa check: bỏ các
PUT khớp một lệnh khôi phục đã chấp nhận (tên, vai trò) trong log. Chạy lại toàn bộ self-test sau khi sửa.
Cùng lượt: bộ ba `admin`/`victim` trên `PUT /api/v1/users/{userId}`, mã `200/200/403`; ba tài khoản còn đăng nhập
được sau lượt chạy.
Rollback diễn tập 19:34: checkout hai file, `git diff HEAD` rỗng, `git apply` lại, diff trùng byte với patch, sha `ef3690d3`.
Self-test lần 2 (`em-results/rolevalue-selftest-20260929-193409/`): 9/9. Bộ ba `admin`/`victim` lại `200/200/403`.
Sửa 09-30: script có 9 check; bản trước ghi nhầm 10/11 và 11/11.
