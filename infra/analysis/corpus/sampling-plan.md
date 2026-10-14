# Mẫu spec cho đợt gán nhãn — bốc 2026-09-18

Lệnh bốc lại y hệt:

```
cd infra/analysis/corpus && python3 sample_specs.py
```

Hai lần chạy cho ra cùng danh sách (đã kiểm bằng `diff`).

## 1. Tham số đã khai trước khi bốc

| Tham số | Giá trị |
|---|---|
| Hạt giống | `20260918` |
| Nguồn | `apis-guru-list.json`, 2.529 API, ảnh chụp ghi ở `PROVENANCE.md` |
| Đơn vị bốc | nhà cung cấp, mỗi nhà cung cấp nhiều nhất một API |
| Nhóm giàu | có ít nhất một trong `security`, `collaboration`, `developer_tools`, `enterprise` — 134 nhà cung cấp |
| Nhóm ngẫu nhiên | phần còn lại — 542 nhà cung cấp |
| Cỡ mẫu | 20 giàu + 10 ngẫu nhiên = 30 |
| Chia train/test | theo nhà cung cấp, 50/50, một nhà cung cấp không nằm cả hai bên |
| Loại trừ | ba target của ta (`vampi`, `pyload`, `reports-api`) |

Vì sao giữ 10 spec nhóm ngẫu nhiên: bốc toàn nhóm giàu thì tỉ lệ endpoint `R` cao giả tạo và bộ từ vựng rút ra chỉ
đúng với loại API đó. Nhóm ngẫu nhiên là chỗ kiểm chứng điều ngược lại.

36 spec WFD nằm ngoài mẫu này: chúng là nguồn ứng dụng chạy được, và hai spec pilot `S034`, `S008` lấy từ đó đã
gán nhãn tối 2026-09-17, báo cáo riêng làm pilot, không nhập vào train hay test.

## 1b. Hai luật thêm sau khi tải spec

Ước lượng 12 operation một spec lấy từ hai spec pilot WFD. Spec thật của apis.guru lớn hơn nhiều: 30 spec đầu cho
1.173 operation ghi, gấp hơn ba lần ngân sách. Hai luật dưới đây chốt sau khi đếm operation, **trước khi nhìn bất
kỳ nhãn nào**.

**Luật A — spec rỗng thì thay.** 8 trong 30 spec không có operation ghi nào, không gán nhãn được. Mỗi cái thay
bằng một nhà cung cấp mới bốc từ đúng pool của nó, hạt giống `20260918 + 1`, giữ nguyên `pool` và `split`
(`replace_empty.py`). Chỉ một vòng thay: `S134` thay vào vẫn rỗng thì bỏ hẳn, không thay tiếp. Còn 29 spec có
operation.

**Luật B — mỗi spec nhiều nhất 15 operation.** Spec nào nhiều hơn thì bốc ngẫu nhiên 15, hạt giống
`20260918 + số hiệu spec` (`cap_ops.py`). Bản trích đầy đủ giữ ở `ops-full/`, không xoá.

Vì sao cắt theo spec chứ không bỏ bớt spec: số nhà cung cấp quyết định độ phủ của bộ từ vựng, còn 200 operation
của riêng GitLab chỉ lặp lại một kiểu đặt tên. Cắt 15 giữ 29 nhà cung cấp mà vẫn vừa ngân sách.

Kết quả: **318 operation** trên 29 spec. Theo giá đo tối 09-17 (79 giây một dòng, 21% số dòng cần người) thì phần
của bạn khoảng 67 dòng, khoảng 88 phút. Tỉ lệ 21% lấy từ 24 dòng pilot nên còn thô; spec thật lệch nhiều hơn thì
số dòng tăng.

## 1c. Luật bổ sung mẫu — chốt 2026-09-19

Vòng 1 cho 318 dòng, trong đó hai máy cùng gán `R` cho 9 dòng. Rút từ vựng và chia train/test trên chừng đó dòng
dương thì mỗi nửa còn 5–8 dòng. Luật dưới đây bổ sung dòng, **không thay** 318 dòng cũ.

**Cổng từ khoá.** Một operation qua cổng khi trong `path`, `summary`, `description`, `param_names`,
`body_field_names` hoặc `enum_values` có ít nhất một từ thuộc danh sách chủ thể và ít nhất một từ thuộc danh sách
quyền (`gate_words.py`, 27 từ chủ thể, 34 từ quyền, tách theo ký tự không phải chữ, cắt đuôi `s`/`es`/`ies`).
Trên 1.727 operation của bản trích đầy đủ: 198 dòng qua cổng, 615 dòng có đúng một loại từ, 914 dòng không có
loại nào.

**Cổng này không phải bộ từ vựng của luận văn.** Nó chỉ là bộ lọc sàng để tiêu ngân sách gán nhãn vào chỗ có
dòng dương. Nó bỏ sót: trong 14 dòng `R` mà lượt L1 vòng 1 gán trên mẫu ngẫu nhiên, chỉ 7 dòng qua cổng. Vì vậy
318 dòng ngẫu nhiên giữ nguyên trong ngữ liệu và là tầng duy nhất dùng để nói về tỉ lệ.

**Bốc thêm.** Với mỗi spec, ngoài các dòng đã có ở vòng 1: bốc ngẫu nhiên tối đa **15** dòng qua cổng và tối đa
**6** dòng chỉ có một loại từ, hạt giống `20260919 + số hiệu spec` (`enrich_gate.py`). Trần 15/6 chọn từ bảng đếm
theo ngân sách "thêm không quá 300 dòng", in ra trước khi nhìn nhãn nào; nhãn vòng 1 chỉ được xem sau đó, để
tính tỉ lệ bỏ sót của cổng ghi ở trên.

Nhóm 6 dòng một loại từ dùng để ước lượng cổng bỏ sót bao nhiêu trong nhóm giáp ranh, chứ không phải để làm giàu.

Kết quả: **519 dòng** trên 29 spec (`labelling-r2/`) = 318 cũ + 111 qua cổng + 90 một loại từ.

**Hệ quả khi đo.** Ngữ liệu gồm hai tầng có xác suất lấy mẫu khác nhau. Precision/recall báo cáo riêng trên tầng
ngẫu nhiên của các spec test; tầng làm giàu chỉ dùng để rút từ vựng và để báo cáo thêm. Không lấy tỉ lệ `R`
của ngữ liệu này làm tỉ lệ `R` của thế giới thật.

## 1d. Tầng soát của lượt người — chốt 2026-09-20

Thay cho "bốc ngẫu nhiên 20% số dòng hai máy đồng thuận". Lượt người gán 121 dòng theo ba tầng:

| Tầng | Cỡ | Soát | Xác suất vào mẫu |
|---|---|---|---|
| hai máy lệch nhau hoặc có `U` | 44 | toàn bộ | 1 |
| hai máy cùng `R` | 37 | toàn bộ | 1 |
| hai máy cùng `N` | 438 | bốc 40, hạt giống `20260918` | 40/438 |

Lý do: bộ từ vựng rút ra từ các dòng `R`. Tầng này có 37 dòng, soát hết thì mọi dòng dương đi vào từ vựng đều
có một lượt người đọc. Mẫu bốc trước khi người nhìn bất kỳ nhãn nào, bằng `stratify_r2.py`.

Giá phải trả: tỉ lệ sai của phần đồng thuận không soát nay dựa trên 40 dòng thay vì 95. Nếu lượt người không
tìm thấy dòng sai nào, khoảng Wilson 95% là [0; 0,088] trên tầng `N`, tức [0; 0,081] quy về toàn bộ 475 dòng
đồng thuận. Với 95 dòng thì cận trên là 0,039.

Cách tính sau khi gán xong:

- Tỉ lệ sai của tầng đồng thuận = `(e_R + 438 × p_N) / 475`, với `e_R` là số dòng sai đếm đủ trên 37 dòng `R`
  và `p_N` là tỉ lệ sai trên 40 dòng `N`. Khoảng tin cậy lấy Wilson của `p_N` rồi nhân `438/475`.
- Kappa người–máy trên tầng đồng thuận tính có trọng số: mỗi dòng `R` trọng số 1, mỗi dòng `N` trọng số 438/40.
  Không báo cáo kappa gộp 77 dòng không trọng số.
- Tầng lệch nhau 44 dòng báo cáo riêng, không trộn vào hai số trên.

**Mô hình can thiệp, 2026-09-20.** Người gán xong 121 dòng rồi yêu cầu mô hình làm hai việc, ghi ở
`labelling-r2/`:

| Việc | Sổ | Đụng vào gì |
|---|---|---|
| Chuẩn hoá 14 mã luật trong nội bộ `N` | `model-revisions.csv` | cột `rule_id` |
| Phân xử 20 dòng tầng `agree-R` mà người và hai lượt máy lệch nhau | `adjudication.csv` | cột `final_label` |

Cột `label` giữ nguyên nhãn người gán độc lập, nên kappa người–máy vẫn tính được trên lượt gốc. Kappa báo cáo
là con số tính trên cột `label`. Con số tính trên `final_label` cao hơn vì mô hình phân xử theo phía máy 17/20
lần; nó không phải thống kê đồng thuận và không được trích dẫn như vậy.

Sai lệch so với giao thức: `labelling-form.md` §8.2 ghi người phân xử, LLM không tham gia. Hai mươi dòng này
do mô hình phân xử. Ghi ở `rules-changelog.md`.

## 1e. Mở rộng nửa train — chốt 2026-09-21

Lý do: nửa train chỉ có 26 dòng `R` trên 5 nhà cung cấp, trong đó keycloak và gitlab chiếm 18.
Bộ từ vựng rút ra từ đó bỏ sót 6 trong 7 dòng `R` của nửa test vì từ tương ứng
(`securityentries`, `collaborators`, `teams`) không có trong một dòng `R` nào của nửa train
(`../lexicon-rules/lexicon-20260920/RESULTS.md` §3).

| Tham số | Giá trị |
|---|---|
| Nguồn | `apis-guru-list.json`, đúng file đã dùng ngày 09-18 |
| Pool | chỉ tầng làm giàu, 110 nhà cung cấp còn lại sau khi loại 38 đã dùng |
| Số bốc | 15 |
| Seed | `20260921` (`sample_specs_ext.py`) |
| Một API một nhà cung cấp | giữ nguyên, chọn bằng seed `20260918` như lần đầu |
| split | tất cả vào **train** |
| Cap | 36 operation ghi một spec, seed `20260921 + số spec` (`cap_ext.py`) |
| spec_id | S200–S214 |
| Ra | `ops-ext/`, `../lexicon-rules/labelling-r3/` |

Nửa test không đổi và không được mở lại. Việc chỉ thêm vào nửa train giữ được ranh giới train/test,
nhưng không sửa được một điều: nửa test đã bị dùng để phát triển, khai ở `rules-draft.md` §12.5.

15 spec: akeneo.com, anchore.io, apimatic.io, cdcgov.local, citrixonline.com, cycat.org,
extendsclass.com, firmalyzer.com, fisheye.local, getsandbox.com, github.com, id4i.de, shorten.rest,
slack.com, visualstudio.com. Tổng 249 dòng sau cap.

## 1g. Nhãn chốt cho phần mở rộng — chốt 2026-09-21 00:28, viết khi chưa thấy lượt L1

Phần mở rộng không có lượt người. Luật:

- Hai lượt máy cùng nhãn `R` hoặc cùng nhãn `N`: lấy nhãn đó, `audited=0`, `nguon = "may trung nhau, khong soat"`.
- Hai lượt lệch nhau, hoặc một trong hai gán `U`: **loại khỏi phần rút từ vựng**, đếm riêng và báo số.
  Không ai phân xử, không mô hình nào gán thay.
- Không dòng nào của phần mở rộng vào nửa test, vào bảng kappa của `labelling-r2`, hay vào `final.csv` cũ.

Lý do loại thay vì phân xử: `rules-changelog.md` đã ghi một lần sai lệch giao thức, khi mô hình phân xử
32 dòng thay người. Lặp lại việc đó trên 266 dòng nữa thì phần mở rộng không còn điểm tựa ngoài mô hình.

Số dòng bị loại được báo cùng bộ từ vựng, vì nó là giới hạn của bộ đó.

## 1h. Gán bù để đo hạng chính xác — chốt 2026-09-21 00:47, viết trước khi gán

Vấn đề: mỗi spec chỉ giữ tối đa 36 operation ghi, trong khi spec thật có tới 451. Hạng đo trên phần
đã giữ là lạc quan; hạng đo trên toàn bộ mà coi mọi dòng chưa gán là `N` là bi quan.
Nửa test: top-1 `0.667` so với `0.167`, top-3 `1.000` so với `0.667`.

Luật chọn dòng gán bù: trong mỗi spec có endpoint `R` đã biết, lấy **mọi** endpoint ghi xếp trên
endpoint `R` điểm cao nhất của spec đó, theo đúng thứ tự §12.4. 41 dòng, 11 spec, ghi ở `labelling-r4/`.

Hai ràng buộc:

- 41 dòng này **chỉ dùng để đo hạng**, không vào phần rút từ vựng. Chọn dòng theo điểm rồi lấy chính
  chúng làm dữ liệu huấn luyện là vòng tròn.
- Vẫn hai lượt máy mù, vẫn luật §1g: hai máy cùng nhãn thì lấy, lệch nhau hoặc có `U` thì loại và đếm.

Sau khi gán, hạng của mỗi spec là chính xác trong phạm vi các dòng đã gán: không còn dòng chưa biết
nào xếp trên endpoint `R` của spec đó.

## 1i. Lượt soát thứ ba trên phần mở rộng — chốt 2026-09-21, viết trước khi gán

`labelling-r3` (266 dòng) và `labelling-r4` (41 dòng) chỉ có hai lượt máy, không có lượt người của
`rules-draft.md` §9. Mục này thêm một lượt gán mù thứ ba và khai trước cách dùng kết quả.

**Ai gán.** Một agent rời, phiên riêng, chỉ mở `labelling-form.md` v2 và file dòng vào. Không thấy nhãn L1, L2,
không thấy `final.csv`, không thấy kết quả xếp hạng, không thấy tên nhà cung cấp, không thấy chia train/test,
không thấy hội thoại này. Đây là lượt máy thứ ba, không phải lượt người.

**Gán dòng nào.** Toàn bộ 28 dòng có `final_label = R` của hai mẻ, cộng 28 dòng bốc ngẫu nhiên từ các dòng
`final_label = N` của cùng hai mẻ, hạt giống `20260921`, bốc trước khi gán. Dòng nhiễu để lượt gán không nhìn ra
mình đang xem một tập toàn `R`. Thứ tự trộn theo cùng hạt giống.

**Dùng kết quả thế nào.** Trên 28 dòng `R`: nhãn của lượt soát là nhãn chốt, `audited=1`, `nguon=audit-3`.
Dòng lượt soát gán `N` rời khỏi tập `R`. Dòng lượt soát gán `U` bị loại, theo §1g. 28 dòng nhiễu không đổi nhãn
chốt: chúng chỉ dùng để đo đồng thuận.

**Phải báo cáo.** Tỉ lệ thô và kappa hai lớp `R`/`N` giữa lượt soát và nhãn đồng thuận của hai lượt máy, tính
riêng cho nhóm `R` và nhóm nhiễu, kèm số dòng `U` đã bỏ.

**Lượt này không tìm được gì.** Nó chỉ xem các dòng hai lượt máy đã gọi là `R`, nên không phát hiện được dòng
`R` bị hai lượt máy bỏ sót. Sai sót theo chiều đó vẫn không có phép đo nào.

## 1f. Sửa trích xuất envelope — chốt 2026-09-21

`extract_ops.py` trước đây trả `body_field_names` là đúng chữ `data` với spec bọc thân theo JSON:API.
`unwrap_envelope` nay bóc `data`, rồi gộp `attributes` với `relationships` khi phần còn lại chỉ là
khoá envelope. Ví dụ `PATCH /v1/users/{id}` của S131: `data` thành
`allAppsVisible;provisioningAllowed;roles;visibleApps`.

17 trong 25 dòng của S131 đổi. Nhãn cũ của chúng giữ nguyên trong `labelling-r2/`; bản trích lại nằm ở
`labelling-r3/S131.v2.csv` và được gán lại từ đầu bằng hai lượt máy mù.

## 2. Danh sách đã bốc

| spec_id | nhà cung cấp | API | pool | split | op ghi | op giữ v1 | op giữ v2 | ghi chú |
|---|---|---|---|---|---|---|---|---|
| S100 | apideck.com | `apideck.com:file-storage` | enriched | train | 21 | 15 | 15 | - |
| S101 | appcenter.ms | `appcenter.ms` | enriched | train | 151 | 15 | 36 | - |
| S102 | authentiq.io | `authentiq.io` | enriched | train | 4 | 4 | 4 | - |
| S103 | bluemix.net | `bluemix.net:containers` | enriched | test | 27 | 15 | 21 | - |
| S104 | configcat.com | `configcat.com` | enriched | train | 35 | 15 | 21 | - |
| S105 | credas.co.uk | `credas.co.uk:pi` | enriched | train | 19 | 15 | 17 | - |
| S106 | crucible.local | `crucible.local` | enriched | train | 36 | 15 | 21 | - |
| S107 | flat.io | `flat.io` | enriched | test | 47 | 15 | 25 | - |
| S108 | gitea.io | `gitea.io` | enriched | test | 159 | 15 | 36 | - |
| S109 | gitlab.com | `gitlab.com` | enriched | train | 200 | 15 | 36 | - |
| S110 | interzoid.com | `interzoid.com:getcitymatch` | enriched | train | 0 | 0 | 0 | - |
| S111 | ip2location.io | `ip2location.io` | enriched | test | 0 | 0 | 0 | - |
| S112 | keycloak.local | `keycloak.local` | enriched | train | 147 | 15 | 36 | - |
| S113 | link.fish | `link.fish` | enriched | test | 0 | 0 | 0 | - |
| S114 | noosh.com | `noosh.com` | enriched | train | 25 | 15 | 21 | - |
| S115 | openlinksw.com | `openlinksw.com:osdb` | enriched | test | 3 | 3 | 3 | - |
| S116 | osisoft.com | `osisoft.com` | enriched | test | 161 | 15 | 21 | - |
| S117 | truanon.com | `truanon.com` | enriched | test | 0 | 0 | 0 | - |
| S118 | uscann.net | `uscann.net` | enriched | train | 5 | 5 | 5 | - |
| S119 | zapier.com | `zapier.com:nla` | enriched | train | 1 | 1 | 1 | - |
| S120 | aucklandmuseum.com | `aucklandmuseum.com` | random | test | 2 | 2 | 2 | - |
| S121 | bandsintown.com | `bandsintown.com` | random | train | 0 | 0 | 0 | - |
| S122 | betfair.com | `betfair.com` | random | train | 1 | 1 | 1 | - |
| S123 | bungie.net | `bungie.net` | random | test | 46 | 15 | 31 | - |
| S124 | isendpro.com | `isendpro.com` | random | test | 12 | 12 | 12 | - |
| S125 | just-eat.co.uk | `just-eat.co.uk` | random | train | 69 | 15 | 31 | - |
| S126 | nasa.gov | `nasa.gov:apod` | random | test | 0 | 0 | 0 | - |
| S127 | refugerestrooms.org | `refugerestrooms.org` | random | test | 0 | 0 | 0 | - |
| S128 | shotstack.io | `shotstack.io` | random | test | 2 | 2 | 2 | - |
| S129 | tcgdex.net | `tcgdex.net` | random | test | 0 | 0 | 0 | - |
| S130 | personio.de | `personio.de:authentication` | enriched | train | 1 | 1 | 1 | thay S110 |
| S131 | apple.com | `apple.com:app-store-connect` | enriched | test | 103 | 15 | 25 | thay S111 |
| S132 | trello.com | `trello.com` | enriched | test | 181 | 15 | 21 | thay S113 |
| S133 | getpostman.com | `getpostman.com` | enriched | test | 34 | 15 | 15 | thay S117 |
| S134 | etmdb.com | `etmdb.com` | random | train | 0 | 0 | 0 | thay S121 |
| S135 | paypi.dev | `paypi.dev` | random | test | 2 | 2 | 2 | thay S126 |
| S136 | sinao.app | `sinao.app` | random | test | 161 | 15 | 34 | thay S127 |
| S137 | naviplancentral.com | `naviplancentral.com:factfinder` | random | test | 72 | 15 | 23 | thay S129 |

`op giữ v1` là trần 15 của vòng 1, tổng **318** dòng. `op giữ v2` là số dòng thật sự nằm trong
`../lexicon-rules/labelling-r2/final.csv` sau khi §1c bổ sung mẫu, tổng **519** dòng trên 29 spec;
nó chạy từ 1 đến 36 vì §1c thêm tối đa 15 dòng qua cổng và tối đa 6 dòng một loại từ cho mỗi spec.
Mọi con số rút từ vựng và đo hạng dùng cột v2. Train 14 spec, test 15 spec.

Mười lăm spec mở rộng S200–S214 (§1e, 249 dòng, cap 36, tất cả vào train) không nằm trong bảng này;
danh sách nhà cung cấp ghi ở §1e, dòng ở `../lexicon-rules/labelling-r3/`.

## 3. Lệnh chạy lại toàn bộ

```
python3 sample_specs.py --json > sample-picked.json
python3 replace_empty.py
python3 cap_ops.py
```

Spec tải về nằm ở `specs/`, bản trích đầy đủ ở `ops-full/`, bản đã cắt ở `../lexicon-rules/labelling/`.

## 4. Chưa làm

Hai lượt máy gán nhãn mù trên 318 operation, rồi chia tầng và bốc mẫu soát như `rules-draft.md` §9.
