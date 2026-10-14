# alvaro held-out — giao thức chạy máy (ghi 2026-10-14, trước lượt chạy đầu)

App held-out thứ 3 (Qualifier 6, `infra/analysis/mra1-candidates-20261007/FINDINGS.md`, hạng 3). MR-A1 kiểm tay XÁC NHẬN, chưa chạy EvoMaster.

## Target

- `alvaromrveiga/ecommerce-backend`, build từ source HEAD `dbd0cd1`, NestJS 8/9 + Prisma + Postgres.
- Chạy: app trong container **node:18** (`alvaro-app`, Node 25 gỡ `util.isObject`), Postgres 16 (`alvaro-pg`) trên network `alvaro-net`, port 3000. node_modules build sẵn 10-09 (mount).
- Spec: `/api-json` công khai, OpenAPI **3.0.0**, 30 op / 19 ghi / 20 path, **không vòng tròn $ref** (khác fastschema). Lưu `openapi.json`.
- Login `POST /login {email,password}` → `accessToken`; JWT mang claim `userRole`, access 15m.
- SOURCE `PATCH /category/{id}` (@IsAdmin, idempotent; EvoMaster tự POST /category rồi PATCH). TRANSITION `PATCH /user/role {email,role}` (@IsAdmin, **hạ victim theo email**).
- Tài khoản: operator=admin@test.com (ADMIN), victim=victim@test.com (ADMIN), low=plain@test.com (USER), mật khẩu `Passw0rd1`. Denial 403.
- MR-A1 kiểm tay live (`handcheck.sh`, dbd0cd1): token-cũ(ADMIN)=200 sau hạ / token-mới(USER)=403 / neg=403.

## Jar + chế độ

`evomaster-P2e-6ae8277b.jar`. D1 tắt, `useExperimentalOracles`, `extraPhaseBudgetPercentage 0.25`, rate 600, maxTime 600s, qua proxy ghi request (:8212→:3000).

## Lệch luật đã khai

1. **Chạy trong container node:18** (môi trường mặc định máy gỡ `util.isObject`); npm install `--legacy-peer-deps` + bổ sung `multer` (đã làm 10-09).
2. **Bootstrap admin qua DB** (`reseed.sh`): app không có REST path tạo admin đầu (register chỉ ra USER). Reseed = register admin/victim/plain (POST /user) + `UPDATE "User" SET role='ADMIN'` cho admin+victim, `='USER'` cho plain. Marker `RESEED_OK victim_role=ADMIN operator_role=ADMIN`. Bootstrap, không phải bước bộ ba. Kiểm chạy tay: PASS.
3. **Strip 4 op phá-chủ-thể** (`strip_spec.py` → `openapi-nokill.json`): `PATCH /user`, `DELETE /user`, `POST /logout`, `POST /logoutAll` (tránh EvoMaster tự xoá/đổi credential của tài khoản cấu hình). Giữ 26 op; source + transition + login còn nguyên.
4. **Không có bản vá** → không arm 0-FP; mọi 970 soát tay. **Chỉ arm "không reset"**.

## Rủi ro đã biết (ghi trước lượt chạy)

- **Transition hạ victim theo EMAIL** (`PATCH /user/role {email,role}`) — builder phải nhận `email` trong body là tham số định danh victim. Đây đúng **lớp FN bamf** (builder không nhận `{email}`). Auto nhiều khả năng FN. Phép đo, không ghi kết quả mong đợi.
- Arm `declared` biểu diễn được (body phẳng): `--statefulAuthzTransition "PATCH /user/role email=victim@test.com role=USER"` — dùng xác nhận reachable nếu auto FN (như raouf).

## Đếm / dừng sớm / held-out

Như raouf. Lộ bug builder (email param) → ghi FN, KHÔNG sửa builder.
