# lumiverb — kết quả kiểm tay + probe P2f (ghi 2026-10-16, held-out)

Target `bubbafat/lumiverb` (MIT, FastAPI). Bản dính `6c3998f06747`, bản vá `6210c88923c6` (#CK token_version).
Jar `evomaster-P2f-64ee8ffc.jar`. Postgres pgvector:pg18 cổng 5433. Spec 177 operation (< 200, S4 qua).
Lệch luật đã khai: nới `login_limiter`/`forgot`/`reset` lên 1e8 (`rate_limit.py`, chỉ hằng số rate-limit, không đụng
auth/role); vision key giả; spec trung thực thêm enum `role=[admin,editor,viewer]` cho black-box (app nguyên vẹn);
reseed mỗi lượt (`reseed.sh`: drop control_plane + migrate + bootstrap tenant + victim/operator/viewer).

## Kiểm tay MR-A1 trên bản dính — NỔ (lỗi có thật), `handcheck-vuln.log`
source token-cũ(admin) `POST /v1/users` 201; viewer 403; operator `PATCH /v1/users/{victim}{role:viewer}` 200;
victim login mới role=viewer `POST /v1/users` 403; **REPLAY token cũ(claim admin) 201** (vi phạm MR-A1); token cũ còn
`PATCH` tự nâng lại admin 200. Cơ chế: middleware bản dính `role=claims["role"]` (tin claim, không tra DB). Bất biến
"last-admin" (409) chặn hạ admin cuối → cần 2 admin (operator+victim).

## Probe P2f (seed 1, maxTime 600s, extraPhase 0.6, rate 120) — đều FN (0 fault 970)
| Lượt | Spec | Transition | Kết quả |
|---|---|---|---|
| c (`em-results/lumiverb-probe-20261016c`) | live (`role` không enum) | black-box | 0 bộ ba; reduced role values `[read,member,guest]` không khớp vocab; transition 400 |
| d (`…20261016d`) | trung thực (enum role) | black-box | 0 bộ ba; reduced role values có `[viewer,editor]` nhưng builder dựng mảng/cờ, không set scalar → UNCONFIRMED (re-login thấy quyền còn) |
| e (`…20261016e`) | live | declared `PATCH /v1/users/{user_id} user_id=<victim> role=viewer` | 0 bộ ba; transition trả **404** (không map được `<victim>`→ULID `usr_…`) |

Soát "970" trong test/report.json: 0 fault `SECURITY_STATEFUL_AUTHORIZATION` (khớp "970" chỉ là `endLine` và chữ số
ngẫu nhiên). Nguồn OK (builder tìm được `PUT /v1/ai/jobs/{job}` victim 2xx).

## Hai ranh giới FN (builder EvoMaster v6.1.1, không phải lỗi oracle)
1. **Trường role là scalar enum string** (`{"role":"viewer"}`). Builder dựng demotion kiểu mảng `roles`
   (vampi/reports) hoặc cờ boolean `is_admin` (artifact-keeper/AF2), không set một trường scalar enum → PATCH không
   thực sự hạ victim → C4/D1 re-login thấy quyền chưa mất → UNCONFIRMED.
2. **Victim định danh bằng path param ULID** `usr_01M…`; builder/declared-transition không map tài khoản auth →
   id path → `PATCH /v1/users/{user_id}` trả 404 (cùng lớp bamf §12, giới hạn v6.1.1).

Kiểm tay xác nhận lỗi thật + oracle đủ điều kiện bắt; builder v6.1.1 chưa với tới. Xếp loại: FN held-out trên app
công khai vendor-confirmed. Datapoint nổ công khai vẫn là pyLoad + artifact-keeper.

## Trạng thái môi trường (đang để nguyên chờ user quyết)
Container `lumiverb-postgres` (5433) + server uvicorn (8000, bản dính) đang chạy. Bản vá `6210c88` chưa dựng/kiểm.
