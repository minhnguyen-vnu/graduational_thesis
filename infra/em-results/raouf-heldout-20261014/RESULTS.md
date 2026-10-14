# raouf held-out — kết quả chạy máy (jar P2e-6ae8277b, 2026-10-14)

Giao thức, lệch luật, reseed: `PROTOCOL.md`. D1 tắt, qua proxy ghi request, maxTime 600s, rate 600.

## Hàng (seed 1 mỗi arm)

| arm | seed | det970 | assembled | void | evaluated | login v/o/l | transition |
|---|---|---|---|---|---|---|---|
| auto | 1 | 0 | 0 | 0 | 3132 | 1575/1504/1441 | none (proven false) |
| declared | 1 | 1 | 2 | 1 | 3166 | 1549/1584/1506 | PUT /v1/users/{id}/role 200/204/200 |

`runs-auto.csv`, `runs-declared.csv`.

## auto = FN (builder không tự với tới), cơ chế

Builder P2e **chọn đúng** transition `PUT /v1/users/{id}/role` (score 2.59, roleField `body:roleCode`, victimField
`path:id`, candidate 1/1) nhưng không dựng nổi bộ ba (`logs/auto-seed1-600s.log`):
- `reduced role values: [read, member, guest]` — spec `AssignRoleDto.roleCode` là **string tự do, không enum**
  (`{"type":"string","example":"ADMIN"}`). Không có enum để rút giá trị hạ quyền → builder lấy từ từ vựng NB học sẵn
  (model `low` 8 token: read/member/guest), không trùng role thật của raouf (SUPER_ADMIN/ADMIN/CUSTOMER).
- `victim 'victim' current roles []` — builder không đọc role hiện tại của victim (dù `GET /v1/users/{id}` phơi role).
- Hệ quả: `could not target victim` → `transition ... exhausted its sources after 0 attempts, proven false` → 0 bộ ba.

Cùng họ FN với bamf (`{email}` không nhận là user param) và artifact-keeper (admin-flip boolean). Không sửa builder
(giữ held-out). Đúng điểm yếu "từ vựng nhận diện trường" CLAUDE.md §6.

## declared = TP (lỗi reachable khi đưa đúng transition)

Ép `--statefulAuthzTransition "PUT /v1/users/{id}/role roleCode=CUSTOMER id=2"`. Builder dựng 2 bộ ba, nổ 970.
Test `EvoMaster_0_faults_Test.py::test_48_patch_on_categori_showsFaults_101_970`:
1. victim(ADMIN) `POST /v1/categories` 201, `PATCH /v1/categories/{id}` 200 — source, ALLOWED.
2. operator `PUT /v1/users/2.0/role {roleCode:CUSTOMER}` 204 — transition.
3. Fault970: victim token cũ `PATCH /v1/categories/{id}` **200** — follow-up vẫn ALLOWED sau khi hạ.

Soát tay ground-truth (reseed sạch): ADMIN `PATCH /categories/{id}`=200, CUSTOMER=403, CUSTOMER `POST /categories`=403.
Sửa category là op ADMIN-only, CUSTOMER bị chặn thật → 970 là **TP**, không phải FP guard (§3). Nổ cả dưới D1 (token mới 403).

## Dè dặt

- `audit970_seeded.py` không nhận format raouf (ra 0/0/0) — tuned cho target tự gieo; soát bằng đọc test + probe tay.
- Chưa replay test sinh ra từ trạng thái sạch (test mang id fuzz float + resolve_location); TP đã xác nhận bằng probe tay.
- Mỗi arm mới 1 seed. auto FN tất định (thiếu enum, seed-independent); declared TP 1 seed.
- raouf không có bản vá role-demotion → không có arm 0-FP; mọi 970 soát tay.
