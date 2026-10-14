# ai-native-callcenter, held-out, jar `VI-d2325da7` — 2026-09-29

Giao thức: `infra/analysis/heldout-small-apps.md` §6. Lượt 1 ở `../aicc-heldout-20260929/`, lượt 2 ở đây.

## Kết quả

| Lượt | Seeds | 970 | Bộ ba hợp lệ | VOID | UNCONFIRMED | Mã bộ ba |
|---|---|---|---|---|---|---|
| 1 | 1 | 0 | 0 | 0 | 0 | — |
| 2 | 1 | 0 | 0 | 0 | 1 | `200/200/200`, nạn nhân `admin`, người hạ `victim` |

FP 0, TN 0.

## Sai lệch

Cả hai lượt dừng tay sau seed 1, giữa seed 2: lượt 1 lúc 10:20, lượt 2 lúc 10:33. Nguyên nhân tìm được trong log của
seed 1 cho thấy mọi seed sau lặp lại cùng mẫu.

## Nguyên nhân

Lượt 1: 462 response `403 missing X-AICC-Csrf header`. `--header0` tạo tài khoản thứ tư "Fixed Headers"
(`HttpWsSampler.kt:64–90`, upstream), không gắn header vào ba tài khoản cấu hình.

Lượt 2 (`logs/auto-seed1-300s-evomaster-VI-d2325da7.log`, `traffic/…seed1….jsonl` 10:30:33):
1. Builder chọn transition `PUT /api/v1/users/{userId}`, giá trị `[ADMIN, AGENT, EVOMASTER, SUPERVISOR, ACTIVE,
   SUSPENDED]`; một nguồn có nạn nhân, `PUT /api/v1/queues/{queueId}`, nạn nhân `admin`.
2. Transition gửi `{"username":"T9","role":"ADMIN","status":"ACTIVE"}`, 200. `role` là giá trị đầu danh sách, trùng
   vai trò hiện tại của nạn nhân: không hạ quyền nào. Với mỗi người hạ, builder chỉ thử giá trị đầu
   (`RestSecurityBuilder.kt:636–651`); seed nào có nạn nhân ADMIN cũng gửi `ADMIN`.
3. `username` bắt buộc trong body, nhận giá trị ngẫu nhiên `T9`: tài khoản `admin` bị đổi tên, các lần đăng nhập
   `admin` sau đó 401.
4. C4 đăng nhập lại nạn nhân, vẫn 200, loại bộ ba UNCONFIRMED. Không có C4, bộ ba `200/200/200` này thành 970, một
   FP trên code bên thứ ba.

Kiểm tay 10:08 (`infra/aicc-target/handcheck-20260929-1008.txt`) cho thấy app chặn cookie cũ sau khi hạ `role=AGENT`.
