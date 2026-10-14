# Victim id, route không tồn tại, chuyển transition khi 404 — 2026-09-28

Patch: `transtrim-victimid-routemissing-20260928e.patch` (cây `cc178c8d`, trên cây `4d2beb47` của jar `TT`).
Jar `EvoMaster/evomaster-VI-d2325da7.jar`. Lý do: `em-results/grafana-heldout-20260928/RESULTS.md`, nguyên nhân 1
và 4. Self-test `selftest/victim-id.sh`.

Rollback diễn tập 09-29 09:15 trên cây `cc178c8d`: checkout hai file, `git diff HEAD` rỗng, apply lại, diff trùng
patch từng byte.

Jar trung gian, không đo: `VI-96ca8605` (route check đếm cả 401 của lời gọi không đăng nhập, không bỏ được route
nào), `VI-f59750ed` (bỏ nhầm `PUT /api/teams/{team_id}/members/{user_id}` vì cha có tham số), `VI-0222dd68` (chỉ xét
mã của lần thử cuối, không chuyển transition), `VI-f12cbcd6` (self-test FAIL `grafana-transition-uses-id`: id
vào `team_id` vì `team_id` khớp tín hiệu `id` và đứng trước `user_id`; `selftest-VI-f12cbcd6/`). Log: `em-results/grafana-dev-20260928/`.

## Ba thay đổi trong `RestSecurityBuilder.kt`

1. `routeLooksMissing`: bỏ một transition ứng viên khi đường dẫn kết thúc bằng tham số, đường dẫn cha không có tham
   số, archive có ít nhất một lời gọi đã đăng nhập trên đường dẫn cha, và mọi lời gọi đã đăng nhập trên hai đường
   dẫn đều 404. Grafana: `/api/access-control/roles/{roleUID}` và `/api/access-control/roles`.
2. `victimIdentifiers`, `setUserInParams`: đọc body 2xx trong archive, tìm object có `login`, `username`,
   `userName`, `user_name` hoặc `name` bằng tên tài khoản nạn nhân, lấy `userId`, `user_id`, `id`, `uid` của object
   đó. Gene khớp tín hiệu người dùng cụ thể (`user`, `username`, `member`…) được xét trước gene chỉ khớp `id`. Gene
   có tên kết thúc bằng `id` thử các id trước rồi tới tên; gene khác thử tên trước. Grafana:
   `{"userId":2,"login":"victim"}` cho `user_id` = 2.
3. Hàng đợi transition: builder giữ mọi ứng viên trong top 8 có giá trị vai trò, thay vì ứng viên đầu tiên. Khi một
   lần thử có nguồn 2xx và transition 404 (`transitionNotFoundSeen`), builder bỏ transition đó và thử ứng viên kế
   tiếp. Trần 8 lần thử giữ nguyên, tính chung cho mọi transition. Transition khai báo không đổi.

## Không đổi trên target cũ

- Archive không có id của nạn nhân: danh sách thử chỉ còn tên, như jar `TT`. Tier-1, Tier-2, pyLoad, Airflow dùng
  gene `username` hoặc `user`, tên không kết thúc bằng `id`: thử tên trước như cũ.
- Log jar `TT` (`transitiontrim-chain-20260927c`, pyLoad, Airflow): 0 lần thử có nguồn 2xx và transition 404; 6 lần
  transition 404 trên Tier-2 đều có nguồn 401.

## Grafana sau thay đổi, seed 1, 300 s (`grafana-dev-20260928/logs/auto-seed1-300s-evomaster-VI-f12cbcd6.log`)

Builder thử 4 transition, cả 4 trả 404, hết trần 8 lần thử. `PATCH /api/org/users/{user_id}` không nằm trong top 8:
7 ứng viên đồng điểm 0,5455 đứng trước, 5 trong đó là route `access-control` của bản Enterprise.
