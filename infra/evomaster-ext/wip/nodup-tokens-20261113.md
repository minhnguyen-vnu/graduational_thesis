# Mô hình bỏ lặp và `tokens` không regex, trên HEAD `2c3f281f13`, 2026-11-13

Hai thay đổi, một jar. User duyệt mã ngày 2026-11-12 trước khi viết. Chưa commit.

## 1. Bỏ lặp trong đặc trưng op

`opFeatures` lấy `f:` từ tên lá mọi trường, kể cả tham số path, trong khi `p:` đã lấy từ cả chuỗi path. Một từ của
tham số path vì vậy được cộng hai lần (`p:user` và `f:user` từ `{userID}`). Sửa: vòng `f:` bỏ trường `loc == "path"`.
Mô hình học lại với cùng đặc trưng: `infra/analysis/lexicon-rules/m2-nodup-20261112/` (`derive_nodup.py`,
`stateful-authz-model.csv` sha256 `dcc77b59ed0f…`, self-test 11/11 trong thư mục đó). Chỉ bảng `op` đổi; `role`,
`victim`, `low`, `high`, `lowstr`, `highstr` trùng M2 từng dòng.

Số offline (Python, chưa qua jar), phần thi 8.674 op: bắt 117/153 (M2) thành 101/153; chọn 880 thành 624; báo nhầm
763 thành 523. McNemar chính xác: op T p = 3,1e-5 (16 chỉ M2 bắt, 0 chỉ bản bỏ lặp bắt); op N p = 6,9e-67 (244, 4).
`m2-nodup-20261112/ket-qua.txt`. Transition thật của bốn target vẫn qua guard, hạng 1, 1, 1 và 4 thành 3
(artifact-keeper): `m2-nodup-20261112/compare_targets_nodup.out`.

## 2. `tokens` duyệt từng ký tự

`TOKEN_PART = Regex("[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+")` và `findAll` thay bằng vòng `while` gọi
`tokenEnd(text, start)`. `tokenEnd` trả vị trí cuối của mảnh bắt đầu tại `start`:

| Ở `start` | Mảnh | Ứng với nhánh regex |
|---|---|---|
| dãy chữ hoa, sau đó không phải chữ thường | cả dãy (`ABC123` → `ABC`, `A1b` → `A`) | `[A-Z]+(?![a-z])`, độ dài đầy đủ |
| từ 2 chữ hoa, sau đó chữ thường | dãy trừ chữ cuối (`APIKey` → `API`) | `[A-Z]+(?![a-z])` sau khi lùi một ký tự |
| 1 chữ hoa, sau đó chữ thường | chữ hoa + dãy `[a-z0-9]` (`Key`, `User2`) | `[A-Z][a-z0-9]*` |
| chữ thường hoặc số | dãy `[a-z0-9]` | `[a-z0-9]+` |
| ký tự khác | không có mảnh, `tokens` bỏ qua ký tự đó | không nhánh nào khớp |

Chỉ so với `'A'..'Z'`, `'a'..'z'`, `'0'..'9'`: `Char.isUpperCase()` nhận cả `É`, regex cũ thì không. Lọc giữ nguyên:
chữ thường, bỏ từ ngắn hơn `minLength` và từ toàn số. Comment `THESIS` của user phía trên `TOKEN_PART` bị xoá theo
thống nhất; hai dòng `THESIS` của `opFeatures` sửa theo nội dung mới (user duyệt).

## Bản vá

- `nodup-tokens-20261113.patch`: chỉ phần đổi, so với cây có comment `THESIS` (mã + model).
- `nodup-tokens-20261113-tree.patch`: cả cây so với HEAD `2c3f281f13`. Diễn tập rollback: áp lại trùng từng byte.
- `thesis-comments-pre-nodup-20261113.patch`: cây trước thay đổi (chỉ comment `THESIS`), cũng đã diễn tập.

## Commit trước thay đổi

Shorten-logic commit thành `2c3f281f13` (`refactor: merge duplicated logic in stateful-authz builder and oracle`), chỉ
phần mã: 98 dòng đổi trùng phần mã của `shorten-logic-20261112.patch`; comment `THESIS` để ngoài commit như mọi commit
trước. Chưa push.

## Jar

`EvoMaster/evomaster-ND-07ebf19f.jar`, sha256 `07ebf19f9682497e8a9a637e99d66e63e15bf72db4c6f985f92bb656af143897`
(`.sha256` cạnh jar). Model trong jar `dcc77b59ed0f`; `EMConfig` không có cờ `statefulAuthz*`.

## Self-test

`selftest/nodup-tokens-20261113.sh` (cùng `TokensNoRegex.java`, `nodup_corpus.py`, `nodup_scores.py`,
`nodup_compare.py`), so với jar SLM2. Kết quả `em-results/nodup-tokens-selftest-20261113-002956/selftest.out`:
90 PASS, 0 FAIL, máy không ngủ.

- Kiểm tĩnh: regex và `TOKEN_PART` hết khỏi mã và jar; `tokenEnd` có trong jar; bỏ path là lệnh đầu của vòng trường
  trong `opFeatures`; 0 comment mới ngoài `THESIS`, 0 print, 0 stream, 0 hàm ký tự Unicode; đúng 3 dòng `THESIS` đã
  duyệt biến mất và 2 dòng thay có mặt; model trùng sha ở jar, cây và thư mục phân tích.
- `tokens` trong jar so với regex cũ: 742.452 lần so (71.185 chuỗi corpus, 41 ca biên, 300.000 chuỗi ngẫu nhiên;
  `minLength` 1 và 4), 0 lệch. Cùng harness với một regex sai báo 117.170 lệch.
- 17 mode stub, mỗi mode chạy jar ND và SLM2 (`--maxEvaluations 300`, seed 1): điểm transition trong log ND trùng
  Python `op_feats_nodup` + model bỏ lặp, log SLM2 trùng Python `op_feats` + M2 (sai số 1e-9, cùng tập qua guard);
  20 điểm khác M2 đúng như mô hình bỏ lặp; đối chiếu log ND với điểm M2 cho 20 lệch (bộ so sánh trượt được); 970 của
  ND trùng SLM2 ở cả 17 mode.

Review độc lập (agent `thesis-verifier`, không có ngữ cảnh): 7/7 tiêu chí PASS, không gì chặn đo lại. Theo góp ý,
thêm bộ chấm `nodup-pathf` (model bỏ lặp nhưng `f:` vẫn lấy tham số path) và kiểm `forgot-path-caught`; chạy trên log
ND sẵn có của lượt `002956` (chỉ bật stub, không chạy EvoMaster): 18 lệch, tức self-test bắt được jar quên bỏ path
(`compare-supplement-20261113.txt`, 71 PASS). Góp ý chưa làm: `no-comments` không bắt comment cuối dòng; `ascii-only`
không bắt `uppercaseChar()`; hai chỗ đều thừa so với `tokens-equal`, và bản vá không có ca nào như vậy.

Lần chạy đầu (`nodup-tokens-selftest-20261113-002637/`) có 1 FAIL `ascii-only`: mẫu grep `isDigit` khớp nhầm chuỗi
con của `isDigitsOnly(token)`, hàm sẵn có của file (HEAD gọi 2 lần, chỉ so `'0'..'9'`). Mẫu sửa thành lời gọi phương
thức `.isDigit(`, `.isUpperCase(`...; kiểm trên 4 dòng mẫu: bỏ qua `isDigitsOnly(`, bắt 3/3 lời gọi Unicode.
