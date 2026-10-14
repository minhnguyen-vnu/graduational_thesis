# Tham số user tên `email` — 2026-09-30

Cây trước: `46f937b4` (jar `LP-3cc44770`), lưu ở `pre-emailparam-20260930.patch`. Cây sau: `95ddb7b4`
(`emailparam-20260930.patch`), jar `EvoMaster/evomaster-EP-9007f79a.jar`, build 11:19. Self-test: `selftest/email-param.sh`.
Nguồn lỗi: bamf lượt c (`infra/analysis/heldout-small-apps.md` §12, `em-results/bamf-heldout-20260930c/`).

## Lỗi

bamf, transition `PATCH /api/v1/users/{email}`. `setUserInParams` gán tên nạn nhân vào tham số có tên khớp
`transitionUserParamSignals` (`username`, `userid`, `user_id`, `user`, `account`, `member`, `subject`, `principal`, rồi
`id`). `email` không khớp tên nào: 20 lần `could not target victim 'victim@example.com'`, 0 lần thử bộ ba.

## Sửa

| Chỗ | Làm gì |
|---|---|
| `userEmailParamSignals` | Danh sách mới, `["email"]`. |
| `setUserInParams` | Ba nhóm theo thứ tự: tên cũ trừ `id`, rồi `email`, rồi `id`. Nhóm `email` chỉ dùng khi không tham số nào khớp nhóm đầu. |

`transitionUserParamSignals` không đổi, nên `keepOnlyTargetFields` và `setInQueryParamsTopLevel` không đổi; `hasUserParam`
(xếp hạng) đọc lexicon, không đọc danh sách này.

Chạy tay trên bamf: path param `email`, nạn nhân `victim@example.com` (tên trong `bamf-auth-emailnames.yaml`); nhóm đầu không
khớp, nhóm hai khớp `email`, giá trị `victim@example.com`.

## Giới hạn

- Tên nạn nhân phải là email thật của tài khoản: file auth đặt tên theo định danh của API.
- Body có cả trường tên user và trường `email` thì vẫn gán vào trường tên user, như trước.
