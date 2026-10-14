# Gán nhãn mức trường, vòng 2 — protocol

Chốt 2026-10-04, trước khi bốc spec mới của vòng này và trước khi gán dòng nào của vòng này. Mốc giờ lấy từ mtime file;
thay đổi sau khi chốt ghi ở §9.

Lý do có vòng 2 (`../field-labelling-20261004/RESULTS.md` §1, §6): nửa test vòng 1 nhỏ (5 nhà cung cấp có trường
quyền), và luật lọc P2 của vòng 1 cho qua từ chung. Đổi luật sau khi đã thấy nửa test vòng 1 là chỉnh theo kết quả,
nên vòng 2 dùng nửa test vòng 1 làm tập dev và bốc một nửa test mới chưa ai nhìn.

## 1. Ba tập

| Tập | Nguồn | Dùng để |
|---|---|---|
| train | nửa train vòng 1: 90 nhà cung cấp, `../field-labelling-20261004/final.csv` | rút danh sách ứng viên |
| dev | nửa test vòng 1: 46 nhà cung cấp | chọn luật lọc (§5) |
| test | 100 nhà cung cấp mới (§2) | đo cuối |

Nhãn train, dev giữ nguyên như vòng 1, không gán lại.

## 2. Bốc spec test

`../../corpus/sample_specs_field_r2.py`:
- Loại mọi nhà cung cấp đã dùng (177) và cùng danh sách target như vòng 1.
- Lấy cả 37 nhà cung cấp còn lại của tầng giàu và 63 nhà cung cấp tầng ngẫu nhiên, seed `20261006`. Một API một nhà
  cung cấp, chọn bằng seed `20260918` như các lần trước.
- Spec không tải được hoặc có 0 operation ghi: thay một vòng từ tầng ngẫu nhiên, seed `20261007`. Thay vào vẫn hỏng
  thì bỏ.
- Mã S500–S599, thay thế S600 trở đi. Trần 36 operation ghi một spec, seed `20261006 + số spec`.
- Trích trường như vòng 1 (`extract_fields.py`, tối đa 80 trường một operation).

## 3. Luật gán nhãn

Giữ nguyên `../field-labelling-20261004/PROTOCOL.md` §2, §3. Thêm các điểm sau, rút từ các trường đã phân xử ở vòng 1
(`adjudication.csv`) và chốt trước khi nhìn dòng nào của vòng 2:

- Chủ thể gồm user, member, account, principal, service account, client, API key, token. C gán cho mọi chủ thể đó.
- Tạo credential mới (token, API key, client, app): các trường của nó không phải A.
- Trường định nghĩa quyền của một role hoặc nhóm quyền (cả khi tạo, cả khi sửa) là A.
- Khi một trường mảng chứa quyền và trường con cũng chứa quyền, gán cả hai.
- Không phải C: người được mời (chưa tồn tại); tham số đăng nhập, xác thực; thao tác chỉ đọc qua POST; tài nguyên thuộc
  về người dùng (thiết bị, ghi chú, lịch); thanh toán, chuyển khoản.
- Là C: chủ thể được thêm vào hoặc bỏ khỏi một quan hệ (member, collaborator, follower, subscriber, reviewer, tester),
  chủ thể bị khoá, xoá, đổi mật khẩu, đổi khoá.
- Đọc hết mọi dòng của mọi khối; khối dài thì đọc theo đoạn (offset/limit), không lọc bằng grep.

## 4. Lượt gán

Như vòng 1: L1 là phiên chính (Claude Opus 5.5), L2 là một agent model Sonnet, mù với L1. Phân xử do phiên chính làm,
ghi mã chọn và lý do; kappa tính trên nhãn gốc.

## 5. Chọn luật lọc trên dev

Ứng viên từ và điểm tính như vòng 1 (`derive_eval.py`). Năm luật lọc, khai trước:

| Mã | Giữ từ khi |
|---|---|
| R0 | ≥ 2 nhà cung cấp và precision ≥ 2 × tỉ lệ nền (luật vòng 1) |
| R1 | ≥ 2 nhà cung cấp và precision ≥ 0,3 |
| R2 | ≥ 2 nhà cung cấp và precision ≥ 0,5 |
| R3 | ≥ 2 nhà cung cấp và điểm ≥ 0,3 |
| R4 | ≥ 2 nhà cung cấp, 5 từ điểm cao nhất |

Mọi luật đều bỏ từ chứa một từ ngắn hơn đã giữ (P3). Danh sách rút trên train, đo F1 trên dev cho năm danh sách A-role,
A-admin, C, B-low, B-high. Chọn luật có trung bình F1 cao nhất; hoà thì chọn luật có ngưỡng precision cao hơn
(thứ tự R2 > R3 > R1 > R4 > R0).

Danh sách cuối: rút trên train + dev bằng luật đã chọn.

## 6. Đo trên test

Cho mỗi danh sách: danh sách viết tay và danh sách cuối, precision, recall, F1, McNemar chính xác hai phía. Báo thêm
danh sách R0 trên test, và danh sách viết tay C bỏ `id`.

Neo trên target (không phải held-out: các target này đã định hình danh sách viết tay). Ground truth lấy từ nguồn:

| Target | Trường A | Loại | Trường C | B thấp / cao | Nguồn |
|---|---|---|---|---|---|
| reports-api | `role` | role | `username` | VIEWER / ADMIN | `infra/reports-api/.../RoleUpdateRequest.java:7` |
| vampi-seeded | `role` | role | `username` | user / admin | `infra/vampi-seeded/openapi_specs/openapi3.yml:609` |
| pyLoad | `permission`, `role` | role | `user` | | `infra/pyload-cve/openapi-merged.json` `/api/set_user_permission` |
| artifact-keeper | `is_admin` | admin | `id` | | `CLAUDE.md` §6 |
| Airflow | `roles` | perms | `username` | | `docs/lexicon.md` §5 |
| bamf | | | `email` | | `CLAUDE.md` §6 |

Báo: danh sách nào nhận đúng từng tên trường.

## 7. Luật dừng sớm

- Sau khối đầu tiên chứa ít nhất 10 spec mới có cả L1, L2: kappa A nhị phân dưới 0,6 thì dừng, ghi lệch luật, sửa §3.

## 8. Đầu ra

`rows/`, `L1/`, `L2/`, `kappa-raw.json`, `adjudication.csv`, `final.csv`, `select.json`, `lists/`, `results.json`,
`mcnemar.json`, `anchor.json`, `RESULTS.md`.

## 9. Thay đổi sau khi chốt

Sau khi bốc và trích, trước khi gán dòng nào (`build_rows.py`, `sample-print.txt`):

- Tầng giàu cho 36 nhà cung cấp: chọn một API cho mỗi nhà cung cấp bằng seed `20260918` làm 1 nhà cung cấp rơi sang
  tầng ngẫu nhiên. Tổng 99 spec S500–S598.
- 29 spec có 0 operation ghi; thay từ dự phòng (S600–S628). 7 spec thay vào vẫn rỗng, bỏ. Còn 92 spec, 1.652
  operation, 10.221 trường, 22 khối; 11 operation bị cắt sau 80 trường.

Chọn luật §5 (`select_rule.py`, `select.json`), chạy trên train và dev của vòng 1, trước khi gán dòng nào của vòng 2:
trung bình F1 trên dev R0 0,464, R1 0,473, R2 0,286, R3 0,339, R4 0,503. Chọn R4.

Luật dừng §7 (`kappa.py 001,002,003,004,005`, 13 spec, 1.485 trường; chỉ in số tổng): kappa A nhị phân 0,704, không dừng.

Lộ mù §4: L2 xong trước L1. Báo cáo bàn giao của L2 nêu nhãn cụ thể trên S608, S615, S617, S624, S626, và phiên chính
đọc nó khi L1 đã gán xong 001–019, chưa ghi 020. L1 khối 020 ghi theo nhãn đã chốt trước tin nhắn; khối 021, 022 gán
sau khi đọc. `kappa-raw.json` báo tách 001–019 (mù) và 020–022 (đã lộ).

Đo §6: `evaluate.py` gộp `derive_eval.py` và `mcnemar.py` của vòng 1, cùng hàm; McNemar tính bằng phân số chính xác vì
n lớn làm tràn số thực. Báo thêm, ngoài §8 và sau khi thấy kết quả test: `exploratory.json` (R0–R4 trên test, McNemar
tách trường dương và âm), `merged-lists.json` (R4 trên cả ba tập, không có tập đo).

Phân xử §3: 3 trường yêu cầu đặt lại mật khẩu (luật `reset-target`) chọn C theo L2, để nhất quán với S505-0008 và
S606-0001 mà cả hai lượt cùng gán C; lúc gán, L1 xếp loại trường này vào tham số xác thực.
