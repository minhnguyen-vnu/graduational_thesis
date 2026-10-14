# Vì sao ba danh sách nhận-diện trường vẫn viết tay — 2026-10-04

Quyết định "không đổi mã" ở đây đã được thay ngày 2026-10-06: `field-identification-direction-20261006.md`.

Ghi lại nền móng dưới điểm yếu "bộ từ vựng tự chọn" (`CLAUDE.md` §6) trước khi quyết có đổi mã hay không.

**Kết luận.** Nhóm từ vựng CHẤM ĐIỂM transition (98 từ path+param) đã rút từ corpus và đo trên nửa held-out; jar
`AF2` còn gấp tên trường thân vào chuỗi chấm điểm (biến thể V1). Nhóm từ vựng NHẬN DIỆN trường (19 từ, viết tay ở
`RestSecurityBuilder.kt:104/:414/:417`) không rút được từ corpus hiện có vì ba lý do độc lập (mục 3). Không đổi mã;
19 từ ở lại viết tay kèm lý do corpus. Gỡ thật cần mở rộng corpus (mục 5).

## 1. Hai nhóm từ vựng trong builder

| Nhóm | Danh sách | Dòng | Nguồn | Dùng để |
|---|---|---|---|---|
| Chấm điểm | `TRANSITION_PATH_LEXICON` (53), `TRANSITION_USER_PARAM_LEXICON` (45) | `:97`, `:99` | CSV rút từ corpus | `transitionPathScore :102`; xếp hạng ứng viên transition |
| Nhận diện | `ADMIN_FLAG_FIELD_SIGNALS` (5) | `:104` | viết tay | nhận cờ admin boolean, đặt giá trị |
| Nhận diện | `transitionUserParamSignals` (9) | `:414` | viết tay | nhận tham số chỉ nạn nhân khi đặt giá trị |
| Nhận diện | `roleFieldSignals` (5: role, plan, permission, level, tier) | `:417` | viết tay | nhận trường mang quyền, đặt giá trị quyền thấp |

Chuỗi chấm điểm `transitionHay(a) :120` = `path + " " + name + " " + bodyFieldNames` → đã gấp tên trường thân vào
(biến thể V1 của `field-gate-20260923/`). `transitionScore :108` = `max(transitionPathScore(hay), cờ-admin 0.6)`.
Dùng thật ở `:139` (`looksLikePermissionReducingTransition`), `:525` (chẩn đoán), `:948`/`:950` (lọc + sắp ứng
viên). Committed `a5f3ff0ba5`, cây làm việc sạch trên file này.

## 2. Nhóm chấm điểm: rút từ corpus + đo held-out (A, B đã khoá)

Tái lập `derive3.py` vào thư mục scratch (không ghi đè file đã ghi nhận): candidates-1/2/3, list-3,
`stateful-authz-lexicon.csv` **trùng khít** bản trong `lexicon-20260921-audited/`.
- Train: `36 dòng R, 441 dòng N, 29 nhà cung cấp, 10 nhà cung cấp có R`.
- CSV: 53 path, 45 param (mọi ứng viên kèm điểm; `derive3.py:126` chỉ ghi list 1,2 vào CSV).

Tái lập `rank_field.py` (chỉ đọc), khớp `field-gate-20260923/RESULTS.md`:

| Biến thể | test top-1 | top-3 | top-8 |
|---|---|---|---|
| V0 (path-only) | 0.500 | 0.667 | 1.000 |
| **V1 (path+tên trường, đang ở `AF2`)** | **0.667** | **0.833** | **1.000** |
| V2 (bộ field riêng) | 0.333 | 0.500 | 0.833 |

## 3. Nhóm nhận diện: ba lý do không rút được từ corpus

**(a) Token cờ-admin vắng mặt trong corpus.** `candidates-3.csv` liệt kê 135 token rút từ `body_field_names` của
36 endpoint `R` train. Token admin-ish duy nhất là `admin` (`df_r=1, df_n=1, nha_cung_cap=1, diem=0.2500, p1=0`) —
rớt cổng provider≥2. `is_admin`/`isadmin`/`is_superuser`/`is_superadmin`/`is_staff`/`superuser`/`superadmin` không
xuất hiện (grep rỗng trên `../corpus/ops-full/` + `ops-ext/`). Nối `:104` vào danh sách rút được sẽ mất nhận diện
`is_admin` → artifact-keeper (`PATCH /api/v1/users/{id}` cờ `is_admin`) thành FN.

**(b) Danh sách trường rút được quá chung để nhận diện.** list-3 (23 từ) = `access allowed client default description
direct enabled flow grant group logo members permission product public required role scope secret setting updates
uris view`. Chỉ `role`, `permission` trùng danh sách viết tay; `plan`, `level`, `tier` không có trong corpus. Ablation
V2 (`field-gate-20260923/RESULTS.md` §4) đã chứng minh dùng bộ trường này để chấm điểm làm tụt hạng: test top-1
0.667 → 0.333, spec S116 từ hạng 1 xuống 24–27, do `description`/`enabled`/`public` kéo endpoint không liên quan lên.

**(c) Không có nhãn mức trường.** Corpus gán nhãn `R`/`N` mức thao tác, không có nhãn "trường nào mang quyền" hay thứ
tự giữa các giá trị quyền (`docs/lexicon.md` §9). Không có cách đo độ chính xác của bước nhận diện trường trên
held-out.

## 4. Phát hiện phụ cần quyết: số held-out trích là V0, jar chạy V1

`CLAUDE.md` §6 và `docs/lexicon.md` §7 trích `top-1 0,500 / top-3 0,667 / top-8 1,000` — đó là **V0** (path-only).
Jar `AF2` chấm điểm bằng haystack có tên trường = **V1** (`0,667 / 0,833 / 1,000`). Hai lựa chọn, cần user quyết vì
đổi một số headline: (1) trích V1 cho khớp bộ chấm điểm đã ship; hoặc (2) giữ V0 và ghi rõ §7 đo "chất lượng danh
sách path" tách khỏi việc gấp tên trường ở builder.

## 5. Kết luận cho luận văn

- Lời chê "56 từ tự chọn, chỉ thử trên target của ta": đã trả lời cho **nhóm chấm điểm** (98 từ path+param rút từ
  corpus, đo held-out; gấp tên trường V1 đang chạy).
- **19 từ nhận diện** (`:104` 5 + `:414` 9 + `:417` 5) ở lại viết tay, có lý do corpus (vắng mặt + V2 tụt + thiếu
  nhãn mức trường), không phải tuỳ tiện.
- Gỡ thật cần mở rộng corpus: nhãn mức trường + spec thật có cờ admin boolean, rồi rút lại và đo. Rủi ro hạn cuối
  tháng 11, lợi ích nhỏ (xem đánh giá L3). Ghi là future work.

## 6. Chạy tay / truy nguồn

```
# A — tái lập derivation vào scratch, diff với bản ghi nhận
sed "s#OUT = 'lexicon-20260921-audited/'#OUT = '<scratch>/'#" derive3.py > derive3_verify.py
python3 derive3_verify.py            # (cwd = lexicon-rules)
diff candidates-3.csv list-3.txt stateful-authz-lexicon.csv  -> IDENTICAL

# B — tái lập ranking held-out (chỉ đọc)
python3 rank_field.py                # V0/V1/V2 train+test, khớp field-gate-20260923

# (a) token cờ-admin
grep -iE 'admin|superuser|staff|super|is_' lexicon-20260921-audited/candidates-3.csv   -> chỉ "admin",1,1,1
grep -riE 'is_admin|isadmin|superuser|is_staff|superadmin' ../corpus/ops-full ../corpus/ops-ext  -> rỗng
```

Builder: `core/src/main/kotlin/org/evomaster/core/problem/rest/service/RestSecurityBuilder.kt`
`:97 :99 :102 :104 :108 :120 :139 :414 :417`, commit `a5f3ff0ba5`.
