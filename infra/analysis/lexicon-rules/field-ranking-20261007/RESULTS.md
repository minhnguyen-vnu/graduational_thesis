# Xếp hạng từ cho nhận diện trường — kết quả

Chạy 2026-10-07 khoảng 22:40, offline, không sửa mã EvoMaster. Protocol: `PROTOCOL.md`. Lệnh: `python3 sim_rank.py .`
(25 giây). Số: `cv.json`; ranking trên toàn bộ dữ liệu: `rankings/*.csv`; chẩn đoán M2: `diag_m2.py`, `diag-m2.txt`.
Lexicon nhóm A như vòng 4 (sha256 `535265ea…`).

## 1. Kết luận

- **Nạn nhân:** ranking ngang bộ viết tay (M3 117/184 so với 117, p = 1,0) và hơn R4 (107; p = 0,021, KTC bootstrap
  −0,011 … +0,142 chứa 0). Nhận `{email}` của bamf mà không cần danh sách email: neo 6/6, R4 5/6.
- **Vai trò:** ranking làm số API báo nhầm tăng mạnh: M2 77/174 so với 17 của V (p < 0,001). M1 14 so với 18
  (p = 0,34).
- **Thấp/cao:** kiểm chéo M4 13/18 so với 15 của V (p = 0,63). Trong mẫu 16/18, V 15, R4 11.
- **Luật chọn §6:** RK đạt (không thua V có ý nghĩa ở M1, M3, M4; neo 6/6). Luật này bỏ sót M2; đây là lỗi khi viết
  protocol (§5). Luật giữ nguyên.
- **Biến thể:** RK2 và RKs cùng đạt luật thay RK (M2 giảm có ý nghĩa, không thua chỉ số nào), nhưng M2 vẫn cao hơn V
  nhiều: RK2 55, RKs 65, V 17 (p < 0,001 cả hai). RK0 không đạt: không thắng ở M1–M4, và op của artifact-keeper rơi khỏi
  8 transition đầu.

## 2. Tái lập

V và R4 khớp từng số của `../field-labelling-r4-20261006/RESULTS.md` §4 ở cả 4 lần lặp (V: M1 18, M2 17, M3 117, M4 15,
M5 4; R4 lần lặp 1–4: M3 107, 106, 117, 109; M5 165, 213, 229, 249).

## 3. Kiểm chéo, lần lặp 1

| Chỉ số | Đơn vị | V | R4 | RK | RK2 | RK0 | RKs |
|---|---|---|---|---|---|---|---|
| M1 | 52 API | 18 | 16 | 14 | 16 | 15 | 15 |
| M1any | 52 API | 26 | 23 | 27 | 26 | 26 | 26 |
| M1top | 52 API | 18 | 16 | 14 | 16 | 14 | 15 |
| M2 báo nhầm | 174 API | 17 | 17 | 77 | 55 | 77 | 65 |
| M3 | 184 op | 117 | 107 | 117 | 117 | 117 | 117 |
| M4 | 18 op | 15 | 15 | 13 | 14 | 13 | 11 |
| M5 | 10.182 op | 4 | 165 | 165 | 165 | 0 | 165 |

McNemar chính xác hai phía; KTC 95% bootstrap theo nhà cung cấp cho hiệu (arm sau − arm trước).

| So | M1 | M2 | M3 | M4 |
|---|---|---|---|---|
| RK − V | 0,34; −0,192 … +0,038 | < 0,001; +0,276 … +0,420 | 1,0; −0,029 … +0,025 | 0,63; −0,357 … +0,105 |
| RK − R4 | 0,69; −0,135 … +0,058 | < 0,001; +0,276 … +0,414 | 0,021; −0,011 … +0,142 | 0,63; −0,357 … +0,105 |
| RK2 − RK | 0,50; 0 … +0,096 | < 0,001; −0,178 … −0,080 | 1,0 | 1,0; 0 … +0,200 |
| RKs − RK | 1,0; 0 … +0,058 | < 0,001; −0,109 … −0,034 | 1,0 | 0,50; −0,353 … 0 |
| RK0 − RK | 1,0; −0,058 … +0,096 | 1,0 | 1,0 | 1,0 |
| RK2 − V (ngoài protocol) | 0,73; −0,135 … +0,058 | < 0,001; +0,155 … +0,287 | 1,0 | 1,0; −0,250 … +0,150 |
| RKs − V (ngoài protocol) | 0,51; −0,173 … +0,058 | < 0,001; +0,213 … +0,345 | 1,0 | 0,22; −0,533 … +0,059 |

RK0 − RK ở M5: 0 so với 165, p < 0,001.

Lần lặp 2–4. RK: M1 15, 15, 11; M2 79, 77, 81; M3 121, 121, 121; M4 13, 13, 14. RK2: M1 17, 18, 14; M2 47, 46, 53;
M3 117, 117, 117; M4 13, 14, 14.

Ranking thấp/cao có ở mọi phần, nên M4 kiểm chéo của RK đo chính ranking. M4 của R4 ở bảng trên chủ yếu đo danh sách
viết tay dự phòng (B dưới ngưỡng ở 3/5 phần, vòng 4 §4).

## 4. Trong mẫu (rút và đo trên toàn bộ dữ liệu)

| Chỉ số | V | R4 | RK | RK2 | RK0 | RKs |
|---|---|---|---|---|---|---|
| M1 (52) | 18 | 18 | 15 | 16 | 18 | 15 |
| M1any (52) | 26 | 25 | 33 | 28 | 30 | 33 |
| M2 (174) | 17 | 11 | 75 | 41 | 75 | 57 |
| M3 (184) | 117 | 118 | 129 | 127 | 129 | 129 |
| M4 (18) | 15 | 11 | 16 | 14 | 16 | 13 |
| M5 (10.182) | 4 | 249 | 249 | 249 | 0 | 249 |

## 5. Vì sao M2 tăng

Cổng vai trò cho 49/70 từ của ranking vai trò qua (`rankings/RK.csv`, cột `gate`). Transition đầu tiên của các API báo
nhầm khớp những từ chung (`diag-m2.txt`), RK:

| Từ | API | Ví dụ thật | Trường khớp |
|---|---|---|---|
| `code` | 20 | credas.co.uk `PUT /api/registrations/{id}/contact-details` | `diallingCode` |
| `create` | 16 | apideck.com `PATCH /file-storage/shared-links/{id}` | `created_at` |
| `client` | 10 | authentiq.io `PUT /client/{client_id}` | |
| `post` | 10 | gamesparks.net `PUT /restv2/game/{apiKey}/admin/billingDetails` | |
| `custom` | 10 | onsched.com `PUT /consumer/v1/appointments/{id}/book` | |

RK2 bỏ được `code`, `client`, `post`, `custom`, còn `create` ở 21 API.

Giải thích (chưa kiểm bằng arm riêng): tỷ lệ `pos/any` của cổng chỉ đếm trường trong op `T = 1`. Một từ như `code` hiếm
khi xuất hiện trong op đổi quyền nên trông chính xác, nhưng ở runtime nó khớp trường của mọi op. Luật vòng 4 đếm cùng cách;
điều kiện ≥ 3 nhà cung cấp và bootstrap chặn những từ này.

Đếm `any` trên mọi op thay vì op `T = 1` không sửa được (`diag_gate_all.py`, `diag-gate-all.txt`, ngoài protocol): cổng
còn 14 từ; `permission` (9/21 nhà cung cấp) và `admin` (6/25) rơi ra, trong khi từ của một nhà cung cấp như `sftp`,
`ultra`, `timesheet` vẫn qua vì chúng hiếm ở mọi nơi.

Luật chọn §6 chỉ xét M1, M3, M4. Bỏ sót M2 là lỗi của protocol; số M2 ở trên là lý do chính để không dùng RK nguyên trạng
dù RK đạt luật.

## 6. Neo và spec thật

Neo theo tên trường (6 target như vòng 4): V 6/6, R4 5/6 (mất `email` của bamf), RK, RK2, RK0, RKs đều 6/6.

Chạy runtime mô phỏng trên spec mà EvoMaster đã dùng:

| Target, op | V | R4 | RK | RK2 | RK0 | RKs |
|---|---|---|---|---|---|---|
| bamf `PATCH /api/v1/users/{email}`: hạng trong transition khả dụng | 3/5 | 3/5 | 3/5 | 3/5 | 3/5 | 3/5 |
| bamf: trường nạn nhân | `path:email` | không có | `path:email` | `path:email` | `path:email` | `path:email` |
| artifact-keeper `PATCH /api/v1/users/{id}`: hạng | 1/2 | 1/1 | 4/4 | 4/4 | ngoài 8 đầu | 2/2 |

Trường nạn nhân của artifact-keeper là `path:id` ở mọi arm. Giá trị hạ quyền đứng đầu là `[]` (bamf) và `false`
(artifact-keeper) ở mọi arm. Ở RK0 op của artifact-keeper chỉ còn điểm 0,222 (điểm path).

## 7. Giới hạn

- Chiều của boolean không đo được (protocol §7): RK nhận `restrict` là từ vai trò, runtime sẽ ghi `restricted = false`.
- Mô phỏng chưa đối chiếu với lượt EvoMaster thật.
- Ranking đặt ra sau khi thấy kết quả vòng 4. Hai cặp so với V của RK2, RKs thêm sau khi chạy (protocol §8), chỉ để báo.
- M4 chỉ có 18 op từ 11 nhà cung cấp.
