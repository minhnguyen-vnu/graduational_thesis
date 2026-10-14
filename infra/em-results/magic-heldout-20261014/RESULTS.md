# magic held-out — kết quả (jar P2e-6ae8277b, 2026-10-14)

Giao thức: `PROTOCOL.md`. MR-A1 kiểm tay XÁC NHẬN live (`../../magic-target/handcheck.sh`, token-cũ=202 sau hạ / token-mới=403 / neg=403).

## Hàng (auto, seed 1, 600s)

```
auto,1,600s,exit=0,det970=0,assembled=0,void=0,evaluated=3535,logins v:217 o:212 l:211,sleep=0,transition=none
```
`runs-auto.csv`. (Smoke 120s + lượt dựng auth ở `runs-auto-smoke.csv`.)

## Kết quả: auto = FN (builder không dựng được nguồn), app chạy sạch

magic chạy máy được (khác fastschema/alvaro bị chặn). Auth, spec, throttle đều giải xong (xem lệch luật). 3535 test,
cả ba tài khoản login hàng trăm lần. Nhưng oracle dựng **0 bộ ba**.

Builder decisions (`logs/auto-seed1-600s.log`):
- Transition **nhận đúng**: `transition candidate DELETE:/magic/system/magic/users_roles score 4.08 roleField query:role
  victimField query:user reducedRoleValues 3` → chosen. Builder xử lý được transition DELETE + tham số query-string.
- Source **thất bại**: `guarded source candidates: 0 []` → `exhausted its sources after 0 attempts, proven false` → 0 bộ ba.

Cơ chế FN (khác raouf enum-gap): nguồn thật `PUT /magic/system/magic/roles` là **crud-update trả HTTP 404 khi tên role
chưa tồn tại** (quirk magic). EvoMaster PUT tên ngẫu nhiên → 404, không bao giờ quan sát 2xx trên nó → builder không nhận
ra nó (hay bất kỳ root-guarded write nào) là "guarded source có victim ALLOWED" → 0 nguồn. Nguồn cần được quan sát 2xx
mới vào danh sách; magic không cho 2xx trên write trừ khi hàng đích tồn tại sẵn (handcheck phải tạo `src_role` trước).

Phụ: transition của magic là **xoá grant role cao (root)**, không phải gán role thấp; mô hình "reduced role values
[read,member,guest]" của builder gán role thấp, lệch ngữ nghĩa với DELETE-grant. Nhưng điểm chặn chính là nguồn (0 candidate).

Lỗi MR-A1 reachable (kiểm tay xác nhận); builder không tự với tới vì không định danh được nguồn. Arm declared không chạy:
chỉ ép được transition, không ép được nguồn — 0 source candidate thì declared cũng 0 bộ ba.

## Lệch luật đã khai

1. **Spec tổng hợp** (`synth_spec.py` → `openapi.json`): magic serve OpenAPI rỗng (`/endpoints/openapi` 0 path). Dựng
   OpenAPI 3.0 từ `/endpoints/list` (metadata input của chính magic). Tự chọn 3.0 → tránh bẫy 3.1/vòng tròn (fastschema).
2. **Loại /auth/ khỏi spec fuzz**: EvoMaster fuzz endpoint login bằng mật khẩu sai → khoá tài khoản per-user (config-login
   đúng cũng 401). Bỏ 13 endpoint /auth/ khỏi spec (login vẫn qua externalEndpointURL ngoài spec). 219→205 op.
3. **Nâng throttle login**: `throttles.hl` hardcode 10/phút/IP (429). Reseed `docker cp` bản limit cao + `restart` để startup
   khai lại throttle (file nằm trong image, không volume). Như NODE_ENV=test của raouf.
4. **Login GET query-string**: auth config bake creds per-account vào externalEndpointURL, verb GET, rút `/ticket`. WFC xử lý được.
5. **Reseed** = `down -v` (magic persist qua named volume) + cp throttle + restart + setup (authenticate root/root → config/setup)
   + bootstrap (victim+plain, gán root cho victim, tạo src_role). ~7–30s. Marker `RESEED_OK victim_role=root`.
6. **Không có bản vá** → không arm 0-FP; **chỉ arm không reset**.

## Dè dặt

- Spec tổng hợp (3.0) từ metadata magic, không phải spec do magic phát hành (magic không phát hành spec dùng được).
- 1 seed auto. FN tất định (source-identification cấu trúc + 404-quirk, seed-independent).
