# hrm (quuuuj/hrm, Spring Boot HRM) — dựng + kiểm tay MR-A1

Qualifier 2 của `infra/analysis/mra1-candidates-20261007/FINDINGS.md`. Nâng từ Tier B (đọc code) lên Tier B **đã quan sát**. CHƯA chạy EvoMaster. CHƯA tìm hợp đồng vendor → vẫn Tier B.

## Phiên bản

- Source clone: `infra/hrm-target/app`, HEAD `1ef6abc57540463d421cd800f7fc9f21db649384`, remote `github.com/quuuuj/hrm.git`.
- Backend `hrm-server` (Spring Boot 3.4 + MyBatis-Plus + Spring Security + JJWT + Flowable). Build jar trong container `maven:3-eclipse-temurin-17` (Lombok không sinh getter trên host Java 21), chạy jar bằng Java 21 host trên :8888.
- Middleware: `hrm-mysql` (db `hrm` + `hrm_flowable`, seed từ `db/mysql/*.sql`), `hrm-redis` (captcha), `hrm-postgres` pgvector (`hrm_kb`), `hrm-minio` (ảnh `bitnamilegacy/minio:2025.7.23-debian-12-r5`; `minio/minio:latest` trên Docker Hub hỏng). MinIO bắt buộc lúc boot (`MinioStorageService` re-throw nếu init lỗi).
- `.env`: `JWT_SECRET` phải base64 (`JwtUtil`: `Keys.hmacShaKeyFor(Decoders.BASE64.decode(secret))`), sinh bằng `openssl rand -base64 48`.

## Dựng

- Login cần captcha: `GET /validate/code` ghi captcha vào Redis key `validate:code` (có TTL); `POST /login/{captcha}` body `{code,password}` so captcha với path param (`LoginService:45,49`), auth bằng `UsernamePasswordAuthenticationToken(code,password)`, set cookie `token` (JWT HS256). Token dùng lại qua `Authorization: Bearer` (`JwtAuthenticationFilter`: Header → query `token` → cookie).
- Mật khẩu admin seed là bcrypt không rõ plaintext (`sys_staff` id=1 code='admin', `$2a$10$hPdTHgqX…`). Target tự gieo → reset sang `Admin123!` bằng hash `$2a$` tự sinh (`bcrypt.hashpw`, rounds 10), `UPDATE hrm.sys_staff SET pwd=… WHERE id=1`.
- Staff mới qua `POST /staff {name,deptId}` (`system:staff:add`): service tự set password = `staff.default-password` = `123`, code = `staff_<id>` (`StaffService.add:65-80`).

## Kiểm tay — `handcheck.sh`, log `handcheck.log`

JWT (HS256) mang claim `permissions` (chuỗi quyền phẩy) + `staffId`. `JwtAuthenticationFilter:88` dựng authority thẳng từ claim `permissions`, KHÔNG tra DB mỗi request (comment `:25`) = C-JWT. Guard `@PreAuthorize("hasAnyAuthority('…')")`.

- SOURCE `PUT /role {id,remark}` guard `permission:role:edit` (`RoleController:58-60`). Chỉ role 1 có quyền này → discriminator sạch.
- TRANSITION `POST /staff/set/{id} [roleIds]` guard `system:staff:set_role` (`StaffController:99-101`).
- Victim gán role 1 (high, có role:edit) → admin hạ sang role 9 (low, không có). Plain gán role 9 = neg control.

**Denial là body-code, không phải HTTP status.** Request thiếu quyền trả **HTTP 200** + body `{"code":1300,"message":"不好意思，你没有此权限"}`. ALLOWED = body code 200, DENIED = body code 1300.

| Bước | token (role:edit) | Lời gọi | body code |
|---|---|---|---|
| Neg-control plain | role 9, role:edit=False | PUT /role | 1300 |
| Source victim_old | role 1, role:edit=True | PUT /role | 200 |
| Transition | — | admin POST /staff/set/victim [9] | 200 |
| Follow-up victim_old (cùng token) | role 1, role:edit=True | PUT /role | 200 |
| D1 victim_new (re-login) | role 9, role:edit=False | PUT /role | 1300 |

→ token-cũ (role:edit) sau khi DB hạ role victim sang 9 vẫn code 200; token-mới code 1300; neg code 1300. Token cũ giữ `permission:role:edit` trong claim sau khi membership đổi → **MR-A1 quan sát được**.

## Mở / mong manh

- **Oracle 970 hiện tại không nổ trên hrm nguyên trạng.** 970 map DENIED = HTTP 403 (§3). hrm báo từ chối bằng HTTP 200 + body code 1300, nên EvoMaster sẽ thấy toàn 2xx và không phân biệt được → bộ ba VOID/không nổ. Đây đúng hạn chế đã khai ở CLAUDE.md §6 "mã từ chối chưa cấu hình được". hrm là bằng chứng một app C-JWT có MR-A1 thật mà oracle bỏ lỡ chỉ vì quy ước mã từ chối.
- Token access sống 900s (claim exp−iat). Bộ ba kiểm tay xong <1s.
