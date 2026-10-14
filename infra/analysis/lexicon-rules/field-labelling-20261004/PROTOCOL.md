# Gán nhãn mức trường — protocol

Chốt 2026-10-04 khoảng 23:02 +0700, trước khi bốc spec mới (`sample-field.json` mtime 23:03:11) và trước khi gán dòng nào.
Mọi thay đổi sau giờ này ghi ở §9 kèm giờ.

Mục tiêu: rút từ corpus các danh sách đang viết tay trong `RestSecurityBuilder.kt` (`:104`, `:414`, `:415`,
`:417`, `:418`, `:419`, `:421`–`:427`, `:1154`–`:1160`), đo trên nửa test chưa ai nhìn, so với danh sách viết tay.
Không sửa mã EvoMaster.

## 1. Corpus

| Phần | Nguồn | Dòng | Nửa |
|---|---|---|---|
| Cũ | 44 spec S100–S137, S200–S214; đúng các operation đã gán ở `labelling-r2/`, `labelling-r3/` (S131 dùng bản `.v2`) | 785 | train |
| Mới | 100 nhà cung cấp chưa dùng của `apis-guru-list.json` (sha256 `dfac835d…`), S300–S399 | trần 36 operation ghi một spec | 50/50 |

Bốc spec mới (`../../corpus/sample_specs_field.py`):
- Một API một nhà cung cấp, chọn bằng seed `20260918` như các lần trước.
- Loại: 53 nhà cung cấp đã dùng; mọi khoá chứa `airflow`, `vampi`, `pyload`, `reports-api`, `grafana`, `mattermost`,
  `vikunja`, `callcenter`, `truthy`, `bamf`, `artifact-keeper` (target đã hoặc sẽ chạy).
- 50 từ tầng giàu (96 nhà cung cấp còn lại), 50 từ tầng ngẫu nhiên; seed `20261004`.
- Spec không tải được hoặc không có operation ghi: thay một vòng từ cùng tầng, seed `20261005`. Thay vào vẫn hỏng
  thì bỏ, không thay tiếp.
- Chia: trong từng tầng, xáo bằng seed `20261004`, nửa đầu train, nửa sau test.
- Trần: spec nhiều hơn 36 operation ghi thì bốc 36, seed `20261004 + số spec`.

Nửa test chỉ gồm spec mới. Không ai nhìn dòng của nửa test trước khi gán nhãn; luật rút từ (§5) và cách đo (§6)
chốt trong file này.

## 2. Dòng dữ liệu vào

Một dòng = một operation ghi (POST, PUT, PATCH, DELETE). Người gán thấy: method, path, `summary`, `description`
(400 ký tự đầu), và danh sách trường. Mỗi trường: vị trí (`path`, `query`, `body`), tên (trường lồng ghi `a.b`,
phần tử mảng ghi `a[].b`, sâu tối đa 3 tầng), kiểu, `enum` (12 giá trị đầu).

Không thấy: tham số `header`, `cookie`; response; tags; operationId; security; mô tả từng trường; tên nhà cung
cấp; nửa train/test; nhãn của lượt kia; nhãn R/N cũ.

## 3. Ba nhãn

**A — trường mang quyền.** Trường mà giá trị client gửi trong thao tác này quyết định quyền của một chủ thể
(user, member, account, principal, service account, client, API key, token).

| Mã | Khi nào | Ví dụ |
|---|---|---|
| `role` | đặt một vai trò hoặc mức quyền, một giá trị | `role ∈ [ADMIN, VIEWER]`, `permission_level`, `access_level: integer` |
| `perms` | đặt một danh sách vai trò, quyền, scope | `roles[]`, `scopes`, `permissions.push` |
| `admin` | boolean trao quyền quản trị | `is_admin`, `site_admin`, `superuser` |
| `active` | đặt trạng thái hoạt động của chủ thể | `active`, `enabled`, `suspended`, `status ∈ [active, disabled]` |

Không phải A: trường của tài nguyên nghiệp vụ (`public` của một repo, `visibility` của một file); trường mô tả role
(`description`, `name` của role khi tạo role); trường tạo credential mới.

**B — thứ tự giá trị.** Chỉ cho trường A `role` hoặc `perms` có `enum`. Ghi giá trị quyền thấp nhất và cao nhất
theo nghĩa của chữ. Không xếp được thì `unordered`. Chỉ chọn giá trị có trong `enum`.

**C — chỉ chủ thể bị tác động.** Trường mà giá trị là danh tính của một chủ thể đã tồn tại mà thao tác này tác
động lên.

| Mã | Ví dụ |
|---|---|
| `name` | `{username}`, `login`, `member_name` |
| `id` | `{userId}`, `account_id`, `{id}` trong `/users/{id}` |
| `email` | `{email}`, `user_email` |

Không phải C: id của tài nguyên không phải chủ thể (`{repoId}`, `{orgId}`, `{projectId}`); trường của chủ thể đang
được tạo mới (`POST /users` body `username`).

Một trường có thể vừa không A vừa không C (đa số). Một trường không thể vừa A vừa C.

## 4. Lượt gán

| Lượt | Ai | Ghi vào |
|---|---|---|
| L1 | Claude Opus 5.5, phiên chính | `L1/` |
| L2 | một agent model Sonnet, mù với L1 | `L2/` |
| Phân xử | Claude Opus 5.5, phiên chính, sau khi cả hai lượt xong | `adjudication.csv` |

Cả hai lượt cùng nhà cung cấp model (Anthropic): kappa đo độ nhất quán trong một nhà cung cấp. Không có lượt người
(quyết định của user, 2026-10-04). Phân xử do model làm theo yêu cầu của user: xem lại dòng lệch, chọn mã hợp
nhất theo §3, ghi lý do. Nhãn gốc L1, L2 giữ nguyên; kappa tính trên nhãn gốc.

Định dạng đầu ra, một dòng một trường có nhãn, trường không có dòng = không A, không C:
`row_id,field,A,B_low,B_high,C`. Mỗi lượt ghi theo khối; khối đã xong ghi vào `done.txt` của lượt đó, để kiểm
không sót khối.

## 5. Rút từ

Train = 44 spec cũ + nửa train mới. Tài liệu của một trường = tên lá (phần sau dấu `.` cuối, bỏ `[]`) hạ chữ thường,
đúng chuỗi mà builder so (`g.name.lowercase()`). Tài liệu của một giá trị = giá trị `enum` hạ chữ thường.

| Danh sách | Dương | Âm | So với |
|---|---|---|---|
| `A-role` | trường A ∈ {`role`, `perms`} | mọi trường khác | `:417` |
| `A-admin` | trường A = `admin` | mọi trường boolean khác | `:104` |
| `A-active` | trường A = `active` | mọi trường khác | (builder không có) |
| `C` | trường C ≠ rỗng | mọi trường khác | `:414`, `:415` |
| `B-low` | giá trị B_low | giá trị khác cùng `enum` | `:418` |
| `B-high` | giá trị B_high | giá trị khác cùng `enum` | `:419` |

Luật như `derive3.py`: ứng viên = token của tài liệu dương (cắt theo ký tự không phải chữ-số, tách camelCase, hạ
chữ thường, bỏ token toàn số và ngắn hơn 4 ký tự). Khớp bằng chuỗi con, như runtime. Điểm
`(df+ + 1)/(df+ + df- + 2) × ncc/(ncc+1)`. Giữ từ qua P1 (ít nhất 2 nhà cung cấp) và P2 (precision ≥ 2 × tỉ lệ
dương nền); P3 bỏ từ chứa một từ ngắn hơn đã giữ.

Rút xong không thêm, không bớt từ nào bằng tay.

## 6. Đo trên nửa test

Bộ phân loại của một danh sách: trường dương khi tên lá chứa một từ trong danh sách (`n == w || n.contains(w)`);
`B-low` theo `:711` (chứa từ thấp và không chứa từ cao). Báo precision, recall, F1 cho danh sách viết tay và danh
sách rút được, cạnh nhau, trên nửa test; trên train chỉ báo thêm.

Danh sách giá trị thử (`:421`–`:427`): báo tỉ lệ trường `role` có `enum` ở nửa test mà danh sách chứa đúng giá trị
B_low (hoặc B_high). Danh sách trường response (`:1154`–`:1160`) khớp object trong response, không có nhãn tương ứng:
báo độ phủ so với trường C trong body, ghi rõ là xấp xỉ.

## 7. Luật dừng sớm

- Sau 10 spec mới đầu tiên có cả L1, L2: kappa nhị phân A (có/không) mức trường dưới 0,6 thì dừng gán, sửa §3,
  ghi lệch luật, gán lại 10 spec đó.
- Một danh sách có 0 từ qua P1 trên train: không rút danh sách đó, báo "corpus không đủ".

## 8. Đầu ra

`rows/` (khối dữ liệu vào), `L1/`, `L2/`, `adjudication.csv`, `final.csv`, `lists/`, `RESULTS.md`.

## 9. Thay đổi sau khi chốt

2026-10-04 23:06 (`rows.jsonl` mtime), sau khi trích, trước khi gán dòng nào (`build_rows.py`):

- Trích trường: `allOf`/`oneOf`/`anyOf` gộp hợp các `properties`; tham số `formData` tính là `body`; mỗi operation
  giữ tối đa 80 trường theo thứ tự path, query, body (39 operation bị cắt, số trường bị cắt ghi trong dòng).
- 24 spec mới có 0 operation ghi; thay bằng `sample-field-reserve.json` (seed `20261005`), mã S400–S423, giữ tầng và
  nửa của spec bị thay. 6 spec thay vào vẫn rỗng, bỏ. Còn 94 spec mới: train 47 spec 846 dòng, test 47 spec 714 dòng.
- Phần cũ: 760 operation có nhãn trong `labelling-r2/final.csv` và `labelling-r3/final.v2.csv` (không phải 785).
- Tổng 2.320 operation, 20.216 trường, 31 khối trong `rows/`.

2026-10-04 khoảng 23:14, kiểm luật dừng §7 bằng `kappa.py 011,012,013,014` (chỉ in số tổng; L1 chưa xem nhãn L2 nào):
2.086 trường, kappa A nhị phân 0,940 (L1 26 dương, L2 25 dương). Không dừng.

Trường tên `(body)` (thân không có `properties`) không có tên để rút từ; loại khỏi §5, vẫn tính trong kappa.

2026-10-04 khoảng 23:21, sau khi gán xong, ghi lại lệch luật:

- Sửa mốc giờ: bản trước của mục này ghi "23:10", "23:40" và "2026-10-05"; các mốc đó không lấy từ đồng hồ. Mốc hiện tại lấy từ mtime file.

- Đọc không trọn: cả L1 và L2 đọc chunk 028 (Kubernetes S400, Bitbucket S404) và 031 (S420, S423) qua danh sách
  operation rồi lọc bằng grep, không đọc hết từng dòng trường. Trường dương nằm trong phần không đọc sẽ bị bỏ sót ở
  cả hai lượt.
- Quy ước riêng của L1 khác chữ của §3: trong lúc gán, L1 chỉ gán C cho chủ thể kiểu người dùng (user, member,
  account), không gán cho client, API key, token. §3 liệt kê cả ba là chủ thể. Phân xử theo chữ của §3 (21 trường,
  mã `subject-key` trong `adjudication.csv`).
- Phân xử do chính phiên L1 làm (yêu cầu của user). Kết quả nghiêng về L1: 108 theo L1, 51 theo L2, 2 khác cả hai.
- `B-low`, `B-high`: tài liệu là giá trị `enum` hạ chữ thường của trường A `role`/`perms` có B_low khác rỗng và khác
  `unordered`.
- Thêm `mcnemar.py` (kiểm định ghép đôi chính xác trên nửa test, đơn vị là tài liệu của từng danh sách); không có
  trong §6 lúc chốt, thêm theo luật dự án "chênh lệch ghép đôi cần kiểm định".
