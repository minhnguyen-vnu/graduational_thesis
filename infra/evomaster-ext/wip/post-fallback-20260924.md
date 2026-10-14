# Xét nguồn POST khi không nguồn PUT/PATCH nào có nạn nhân — duyệt và áp 2026-09-24 23:53

Patch `post-fallback-20260924.proposed.patch`, tạo 2026-09-24 22:45 từ cây làm việc sha `d5a9b00d`. Người dùng duyệt
23:50, áp 23:53. Cây làm việc mới sha `00f98d290947d998` = `d1-lexicon-field-harvest-rolefield-postfallback-20260924.patch`,
tập rollback: cùng sha trước và sau. Jar `EvoMaster/evomaster-PF-0607485b.jar`.

## Self-test `selftest/post-fallback.sh`, jar `0607485b`: 5/6

`em-results/postfallback-selftest-20260925-b/selftest.txt`. Lượt `postfallback-selftest-20260925/` dừng tay vì
`reset-3users.sh` thiếu quyền thực thi.

| Check | Kết quả |
|---|---|
| `rf-baseline-putpatch-only` | PASS |
| `airflow-post-considered` | FAIL: danh sách có 14 nguồn POST, nhưng EvoMaster exit 1 |
| `airflow-putpatch-replaced` | PASS |
| `tier1-putpatch-kept` | PASS |
| `tier1-970` | PASS |
| `tier1-fixed-no-970` | PASS |

Exit 1 trên Airflow: nguồn `POST /api/v2/connections/defaults` có nạn nhân `[admin, victim]`; hai bộ ba VOID
(nạn nhân `admin`, người thao tác `victim` rồi `viewer`, `204/403/204`); nhánh khôi phục quyền gọi
`setAllRoleFieldsTo` (`RestSecurityBuilder.kt:1009`), `ObjectGene.unsafeSetFromStringValue` parse `admin` như JSON
và ném `JsonParseException`, không ai bắt. Đề xuất bắt lỗi khi gán gene: chưa duyệt, chưa áp.

## Thay đổi

`RestSecurityBuilder.kt:542–543`. Hiện tại nguồn POST chỉ được xét khi danh sách PUT/PATCH được canh rỗng.
Đề xuất: xét nguồn POST khi không phần tử nào của danh sách PUT/PATCH có một lần gọi 2xx có xác thực
(cùng điều kiện `findAndSlice` dùng để tìm nạn nhân ở `:562`).

Chạy tay trên lượt Airflow 3 tài khoản (`em-results/airflow-3users-20260924/`): 18 nguồn PUT/PATCH, cả 18
`victims []`, nên điều kiện `any` sai và danh sách thành các nguồn POST có 403, trong đó có
`POST /api/v2/connections/defaults` (204 và 403 trong test sinh ra). Với jar `RF` danh sách giữ 18 nguồn
PUT/PATCH và `sources exhausted after 0 triple attempts`.

Vikunja 2.2.2 (`em-results/vikunja-diag-20260924/RESULTS.md`) dừng ở cùng chỗ, cả khi khai transition: 1 nguồn
`PUT /teams/{id}/members`, 0 nạn nhân. Trên Vikunja mọi lệnh cập nhật là POST. Bộ test rút gọn không có lệnh
POST nào vừa 2xx vừa 403, nên chưa biết patch có đủ cho Vikunja hay không.

## Ảnh hưởng tới ba target

Không đổi khi ít nhất một nguồn PUT/PATCH có nạn nhân. Tier-1 seed 1 có `PUT /reports/{id}` với nạn nhân
`[alice, superadmin]` (`rolefield-chain-20260924/selftest-rolefield`). Tier-2 và pyLoad chưa kiểm được: log của
chuỗi 09-24 không bật debug. Gate và seeds 1–10 trả lời.

## Self-test đã định trước khi chạy

- Airflow 3 tài khoản, seed 1: dòng `guarded source candidates` có ít nhất một `POST:`; jar `RF` cùng lệnh thì
  không có.
- Tier-1 seed 1: dòng `guarded source candidates` giống hệt jar `RF`, 970 vẫn nổ.
- Tier-1 bản đã vá: 0 phát hiện 970.

## Rủi ro đã biết

Một bộ ba trên Airflow còn có thể kẹt ở `roles` (`airflow-3users-20260924/RESULTS.md`, mục kiểm hai trở ngại).
Kết quả đúng trên Airflow là không có 970: FAB cache user 30 giây theo `sub`, token cũ và mới cùng còn dùng được.
Chi phí khi duyệt: khoảng 1 giờ build, self-test, một lượt Airflow; gate và seeds 1–10 khoảng 8,5 giờ.
