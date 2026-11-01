# EvoMaster upstream master trên Tier-1, 20 seed — kết quả (2026-10-19 00:07)

Protocol `PROTOCOL.md`. Jar `EvoMaster-upstream/evomaster-upstream-master-d898c1ce.jar` (master `ab983ba338`,
2026-10-16). Bản lỗi Tier-1 `reports-api` :8080, seed 1–20, 22:21–00:06.

## Kết luận

0/20 seed báo lỗi nào thuộc lớp MR-A1. Trong traffic, 4 lời gọi bằng token cấp lúc còn ADMIN cho thao tác chỉ-ADMIN sau
khi tài khoản đã bị hạ trả 200 (seed 5, 11, 12, 17). Không lời gọi nào có source 2xx bằng cùng token trước lần hạ, không
lời gọi nào được gắn lỗi, và không test nào trong bộ test xuất ra giữ chuỗi đó.

## Toàn vẹn

- 20/20 hàng exit 0, `report.json` đọc được; không luật dừng nào nổ; 0 lỗi chuyển tiếp của proxy; không `Entering Sleep`.
- Mỗi seed cả ba tài khoản đều đăng nhập 200: alice 90–148, superadmin 104–130, bob 78–114 lần (`runs.csv`).
- 886–1013 request mỗi seed qua proxy.

## Lỗi upstream báo (`report.json`, tên lấy từ chú thích test sinh ra)

| Mã | Tên | Lần | Seed | Op |
|---|---|---|---|---|
| 109 | HTTP Violation: no-401-if-no-authenticate | 279 | 20/20 | mọi op, nhiều nhất `POST /auth/login` (95) |
| 202 | Schema Violation: no-401-if-no-auth | 279 | 20/20 | như 109 |
| 305 | Wrongly Not Recognized as Authenticated | 15 | 15/20 | `POST /auth/login` |
| 301 | Cross-Site Scripting (XSS) | 7 | 5/20 | `PUT /reports/{id}` (5), `POST /reports` (2) |

286 lỗi trên 1.160 test. Không mã nào nói về quyền còn sót sau khi hạ.

## Traffic (`audit-traffic.out`)

61 lần hạ ADMIN xuống VIEWER, ở 18/20 seed (seed 3 và 14: 0). 6 lời gọi chỉ-ADMIN bằng token claim ADMIN của tài khoản
đang là VIEWER:

| Seed | Lúc | Chuỗi | Mã | Source cùng token trước đó |
|---|---|---|---|---|
| 5 | 22:46:47–48 | alice hạ superadmin; token cũ của superadmin `PUT /users/superadmin/role` VIEWER; lời gọi không token 401 | 200 | không |
| 11 | 23:17:50 | superadmin hạ alice; token cũ của alice `PUT /users/alice/role` VIEWER; không token 401 | 200 | không |
| 12 | 23:20:33 | token superadmin tự hạ mình, rồi cùng token `PUT /users/bob/role` ADMIN | 200 | không |
| 17 | 23:49:46 | như seed 11 | 200 | không |
| 17 | 23:48:29 | bob được nâng ADMIN, nhận token claim ADMIN (23:48:24); `POST /reset` 200 đưa bob về VIEWER; token đó `PUT /reports/683` | 404 | không |
| 20 | 00:02:56 | alice hạ superadmin; token cũ của superadmin `POST /reports` thân sai enum | 400 | không |

- Seed 5, 11, 17 (200): lời hạ quyền rồi cùng op lặp lại bằng tài khoản khác và không token (200, 200, 401). Thứ tự
  này khớp cách builder bảo mật upstream thử một op với mọi chứng chỉ; suy từ thứ tự lời gọi, chưa đối chiếu với log.
- Seed 12 (200): ngay trước là `POST /reports`, `GET /reports/6`, `DELETE /reports/6` bằng một token khác.
- 404 và 400 không là ALLOWED theo `CLAUDE.md` §3. Trên bản lỗi, 404 ở seed 17 cho thấy kiểm quyền đã cho qua (Tier-1
  kiểm quyền trước tồn tại); 400 ở seed 20 dừng ở kiểm thân, trước kiểm quyền.
- `full_triples_2xx` = 0 ở cả 20 seed.

## Test sinh ra (`audit-tests.out`)

1.160 test, 139 test có gọi `PUT /users/{u}/role`. 2 test có `VIEWER` 2xx rồi một thao tác chỉ-ADMIN bằng token của
nạn nhân: seed 8 `test_12_put_on_role_showsFaults_109_202`, seed 20 `test_11_put_on_role_showsFaults_109_202`, cả hai
trả 403. Traffic cho thấy token nạn nhân ở hai test này cấp khi nạn nhân đã là VIEWER (claim VIEWER: seed 8 idx 626,
seed 20 idx 636), nên 403 là hành vi đúng của bản lỗi, không phải token cũ. 0 test chứa lời gọi token cũ 2xx; bốn chuỗi
200 ở trên không có trong bộ test xuất ra.

## Dè dặt

- Arm này có proxy, khác arm Tier-1 của ta (lệch luật 1 của protocol); không ghép đôi với số của ta.
- Soát traffic dựa vào claim `role` của JWT và theo dõi vai trò qua `PUT /users/{u}/role` và `POST /reset`; trạng thái
  đầu mỗi seed là seed của `POST /reset` gọi trực tiếp vào :8080.
- Chỉ Tier-1, chỉ bản lỗi. Không chạy bản vá vì câu hỏi là upstream có báo lỗi trên bản lỗi không.
