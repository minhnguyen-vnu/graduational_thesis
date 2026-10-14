# Rút lexicon nhóm A từ nhãn vòng 4 — protocol

Chốt 2026-10-07 trước 23:29 (trước khi chụp spec vampi lúc 23:29:33 và trước lượt chạy đầu), trước khi chạy bất kỳ phép rút hay phép đo nào của protocol này. Chỉ đo offline; không sửa mã
EvoMaster, không chép file lexicon mới vào `core/src/main/resources/`. User duyệt lịch và bốn đề xuất lúc 23:20 ("bắt đầu
làm theo lịch luôn"), không dùng agent. Thay đổi sau khi chốt ghi ở §9.

## 1. Luật cũ, chép từ mã

Lexicon trong jar (`lexicon-20260921-audited/stateful-authz-lexicon.csv`, sha256 `535265ea…`) do `../derive3.py` sinh:

- Dữ liệu: dòng `R`/`N` nửa train (`labelling-r2/final.csv`, `labelling-r3/final.v2.csv`; S200–S214 vào train), dòng `U`
  bị bỏ.
- Hai danh sách: `path` (ứng viên và chuỗi đếm là `path + " " + method + ":" + path`) và `param` (ứng viên và chuỗi đếm là
  `param_names`).
- Ứng viên: token tách từ trường đó của dòng `R` (`derive3.py:60–69`): cắt ký tự không chữ-số, tách camelCase, hạ chữ
  thường, bỏ token toàn số, bỏ token < 4 ký tự.
- Điểm: `(df_R + 1)/(df_R + df_N + 2) × ncc/(ncc + 1)`, đếm chuỗi con. File giữ **mọi** ứng viên kèm điểm, không ngưỡng.
  Định dạng `kind,word,score`, điểm 4 chữ số, sắp `path` trước, điểm giảm dần, rồi từ.
- Runtime (jar `RF` trở đi): điểm endpoint = điểm lớn nhất của từ `path` nằm trong `pathHay + " " + tên trường thân cấp
  đỉnh`; cộng 0,6 khi chuỗi đó chứa từ của danh sách admin; hoà điểm thì endpoint có tên tham số chứa từ `param` trước,
  rồi verb `PUT, PATCH, POST, DELETE`, rồi thứ tự spec (`rules-draft.md` §12–13, `RestSecurityBuilder.kt:101–121`,
  `:945–954`).

## 2. Dữ liệu mới

`../field-labelling-r4-20261006/final-all.csv` và `rows-all.jsonl`: 10.381 op ghi của 230 API, nhãn `T`.

- `R := T = 1`, `N := T = 0`. Lệch định nghĩa với nhãn cũ: cấp quyền thuần (`N3` cũ) thành `R`; khoá tài khoản (`R4` cũ)
  thành `N`.
- Dựng trường như `derive3.py` cần: `path`, `method`; `param_names` = tên trường `loc` path/query (vòng 4 không trích
  header); tên trường thân cấp đỉnh = trường `loc` body không có `.` và `[` (như `sim.hay`).
- Nhà cung cấp: `sim.providers()` vòng 4.

## 3. Arm

| Arm | Lexicon | Ứng viên và chuỗi đếm `path` | Cộng 0,6 |
|---|---|---|---|
| A-cur | file trong jar | như cũ | có |
| A-new | rút từ nhãn vòng 4 | `pathHay`, như luật cũ | có |
| A-newV1 | rút từ nhãn vòng 4 | ứng viên từ path và tên trường thân cấp đỉnh của op `R`; đếm trên `pathHay + tên trường thân`, đúng chuỗi runtime so | có |
| A-newV1-0 | như A-newV1 | như A-newV1 | không |

Danh sách `param` của các arm mới rút như luật cũ từ `param_names` mới. Mọi arm chấm endpoint bằng chuỗi runtime
(`pathHay + tên trường thân`). Danh sách admin cho 0,6 là bộ viết tay (`sim.HARD`), như jar hiện tại.

## 4. Đo

**Kiểm chéo:** nhóm theo nhà cung cấp, 5 phần × 4 lần lặp, seed `20261006` (thứ tự xáo như `sim.cv`), lần 1 là số chính.
Lexicon mới rút trên các phần train. Spec test chỉ tính khi spec đó **không** thuộc 29 spec lexicon cũ đã học (nửa train
cũ + S200–S214).

**Chỉ số:**
- Hạng (thước đo `rules-draft.md` §12.4, `../rank_field.py`): mỗi spec test có ít nhất một op `T = 1`, sắp mọi op ghi theo
  khoá runtime; top-1, top-3, top-8 theo thứ tự spec (số chính) và khoảng tốt nhất–xấu nhất.
- Mô phỏng runtime (`../field-labelling-r4-20261006/sim.py`, đổi lexicon theo arm): M1, M1any, M2, M5; nhóm B giữ bộ viết
  tay (V, như jar) là số chính, nhóm B = RF (`../field-ranking-v2-20261007/`) báo thêm.
- McNemar chính xác hai phía ghép đôi theo spec (M5 theo op); KTC 95% bootstrap theo nhà cung cấp 2.000 lần, lần lặp 1.
- So: A-new − A-cur, A-newV1 − A-new, A-newV1-0 − A-newV1, A-newV1-0 − A-cur.

**Target** (lexicon rút trên toàn bộ dữ liệu): hạng của transition đã biết trong mọi op ghi (khoá runtime, kèm khoảng hoà)
và trong danh sách transition khả dụng (8 đầu, lọc nhóm B = V):

| Target | Spec | Transition |
|---|---|---|
| reports-api | `targets/reports-api.json` (chụp từ app đang chạy, 23:25) | `PUT /users/{username}/role` |
| vampi-seeded | `infra/vampi-seeded/openapi_specs/openapi3.yml` | `PUT /users/v1/{username}/role` |
| pyLoad | `infra/pyload-cve/openapi-merged.json` | `POST /api/set_user_permission` |
| Airflow | `infra/airflow-target/airflow-merged.json` | `PATCH /auth/fab/v1/users/{username}` |
| artifact-keeper | `infra/em-results/artifactkeeper-machine-20261001/openapi-trimmed.json` | `PATCH /api/v1/users/{id}` |
| bamf | `infra/bamf-target/run-bamf/openapi.json` | `PATCH /api/v1/users/{email}` |

## 5. Self-test (`checks.py`, mỗi kiểm một dòng PASS/FAIL, exit 0 khi mọi kiểm đạt)

| Mã | Kiểm | Bước dừng nếu trượt |
|---|---|---|
| C1 | Mã rút mới chạy trên nhãn và dòng cũ ra file trùng từng byte với lexicon trong jar | dừng hẳn |
| C2 | Mã đo hạng với lexicon jar trên nhãn cũ ra lại `field-gate-20260923/rank-field.txt` (V0, V1; train, test; theo spec và khoảng) | dừng hẳn |
| C3 | Mô phỏng với lexicon jar ra lại số V và R4 vòng 4 (lần lặp 1: V M1 18, M2 17, M5 4; R4 M1 16, M2 17, M5 165) | dừng hẳn |
| C4 | Nhãn: 10.381 op, 199 op `T = 1`, 56 nhà cung cấp có `T = 1`, không trùng `row_id`, mọi nhãn có dòng | dừng |
| C5 | Spec cũ và spec vòng 4 cùng mã là cùng một spec: mọi (method, path) của dòng cũ có trong dòng vòng 4 | dừng |
| C6 | Đếm độc lập `df_R`, `df_N`, `ncc` của `permission`, `admin`, `user` trên dữ liệu mới bằng vòng lặp đơn, so với kết quả rút | dừng |
| C7 | Không rò rỉ: mỗi phần, nhà cung cấp train ∩ test = ∅; spec test ∩ 29 spec cũ = ∅ | dừng |
| C8 | Đối chứng âm: xáo nhãn `T` trên phần train (seed `20261006`) rồi rút A-newV1-0; top-1 theo spec phải thấp hơn bản thật, kèm mức ngẫu nhiên kỳ vọng | không kết luận về hạng nếu trượt |
| C9 | Chạy toàn bộ hai lần, hash đầu ra như nhau | dừng |
| C10 | File lexicon mới: header `kind,word,score`, kind ∈ {path, param}, không trùng (kind, word), điểm trong (0, 1) | dừng |
| C11 | Hạng target với lexicon jar ra lại `field-gate-20260923/rank-targets.txt` cho reports-api, vampi, pyLoad, Airflow (dòng V1), và log thật AF2 của artifact-keeper (8 ứng viên, điểm, 2 ứng viên có giá trị hạ quyền) | dừng phần target |

Kiểm phải có khả năng trượt: C1, C2, C3, C11 so với file đã ghi từ trước; C8 so hai số đo.

## 6. Luật chọn

A-newV1-0 (bản tổng quát nhất) được đề xuất thay lexicon hiện tại khi, ở lần lặp 1:
- không thua A-cur có ý nghĩa (p < 0,05) ở top-1, top-3, top-8 theo thứ tự spec, M1, M2 (nhóm B = V);
- số target có transition nằm trong danh sách khả dụng 8 đầu không ít hơn A-cur.

M5 báo kèm, không nằm trong luật. Nếu A-newV1-0 không đạt, các arm còn lại chỉ ra phần nào gây thua; không chọn arm khác
thay. Không đổi luật sau khi thấy số.

## 7. Đầu ra

`derive_r4.py`, `measure.py`, `checks.py`, `lexicon-*.csv`, `candidates-*.csv`, `cv.json`, `targets.json`,
`report.py` (sinh mọi bảng của `RESULTS.md` từ JSON), `RESULTS.md`. Xong thì chụp thư mục sang `~/thesis-backups/`.

## 8. Giới hạn biết trước

- Định nghĩa nhãn lệch với nhãn cũ (§2); A-cur học `R` cũ nhưng được chấm theo `T` mới.
- 15 spec nửa test cũ đã được nhìn khi chỉnh luật lexicon cũ (`rules-draft.md` §12.5); chúng nằm trong tập test chung.
- Vòng 4 không có tên tham số header; `param_names` mới hẹp hơn cũ.
- Mô phỏng chưa đối chiếu với lượt EvoMaster thật.

## 9. Thay đổi sau khi chốt

- 23:29, trước khi chạy: spec vampi đổi từ `openapi3.yml` sang bản JSON chụp từ app đang chạy (`targets/vampi-seeded.json`,
  `/openapi.json`, đúng URL EvoMaster dùng); `rank-targets.txt` cũ cũng đo trên bản JSON (`rank_targets.py` chỉ đọc JSON).
- Self-test trước khi rút (C1–C5, C11): tất cả PASS (`checks-pre.txt`).
- Lượt đo đầu, self-test sau rút trượt hai kiểm; dừng, tìm nguyên nhân, sửa phần cài đặt, chạy lại:
  - C7: danh sách loại trừ lấy từ bảng chia của `sampling-plan.md` có 32 mã; 3 mã (S110, S121, S134) không có dòng train
    nào và không có trong corpus vòng 4. Sửa: loại trừ đúng các spec có dòng train cũ (29). `cv.json` lượt đầu
    (`cv-run1.json`) và lượt sau giống hệt nhau ngoài danh sách đó.
  - C9: `targets.json` khác nhau giữa hai lần chạy trong cùng tiến trình. Nguyên nhân: bộ nhớ đệm điểm khoá bằng `id(op)`;
    khi op của spec trước bị thu hồi, `id` được dùng lại cho op của spec sau. Sửa: bộ nhớ đệm giữ tham chiếu op và kiểm
    `is`; mỗi spec target một bộ chấm riêng. `targets.json` lượt đầu (`targets-run1-cachebug.json`) không có trường nào
    khác lượt sau.
  - Chạy lại: C1–C11 đều PASS (`checks-pre.txt`, `checks-post.txt`).
