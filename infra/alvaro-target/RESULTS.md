# alvaromrveiga/ecommerce-backend — dựng + kiểm tay MR-A1

Qualifier 6 của `infra/analysis/mra1-candidates-20261007/FINDINGS.md`. Nâng từ Tier B (đọc code) lên Tier B **đã quan sát**. CHƯA chạy EvoMaster. CHƯA tìm hợp đồng vendor → vẫn Tier B.

## Phiên bản

- Source clone: `infra/alvaro-target/app`, HEAD `dbd0cd10e9a71dd1775f67f8e6036904e127546c` (2022-06-09, dự án cũ). Build từ source → khớp SHA đã clone.
- NestJS 8/9 + Prisma + Postgres. Không docker-compose/Dockerfile/seed trong repo.

## Dựng + lệch luật đã khai

- **Node 25 không chạy được** app này: `(0, util_1.isObject) is not a function` — NestJS 2022 dùng `util.isObject` đã bị Node 25 gỡ. → chạy app trong container **node:18**.
- `npm install` host trượt ERESOLVE (passport 0.6 vs @nestjs/passport 8.2) → `--legacy-peer-deps`. Native module (prisma engine) phải cho linux → cài trong node:18.
- Thiếu `multer` (code import trực tiếp, không được hoist) → cài bổ sung `npm install multer`.
- Postgres 16 container riêng (`alvaro-pg`), network `alvaro-net`; `.env` DATABASE_URL trỏ `alvaro-pg:5432`. `prisma migrate deploy` áp 10 migration tạo schema.
- **Bootstrap admin qua DB** (lệch luật — tiền lệ "bootstrap qua REST, không chọc DB" không áp được): app KHÔNG có REST path tạo admin đầu (register chỉ ra role USER; `PATCH /user/role` đòi @IsAdmin). Dùng `UPDATE "User" SET role='ADMIN'` cho admin+victim. Đây là bootstrap, không phải bước của bộ ba.

## Kiểm tay — `handcheck.sh`, log `handcheck.log`

Token mang claim `userRole` (`auth.service.ts:42` payload `{sub, userRole}`, access 15m). SOURCE `PATCH /category/:id {name}` (@IsAdmin, idempotent). TRANSITION `PATCH /user/role {email, role}` (@IsAdmin). victim register rồi nâng ADMIN qua DB.

| Bước | userRole token (sub) | Lời gọi | Mã |
|---|---|---|---|
| Neg-control plain | USER | PATCH /category/{id} | 403 |
| A/B source victim_old | ADMIN (d5115…) | PATCH /category/{id} | 200 |
| D transition | — | admin PATCH /user/role victim→USER | 200 |
| E bug victim_old (cùng token) | ADMIN (d5115…) | PATCH /category/{id} | 200 |
| F D1 victim re-login | USER (d5115…) | PATCH /category/{id} | 403 |

→ token-cũ (userRole ADMIN)=200 / token-mới (userRole USER)=403, neg=403. `roles.guard.ts` đọc `userRole` từ `request.user` (claim), không tra DB; `access-jwt.strategy validate` trả role từ token. Access token 15m giữ userRole=ADMIN sau khi DB đổi sang USER → **MR-A1 quan sát được**. (Refresh re-đọc role từ DB — `auth.service.ts:67` — nhưng access token cũ vẫn sống tới hết hạn.)

## Mở

- Chạy trên node:18 (không phải môi trường mặc định của máy). Chưa chạy EvoMaster.
