# Bàn giao: rút lại bộ từ nhận-diện trường, lần 2 (derive v2)

Viết 2026-10-05 để một phiên mới tiếp nhận. Phiên mới đọc file này là đủ ngữ cảnh; không cần hỏi lại phiên cũ.
Mọi con số dưới đây truy được về `RESULTS.md`, `derive_eval.py`, `results.json`, hoặc `RestSecurityBuilder.kt` trong
repo EvoMaster. Phần "ĐỀ XUẤT v2" (§5–§6) **chưa chốt, chưa chạy** — cần user duyệt ba con số ở §6 trước khi code.

Đọc kèm: `CLAUDE.md` §2 (luật làm việc), §6 (hiện trạng từ vựng), `docs/lexicon.md`, `PROTOCOL.md` (protocol lần 1).

## 0. Việc cần làm, một câu

Rút từ corpus đã gán nhãn một bộ từ **nhận diện trường** (trường vai trò, cờ admin, tham số nạn nhân, thứ tự giá trị)
để thay các danh sách đang **viết tay** trong `RestSecurityBuilder.kt`, sao cho bộ rút được **đo tốt trên nửa test chưa
ai nhìn** và **bảo vệ được trước hội đồng**. Lần 1 (2026-10-04) rút ra nhưng không thắng hardcode; nguyên nhân là luật
rút hỏng, không phải corpus bất lực. Lần 2 sửa luật + mở rộng corpus.

**Không phải mục tiêu:** chọn "cái ít tệ hơn" rồi giữ hardcode. Một phân tích trước đó kết luận "giữ hardcode vì nó
thắng" — đó là né mục tiêu: hardcode cũng chỉ là list tự nghĩ (`plan`, `tier` có 0 trường dương trong corpus), ra bảo vệ
không đỡ được. Mục tiêu là một bộ **rút được, có số đỡ lưng**.

## 1. Bộ hardcode đang bị thay (nguồn: RestSecurityBuilder.kt)

Matcher runtime cho nhóm nhận diện: `n == it || n.contains(it)` với `n` = tên lá trường hạ chữ thường
(dòng 960, 1000, 1100, 1258, 1262–1264, 1296, 1304, 1311). Cờ admin khớp bằng `.contains` trên tên gene boolean
(`:963`, `:1197`). B-low/high khớp `.contains` trên giá trị enum (`:711`, `:995`). **Matcher là `contains`, nên một từ
ngắn như `read` dính cả `thread`; mọi từ rút ra phải được vét dưới đúng `contains`.**

| Danh sách | Dòng | Nội dung hiện tại |
|---|---|---|
| `ADMIN_FLAG_FIELD_SIGNALS` | :104 | is_admin, isadmin, is_superuser, is_superadmin, is_staff |
| `transitionUserParamSignals` | :414 | username, userid, user_id, user, account, member, subject, principal, id |
| `userEmailParamSignals` | :415 | email |
| `roleFieldSignals` | :417 | role, plan, permission, level, tier |
| `roleLowPrivSignals` | :418 | view, read, guest, basic, free, member, user, none, restrict, limited |
| `roleHighPrivSignals` | :419 | admin, owner, super, root, manage, write, edit, power, full |

Giá trị thử (`:421`–`:427` quanh đó): numericRoleCandidates 1/0/2, stringRoleCandidates user/viewer/guest/member/basic,
elevatedStringRoleCandidates admin/administrator/owner/superuser. Nhóm chấm điểm transition (`:78`,`:97`,`:99`,`:102`)
đã rút được từ corpus và đo held-out — **không nằm trong phạm vi lần này**.

Quyết 2026-10-04 (CLAUDE.md §6): tạm giữ hardcode kèm lý do corpus; gỡ thật = mở rộng corpus (future work). Lần 2 này
chính là việc "gỡ thật" đó.

## 2. Corpus và nhãn đã có (nguồn: RESULTS.md §2, results.json)

- 2.320 operation ghi, 20.216 trường, 136 nhà cung cấp. Chia: **train 13.714 trường / test 6.502 trường**.
  Nửa test chỉ gồm spec mới, chưa ai nhìn khi chốt luật.
- Nhãn (train / test):
  - A role 40/7, perms 121/10, admin 6/2, active 13/2.
  - C name 33/7, id 111/31, email 11/0.
- `final.csv` = **394 trường DƯƠNG** (A 201 + C 193). **Chỉ chứa dương, không chứa âm** — muốn tính precision phải
  đọc `rows.jsonl` (toàn bộ 20.216 trường, gồm âm). Đây là cái bẫy đã gây một lần tính sai precision ở lần 1.
- Kappa hai lượt gán mù: A 0,774, C 0,803. **Kappa đo model tự nhất quán, KHÔNG đo đúng** — cả hai lượt + phân xử đều
  là model Anthropic, không có lượt người. Đây là điểm yếu hội đồng sẽ đâm (§8).
- Tỉ lệ nền mức trường = **1,17%** (trường role/perms rất hiếm trong tổng số trường).

## 3. Lần 1 rút gì, ra sao (nguồn: RESULTS.md §3, derive_eval.py)

Luật lần 1 (`derive_eval.py`, như `derive3.py` mức operation):
- Ứng viên = token của tên lá dương: tách camelCase + ký tự không chữ-số, hạ chữ thường, bỏ token toàn số và < 4 ký tự.
- Mỗi từ: precision = df_pos/(df_pos+df_neg) đo bằng `contains`; providers = số NCC có trường dương chứa từ.
- Giữ nếu **P1** (providers ≥ 2) **và P2** (precision ≥ 2 × nền) **và P3** (bỏ từ chứa một từ ngắn hơn đã giữ).

Kết quả trên nửa test, hardcode so rút được (P / R / F1):

| Danh sách | Hardcode | Rút được | p (McNemar) |
|---|---|---|---|
| A-role `:417` | 0,353 / 0,706 / **0,471** | 0,045 / 0,765 / 0,085 | < 10⁻⁶ (hardcode thắng) |
| A-admin `:104` | 0 / 0 / 0 | 0,667 / 1,0 / 0,8 | 1,0 (rút từ 1 NCC, vô nghĩa) |
| C `:414`+`:415` | 0,028 / 0,868 / 0,055 | 0,063 / 0,526 / 0,113 | < 10⁻⁶ (cả hai đều rác) |
| B-low `:418` | 1,0 / 1,0 / **1,0** | 1,0 / 0,4 / 0,571 | 0,25 (không ý nghĩa) |
| B-high `:419` | 0,833 / 1,0 / **0,909** | 1,0 / 0,6 / 0,75 | 1,0 (không ý nghĩa) |

Đọc: chỉ A-role và C đủ số để kết luận. A-role hardcode thắng rõ. C thì cả hai đều hỏng (hardcode có `id` → 1.139 bắt
sai, precision 0,028). A-admin/B-low/B-high chênh lệch không qua kiểm định.

Hardcode được corpus ủng hộ tới đâu (train): `role` 23 dương/35, 10 NCC; `permission` 7/12, 4 NCC. Nhưng `plan` 0/15,
`tier` 0/0, `level` 5/16 nhưng chỉ 1 NCC. **19/39 từ hardcode có 0 trường dương trong train.**

## 4. Vì sao lần 1 hỏng (bốn lỗi sửa được)

1. **P2 là no-op.** Ngưỡng precision ≥ 2 × nền = 2 × 1,17% = **2,35%**, gần như không lọc. Nó được bê từ `derive3.py`
   mức operation nơi nền cao hơn nhiều.
2. **Khớp `contains` cho từ ngắn đẻ rác.** `read` ⊂ `thread`; `create` ⊂ `created_at`, `created_by` (có ở mọi spec).
3. **Cắt camelCase đẻ token rác.** `canCreateConfig` → `can`, `create`, `config`. `create` lọt ra từ đây.
4. **Nền 1,17% quá thấp**, precision kiểu gì cũng khó vì dương quá hiếm trong tổng trường.

Ví dụ `create` (minh hoạ lỗi 1+3, nguồn `candidates-A-role.csv`): train precision 0,553 (vì vài NCC đẻ đống
`canCreate*` nhãn perms), 4 NCC → qua cả P1 lẫn P2. Sang test không còn mấy NCC đó, trường chứa `create` còn lại chủ yếu
`created_at` → precision sập về ~0,04. Luật cũ đo precision trên một cục train nên không thấy trước cú sập này.

## 5. ĐỀ XUẤT v2 — phương pháp (chưa chốt, chưa chạy)

Ý tưởng trung tâm: **một từ chỉ tốt nếu nó tổng quát hoá sang nhà cung cấp chưa gặp.** Kiểm việc đó bằng chia fold theo
NCC ngay trong train, test vẫn nguyên.

Năm luật mới thay P1/P2/P3:

1. **Ứng viên = nguyên tên lá**, cộng token chỉ khi token đó xuất hiện như một tên lá nguyên ở ≥ 2 NCC (không carve
   `role` ra từ `authorrole`). Bỏ cắt camelCase thành mảnh vô nghĩa.
2. **Sàn precision tuyệt đối** τ thay cho "2 × nền". Giữ từ khi precision ≥ τ, đo **đúng bằng matcher runtime
   `contains`** trên train (đề xuất τ = 0,5).
3. **Stop-list khai báo trước**: loại tiên nghiệm các token CRUD và timestamp (`create delete update read list get add
   remove default group name id at by time date`) vì chúng tả thao tác, không tả quyền của chủ thể. Lý do khai trong
   protocol để bảo vệ được.
4. **Lọc tập ứng viên trước khi rút**: chỉ xét trường trong operation có đụng chủ thể (operation đó có ≥ 1 trường C).
   Nền nhảy từ 1,17% lên hai chữ số → precision có cửa.
5. **Fold theo NCC (lõi):** giữ một từ chỉ khi precision ≥ τ ở ≥ 80% fold khi lần lượt **giấu từng nhóm NCC**. `create`
   dựa vào 4 ông canCreate — giấu họ đi là precision rơi → loại. `role` rải khắp → fold nào cũng sống → giữ.

Đòn bẩy mạnh hơn, **ngoài phạm vi đã chốt**: đổi matcher runtime từ `contains` sang khớp nguyên tên lá (`read` thôi
dính `thread`). Đó là sửa code EvoMaster → phải qua cổng hồi quy + đo lại mọi target. Nếu phiên mới muốn làm, hỏi user
trước; mặc định giữ `contains` và vét từ dưới `contains`.

Mở rộng corpus:
- Hiện nửa test nhãn A chỉ từ **5 NCC** — mỏng tới mức một NCC lung lay cả bảng §3. Cần dày hơn.
- Thêm NCC mới (S424 trở đi) đúng quy trình bốc có seed + đóng băng như `PROTOCOL.md` §1, chia 50/50, **nửa test không
  ai nhìn tới lúc đo**.
- Bốc hai rổ khai báo riêng: một rổ **ngẫu nhiên** (giữ nền thật để precision trung thực) + một rổ **làm giàu** theo
  spec có dấu hiệu authz (để test phủ đủ biến thể từ). Số từ mỗi rổ khai trong protocol.

## 6. Ba con số user phải chốt trước khi code

1. **τ (sàn precision)** = 0,5 (đề xuất). Ngặt hơn 0,6 ít dương giả nhưng mất recall; lỏng hơn 0,4 ngược lại.
2. **Số NCC thêm** = 120 (train 60 / test 60) (đề xuất).
3. **Stop-list §5.3** — duyệt danh sách từ CRUD/timestamp; thêm/bớt từ nào.

Chốt xong → viết `PROTOCOL-v2.md` đóng băng (luật + ngưỡng + cỡ mẫu, **không ghi kết quả mong đợi**) → bốc spec → gán
nhãn phần mới → viết lại `derive` → đo một lần trên test mới.

## 7. Luật bắt buộc theo (CLAUDE.md)

- Đóng băng protocol **trước** khi nhìn nửa test. Không sửa luật sau khi thấy kết quả test; muốn sửa thì phải chốt lại
  trên một nửa test mới. (Lỗi này đã xảy ra ngầm ở lần 1 vì P2 lấy từ derive3.)
- Không bao giờ ghi kết quả mong đợi vào harness/protocol/doc trước lượt chạy.
- **Không sửa code EvoMaster** nếu không được user duyệt; sửa xong phải qua cổng hồi quy (`regression-gate`) và đo lại
  các arm bị ảnh hưởng. Thay nhóm nhận diện trong `RestSecurityBuilder.kt` **có** làm xê dịch số ở CLAUDE.md §4, nên
  phải diễn tập rollback và đo lại ba target.
- Mã thêm vào **không comment**. Self-test cho mỗi thay đổi code đặt trong `infra/evomaster-ext/selftest/`, không nằm
  trong cây EvoMaster.
- Một chênh lệch ghép đôi chỉ thành phát hiện khi có kiểm định + p-value (đã có `mcnemar.py`).
- Mỗi con số nêu jar của nó; jar hiện tại = `evomaster-AF2-6b5606d4.jar` (commit `8d6cf8431f`).

## 8. Điểm yếu hội đồng sẽ đâm (phải viết thành hạn chế)

- **Nhãn toàn model, không có lượt người.** Kappa chỉ đo model tự nhất quán. Nếu không thêm một lát người gán, phải nói
  thẳng đây là hạn chế. (User lần này chọn chưa làm người gán.)
- Nửa test mỏng (A từ 5 NCC, admin từ 1 NCC) — mọi số §3 dao động mạnh nếu thêm/bớt một NCC.
- Chunk 028, 031 chỉ đọc qua grep; 39 operation bị cắt sau 80 trường (PROTOCOL §9) — một số trường dương có thể sót ở
  cả hai lượt.
- Dù v2 có thể vẫn không thắng hardcode. Nếu vậy, câu chuyện bảo vệ được là: "đã rút theo protocol đăng ký trước, đo
  held-out, đây là F1 đạt được, đây là lý do dương hiếm + nhãn mỏng chặn trần" — một kết quả âm có kỷ luật, không phải
  "giữ list tự nghĩ".

## 9. Bản đồ file (thư mục này)

| File | Nội dung |
|---|---|
| `PROTOCOL.md` | Protocol lần 1, lệch luật §9 |
| `RESULTS.md` | Kết quả lần 1 (nguồn mọi con số §2–§4 trên) |
| `rows.jsonl` | 20.216 trường vào (gồm âm) — dùng cái này để tính precision |
| `final.csv` | 394 trường dương (A+C) — KHÔNG có âm |
| `derive_eval.py` | Luật rút lần 1 (sửa file này hoặc viết `derive_v2.py`) |
| `lists/candidates-*.csv` | Mọi ứng viên kèm điểm, df_pos, df_neg, providers, p1, p2 |
| `lists/list-*.txt` | Từ rút được lần 1 |
| `results.json` | counts, lists, values, victim, hard_word_support_train |
| `mcnemar.py`, `mcnemar.json` | Kiểm định ghép đôi |
| `L1/`, `L2/`, `adjudication.csv` | Nhãn gốc hai lượt + phân xử |
| `../../corpus/sample_specs_field.py`, `sample-field*.json` | Bốc và tải spec |
