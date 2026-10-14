# Tìm app công khai có khả năng dính MR-A1 — phiên overnight 2026-10-07

Mục đích: tìm app/repo công khai mà oracle 970 `SECURITY_STATEFUL_AUTHORIZATION` của ta có khả năng bắt được lỗi.
Chỉ kiểm tay (đọc repo/diff/code qua web + GitHub API). Không dựng, không chạy code. Kết quả mong đợi không ghi trước.

Folder này KHÔNG được link vào `CLAUDE.md` (theo yêu cầu user: tránh bị flag ở phiên opus 5.5). Đây là kho kết quả
của riêng phiên overnight.

## File

- `STATE.md` — trạng thái phục hồi được: heartbeat, hàng đợi truy vấn, nhật ký mọi candidate đã xét (kể cả loại),
  đếm qualifier, luật dừng, lệch luật. Đây là mỏ neo để resume sau khi hết quota.
- `FINDINGS.md` — chỉ các qualifier: app thật sự có khả năng 970 nổ, mỗi app một mục chi tiết.

## Luật áp dụng (chi tiết: `infra/analysis/heldout-small-apps.md` §1, §13, §17)

Lọc theo thứ tự, dừng ở luật trượt đầu:

- **S10 (hợp đồng)**: có commit/PR đã merge, hoặc issue có maintainer xác nhận là lỗi, mô tả đúng lớp — admin thu hẹp
  role/quyền/nhóm của một user khác; phiên hoặc token có từ trước vẫn giữ quyền cũ. LOẠI: logout, đổi mật khẩu,
  xoá/vô hiệu user (đăng nhập lại hỏng nên không có chứng chỉ mới), lỗi chéo tài khoản (BOLA/BFLA).
- **S7′ (sao)**: `5 ≤ sao < 2000`, **ưu tiên xét từ ít sao lên**. 2000 là trần; mục tiêu là app công khai ít người
  dùng / ít đóng góp. Sàn 5 sao (user hạ từ 10 xuống 5, 2026-10-07 ~22:47) — CHỈ cho **app active thật**: có push gần
  đây, là application chạy được (không phải repo rác/bỏ hoang/throwaway, không phải lib/CLI/frontend).
- **S1**: mã nguồn mở, chưa có trong `infra/`, chưa từng là target (danh sách loại trong STATE.md).
- **S2**: dựng được không cần dịch vụ trả phí/IdP (image hoặc Dockerfile/compose, hoặc chạy bằng công cụ chuẩn của
  stack). Thư viện / CLI / operator / chỉ-frontend trượt.
- **S3**: có spec OpenAPI/Swagger (file hoặc framework tự phục vụ).
- **S4**: dưới 200 operation.
- **S5**: đăng nhập user/mật khẩu qua một endpoint, trả token hoặc cookie. Captcha / rate-limit chặt / API-key / OAuth
  / chứng chỉ trượt.
- **S6**: ≥ 2 mức quyền, admin đổi vai trò user khác bằng một REST JSON request; user bị hạ đăng nhập lại được.
- **S8**: endpoint bị chặn trả 403 (không phải 200-với-mã-trong-thân).
- **S9**: Dockerfile/mã khởi động không tải/chạy mã từ xa.

Hình dạng để 970 nổ (§17), xét trên code authz + diff:

- **C-JWT**: bản dính ủy quyền từ claim trong token (role/is_admin/quyền), KHÔNG tra lại DB/session mỗi request.
  Fix kiểu "invalidate sessions / flush cache" = authz dựa DB → KHÔNG nổ. Fix kiểu "revoke/invalidate TOKENS/JWTs"
  hoặc "recheck DB" = bản dính tin token → đúng hình dạng.
- **C-SRC**: có một admin-write **idempotent** (PUT upsert / PATCH / thao tác lặp được) dùng làm source; không chỉ
  create non-idempotent (ranh giới wagoe: POST tạo → replay 409).
- **C-STEP**: transition (đổi role/quyền) KHÔNG đòi step-up/MFA re-proof (ranh giới orkestra).

Qualifier = qua S1–S10 + C-JWT + C-SRC + C-STEP, và nhìn code suy ra được chuỗi token-cũ=ALLOWED / token-mới=DENIED.

## Luật dừng

Dừng khi **đủ 10 qualifier** HOẶC **giờ local ≥ 2026-10-08 12:00**.
