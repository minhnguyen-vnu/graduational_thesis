# Transition chỉ gửi trường quyền — 2026-09-26, sửa lần 2 ngày 09-27

Viết và build không chờ duyệt, theo quyền người dùng cho ngày 2026-09-26 (CLAUDE.md §2). Người dùng duyệt sau.

Patch `transition-trim-20260926.patch`, trên cây sha `66bffda6` (jar `GG`). Hàm mới `keepOnlyTargetFields`
(`RestSecurityBuilder.kt`, ngay trước `trySetFromStringValue`), gọi ở hai chỗ: sau `setRoleFieldToReduced` trong
`executeStatefulAuthzTriple` (nhánh không khai transition) và sau `setAllRoleFieldsTo` trong `restorePrivilege`.

Nó làm gì: với transition vừa dựng, tắt mọi trường tuỳ chọn cấp một của thân yêu cầu và mọi query param tuỳ chọn,
trừ trường khớp `roleFieldSignals`, và trừ trường khớp `transitionUserParamSignals` khi path không có tham số người
dùng. Trường bắt buộc không bị đụng. In một dòng debug `removed optional fields [...] from <endpoint>`.

Lý do: jar `GG` trên Airflow, cặp đúng (nạn nhân `victim`, người thao tác `admin`) nhận 422 ở transition
(`em-results/genesetguard-chain-20260925/RESULTS.md`). Proxy ghi request đêm 09-26
(`em-results/gg-overnight-20260926/airflow/`) cho thấy thân `PATCH /auth/fab/v1/users/{username}` là thân ngẫu
nhiên của `doInitialize`, ví dụ `"last_name": {"EWMu9Cce": "f7vg", ...}`: sai kiểu thì Airflow trả 422. Trường
`username` ngẫu nhiên, nếu transition 2xx, đổi tên nạn nhân (curl 09-25), và `update_mask` ngẫu nhiên cho 400.

Ví dụ Airflow, `PATCH /auth/fab/v1/users/victim`: thân trước patch mang tới sáu trường
`email, first_name, last_name, password, roles, username` và có thể kèm `?update_mask=...`; sau patch chỉ còn
`roles`. Path có `{username}` nên `username` trong thân bị tắt.

Tier-1 `PUT /users/{username}/role`, thân `{role}`: không trường nào bị tắt. pyLoad `POST /api/set_user_permission`:
ba query param `user`, `permission`, `role` đều khớp, không bị tắt.

`roles` là mảng object; `setFromStringValue("user")` trên `ArrayGene<ObjectGene>` làm rỗng mảng và trả `true`
(`ArrayGene.unsafeSetFromStringValue`). Transition vì thế gửi `roles: []`, tức gỡ mọi vai trò: vẫn là một lần hạ
quyền, giữ nguyên.

**Sửa lần 2, 09-27 00:2x.** Lượt self-test đầu (`em-results/transitiontrim-chain-20260926/`, jar `0b6f3c31`) cho
thấy lần khôi phục quyền cũng gửi `{"roles":[]}`, Airflow trả 200 và gỡ mọi vai trò của người thao tác `victim`;
bộ ba đúng cặp sau đó có nguồn 403 (`403/200/403`). `setAllRoleFieldsTo` nay bỏ qua `ArrayGene` có template là
`ObjectGene`: trên Airflow không còn trường nào đặt được, `restorePrivilege` trả `false` trước khi gửi.
**Sửa lần 3, 09-27 01:0x.** Lần 2 kiểm `g is ArrayGene<*>`, nhưng `roles` khai `anyOf [array, null]` nên gene tên
`roles` là wrapper; kiểm `airflow-no-empty-restore` hỏng (`em-results/transitiontrim-chain-20260927/RESULTS.md`).
Nay bỏ qua mọi gene mà `flatView()` chứa `ArrayGene` có template `ObjectGene`. Patch gộp ba lần:
`transition-trim-20260927b.patch`.

**Sửa lần 4, 09-27 01:3x.** `roles` là `ChoiceGene` ba lựa chọn cùng tên (mảng, gene cho `null`, object gộp;
`RestActionBuilderV3.kt:1688–1706`). Lần 3 chỉ bỏ qua gene chứa mảng, `"admin"` vẫn gán vào hai lựa chọn còn lại
(`em-results/transitiontrim-chain-20260927b/RESULTS.md`). Nay `setAllRoleFieldsTo` bỏ qua cả cây con của mọi trường
quyền có chứa `ArrayGene` template `ObjectGene`. Patch gộp bốn lần: `transition-trim-20260927c.patch`. Self-test 8/8
trên jar `TT-129a7a56` (`em-results/transitiontrim-chain-20260927c/`).

Self-test `selftest/transition-trim.sh`, 8 kiểm, gồm `airflow-no-empty-restore` (jar `GG` có dòng `Privilege-restore`, jar mới không có): jar `GG` có transition 422 (đọc log cũ); Airflow seed 1 qua proxy
exit 0; có dòng `removed optional fields` khác rỗng trên PATCH users; mọi PATCH users gửi sau lúc builder chọn
transition có thân chỉ gồm khoá `roles` và không query; Tier-1 bản lỗi 970 và transition không mất trường nào;
Tier-1 bản đã vá không 970. Mã trạng thái bộ ba trên Airflow in ra dòng `INFO`, không phải một kiểm.
