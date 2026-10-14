# Vikunja 2.2.2, lượt chẩn đoán đầu tiên — 2026-09-24

Jar `7f9d977e` (`evomaster-RF-7f9d977e.jar`), seed 1, `--maxTime 600s`, `--ratePerMinute 60`, cờ D1 tắt, log
builder mức debug. Container mới `vikunja-em` cổng 3457, CSDL trên tmpfs, dựng lại và gieo trước mỗi lượt bằng
`infra/vikunja-target/reset.sh`: alice tạo project 4, chia cho bob `permission=2`, carol `permission=0`; bob ghi
task 201, carol 403. Spec `infra/vikunja-target/vikunja-2.2.2-docs.json` (sha `7ceb3bc705a73be8`, lấy từ
`/api/v1/docs.json`). Tài khoản `infra/em-config/vikunja-auth.yaml`. Container `vikunja-vuln` cổng 3456 không bị đụng.

| Lượt | Khác biệt | Kết quả |
|---|---|---|
| `rf-seed1` 22:41 | giới hạn mặc định của Vikunja | exit 1 sau 9 giây: đăng nhập nhận 429, nhánh chờ 429 của EvoMaster gọi `List.removeLast()` (`AbstractRestFitness.kt:818`, commit upstream `181ad40bf8e`), hàm chỉ có từ JDK 21, chạy trên JDK 17 thì `NoSuchMethodError` |
| `rf-seed1-b` 22:44 | `VIKUNJA_RATELIMIT_NOAUTHLIMIT` và `_LIMIT` = 100000 | chọn `PUT /api/v1/projects`; 1 nguồn được canh, 0 nạn nhân, 0 bộ ba |
| `rf-declared-seed1` 23:20 | thêm `--statefulAuthzTransition "POST /api/v1/projects/{projectID}/users/{userID} permission=0 projectID=4"` (`run-declared.sh`) | 1 nguồn được canh, 0 nạn nhân, 0 bộ ba |

Cả hai lượt chạy đủ: mã lỗi `[100, 101]`, 0 exception, 0 lần đăng nhập hỏng.

## Builder chọn gì

`rf-seed1-b`: `transition candidate PUT:/api/v1/projects score 0.5455 userParam true reducedRoleValues 4`,
giá trị `[0, 1, 2, 42]` qua trường `max_permission`. Trên Vikunja PUT là tạo mới, POST là cập nhật:
`PUT /projects` tạo project, không hạ quyền ai. Transition thật, `POST /projects/{projectID}/users/{userID}`,
có cùng điểm 0.5455 và đứng hạng 8 theo tính tay trên spec (tie-break PUT trước POST); vòng lặp dừng ở ứng viên
đầu tiên gặt được giá trị, không thử tiếp khi ứng viên đó không tạo được bộ ba.

## Nguồn

Cả hai lượt: `guarded source candidates: 1 [PUT:/api/v1/teams/{id}/members]`, `victims []`,
`sources exhausted after 0 triple attempts`. Lượt khai transition dừng ở cùng chỗ: chưa tới bước gọi transition.
Giống Airflow: nguồn POST không được xét vì danh sách PUT/PATCH không rỗng. Trên Vikunja mọi lệnh cập nhật là POST.

Trong bộ test đã rút gọn của `rf-seed1-b`, lệnh ghi có 2xx: `POST /notifications`, `POST /tasks/{projecttask}/read`,
`POST /user/logout`, `POST /user/settings/avatar`, `POST /user/settings/webhooks/{id}`,
`PUT /user/settings/token/caldav`. Không lệnh nào trong số đó có 403 trong bộ test. `POST /tasks/{id}` chỉ có
400: fuzzer sinh id ngẫu nhiên, còn task tồn tại có id 1–3. Bộ test rút gọn không phải toàn bộ archive, nên chưa
biết hướng 2 có tìm được nguồn POST có cả 2xx lẫn 403 trên Vikunja hay không.

## Trở ngại đã biết từ kiểm tay 09-17

`userID` khai `integer` trong spec nhưng thực thi đòi username (`analysis/cve-survey/vikunja-handcheck-20260917.md` §3).
Nhánh hạ quyền người dùng trên Vikunja là target âm tính: token cũ bị chặn 403 sau khi hạ quyền.
