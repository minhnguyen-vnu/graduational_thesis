# Vikunja 2.2.2 trên jar `PF` và `GG` — 2026-09-25

Lệnh `run.sh`: seed 1, `--maxTime 600s`, `--ratePerMinute 60`, cờ D1 tắt, log builder mức debug. Container
`vikunja-em` cổng 3457, dựng lại và gieo trước mỗi lượt bằng `infra/vikunja-target/reset.sh` (alice chủ project
4, bob `permission=2`, carol `permission=0`; bob ghi task 201, carol 403; `progress.log`).

| Lượt | Jar | Exit | Transition chọn | Nguồn được canh | Nạn nhân | Bộ ba |
|---|---|---|---|---|---|---|
| `pf-seed1` 07:46 | `0607485b` | 0 | `PUT /api/v1/projects` | 9, toàn POST | 0 | 0 |
| `gg-seed1` 11:07 | `a6839ada` | 0 | `PUT /api/v1/projects` | 9, toàn POST | 0 | 0 |

Chín nguồn của `gg-seed1`: `POST /login`, `/notifications/{id}`, `/teams/{id}/members/{userID}/admin`,
`/user/deletion/cancel`, `/user/deletion/request`, `/user/export/download`, `/user/export/request`,
`/user/password`, `/user/settings/totp/disable`. Mỗi nguồn: `victims []`.

## Chỗ chặn là nguồn, transition thì chưa tới

Đọc 2026-09-26. Danh sách nguồn chỉ phụ thuộc transition ở một điều kiện, `op.path != transitionOp.path`
(`RestSecurityBuilder.kt:531–539`). Nguồn phải có một 403 và một 2xx có xác thực trong archive, trên cùng
endpoint. Chín nguồn trên không cái nào có 2xx có xác thực. Đổi transition sang ứng viên kế tiếp giữ nguyên
chín nguồn đó, nên vẫn 0 bộ ba.

Ghi chú cuối tuần 09-25 "Vikunja cần vòng lặp thử ứng viên transition kế tiếp" sai hướng. Patch đó không soạn.

Nguồn đúng trên Vikunja là lệnh ghi vào project 4 hoặc task của nó, nơi carol nhận 403 và bob nhận 2xx. Trong
archive không có lệnh nào như vậy: fuzzer sinh id ngẫu nhiên, còn id thật là project 4 và các task đã gieo
(`../vikunja-diag-20260924/RESULTS.md`, mục Nguồn).

## Hướng không cần sửa code, chưa chạy

- Thêm `example` cho `projectID`, `id` của project và task vào bản sao spec. EvoMaster dùng `example` với xác suất
  `probRestExamples = 0.20` (`EMConfig.kt:2992`). Đây là một sai lệch của target, phải khai.
- Gieo test ban đầu bằng `--seedTestCases` (Postman, `EMConfig.kt:2633`, đánh dấu `@Experimental`).

Kiểm tay 09-17: bob hạ quyền rồi ghi bằng token cũ nhận 403
(`../../analysis/cve-survey/vikunja-handcheck-20260917.md`).
