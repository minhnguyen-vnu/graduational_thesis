# bcms/cms (BCMS headless CMS) — dựng + kiểm tay MR-A1

Qualifier 3 của `infra/analysis/mra1-candidates-20261007/FINDINGS.md`. Nâng từ Tier B (đọc code) lên Tier B **đã quan sát**. CHƯA chạy EvoMaster. CHƯA tìm hợp đồng vendor → vẫn Tier B.

## Phiên bản

- Source clone: `infra/bcms-target/app`, HEAD `d0e643d3269c27f20f57b23dfed4b45655a465fb` (2026-06-25). Build từ source (Dockerfile.backend.dev, node:20-slim) → khớp SHA đã clone.
- MongoDB 7 + backend (Fastify/TS). Node 25 host không chạm tới (backend build+chạy trong container node:20).

## Dựng

- `setup.ts` chỉ tạo thư mục + `.env` rỗng; tôi tạo tay (db, uploads, backups, backend/logs,... + `backend/.env` rỗng + `backend/custom-package.json`={}). `.env` rỗng là đủ: `config.ts` default DB_URL=`mongodb://test:test1234@db:27017/admin` (khớp compose), jwtSecret='secret', jwtExpIn=60000 (60s).
- `docker-compose.override.yml` (của tôi) publish backend 8085→8080, bỏ ui/proxy (proxy mặc định 8080 đụng reports-api của luận văn). `docker compose up -d --build db backend`.
- Admin đầu: backend in `Server token: <128hex>` lúc start (one-time); `POST /api/v4/auth/signup-admin {serverToken, email, password, firstName, lastName}` tạo ADMIN. Sau đó mainadmin tạo victim(ADMIN), plain(USER), target(USER) qua `POST /api/v4/user/create` (ADMIN-only).

## Kiểm tay — `handcheck.sh`, log `handcheck.log`

Token BCMS JWT (HS256) payload mang `rls` (mảng tên role) + `userId`. SOURCE+TRANSITION cùng endpoint `PUT /api/v4/user/update {_id, role?}` (guard ['ADMIN']). Bộ ba chạy nhanh (<1s) trong cửa sổ token 60s.

| Bước | rls token (uid) | Lời gọi | Mã |
|---|---|---|---|
| Neg-control plain | ['USER'] | PUT /user/update target | 403 |
| A/B source victim_old | ['ADMIN'] (…d8a) | PUT /user/update target | 200 |
| D transition | — | mainadmin PUT /user/update victim→USER | 200 |
| E bug victim_old (cùng token) | ['ADMIN'] (…d8a) | PUT /user/update target | 200 |
| F D1 victim re-login | ['USER'] (…d8a) | PUT /user/update target | 403 |

→ token-cũ (rls ADMIN)=200 / token-mới (rls USER)=403, neg=403. `JWTManager` so role yêu cầu với claim `rls`, không tra DB (`manager.ts:154`). Token cũ giữ `rls=[ADMIN]` sau khi DB đổi role victim sang USER → **MR-A1 quan sát được**.

## Mở / mong manh

- Token mặc định 60s: bộ ba phải xong trong 60s kể từ victim login. Kiểm tay script OK (<1s); khi chạy EvoMaster, bước source→transition→follow-up phải nằm trong 60s nếu không token cũ hết hạn → 401 INCONCLUSIVE (không FP). Chưa chạy EvoMaster.
