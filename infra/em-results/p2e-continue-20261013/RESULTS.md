# Kết quả — P2e chạy tiếp từ P2d

71 hàng P2e, 2026-10-13 14:32 → 10-14 00:41, không luật dừng nào nổ, 0 hàng ERR. Bộ gộp 180 hàng: 71 hàng P2e
(`6ae8277b`), 109 hàng P2d (`2e0dbd4d`), cột `jar` trong `merged.csv`. Không trích vào §4 (`PROTOCOL.md`, lệch luật 2).

## So với AF2 (`merge.out`)

| Arm | AF2 | Bộ gộp | Seed lệch |
|---|---|---|---|
| reports vuln không reset | 19/20 | 19/20 | 0 |
| reports vuln có reset | 20/20 | 20/20 | 0 |
| reports fixed không reset | 0/20 | 0/20 | 0 |
| reports fixed có reset | 0/20 | 0/20 | 0 |
| vampi vuln không reset | 7/20 | 7/20 | 0 |
| vampi vuln có reset | 13/20 | 13/20 | 0 |
| vampi fixed không reset | 0/20 | 0/20 | 0 |
| vampi fixed có reset | 0/20 | 0/20 | 0 |
| pyLoad vuln không reset | 5/5 | 5/5 | 0 |
| pyLoad vuln có reset | 5/5 | 5/5 | 0 |
| pyLoad fixed không reset | 0/5 | 0/5 | 0 |
| pyLoad fixed có reset | 0/5 | 0/5 | 0 |

## Từng bước

- Bước 1, 10 hàng vampi P2d gọi restore với `EVOMASTER`: 10/10 trùng AF2 trên det970, assembled, void, resets,
  restores_ok, restores_no, statuses. Seed 11 vuln nổ lại; seed 11 fixed dựng lại bộ ba 200/200/403.
- Bước 2, 33 hàng vampi chưa chạy: 32/33 trùng AF2 trên 7 cột. Vampi fixed không reset seed 19: void 9, AF2 8; thêm
  một lượt VOID nạn nhân `admin`, operator `name2`, mã 401/403/401; hàng không gọi restore.
- Bước 3, 11 hàng reports kiểm lập luận giữ hàng: 11/11 trùng P2d trên 7 cột; bước 5 không chạy
  (`verify-rerun.csv` rỗng).
- Bước 4, 17 hàng pyLoad: det970 trùng AF2 cả 17. Không reset: 7 cột trùng AF2. Có reset: P2e dựng 14–15 bộ ba
  trên vuln (AF2 7–8) và 10–11 trên fixed (AF2 7); 8 source của AF2 ở seed 1 vuln nằm trong 14 source của P2e.
  52/52 bộ ba trên fixed có reset là 200/200/403.

## Soát

`audit970_seeded.py` trên 54 lượt P2e reports và vampi: 7 test 970 PASS, 0 FAIL, 0 UNPARSED (`audit970.out`). pyLoad
không qua script này (auth bằng cookie). Chưa replay.

## Quyết định dùng bộ gộp (user, 2026-10-14)

Tạm dùng bộ gộp này cho P2e, ghi thành lệch luật (CLAUDE §2: một bảng không trộn jar). 109 hàng P2d không chạy qua
đoạn mã P2e đổi: 106 hàng không gọi restore, 3 hàng pyLoad restore trường kiểu integer; 11 hàng chạy qua đoạn đó
trùng P2d (bước 3). Lượt đầy đủ trên riêng P2e chạy sau; harness soạn sẵn ở `p2e-full-20261014/`.

## Soát tay (2026-10-14)

Cả hai chênh lệch với AF2 đến từ trần số lần thử dựng bộ ba: `MAX_STATEFUL_TRIPLE_ATTEMPTS` là 8 ở `8d6cf8431f`
(dòng 126), 20 ở `a544c996ac` (dòng 233, P1). Không chênh lệch nào đổi det970.

**Vampi fixed không reset seed 19, VOID 9 so với 8.** Cả hai jar thử cùng source `PUT /books/v1/{book_title}/secret`
với 3 nạn nhân (`superadmin`, `name1`, `admin`) × 3 operator, cùng thứ tự; 8 dòng VOID đầu trùng nhau từng dòng.
AF2 dừng ở lần thử thứ 8; P2e thử cặp thứ 9 (`admin`, `name2`, 401/403/401). Cả 9 lần thử VOID vì source trả 401;
log ghi đăng nhập thất bại `Username does not exist`.

**pyLoad có reset, nhiều bộ ba hơn.** AF2 dừng ở 8 lần thử: vuln 7–8 bộ ba, 0 VOID. P2e: vuln 14–15 bộ ba và 4 VOID,
fixed 10–11 bộ ba và 8–9 VOID. Gộp 5 seed, source P2e có mà AF2 không có: vuln `update_users`, `get_apikeys`,
`generate_apikey`, `delete_apikey`, `update_accounts`; fixed `add_account`, `update_accounts`. Danh sách 6 source
trước đây chỉ so seed 1; `edit_package`, `package_order` có ở AF2 trong seed khác.

Mọi source mới đều bị chặn bởi quyền mà transition gỡ. Transition P2e gửi `permission=1` (chỉ `ADD`) và `role` khác 0
ở cả 14 test 970 của vuln seed 1. `parse_permissions` (`webui/app/helpers.py:134–151`) chỉ cấp `ADMIN` khi
`role == 0`, còn lại cấp theo bit của `perms`.

| Source | Quyền đòi (`json_blueprint.py`) | Sau transition |
|---|---|---|
| `update_users`, `get_apikeys`, `generate_apikey`, `delete_apikey` | `ADMIN` (:435, :480, :488, :495) | mất |
| `add_account`, `update_accounts` | `ACCOUNTS` = 256 (:338, :353) | mất |
| `edit_package`, `package_order` | `MODIFY` = 32 (:246, :153) | mất |

Trên fixed, `update_users` chỉ ra VOID (transition 401, 25 lần, nguyên nhân chưa kiểm vì log không ghi thân request);
`get_apikeys`, `generate_apikey`, `delete_apikey` không được thử vì hết trần 20 lần. Ba source này chỉ được xác nhận
bằng đọc mã, chưa có bộ ba trên fixed. `get_apikeys`, giống `status` và `links` mà AF2 đã dùng, là lời gọi đọc qua
`POST`; builder coi mọi `POST` là ghi.
