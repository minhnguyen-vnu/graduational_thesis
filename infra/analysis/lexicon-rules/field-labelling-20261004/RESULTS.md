# Gán nhãn mức trường và so với danh sách viết tay — 2026-10-04

Protocol: `PROTOCOL.md` (chốt 2026-10-04 khoảng 23:02, lệch luật ở §9). Không sửa mã EvoMaster.

## 1. Kết luận

1. Rút được 6 danh sách theo luật đã chốt (§3). Trên nửa test, không danh sách rút được nào thay được danh sách viết
   tay tương ứng: A-role rút được kém hơn rõ (F1 0,085 so với 0,471; McNemar chính xác p < 10⁻⁶), B-low và B-high kém
   hơn hoặc ngang (p = 0,25 và 1,0).
2. Nguyên nhân chính của A-role: luật P2 (precision ≥ 2 × tỉ lệ nền) với tỉ lệ nền 1,17% cho qua các từ chung `create`,
   `delete`, `read`, `write`, `default`, `group`. Luật này chốt trước, không sửa sau khi thấy kết quả.
3. Cờ admin: danh sách viết tay `:104` trúng 0 trên 8 trường admin của corpus (train 6, test 2). Từ rút được `admin`
   trúng 2/2 trường test, nhưng cả hai đến từ 1 nhà cung cấp (McNemar p = 1,0).
4. Tham số nạn nhân: danh sách viết tay `:414` + `:415` có từ `id`, cho 1.139 dương giả trên nửa test (precision 0,028).
   Bỏ `id` thì F1 0,125; danh sách rút được F1 0,113.
5. 19 trong 39 từ viết tay được đo có 0 trường dương trong nửa train (§4). Corpus không cho thấy các từ đó đến từ đâu.
6. Nửa test nhỏ: trường A đến từ 5 nhà cung cấp, cờ admin từ 1, nhãn B có 5 trường. Không đủ để thay danh sách viết
   tay bằng danh sách rút được, cũng không đủ để khẳng định danh sách viết tay đúng.

## 2. Dữ liệu và nhãn

| | Nửa train | Nửa test |
|---|---|---|
| Nhà cung cấp | 90 (44 cũ + 46 mới) | 46 (mới) |
| Operation ghi | 1.570 | 695 |
| Trường | 13.714 | 6.502 |
| A: role / perms / admin / active | 40 / 121 / 6 / 13 | 7 / 10 / 2 / 2 |
| C: name / id / email | 33 / 111 / 11 | 7 / 31 / 0 |
| Nhà cung cấp có ít nhất 1 trường A / C | 29 / 36 | 5 / 11 |

Nguồn: `results.json` `counts`, `final.csv`.

Hai lượt gán mù trên 20.216 trường (`kappa-raw.json`):

| Nhãn | Kappa | Dương L1 | Dương L2 |
|---|---|---|---|
| A có/không | 0,774 | 172 | 176 |
| A theo loại | 0,769 | | |
| C có/không | 0,803 | 172 | 223 |
| C theo loại | 0,799 | | |

Luật dừng §7 (chunk 011–014, 2.086 trường): kappa A 0,940, không dừng.

Phân xử 161 trường lệch (`adjudication.csv`): 108 theo L1, 51 theo L2, 2 khác cả hai. Lý do lớn nhất: 42 trường danh
tính không bị thao tác tác động (lời mời, xác thực, đọc), 37 trường quyết định quyền, 23 trường của nhóm quyền khi tạo,
21 trường client/key/token là chủ thể theo §3.

## 3. Danh sách rút được so với viết tay, trên nửa test

Bộ phân loại: tên lá hạ chữ thường chứa một từ của danh sách, như runtime. B-low viết tay theo `:711`.

| Danh sách | Viết tay | Rút được | Viết tay P / R / F1 | Rút được P / R / F1 | Chỉ viết tay đúng / chỉ rút được đúng | p |
|---|---|---|---|---|---|---|
| A-role (`:417`) | role plan permission level tier | access allowed approve create default delete group members permission read restrict role scopes write | 0,353 / 0,706 / 0,471 | 0,045 / 0,765 / 0,085 | 265 / 12 | < 10⁻⁶ |
| A-admin (`:104`) | is_admin isadmin is_superuser is_superadmin is_staff | admin | 0 / 0 / 0 | 0,667 / 1,0 / 0,8 | 1 / 2 | 1,0 |
| C (`:414`, `:415`) | username userid user_id user account member subject principal id email | account client email user | 0,028 / 0,868 / 0,055 | 0,063 / 0,526 / 0,113 | 20 / 850 | < 10⁻⁶ |
| C, bỏ `id` | 9 từ trên trừ `id` | | 0,069 / 0,605 / 0,125 | | | |
| B-low (`:418`) | view read guest basic free member user none restrict limited | none only read | 1,0 / 1,0 / 1,0 | 1,0 / 0,4 / 0,571 | 3 / 0 | 0,25 |
| B-high (`:419`) | admin owner super root manage write edit power full | admin | 0,833 / 1,0 / 0,909 | 1,0 / 0,6 / 0,75 | 2 / 1 | 1,0 |
| A-active | (builder không có) | active enabled | | 0,017 / 0,5 / 0,032 | | |

Số dương trên nửa test: A-role 17 trường, A-admin 2, C 38, B 5 trường (17 giá trị). McNemar chính xác hai phía trên
mọi tài liệu của danh sách (`mcnemar.json`), nên chênh lệch C và A-role chủ yếu do số dương giả.

## 4. Từ viết tay có được corpus ủng hộ không (nửa train)

Đếm trường dương / âm chứa từ, và số nhà cung cấp có trường dương (`results.json` `hard_word_support_train`).

| Danh sách | Có ở ≥ 2 nhà cung cấp dương | 0 trường dương |
|---|---|---|
| `:417` | role (23/35, 10), permission (7/12, 4) | plan (0/15), tier (0/0); level 5/16 nhưng 1 nhà cung cấp |
| `:104` | không có | cả 5 từ |
| `:414` + `:415` | user (78/218, 20), userid (26/39, 6), username (16/77, 6), user_id (12/27, 4), account (7/67, 4), member (16/31, 4), email (11/100, 7), id (94/2.426, 25) | subject, principal |
| `:418` | read (6/5, 3), none (6/0, 2) | guest, basic, free, restrict, limited; view, member, user có dương ở 1 nhà cung cấp |
| `:419` | admin (4/2, 3) | owner, super, root, edit, power; manage, write, full có dương ở 1 nhà cung cấp |

Tổng 39 từ: 19 từ có 0 trường dương, 7 từ có dương nhưng chỉ ở 1 nhà cung cấp, 13 từ có dương ở ít nhất 2 nhà cung cấp.

## 5. Danh sách giá trị thử và trường nạn nhân trong response

| | Nửa train | Nửa test |
|---|---|---|
| Trường role/perms có `enum` xếp được | 16 | 5 |
| Trường role/perms không có `enum` | 140 | 12 |
| `:423` chứa đúng giá trị thấp nhất | 4 / 16 | 3 / 5 |
| `:427` chứa đúng giá trị cao nhất | 4 / 16 | 4 / 5 |
| `enum` toàn số (`:421`, `:425`) | 0 | 0 |

Đa số trường quyền không có `enum` (140/156 ở train). Với các trường đó, builder chỉ có danh sách giá trị thử, và corpus
không có nhãn giá trị nào để kiểm.

`:1154`–`:1160` khớp object trong response; corpus không có nhãn response. Xấp xỉ: tên lá của trường C trong thân
request nằm trong danh sách ở 14/37 trường train, 4/11 trường test.

## 6. Hạn chế

- Không có lượt người. L1, L2 và người phân xử cùng là model Anthropic; người phân xử chính là phiên L1, và chọn theo
  L1 ở 108/161 trường.
- L1 lệch §3 trong lúc gán: không gán C cho client, API key, token. Đã sửa ở phân xử (21 trường), nhưng các trường mà
  cả L1 và L2 cùng bỏ qua không được phân xử.
- Chunk 028 và 031 chỉ được đọc qua grep ở cả hai lượt. 39 operation bị cắt sau 80 trường.
- Nửa test có 5 nhà cung cấp có trường A, 1 có cờ admin. Mọi con số §3 trên các danh sách đó dao động mạnh nếu thêm
  một nhà cung cấp.
- Luật rút từ (P1, P2, P3) lấy từ `derive3.py`, vốn viết cho nhãn mức operation với tỉ lệ nền khác. Với tỉ lệ nền mức
  trường 1,17%, P2 gần như không lọc. Sửa luật bây giờ là chỉnh sau khi đã nhìn nửa test, nên phải chốt lại trên một
  nửa test mới.
- Chưa đo trên các app target (bước neo ngoài model ở plan ban đầu); protocol này không gồm bước đó.

## 7. File

| File | Nội dung |
|---|---|
| `PROTOCOL.md` | Luật chốt trước, lệch luật §9 |
| `rows/`, `rows.jsonl` | Dữ liệu vào |
| `L1/`, `L2/` | Nhãn gốc hai lượt |
| `kappa.py`, `kappa-raw.json` | Độ đồng thuận trên nhãn gốc |
| `disagreements.csv`, `adjudicate.py`, `adjudication.csv` | Trường lệch, mã chọn, lý do |
| `final.csv` | 394 trường dương sau phân xử |
| `derive_eval.py`, `results.json`, `lists/` | Rút từ, đo, ứng viên kèm điểm |
| `mcnemar.py`, `mcnemar.json` | Kiểm định ghép đôi |
| `../../corpus/sample_specs_field.py`, `sample-field*.json`, `specs/S3*`, `specs/S4*` | Bốc và tải spec mới |
