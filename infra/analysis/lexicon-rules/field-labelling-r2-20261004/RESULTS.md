# Gán nhãn mức trường vòng 2 và so với danh sách viết tay — 2026-10-04

Protocol: `PROTOCOL.md` (lệch luật ở §9). Vòng 1: `../field-labelling-20261004/RESULTS.md`. Không sửa mã EvoMaster.
Không có lượt người: mọi nhãn do model gán (§7).

## 1. Kết luận

1. Trên nửa test mới (92 nhà cung cấp, 10.221 trường), danh sách rút bằng luật R4 không thay được danh sách viết tay ở
   A-role, B-low, B-high. A-role: F1 0,295 so với 0,354. Trên 61 trường dương A-role, viết tay đúng 10 trường mà R4
   trượt, R4 đúng 0 trường mà viết tay trượt (McNemar chính xác p = 0,002).
2. R4 loại `role`. Từ này có nhiều trường dương nhất ở train+dev (26 trường, 12 nhà cung cấp) nhưng đứng hạng 7 vì
   có 44 trường âm, và R4 chỉ giữ 5 từ. Danh sách R4 vì vậy không nhận trường `role` của reports-api, vampi, pyLoad.
   Rút lại trên cả 228 nhà cung cấp, `role` đứng hạng 8.
3. Cờ admin: danh sách viết tay `:104` nhận 1 trên 5 trường test, R4 (`admin`) nhận 3 trên 5 với 1 dương giả; p = 1,0.
   Năm từ của `:104` có 0 trường dương ở train+dev.
4. Tham số nạn nhân: danh sách viết tay có `id` cho 2.306 dương giả (precision 0,044, F1 0,083). Bỏ `id` thì F1 0,190;
   R4 (`clientid member user`) F1 0,224. So với bản bỏ `id`, R4 trượt thêm 13 trường dương (p = 0,002) và tránh thêm
   191 dương giả (p < 10⁻⁶).
5. 17 trong 39 từ viết tay có 0 trường dương ở train+dev (136 nhà cung cấp); 15 từ có 0 ở cả ba tập (228 nhà cung cấp).
6. Trung bình F1 năm danh sách trên test: viết tay 0,413, R4 0,431. Không có kiểm định cho trung bình này.

## 2. Dữ liệu và nhãn

| | train + dev (vòng 1) | test (vòng 2) | Gộp |
|---|---|---|---|
| Nhà cung cấp | 136 | 92 | 228 |
| Operation ghi có trường | 2.265 | 1.558 | 3.823 |
| Trường | 20.216 | 10.221 | 30.437 |
| A: role / perms / admin / active | 47 / 131 / 8 / 15 | 21 / 40 / 5 / 12 | 68 / 171 / 13 / 27 |
| C: name / id / email | 40 / 142 / 11 | 21 / 90 / 16 | 61 / 232 / 27 |
| Nhà cung cấp có trường A / C | 34 / 47 | 23 / 29 | 57 / 76 |

Nguồn: `results.json` `counts`, `merged-lists.json` `counts`, `final.csv` (205 trường dương vòng 2). Nửa test vòng 1 có
5 nhà cung cấp có trường A; nửa test này có 23.

Hai lượt gán trên 10.221 trường (`kappa-raw.json`):

| Khối | Trường | Kappa A có/không | Kappa C có/không | Dương A L1 / L2 | Dương C L1 / L2 |
|---|---|---|---|---|---|
| 001–022 | 10.221 | 0,890 | 0,801 | 70 / 76 | 117 / 132 |
| 001–019, mù | 8.794 | 0,844 | 0,791 | 43 / 47 | 85 / 104 |
| 020–022, L1 đã đọc báo cáo L2 | 1.427 | 0,964 | 0,830 | 27 / 29 | 32 / 28 |

Phân xử 72 trường lệch (`adjudication.csv`): 44 theo L1, 28 theo L2. Lý do lớn nhất: 20 trường danh tính không bị thao
tác tác động (phân công nghiệp vụ, lời mời, tài nguyên của người dùng), 16 trường chủ thể bị thêm vào quan hệ hoặc bị
sửa, 10 trường token/key bị xoá, khoá, bật tắt.

## 3. R4 so với viết tay, trên nửa test

R4: rút trên train + dev, giữ 5 từ điểm cao nhất có ở ≥ 2 nhà cung cấp; chọn trên dev trước khi gán vòng 2
(`select.json`). Bộ phân loại: tên lá hạ chữ thường chứa một từ, như runtime; B-low viết tay theo `:711`.

| Danh sách | Viết tay | R4 | Viết tay P / R / F1 | R4 P / R / F1 | Chỉ viết tay đúng / chỉ R4 đúng | p |
|---|---|---|---|---|---|---|
| A-role (`:417`) | role plan permission level tier | approve permission privilege restrict roles | 0,333 / 0,377 / 0,354 | 0,481 / 0,213 / 0,295 | 14 / 36 | 0,003 |
| A-admin (`:104`) | is_admin isadmin is_superuser is_superadmin is_staff | admin | 1,0 / 0,2 / 0,333 | 0,75 / 0,6 / 0,667 | 1 / 2 | 1,0 |
| C (`:414`, `:415`) | username userid user_id user account member subject principal id email | clientid member user | 0,044 / 0,835 / 0,083 | 0,160 / 0,370 / 0,224 | 59 / 2.060 | < 10⁻⁶ |
| C, bỏ `id` | 9 từ trên trừ `id` | clientid member user | 0,120 / 0,465 / 0,190 | 0,160 / 0,370 / 0,224 | 16 / 192 | < 10⁻⁶ |
| B-low (`:418`) | view read guest basic free member user none restrict limited | member none only read | 0,75 / 0,75 / 0,75 | 0,667 / 0,5 / 0,571 | 2 / 0 | 0,5 |
| B-high (`:419`) | admin owner super root manage write edit power full | admin full | 1,0 / 0,375 / 0,545 | 1,0 / 0,25 / 0,4 | 1 / 0 | 1,0 |
| A-active | (builder không có) | active enabled | | 0,036 / 0,333 / 0,066 | | |

Số dương trên test: A-role 61 trường (19 nhà cung cấp), A-admin 5 (4), C 127 (29), B 8 trường có `enum` xếp được
(5 nhà cung cấp, 23 giá trị). McNemar ở bảng trên tính trên mọi trường (`mcnemar.json`), nên trường âm chiếm đa số.
Tách riêng (`exploratory.json`, hậu kiểm):

| So sánh | Trên trường dương: chỉ viết tay đúng / chỉ R4 đúng, p | Trên trường âm: chỉ viết tay đúng / chỉ R4 đúng, p |
|---|---|---|
| A-role | 10 / 0, p = 0,002 | 4 / 36, p < 10⁻⁶ |
| C | 59 / 0, p < 10⁻⁶ | 0 / 2.060, p < 10⁻⁶ |
| C bỏ `id` | 13 / 1, p = 0,002 | 3 / 191, p < 10⁻⁶ |

Luật R0 của vòng 1 trên test (`results.json` `r0_test`): A-role 18 từ, F1 0,081 (721 dương giả); C 6 từ, F1 0,172.

Hậu kiểm, không thuộc protocol: R1 và R3 giữ `role` thay vì `roles`, A-role F1 0,379 trên test, trung bình F1 0,451
(`exploratory.json`). Luật được chọn trên dev là R4; đổi sang R1 hoặc R3 bây giờ là chọn theo test.

## 4. Từ viết tay có được corpus ủng hộ không

Số trường dương chứa từ ở train+dev / ở test; trong ngoặc: số nhà cung cấp có trường dương ở train+dev
(`results.json` `hard_word_support_train_dev`).

| Danh sách | Có trường dương ở ≥ 2 nhà cung cấp | 0 trường dương ở cả ba tập |
|---|---|---|
| `:417` | role 26 / 15 (12), permission 16 / 7 (5) | plan, tier; level 5 / 1 nhưng 1 nhà cung cấp |
| `:104` | không có | is_admin, is_superuser, is_superadmin, is_staff; isadmin 0 / 1 |
| `:414` + `:415` | user 97 / 42 (25), id 116 / 78 (32), userid 26 / 21 (6), user_id 24 / 3 (6), username 20 / 5 (9), member 20 / 4 (6), email 11 / 16 (7), account 7 / 0 (4) | subject; principal 0 / 5 |
| `:418` | read 7 / 4 (4), none 7 / 0 (3), member 2 / 0 (2) | basic, free, restrict, limited; view, guest, user có dương ở 1 nhà cung cấp |
| `:419` | admin 7 / 2 (5), full 7 / 0 (2) | super, root, edit, power; owner, manage, write có dương ở 1 nhà cung cấp |

Cột phải gom 15 từ có 0 trường dương trên 228 nhà cung cấp. Hai từ còn lại trong số 17 từ có 0 ở train+dev là
`isadmin` và `principal`, có dương ở test.

## 5. Neo trên target

Các target đã định hình danh sách viết tay, nên đây không phải phép đo held-out (`anchor.json`).

| Target | Trường | Viết tay nhận | R4 nhận |
|---|---|---|---|
| reports-api | `role` / `username` / VIEWER thấp, ADMIN cao | có / có / có, có | không / có / không, có |
| vampi-seeded | `role` / `username` / user thấp, admin cao | có / có / có, có | không / có / không, có |
| pyLoad | `permission`, `role` / `user` | có, có / có | có, không / có |
| artifact-keeper | `is_admin` / `id` | có / có (chỉ nhờ `id`) | có / không |
| Airflow | `roles` / `username` | có / có | có / có |
| bamf | `email` | có | không |

R4 trượt 7 trên 16 kiểm tra. Danh sách viết tay nhận đủ 16.

## 6. Giá trị thử và trường nạn nhân trong response, trên test

- 8 trường role/perms có `enum` xếp được, 51 trường không có `enum`. `:423` chứa đúng giá trị thấp nhất ở 2/8, `:427`
  chứa đúng giá trị cao nhất ở 2/8. Không có `enum` toàn số. Hai trường `mode ∈ [r, w, rw]` có giá trị ngắn hơn 4 ký
  tự, nên không thể thành từ ứng viên.
- Xấp xỉ `:1154`–`:1160`: tên lá của trường C trong thân request nằm trong danh sách ở 11/38 trường.

## 7. Danh sách rút trên cả 228 nhà cung cấp

`merged-lists.json`, R4 trên train + dev + test. Không còn tập nào để đo các danh sách này.

| Danh sách | Từ |
|---|---|
| A-role | approve groupids permission privilege roles |
| A-admin | admin owner |
| A-active | active enabled state status |
| C | collaborator membershipid principalid useremail userid |
| B-low | guest member none only read |
| B-high | admin full write |

So với R4 trên train+dev, C mất cả 3 từ `clientid member user` và thay bằng 5 từ khác. Thành phần danh sách đổi theo dữ liệu thêm vào,
vì R4 cắt ở 5 từ.

## 8. Hạn chế

- Không có lượt người. L1, L2 và người phân xử cùng là model Anthropic; người phân xử là phiên L1, chọn theo L1 ở 44/72
  trường.
- L1 khối 021–022 gán sau khi đọc báo cáo bàn giao của L2 (PROTOCOL §9). Kappa khối đó (0,964) không tính là đồng
  thuận độc lập; kappa mù là 0,844 (A) và 0,791 (C).
- Neo trên target không phải held-out (§5).
- B có 8 trường từ 5 nhà cung cấp, A-admin 5 trường từ 4 nhà cung cấp. Thêm một nhà cung cấp có thể đổi kết luận ở
  hai danh sách này.
- Bộ phân loại đo trên mọi trường của operation ghi. Builder dùng danh sách trong ngữ cảnh hẹp hơn (`:414` chỉ tìm
  tham số nạn nhân của operation đã chọn làm transition), nên precision ở §3 thấp hơn precision lúc chạy. Chưa đo trong
  ngữ cảnh đó.
- Corpus không có nhãn response và nhãn giá trị cho trường không có `enum`.

## 9. File

| File | Nội dung |
|---|---|
| `PROTOCOL.md` | Luật chốt trước, lệch luật §9 |
| `build_rows.py`, `rows/`, `rows.jsonl` | Dữ liệu vào vòng 2 |
| `L1/`, `L2/` | Nhãn gốc hai lượt |
| `kappa.py`, `kappa-raw.json` | Độ đồng thuận, tách mù và đã lộ |
| `diff_labels.py`, `disagreements.csv`, `adjudicate.py`, `adjudication.csv` | Trường lệch, mã chọn, lý do |
| `final.csv` | 205 trường dương vòng 2 sau phân xử |
| `common.py`, `select_rule.py`, `select.json` | Chọn luật trên dev |
| `evaluate.py`, `results.json`, `mcnemar.json`, `anchor.json`, `lists/` | Rút R4 trên train+dev, đo trên test, neo |
| `exploratory.py`, `exploratory.json` | Hậu kiểm: R0–R4 trên test, McNemar tách dương/âm |
| `merge_lists.py`, `merged-lists.json` | R4 trên cả ba tập |
| `../../corpus/sample_specs_field_r2.py`, `sample-field-r2*.json`, `specs/S5*`, `specs/S6*` | Bốc và tải spec |
