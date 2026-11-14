# EvoMaster upstream master mới nhất trên Tier-1, 20 seed — kết quả (2026-11-11 22:51)

Protocol `PROTOCOL.md`. Jar `EvoMaster-upstream/evomaster-upstream-master-96365f7a.jar` (master `067df22ae2`,
2026-11-10). Bản lỗi Tier-1 `reports-api` :8080, seed 1–20, 21:06–22:51.

## Kết luận

0/20 seed báo lỗi nào thuộc lớp MR-A1. Trong 18 seed không bị nhiễu, 4 lời gọi bằng token cấp lúc còn ADMIN cho thao
tác chỉ-ADMIN sau khi tài khoản đã bị hạ trả 200 (seed 11, 12, 17, cộng seed 5 hàng 702 trước lúc nhiễu). Không lời
gọi nào có source 2xx bằng cùng token trước lần hạ, không lời gọi nào bị gắn lỗi, và không test xuất ra nào giữ chuỗi đó.

## Toàn vẹn

- 20/20 hàng exit 0, `report.json` đọc được; không luật dừng nào nổ; 0 lỗi chuyển tiếp của proxy.
- Mỗi seed cả ba tài khoản đăng nhập 200: alice 90–148, superadmin 104–130, bob 78–114 lần (`runs.csv`).
- 886–1013 request mỗi seed qua proxy.
- **Nhiễu từ Postman.** Postman (PID 89893, mở 20:41) giữ kết nối tới :8080 trong lúc batch chạy (`lsof` lúc 21:44).
  Lời gọi của nó không qua proxy. Kiểm tra trạng thái ngoài proxy (`diag/hidden-state-check.out`: claim đăng nhập lệch
  vai trò audit đang giữ) ra 3 chỗ, ở seed 5 (reseed, 21:32:01–02) và seed 7 (alice bị hạ quanh 21:42:58, nâng lại
  quanh 21:43:05); 0 ở 18 seed còn lại. Lượt 2026-10-18 ra 0 ở cả 20 seed.
- Từ 21:44:40 một vòng `lsof` mỗi 0,2 s ghi mọi client không phải proxy tới :8080 (`diag/port8080-clients.log`).
  Đối chứng: một kết nối `nc` 1,5 s bị ghi 5 lần. Seed 8–20: client ngoài duy nhất là EvoMaster seed 11 tải spec
  (`--bbSwaggerUrl` trỏ :8080). Seed 1–4 và 6 chạy trước khi có vòng ghi; với chúng chỉ có kiểm tra trạng thái, nên lời
  gọi chỉ-đọc từ ngoài không loại trừ được.
- Seed 5 và 7 bị đánh dấu nhiễu. `stale_2xx=23` của seed 5 gồm hàng 702 (token cũ thật, trước lúc nhiễu) và 22 lời gọi
  sau hàng 858, khi superadmin đã thật sự là ADMIN do reseed ngoài proxy.

## Lỗi upstream báo (`report.json`)

| Mã | Tên | Lần | Seed | Op nhiều nhất |
|---|---|---|---|---|
| 109 | HTTP Violation: no-401-if-no-authenticate | 280 | 20/20 | `POST /auth/login` (95) |
| 202 | Schema Violation: no-401-if-no-auth | 280 | 20/20 | như 109 |
| 305 | Wrongly Not Recognized as Authenticated | 15 | 15/20 | `POST /auth/login` |
| 301 | Cross-Site Scripting (XSS) | 7 | 5/20 | `PUT /reports/{id}` (5), `POST /reports` (2) |

287 lỗi trên 1.162 test. Tên mã lấy từ bảng của lượt 2026-10-18; `report.json` của jar này để trống trường tên.

## Traffic (`audit-traffic.out`, bỏ seed 5 sau hàng 858)

61 lần hạ ADMIN xuống VIEWER ở 18/20 seed (seed 3, 14: 0).

| Seed | Hàng | Chuỗi | Mã | Source cùng token |
|---|---|---|---|---|
| 5 | 702 | superadmin bị hạ ở 701; token cũ của superadmin `PUT /users/superadmin/role` VIEWER | 200 | không |
| 11 | 694 | alice bị hạ ở 693; token cũ của alice `PUT /users/alice/role` VIEWER | 200 | không |
| 12 | 145 | superadmin bị hạ ở 144; cùng token `PUT /users/bob/role` | 200 | không |
| 17 | 681 | alice bị hạ ở 680; token cũ của alice `PUT /users/alice/role` | 200 | không |
| 17 | 431 | token claim ADMIN của bob sau `POST /reset`; `PUT /reports/683` | 404 | không |
| 20 | 198 | superadmin bị hạ ở 196; token cũ `POST /reports` | 400 | không |

`full_triples_2xx` = 0 ở cả 20 seed. Các seed có chuỗi 200 và mã của chúng trùng lượt 2026-10-18 (5, 11, 12, 17).

## Test sinh ra (`audit-tests-perseed.out`)

1.162 test, 139 test có gọi `PUT /users/{u}/role`. 2 test có hạ quyền 2xx rồi một thao tác chỉ-ADMIN bằng token nạn
nhân: seed 8 `test_12_put_on_role_showsFaults_109_202` (superadmin), seed 20 `test_11_put_on_role_showsFaults_109_202`
(alice), cả hai 403, không source, không mã lỗi trên lời gọi đó. Cùng tên test và cùng mã với lượt 2026-10-18; claim
của token nạn nhân ở lượt này chưa đối chiếu với traffic. 0 test chứa lời gọi token cũ 2xx.
`audit-tests.out` là lần gọi sai đối số (`tests` thay vì từng thư mục seed), ra 0 test; không dùng.

## Dè dặt

- Arm này có proxy, khác arm Tier-1 của ta; không ghép đôi với số của ta.
- Seed 5 và 7 nhiễu; chạy lại hay không do user quyết.
