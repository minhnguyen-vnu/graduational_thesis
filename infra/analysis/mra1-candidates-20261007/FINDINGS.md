# FINDINGS — khảo sát app công khai có khả năng dính MR-A1 (phiên 2026-10-07/08)

Kiểm tay (đọc repo/diff/code qua GitHub API + raw), KHÔNG dựng, KHÔNG chạy. Nhật ký đầy đủ: `STATE.md`.

## Tóm tắt

- **6 qualifier đầy đủ** (dải 30–1500★, chiến thuật mới):
  - `polterguy/magic` (1200★, C#/.NET, MIT) — C-JWT + `DELETE /magic/users_roles` (hạ-role) + `PUT /magic/roles`
    (idempotent source) + 403-on-deny + tự serve OpenAPI.
  - `quuuuj/hrm` (464★, Java/Spring Boot 3) — C-JWT (authority từ claim, code tự ghi chú không tra DB) +
    `POST /staff/set/{id}` (hạ-role) + `PUT /role` (idempotent source) + springdoc. Denial = HTTP 200 + body code 1300
    (KHÔNG 403; kiểm tay 2026-10-11 → oracle nguyên trạng không nổ, §6). Hợp nền tảng luận văn.
  - `bcms/cms` (464★, TypeScript/Node, headless CMS) — C-JWT (role `rls` trong token, `JWTManager` kiểm claim không tra
    DB) + `PUT /api/v4/user/update {role}` (vừa hạ-role vừa idempotent source) + 403-on-deny + OpenAPI.
  - `fastschema/fastschema` (575★, Go, BaaS) — C-JWT (user+RoleIDs trong JWT, `ParseUser` không re-fetch membership) +
    content-API `PUT /api/content/user/{id}` đổi roles m2m (hạ-role) + PUT idempotent + 403-on-deny + OpenAPI.
  - `raouf-b-dev/ecommerce-store-api` (55★, TS/NestJS) — C-JWT (role trong token, `PermissionsGuard` resolve quyền theo
    role-của-token, không tra assignment DB; assign-role không revoke) + `assign-user-role` (hạ-role) + `PUT /users/:id`
    (idempotent source) + 403-on-deny. Chứng minh dải nhỏ 30–100★ cũng có qualifier.
  - `alvaromrveiga/ecommerce-backend` (72★, TS/NestJS) — C-JWT (`access-jwt.strategy validate` role từ token, `RolesGuard`
    đọc token role) + `PATCH /user/role @IsAdmin` (hạ-role, cũng idempotent source) + 403-on-deny.
  - Cả sáu Tier B (xác nhận bằng đọc code, chưa dựng/chạy, chưa tìm hợp đồng vendor). Chi tiết + chạy tay A–F bên dưới.
- **2 near-miss in-band**: `placement-portal` (10★), `pairs-api` (14★) — C-JWT xác nhận qua code, thiếu endpoint đổi
  role → không dựng được transition.
- **Chỉnh chiến thuật (2026-10-08 sáng)**: phiên đêm dồn vào đáy 5–54★ (hầu hết tutorial/boilerplate, không có endpoint
  đổi role) → chỉ ra near-miss. Dải thật đáng tìm = **100–1500★ app self-hosted thật** (nơi artifact-keeper 1097★ đã
  trúng). Đổi S7′ sang ưu tiên dải này. magic tìm được ngay trong lượt đầu theo dải mới.
- Phát hiện giữ nguyên: full-MR-A1 là lớp lỗi thật nhưng hiếm; đa số app re-resolve quyền từ DB mỗi request.

## Kiểm chứng mã nguồn lần 2 (2026-10-08) — đọc lại file thật qua raw, bốn điều kiện quyết định

Kiểm lại từng qualifier bằng cách mở đúng các file nguồn (raw.githubusercontent.com), xét 4 điều kiện để 970 nổ:
(1) authz đọc role/quyền TỪ TOKEN, không tra lại DB mỗi request; (2) có endpoint admin hạ role user **khác**, trả 2xx;
(3) user bị hạ **vẫn login lại được** (để D1 có token mới và token mới bị 403); (4) **không có revoke/denylist** giết token
cũ khi đổi role. Tất cả 6 đều qua — lớp lỗi 970 có thật trong mã. Kèm theo cảnh báo và hai chỗ sửa dưới đây.

| # | App | 970 nổ được? | Độ tin | Cảnh báo quan trọng (cho lượt chạy EvoMaster) |
|---|---|---|---|---|
| 1 | magic | **Có** | Cao | token = `settings.ValidMinutes` (cấu hình; 5 năm nếu Expires=MinValue); `roles.put` trả 404 khi affected=0 (quirk theo giá trị); op có thể >200 |
| 2 | hrm | Lỗi có thật nhưng **oracle không nổ nguyên trạng** | Thấp để nổ máy | **denial = HTTP 200 + body code 1300, không phải 403** (kiểm tay 2026-10-11) → oracle thấy toàn 2xx, cần tính năng mã-từ-chối-cấu-hình-được mới nổ (§6); thêm **login captcha ảnh** (`/validate/code`) phải tắt như lệch luật bamf §12; token cookie httpOnly; op có thể >200 |
| 3 | bcms | **Có nhưng mong manh** | Trung bình | access token mặc định **60 giây** (`jwtExpIn=60000`, check `iat+exp<now`) → cửa sổ stale 60s; chỉ nổ nếu source→transition→follow-up xong trong 60s, chậm hơn thì token cũ hết hạn = 401 = INCONCLUSIVE |
| 4 | fastschema | **Có** | Cao | token mặc định 7 ngày (15′ nếu bật refresh); transition là `PUT /api/content/user/{id}` cần body quan hệ m2m `roles` (builder phải sinh được) |
| 5 | raouf | **Có** | Cao | access token stateless thật (refresh mới có `sid`/session; access thì không) |
| 6 | alvaromrveiga | **Có** | Cao | token 15′; chỉ có đúng 1 admin-write nên source=transition (giống artifact-keeper); repo push lần cuối 2022-06-09 (không "active thật" theo S7′) |

Bằng chứng đã mở (file:dòng), xác nhận code tồn tại đúng như mô tả:

- **magic**: `TicketFactory.cs:67` mint claim Role; `:115–116` VerifyTicket đọc `ticketProvider.InRole` → 403; `HttpTicketProvider.cs:55–58` `InRole`=`HttpContext.User.IsInRole` (claim, không DB); `magic.library/Initializer.cs:388–407` JWT bearer chỉ `ValidateLifetime`, **không** `OnTokenValidated`/denylist; `users_roles.delete.hl:13` guard root, xoá hàng (không xoá user); `roles.put.hl:14,43` PUT idempotent guard root, 202; `magic.auth.authenticate.hl:45–61` login đọc `users_roles` → bake vào token.
- **hrm**: `JwtAuthenticationFilter.java:24–25,87–96` comment+code tự ghi "không gọi loadUserByUsername, dựng authority từ claim"; `JwtUtil.java:26,60–66` access 15′, `extractPermissions` đọc claim; `SecurityConfig.java:27,80,82–85` STATELESS + 403/401 tách handler; `StaffController.java:98–103` `POST /staff/set/{id}` guard `system:staff:set_role`; `StaffRoleService.java:26–31` setRole xoá+gán lại (không khoá account); `RoleController.java:57–61` `PUT /role` guard `permission:role:edit`; `LoginService.java:44–51` **captcha bắt buộc**, `:58–68` login tính lại permissions từ role DB hiện tại.
- **bcms**: `jwt/manager.ts:151–163` checkPermissions đọc `payload.rls`, `:121–149` validate chỉ sig+iss+exp (không denylist); `route-protection/jwt.ts:24–29` fail→Forbidden; `user/controller.ts:313–339` `PUT /api/v4/user/update` guard `['ADMIN']`, chặn tự-đổi (phải đổi user khác), set `user.roles[0].name`; `auth/controller.ts:243` login bake `user.roles`; `config.ts:4–6` `jwtExpIn` mặc định **60000ms**.
- **fastschema**: `services/auth/middlewares.go:26–27` `user=claims.User; user.Roles=GetRolesFromIDs(user.RoleIDs)` (RoleIDs từ token), `:81–88` Authorize→Forbidden; `fs/user.go:30–31` RoleIDs+Roles m2m, `:67–83` IsRoot theo roles token; `auth.go:57–68` token 7 ngày mặc định; `local.go:314–330` LocalLogin đọc roles DB hiện tại, `:340–342` inactive không login được (demote vẫn active); `content.go:45–46` `PUT /content/:schema/:id`→Update; `services/auth/session.go:42` `UserToJwtClaims(user)` bake RoleIDs từ roles DB.
- **raouf**: `guards/auth.guard.ts:48,55` role từ `payload.role`; `jwt-verifier.service.ts:66–82` chỉ sig+iss+exp, access không có `sid`; `permissions.guard.ts:36–37` resolve quyền theo `user.role` (token), không theo userId; `resolve-role-permissions.service.ts:16` theo roleCode; `assign-role.usecase.ts:57` `updateRole` (thay thế, 1 role/user); `users.controller.ts:97–98` **PATCH** `/users/:id` guard `manage_users` (source), `:150–151` `PUT /users/:id/role` guard `manage_roles` (transition); `login-user.usecase.ts:120–151` bake role DB hiện tại.
- **alvaromrveiga**: `access-jwt.strategy.ts:24–29` validate trả `{userId,userRole}` từ token, không DB; `roles.guard.ts:31–37` đọc `userRole` token; `user.controller.ts:66–72` `PATCH /user/role` `@IsAdmin`; `user.service.ts:84–95` updateUserRole theo **email** (user khác), set role; `auth.service.ts:42` login bake `user.role`; `jwt.config.ts` access **15m**.

Hai chỗ đã sửa trong mục qualifier sau khi đọc lại code:
- **Q5 raouf**: source là **`PATCH /users/:id`** (guard `manage_users`), transition là `PUT /users/:id/role` (guard `manage_roles`) — bản cũ ghi nhầm "PUT /users/:id" và gộp guard.
- **Q3 bcms**: bổ sung cảnh báo access token mặc định 60 giây (cửa sổ stale rất ngắn).

**Xếp hạng khả năng oracle 970 NỔ khi chạy EvoMaster (black-box, dùng OpenAPI của app) — cập nhật 2026-10-11 sau kiểm tay, lật xếp hạng code-read cũ.** Dự đoán, chưa đo lượt nào; dựa 4 kiểu-trượt đã có bằng chứng: denial-code (kiểm tay hrm trực tiếp), mất-victim do ngân sách (Grafana 309 / Mattermost 623, §Đo đạc), FN do builder không nhận tham số user (bamf `{email}`), cửa sổ token (bcms 60s).

1. **raouf** — không dính kiểu-trượt nào: victim `:id` số sạch, API nhỏ → ngân sách chạm victim, denial=403 (204/403), access stateless không revoke, login đơn giản.
2. **fastschema** — token 7 ngày (cửa sổ an toàn nhất) + tự serve OpenAPI + victim `{id}` số; rủi ro: transition `PUT /content/user/{id}` cần builder sinh body quan hệ m2m lồng `roles:[{id}]`.
3. **alvaro** — hình dạng source≈transition như artifact-keeper (đã nổ máy 5/5), token 15′, tự đăng ký; rủi ro: transition `PATCH /user/role {email,role}` khoá victim theo **email** = đúng lớp FN bamf (builder không nhận email là tham số user).
4. **magic** — oracle mạnh + token cấu hình dài, nhưng **op>200** → nguy cơ ngân sách không chạm victim (như Grafana/Mattermost) + transition `DELETE …/users_roles` qua query-string + bootstrap nhiều bước.
5. **bcms** — endpoint sạch + OpenAPI, nhưng **token 60s**: source→follow-up trong search thường vượt 60s → token cũ hết hạn → 401 INCONCLUSIVE → bộ ba VOID.
6. **hrm** — **denial = HTTP 200 + body code 1300, không phải 403** → oracle thấy toàn 2xx, không phân biệt được → KHÔNG nổ nguyên trạng dù lỗi thật; thêm captcha + op>200. Chỉ nổ sau khi có tính năng "mã từ chối cấu hình được" (§6/tháng 10).

Mũi rẻ nhất để thử nổ thật đầu tiên: raouf.

## Qualifier 1 — polterguy/magic (1200★, C#/.NET, MIT, push 2026-09-29)

Low-code backend generator (Aista Magic). Auth stateless JWT, role nhét vào claim lúc mint, authorize đọc role từ claim
KHÔNG tra DB → đúng hình dạng C-JWT. Dedup: chưa từng xét ở phiên nào.

Bằng chứng code (đọc raw master, chưa dựng):

- **Role vào token lúc đăng nhập** — `backend/files/system/auth/magic.startup/magic.auth.authenticate.hl`: đọc
  `users_roles` của username rồi `add:x:./*/auth.ticket.create/*/roles` → `auth.ticket.create`. Mint ở
  `plugins/magic.lambda.auth/.../helpers/TicketFactory.cs CreateTicket`:
  `tokenDescriptor.Subject.AddClaims(ticket.Roles.Select(x => new Claim(ClaimTypes.Role, x)))`.
- **Authorize đọc role từ claim, KHÔNG tra DB** — `TicketFactory.VerifyTicket` → `ticketProvider.InRole("root")` →
  `services/HttpTicketProvider.cs InRole` = `HttpContext.User.IsInRole(role)`, lấy `ClaimsIdentity.Claims` type
  `ClaimTypes.Role`. Đường authorize không có query DB nào. (C-JWT ✓✓)
- **Token sống lâu, không denylist** — `CreateTicket`: `Expires` mặc định `settings.ValidMinutes`; nếu `DateTime.MinValue`
  → +5 năm ("never expires"). Không có cột `privileges_changed_at`/denylist/version được kiểm mỗi request.
- **Mã từ chối khớp oracle** — `VerifyTicket`: user đã auth nhưng thiếu role → `throw HyperlambdaException("Access
  denied", true, 403)`; thiếu session → 401. Đúng ALLOWED=2xx / DENIED=403 / 401=INCONCLUSIVE (§3).
- **Transition hạ-role tồn tại** — `backend/files/system/magic/users_roles.delete.hl`: `DELETE` bảng `users_roles` theo
  `{role, user}`, guard `auth.ticket.verify:root`. Admin gỡ role của user khác. (Mảnh mà 2 near-miss thiếu.)
- **C-SRC idempotent** — `backend/files/system/magic/roles.put.hl`: `PUT` update bảng `roles`, guard
  `auth.ticket.verify:root`, lặp lại được (không phải create-409 kiểu wagoe §14).
- **C-STEP** — delete/put chỉ `auth.ticket.verify:root`, không step-up/MFA.
- **S2** `docker-compose.yml`+`docker.backend`; **S3** `backend/files/system/endpoints/openapi.get.hl` tự serve OpenAPI →
  EvoMaster nạp được; **S5** `authenticate`→JWT; **S6** ≥2 role, root gỡ role user khác, user vẫn login lại được.
- **Mở**: S4 (đếm op trên spec thật — CRUDify nhiều bảng có thể >200, cần sizing ngân sách EvoMaster); S9 (magic chạy
  Hyperlambda động — là chức năng app, không phải tải mã từ xa lúc dựng; xác nhận khi dựng).

Chạy tay suy từ code (chưa chạy máy), victim khởi đầu có role `root`:
- A victim login → token_cũ mang claim `role=root`.
- B token_cũ → `PUT /magic/roles {name, description}` → **202** (VerifyTicket: `InRole("root")` true từ claim).
- C token user-thường (không root) → cùng call → **403** (guard là phủ định).
- D transition: admin `DELETE /magic/users_roles {role:root, user:victim}` → **200** (gỡ root của victim).
- E follow-up token_cũ (vẫn mang `root`) → `PUT /magic/roles` → **202** = tín hiệu lỗi (claim không đổi, không tra DB).
- F D1: victim login lại → token_mới đọc `users_roles` (đã hết root) → không có claim root → `PUT /magic/roles` → **403**.
- → token_cũ=202 / token_mới=403 → **970 nổ**. Tồn dư credential-specific (nằm trong JWT cũ), KHÔNG phải cache dùng
  chung (khác orkestra §16); source idempotent (khác wagoe §14). Cùng hình dạng artifact-keeper §18 đã XÁC NHẬN máy nổ.
- Nhãn: **Tier B** (CHƯA tìm hợp đồng vendor). **Dựng + kiểm tay XÁC NHẬN 2026-10-09** (`infra/magic-target/RESULTS.md`): trên image chính thức, token-cũ=202 / token-mới=403, neg-control=403. Chưa chạy EvoMaster.

## Qualifier 2 — quuuuj/hrm (464★, Java/Spring Boot 3 + Vue, push 2026-09-30)

Hệ thống quản lý nhân sự (HR). Spring Security STATELESS, authority lấy từ claim JWT, `@PreAuthorize` gác theo claim đó
KHÔNG tra DB → C-JWT. Dedup: chưa từng xét. Đặc biệt hợp nền tảng luận văn (tác giả Spring Boot).

Bằng chứng code (đọc raw nhánh `dev`, chưa dựng):

- **C-JWT ✓✓, code tự ghi chú** — `hrm-server/.../security/JwtAuthenticationFilter.java`: comment "不再调用
  StaffDetailsService.loadUserByUsername() 查 DB，而是从 JWT claims 中读取 staffId + permissions 直接构建认证对象"
  (không tra DB nữa, dựng authentication từ claim). Code: `authorities = JwtUtil.extractPermissions(token).stream()
  .map(SimpleGrantedAuthority::new)...` rồi set `SecurityContextHolder`. `JwtUtil.extractPermissions` đọc claim
  `permissions` (chuỗi phẩy). Login nhét permissions vào token (`buildClaims`).
- **Authorize đọc claim** — `config/SecurityConfig.java`: `@EnableMethodSecurity`, `SessionCreationPolicy.STATELESS`.
  Gác bằng `@PreAuthorize("hasAnyAuthority('permission:role:edit')")` (`role/controller/RoleController.java`) — kiểm
  authority dựng từ claim, không tra DB.
- **Mã từ chối KHÔNG khớp oracle** (kiểm tay 2026-10-11 sửa suy luận này) — `SecurityConfig.accessDeniedHandler` chỉ
  bắt denial mức filter-chain. Denial mức `@PreAuthorize` (guard controller) bị `@RestControllerAdvice` bắt và trả
  **HTTP 200 + body code 1300** (`不好意思，你没有此权限`), KHÔNG phải 403. Oracle 970 (DENIED=403) do đó không nổ nguyên
  trạng; map tay ALLOWED=body code 200 / DENIED=body code 1300. Xem §Dựng+kiểm tay cuối Qualifier 2 + `infra/hrm-target/RESULTS.md`.
- **Transition hạ-role** — `staff/controller/StaffController.java`: `POST /staff/set/{id}` body `List<Integer> roleIds`,
  guard `@PreAuthorize("hasAnyAuthority('system:staff:set_role')")` → `StaffRoleService.setRole(id, roleIds)` (xoá hết
  StaffRole của staff rồi gán lại). Admin đổi role staff khác. Staff account còn → re-login được.
- **C-SRC idempotent** — `PUT /role` (`RoleController.edit`) guard `permission:role:edit`, update lặp được.
- **C-STEP** — set_role/edit chỉ `@PreAuthorize`, không MFA.
- **Token access 15 phút** (`JwtUtil.ACCESS_EXPIRATION`) — cửa sổ stale bị chặn 15' nhưng thật; follow-up dùng token cũ
  ngay trước re-login nên đủ dựng bộ ba.
- **S3** springdoc `/v3/api-docs` (permitAll trong SecurityConfig) → EvoMaster nạp được.
- **Mở**: S5 login có `/validate/code` (captcha) — cần kiểm captcha có BẮT BUỘC không (nếu có, phải tắt qua config như
  lệch luật rate-limit bamf §12); S4 (219 file Java, nhiều CRUD controller → nghi >200 op, cần đếm trên spec).

Chạy tay suy từ code (chưa chạy máy), victim là staff có authority `permission:role:edit`:
- A victim login → token_cũ (15') claim `permissions` chứa `permission:role:edit`.
- B token_cũ → `PUT /role {id,name,...}` → **200**.
- C token staff thiếu authority đó → `PUT /role` → **403**.
- D transition: admin `POST /staff/set/{victimId}` body `[roleId_thấp]` (role không có `permission:role:edit`) → **200**.
- E follow-up token_cũ (claim vẫn có `permission:role:edit`) → `PUT /role` → **200** = tín hiệu lỗi.
- F D1: victim login lại → token_mới permissions hết `permission:role:edit` → `PUT /role` → **403**.
- → token_cũ=200 / token_mới=403 → **970 nổ**. Cùng hình dạng artifact-keeper §18 (credential-specific). Nhãn: **Tier B**.
- **Dựng + kiểm tay XÁC NHẬN 2026-10-11** (`infra/hrm-target/RESULTS.md`, build từ source HEAD 1ef6abc trong maven JDK17 container, chạy jar Java 21, middleware mysql×2+redis+pgvector+minio). Reset bcrypt pwd admin sang `Admin123!` (plaintext seed không rõ); victim tạo mới (`POST /staff`, pwd mặc định `123`) gán role 1 (có `permission:role:edit`) rồi admin hạ sang role 9. SOURCE `PUT /role`, TRANSITION `POST /staff/set/{id}`. token_cũ(role:edit) sau hạ=ALLOWED, token_mới=DENIED, neg=DENIED. **SỬA suy luận cũ**: denial mức `@PreAuthorize` KHÔNG trả HTTP 403 — hrm trả **HTTP 200 + body code 1300** (`不好意思，你没有此权限`); map ALLOWED=body code 200 / DENIED=body code 1300. accessDeniedHandler 403 ở SecurityConfig chỉ áp cho denial mức filter-chain, không áp cho method-guard. Hệ quả: **oracle 970 nguyên trạng (DENIED=403) KHÔNG nổ trên hrm** → đúng hạn chế CLAUDE.md §6 "mã từ chối chưa cấu hình được". Chưa chạy EvoMaster.

## Qualifier 3 — bcms/cms (464★, TypeScript/Node, headless CMS, push gần đây)

BCMS self-hosted headless CMS. JWT mang mảng role `rls`, authorize kiểm role từ claim KHÔNG tra DB → C-JWT. Dedup: chưa
từng xét.

Bằng chứng code (đọc raw `master`, chưa dựng):

- **C-JWT ✓✓** — `backend/src/_server/modules/jwt/models/payload.ts`: `JWTPayload { userId, rls: Roles, ... }` (role
  trong token). `_server/modules/jwt/pre-request-handler.ts`: `createJwtPreRequestHandler({roles})` →
  `JWTManager.get({token, roles})`; sai → `HttpStatus.Forbidden`. `JWTManager` (manager.ts:154):
  `const role = data.jwt.payload.rls.find((r) => data.roles.find((rn) => rn === r))` — so khớp role yêu cầu với claim
  `rls`, KHÔNG query DB. Hết hạn: `iat + exp < Date.now()`.
- **Transition + C-SRC (cùng một endpoint)** — `backend/src/user/controller.ts`: `PUT /api/v4/user/update`,
  guard `RP.createJwtBodyCheck(UserUpdateBodySchema, ['ADMIN'])`. Handler: `findById(body._id)`; nếu
  `body.role && body.role !== user.roles[0].name` và không phải tự-đổi → `user.roles[0].name = body.role`. Admin hạ
  role user khác (ADMIN→USER). PUT idempotent (update theo `_id`) → dùng chính nó / một PUT khác làm source lặp lại được.
- **403-on-deny** — guard trả `HttpStatus.Forbidden`. **C-STEP** — update không MFA. **Re-login** — user còn trong DB,
  login lại mint token `rls=[USER]`.
- **S3** controller có khối `openApi` + `path /api/v4/user` → BCMS sinh OpenAPI. Access token ngắn + `refresh-token-service`
  (cửa sổ stale có hạn; follow-up dùng token trước-transition ngay).
- **Cảnh báo (kiểm 2026-10-08)**: access token mặc định **60 giây** (`config.ts:4–6` `jwtExpIn=60000`;
  `manager.ts:139` check `iat+exp < Date.now()`). 970 chỉ nổ nếu source→transition→follow-up xong trong 60s kể từ lúc
  victim login; chậm hơn thì token cũ hết hạn → 401 = INCONCLUSIVE (không FP). Lỗi thật nhưng mong manh khi dựng máy.

Chạy tay suy từ code (victim là ADMIN thứ hai, admin-chính hạ victim):
- A victim(ADMIN) login → token_cũ `rls=[ADMIN]`.
- B token_cũ → `PUT /api/v4/user/update {_id: userX, email: same}` → **200** (JWTManager thấy ADMIN trong `rls`).
- C token USER → cùng call → **403**.
- D transition: admin-chính `PUT /api/v4/user/update {_id: victim, role: 'USER'}` → **200** (hạ victim).
- E follow-up token_cũ (vẫn `rls=[ADMIN]`) → `PUT .../update` → **200** = tín hiệu lỗi (không tra DB role victim).
- F D1: victim login lại → token_mới `rls=[USER]` → `PUT .../update` → **403**.
- → token_cũ=200 / token_mới=403 → **970 nổ**. Tier B. **Dựng + kiểm tay XÁC NHẬN 2026-10-09** (`infra/bcms-target/RESULTS.md`, build từ source HEAD d0e643d, node:20): token mang `rls`; cũ ['ADMIN']→200, mới ['USER']→403, neg=403; bộ ba <1s trong cửa sổ 60s. Chưa chạy EvoMaster.

## Qualifier 4 — fastschema/fastschema (575★, Go, BaaS + headless CMS, MIT)

All-in-one Backend-as-a-Service. User (gồm RoleIDs) nằm trong JWT, membership không re-fetch DB mỗi request → C-JWT.
Dedup: chưa từng xét.

Bằng chứng code (đọc raw nhánh `develop`, chưa dựng):

- **C-JWT ✓✓** — `fs/jwt.go`: `UserJwtClaims { User *User }` (cả user object vào token). `services/auth/middlewares.go
  ParseUser`: parse JWT → `user := claims.User; user.Roles = as.GetRolesFromIDs(user.RoleIDs)` — RoleIDs lấy từ CLAIM,
  không query user→role DB. `Authorize`: dùng `user` từ token; `user.IsRoot()` duyệt `u.Roles` (từ token);
  `AuthUserCan(c, user, resourceID)` theo role đó. Không có DB recheck membership.
- **Transition** — `fs/user.go`: `Roles []*Role` quan hệ `m2m` schema `role` (`fs.relation type=m2m`). Admin/root sửa
  roles của user khác qua content API `PUT /api/content/user/{id}` (roles relation) → hạ role. User còn trong DB → re-login.
- **C-SRC idempotent** — content update là PUT (lặp lại được); root-guarded admin-write khác cũng dùng được làm source.
- **403-on-deny** — `Authorize` user có id mà không quyền → `errors.Forbidden("Forbidden")`; không id → `Unauthorized`
  (401). Khớp oracle. **C-STEP** — không MFA trên content update.
- **S2/S3** Go binary + OpenAPI (fastschema tự expose); dựng không cần dịch vụ trả phí.

Chạy tay suy từ code (victim có role chứa quyền `api.content.X.update`, admin-chính hạ victim):
- A victim login → token_cũ `claims.User.RoleIDs=[adminRole]`.
- B token_cũ → `PUT /api/content/{X}/{id}` → **2xx** (AuthUserCan theo role từ token).
- C token role thường → **403**.
- D transition: admin `PUT /api/content/user/{victimId}` roles=[lowRole] → **2xx** (đổi membership DB).
- E follow-up token_cũ (RoleIDs vẫn =[adminRole]) → `PUT /api/content/{X}/{id}` → **2xx** = tín hiệu lỗi.
- F D1: victim login lại → token_mới RoleIDs=[lowRole] → **403**.
- → token_cũ=2xx / token_mới=403 → **970 nổ**. Tier B. **Dựng + kiểm tay XÁC NHẬN 2026-10-09** (`infra/fastschema-target/RESULTS.md`): token mang `role_ids`; token-cũ=[Admin]→200, token-mới=[User]→403, neg=403. Chưa chạy EvoMaster.

## Qualifier 5 — raouf-b-dev/ecommerce-store-api (55★, TypeScript/NestJS, modular-monolith ecommerce)

NestJS ecommerce. Role nằm trong JWT (tự mint RS256, issuer `ecommerce-api`); permission resolve theo role-của-token mỗi
request, role membership KHÔNG tra lại DB → C-JWT. App nhỏ (55★) nhưng active thật (e2e tests, clean-arch). Dedup: mới.

Bằng chứng code (đọc raw `master`, chưa dựng):

- **C-JWT ✓✓** — `src/guards/auth.guard.ts`: `payload = jwtVerifierService.verifyAccessToken(token)`;
  `request.user = { userId, email, role: payload.role, ... }` (role từ claim). `src/modules/authorization/
  primary-adapter/guards/permissions.guard.ts`: `resolveRolePermissionsService.execute(user.role)` — resolve quyền theo
  ROLE CỦA TOKEN; không tra user-role-assignment DB theo userId. Demote user (đổi assignment DB) không đụng token cũ.
- **Verify path không revoke** — `infrastructure/jwt/services/jwt-verifier.service.ts`: `jose jwtVerify` chỉ chữ ký +
  issuer `ecommerce-api` + `typ`; KHÔNG kiểm denylist/jti/version. `assign-user-role.usecase.ts` (transition) chỉ
  `authorizationGateway.assignRole(userId, roleCode)`, KHÔNG gọi `revoke-all-for-user`. → access token cũ còn hiệu lực.
- **Transition** — `AssignUserRoleUseCase` nối trong `identity/users.controller.ts` (`@RequirePermissions('manage_users')`
  cấp class) → admin gán role khác cho user. User còn → re-login.
- **C-SRC idempotent** — `PATCH /users/:id` (`update-user.usecase`) guard `manage_users`, lặp lại được (kiểm 2026-10-08:
  method là PATCH, không phải PUT; transition `PUT /users/:id/role` guard `manage_roles`).
- **403-on-deny** — `PermissionsGuard` trả `false` → NestJS ForbiddenException (403). **C-STEP** — không MFA.
- Token RS256 local + JWKS (tự expose), issuer riêng → không external IdP.

Chạy tay suy từ code (victim có role `admin` → quyền `manage_users`):
- A victim login → token_cũ `role=admin`.
- B token_cũ → `PUT /users/{x}` → **2xx** (PermissionsGuard resolve admin→manage_users từ role token).
- C token role thường → **403**.
- D transition: admin `POST .../assign-user-role {userId:victim, roleCode:customer}` → **2xx** (đổi assignment DB).
- E follow-up token_cũ (role vẫn `admin`) → `PUT /users/{x}` → **2xx** = tín hiệu lỗi (role membership từ token).
- F D1: victim login lại → token_mới `role=customer` → `PUT /users/{x}` → **403**.
- → token_cũ=2xx / token_mới=403 → **970 nổ**. Tier B. **Dựng + kiểm tay XÁC NHẬN 2026-10-09** (`infra/raouf-target/RESULTS.md`, build từ source HEAD 08b0760): token mang `role`; token-cũ(ADMIN) PATCH=204, token-mới(CUSTOMER)=403, neg=403. Chưa chạy EvoMaster.

## Qualifier 6 — alvaromrveiga/ecommerce-backend (72★, TS/NestJS + Prisma)

Cùng khuôn NestJS như Qualifier 5, xác nhận code (raw `main`):
- **C-JWT ✓✓** — `src/auth/access-jwt.strategy.ts`: `validate(payload)` trả `{ userId: payload.sub, userRole:
  payload.userRole }` — role từ token, KHÔNG tra DB. `src/common/guards/roles.guard.ts`: `const { userRole } =
  request.user; if (isAdmin && userRole === Role.ADMIN) return true` — đọc role token, không DB.
- **Transition** — `src/models/user/user.controller.ts`: `@IsAdmin() @Patch('role') updateUserRole(UpdateUserRoleDto)`
  → `userService.updateUserRole` (admin đổi role user khác). User còn → re-login.
- **C-SRC** — `PATCH /user/role` idempotent (set cùng role) admin-guarded; dùng làm source lặp lại được.
- **403-on-deny** — RolesGuard `false` → ForbiddenException (403). **C-STEP** — không MFA.
- Chạy tay = như Qualifier 5 (token_cũ userRole=ADMIN vẫn 2xx sau khi bị hạ; token_mới=USER → 403). Tier B. **Dựng + kiểm tay XÁC NHẬN 2026-10-09** (`infra/alvaro-target/RESULTS.md`, build từ source HEAD dbd0cd1 trong node:18 vì Node 25 gỡ util.isObject): token mang `userRole`; cũ ADMIN PATCH=200, mới USER=403, neg=403. Chưa chạy EvoMaster.

## Phương pháp

Luật S1–S10 + C-JWT/C-SRC/C-STEP (xem `README.md`). Route đã dùng: issue-title contract; commit free-text (nhiễu, bỏ);
GHSA CWE-613/863 (toàn lib phổ biến); search/repositories theo stack (NestJS, Go, Flask, multi-tenant, helpdesk/CRM,
Rails, Laravel). Mỗi candidate: dedup với các phiên trước (`heldout-small-apps.md`), lọc sao, đọc code authz thật
(verify tồn tại — một issue mô tả C-JWT đẹp hoá ra phantom, code không tồn tại: gittensor#1420).

## Khảo sát theo ecosystem (vì sao đa số KHÔNG nổ 970)

| Ecosystem / lớp | App đại diện đã đọc | Cơ chế authz | C-JWT? | Kết luận |
|---|---|---|---|---|
| FastAPI admin-backend | fastapi-admin-v2, fastapiReactadmin | DB + Redis cache version-bumped | Không | Loại cả lớp |
| NestJS auth | nestjs-auth, caps-pizza | JwtStrategy.validate → findById DB | Không | Loại cả lớp |
| Go + Casbin | gin-casbin-admin | Casbin enforce theo DB policy | Không | Loại cả lớp |
| Go CRM (JWT thủ công) | GopherCRM | JWT có role claim NHƯNG ValidateToken GetByID DB | Không | Loại (chống stale chủ động) |
| Multi-tenant SaaS | rcrdk, innkeeper | membership-role findFirst DB mỗi request | Không | Loại cả lớp |
| Session-store | FastAPI-Authentication | session revocable DB | Không | Loại cả lớp |
| Helpdesk self-hosted | douban/helpdesk, paw | OIDC external IdP / Django DB | Không | Loại (external-IdP / DB) |
| Rails | devise-jwt (khung) | Warden load user DB + revocation DB | Không | Loại cả lớp |
| Laravel | tymon/Sanctum (khung) | guard retrieveById DB | Không | Loại cả lớp |
| **Flask-JWT-Extended app nhỏ** | **placement-portal, pairs-api** | **role/is_admin trong JWT, KHÔNG tra DB** | **CÓ** | **near-miss** (thiếu endpoint đổi role) |

## Near-miss 1 — VIJAYAPANDIANT/placement-portal-application (10★, Flask, active)

- **C-JWT ✓**: `backend/app/utils/decorators.py` — `claims = get_jwt(); if claims.get('role') != role: return 403`,
  KHÔNG tra DB. `backend/app/routes/auth.py` login: `create_access_token(identity=str(user.id),
  additional_claims={'id':.., 'role': role, 'email':..})` — role nằm trong token.
- **C-SRC ✓**: admin-write idempotent trong `routes/admin.py`: `PUT /companies/{id}/approve`,
  `PUT /students/{id}/blacklist` (toggle), guard `@role_required('admin')`.
- **Thiếu transition (S6)**: KHÔNG endpoint nào cho admin đổi/hạ role user khác; role cố định lúc đăng ký. Chỉ có
  approve/deactivate/blacklist/delete = lớp vô hiệu/xoá (§3 LOẠI: re-login hỏng → D1 không có chứng chỉ mới).
- **Chạy tay suy từ code (chưa chạy máy)**:
  - A victim (role=admin) login → token cũ claim `role=admin`
  - B token cũ → `PUT /companies/{id}/approve` → dự đoán **200** (decorator đọc `claims['role']=='admin'`)
  - C token student → cùng call → **403**
  - D **(gãy ở đây)** không có endpoint hạ role admin → không tạo được transition
- **Kết luận**: nếu thêm một endpoint đổi role (vẫn login được) → đủ qualifier. Hiện: near-miss.

## Near-miss 2 — ozdemirozcelik/pairs-api (14★, Flask-JWT-Extended, active)

- **C-JWT ✓**: `services/resources/users.py` — `claims = get_jwt(); if not claims["is_admin"]: 401`, KHÔNG tra DB;
  dùng ở `UserRegister.post/put`, `UserList.get`, `User.get`, `User.delete`.
- **C-SRC ~**: admin-write `DELETE /users/<username>` (non-idempotent — ranh giới), `PUT /register`.
- **Thiếu transition (S6)**: user tạo bằng password; KHÔNG cơ chế đổi `is_admin` của user khác.
- **Chạy tay suy từ code**: A admin login → claim `is_admin=true`; B token cũ → `GET /users` → dự đoán 200;
  C token thường → 403; D không có endpoint set `is_admin=false` → gãy.
- **Kết luận**: cùng khuôn #1 — near-miss.

## Phụ lục — app 0★ hình-dạng-khớp (dưới sàn 5, Tier C tiềm năng nếu user nới sàn)

- `DevLifeCrisis/lessondeck` (0★): issue tự ghi "[SEC-006] HIGH: Stale JWT session — role/subscription change" (C-JWT).
- `kunal-ak23/rentaxis` (0★): "NextAuth JWT session never re-validates against the backend" (C-JWT).
- `NaderZico/ai-appointment-scheduler` (0★): commit "token carries only the user id" = fix bỏ role khỏi token → bản cha C-JWT.
(Chưa verify sâu code; dưới sàn 5 nên chưa xét đủ.)

## Phát hiện chính

Full-MR-A1 = giao điểm ba điều kiện hiếm cùng xảy ra: **(role trong token, không tra DB) × (có endpoint admin đổi role
user khác qua REST) × (account bị hạ vẫn login lại được)**. App in-band 5–2000★ thường chỉ có 1–2/3: admin-dashboard
re-resolve DB (có transition nhưng không C-JWT); app C-JWT nhỏ cố định role (C-JWT nhưng không transition). Đây là lý do
các target xác nhận (pyLoad, artifact-keeper, wagoe) ít — chúng rơi đúng giao điểm. Việc 37 app đều trượt, phân theo
ecosystem, bản thân là dữ liệu cho chương đánh giá: oracle bắt một lớp lỗi THẬT nhưng HIẾM.

## Ba lựa chọn cho user (tôi không tự chốt)

1. **Nới sàn** để nhận app 0★ hình-dạng-khớp (lessondeck/rentaxis/NaderZico) làm Tier C — cần verify code thêm.
2. **Chốt output** = bảng khảo sát ecosystem + 2 near-miss in-band (C-JWT thật) + phát hiện "MR-A1 hiếm" cho chương đánh giá.
3. **Giữ nguyên luật**, chấp nhận 0 qualifier in-band.
