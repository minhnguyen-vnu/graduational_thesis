# Rút bộ từ vựng lần 2 — 2026-09-21, train đã mở rộng

> Bị thay bởi `../lexicon-20260921-audited/RESULTS.md`: nhãn phần mở rộng đã soát lại,
> nửa `param` sửa cách tách từ, thước đo hạng viết lại thành khoảng. Bộ từ vựng đóng vào jar là bộ đã soát.

Luật: `../rules-draft.md` §11 và §12, không sửa gì sau khi mở rộng corpus.
Dữ liệu thêm: `../../corpus/sampling-plan.md` §1e (15 spec mới), §1f (sửa envelope), §1g (nhãn chốt phần mở rộng).
Chạy: `python3 derive2.py`.

## 1. Corpus sau khi mở rộng

| | Spec | Dòng | `R` | `N` | Nhà cung cấp | Nhà cung cấp có `R` |
|---|---|---|---|---|---|---|
| train | 29 | 478 | 39 | 439 | 29 | **11** |
| test | 15 | 270 | 15 | 255 | 15 | 6 |

Nửa train trước đó: 26 `R` trên 5 nhà cung cấp. Tỉ lệ nền train `0.0816`, ngưỡng P2 `0.1632`.

Hai lượt máy trên 266 dòng mới: đồng thuận thô `0.959`, `pe 0.840`, **kappa `0.742`**.
Giữ 253 dòng hai máy cùng nhãn, loại 13 dòng lệch hoặc có `U` theo §1g. Không ai phân xử.

Nửa test đổi vì `S131` được trích lại và gán lại: `S131-0097` từ `U` thành `N`, `S131-0100` từ `U`
thành `R`, `S131-0082` bị loại vì hai máy cùng gán `U`. Đây đúng hai dòng từng được ghi là hạn chế
"hai lượt máy dùng kiến thức ngoài spec"; sửa trích xuất đã gỡ chúng.

## 2. Kết quả trên nửa test

Tất cả đo trên cùng bộ nhãn test mới, nên ba dòng dưới so được với nhau.

| Bộ từ vựng | Nhãn test | top-1 | top-3 | top-8 |
|---|---|---|---|---|
| cũ, train 26 `R` / 5 nhà cung cấp | cũ | 0.167 | 0.500 | 0.833 |
| cũ, train 26 `R` / 5 nhà cung cấp | mới | 0.333 | 0.667 | 0.833 |
| mới, train 39 `R` / 11 nhà cung cấp | mới | **0.667** | **1.000** | **1.000** |

Cải thiện `0.167 → 0.667` chia gần đôi: sửa trích xuất envelope đưa `0.167` lên `0.333`,
mở rộng nửa train đưa `0.333` lên `0.667`.

Luật tính điểm không sửa một chữ nào giữa hai lần. Chỉ dữ liệu train đổi.

## 3. Hạng của endpoint `R` đầu tiên, từng spec test

| Spec | Hạng | Đứng đầu bảng |
|---|---|---|
| S107 | 1/25 | `POST /scores/{score}/collaborators` — đúng |
| S108 | 1/36 | `DELETE /repos/{owner}/{repo}/collaborators/{collaborator}` — đúng |
| S131 | 1/24 | `PATCH /v1/users/{id}` — đúng |
| S136 | 1/34 | `POST /apps/{appId}/access/{userId}` — đúng |
| S123 | 2/30 | `POST /Destiny2/SearchDestinyPlayerByBungieName/...` |
| S116 | 3/21 | `POST /assetservers/{webId}/securitymappings` |

S107 và S108 là hai spec lần trước không từ nào bắt được. Từ cứu chúng là `collaborators`,
điểm `0.375`, học từ 2 dòng `R` của `github.com` ở nửa train, áp sang `flat.io` và `gitea.io` ở nửa test.
Đây là chỗ duy nhất trong cả hai lần đo có một từ học ở nhà cung cấp này dùng được ở nhà cung cấp khác.

## 4. Bộ lọc nhị phân vẫn kém

| Bộ | Nửa | TP | FN | FP | Precision | Recall |
|---|---|---|---|---|---|---|
| 4 từ sau P1+P2+P3 (`client members permission user`) | train | 29 | 10 | 58 | 0.333 | 0.744 |
| 4 từ sau P1+P2+P3 | test | 8 | 7 | 39 | 0.170 | 0.533 |

Thêm dữ liệu không cứu được cách lọc nhị phân. Chênh lệch giữa `recall 0.533` của bộ lọc và
`top-3 1.000` của xếp hạng là toàn bộ lý do đổi sang xếp hạng.

## 5. Ba điều chưa chứng minh

- Nửa test đã bị dùng để phát triển từ 09-20 (`rules-draft.md` §12.5). Luật tính điểm được đóng băng
  từ trước khi mở rộng corpus, nên con số mục 2 sạch hơn con số ngày 09-20, nhưng vẫn không phải
  ước lượng trên dữ liệu chưa ai nhìn.
- 253 dòng mới mang nhãn hai máy đồng thuận, không ai soát. Không có lượt người nào trên phần mở rộng.
- Chưa lần chạy EvoMaster nào. Patch xếp hạng chưa áp, chưa build, chưa qua cổng hồi quy.

## 6. Ba target của luận văn, xếp hạng trên toàn bộ endpoint

Khác mục 3: ở đây không lấy mẫu, danh sách endpoint của cả ba target là đầy đủ.

| Target | Ứng viên | Hạng của transition thật | Đứng ngay sau |
|---|---|---|---|
| Tier-1 `reports-api` | 2 | **1** (`PUT /users/{username}/role`, điểm 0.273) | `DELETE /reports/{id}` 0.126 |
| Tier-2 `vampi-seeded` | 6 | **1** (`PUT /users/v1/{username}/role`, điểm 0.273) | `PUT /users/v1/{username}/email` 0.222 |
| Tier-2b pyLoad | 2 | **1** (`POST /api/set_user_permission`, điểm 0.545) | `POST /json/update_users` 0.214 |

Lo ngại ghi ở `lexicon-20260920/RESULTS.md` §9 — bộ từ mới kéo 6 endpoint `PUT` của vampi vào diện
ứng viên trong khi `firstOrNull` chỉ lấy một — được xếp hạng gỡ trên giấy: `role` ăn điểm cao hơn
`email` và `password`. Chưa lần chạy EvoMaster nào xác nhận.

## 7. Sửa mục 2 và 3: hạng đo trên mẫu là lạc quan

Mục 2 và 3 xếp hạng trên các dòng đã giữ của mỗi spec, tối đa 36. Lúc chạy thật EvoMaster xếp trên
mọi endpoint ghi của spec: S108 có 159, S116 có 161, S210 có 451.

| Nửa test | top-1 | top-3 | top-8 |
|---|---|---|---|
| xếp trên các dòng đã giữ | 0.667 | 1.000 | 1.000 |
| xếp trên toàn bộ endpoint ghi | 0.167 | 0.667 | 0.833 |

| Spec | Hạng trên mẫu | Hạng trên toàn bộ |
|---|---|---|
| S107 | 1/25 | 1/47 |
| S108 | 1/36 | 2/159 |
| S123 | 2/30 | 2/46 |
| S131 | 1/24 | 2/103 |
| S136 | 1/34 | 5/161 |
| S116 | 3/21 | 16/161 |

Hàng dưới là cận dưới, không phải số thật: nó coi mọi endpoint chưa gán xếp trên là `N`.
S116 là ví dụ rõ nhất — 15 endpoint đứng trên nó chưa ai gán, mà S116 chính là spec chứa
`securityentries`, loại endpoint corpus đã ghi là `R` ở ba dòng khác.

Sự thật nằm giữa hai hàng. `sampling-plan.md` §1h khai luật gán bù 41 dòng để đóng khoảng này:
mọi endpoint xếp trên endpoint `R` điểm cao nhất của từng spec. 41 dòng đó chỉ dùng để đo hạng,
không vào phần rút từ vựng.

Số liệu: `rank-full.txt`.

## 8. Hạng chính xác sau khi gán bù

41 dòng gán bù theo `sampling-plan.md` §1h, hai lượt máy mù: đồng thuận thô `0.854`, `pe 0.465`,
kappa `0.727`. Giữ 34 dòng (13 `R`, 21 `N`), loại 7 dòng lệch. 13 trong 41 endpoint xếp trên
là `R` thật — đúng nghi ngờ ở mục 7.

| Nửa test, xếp trên mọi endpoint ghi | top-1 | top-3 | top-8 |
|---|---|---|---|
| cận trên: chỉ xếp trong các dòng đã giữ | 0.667 | 1.000 | 1.000 |
| cận dưới: coi mọi dòng chưa gán là `N` | 0.167 | 0.667 | 0.833 |
| **chính xác** | **0.500** | **0.833** | **1.000** |

| Spec | Hạng | Trên tổng |
|---|---|---|
| S107 | 1 | 47 |
| S108 | 1 | 159 |
| S116 | 1 | 161 |
| S123 | 2 | 46 |
| S131 | 2 | 103 |
| S136 | 5 | 161 |

Ba con số này sai. Chúng giả định một luật phá hoà chưa khai: nhiều endpoint cùng điểm, cùng verb,
cùng trạng thái tham số người dùng, nên hạng của endpoint `R` trong nhóm bằng điểm không xác định.
Thước đo đã viết lại thành khoảng cộng một giá trị theo thứ tự spec ở `../lexicon-20260921-audited/RESULTS.md` §5.
Bộ từ vựng của thư mục này cũng bị thay: nửa `param` tách từ sai thứ tự (§2 của tài liệu đó).

S116 từ hạng 16 lên hạng 1: 13 endpoint `securityentries`/`securitymappings` xếp trên nó đều là `R`.

Nửa train: top-1 `0.455`, top-3 `0.727`, top-8 `1.000`. Ba spec còn dòng chưa rõ xếp trên
(S112 một dòng, S201 một dòng, S214 năm dòng) vì chúng nằm trong 7 dòng hai máy lệch.

**Hệ quả cho patch.** `top-8 = 1.000` và `top-3 = 0.833`: mọi spec test đều có endpoint `R` trong
8 ứng viên đầu, không phải trong 3. `MAX_TRANSITION_CANDIDATES = 8` của
`lexicon-rank-20260921.patch` là con số đo được, không phải con số dư.

Số liệu: `rank-exact.txt`.
