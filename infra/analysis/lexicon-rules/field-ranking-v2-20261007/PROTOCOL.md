# Lọc theo vòng 4, chọn theo ranking — protocol

Chốt 2026-10-07 22:45, trước khi chạy mô phỏng nào của protocol này. Chỉ đo offline, không sửa mã EvoMaster. Thay đổi
sau khi chốt ghi ở §7.

Bối cảnh: `../field-ranking-20261007/RESULTS.md`. Ranking vai trò làm cổng lọc transition quá rộng (M2 77/174 so với 17
của V), vì danh sách trường quyền đồng thời là bộ lọc transition (`RestSecurityBuilder.kt:523–530`, `:965–967`).
Ranking nạn nhân ngang V ở M3 và nhận `{email}` của bamf. Đã thấy toàn bộ số của lượt đó.

## 1. Dữ liệu và điểm

Dữ liệu, công thức điểm, bốn ranking (nạn nhân, vai trò mọi kiểu, thấp, cao), luật bỏ từ chứa từ ngắn hơn: nguyên như
`../field-ranking-20261007/PROTOCOL.md` §1–§2, arm RK. Không dùng cổng vai trò của RK.

## 2. Runtime mô phỏng (RF)

| Việc | RF dùng |
|---|---|
| Chấm điểm transition, cộng 0,6 | như R4 (lexicon nhóm A, danh sách admin của R4) |
| Lọc transition: có trường quyền không | như R4: trường khớp danh sách vai trò R4, hoặc trường boolean khớp danh sách admin R4 |
| Trường quyền đứng đầu (M1top) | trong các trường qua lọc, điểm ranking vai trò cao nhất; hoà theo thứ tự trường |
| Thứ tự giá trị hạ quyền | như RK: `false` nếu có trường admin boolean, giá trị enum có `k > 0` theo `k` giảm dần, `[]`, số, enum còn lại theo `k`, chuỗi; điều kiện của từng phần theo trường qua lọc |
| Trường nạn nhân | như RK: path, body, query; điểm ranking nạn nhân cao nhất, > 0 |

Tập giá trị hạ quyền của RF trùng tập của R4 (chỉ khác thứ tự), nên bộ lọc transition của RF và R4 như nhau.

## 3. Arm

| Arm | Nạn nhân | Thứ tự enum | Trường quyền đứng đầu |
|---|---|---|---|
| V | viết tay | viết tay | viết tay |
| R4 | R4 | R4 | R4 |
| RFv | ranking | R4 | R4 |
| RFe | R4 | ranking | R4 |
| RF | ranking | ranking | ranking |

Mỗi arm RFv, RFe khác R4 một biến; RF gộp cả ba.

## 4. Đo

- Chỉ số M1, M1any, M1top, M2, M3, M4, M5 như `../field-ranking-20261007/PROTOCOL.md` §5.
- Kiểm chéo theo nhà cung cấp 5 phần × 4 lần lặp, seed `20261006`, lần 1 là số chính; ranking rút lại trên phần train.
- McNemar chính xác hai phía ghép đôi; KTC 95% bootstrap theo nhà cung cấp 2.000 lần, lần lặp 1.
- So: RF − V, RF − R4, RFv − R4, RFe − R4.
- Số trong mẫu, neo 6 target, kiểm trên spec bamf và artifact-keeper: như lượt trước.

## 5. Luật chọn

- RF được đề xuất thay bộ viết tay cho phần nhận diện trường khi, ở lần lặp 1, RF không thua V có ý nghĩa (p < 0,05) ở
  M1, M1top, M2, M3, M4, và số neo không ít hơn V.
- M5 do danh sách admin cho điểm 0,6 quyết định; RF giữ danh sách của R4. M5 được báo và xử lý riêng, không nằm trong luật
  này.
- RFv, RFe chỉ để quy công cho từng phần, không dùng để chọn.
- Không đổi luật sau khi thấy số.

## 6. Giới hạn biết trước

- Chiều của boolean không đo được.
- Mô phỏng chưa đối chiếu với lượt EvoMaster thật.
- Thiết kế này đặt ra sau khi thấy số lượt trước.

## 7. Thay đổi sau khi chốt

- Thêm chẩn đoán `diag_m4.py` (op M4 mà V và RF khác nhau, lần lặp 1), ngoài protocol.
