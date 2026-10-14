# Target Vikunja 2.2.2

Kiểm tay: `../analysis/cve-survey/vikunja-handcheck-20260917.md`. Hạ quyền người dùng trên project (§1) là mặt
âm tính: token cũ bị chặn 403 sau khi hạ.

`reset.sh [cổng]` dựng lại container `vikunja-em` (CSDL tmpfs, giới hạn tốc độ nâng lên 100000) và gieo: alice chủ
project 4, bob `permission=2`, carol `permission=0`.

## Hai file spec

- `vikunja-2.2.2-docs.json`: lấy từ `GET /api/v1/docs.json`, swagger 2.0, sha `7ceb3bc705a73be8`.
- `vikunja-2.2.2-docs-examples.json` (2026-09-27, sha `ca71849841104ec8`): bản của ta, hai sai lệch phải khai.
  1. `x-example: 4` trên tham số path `id` của `PUT /projects/{id}/tasks` và `POST /projects/{id}`, và `projectID`
     của `POST /projects/{projectID}/users/{userID}`. Lý do: không có nó, fuzzer không gọi trúng project 4, nên
     không nguồn nào có nạn nhân (`../em-results/vikunja-postfallback-20260925/RESULTS.md`).
  2. `userID` của `POST` và `DELETE /projects/{projectID}/users/{userID}` đổi `integer` thành `string`. Lý do:
     thực thi đòi username, số cho 404 (kiểm tay 09-17 §3). Đây là lỗi spec của vendor.
