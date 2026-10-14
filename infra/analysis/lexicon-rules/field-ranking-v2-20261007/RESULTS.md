# Lọc theo vòng 4, chọn theo ranking — kết quả

Chạy 2026-10-07 khoảng 22:55, offline, không sửa mã EvoMaster. Protocol: `PROTOCOL.md`. Lệnh: `python3 sim_rf.py .`
Số: `cv.json`; chẩn đoán M4: `diag_m4.py`, `diag-m4.txt`. Ranking và lexicon nhóm A như `../field-ranking-20261007/`.

## 1. Kết luận

- **RF đạt luật §5:** ở lần lặp 1, RF không thua V có ý nghĩa ở chỉ số nào trong M1, M1top, M2, M3, M4; neo 6/6 như V.
- **M2 về lại 17/174**, bằng V (p = 1,0). Bộ lọc theo vòng 4 bỏ được 77 API báo nhầm của RK.
- **Ranking nạn nhân** là phần có lợi: M3 từ 107 (R4) lên 117, bằng V (RFv − R4 p = 0,021, KTC −0,011 … +0,142 chứa 0).
  Nhận `{email}` của bamf; bỏ được danh sách email và ba tầng.
- **Ranking enum:** kiểm chéo M4 13/18 so với 15 của V (p = 0,5); trong mẫu 15/18, bằng V, hơn R4 (11).
- **Ranking trường quyền đứng đầu:** không đổi gì (M1top = M1 ở mọi arm).
- **M1** 16 so với 18 của V (p = 0,69): đến từ bộ lọc vòng 4 (`role, permission`), RF và R4 như nhau.
- **M5** 165 so với 4 của V (p < 0,001): đến từ điểm 0,6 với danh sách admin `admin` của R4, ngoài luật §5, chưa xử lý.

## 2. Kiểm chéo, lần lặp 1

| Chỉ số | Đơn vị | V | R4 | RFv | RFe | RF |
|---|---|---|---|---|---|---|
| M1 | 52 API | 18 | 16 | 16 | 16 | 16 |
| M1any | 52 API | 26 | 23 | 23 | 23 | 23 |
| M1top | 52 API | 18 | 16 | 16 | 16 | 16 |
| M2 báo nhầm | 174 API | 17 | 17 | 17 | 17 | 17 |
| M3 | 184 op | 117 | 107 | 117 | 107 | 117 |
| M4 | 18 op | 15 | 15 | 15 | 13 | 13 |
| M5 | 10.182 op | 4 | 165 | 165 | 165 | 165 |

McNemar chính xác hai phía; KTC 95% bootstrap theo nhà cung cấp cho hiệu (arm sau − arm trước).

| So | M1 | M1top | M2 | M3 | M4 |
|---|---|---|---|---|---|
| RF − V | 0,69; −0,135 … +0,038 | 0,69; −0,135 … +0,038 | 1,0; −0,034 … +0,040 | 1,0; −0,029 … +0,025 | 0,50; −0,286 … 0 |
| RF − R4 | 1,0 | 1,0 | 1,0 | 0,021; −0,011 … +0,142 | 0,50; −0,286 … 0 |
| RFv − R4 | 1,0 | 1,0 | 1,0 | 0,021; −0,011 … +0,142 | 1,0 |
| RFe − R4 | 1,0 | 1,0 | 1,0 | 1,0 | 0,50; −0,286 … 0 |

RF − V ở M5: 165 so với 4, p < 0,001, KTC +0,005 … +0,032.

Lần lặp 2–4, RF: M1 16, 16, 18; M2 11, 11, 18; M3 121, 121, 121; M4 12, 12, 13. V không đổi giữa các lần lặp.

M4 của R4 trong kiểm chéo chủ yếu đo danh sách viết tay dự phòng (B dưới ngưỡng ở 3/5 phần, vòng 4 §4). Ranking enum có
ở mọi phần, nên RFe − R4 gần như là ranking so với bộ viết tay.

## 3. Hai op M4 mất so với V (lần lặp 1)

| Op | Thứ tự đã gán | V đứng đầu | RF đứng đầu |
|---|---|---|---|
| appcenter.ms `PATCH /v0.1/apps/{owner_name}/{app_name}/users/{user_email}` | `viewer<developer<manager` | `viewer` | `manager` |
| flat.io `PUT /organizations/users/{user}` | `user<billing=teacher<admin` | `user` | `billing` |

`viewer` và `user` ở mức thấp nhất chỉ có ở đúng nhà cung cấp đang bị giữ lại làm test, nên ranking của phần train không
có chúng; mọi giá trị điểm 0 và thứ tự spec quyết định. Bộ viết tay có `view` và `user`.

## 4. Trong mẫu

| Chỉ số | V | R4 | RFv | RFe | RF |
|---|---|---|---|---|---|
| M1 (52) | 18 | 18 | 18 | 18 | 18 |
| M2 (174) | 17 | 11 | 11 | 11 | 11 |
| M3 (184) | 117 | 118 | 129 | 118 | 129 |
| M4 (18) | 15 | 11 | 11 | 15 | 15 |
| M5 (10.182) | 4 | 249 | 249 | 249 | 249 |

## 5. Neo và spec thật

Neo theo tên trường: V 6/6, R4 5/6, RFv 6/6, RFe 5/6, RF 6/6. Arm thiếu ranking nạn nhân mất `email` của bamf.

| Target, op | V | R4 | RF |
|---|---|---|---|
| bamf `PATCH /api/v1/users/{email}`: hạng / số transition khả dụng | 3/5 | 3/5 | 3/5 |
| bamf: trường nạn nhân | `path:email` | không có | `path:email` |
| artifact-keeper `PATCH /api/v1/users/{id}`: hạng | 1/2 | 1/1 | 1/1 |

Giá trị hạ quyền đứng đầu: `[]` (bamf), `false` (artifact-keeper) ở mọi arm.

## 6. Giới hạn

- Mô phỏng chưa đối chiếu với lượt EvoMaster thật.
- Thiết kế đặt ra sau khi thấy số của `../field-ranking-20261007/`.
- M4 chỉ có 18 op từ 11 nhà cung cấp; hai op mất ở §3 là giới hạn dữ liệu, ranking không đoán được từ chưa thấy.
