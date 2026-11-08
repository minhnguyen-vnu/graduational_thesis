# artifact-keeper — lỗi phân quyền có trạng thái của vendor (#1821)

Số hiện tại: `docs/results.md` §1, §5.

## 1. App và lỗi

- `artifact-keeper/artifact-keeper`: kho artifact mã nguồn mở viết bằng Rust, 1.097 sao ngày 2026-10-01.
- Bản lỗi `e56d3aa7e2`: lúc đăng nhập, `is_admin` được ghi vào claim của JWT. Middleware đọc lại cờ này từ claim, không
  tra cơ sở dữ liệu (`backend/src/middleware/auth.rs:153`). Watermark đổi chứng chỉ chỉ gồm mật khẩu và TOTP. Admin bị
  hạ quyền vẫn giữ quyền admin tới khi token hết hạn (30 phút).
- Bản vá của vendor `e64cc5c608` (#1821): thêm cột `privileges_changed_at` (migration `131`) vào watermark. Token cấp
  trước lần hạ quyền nhận 401.
- Transition: `PATCH /api/v1/users/{id}` với `{"is_admin": false}` (`backend/src/api/handlers/users.rs:455`), không
  đòi xác thực lại.
- Cách chọn: tìm commit của vendor sửa lỗi quyền nằm trong token; #1821 mô tả đúng MR-A1 (`is_admin` đọc từ claim,
  không tra cơ sở dữ liệu).

## 2. Phần của ta

| Chỗ | Thay đổi | Lý do |
|---|---|---|
| Build | `docker-compose.thesis.yml` (backend chỉ phụ thuộc postgres, cổng 8080, `user: "0:0"`, tắt OpenSearch và Dependency-Track) | dựng stack tối thiểu trên máy tác giả |
| Build | `protoc` v29.3 trong `docker/Dockerfile.backend.dev` (dòng mốc `THESIS`) | image dev thiếu proto well-known types; image production đã có |
| Spec | bỏ `DELETE /users/{id}` (`m2-wave2-20261108/openapi-trimmed.json`, 389 op) | fuzzer xoá mất tài khoản test |

Logic app, lỗi, bản vá và phần còn lại của spec là của vendor. Bản đối chứng là bản vá của vendor.

## 3. Dựng và reseed

- Mã nguồn: `infra/artifact-keeper-target/src`, checkout `e56d3aa7e2` (bản lỗi) hoặc `e64cc5c608` (bản vá).
- Reseed trước mỗi lượt: `infra/em-results/artifactkeeper-20261001/reseed.sh full`. Script xoá volume DB, dựng lại
  postgres và backend, đổi mật khẩu `admin` (mật khẩu mặc định bị khoá thao tác ghi), tạo `victim` (`is_admin=true`) và
  `viewer` (`is_admin=false`). Đổi giữa hai commit phải xoá volume: DB của bản vá đã lên migration 131, bản lỗi thiếu
  migration này và backend thoát.
- Tài khoản trong file auth (`m2-wave2-20261108/artifactkeeper-auth-proxied.yaml`): `viewer`, `operator` (đăng nhập
  bằng `admin`), `victim`; mật khẩu `Thesis-Pass-1234`.
- EvoMaster gọi qua proxy ghi traffic `capture_proxy.py` (cổng 8212, chuyển tới 8080) để đếm số lần đăng nhập của
  từng tài khoản.
- Cờ: `docs/results.md` §0. Harness: `m2-wave2-20261108/ak_vuln.sh`, `ak_fixed.sh`.

## 4. Kiểm tay (`artifactkeeper-20261001/handcheck-*.log`)

| Bước | Bản lỗi | Bản vá |
|---|---|---|
| `victim` đăng nhập, ghi `POST /api/v1/users` bằng token cũ | 200 | 200 |
| `viewer` cùng lời gọi | 403 | 403 |
| admin `PATCH /api/v1/users/{victim}` `{"is_admin": false}` | 200 | 200 |
| `victim` đăng nhập lại, cùng lời gọi bằng token mới | 403 | 403 |
| cùng lời gọi bằng token cũ | **200** | 401 |

## 5. Chạy máy

Bộ ba công cụ tự dựng, jar M2: source `POST /api/v1/admin/analytics/snapshot`, victim `victim`, operator `operator`,
transition `PATCH /api/v1/users/{id}`. Bản lỗi `200/200/200`, 970 ở 5/5 lượt. Bản vá: token cũ nhận 401, bộ ba VOID,
0/3 báo vi phạm và 0 bộ ba (`docs/results.md` §1).
