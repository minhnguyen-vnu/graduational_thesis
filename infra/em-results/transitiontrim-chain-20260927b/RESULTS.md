# Chuỗi transition-trim lần 3 — 2026-09-27

Jar `88f8e7a1ce0952e3` (`EvoMaster/evomaster-TT-88f8e7a1.jar`), cây `bea33bab`. Self-test 00:57–01:30: 6/7, dừng,
không chạy gate và seeds.

| Kiểm | Kết quả |
|---|---|
| `gg-baseline-422`, `airflow-exit-0`, `airflow-fields-removed` | PASS |
| `airflow-sent-roles-only` | PASS: 6 PATCH users sau 01:15:35, thân chỉ có `roles`, không query |
| `airflow-no-empty-restore` | FAIL: 3 dòng `Privilege-restore`, cả ba 422 |
| `tier1-970`, `tier1-nothing-removed`, `tier1-fixed-no-970` | PASS |

## Vì sao `airflow-no-empty-restore` còn hỏng

Ba thân khôi phục gửi đi (`selftest-transtrim/airflow-seed1-traffic.jsonl`): `{"roles":"admin"}`, `{"roles":{}}`,
`{"roles":{}}`, cả ba 422 `list_type`. `roles` khai `anyOf [array, null]`; `RestActionBuilderV3` (dòng 1688–1706)
dựng nó thành `ChoiceGene` gồm ba lựa chọn cùng tên `roles`: mảng, gene cho `null`, và một object gộp. Bản sửa lần 3
bỏ qua gene nào chứa mảng object, nhưng lựa chọn thứ hai và thứ ba không chứa mảng, nên `"admin"` vẫn gán được vào
chúng. Thứ được gửi là lựa chọn đang active. Sửa lần 4: bỏ qua cả cây con của mọi trường quyền chứa mảng object
(`wip/transition-trim-20260927c.patch`, `../transitiontrim-chain-20260927c/`).

## Bộ ba hợp lệ đầu tiên trên Airflow

Log `selftest-transtrim/airflow-seed1.log` dòng 3090:
`Discarded an UNCONFIRMED stateful-authorization (MR-A1) attempt on POST:/api/v2/connections/defaults: re-logging
the victim in did not show the privilege removed (victim 'victim', operator 'admin', codes 204/200/204)`.

| Giờ | Request | Token (12 ký tự cuối) | Mã |
|---|---|---|---|
| 01:15:55 | `POST /api/v2/connections/defaults` (nguồn) | `nKGSr_-0Rz-w` | 204 |
| 01:15:56 | `PATCH /auth/fab/v1/users/victim` `{"roles":[]}` (transition, `admin`) | `iOhWwDxAQbfA` | 200, response `"roles":[]` |
| 01:15:57 | `POST /api/v2/connections/defaults` (follow-up, token cũ) | `nKGSr_-0Rz-w` | 204 |
| 01:16:00 | `POST /api/v2/connections/defaults` | `spR7bCo8ExDA` | 204 |

Nguồn 2xx, transition 2xx, follow-up bằng token cũ 2xx. Bước C4 đăng nhập lại nạn nhân và không thấy quyền bị
gỡ, nên bộ ba bị loại, không có 970. Dòng 01:16:00 là một token khác, khớp với lần đăng nhập lại; chưa đối chiếu
với dòng log của probe.

Nghĩa là sau khi `victim` mất mọi vai trò, cả token cũ lẫn token mới vẫn gọi được `POST /connections/defaults`.

## Kiểm tay 09-27 01:58, Airflow cổng 8082

Cửa sổ này đã được đo ngày 09-20, trên cả provider 3.8.1 lẫn 3.9.0, và bản kiểm tay đó đã dự đoán oracle sẽ không
nâng 970 vì chứng chỉ mới cũng dùng được (`../../analysis/cve-survey/airflow-handcheck-20260920.md` §3 đường A, §4).
Lượt chạy máy này xác nhận dự đoán. Kiểm tay dưới đây lặp lại phép đo đó trên container hiện tại.

Nguyên nhân là bộ đệm user 30 giây của FAB. Mã nguồn trong container (`apache-airflow-providers-fab` 3.8.1,
`auth_manager/fab_auth_manager.py`): dòng 177 `CACHE_TTL = conf.getint("fab", "cache_ttl", fallback=30)`, dòng 196
`cache: TTLCache = TTLCache(maxsize=1024, ttl=CACHE_TTL)`, dòng 288
`@cachedmethod(lambda self: self.cache, key=lambda _, token: int(token["sub"]))` trên `deserialize_user`.
Khoá đệm là user id, không phải token: token cũ và token mới của cùng user đọc cùng một bản user, kèm vai trò.
`airflow config get-value fab cache_ttl` trả `30`.

| Giờ | Bước | Mã |
|---|---|---|
| 01:58:02 | `victim` (vai trò `Op`) `POST /api/v2/connections/defaults` | 204 |
| | `viewer` (vai trò `Viewer`) cùng request | 403 |
| | `admin` `PATCH /users/victim {"roles":[]}` | 200, vai trò `[]` |
| | `victim` token cũ | 204 |
| | `victim` token mới, không vai trò | 204 |
| | `admin` đặt `victim` về `[{"name":"Viewer"}]` | 200 |
| | `victim` token cũ; token mới | 204; 204 |
| | `viewer` | 403 |
| 01:58:17 | `victim` token mới | 204 |
| 01:58:47 | `victim` token mới | 403 |
| 01:59:09 | `admin` đặt `victim` về `Op`, rồi `victim` gọi lại | 403 |

Dòng cuối là chiều ngược lại: bản đệm lúc 01:58:47 mang vai trò `Viewer`, nên 22 giây sau khi được trả `Op` user vẫn
bị chặn. Sau kiểm tay: `reset-3users.sh`, `victim` về `Op`, `viewer` về `Viewer`.

Với oracle: bộ ba `204/200/204` là quyền sống sót 30 giây sau khi hạ, nhưng gắn với user, không gắn với credential.
C4 đăng nhập lại và vẫn thấy 2xx, nên loại bộ ba. MR-A1 đòi chính credential cũ giữ quyền; ở đây mọi credential
đều giữ, và tự hết sau `cache_ttl`. Đây là hành vi có cấu hình của Airflow, nằm ngoài phạm vi 970.

Hệ quả đo: follow-up chạy 1 giây sau transition, trong cửa sổ 30 giây. Với `cache_ttl` mặc định, oracle không
phân biệt được một lỗi token cũ thật với bộ đệm, và mọi bộ ba trên Airflow sẽ ra UNCONFIRMED. Chạy với
`AIRFLOW__FAB__CACHE_TTL=0` bỏ được bộ đệm; đó là một sai lệch cấu hình target, phải khai. Chưa chạy.
