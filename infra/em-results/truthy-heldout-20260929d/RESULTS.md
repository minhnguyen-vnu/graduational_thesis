# truthy, held-out, jar `RV-44254256` — 2026-09-29

Giao thức: `infra/analysis/heldout-small-apps.md` §9 và các mục bổ sung. Bốn lượt, đều dừng sau seed 1 hoặc trước đó.

## Kết quả

| Lượt | Thư mục | Seeds | 970 | Lần thử bộ ba | Dừng vì |
|---|---|---|---|---|---|
| a | `truthy-heldout-20260929/` | 0 | — | — | harness đếm sai dòng đăng nhập |
| b | `…b/` | 1 | ERR | 0 | throttle đăng nhập sai khoá `admin`, `victim`; EvoMaster exit 1 khi gặp 429 |
| c | `…c/` | 1 | 0 | 0 | `PUT /auth/profile` đổi tên cả ba tài khoản |
| d | `…d/` | 1 | 0 | 0 | builder không gán được giá trị vai trò |

FP 0, TN 0, TP 0.

## Lượt d, seed 1

`logs/auto-seed1-300s-evomaster-RV-44254256.log`, 1573 test. Đăng nhập: `admin` 815 lần 204, `victim` 815,
`viewer` 619.

1. Transition chọn `PUT /users/{id}`, ứng viên thứ 8 trong 8. Giá trị: `[EVOMASTER, active, blocked, inactive]`,
   toàn giá trị enum `status`.
2. Source có guard: 4. `PUT /roles/{id}` có nạn nhân `victim`, khớp source của kiểm tay 21:39.
3. `victimRoleValues("victim") = []`: body trả về không có trường vai trò kiểu giá trị (`roleId` bị ẩn khi serialize,
   `role` là object).
4. 8 dòng `could not set reduced role …` trên `PUT /users/{id}`. Spec khai báo `"roleId": {"type": "number"}`, EvoMaster
   sinh gene số thực; `harvestReducedRoleCandidates` chỉ thêm giá trị số khi gene là `IntegerGene` hoặc `LongGene`
   (`RestSecurityBuilder.kt:945`), nên danh sách chỉ còn chuỗi, gán vào `roleId` đều hỏng.
5. 0 lần thử bộ ba.

Kiểm tay (`infra/truthy-target/handcheck-20260929-2139.txt`) cho thấy app từ chối cookie cũ sau khi hạ `roleId=2`.
