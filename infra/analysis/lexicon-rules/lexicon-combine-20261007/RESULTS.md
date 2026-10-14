# Thay điểm 0,6 bằng cách chấm tổng quát — kết quả

Chạy 2026-10-07/08, offline, không sửa mã EvoMaster. Protocol: `PROTOCOL.md`. Lệnh: `python3 checks.py pre`,
`python3 measure2.py .`, `python3 checks.py post`, `python3 report.py`. Mọi bảng và con số do `report.py` sinh từ
`cv.json`, `targets.json`, `checks-*.txt`.

## 1. Kết luận

- **A-new-OR không đạt luật §4**: mất target artifact-keeper (hạng 14/216).
  So với A-new: top-1 21/26 (p = 0,359), top-3 35/36 (p = 1,000), top-8 45/44 (p = 1,000), M1 15/17 (p = 0,688), M2 18/18 (p = 1,000).
- **A-new-bool không đạt luật §4**: mất target artifact-keeper (hạng 9/216).
  So với A-new: top-1 24/26 (p = 0,625), top-3 34/36 (p = 0,625), top-8 42/44 (p = 0,500), M1 16/17 (p = 1,000), M2 18/18 (p = 1,000).
- artifact-keeper `PATCH /api/v1/users/{id}`: A-cur hạng 1/216, điểm 0,6000; A-new hạng 1/216, điểm 0,6000; A-new-0 hạng 22/216, điểm 0,1627; A-new-OR hạng 14/216, điểm 0,2931; A-new-bool hạng 9/216, điểm 0,2532.
  Runtime chỉ xét 8 endpoint đầu (`MAX_TRANSITION_CANDIDATES = 8`); danh sách khả dụng của A-new-bool là `[]`, của A-new-OR là `['POST /api/v1/users']`.
- Đặc trưng F trên toàn bộ dữ liệu: cờ `admin`, 12 op đổi quyền, 30 op không, 6 nhà cung cấp, điểm 0,2532. Theo phần (lần lặp 1): 0,1750; danh sách cờ rỗng; 0,2183; 0,2857; 0,2532.
- Cả hai arm tổng quát không đạt; theo §4, chọn giữa A-new (kèm 0,6, giữ artifact-keeper) và A-new-0 (bỏ 0,6, mất
  artifact-keeper) là việc của user. A-new-0 so với A-new: top-1 24/26 (p = 0,625), top-3 33/36 (p = 0,250), top-8 41/44 (p = 0,250), M5 0/4.
- Đối chứng âm (A-new-OR): top-1 nhãn thật 21, nhãn xáo 0, trên 47 spec.

## 2. Self-test

| Mã | Kết quả | Chi tiết |
|---|---|---|
| K2 | PASS | lexicon equals lexicon-new.csv: True; PATCH /api/v1/users/{id}: words ['users', 'admin', 'email', 'name'] hand 0.293071 code 0.293071; PUT /users/{username}/role: words ['username', 'users', 'role'] hand 0.414434 code 0.414434; POST /file-storage/drive-groups: words ['groups', 'name', 'update'] hand 0.096762 code 0.096762 |
| K3 | PASS | nested -> ['collaborators']; disjoint -> ['collaborator', 'user'] |
| K4 | PASS | flag ['admin']; independent 12/30/6 vs code 12/30/6; score 0.2532; T=1 examples ['gitea.io PATCH /admin/users/{username}', 'gitlab.com PUT /v3/users/{id}', 'files.com POST /group_users'] |
| K1 | PASS | A-cur, A-new repeat 1 vs ../lexicon-r4-20261007/cv.json: 0 differences [] |
| K5 | PASS | 20 folds; excluded 29 specs = old training specs |
| K6 | PASS | A-new-OR top-1 real 21, permuted 0, of 47 specs; equals arm repeat 1 (21) |
| K8 | PASS | A-cur, A-new target rows: 12 here, 12 before, identical True |
| K7 | PASS | second full run, differing files: none |

## 3. Kiểm chéo, lần lặp 1, nhóm B = bộ viết tay

Hạng: số spec có op `T = 1` trong k op đầu, theo thứ tự spec; trong ngoặc là xấu nhất–tốt nhất khi hoà điểm.

| Chỉ số | Đơn vị | A-cur | A-new | A-new-0 | A-new-OR | A-new-bool |
|---|---|---|---|---|---|---|
| top-1 | 47 spec | 19 (17–24) | 26 (19–28) | 24 (17–26) | 21 (21–21) | 24 (17–26) |
| top-3 | 47 spec | 27 (26–29) | 36 (32–39) | 33 (29–37) | 35 (35–35) | 34 (30–36) |
| top-8 | 47 spec | 37 (35–37) | 44 (42–46) | 41 (39–44) | 45 (45–45) | 42 (40–44) |
| M1 | 43 API | 15 | 17 | 15 | 15 | 16 |
| M1any | 43 API | 21 | 20 | 17 | 20 | 18 |
| M2 | 154 API | 17 | 18 | 18 | 18 | 18 |
| M5 | 8652 op | 4 | 4 | 0 | 0 | 7 |

## 4. Kiểm định, lần lặp 1

McNemar chính xác hai phía; KTC 95% bootstrap theo nhà cung cấp cho hiệu (arm sau − arm trước).

| So | top-1 | top-3 | top-8 | M1 | M2 | M5 |
|---|---|---|---|---|---|---|
| A-new-0 − A-new | 0,625; -0,128 … +0,043 | 0,250; -0,149 … 0,000 | 0,250; -0,149 … 0,000 | 0,625; -0,140 … +0,047 | 1,000; 0,000 … 0,000 | 0,125; -0,001 … 0,000 |
| A-new-OR − A-new | 0,359; -0,277 … +0,064 | 1,000; -0,149 … +0,106 | 1,000; -0,043 … +0,106 | 0,688; -0,163 … +0,070 | 1,000; 0,000 … 0,000 | 0,125; -0,001 … 0,000 |
| A-new-bool − A-new | 0,625; -0,128 … +0,043 | 0,625; -0,128 … +0,043 | 0,500; -0,106 … 0,000 | 1,000; -0,116 … +0,047 | 1,000; 0,000 … 0,000 | 0,508; -0,000 … +0,001 |
| A-new-OR − A-new-0 | 0,607; -0,234 … +0,085 | 0,754; -0,085 … +0,170 | 0,125; +0,021 … +0,170 | 1,000; -0,116 … +0,116 | 1,000; 0,000 … 0,000 | 1,000; 0,000 … 0,000 |
| A-new-bool − A-new-0 | 1,000; 0,000 … 0,000 | 1,000; -0,043 … +0,085 | 1,000; 0,000 … +0,064 | 1,000; 0,000 … +0,070 | 1,000; 0,000 … 0,000 | 0,016; 0,000 … +0,002 |
| A-new-OR − A-cur | 0,832; -0,149 … +0,234 | 0,077; +0,021 … +0,319 | 0,021; +0,064 … +0,298 | 1,000; -0,140 … +0,140 | 1,000; -0,026 … +0,039 | 0,125; -0,001 … 0,000 |
| A-new-bool − A-cur | 0,424; -0,106 … +0,319 | 0,189; -0,043 … +0,340 | 0,227; -0,021 … +0,234 | 1,000; -0,093 … +0,140 | 1,000; -0,026 … +0,039 | 0,508; -0,000 … +0,001 |

Lần lặp 2–4:
- Lần 2: A-cur 19/27/37, M1 15, M2 17; A-new 26/38/40, M1 16, M2 18; A-new-0 24/35/37, M1 14, M2 18; A-new-OR 24/35/44, M1 17, M2 17; A-new-bool 25/35/37, M1 16, M2 18 (top-1/top-3/top-8).
- Lần 3: A-cur 19/27/37, M1 15, M2 17; A-new 27/36/42, M1 17, M2 18; A-new-0 25/34/40, M1 16, M2 18; A-new-OR 23/37/44, M1 16, M2 17; A-new-bool 25/34/38, M1 16, M2 18 (top-1/top-3/top-8).
- Lần 4: A-cur 19/27/37, M1 15, M2 17; A-new 25/36/43, M1 17, M2 17; A-new-0 23/34/41, M1 16, M2 17; A-new-OR 23/35/44, M1 17, M2 17; A-new-bool 21/34/41, M1 14, M2 17 (top-1/top-3/top-8).

Nhóm B = RF, lần lặp 1: A-cur M1 13, M2 17, M5 4; A-new M1 15, M2 18, M5 4; A-new-0 M1 15, M2 18, M5 0; A-new-OR M1 14, M2 20, M5 0; A-new-bool M1 16, M2 18, M5 7.

## 5. Target (rút trên toàn bộ dữ liệu)

Mỗi ô: hạng theo thứ tự spec (khoảng khi hoà) / số op ghi; điểm; vị trí trong danh sách khả dụng (8 đầu, lọc nhóm B
viết tay), `—` nếu không có.

| Target | A-cur | A-new | A-new-0 | A-new-OR | A-new-bool |
|---|---|---|---|---|---|
| reports-api | 1/6; 0,2727; 1 | 1/6; 0,1706; 1 | 1/6; 0,1706; 1 | 1/6; 0,4144; 1 | 1/6; 0,1706; 1 |
| vampi-seeded | 1/8; 0,2727; 1 | 3 (1–3)/8; 0,1706; 1 | 3 (1–3)/8; 0,1706; 1 | 1/8; 0,4144; 1 | 3 (1–3)/8; 0,1706; 1 |
| pyLoad | 1/62; 0,5455; 1 | 6 (3–10)/62; 0,1517; 3 | 6 (3–10)/62; 0,1517; 3 | 2/62; 0,2383; 2 | 6 (3–10)/62; 0,1517; 3 |
| Airflow | 2 (1–2)/68; 0,3000; 1 | 1/68; 0,1706; 1 | 1/68; 0,1706; 1 | 1/68; 0,3641; 1 | 1/68; 0,1706; 1 |
| artifact-keeper | 1/216; 0,6000; 1 | 1/216; 0,6000; 1 | 22/216; 0,1627; — | 14/216; 0,2931; — | 9/216; 0,2532; — |
| bamf | 3 (2–3)/50; 0,3000; 3 | 1/50; 0,1627; 1 | 1/50; 0,1627; 1 | 1/50; 0,2333; 1 | 1/50; 0,1627; 1 |

Số target có transition trong danh sách khả dụng: A-cur 6/6, A-new 6/6, A-new-0 5/6, A-new-OR 5/6, A-new-bool 5/6.

Mười endpoint đầu của artifact-keeper:
- A-new-OR: `POST /api/v1/repositories 0.5122`; `POST /api/v1/groups/{id}/members 0.4613`; `DELETE /api/v1/groups/{id}/members 0.4613`; `POST /api/v1/users 0.3931`; `PUT /api/v1/permissions/{id} 0.3859`; `POST /api/v1/permissions 0.3859`; `PUT /api/v1/repositories/{key}/members 0.3440`; `POST /api/v1/repositories/{key}/members 0.3440`; `DELETE /api/v1/repositories/{key}/members/{member_key} 0.3440`; `PUT /api/v1/admin/sso/oidc/{id} 0.3049`.
- A-new-bool: `PUT /api/v1/repositories/{key}/members 0.3380`; `POST /api/v1/groups/{id}/members 0.3380`; `POST /api/v1/repositories/{key}/members 0.3380`; `DELETE /api/v1/groups/{id}/members 0.3380`; `DELETE /api/v1/repositories/{key}/members/{member_key} 0.3380`; `POST /api/v1/repositories 0.3367`; `PUT /api/v1/permissions/{id} 0.3030`; `POST /api/v1/permissions 0.3030`; `PATCH /api/v1/users/{id} 0.2532`; `POST /api/v1/users 0.2532`.

## 6. Giới hạn

- F dựa trên 12 op đổi quyền của 6 nhà cung cấp; ở một phần của lần lặp 1 danh sách cờ rỗng nên F không cộng gì.
- OR coi các từ như bằng chứng độc lập.
- Giới hạn của `../lexicon-r4-20261007/PROTOCOL.md` §8 vẫn áp dụng; mô phỏng chưa đối chiếu với lượt EvoMaster thật.
