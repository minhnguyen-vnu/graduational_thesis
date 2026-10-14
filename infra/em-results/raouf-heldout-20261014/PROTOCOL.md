# raouf held-out — giao thức chạy máy (ghi 2026-10-14, trước lượt chạy đầu)

Target đầu tiên của campaign held-out app công khai (Qualifier 5, `infra/analysis/mra1-candidates-20261007/FINDINGS.md`).
App công khai thật, lỗi MR-A1 có thật trong mã (kiểm tay XÁC NHẬN), **chưa chạy EvoMaster lần nào**.

## Target

- `raouf-b-dev/ecommerce-store-api`, build từ source `infra/raouf-target/app`, HEAD `08b0760` (khớp `infra/raouf-target/RESULTS.md`).
- Chạy host: `NODE_ENV=test ./node_modules/.bin/nest start` → cổng 3000. Postgres `postgres-db` :5432/`my_database`, Redis :6379.
- Spec phục vụ: `http://localhost:3000/api/docs-json` (OpenAPI 3.0.0, 79 op / 48 ghi / 64 path). Bản lưu: `openapi.json`.
- SOURCE `PATCH /v1/users/{id}` (manage_users). TRANSITION `PUT /v1/users/{id}/role {roleCode}` (manage_roles). victim = admin@store.local (ADMIN), operator = superadmin@store.local (SUPER_ADMIN), low = customer@store.local (CUSTOMER).
- Denial = 403 sạch; MR-A1 kiểm tay live: token-cũ(ADMIN)=204 / token-mới(CUSTOMER)=403 / neg=403 (`handcheck.sh`).

## Jar

`EvoMaster/evomaster-P2e-6ae8277b.jar`, sha256 `6ae8277b…c751e`. Quyết định của user 2026-10-14: chạy P2e luôn, chấp
nhận cổng P2d 21/21 + 2 hàng delta P2e đã khớp làm đủ (lệch luật đã khai, `jars.md`). Không chạy cổng riêng P2e.

## Lệch luật đã khai

1. **Throttle tắt bằng `NODE_ENV=test`.** Login bị `@Throttle` strict 10/phút (xác nhận: lần 11 trả 429). EvoMaster đăng
   nhập nhiều lần/test → sẽ ăn 429 giết bộ ba. `UserThrottlerGuard.canActivate` tự skip toàn bộ throttle khi
   `NODE_ENV=test` (công tắc có sẵn của app, không sửa mã target). `.env.test` dùng **chung** DB/port với dev. Soát src:
   chỉ 3 nhánh `NODE_ENV==='test'` — throttle-skip, một test-helper ngoài đường request, bypass chữ ký Stripe webhook;
   **không nhánh nào chạm auth/role/login**. Kiểm lại: 30 login liên tiếp đều 200, handcheck MR-A1 vẫn PASS dưới test mode.
2. **Strip spec 6 op phá-chủ-thể** (`strip_spec.py` → `openapi-nokill.json`, luật 09-17): `POST /authentication/{logout,logout-all,change-password}`,
   `DELETE /users/{id}`, `POST /users/{id}/deactivate`, `DELETE /roles/{id}`. Giữ 73 op; source + transition + login còn nguyên.
3. **Reseed bằng SQL khôi phục role** (`reseed.sh`): không có endpoint reset HTTP; `db:seed` reset mật khẩu +
   `must_change_password` theo email nhưng **không** reset role (đã kiểm: admin kẹt CUSTOMER qua cả `npm run setup`). Reseed
   mỗi seed = `db:seed` → SQL set `user_role_assignments.role_id` canonical cho 3 tài khoản → rotate mật khẩu (login →
   change-password, docpw→docpw+"x") để login một-bước trả token `mustChangePassword=false`. Marker `RESEED_OK victim_role=ADMIN`.
4. **Không có bản vá role-demotion** → không có arm 0-FP từ bản đã sửa. Mọi 970 **soát tay** so với bộ ba kiểm-tay
   (source PATCH /users/{id}, transition PUT /users/{id}/role, victim ADMIN→CUSTOMER) trước khi xếp TP; 970 khác hình dạng → audit FP.
5. **Chỉ arm "không reset"** (con số chính, CLAUDE.md §4). Arm ablation-reset N/A (không endpoint reset HTTP).

## Rủi ro giữ lại (ghi để người đọc tự cân)

- Role CRUD `POST/PATCH /roles` giữ trong spec. EvoMaster (as superadmin) có thể sửa role giữa lượt; `RoleSystemDataInitializer`
  chỉ chạy lúc app bootstrap, không chạy theo `db:seed`. Reseed phục hồi gán role của 3 tài khoản nhưng không tái tạo role bị
  sửa định nghĩa trong cùng lượt. Nếu nhiễu, sẽ khai thêm và strip ở lượt sau — không sửa builder.

## Nhánh và ngân sách

- Jar P2e, cờ D1 **tắt** (`--statefulAuthzTwoCredentialJudgment false`), `--useExperimentalOracles true`,
  `--extraPhaseBudgetPercentage 0.25`, `--ratePerMinute 600`, `--maxTime 600s`, qua proxy ghi request (`capture_proxy.py` :8212→:3000).
- Arm chính `auto`: builder tự chọn transition. Seeds 1–10. Con số recall black-box.
- Arm `declared` (phụ): `--statefulAuthzTransition "PUT /v1/users/{id}/role roleCode=CUSTOMER id=2"`. Không trích recall từ arm này.

## Đếm (`runs-<arm>.csv`)

`arm,seed,maxtime,exit,det970,assembled,void,unconfirmed,evaluated,victim_login,operator_login,low_login,sleep,transition`.
det970 từ `report.json` faultCategories code 970. Login từng tài khoản đếm từ traffic jsonl (xác minh victim+operator có đăng nhập).

## Luật dừng sớm (ghi trước lượt chạy)

- Sau seed 1: trong traffic không có login victim **hoặc** không có login operator → DỪNG, tìm nguyên nhân trong log.
- `Evaluated tests` seed 1 < 200 → CẢNH BÁO (không dừng), xét ngân sách.
- 3 seed đầu cùng một mẫu và 0 bộ ba hợp lệ (assembled=0) → DỪNG batch, ghi lệch luật, tìm nguyên nhân (đọc từng hàng khi rơi xuống).
- Bất kỳ `Entering Sleep` nào trong lúc một hàng chạy → DỪNG (harness tự kiểm qua `pmset`).

## Giữ held-out

raouf là held-out tới lượt chạy này. Nếu lộ bug builder (ví dụ không chọn được `roleCode=CUSTOMER` là giá trị hạ quyền):
**ghi FN, KHÔNG sửa builder giữa campaign** — sửa là raouf thành target phát triển.
