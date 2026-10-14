# Tier-1 bản lỗi seed 10, log debug, jar `NR-3c087e58` và `VI-d2325da7` — 2026-09-30

Chuỗi `numrole-chain-20260930/` ra Tier-1 seed 10 không có 970 (bản lỗi) và không có bộ ba (bản đã sửa); jar `VI` và 5 jar
trước đều có. Chạy lại dòng bản lỗi với log debug (`rerun.sh`): jar `NR` lặp lại (0 bộ ba, 09:06–09:10), jar `VI` ra
bộ ba `200/200/200` (09:10–09:14). Lỗi của jar, không phải nhiễu thời gian.

| | jar `VI` | jar `NR` |
|---|---|---|
| Giá trị hạ harvest | `[VIEWER, ADMIN, EVOMASTER]` | như bên trái |
| Vai trò hiện tại của `superadmin` | không đọc | `[VIEWER]` |
| Giá trị hạ dùng | `[VIEWER, ADMIN, EVOMASTER]` | `[ADMIN, EVOMASTER]` |
| Hai lần thử đầu | VOID `200/403/200` (operator `alice`, `bob`) | như bên trái |
| Khôi phục quyền | `alice` role `ADMIN`, 200 | không có |
| Bộ ba | `200/200/200`, 970 | không |

Nguyên nhân, hai chỗ của sửa role-value (jar `RV`, `wip/role-value-20260929.md`):
1. `victimRoleValues` đọc `VIEWER` từ một response GET trong archive. Suy luận, chưa kiểm body: trong pha search có test
   hạ `superadmin` xuống `VIEWER` rồi GET; lúc builder chạy `superadmin` đã về vai trò gốc. Archive là lịch sử, không phải
   trạng thái hiện tại — cùng loại với sửa thứ năm.
2. `harvestElevatedRoleCandidates(transitionDef, roleValues.firstOrNull())` loại giá trị đầu của danh sách đã lọc. Danh
   sách đã lọc bắt đầu bằng `ADMIN`, nên `ADMIN` bị loại khỏi giá trị khôi phục.
