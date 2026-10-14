# magic (polterguy/magic) — dựng + kiểm tay MR-A1

Qualifier 1 của `infra/analysis/mra1-candidates-20261007/FINDINGS.md`. Nâng từ Tier B (đọc code) lên Tier B **đã quan sát** (dựng + kiểm tay). CHƯA chạy EvoMaster. CHƯA tìm hợp đồng vendor → vẫn Tier B.

## Phiên bản

- Source clone: `infra/magic-target/magic`, HEAD `aefa6685639cc608fab5774a91268a7ef273cd5b` (2026-09-29 "Update Version.cs").
- App chạy: image chính thức `servergardens/magic-backend@sha256:a55bc889198e6bdd05dbcdea4c86277e6f6199578bd6e20b2e33909789f277df`, created 2026-09-29 (cùng ngày HEAD). docker-compose.yml dùng image publish sẵn, không build từ source; S2 (image chính thức) + S9 (không fetch mã lúc dựng) qua.
- Lệch độ trung thực: app chạy là image `:latest`, không build lại từ SHA đã clone. Kiến trúc auth quan sát được (role-in-claim, token cũ sống sót) khớp code đã đọc ở HEAD.

## Dựng

- `docker compose -f magic/docker-compose.yml up -d backend`, cổng 4444. healthz 200 sau ~6s.
- Setup: `GET /magic/system/auth/authenticate root/root` (secret mặc định <50 ký tự) → ticket; `POST /magic/system/config/setup {password, subscribe:false}` đổi secret thành chuỗi mạnh. `subscribe:false` để chặn `http.post https://ainiro.io/...` trong setup.post.hl.
- Bootstrap qua REST (không chọc DB): tạo `victim`, `plain`; gán role `root` cho victim; tạo role `src_role` làm đích source idempotent.

## Kiểm tay — `handcheck.sh`, log `handcheck.log`

SOURCE `PUT /magic/system/magic/roles {name,description}` (guard root, 202/404). TRANSITION `DELETE /magic/system/magic/users_roles {role,user}` (guard root, arg qua query string). Token mang claim `role` (giải mã JWT: `{"unique_name":"root","role":"root",...}`).

| Bước | Lời gọi | Mã | Nghĩa |
|---|---|---|---|
| Neg-control | plain (không root) → PUT roles | 403 | instrument tạo được DENIED |
| A/B source | victim_old (claim root) → PUT roles | 202 affected:1 | ALLOWED |
| D transition | admin DELETE users_roles root/victim | 200 affected:1 | hạ quyền victim |
| E bug | victim_old **cùng token** → PUT roles | 202 affected:1 | token cũ vẫn qua |
| F D1 | victim login lại (token mới) → PUT roles | 403 | token mới bị từ chối |

Token mới ngắn hơn token cũ (181 vs 200 ký tự) vì mất claim `root`.

→ token-cũ=202 (ALLOWED) / token-mới=403 (DENIED), source idempotent, transition không step-up → **MR-A1 quan sát được trên app chạy**. Tồn dư credential-specific (trong JWT cũ), khác cache dùng chung (orkestra §16); source idempotent khác wagoe §14. Cùng hình dạng artifact-keeper §18.

## Mở

- S4 (đếm op spec thật) chưa đo — cần khi định cỡ ngân sách nếu chạy EvoMaster.
- Chưa chạy EvoMaster: chưa biết oracle 970 có tự dựng được bộ ba trên magic không (lexicon path/param, nhận diện field).
