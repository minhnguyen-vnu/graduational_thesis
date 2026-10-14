# fastschema held-out — giao thức chạy máy (ghi 2026-10-14, trước lượt chạy đầu)

App held-out thứ 2 của campaign (Qualifier 4, `infra/analysis/mra1-candidates-20261007/FINDINGS.md`). Lỗi MR-A1 kiểm
tay XÁC NHẬN, chưa chạy EvoMaster. Thứ hạng 2 (token 7 ngày, tự serve OpenAPI).

## Target

- `fastschema/fastschema`, image chính thức pin digest `sha256:e1ce4c3f…cc2bba` (khớp kiểm tay 10-09, `infra/fastschema-target/RESULTS.md`).
- `docker run -d --name fastschema -p 8008:8000 -v fastschema_data:/fastschema/data <img>`. SQLite, named volume bắt buộc (bind-mount lỗi I/O trên macOS).
- Spec: `/docs/openapi.json` **sau auth** (401 nếu không token), OpenAPI **3.1.0**, 97 op / 66 ghi / 67 path. Fetch bằng token admin ra `openapi.json`, dùng `file://`.
- Login `POST /api/auth/local/login {login,password}` → `data.token`; JWT mang `user.role_ids`.
- SOURCE `PUT /api/role/{id}` (root-only, idempotent). TRANSITION `PUT /api/content/user/{victimId} {roles:[{id:UserRoleUUID}]}` (thay membership m2m).
- Tài khoản: operator=admin (Admin/root, làm transition), victim=victim (Admin, bị hạ), low=plain (User). Denial 403.
- MR-A1 kiểm tay live (`handcheck.sh`, HEAD 8133499): token-cũ(Admin)=200 sau hạ / token-mới(User)=403 / neg=403.

## Jar

`evomaster-P2e-6ae8277b.jar` (sha256 `6ae8277b…c751e`). Cùng jar, cùng chế độ như raouf: D1 tắt, `useExperimentalOracles`,
`extraPhaseBudgetPercentage 0.25`, rate 600, maxTime 600s, qua proxy ghi request (`capture_proxy.py` :8212→:8008).

## Lệch luật đã khai

1. **Image publish sẵn (digest pin) mới hơn develop HEAD đã clone** — kiến trúc auth quan sát khớp (`RESULTS.md`).
2. **Spec sau auth** → fetch một lần bằng token admin ra `openapi.json`, dùng `file://`. Spec tĩnh theo image (setup tạo schema cố định).
3. **Reseed = tái tạo container + volume + setup-token + bootstrap** (`reseed.sh`): `docker rm -f` + `volume rm` + `docker run` →
   chờ listening (poll http_code≠000) → đọc setup token từ `docker logs` → `POST /api/setup` (admin/AdminPass123) → login admin → đọc role UUID → tạo victim (Admin) + plain (User). Marker `RESEED_OK victim_role_ids=[AdminUUID]`. Kiểm chạy tay: ~2s, PASS.
4. **Không có bản vá** → không arm 0-FP; mọi 970 soát tay. **Chỉ arm "không reset"**.

## Rủi ro đã biết (ghi trước lượt chạy)

- **Role/user id là UUID sinh mới mỗi reseed**; transition là **body m2m lồng** `{roles:[{id:UUID}]}`. Auto phải (a) nhận field
  `roles` m2m là trường role, (b) sinh một UUID role hạ quyền hợp lệ trong body lồng. Nhiều khả năng auto FN — cơ chế khác raouf
  (quan hệ m2m + id động, không phải thiếu enum). Đây là phép đo, không ghi kết quả mong đợi.
- **OpenAPI 3.1.0** (raouf 3.0.0): để ý parser EvoMaster v6.1.1 có nuốt trọn không — theo dõi `evaluated` seed 1.
- Arm `declared` chưa dựng: cần tiêm UUID role + victim động vào `--statefulAuthzTransition` mỗi reseed, và body m2m lồng
  có thể không biểu diễn được bằng k=v. Xét sau khi có kết quả auto.

## Đếm / dừng sớm / held-out

Như raouf (`../raouf-heldout-20261014/PROTOCOL.md`): CSV `runs-<arm>.csv`; det970 từ report.json; login từng tài khoản từ
traffic jsonl. Dừng sớm seed 1 nếu thiếu login victim/operator; 3 seed đầu 0 bộ ba → dừng, tìm nguyên nhân. Lộ bug builder →
ghi FN, KHÔNG sửa builder (giữ held-out).
