# Mô hình Naive Bayes chọn transition và trường — jar P2e

Từ jar `P2e` (commit `a544c996ac`), builder chọn transition, trường vai trò, trường nạn nhân và giá trị quyền bằng
một mô hình Naive Bayes rút từ nhãn vòng 4 (10.381 op ghi, 230 API). Mô hình thay bộ từ vựng 53 + 45 từ của jar `L`
tới `AF2` (`docs/lexicon.md`) và các danh sách viết tay. Kiểm chéo theo nhà cung cấp: op transition thật (op T) đứng
đầu ở 16–18, trong 4 đầu ở 21–25 của 47 spec test. Trên ba target của luận văn, thay danh sách viết tay bằng mô hình
không mất phát hiện 970 nào: trên 180 hàng, số nổ 970 và FP trùng `AF2` từng seed (`docs/results.md` §0). 47 spec test đã bị nhìn nhiều
lần khi chọn mô hình, nên mọi số kiểm chéo là số thăm dò.

Thiết kế, mọi lựa chọn bị loại và số đo đầy đủ: `infra/evomaster-ext/wip/p2-design-20261012.md`.

## 1. Mô hình quyết định gì

Pha security chạy sau search. `addForStatefulAccessControl` (`RestSecurityBuilder.kt:600`) gọi mô hình ở bốn chỗ:

| Việc | Hàm | Bảng |
|---|---|---|
| Xếp hạng op ghi làm transition | `rankPermissionReducingTransitions` `:1201`, `transitionScore` `:223` | `op` |
| Chọn trường vai trò trong transition | `roleField` `:1215` | `role` |
| Chọn trường chỉ nạn nhân | `victimField` `:1222` | `victim` |
| Chọn giá trị hạ quyền và nâng quyền | `harvestReducedRoleCandidates` `:1252`, `restoreValues` `:1260`, `valueScore` `:225` | `low`, `high`, `lowstr`, `highstr` |

Oracle dùng cùng vị từ `looksLikePermissionReducingTransition` (`:241`): verb ghi và điểm op > 0, tức
hậu nghiệm > 0,5. Khi D1 tắt, oracle bỏ qua source mà vị từ này nhận (`RestSecurityOracle.kt:583`) và đòi lời gọi xen giữa mà
vị từ này nhận (`:602`). Builder và oracle dùng một vị từ ở một ngưỡng, nên builder không dựng bộ ba mà oracle từ
chối.

## 2. Cách tính

- Trọng số dấu hiệu `w(t) = ln((d_T + 1)/(N_T + 2)) − ln((d_N + 1)/(N_N + 2))`; tiên nghiệm `ln(N_T/N_N)`.
- Điểm = tiên nghiệm + Σ w của dấu hiệu có mặt; điểm > 0 nghĩa là hậu nghiệm > 0,5.
- Chỉ giữ dấu hiệu có mặt ở mục dương của ít nhất 2 nhà cung cấp.
- Dấu hiệu của op: `p:` token path, `f:` token tên lá của tham số và trường thân, `v:` verb. Token: cắt ký tự không
  chữ-số, tách camelCase, chữ thường, bỏ token toàn số và token dưới 4 ký tự.

Chạy tay trên pyLoad, trọng số lấy từ `stateful-authz-model.csv`:

| Op | Dấu hiệu | Trọng số | Điểm |
|---|---|---|---|
| `POST /api/set_user_permission` | tiên nghiệm | −3,935 | |
| | `f:permission` | +2,073 | |
| | `f:role` | +2,120 | |
| | `f:user` | +1,978 | |
| | `p:permission` | +1,846 | |
| | `p:user` | +1,997 | |
| | `v:POST` | −0,465 | **+5,613**, transition |
| `POST /json/edit_package` | tiên nghiệm | −3,935 | |
| | `f:name` (từ `pack_name`) | −0,181 | |
| | `v:POST` | −0,465 | **−4,581**, không phải transition |

Trên `AF2`, từ lexicon `name` (0,08) khớp `pack_name`, nên oracle `AF2` coi `edit_package` là transition và không
chấm bộ ba trên nó (`em-results/p2e-continue-20261013/af2-41-vs-38.md`). Trên `P2e` op này dưới cổng và được chấm.

## 3. Dữ liệu và kiểm chéo

Nhãn `field-labelling-r4-20261006/` (10.381 op ghi, 230 API), kiểm chéo theo nhà cung cấp 5 phần × 4 lần lặp, seed
20261006, loại 29 spec cũ: 47 spec test có op T. Mỗi ô là bốn lần lặp; tiên nghiệm op −3,94 (199 op T / 10.182).

| Luật xếp op | Op T đứng đầu /47 | Op T trong 4 đầu /47 | Op phí lớn nhất ở một spec |
|---|---|---|---|
| max điểm lexicon | 18 / 19 / 19 / 20 | 22 / 21 / 22 / 23 | 2 / 2 / 2 / 76 |
| Naive Bayes (chốt) | 16 / 16 / 17 / 18 | 22 / 21 / 22 / 25 | 1 / 2 / 1 / 3 |

Không chênh nào giữa hai luật có p < 0,05. Naive Bayes được chọn vì op T luôn nằm trong tầm builder tới: trên
netbox, luật max để op T ở hạng 77 vì từ `outside` (0,375) thắng `username` (0,171).

Trường vai trò (B1), op T trong 4 đầu và trường chọn trùng nhãn: Naive Bayes 15–16/47, luật RF (`permission`, `role`,
bool `admin`) 11–13/47. Trường nạn nhân (B3), trên 184 trường: Naive Bayes chọn đúng 129–132, luật RF 117–121, danh
sách viết tay 117; Naive Bayes so với RF p = 0,065–0,27.

## 4. Trên target

- Hạng của transition: 1 ở reports, vampi, pyLoad, Airflow, bamf; 3 ở artifact-keeper.
- Trên reports, vampi, pyLoad (180 hàng), số lần nổ 970 và FP trùng `AF2` ở cả 12 arm. Chỗ khác `AF2` (thêm bộ ba và
  VOID trên pyLoad có reset, thêm một VOID ở vampi fixed không reset seed 19) đến từ trần lần thử 20 thay vì 8 (P1)
  (`em-results/p2e-continue-20261013/RESULTS.md`, Soát tay).
- P2e chưa chạy Airflow, bamf, artifact-keeper; hạng ở trên xếp từ spec tĩnh.

## 5. File mô hình

`core/src/main/resources/stateful-authz-model.csv` (sha256 `9a7a7749…`), cột `table,feature,weight`. Bảng `op`
(166 dấu hiệu), `role` (45), `victim` (25), mỗi bảng một dòng `__prior__`; `low` (8), `high` (9), `lowstr` (3),
`highstr` (1). Sinh bằng `infra/analysis/lexicon-rules/p2-model-20261012/derive_model.py`; `check_model.py` 8/8:
sinh lại trùng từng byte, trọng số bằng script đo, `low`/`high` khớp `field-ranking-20261007/rankings/RK.csv`.

## 6. Còn viết tay và hạn chế

- Viết tay: `1, 0, 2` / `0, 1, 2` cho trường vai trò kiểu số; token `id` khi điền giá trị nạn nhân.
- Giá trị nâng quyền của trường enum chỉ gồm giá trị mô hình chấm `high > low` (P2e, `RestSecurityBuilder.kt:1265–1269`):
  trước sửa này, restore tiêu một lượt vào `EVOMASTER`, giá trị EvoMaster tự chèn vào enum chuỗi, và vampi seed 11
  mất 970 (`em-results/p2d-night-20261012/STOPPED.md`).
- 47 spec test đã bị nhìn nhiều lần: số kiểm chéo là thăm dò, không gắn p-value xác nhận. Ước lượng sạch cần spec gán
  nhãn mới.
- Giả định độc lập sai với các token đi cùng nhau (`user`, `username`, `email`, `password`); mô hình chỉ cộng dấu hiệu
  có mặt.
- Trần B1 khoảng 23–25/47: transition chỉ có DELETE, vai trò là id hoặc tên của object role, số không enum, object.
- Hạn chế khác của thiết kế: `wip/p2-design-20261012.md` §10.
