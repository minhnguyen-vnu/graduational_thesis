# Bộ từ vựng chọn transition — nháp 2026-09-26

Chương này tả bộ từ vựng của jar `L` tới `AF2`. Từ jar `P2e` (2026-10-14), builder không đọc bộ từ vựng nữa: một
mô hình Naive Bayes thay cả bộ từ vựng lẫn các danh sách viết tay (`docs/naive-bayes.md`). Chương giữ lại làm lịch sử
và làm phép so.

Bộ từ vựng của jar `L` tới `AF2` rút từ 36 endpoint `R` của 10 nhà cung cấp, gán nhãn theo luật khai trước.
Trên nửa test (6 spec có endpoint `R`), endpoint `R` đứng hạng 1 ở 4 spec, trong 3 hạng đầu ở 5 spec, trong 8
hạng đầu ở cả 6 spec. Trên ba target của luận văn, thay bộ từ cứng bằng bộ này không mất phát hiện 970 nào
(0 trên 30 dòng ghép cặp). Nửa test đã được dùng trong lúc phát triển, nên các con số hạng là số báo cáo,
chưa phải ước lượng trên dữ liệu chưa ai nhìn (§7).

## 1. Bộ từ vựng quyết định gì

`RestSecurityBuilder` của jar `L` tới `AF2` dùng từ vựng ở bốn chỗ: chọn endpoint transition, chọn tham số chỉ nạn nhân, chọn trường
mang quyền, chọn giá trị quyền thấp. Chương này chỉ đo chỗ thứ nhất, vì chỉ chỗ đó quyết định builder có dựng
được bộ ba hay không.

Trước bộ từ vựng, builder lọc endpoint ghi bằng 8 từ path cứng trên chuỗi `path + " " + "VERB:path"` và 9 từ param cứng (cả hai
thuộc bộ 56 từ viết tay), rồi lấy
`firstOrNull` theo thứ tự verb (`RestSecurityBuilder.kt:809`, bản trước patch). Trên nửa test, endpoint được
chọn là endpoint `R` ở 0 trong 6 spec (`infra/analysis/lexicon-rules/lexicon-20260920/RESULTS.md` §10). Tám từ
đó chưa từng được chỉnh trên corpus này, nên `0/6` là số sạch. Bộ 8 từ do ta tự đặt và chỉ dùng làm phép kiểm
tra lúc phát triển.

## 2. Luật gán nhãn

Nguồn đầy đủ: `infra/analysis/lexicon-rules/rules-draft.md`, phiếu `labelling-form.md`, lịch sử sửa
`rules-changelog.md`.

Một dòng là một operation (method, path). Người gán chỉ được nhìn method, path, `summary`, `description`, tên
tham số, tên trường thân yêu cầu và `enum` của chúng (§2, §7). Ba nhãn: `R` (ghi có thể làm giảm quyền của một
chủ thể), `N`, `U` (chữ trong spec không đủ để chọn).

Năm quy tắc `R` lấy từ hai nguồn đã đọc bản gốc (`sources.md`): BSR INCITS 359 Draft 4/4/2003 §6.1 và SCIM
RFC 7643 §4.1.

| Mã | Trường hợp | Nguồn | Ví dụ |
|---|---|---|---|
| `R2` | xoá role, thu hồi permission | `DeleteRole`, `RevokePermission` | `DELETE /roles/{id}` |
| `R3` | gỡ chủ thể khỏi một role | `DeassignUser` | `DELETE /users/{id}/roles/{role}` |
| `R4` | đặt được trạng thái hoạt động của chủ thể | SCIM `active` | `PATCH /users/{id}` có trường `enabled` |
| `R5` | client đặt giá trị role hoặc permission | SCIM `roles`, `entitlements` | `PUT /users/{username}/role` với `role ∈ [ADMIN, VIEWER]` |
| `R6` | bỏ một role khỏi phiên đang chạy | `DropActiveRole` | "drop active role" |

Ba target của luận văn đều hạ quyền theo kiểu `R5` (`rules-draft.md` §10).

Sáu điểm chốt ngày 2026-09-17, trước khi gán dòng nào (`rules-draft.md` §8):

| Trường hợp | Nhãn | Lý do |
|---|---|---|
| xoá một user | `N8` | Lần chạy không reset dùng bộ tài khoản cố định; xoá trúng một tài khoản làm hỏng phần còn lại của lần chạy. |
| đặt `active: false` | `R4` | Nhóm lớn nhất trong khảo sát CVE, 29 trên 85; báo cáo tách riêng theo mã. |
| rời group hoặc team | `N9` | Chữ "group" trong API thật phần lớn không mang quyền. |
| gỡ chủ thể khỏi role | `R3` | `DeassignUser` là lệnh gần quan hệ A1 nhất. |
| endpoint vừa nâng vừa hạ role | `R5` | Cả ba target hạ quyền theo kiểu này. |
| được nhìn `enum` | có | Thiếu `enum` thì `status` và `role` rơi hết vào `U`. |

Phiếu sửa một lần giữa hai vòng (v2, 2026-09-19): bước G2 cũ chặn cả ví dụ của chính phiếu. Vòng 2 gán lại
toàn bộ 519 dòng bằng phiếu v2 (`rules-changelog.md`).

## 3. Mẫu

Nguồn `openapi-directory` qua `api.apis.guru/v2/list.json`, 2.529 API (`infra/analysis/corpus/sampling-plan.md` §1).

| Bước | Luật | Kết quả |
|---|---|---|
| Bốc spec | một API một nhà cung cấp; 20 spec nhóm giàu (134 nhà cung cấp có nhãn `security`, `collaboration`, `developer_tools`, `enterprise`) + 10 spec nhóm ngẫu nhiên (542 nhà cung cấp); hạt giống `20260918`; ba target của ta bị loại | 30 spec |
| Spec rỗng | thay một vòng, hạt giống `20260919` | 29 spec có operation ghi |
| Chia | theo nhà cung cấp, 50/50 | train 14 spec, test 15 spec |
| Cắt | 15 operation ghi một spec | 318 dòng |
| Làm giàu | thêm tối đa 15 dòng qua cổng từ khoá và 6 dòng giáp ranh một spec, hạt giống `20260919 + spec` | 519 dòng |
| Mở rộng train | 15 nhà cung cấp mới từ nhóm giàu, hạt giống `20260921`, trần 36 operation, chỉ vào train | 249 dòng, S200–S214 |
| Gán bù để đo hạng | mọi endpoint ghi xếp trên endpoint `R` điểm cao nhất của spec | 41 dòng, chỉ dùng đo hạng |

Cổng từ khoá của bước làm giàu chỉ để tiêu ngân sách gán nhãn vào chỗ có dòng dương. Nó bỏ sót 7 trong 14 dòng
`R` mà lượt L1 vòng 1 gán trên mẫu ngẫu nhiên (§1c). Vì hai tầng có xác suất lấy mẫu khác nhau, tỉ lệ `R` của
corpus không phải tỉ lệ `R` của API thật.

## 4. Nhãn và độ tin cậy

Ba lượt trên 519 dòng của `labelling-r2` (`rules-draft.md` §9):

| Lượt | Ai | Gán gì |
|---|---|---|
| L1 | một LLM, mù | toàn bộ |
| L2 | một LLM khác model, mù, không thấy L1 | toàn bộ |
| H | người | 44 dòng L1 khác L2 hoặc có `U`; toàn bộ 37 dòng cùng `R`; 40 trên 438 dòng cùng `N`, bốc bằng hạt giống `20260918` trước khi người nhìn dòng nào |

Số liệu: `infra/analysis/lexicon-rules/labelling-r2/kappa-output-20260926.txt` (chạy lại `kappa_r2.py`).

| Đại lượng | Giá trị |
|---|---|
| L1–L2, 519 dòng | thô 0,931; `pe` 0,773; kappa 0,694 |
| Người–LLM trên tầng đồng thuận, nhãn độc lập của người, có trọng số | thô 0,889; `pe` 0,824; kappa 0,369 |
| Người khác LLM, tầng cùng `R` | 20 trên 37 |
| Người khác LLM, tầng cùng `N` | 3 trên 40 |
| Tỉ lệ sai ước lượng của tầng đồng thuận | 0,111; Wilson 95% của tầng `N` quy về cả tầng: [0,024; 0,183] |
| Tầng lệch, 44 dòng | nhãn người theo L1 24, theo L2 11, khác cả hai 9 |

Kappa có trọng số: mỗi dòng tầng `R` trọng số 1, mỗi dòng tầng `N` trọng số 438/40 (`sampling-plan.md` §1d).

Kappa L1–L2 đo sự nhất quán của một nhà cung cấp model. Hai lượt cùng nhà cung cấp có thể sai giống nhau mà
kappa vẫn cao. Chỗ neo vào dữ liệu không do model sinh là lượt người: 0,369, với 20 trên 37 dòng hai máy cùng gọi
`R` bị người gọi khác.

Nhãn chốt `labelling-r2/final.csv`: 40 `R`, 470 `N`, 9 `U`; 398 dòng `audited=0` mang nhãn hai máy đồng thuận
mà không ai soát.

**Sai lệch giao thức.** Giao thức ghi người phân xử. Theo yêu cầu của người gán, mô hình phân xử 32 dòng và chuẩn
hoá 14 mã luật (`labelling-r2/adjudication.csv`, `model-revisions.csv`, `rules-changelog.md` 2026-09-20). Cột
`label` giữ nhãn độc lập của người; kappa 0,369 tính trên cột đó. Bộ từ vựng rút từ `final_label`, tức từ nhãn
đã có mô hình tham gia.

**Phần mở rộng train.** 266 dòng (249 dòng S200–S214 và 17 dòng S131 trích lại sau khi sửa envelope JSON:API)
chỉ có hai lượt máy mù: thô 0,959, `pe` 0,840, kappa 0,742. 253 dòng giữ nhãn đồng thuận với `audited=0`, 13 dòng
lệch hoặc có `U` bị loại, không ai phân xử (`sampling-plan.md` §1g).

**Lượt soát thứ ba.** Một lượt máy mù thứ ba gán lại 28 dòng `R` của phần mở rộng trộn với 28 dòng `N` bốc làm
nhiễu, hạt giống `20260921`: thô 0,964, kappa 0,927 trên 56 dòng; 3 dòng train đổi nhãn
(`lexicon-20260921-audited/RESULTS.md` §1). Lượt này chỉ xem dòng hai máy đã gọi `R`, nên không đo được dòng
`R` mà cả hai máy cùng bỏ sót.

## 5. Luật rút từ

Viết xong trước khi có script rút từ (`rules-draft.md` §11, 2026-09-20 23:31; §12, 2026-09-21 00:02).

Sinh ứng viên từ `path` của các dòng `R` nửa train: cắt theo ký tự không phải chữ-số, tách camelCase, hạ chữ
thường, bỏ token toàn số và token ngắn hơn 4 ký tự. Ví dụ: `/users/{username}/roleMappings` cho `users`,
`username`, `role`, `mappings`.

Điểm của một từ `w`, đếm bằng đúng phép so chuỗi con của runtime:

```
diem(w)        = (df_R + 1) / (df_R + df_N + 2)  ×  ncc / (ncc + 1)
diem(endpoint) = max diem(w) trên các từ w là chuỗi con của chuỗi so, 0 nếu không có
```

`ncc` là số nhà cung cấp có dòng `R` chứa `w`. Ví dụ: một từ trúng 2 dòng `R`, 0 dòng `N`, ở 1 nhà cung cấp
được `3/4 × 1/2 = 0,375`.

Hệ số nhà cung cấp có lý do cụ thể: ở lần rút đầu, ba từ điểm cao nhất (`realm`, `containerid`, `clientrole`)
chỉ có ở Keycloak (`rules-draft.md` §11.8).

Builder xếp mọi endpoint ghi theo `diem(endpoint)`; hoà điểm thì endpoint có tham số chỉ người dùng đứng trước,
rồi theo verb `PUT, PATCH, POST, DELETE`, rồi theo thứ tự trong spec.

Chuỗi so gồm path, verb và tên trường thân yêu cầu (`rules-draft.md` §13, biến thể V1, chọn bằng luật phá hoà
khai trước trên nửa train). Tên trường được thêm vì `PATCH /auth/fab/v1/users/{username}` của Airflow mang quyền
ở trường thân `roles`.

## 6. Ba lần rút

| Lần | Ngày | Nửa train | Đổi gì | Thư mục |
|---|---|---|---|---|
| 1 | 09-20 | 26 `R`, 5 nhà cung cấp có `R` | lọc nhị phân P1–P3, 4 từ path | `lexicon-20260920/` |
| 2 | 09-21 | 39 `R`, 11 nhà cung cấp | mở rộng train, xếp hạng | `lexicon-20260921/`, bị thay |
| 3 | 09-21 | 36 `R` / 441 `N`, 10 nhà cung cấp | soát nhãn lượt ba, sửa thứ tự tách từ nửa `param` | `lexicon-20260921-audited/`, trong jar `L` tới `AF2` |

Lần 1 đo bằng precision và recall của bộ lọc trên nửa test: precision 0,156, recall 0,500; recall trên nửa train
là 0,923 (`lexicon-20260920/RESULTS.md` §2). Sáu trong bảy dòng bị sót dùng từ không có trong dòng `R` nào của
nửa train: `securityentries` (3), `collaborators` (2), `teams` (1). Bốn con số này đo trước khi sửa lỗi trích
xuất S131, nên là số tạm.

Bỏ bộ lọc, giữ cả 32 ứng viên, thì recall nửa test lên 0,857 và precision xuống 0,098 (`lexicon-20260920/RESULTS.md`
§8, chẩn đoán chạy sau khi đã thấy §2). Builder chọn một endpoint, nên từ lần 2 thước đo là hạng của endpoint `R`
trong spec.

Lần 3 là bộ trong jar `L` tới `AF2`: `core/src/main/resources/stateful-authz-lexicon.csv`, 53 từ path và 45 từ param, mỗi từ
kèm điểm.

## 7. Hạng trên nửa test

Thước đo (`rules-draft.md` §12.4): trong mỗi spec, xếp mọi endpoint ghi; `top-k` là tỉ lệ spec có endpoint `R`
nằm trong `k` endpoint đầu, trên 6 spec test có endpoint `R`.

Nhiều endpoint cùng điểm, cùng verb, cùng trạng thái tham số. Hạng trong nhóm hoà đó do thứ tự spec quyết định.
Cột "khoảng" là cận tốt nhất–xấu nhất trên mọi cách phá hoà; cột "thứ tự spec" là giá trị runtime nhận, vì
`actionDefinitions` giữ thứ tự spec.

| Chuỗi so | top-1 thứ tự spec | top-1 khoảng | top-3 thứ tự spec | top-8 thứ tự spec |
|---|---|---|---|---|
| path + verb (jar `L`) | 0,500 | 0,333–0,667 | 0,667 | 1,000 |
| path + verb + tên trường thân (jar `RF` tới `AF2`) | 0,667 | 0,500–0,833 | 0,833 | 1,000 |

Nguồn: `lexicon-20260921-audited/rank-exact.txt`, `field-gate-20260923/rank-field.txt`.

Hạng từng spec, chuỗi so có tên trường:

| Spec | Hạng | Trên tổng endpoint ghi |
|---|---|---|
| S107 | 1 | 47 |
| S108 | 1 | 159 |
| S116 | 1 | 161 |
| S123 | 1–10, thứ tự spec 1 | 46 |
| S131 | 1–3, thứ tự spec 2 | 103 |
| S136 | 5 | 161 |

Soát nhãn lần 3 làm S108 tụt từ hạng 1 xuống hạng 6 dưới chuỗi so path + verb: dòng train
`PUT /orgs/{org}/outside_collaborators/{username}` chuyển `R` sang `N` theo luật `N9`, và điểm `collaborators`
giảm từ 0,375 xuống 0,250. Luật không sửa sau khi thấy giá đó (`lexicon-20260921-audited/RESULTS.md` §6).

## 8. Trên target chạy thật

| Target | Transition | Hạng |
|---|---|---|
| Tier-1 `reports-api` | `PUT /users/{username}/role` | 1 |
| Tier-2 `vampi-seeded` | `PUT /users/v1/{username}/role` | 1 |
| Tier-2b pyLoad | `POST /api/set_user_permission` | 1 |
| Airflow | `PATCH /auth/fab/v1/users/{username}` | 1–5 trên 68 endpoint ghi |

Nguồn: `field-gate-20260923/RESULTS.md` §2–§3, xếp từ spec tĩnh.

Chạy EvoMaster, seeds 1–10, cờ D1 tắt:

- Jar `L` (bộ từ lần 3, chuỗi so path + verb): 0 trên 30 dòng ghép cặp mất 970 so với jar trước bộ từ vựng
  (`em-results/lexicon-chain-20260921/`).
- Jar `RF` (thêm tên trường thân, thu giá trị quyền cục bộ): 0 trên 50 dòng đổi kết quả 970 so với jar `L`
  (`em-results/rolefield-chain-20260924/RESULTS.md`).

Airflow: jar `RF` chọn đúng `PATCH /auth/fab/v1/users/{username}` (`em-results/airflow-lexicon-20260923/RESULTS.md`).
Jar `TT` dựng được bộ ba hợp lệ đầu tiên trên Airflow, `204/200/204`, bị C4 loại vì bộ đệm vai trò 30 giây của
FAB (`em-results/transitiontrim-chain-20260927b/RESULTS.md`).

## 9. Hạn chế

- Nửa test được dùng để phát triển từ 09-20 (`rules-draft.md` §12.5). Luật §11–§13 viết trước khi chạy, nhưng
  con số §7 không phải ước lượng trên dữ liệu chưa ai nhìn. Ước lượng sạch cần spec gán nhãn sau ngày đóng băng.
- Nửa test có 6 spec có endpoint `R`. Một spec đổi hạng làm `top-1` đổi 0,167.
- 398 trên 519 dòng của `labelling-r2` và 253 dòng phần mở rộng mang nhãn hai máy đồng thuận, không ai soát.
- Mô hình phân xử 32 dòng thay người (§4).
- Chưa có phép đo nào cho dòng `R` mà cả hai lượt máy cùng bỏ sót.
- Chỉ danh sách từ path được đo trên held-out. Danh sách tham số (45 từ) và danh sách trường quyền (list-3, 23 từ)
  rút theo cùng luật nhưng corpus không có nhãn mức trường, nên không đo được.
- Tới `AF2`, builder không dùng list-3 để nhận diện trường; nó dùng ba danh sách viết tay (`RestSecurityBuilder.kt:104`
  cờ admin, `:414` tham số nạn nhân, `:417` trường quyền, số dòng ở `8d6cf8431f`). `P2e` thay chúng bằng bảng `role`
  và `victim` của mô hình (`docs/naive-bayes.md` §1). Ba danh sách này không rút được từ corpus hiện có: token
  cờ-admin (`is_admin`, `is_staff`…) vắng mặt (chỉ có `admin` ở 1 nhà cung cấp, rớt cổng provider≥2); list-3 quá
  chung nên dùng để chấm điểm làm tụt hạng (ablation V2, `field-gate-20260923/RESULTS.md` §4: test top-1 0,667→0,333);
  và không có nhãn mức trường để đo độ chính xác nhận diện. Chạy tay + truy nguồn:
  `infra/analysis/lexicon-rules/field-identification-hardcode-20261004.md`.
- Tới `AF2`, sáu danh sách giá trị quyền thấp/cao viết tay: corpus không có nhãn thứ tự giữa các giá trị quyền.
  `P2e` thay chúng bằng bảng `low`, `high`, `lowstr`, `highstr` (`docs/naive-bayes.md` §5).
- Hạng trên Airflow và ba target xếp từ spec tĩnh; EvoMaster có thể bớt endpoint trước khi xếp.
- Nhóm `N8` (xoá user) và `N9` (rời group, team) bị loại vì lý do đo đạc (§2).
