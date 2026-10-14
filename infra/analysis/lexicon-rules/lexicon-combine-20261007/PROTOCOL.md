# Thay điểm 0,6 bằng cách chấm tổng quát — protocol

Chốt 2026-10-07 khoảng 23:55, trước khi chạy bất kỳ phép đo nào của protocol này. Chỉ đo offline; không sửa mã EvoMaster.
User duyệt hướng lúc 23:50 ("làm thử đi"). Thay đổi sau khi chốt ghi ở §8.

Bối cảnh: `../lexicon-r4-20261007/RESULTS.md`. A-new (lexicon rút từ nhãn vòng 4 theo luật cũ, giữ 0,6 với danh sách admin
viết tay) hơn lexicon hiện tại ở top-3, top-8. Bỏ 0,6 thì artifact-keeper rơi khỏi danh sách khả dụng (hạng 17/216), vì
điểm endpoint chỉ lấy một từ cao nhất. Đã thấy toàn bộ số của lượt đó.

## 1. Dữ liệu, lexicon, thước đo

Nguyên như `../lexicon-r4-20261007/PROTOCOL.md` §2, §4 (kiểm chéo theo nhà cung cấp 5 × 4, seed `20261006`, lần 1 là số
chính; loại 29 spec lexicon cũ đã học; top-1/3/8 theo thứ tự spec kèm khoảng; M1, M1any, M2, M5 với nhóm B viết tay,
nhóm B = RF báo thêm; 6 target). Mọi arm dùng lexicon A-new (ứng viên và đếm trên `pathHay`, luật cũ), rút lại trên phần
train của từng phần; danh sách `param` của A-new cho phá hoà.

## 2. Arm

Chuỗi so của endpoint là chuỗi runtime: `path + " " + verb + ":" + path + " " + tên trường thân cấp đỉnh`, hạ chữ thường.

| Arm | Điểm endpoint | Phần ngoài lexicon |
|---|---|---|
| A-cur | lexicon jar, từ cao nhất | 0,6 khi chuỗi so chứa từ admin viết tay |
| A-new | lexicon A-new, từ cao nhất | như A-cur |
| A-new-0 | lexicon A-new, từ cao nhất | không |
| A-new-OR | `1 − Π(1 − diem(w))` trên các từ trúng; bỏ từ trúng nào là chuỗi con của một từ trúng khác | không |
| A-new-bool | `max(từ cao nhất, diem(F))` nếu op có đặc trưng F, ngược lại từ cao nhất | F, điểm rút từ nhãn |

Đặc trưng F: op có một trường kiểu boolean (mọi vị trí, như `sim.admin_genes`) mà tên chứa một từ của danh sách cờ admin
rút theo luật vòng 4 trên phần train (`sim.derive(..., "std")["admin"]`). `diem(F)` theo công thức nhóm A:
`(df_R + 1)/(df_R + df_N + 2) × ncc/(ncc + 1)`, `df_R`/`df_N` là số op `T = 1`/`T = 0` của phần train có F, `ncc` là số
nhà cung cấp trong các op `T = 1` có F. Danh sách cờ rỗng hoặc `df_R = 0` thì F không cộng gì.

M5 theo arm: op `T = 0` mà điểm endpoint bị nâng bởi phần ngoài lexicon (0,6 ở A-cur, A-new; `diem(F)` lớn hơn từ cao nhất
ở A-new-bool; A-new-0, A-new-OR luôn 0).

## 3. Kiểm định

McNemar chính xác hai phía ghép đôi, KTC 95% bootstrap theo nhà cung cấp 2.000 lần, lần lặp 1. So: A-new-0 − A-new,
A-new-OR − A-new, A-new-bool − A-new, A-new-OR − A-new-0, A-new-bool − A-new-0, A-new-OR − A-cur, A-new-bool − A-cur.

## 4. Luật chọn

Một arm tổng quát (A-new-OR, A-new-bool) được đề xuất thay A-new khi, ở lần lặp 1:
- không thua A-new có ý nghĩa (p < 0,05) ở top-1, top-3, top-8, M1, M2;
- cả 6 target có transition trong danh sách khả dụng 8 đầu.

M5 báo kèm. Cả hai cùng đạt: báo cả, không tự chọn. Không arm nào đạt: báo phần nào gây thua; quyết định giữa A-new
(kèm 0,6) và A-new-0 (mất artifact-keeper) để cho user. Không đổi luật sau khi thấy số.

## 5. Self-test (`checks.py`, mỗi kiểm một dòng PASS/FAIL, exit 0 khi mọi kiểm đạt)

| Mã | Kiểm | Trượt thì |
|---|---|---|
| K1 | A-cur và A-new ra lại đúng số lần lặp 1 trong `../lexicon-r4-20261007/cv.json` (top-1/3/8 kèm khoảng, M1, M1any, M2, M5; nhóm B viết tay và RF) | dừng |
| K2 | Điểm OR của 3 op (artifact-keeper `PATCH /api/v1/users/{id}`, reports-api `PUT /users/{username}/role`, một op corpus có ≥ 3 từ trúng) bằng phép tính tay độc lập | dừng |
| K3 | Luật bỏ chuỗi con: chuỗi `"/collaborators"` với lexicon {`collaborator`, `collaborators`} chỉ tính `collaborators` | dừng |
| K4 | Đếm độc lập `df_R`, `df_N`, `ncc` của F trên toàn bộ dữ liệu, so với số mã đo dùng | dừng |
| K5 | Không rò rỉ: nhà cung cấp train ∩ test = ∅ ở mọi phần; spec test ∩ 29 spec cũ = ∅ | dừng |
| K6 | Đối chứng âm cho A-new-OR: xáo nhãn `T` trên phần train, top-1 phải thấp hơn bản thật | không kết luận về hạng |
| K7 | Chạy toàn bộ hai lần, hash đầu ra như nhau | dừng |
| K8 | Hàng target của A-cur và A-new trùng `../lexicon-r4-20261007/targets.json` | dừng phần target |

## 6. Đầu ra

`measure2.py`, `checks.py`, `report.py`, `cv.json`, `targets.json`, `RESULTS.md` (mọi bảng và số do `report.py` sinh).
Xong thì chụp sang `~/thesis-backups/`.

## 7. Giới hạn biết trước

- F có thể dựa trên rất ít op (số đếm thật do K4 in ra); `diem(F)` có thể thấp hoặc bằng 0 ở nhiều phần.
- OR coi các từ như bằng chứng độc lập; endpoint có nhiều trường thân được lợi.
- Giới hạn của `../lexicon-r4-20261007/PROTOCOL.md` §8 vẫn áp dụng.

## 8. Thay đổi sau khi chốt
