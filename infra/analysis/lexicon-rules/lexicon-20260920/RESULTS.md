# Rút bộ từ vựng lần 1 — 2026-09-20

Luật: `../rules-draft.md` §11, viết lúc 23:31 trước khi `derive_lexicon.py` tồn tại.
Chạy: `python3 derive_lexicon.py`, `python3 eval_lexicon.py train`, `python3 eval_lexicon.py test`.

## 1. Bộ rút ra từ nửa train

| Danh sách | Trường | Ứng viên | Qua P1 và P2 | P3 bỏ | Còn | Từ |
|---|---|---|---|---|---|---|
| 1 `transitionPathSignals` | `path` | 32 | 5 | 1 | 4 | `client` `members` `permissions` `user` |
| 2 `transitionUserParamSignals` | `param_names` | 36 | 4 | 0 | 4 | `client` `email` `organization` `user` |
| 3 `roleFieldSignals` | `body_field_names` | 84 | 10 | 0 | 10 | `access` `client` `default` `grant` `logo` `permissions` `redirect` `role` `scopes` `uris` |

Ngưỡng P2 = `2 × 26/241` = `0.2158`. P3 bỏ `users` vì `user` là chuỗi con.

## 2. Đo trên nửa test

Chỉ danh sách 1 được đo: chỉ nó quyết định một endpoint có được chọn làm transition hay không.

| Bộ | Nửa | TP | FN | FP | TN | Precision | Recall |
|---|---|---|---|---|---|---|---|
| rút ra, 4 từ | train | 24 | 2 | 38 | 177 | 0.387 | 0.923 |
| rút ra, 4 từ | test | 7 | 7 | 38 | 217 | 0.156 | 0.500 |
| 56 từ, phần path, 8 từ | train | 19 | 7 | 38 | 177 | 0.333 | 0.731 |
| 56 từ, phần path, 8 từ | test | 7 | 7 | 42 | 213 | 0.143 | 0.500 |

Recall tụt từ 0.923 xuống 0.500 khi đổi từ nửa train sang nửa test.
Trên nửa test hai bộ bắt đúng bằng nhau; bộ rút ra dùng 4 từ thay vì 8 và báo sai ít hơn 4 dòng.

## 3. Bảy dòng `R` bộ mới bỏ sót

| row_id | Endpoint | Từ đáng lẽ phải có |
|---|---|---|
| S116-0049 | `DELETE /attributecategories/{webId}/securityentries/{name}` | `securityentries` |
| S116-0107 | `POST /eventframes/{webId}/securityentries` | `securityentries` |
| S116-0153 | `DELETE /tables/{webId}/securityentries/{name}` | `securityentries` |
| S107-0035 | `POST /scores/{score}/collaborators` | `collaborators` |
| S108-0043 | `DELETE /repos/{owner}/{repo}/collaborators/{collaborator}` | `collaborators` |
| S108-0124 | `DELETE /repos/{owner}/{repo}/teams/{team}` | `teams` |
| S107-0025 | `POST /organizations/invitations` | `invitations` |

`securityentries`, `collaborators`, `teams` không xuất hiện trong một dòng `R` nào của nửa train.
Không luật chọn từ nào rút được chúng ra từ nửa train.

`invitations` có trong nửa train và qua P2, nhưng chỉ ở một nhà cung cấp nên P1 loại.

## 4. Từ qua P2 mà P1 loại

`access` `approve` `block` `clients` `composites` `email` `invitations` `invite` `management`
`mappings` `organizationid` `organizations` `permissiongroupid` `realm` `requests` `role` `roles`
`scope` `scopes` `userid`

`role` có precision 0.625 trên nửa train (5 dòng `R`, 3 dòng `N`) và chỉ ở Keycloak.

## 5. Sai thứ tự đã xảy ra

Kế hoạch là sửa extractor cho S131 rồi mới mở nửa test. Phần đo ở mục 2 chạy trước khi sửa.
17 dòng của S131 có `body_field_names` đúng một chữ `data`; nhãn hiện tại của chúng là 14 `N`, 2 `U`, 1 `R`.
Chúng nằm trong mẫu số của bảng mục 2. Con số ở mục 2 là tạm cho tới khi S131 được trích lại và gán lại.
Nửa test coi như đã mở: từ đây không được chỉnh luật chọn từ theo kết quả trong bảng này.

## 6. Hai hạn chế của mục 1

Danh sách 3 lẫn trường của biểu diễn đầy đủ: `logo`, `redirect`, `uris`, `default` là trường thân của
`PUT /clients/{id}` kiểu Keycloak, nơi thân chứa hơn 100 trường. Chúng qua P2 vì thân lớn như vậy hiếm,
không vì chúng liên quan đến quyền.

Sinh ứng viên lấy đúng dạng mặt chữ trong spec, nên được `members` và `permissions` chứ không được
`member` và `permission`. Dưới phép so chuỗi con, dạng số ít bắt rộng hơn dạng số nhiều.

## 7. Sửa lỗi sinh ứng viên — 2026-09-20 23:5x

Bản chạy đầu sinh ứng viên từ `path + " " + verb + ":" + path`, nên các token `post`, `delete`, `patch`
lọt vào tập ứng viên. Số ứng viên của danh sách 1 là 35 thay vì 32. Cả ba từ đó trượt P2, nên bốn từ
được giữ và mọi con số ở mục 2 không đổi. `derive_lexicon.py` nay sinh ứng viên từ trường thô và
chỉ dùng chuỗi runtime khi đếm.

## 8. Chẩn đoán: bỏ hẳn bộ lọc

Lấy cả 32 ứng viên, không áp P1 P2 P3:

| Bộ | Nửa | TP | FN | FP | Precision | Recall |
|---|---|---|---|---|---|---|
| 4 từ, có lọc | train | 24 | 2 | 38 | 0.387 | 0.923 |
| 32 từ, không lọc | train | 26 | 0 | 112 | 0.188 | 1.000 |
| 4 từ, có lọc | test | 7 | 7 | 38 | 0.156 | 0.500 |
| 32 từ, không lọc | test | 12 | 2 | 111 | 0.098 | 0.857 |

Hai dòng còn sót ở nửa test là `POST /scores/{score}/collaborators` và
`POST /eventframes/{webId}/securityentries`.

Đây là chẩn đoán chạy sau khi đã thấy kết quả mục 2, không phải số sạch. Nó không được dùng để
chọn lại luật ở §11.

## 9. Ba target của luận văn

Chạy phép so của cổng chặn trên endpoint transition đã biết của từng target:

| Target | Transition | 4 từ mới | 8 từ cũ | Endpoint khác cùng nổ, 4 từ |
|---|---|---|---|---|
| Tier-1 `reports-api` | `PUT /users/{username}/role` | trúng `user` | trúng `role` | 0 |
| Tier-2 `vampi-seeded` | `PUT /users/v1/{username}/role` | trúng `user` | trúng `role` | 5 |
| Tier-2b pyLoad | `POST /api/set_user_permission` | trúng `user` | trúng `permission` | 1 |

Cả ba vẫn trúng. Trên vampi số ứng viên transition tăng từ 1 lên 6, trong khi
`MAX_STATEFUL_TRIPLE_ATTEMPTS` là 8. Chưa có lần chạy nào đo ảnh hưởng của việc đó.

Trên pyLoad, endpoint thứ hai mà `user` kéo vào là `POST /json/update_users`, đúng transition thật của
CVE mà bộ 8 từ không trúng (`docs/tier2b-pyload-target.md`).

## 10. Xếp hạng thay cho lọc — 2026-09-21

Luật: `../rules-draft.md` §12, viết lúc 00:02 trước khi `rank_lexicon.py` tồn tại.
Thước đo: trong mỗi spec, sắp endpoint ghi theo điểm giảm dần; `top-k` là tỉ lệ spec có endpoint `R`
nằm trong `k` endpoint đầu. Mẫu số chỉ gồm spec có ít nhất một endpoint `R`.

| Cách chọn transition | Nửa | Spec có `R` | top-1 | top-3 | top-8 |
|---|---|---|---|---|---|
| hôm nay: 8 từ path + 9 từ param, `firstOrNull` theo thứ tự verb | train | 5 | 0.600 | — | — |
| hôm nay | test | 6 | **0.000** | — | — |
| A: xếp hạng bằng điểm, 32 từ | train | 5 | 0.800 | 1.000 | 1.000 |
| A | test | 6 | 0.167 | 0.500 | 0.833 |
| B: như A, thêm điều kiện tham số | train | 5 | 0.800 | 1.000 | 1.000 |
| B | test | 2 | 0.500 | 1.000 | 1.000 |
| C: như A, tham số làm trọng tài khi bằng điểm | train | 5 | 0.800 | 1.000 | 1.000 |
| C | test | 6 | 0.167 | 0.500 | 0.833 |

Hệ thống hôm nay trên nửa test: chọn sai ở S108, S123, S136; không chọn được endpoint nào ở S107, S116, S131.
Con số `0.000` này là số sạch: bộ 8 từ và bộ 9 từ chưa bao giờ được chỉnh theo corpus này.
Con số của A và B không sạch, theo §12.5.

Biến thể C là cách patch nháp `lexicon-rank-20260921.patch` xếp hạng. C trùng A ở mọi ô:
điều kiện tham số dùng làm trọng tài không đổi kết quả ở `k = 1, 3, 8`.

Biến thể B loại luôn endpoint `R` ở 4 trong 6 spec test, nên mẫu số tụt từ 6 xuống 2.
Điều kiện tham số của runtime (`RestSecurityBuilder.kt:817`) là chỗ mất nhiều nhất.

Khoảng cách giữa `top-1 0.167` và `top-8 0.833` lớn hơn khoảng cách do bộ từ vựng tạo ra.
Việc builder chỉ thử đúng một endpoint đáng giá hơn việc đổi danh sách từ.

Xếp hạng chạy trên các dòng đã lấy mẫu của mỗi spec, không trên toàn bộ endpoint của spec thật.
Bảng `sampling-plan.md` §2 ghi cột `op giữ` là 15, nhưng các file `S*.csv` giữ tới 36 dòng một spec
(tổng 519 dòng trên 29 spec). Cần đối chiếu lại cột đó.
