# Rút bộ từ vựng lần 3 — 2026-09-21, nhãn đã soát

Thay `lexicon-20260921/` làm bộ từ vựng được đóng vào jar. Luật tính điểm giữ nguyên `../rules-draft.md`
§11 và §12, không sửa một chữ. Ba thứ đổi so với lần 2: nhãn phần mở rộng được soát lại, cách tách từ
của nửa `param` được sửa, và thước đo hạng được viết lại thành khoảng.

Chạy: `python3 ../derive3.py` và `python3 ../rank_exact2.py stateful-authz-lexicon.csv final.v2.csv`.

## 1. Lượt soát nhãn thứ ba

Luật khai trước khi chạy: `../../corpus/sampling-plan.md` §1i.

Một lượt riêng, mù, chỉ được mở `labelling-form.md` v2 và file dữ liệu vào. Mẫu 56 dòng: toàn bộ 28 dòng
`final_label = R` của phần mở rộng, cộng 28 dòng `N` bốc bằng hạt giống `20260921` làm dòng nhiễu. Lượt gán
không biết dòng nào thuộc nhóm nào. Dữ liệu vào dựng bằng `../make_audit_in.py`, kiểm cấu trúc độc lập bằng
`../verify_audit3.py`: 56 dòng, 9 cột vào trùng từng byte với bản gốc, mã hợp lệ, **0 lỗi**. Kết quả thô
25 `R` / 30 `N` / 1 `U`.

| Nhóm | Dòng | Bỏ vì `U` | Đồng thuận thô | `pe` | kappa |
|---|---|---|---|---|---|
| hai máy cùng `R` | 28 | 1 | 0.926 | 0.926 | 0.000 |
| hai máy cùng `N` | 28 | 0 | 1.000 | | |
| cả 56 dòng | 56 | 1 | **0.964** | 0.501 | **0.927** |

Kappa `0.000` ở nhóm trên là hệ quả của việc bốc mẫu theo nhãn: trong một nhóm chỉ có một lớp thì `pe = po`,
nên kappa suy biến. Con số dùng được là đồng thuận thô `0.926` và kappa `0.927` trên cả 56 dòng.

Ba dòng đổi, tất cả thuộc nửa train:

| Dòng | Endpoint | Cũ | Mới |
|---|---|---|---|
| S210-0137 | `PUT /orgs/{org}/outside_collaborators/{username}` | `R` | `N` |
| S211-0008 | `PUT /api/v1/apikeys/{key}` | `R` | `N` |
| S214-0106 | `POST .../plans/{resourceName}/deleteDelegates` | `R` | `U`, bỏ |

Bốn mươi mốt dòng gán bù ở `labelling-r4/` được soát cùng đợt: **0 dòng đổi nhãn**, chỉ cột `audited` từ
`0` lên `1` và `nguon` thành `audit-3`. Nhãn dùng để đo hạng không đổi.

Lượt này không tìm được dòng `R` mà cả hai lượt máy cùng bỏ sót: mẫu chỉ gồm dòng hai máy đã đồng thuận.
Khai ở `sampling-plan.md` §1i.

## 2. Lỗi tách từ ở nửa `param`

`derive_lexicon.py` hạ chữ thường trước khi tách camelCase; `derive2.py` không. `../rules-draft.md` §11.4 khai
thứ tự: tách theo ký tự không phải chữ-số, rồi tách camelCase, rồi mới hạ chữ thường. Nửa `param` của
`lexicon-20260921/` chạy sai thứ tự nên giữ lại `permissiongroupid` và `policyid` — hai token dính liền
không tồn tại trong spec.

`derive3.py` sửa: sinh ứng viên từ chuỗi gốc, không hạ chữ thường trước. Nửa `path` tái lập trùng từng byte
với bản cũ, nên lỗi chỉ ảnh hưởng nửa `param`.

## 3. Bộ từ vựng

Train: 36 `R` / 441 `N`, 29 nhà cung cấp, **10 nhà cung cấp có `R`** (lần 2: 39 `R` / 11 nhà cung cấp).

| Danh sách | Trường | Ứng viên | Qua P1+P2 | P3 bỏ | Giữ |
|---|---|---|---|---|---|
| 1 `transitionPathSignals` | `path` | 53 | 6 | 2 | 4: `client members permission user` |
| 2 `transitionUserParamSignals` | `param_names` | 45 | 4 | 1 | 3: `client email user` |
| 3 `roleFieldSignals` | `body_field_names` | 135 | 26 | 3 | 23 |

File đóng vào jar: `stateful-authz-lexicon.csv`, **53 từ `path`, 45 từ `param`**, mỗi từ kèm điểm. Danh sách 3
đã rút nhưng chưa dùng: cổng chặn hiện chỉ đọc `path` và verb (§6).

## 4. Hạng trên nửa test

Xếp trên **mọi endpoint ghi** của spec, đúng tập mà `RestSecurityBuilder` nhìn thấy.

| | top-1 | top-3 | top-8 |
|---|---|---|---|
| khoảng tốt nhất–xấu nhất | 0.333–0.667 | 0.500–0.667 | 0.833–1.000 |
| theo thứ tự spec | **0.500** | **0.667** | **1.000** |

| Spec | Hạng | Trên tổng | Thứ tự spec |
|---|---|---|---|
| S107 | 1 | 47 | 1 |
| S116 | 1 | 161 | 1 |
| S123 | 1–10 | 46 | 1 |
| S131 | 1–3 | 103 | 2 |
| S136 | 5 | 161 | 5 |
| S108 | 6 | 159 | 6 |

Số liệu: `rank-exact.txt`.

## 5. Vì sao con số là khoảng, không phải một giá trị

`lexicon-20260921/RESULTS.md` §8 ghi "top-1 0.500, top-3 0.833, top-8 1.000 ... là chính xác, không phải
khoảng". Sai. Nhiều endpoint có cùng điểm, cùng verb, cùng trạng thái tham số người dùng; hạng của endpoint
`R` trong nhóm bằng điểm đó do một luật phá hoà chưa khai quyết định. S123 là ví dụ: endpoint `R` nằm trong
nhóm 10 endpoint bằng điểm, nên hạng của nó là `1–10`, không phải `2`.

Thước đo thay bằng hai con số. Khoảng tốt nhất–xấu nhất là cận của mọi luật phá hoà. Giá trị "theo thứ tự
spec" phá hoà bằng thứ tự endpoint trong spec, tức thứ tự `actionDefinitions` mà EvoMaster thật sự nhận.
Con số thứ hai là con số áp dụng được.

## 6. Giá của lượt soát: một spec

Cùng bộ nhãn test đã soát, chỉ đổi bộ từ vựng:

| Bộ từ vựng | top-1 khoảng | top-1 thứ tự spec | top-3 thứ tự spec |
|---|---|---|---|
| lần 2, chưa soát (63 path / 50 param) | 0.500–0.833 | 0.667 | 0.833 |
| lần 3, đã soát (53 path / 45 param) | 0.333–0.667 | **0.500** | **0.667** |

Chênh lệch nằm ở đúng một spec: S108 tụt từ hạng 1 xuống hạng 6. Nguyên nhân là một dòng train,
S210-0137 `PUT /orgs/{org}/outside_collaborators/{username}`, chuyển từ `R` sang `N`. Từ `collaborators`
đi từ 2 dòng `R` / 0 dòng `N` xuống 1 / 1, nên điểm tụt `0.3750` xuống `0.2500`.

Luật ngày 09-17 xếp "đưa một chủ thể ra khỏi nhóm" vào diện không tính (`../rules-draft.md` §8). Lượt soát
áp đúng luật đó. Luật không sửa sau khi thấy giá của nó.

## 7. So với `firstOrNull` hiện tại

`findPermissionReducingTransition` (`RestSecurityBuilder.kt:809`) lọc bằng 8 từ cứng rồi lấy `firstOrNull`.
Trên nửa test, endpoint nó chọn là endpoint `R` ở **0 trong 6 spec**. Bộ từ vựng đã soát, xếp hạng theo điểm,
chọn đúng ở **3 trong 6**. Tám từ cứng chưa bao giờ được chỉnh trên corpus này, nên `0/6` là con số sạch.

## 8. Chạy thật trên ba target

Jar `5b3d54421e22d038`, từ vựng của mục 3 đóng trong `core/src/main/resources/`.
Chuỗi `infra/em-results/lexicon-chain-20260921/`.

| | Kết quả |
|---|---|
| Self-test `selftest/lexicon-rank.sh` | 14/14 đạt |
| Cổng hồi quy, 21 dòng | 21/21 trùng |
| Tier-1 bản lỗi, seeds 1–10 | 970 nổ 10/10 |
| Tier-2 bản lỗi, seeds 1–10 | 3/10, seed 1, 5, 10 |
| pyLoad bản lỗi, seeds 1–10 | 10/10 |
| Tier-1 + Tier-2 bản đã vá, 20 lần | 0 báo động giả |

Đối chiếu từng seed với jar D1 (`d1-seeds1-10/`, `d1-pyload-seeds1-10/`, nhánh `d1=false`): 30 dòng chung,
**0 dòng lệch**. Thay 8 từ `path` và 9 từ `param` cứng bằng 53 và 45 từ rút từ corpus không mất phát hiện nào.

## 9. Bốn điều chưa chứng minh

- Nửa test đã bị dùng để phát triển từ 09-20 (`../rules-draft.md` §12.5). Luật §11 và §12 đóng băng trước khi
  corpus mở rộng, nhưng đây không phải ước lượng trên dữ liệu chưa ai nhìn.
- `top-8 = 1.000` không chuyển được sang runtime. `harvestReducedRoleCandidates` gom `enumVocab` từ
  `allGenes(transition) + actionDefinitions.flatMap { allGenes(it) }`, tức toàn bộ API, nên ứng viên hạng 1
  hầu như luôn có giá trị quyền để đề xuất và vòng lặp 8 ứng viên không bao giờ chạy sang ứng viên thứ hai.
  Self-test `harvest-is-global` ghi lại đúng hành vi này: 6 giá trị quyền thu được trên `POST /auth/login`,
  một endpoint không có trường quyền nào. `MAX_TRANSITION_CANDIDATES = 8` hiện không có tác dụng lúc chạy.
- 240 dòng `N` của phần mở rộng vẫn mang nhãn hai máy đồng thuận, `audited=0`. Lượt soát chỉ phủ 28 dòng `R`
  và 28 dòng `N` bốc làm nhiễu.
- Danh sách 3 (`roleFieldSignals`, 23 từ) chưa vào jar. Cổng chặn đọc `path + " " + "VERB:path"` nên không
  trường thân yêu cầu nào tới được nó; đây là lý do `PATCH /auth/fab/v1/users/{username}` của Airflow bị bỏ sót.
