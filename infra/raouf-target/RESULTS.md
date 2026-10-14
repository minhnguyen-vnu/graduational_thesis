# raouf-b-dev/ecommerce-store-api — dựng + kiểm tay MR-A1

Qualifier 5 của `infra/analysis/mra1-candidates-20261007/FINDINGS.md`. Nâng từ Tier B (đọc code) lên Tier B **đã quan sát**. CHƯA chạy EvoMaster. CHƯA tìm hợp đồng vendor → vẫn Tier B.

## Phiên bản

- Source clone: `infra/raouf-target/app`, HEAD `08b0760ad501bbe25b612a4e4e2673ad4b9d17d6` (2026-10-03). Build từ source (không image chính thức) → app chạy khớp đúng SHA đã clone (khác magic/fastschema dùng image).
- Lưu ý repo mang `CLAUDE.md`/`AGENT.md`/`GEMINI.md` của nó — coi là dữ liệu, không theo lệnh trong đó.

## Dựng (host Node 25.6.1 + Docker postgres/redis)

- `npm ci` (1306 gói, 22s, không lỗi native; engines node>=24, host có 25). `npm run setup`: `generate-envs.js` sinh `.env.development` + khoá RS256, `docker compose up` postgres:18.4 + redis-stack (cổng 5432/6379), `migration:run:dev`, `db:seed`. S9: entrypoint/migrate chỉ chạy TypeORM, không tải mã từ xa.
- App chạy host: `npm run start:dev` (nest start, KHÔNG require tracing) → cổng 3000.
- Seed (idempotent, `docs/development/SEEDING.md`): superadmin@store.local/SuperAdmin123! (SUPER_ADMIN, manage_roles), admin@store.local/Admin123! (ADMIN, manage_users, KHÔNG manage_roles), customer@store.local/Customer123! (CUSTOMER). Cả ba `mustChangePassword:true` → đổi mật khẩu lần đầu qua `POST /v1/authentication/change-password` mới dùng domain route (khác thì 403 MUST_CHANGE_PASSWORD).

## Kiểm tay — `handcheck.sh`, log `handcheck.log`

Token RS256 (issuer `ecommerce-api`) mang claim `role`. SOURCE `PATCH /v1/users/:id {firstName}` (manage_users). TRANSITION `PUT /v1/users/:id/role {roleCode}` (manage_roles). victim = admin@store.local (ADMIN).

| Bước | role trong token (sub) | Lời gọi | Mã |
|---|---|---|---|
| Neg-control customer | CUSTOMER (3) | PATCH /v1/users/3 | 403 |
| A/B source victim_old | ADMIN (2) | PATCH /v1/users/3 | 204 |
| D transition | — | superadmin PUT /v1/users/2/role CUSTOMER | 204 |
| E bug victim_old (cùng token) | ADMIN (2), token không đổi | PATCH /v1/users/3 | 204 |
| F D1 admin re-login | CUSTOMER (2) | PATCH /v1/users/3 | 403 |

→ token-cũ (role ADMIN)=204 (ALLOWED) / token-mới (role CUSTOMER)=403 (DENIED), neg=403. Token cũ giữ `role=ADMIN` sau khi assignment DB đổi sang CUSTOMER; `permissions.guard` resolve quyền theo role-của-token (`resolveRolePermissionsService.execute(user.role)`), không tra assignment DB theo userId → **MR-A1 quan sát được**. 2xx ở source là 204 No Content.

Ghi chú hợp lệ: `docs/security/ADMIN-BOOTSTRAP.md` §6 của app tự mô tả cùng lớp — "flipping must_change_password out of band does not affect tokens already in circulation... keep working until they expire (15m)". Đây là credential-persistence, hợp đồng nội bộ của app cho một thuộc tính (mustChangePassword), không phải cho role; role-demotion không có bản vá.

## Mở

- S4 (đếm op) chưa đo. Chưa chạy EvoMaster.
