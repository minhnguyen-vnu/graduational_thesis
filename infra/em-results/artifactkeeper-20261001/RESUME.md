# RESUME — artifact-keeper 970 hunt (ghi 2026-10-01, bàn giao giữa phiên)

Mục tiêu: xác nhận oracle 970 (MR-A1) trên một app công khai đáng tin, bằng máy. artifact-keeper là ứng viên sạch
nhất (xem `infra/analysis/heldout-small-apps.md` §17). Nền tảng, ba near-miss trước: §14 wagoe, §16 orkestra.

## Vì sao artifact-keeper
- Repo `artifact-keeper/artifact-keeper` (1097★, Rust+Postgres, "drop-in Artifactory"). Bản dính `e56d3aa7e2`
  (đang checkout), bản vá `e64cc5c608` (#1821/#1827).
- C-JWT xác nhận ở code: `AuthContext.is_admin = claims.is_admin` (`backend/src/api/middleware/auth.rs:153`),
  `require_admin()` dùng nó. Bản dính không bump watermark credential-change khi đổi is_admin → token cũ giữ admin tới
  khi hết hạn (30'); token mới mint is_admin=false → bị từ chối. Hình dạng credential-specific → 970 kỳ vọng nổ.
- Transition = `PATCH /api/v1/users/{id} {"is_admin":false}`. Source/follow-up thử nghiệm = `POST /api/v1/users` (create,
  require_admin, non-idempotent — dùng cho hand-check). Source idempotent cho oracle: `update_permission`
  (`permissions.rs`), `assign_role`, hoặc write require_admin khác.

## Hạ tầng đang chạy (docker, độc lập phiên)
- `artifact-keeper-dev-db` (postgres:18, host port 30432) — healthy.
- `artifact-keeper-dev-backend` (rust:1.96 + cargo-watch, host port 8080) — ĐANG COMPILE lần đầu (~20–40').
- Override tối thiểu: `infra/artifact-keeper-target/src/docker-compose.thesis.yml` (backend chỉ phụ thuộc postgres;
  bỏ expose 9090 vì host đã chiếm; tắt opensearch/dtrack; set AK_WEBHOOK_SECRET_KEY).
- Lên lại nếu cần: `cd infra/artifact-keeper-target/src && docker compose -f docker-compose.local-dev.yml -f docker-compose.thesis.yml up -d backend`

## Bước tiếp theo (thứ tự)
1. Chờ compile xong. Kiểm: `curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/health` ra != 000.
   Hoặc đọc `build2.log`. Nếu container exit: `docker logs --tail 50 artifact-keeper-dev-backend`.
2. Chạy hand-check: `bash infra/em-results/artifactkeeper-20261001/handcheck.sh | tee handcheck-vuln.log`.
   Kỳ vọng bản dính: [F] REPLAY token-cũ sau demotion = 2xx (lỗi), [E] token-mới = 403, [B]=2xx, [C]=403.
   Nếu đúng → MR-A1 thật, credential-specific (khác orkestra cache 60s).
3. (Tùy chọn) bản vá: `cd .../src && git checkout e64cc5c608` → cargo-watch rebuild → chạy lại hand-check.
   Kỳ vọng: token-cũ bị từ chối (watermark privileges_changed_at). Cho cột 0 FP.
4. Chạy máy EvoMaster (jar ER-06b48c30), `infra/em-config/artifactkeeper-auth.yaml` (3 tài khoản admin/victim/viewer),
   `--blackBox --bbSwaggerUrl http://localhost:8080/<openapi path> --bbTargetUrl http://localhost:8080
   --useExperimentalOracles true`. Reseed giữa seed = re-promote victim is_admin=true. Logback builder-debug để xem
   builder chọn transition/source. Rủi ro còn mở: builder có chọn được source idempotent require_admin không (giống
   wagoe §14) — chỉ chạy mới biết.

## Bootstrap (trong handcheck.sh)
Admin mặc định: username `admin` / password `admin`, must_change_password=true → đổi qua
`POST /api/v1/users/{id}/password`. Tạo victim (is_admin=true) + viewer (is_admin=false), password `Thesis-Pass-1234!`.
Login `POST /api/v1/auth/login {username,password}` → `access_token` (Bearer, 30').

## Lưu ý model
Việc hand-check/oracle mang hình dạng "replay credential cũ vượt phân quyền". Opus 4.8 làm được; Opus 5.5 có thể từ
chối (safety classifier). Đây là nghiên cứu an toàn hợp lệ trên app test cục bộ của chính tác giả cho luận văn.
