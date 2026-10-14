# fastschema — dựng + kiểm tay MR-A1

Qualifier 4 của `infra/analysis/mra1-candidates-20261007/FINDINGS.md`. Nâng từ Tier B (đọc code) lên Tier B **đã quan sát**. CHƯA chạy EvoMaster. CHƯA tìm hợp đồng vendor → vẫn Tier B.

## Phiên bản

- Source clone: `infra/fastschema-target/fastschema`, nhánh `develop`, HEAD `813349976c7cf4a884a995f6fcad9aace08b1541` (2026-06-23).
- App chạy: image chính thức `ghcr.io/fastschema/fastschema@sha256:e1ce4c3f45e9c0602124fcc2d5aedba3287bd7a23929c116fb18144640cc2bba`, created 2026-07-11. Dockerfile vendor wget binary release lúc build image của họ (không phải tôi chạy); tôi dùng image publish sẵn → S2 (image chính thức) + S9 qua.
- SQLite. Lệch độ trung thực: image release mới hơn develop HEAD đã clone; kiến trúc auth quan sát khớp.

## Dựng

- `docker run -d -p 8008:8000 -v fastschema_data:/fastschema/data ghcr.io/fastschema/fastschema:latest`.
- **Named volume** bắt buộc: bind-mount `-v ./data` trên macOS làm setup 500 `sqlite3: disk I/O error`; named volume hết lỗi.
- Setup token in ra log container; `POST /api/setup {token,username,email,password}` → `{"data":true}`. Setup tạo 3 role: Admin (root=true), User, Guest; user setup nhận Admin, active=true (`services/tool/setup.go`).
- Bootstrap qua REST: tạo `victim` (role Admin), `plain` (role User) bằng `POST /api/content/user`.

## Kiểm tay — `handcheck.sh`, log `handcheck.log`

C-JWT thấy ngay trong token: payload JWT mang `user.role_ids`. SOURCE `PUT /api/role/{id}` (root-only, idempotent). TRANSITION `PUT /api/content/user/{victimId} {roles:[{id:UserId}]}` (thay membership, không cộng dồn — response trả roles=[User]).

| Bước | role_ids trong token | Lời gọi | Mã |
|---|---|---|---|
| Neg-control plain | [User] | PUT /api/role | 403 |
| A/B source victim_old | [Admin] | PUT /api/role | 200 |
| D transition | — | admin PUT content/user victim→[User] | 200 |
| E bug victim_old (cùng token) | [Admin] (token không đổi) | PUT /api/role | 200 |
| F D1 victim re-login | [User] | PUT /api/role | 403 |

→ token-cũ=200 (ALLOWED) / token-mới=403 (DENIED), neg=403. Token cũ giữ `role_ids=[Admin]` sau khi DB đã đổi sang [User]; `GetRolesFromIDs` (auth.go:170) resolve role từ claim, không re-fetch membership → **MR-A1 quan sát được**. Tồn dư credential-specific.

## Mở

- S4 (đếm op) chưa đo. Chưa chạy EvoMaster (oracle tự dựng bộ ba trên schema động của fastschema chưa kiểm).
