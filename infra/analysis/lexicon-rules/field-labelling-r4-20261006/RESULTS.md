# Gán nhãn mức operation, vòng 4 — kết quả

2026-10-07. Protocol `PROTOCOL.md` (chốt 2026-10-06 khoảng 23:35, lệch luật ở §9 của nó và ở §8 dưới đây). Không sửa mã
EvoMaster. Mọi số từ `kappa.json`, `aggregate.json`, `adjudication.csv`, `final-all.csv`, `cv.json`, `extra-tests.json`,
`lists/`. Lexicon transition đọc từ cây làm việc EvoMaster, sha256 ghi trong `cv.json`.

## 1. Kết luận

- Luật rút khai trước, chạy trên 10.381 op ghi của 230 API, cho ra: cờ admin `admin`; vai trò `permission, role`; nạn
  nhân `member, user` cộng tầng `id`; `email` không qua luật; mức thấp `read`; mức cao `admin`. B (thấp/cao) qua ngưỡng
  lần đầu: 18 enum có thứ tự từ 11 nhà cung cấp, ngưỡng 15/10.
- Thuật ngữ SCIM/NIST không thêm từ nào: ba nguồn ứng viên (corpus + SCIM/NIST, corpus + từ viết tay, chỉ corpus) cho
  ra đúng một bộ.
- Kiểm chéo, lần lặp 1: danh sách rút ngang bộ viết tay ở M1, M2, M4. Nó kém hơn ở M3 (nạn nhân, 107 so với 117 trên
  184 op, McNemar p = 0,013, nhưng KTC bootstrap theo nhà cung cấp −0,141 … +0,005 chứa 0) và ở M5 (op không đổi quyền
  được chấm điểm admin, 165 so với 4 trên 10.182 op, p < 0,001).
- Mức thấp `read` làm hỏng lựa chọn giá trị hạ quyền: trên toàn bộ dữ liệu, giá trị đứng đầu đúng ở 11/18 op so với
  15/18 của bộ viết tay. Bốn op mất đều có mức thấp nhất là `viewer`, `user` hoặc `member`, và danh sách rút đẩy
  `manager` hoặc `admin` lên đầu (§5). Kiểm chéo không thấy điều này vì ở 3–4 trên 5 phần, B không đủ dữ liệu và rơi về
  danh sách viết tay.
- Neo trên target: danh sách rút nhận 5/6 target, mất `email` (bamf). Bộ viết tay 6/6. Danh sách vòng 3: 4/6.

## 2. Nhãn

| | Số |
|---|---|
| Op mới / API / khối | 6.409 / 74 / 86 |
| Op T = 1: LA (Sonnet 5.5) / LB (Opus 5.5) / LM (phiên chính) / cuối | 109 / 79 / 108 / 98 |
| Fleiss kappa trên T, ba lượt, 6.409 op | 0,815 |
| Cohen LA–LB / LA–LM / LB–LM | 0,817 / 0,845 / 0,778 |
| Ba lượt cùng T = 0 / cùng T = 1 / hai trên ba T = 1 / một trên ba T = 1 | 6.283 / 72 / 26 / 28 |
| Op phải phân xử | 3, cả 3 chọn X |
| API quay về tập op vòng 3 (luật hạn chót §7) | 0 |
| Tổng corpus đo: op / op T = 1 / nhà cung cấp có op T = 1 | 10.381 / 199 / 56 |

Vòng 3 có 101 op T = 1 từ 45 nhà cung cấp. Nguồn: `kappa.json`, `aggregate.json`, `adjudication-items.md`,
`adjudication.csv` (lý do từng dòng), `final-r4.csv`, `final-all.csv` (cột `source`).

## 3. So với bộ viết tay hiện tại

`pos` = số nhà cung cấp có trường dương chứa từ; `any` = có trường bất kỳ của op T chứa từ (`lists/stats-hand.csv`).
Luật giữ: pos ≥ 3, pos/any ≥ 0,5, qua ở ≥ 70% của 200 bootstrap. Từ chứa một từ đã giữ thì bỏ (`is_admin` chứa
`admin`), vì builder khớp theo chuỗi con.

| Danh sách (dòng mã) | Viết tay hiện tại | Rút vòng 4 | Bằng chứng cho từ viết tay (pos / any) |
|---|---|---|---|
| Cờ admin `:104` | `is_admin, isadmin, is_superuser, is_superadmin, is_staff` | `admin` | `admin` 6/6; `is_admin`, `isadmin`, `is_staff` 1/1; `is_superuser`, `is_superadmin` 0 |
| Vai trò `:417` | `role, plan, permission, level, tier` | `permission, role` | `role` 20/22; `permission` 9/9; `level` 2/3; `plan`, `tier` 0 |
| Nạn nhân `:414` | `username, userid, user_id, user, account, member, subject, principal` | `member, user` | `user` 34/39; `member` 8/14; `userid` 12/16 và `user_id` 8/8 qua luật, bỏ vì chứa `user`; `username` 6/15; `account` 1/6; `principal` 1/2; `subject` 0 |
| Email `:415` | `email` | rỗng | `email` 3/18 |
| Mức thấp `:418` | `view, read, guest, basic, free, member, user, none, restrict, limited` | `read` | `read` 5/6; `member` 3/4 (bootstrap 65%); `guest` 2/2; `view`, `user`, `none` 1/1; còn lại 0 |
| Mức cao `:419` | `admin, owner, super, root, manage, write, edit, power, full` | `admin` | `admin` 6/6; `write` 1/3; `owner`, `manage`, `full` 1/1; còn lại 0 |

Từ chỉ corpus đề xuất mà sát ngưỡng (`lists/stats-derived.csv`): `roles` 6/6 và `permissions` 4/4 (chứa `role`,
`permission`); `membership` 3/3 (bootstrap 60,5%); admin: `create` 3/4, `restrict` 3/3 (bootstrap 56%, 58%).

## 4. Kiểm chéo nhóm theo nhà cung cấp

5 phần, lần lặp 1 là số chính. V = viết tay, R4 = rút lại trên phần huấn luyện của mỗi phần, R3 = danh sách cuối vòng 3
giữ cố định. McNemar chính xác hai phía, KTC 95% bootstrap theo nhà cung cấp 2.000 lần (`cv.json`, `extra-tests.json`).

| Chỉ số | Đơn vị | V | R4 | R3 | R4 − V: p, KTC 95% | R4 − R3: p |
|---|---|---|---|---|---|---|
| M1 transition đầu là op T, khớp trường vai trò | 52 API | 18 | 16 | 15 | 0,69; −0,135 … +0,038 | 1,0 |
| M1 phụ: một transition khả dụng đúng | 52 API | 26 | 23 | 25 | 0,38; −0,154 … +0,019 | 0,69 |
| M2 báo nhầm | 174 API | 17 | 17 | 68 | 1,0; −0,034 … +0,040 | < 0,001 |
| M3 trường nạn nhân đầu tiên đúng | 184 op | 117 | 107 | 118 | 0,013; −0,141 … +0,005 | 0,003 |
| M4 giá trị hạ quyền đứng đầu là mức thấp nhất | 18 op | 15 | 15 | 16 | 1,0; 0 … 0 | 1,0 |
| M5 op T = 0 được 0,6 nhờ danh sách admin | 10.182 op | 4 | 165 | 0 | < 0,001; +0,005 … +0,032 | < 0,001 |

Lần lặp 2–4 cho R4: M1 16, 16, 18; M2 11, 11, 18; M3 106, 117, 109; M4 15, 15, 13; M5 213, 229, 249.

Danh sách theo phần của lần lặp 1 (`cv.json`, `fold_lists`): B đủ dữ liệu ở 2/5 phần, 3 phần còn lại dùng danh sách thấp/cao
viết tay. Nạn nhân chỉ còn `user` ở 2/5 phần; cờ admin rỗng ở 1/5 phần.

## 5. Trên toàn bộ dữ liệu (cùng dữ liệu rút và đo)

Đây là số trong mẫu, không phải kiểm chéo. Nó cho thấy danh sách thấp/cao thật sự được dùng.

| Chỉ số | V | R4 toàn bộ |
|---|---|---|
| M1 (52 API) | 18 | 18 |
| M2 (174 API) | 17 | 11 |
| M3 (184 op) | 117 | 118 |
| M4 (18 op) | 15 | 11 |
| M5 (10.182 op) | 4 | 249 |

Bốn op M4 mất, giá trị đứng đầu theo V và theo R4:

| Op | Thứ tự đã gán | V | R4 |
|---|---|---|---|
| S101-0104 `PATCH /v0.1/apps/{owner_name}/{app_name}/users/{user_email}` | `viewer<developer<manager` | `viewer` | `manager` |
| S107-0031 `PUT /organizations/users/{user}` | `user<billing=teacher<admin` | `user` | `admin` |
| S101-N0135 `PATCH /v0.1/orgs/{org_name}/users/{user_name}` | `member<collaborator<admin` | `member` | `admin` |
| S210-N0132 `PUT /orgs/{org}/memberships/{username}` | `member<admin` | `member` | `admin` |

Khi không giá trị nào khớp mức thấp, mô phỏng (theo `harvestReducedRoleCandidates`, `RestSecurityBuilder.kt:956–984`) giữ thứ tự enum của spec, nên giá trị đầu enum đứng đầu. Builder dừng ở
giá trị đầu tiên được chấp nhận (`RestSecurityBuilder.kt:671–672`), nên ở bốn op này transition sẽ đặt quyền cao thay vì
hạ quyền.

M5: 249 op T = 0 thuộc 28 API được 0,6 vì đường dẫn hoặc tên trường thân chứa `admin`. Nhiều nhất S510 (61 op), S213
(34), S535 (25). Ví dụ `POST /admin/hooks`, `POST /admin/cron/{task}` (S108). M2 không tăng vì một op chỉ thành transition
khả dụng khi có trường vai trò hoặc cờ admin boolean.

## 6. Neo trên 6 target

| Target | Trường cần nhận | V | R4 | R3 |
|---|---|---|---|---|
| reports-api, vampi-seeded | `role`, `username` | có | có | có |
| pyLoad | `permission`, `role`, `user` | có | có | có |
| artifact-keeper | `is_admin` (boolean), `id` | có | có | mất `is_admin` |
| Airflow | `roles`, `username` | có | có | có |
| bamf | `email` | có | mất | mất |

Nguồn: `lists/final-lists.json`, khoá `anchors`.

## 7. Hạn chế

- LA, LB, LM và người phân xử đều là model Anthropic. Kappa đo độ nhất quán, không đo tính đúng. Không có nhãn từ mã nguồn.
- LM là phiên chính, đã thấy nhãn và kết quả ba vòng trước cùng các tranh luận về chúng.
- LA không có Bash nên không tự đếm dòng (log của nó ghi điều này). Đếm ngoài: đủ 6.409/6.409 dòng ở cả ba lượt, không có
  mã dòng lạ.
- Cột R3 dùng danh sách rút từ nhãn vòng 3; 3.972 op vòng 3 nằm trong dữ liệu đo, nên R3 đã thấy một phần dữ liệu kiểm.
- B qua ngưỡng sát nút (18/15 enum, 11/10 nhà cung cấp). Trong kiểm chéo, phần lớn các phần dưới ngưỡng, nên cột M4 của R4
  chủ yếu đo danh sách viết tay dự phòng. Số M4 của danh sách rút thật là §5, trong mẫu, 18 op.
- M3 lần lặp 1: McNemar coi từng op độc lập (p = 0,013); bootstrap theo nhà cung cấp có KTC chứa 0. Hai phép thử lệch nhau
  ở biên.
- Mô phỏng chưa đối chiếu với một lượt EvoMaster thật. Giả định của `sim.py` như vòng 3 (`../field-labelling-r3-20261006/RESULTS.md`
  §8), trừ thứ tự op trong một API: vòng này dùng vị trí op trong spec (`pos`).

## 8. Lệch luật

- Từ khối 034, LM chỉ ghi dòng T = 1; cột `sub` của LM trống từ đó. `sub` không dùng trong gộp, rút hay đo.
- Hết quota 23:42; đổi tài khoản 23:55; dừng 00:07 để quay về tài khoản cũ; LA, LB chạy lại từ 03:02 bằng `run2.sh`, khối dở
  được gán lại từ đầu. LM xong 001–074 trước 00:07, 075–086 sau 03:07.
- Người phân xử chỉ được chọn X, Y hoặc Z, không được sửa nhãn.
- Ngoài protocol: M1 phụ (giữ từ vòng 3), kiểm định cho M5, và §5 (số trong mẫu).

## 9. Theo protocol §6

Danh sách rút trên toàn bộ dữ liệu là kết quả của vòng này: `lists/final-lists.json`, khoá `derived`. Chưa đổi mã.
Trước khi đưa vào `RestSecurityBuilder.kt`, hai điểm ở §5 (mức thấp `read` và `admin` chạm đường dẫn) là nơi danh sách
rút làm builder kém đi trên dữ liệu đo.
