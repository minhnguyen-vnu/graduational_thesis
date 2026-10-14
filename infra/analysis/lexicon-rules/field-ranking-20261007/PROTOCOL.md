# Xếp hạng từ cho nhận diện trường — protocol

Chốt 2026-10-07 khoảng 22:30, trước khi chạy mô phỏng nào cho ranking. Chỉ đo offline, không sửa mã EvoMaster.
Thay đổi sau khi chốt ghi ở §8.

Bối cảnh: danh sách rút vòng 4 chỉ còn 8 từ (`../field-labelling-r4-20261006/RESULTS.md`). Ranking giữ mọi từ có bằng
chứng, mỗi từ một điểm, và runtime chọn trường điểm cao nhất thay vì trường đầu tiên khớp danh sách.

Đã thấy trước khi chốt (nêu ra để người đọc biết): điểm toàn bộ dữ liệu của các ranking ở §2 (chạy trong scratchpad,
2026-10-07), gồm `admin` 13 trường dương / 16 âm và 6/9 nhà cung cấp trong ranking vai trò gộp; chưa thấy số đo nào.

## 1. Dữ liệu

Nhãn cuối vòng 4 `../field-labelling-r4-20261006/final-all.csv` và dòng `rows-all.jsonl`: 10.381 op ghi, 230 API.
Không gán nhãn thêm.

## 2. Điểm

Công thức nhóm A, nguyên văn (`docs/lexicon.md`, mục điểm):

```
diem(w) = (dp + 1) / (dp + dn + 2)  ×  ncc / (ncc + 1)
```

`dp`, `dn`: số mục dương, âm có tên (hạ chữ thường) chứa `w`. `ncc`: số nhà cung cấp có ít nhất một mục dương chứa `w`.
Ứng viên: token tách từ tên mục dương (hàm `tokens` vòng 4), cộng nguyên tên mục dương, cộng thuật ngữ SCIM/NIST của
vòng 4; giữ ứng viên có `dp ≥ 1`. Bỏ từ chứa một từ ngắn hơn có trong cùng ranking. Điểm của một trường hay một giá
trị = điểm cao nhất của các từ trong ranking mà tên nó chứa, 0 nếu không có.

| Ranking | Mục | Dương | Âm |
|---|---|---|---|
| Nạn nhân | mọi trường của op `T = 1` | trường trong cột `victim` | trường còn lại |
| Vai trò (mọi kiểu) | mọi trường của op `T = 1` | trường trong cột `role` | trường còn lại |
| Thấp | giá trị của enum có thứ tự (`order` chứa `<`) | giá trị ở mức thấp nhất | giá trị ở mức khác |
| Cao | như trên | giá trị ở mức cao nhất | giá trị ở mức khác |

Cổng vai trò: một từ vai trò được dùng để nhận trường vai trò khi `pos/any ≥ 0,5` tính theo nhà cung cấp, đúng điều kiện
tỷ lệ của luật vòng 4, bỏ hai điều kiện độ ủng hộ (≥ 3 nhà cung cấp, bootstrap). Nạn nhân, thấp, cao không có cổng.

## 3. Runtime mô phỏng (RK)

Dựa trên `../field-labelling-r4-20261006/sim.py`, chỉ thay các chỗ sau:

- **Chọn transition:** giữ nguyên (điểm path nhóm A, cộng 0,6 khi chuỗi so chứa một từ của danh sách admin; RK dùng danh
  sách admin của R4 rút trên cùng phần train).
- **Trường vai trò:** trường (mọi kiểu, gồm tên schema như `sim.py`) chứa một từ vai trò qua cổng. Thứ tự: điểm giảm dần,
  hoà thì theo thứ tự trường.
- **Giá trị hạ quyền:** `k(v) = diem_thap(v) − diem_cao(v)`. Danh sách = `false` (nếu có trường vai trò boolean) + giá trị
  enum có `k > 0` theo `k` giảm dần + `[]` + `1, 0, 2` + giá trị enum còn lại theo `k` giảm dần + `user, viewer, guest,
  member, basic`; điều kiện của `[]`, số, chuỗi như `sim.py`. Hoà thì theo thứ tự trong spec.
- **Nạn nhân:** path trước, rồi body, rồi query cấp đỉnh; trong mỗi chỗ chọn trường kiểu chuỗi/số có điểm nạn nhân cao
  nhất, điểm > 0; hoà thì theo thứ tự trường. Bỏ ba tầng và danh sách email.

## 4. Arm

| Arm | Khác RK ở |
|---|---|
| V | bộ viết tay (`sim.HARD`) |
| R4 | danh sách rút vòng 4 |
| RK | — |
| RK2 | mỗi ranking chỉ giữ từ có `ncc ≥ 2` (lọc trước khi bỏ từ chứa từ khác) |
| RK0 | bỏ cộng 0,6 khi chọn transition |
| RKs | vai trò tách theo kiểu: ranking vai trò trên trường không boolean, ranking cờ trên trường boolean, mỗi ranking một cổng |

## 5. Đo

- Chỉ số M1, M1any, M2, M3, M4, M5 như vòng 4. Thêm M1top (phụ): trường vai trò đứng đầu của transition đầu tiên nằm
  trong cột `role`; với arm danh sách, trường đứng đầu là trường đầu tiên khớp danh sách vai trò, không có thì trường
  boolean đầu tiên khớp danh sách admin.
- Kiểm chéo nhóm theo nhà cung cấp 5 phần × 4 lần lặp, seed `20261006`, lần 1 là số chính. Ranking rút lại trên phần
  train của từng phần.
- McNemar chính xác hai phía ghép đôi; KTC 95% bootstrap theo nhà cung cấp 2.000 lần, lần lặp 1.
- So: RK với V, RK với R4, mỗi biến thể với RK.
- Số trong mẫu (rút và đo trên toàn bộ dữ liệu), báo kèm.
- Neo: 6 target như vòng 4 (trường vai trò nhận được, trường nạn nhân điểm > 0). Thêm kiểm trên spec thật của bamf
  (`PATCH /api/v1/users/{email}`, `{"roles": []}`) và artifact-keeper (`PATCH /api/v1/users/{id}`, `is_admin`): hạng của
  op đó trong danh sách transition khả dụng, trường nạn nhân chọn được, giá trị hạ quyền đứng đầu.

## 6. Luật chọn

- RK được đề xuất thay danh sách khi, ở lần lặp 1, RK không thua V có ý nghĩa (p < 0,05) ở M1, M3, M4, và số neo không ít
  hơn V.
- Một biến thể thay RK khi nó thắng RK có ý nghĩa ở ít nhất một trong M1–M4, không thua có ý nghĩa ở chỉ số nào, và số
  neo không ít hơn. RK0 thêm điều kiện: op của artifact-keeper vẫn nằm trong 8 transition đầu.
- Nhiều biến thể cùng đạt: báo cả, không tự ghép.
- Không đổi luật sau khi thấy số.

## 7. Giới hạn biết trước

- Boolean: runtime ghi `false` để hạ quyền. Trường như `restricted` hạ quyền khi `true`; nhãn không ghi chiều, nên mô
  phỏng không đo được chỗ này.
- Mô phỏng chưa đối chiếu với lượt EvoMaster thật.
- Ranking đặt ra sau khi thấy kết quả vòng 4; công thức điểm lấy nguyên từ nhóm A để không có tham số mới.

## 8. Thay đổi sau khi chốt

- Sau lượt chạy đầu: thêm hai cặp kiểm định RK2 − V, RKs − V vào `sim_rank.py` (chỉ để báo, không dùng trong luật §6),
  chạy lại; mọi số khác không đổi.
- Thêm chẩn đoán `diag_m2.py` (từ nào làm transition báo nhầm) và `diag_gate_all.py` (cổng đếm trên mọi op), ngoài
  protocol.
- Luật §6 không xét M2. Phát hiện sau khi thấy số; luật giữ nguyên, ghi ở `RESULTS.md` §5.
