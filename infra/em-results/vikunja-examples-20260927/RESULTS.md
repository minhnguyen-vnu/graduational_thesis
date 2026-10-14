# Vikunja, spec có example — 2026-09-27

Jar `129a7a56fce83df8` (`EvoMaster/evomaster-TT-129a7a56.jar`). `run.sh` chạy 16:47–18:21. Spec
`infra/vikunja-target/vikunja-2.2.2-docs-examples.json` (sha `ca71849841104ec8`, hai sai lệch đã khai ở
`infra/vikunja-target/README.md`). Hai nhánh: `auto` (builder tự chọn transition) và `declared`
(`--statefulAuthzTransition "POST /api/v1/projects/{projectID}/users/{userID} permission=0 projectID=4 userID=<victim>"`).
Seeds 1–2, `--maxTime 600s`, cờ D1 tắt, qua proxy.

## Kết quả

Bốn lượt, exit 0, **0 bộ ba**, 0 VOID, 0 970. Builder chọn `PUT /api/v1/projects` ở nhánh `auto`; 10 và 7 nguồn
được canh, toàn POST dưới `/user/...`, `/login`, `/notifications`, mọi nguồn `victims []`.

## Đính chính cột `hits_project4`

`runs.csv` ghi 27 và 40. Sai: điều kiện đếm là chuỗi `"/api/v1/projects/4` nên đếm lẫn project 404, 417, 437, 465…
Đếm lại theo đúng path `/api/v1/projects/4` hoặc `/api/v1/projects/4/...`:

| Lượt | Lời gọi trúng project 4 |
|---|---|
| seed 1 (cả hai nhánh) | `PUT /projects/4/tasks` 400 ×2; `POST /projects/4/users/u132Erv` 400 ×2 |
| seed 2 (cả hai nhánh) | `PUT /projects/4/tasks` 400 ×3, 401 ×2; `POST /projects/4/users/G3MiGv` 401 ×2 |

Không lời gọi nào vào project 4 trả 2xx, và không lời gọi nào của carol trả 403. `x-example` được dùng, nhưng thân
yêu cầu sai (400) hoặc thiếu token (401), nên không có nguồn nào mang cả 2xx lẫn 403.

## Kết luận

Thêm example cho id không đủ để EvoMaster dựng nguồn trên Vikunja trong 600 giây. Mặt âm tính của Vikunja vẫn
chưa cho TN nào bằng chạy máy; chỉ có kiểm tay 09-17.
