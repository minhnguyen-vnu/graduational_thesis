# Rút lexicon nhóm A từ nhãn vòng 4 — kết quả

Chạy 2026-10-07, offline, không sửa mã EvoMaster, không chép lexicon mới vào `core/src/main/resources/`. Protocol:
`PROTOCOL.md` (chốt trước 23:29; thay đổi sau khi chốt ở §9). Lệnh: `python3 checks.py pre`, `python3 measure.py .`,
`python3 checks.py post`, `python3 report.py`. Mọi bảng và mọi con số trong file này do `report.py` sinh từ `cv.json`,
`targets.json`, `candidates-*.csv`, `checks-*.txt`.

## 1. Kết luận

- **Luật §6: A-newV1-0 không đạt**: số target có transition trong danh sách khả dụng 5/6 so với 6/6 của A-cur (mất artifact-keeper). Ở top-1, top-3, top-8, M1, M2 nó không thua A-cur có ý nghĩa.
  Không có điểm 0,6, `PATCH /api/v1/users/{id}` của artifact-keeper đứng hạng 17/216 (điểm 0,1548).
- **Đổi dữ liệu** (A-new − A-cur, cùng luật cũ, nhãn vòng 4): top-1 26 so với 19 (p = 0,189), top-3 36 so với 27 (p = 0,049),
  top-8 44 so với 37 (p = 0,039) trên 47 spec; M1 17 so với 15 (p = 0,625); M2 18 so với 17 (p = 1,000). Target 6/6.
- **Đếm trên chuỗi runtime** (A-newV1 − A-new): top-1 24 so với 26 (p = 0,625), top-3 30 so với 36 (p = 0,070), top-8 39 so với 44
  (p = 0,062); M2 22 so với 18 (p = 0,289).
- **Bỏ điểm 0,6** (A-newV1-0 − A-newV1): M5 0 so với 4 (p = 0,125); top-1 22 so với 24; mất target artifact-keeper.
- **Đối chứng âm:** trên 47 spec test của lần lặp 1, top-1 với nhãn thật 22, với nhãn xáo 3, kỳ vọng ngẫu nhiên 2,11.
- Theo luật §6, không chọn arm khác thay A-newV1-0. A-new hơn A-cur có ý nghĩa ở top-3, top-8; A-newV1 không được so trực tiếp
  với A-cur trong protocol. A-new vẫn giữ điểm 0,6 với danh sách admin viết tay.

## 2. Self-test

| Mã | Kết quả | Chi tiết |
|---|---|---|
| C1 | PASS | old labels -> 53 path, 45 param; sha 535265ea4644 vs jar 535265ea4644 |
| C2 | PASS | V0+V1 train/test blocks (45 lines) identical to rank-field.txt; V1 test: thu tu spec: top-1 4/6 = 0.667 / top-3 5/6 = 0.833 / top-8 6/6 = 1.000 |
| C3 | PASS | repeat 1 with jar lexicon: hard M1 18/52 (ref 18/52), hard M1any 26/52 (ref 26/52), hard M2 17/174 (ref 17/174), hard M5 4/10182 (ref 4/10182), derived M1 16/52 (ref 16/52), derived M1any 23/52 (ref 23/52), derived M2 17/174 (ref 17/174), derived M5 165/10182 (ref 165/10182) |
| C4 | PASS | rows 10381 unique 10381 T=1 199 providers-with-T 56 ops-with-row 10381 |
| C5 | PASS | old rows 768 in 44 specs; not found in round-4 spec of same id: 0 [] |
| C11 | PASS | tier1 match; tier2 match; tier2b match; airflow match; artifact-keeper top-8 vs AF2 log: match (log 8, mine 8, only-log [], only-mine []) |
| C6 | PASS | newV1 permission 23/136/12 vs 23/136/12; new permission 11/81/4 vs 11/81/4; newV1 admin 37/249/14 vs 37/249/14; new admin 22/197/8 vs 22/197/8; newV1 user 132/956/39 vs 132/956/39; new user 115/625/33 vs 115/625/33 |
| C7 | PASS | 20 folds checked; excluded 29 = specs with old training rows 29, present in round-4 corpus 29 |
| C8 | PASS | top-1 real 22, permuted 3, random expected 2.11, of 47 specs; real == A-newV1-0 repeat 1 (22) |
| C10 | PASS | lexicon-new.csv 130 path 57 param ok=True; lexicon-newV1.csv 386 path 57 param ok=True |
| C9 | PASS | second full run, differing files: none |

Lượt đầu trượt C7 và C9; nguyên nhân và cách sửa ở `PROTOCOL.md` §9. Số kiểm chéo không đổi sau khi sửa.

## 3. Kiểm chéo, lần lặp 1, nhóm B = bộ viết tay

Hạng: số spec có op `T = 1` trong k op đầu, theo thứ tự spec; trong ngoặc là xấu nhất–tốt nhất khi hoà điểm.

| Chỉ số | Đơn vị | A-cur | A-new | A-newV1 | A-newV1-0 |
|---|---|---|---|---|---|
| top-1 | 47 spec | 19 (17–24) | 26 (19–28) | 24 (21–25) | 22 (19–23) |
| top-3 | 47 spec | 27 (26–29) | 36 (32–39) | 30 (29–31) | 27 (26–28) |
| top-8 | 47 spec | 37 (35–37) | 44 (42–46) | 39 (38–42) | 36 (35–40) |
| M1 | 43 API | 15 | 17 | 16 | 14 |
| M1any | 43 API | 21 | 20 | 19 | 16 |
| M2 | 154 API | 17 | 18 | 22 | 22 |
| M5 | 8652 op | 4 | 4 | 4 | 0 |

## 4. Kiểm định, lần lặp 1

McNemar chính xác hai phía; KTC 95% bootstrap theo nhà cung cấp cho hiệu (arm sau − arm trước).

| So | top1 | top3 | top8 | M1 | M2 | M5 |
|---|---|---|---|---|---|---|
| A-new − A-cur | 0,189; -0,043 … +0,319 | 0,049; +0,021 … +0,340 | 0,039; +0,043 … +0,255 | 0,625; -0,023 … +0,140 | 1,000; -0,026 … +0,039 | 1,000; 0,000 … 0,000 |
| A-newV1 − A-new | 0,625; -0,128 … +0,043 | 0,070; -0,234 … -0,021 | 0,062; -0,191 … -0,021 | 1,000; -0,070 … 0,000 | 0,289; -0,013 … +0,058 | 1,000; 0,000 … 0,000 |
| A-newV1-0 − A-newV1 | 0,625; -0,128 … +0,043 | 0,250; -0,149 … 0,000 | 0,250; -0,149 … 0,000 | 0,625; -0,140 … +0,047 | 1,000; 0,000 … 0,000 | 0,125; -0,001 … 0,000 |
| A-newV1-0 − A-cur | 0,678; -0,128 … +0,255 | 1,000; -0,191 … +0,191 | 1,000; -0,149 … +0,085 | 1,000; -0,140 … +0,093 | 0,180; -0,006 … +0,071 | 0,125; -0,001 … 0,000 |

## 5. Lần lặp 2–4

- Lần 2: A-cur top-1 19, top-3 27, top-8 37, M1 15, M2 17; A-new top-1 26, top-3 38, top-8 40, M1 16, M2 18; A-newV1 top-1 23, top-3 32, top-8 38, M1 15, M2 20; A-newV1-0 top-1 21, top-3 29, top-8 36, M1 14, M2 20.
- Lần 3: A-cur top-1 19, top-3 27, top-8 37, M1 15, M2 17; A-new top-1 27, top-3 36, top-8 42, M1 17, M2 18; A-newV1 top-1 23, top-3 29, top-8 36, M1 18, M2 23; A-newV1-0 top-1 21, top-3 26, top-8 34, M1 17, M2 23.
- Lần 4: A-cur top-1 19, top-3 27, top-8 37, M1 15, M2 17; A-new top-1 25, top-3 36, top-8 43, M1 17, M2 17; A-newV1 top-1 25, top-3 32, top-8 41, M1 17, M2 21; A-newV1-0 top-1 23, top-3 29, top-8 38, M1 15, M2 21.

## 6. Nhóm B = RF (báo thêm)

| Chỉ số | Đơn vị | A-cur | A-new | A-newV1 | A-newV1-0 |
|---|---|---|---|---|---|
| M1 | 43 | 13 | 15 | 15 | 15 |
| M1any | 43 | 19 | 19 | 18 | 17 |
| M2 | 154 | 17 | 18 | 19 | 19 |
| M5 | 8652 | 4 | 4 | 4 | 0 |

## 7. Target (lexicon rút trên toàn bộ dữ liệu)

Mỗi ô: hạng theo thứ tự spec (khoảng khi hoà) / số op ghi; điểm; vị trí trong danh sách transition khả dụng (lọc nhóm B
viết tay, 8 đầu), `—` nếu không có.

| Target | A-cur | A-new | A-newV1 | A-newV1-0 |
|---|---|---|---|---|
| reports-api | 1/6; 0,2727; 1 | 1/6; 0,1706; 1 | 1/6; 0,1548; 1 | 1/6; 0,1548; 1 |
| vampi-seeded | 1/8; 0,2727; 1 | 3 (1–3)/8; 0,1706; 1 | 3 (1–3)/8; 0,1548; 1 | 3 (1–3)/8; 0,1548; 1 |
| pyLoad | 1/62; 0,5455; 1 | 6 (3–10)/62; 0,1517; 3 | 3/62; 0,1376; 2 | 3/62; 0,1376; 2 |
| Airflow | 2 (1–2)/68; 0,3000; 1 | 1/68; 0,1706; 1 | 1/68; 0,1548; 1 | 1/68; 0,1548; 1 |
| artifact-keeper | 1/216; 0,6000; 1 | 1/216; 0,6000; 1 | 1/216; 0,6000; 1 | 17/216; 0,1548; — |
| bamf | 3 (2–3)/50; 0,3000; 3 | 1/50; 0,1627; 1 | 1/50; 0,1548; 1 | 1/50; 0,1548; 1 |

Số target có transition trong danh sách khả dụng: A-cur 6/6, A-new 6/6, A-newV1 6/6, A-newV1-0 5/6.

## 8. Lexicon mới

- A-new (`lexicon-new.csv`): 130 từ path. Mười từ đầu (`df_R`/`df_N`/nhà cung cấp, điểm): `collaborator` 13/2/4 0,6588; `collaborators` 13/2/4 0,6588; `memberships` 14/11/6 0,4762; `admins` 6/3/2 0,4242; `teammember` 3/0/1 0,4000; `teammembers` 3/0/1 0,4000; `owners` 6/1/1 0,3889; `membership` 17/23/7 0,3750; `moderators` 2/0/1 0,3750; `outside` 2/0/1 0,3750.
  `admin`: 22/197/8, 0,0925.
- A-newV1 (`lexicon-newV1.csv`): 386 từ path. Mười từ đầu (`df_R`/`df_N`/nhà cung cấp, điểm): `collaborator` 14/2/4 0,6667; `collaborators` 13/2/4 0,6588; `moderator` 3/0/2 0,5333; `memberships` 14/11/6 0,4762; `teammember` 4/1/2 0,4762; `joined` 5/2/2 0,4444; `functional` 4/0/1 0,4167; `subjects` 4/0/1 0,4167; `teammembers` 3/0/1 0,4000; `approver` 2/0/1 0,3750.
  `admin`: 37/249/14, 0,1231.
- Danh sách param mới: 57 từ; đầu bảng `principal` 0,3750; `requester` 0,3750; `collaborator` 0,3704; `founder` 0,3333; `root` 0,3333.
- Lexicon trong jar: 53 từ path, 45 từ param.

## 9. Giới hạn

- Nhãn `T` lệch định nghĩa với nhãn `R` cũ (cấp quyền thuần, khoá tài khoản); A-cur học `R` cũ nhưng được chấm theo `T`.
- 15 spec nửa test cũ đã được nhìn khi chỉnh luật lexicon cũ; chúng nằm trong tập test.
- Thứ tự spec của vòng 4 là thứ tự path rồi method (`extract_fields.ops_of`), có thể khác thứ tự EvoMaster đọc spec;
  khoảng xấu nhất–tốt nhất ở §3 cho thấy biên độ.
- Vòng 4 không trích tham số header; `param_names` mới hẹp hơn cũ.
- Mô phỏng chưa đối chiếu với lượt EvoMaster thật.
