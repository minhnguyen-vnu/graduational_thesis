# Gán nhãn mức operation, vòng 3 — kết quả

2026-10-06. Protocol `PROTOCOL.md` (chốt 02:20, lệch luật ở §9 của nó và ở §8 dưới đây). Không sửa mã EvoMaster. Mọi số
từ `cv.json`, `lists/`, `exploratory.json`, `hard-word-evidence.txt`, `m1-failures-hard.txt`. Lexicon transition đọc từ
cây làm việc EvoMaster, sha256 ghi trong `cv.json`.

## 1. Kết luận

- Luật rút khai trước, chạy trên 230 nhà cung cấp, cho ra: vai trò `permission, role, type`; cờ admin rỗng; nạn nhân
  `member, user` cộng tầng `id`; `email` không qua luật; B (thấp/cao) không đủ dữ liệu: 9 enum có thứ tự từ 8 nhà cung
  cấp, dưới ngưỡng 15/10. Biến thể chỉ corpus cho ra đúng bộ đó.
- Trên kiểm chéo (lần lặp 1), danh sách rút không hơn bộ viết tay ở chỉ số nào. Nó báo nhầm nhiều hơn: M2 57/185 API
  so với 18/185, McNemar p < 0,001, KTC 95% của hiệu +0,146 tới +0,276. Nguồn của chênh lệch là từ `type`.
- Neo trên target: danh sách rút mất `is_admin` (artifact-keeper) và `email` (bamf). Bộ viết tay nhận đủ 6/6 target.
- Corpus đỡ được 4 từ viết tay: `role`, `permission`, `user`, `member`. Corpus không có bằng chứng cho `plan`, `tier`,
  `subject`, cả 5 từ cờ admin, và có bằng chứng ngược cho `email` làm tầng nạn nhân (§4).
- Điểm nghẽn ở runtime nằm ở tên trường vai trò. Trong 24 API mà bộ viết tay trượt M1, có 19 API trượt vì trường vai trò
  của op đúng không khớp danh sách (`m1-failures-hard.txt`). Ví dụ: `body:type` (Trello), `path:memberType` (Bungie),
  `body:admin` boolean (S319, S534).

## 2. Nhãn

| | Số |
|---|---|
| Op / spec / nhà cung cấp | 3.972 / 230 / 230 |
| Op T = 1: L1 / L2 / cuối | 66 / 96 / 101 |
| Kappa trên T, cả 53 khối | 0,736 |
| Dòng lệch (T, victim, role hoặc order) | 57, trong đó 42 lệch T |
| Phân xử chọn L1 / L2 | 16 / 41 |
| Nhà cung cấp có ít nhất một op T = 1 | 45 |

Nguồn: `kappa.json`, `disagreements.csv`, `adjudication.csv` (lý do từng dòng), `final.csv` (cột `source`).

## 3. Kiểm chéo nhóm theo nhà cung cấp

5 phần, lần lặp 1 là số chính. Viết tay = V, rút = R. Biến thể chỉ corpus trùng R ở mọi ô.

| Chỉ số | Đơn vị | V | R | McNemar p | KTC 95% hiệu R − V |
|---|---|---|---|---|---|
| M1 transition đầu là op T, khớp trường vai trò | 38 API | 14 | 13 | 1,0 | −0,132 … +0,105 |
| M1 phụ: một trong các transition khả dụng đúng | 38 API | 17 | 15 | 0,69 | −0,184 … +0,079 |
| M2 báo nhầm | 185 API | 18 | 57 | < 0,001 | +0,146 … +0,276 |
| M3 trường nạn nhân đầu tiên đúng | 92 op | 65 | 62 | 0,45 | −0,094 … +0,013 |
| M4 giá trị hạ quyền đứng đầu là mức thấp nhất | 9 op | 7 | 7 | 1,0 | −0,333 … +0,333 |
| M5 op T = 0 được 0,6 nhờ danh sách admin | 3.871 op | 1 | 0 | | |

Lần lặp 2–4 cho R: M1 12, 14, 13; M2 52, 60, 64; M3 66, 66, 60. V không đổi vì không rút.
Danh sách theo từng phần của lần lặp 1 (`cv.json`, `fold_lists`): vai trò dao động giữa `role`, `role type`, `permission role type`;
`email` và cờ admin không qua ở phần nào.

M1 phụ không có trong protocol; thêm vào vì builder thử lần lượt mọi transition khả dụng (`RestSecurityBuilder.kt:545`).

## 4. Từng từ viết tay

`pos` = số nhà cung cấp có trường dương chứa từ; `any` = có trường bất kỳ của op T chứa từ (`hard-word-evidence.txt`).
Ngưỡng giữ: pos ≥ 3, pos/any ≥ 0,5, qua ở ≥ 70% bootstrap.

| Danh sách | Từ | pos / any | Kết quả |
|---|---|---|---|
| Vai trò `:417` | `role` | 12 / 13 | giữ |
| | `permission` | 5 / 5 | giữ |
| | `level` | 2 / 2 | thiếu dữ liệu |
| | `plan`, `tier` | 0 / 0 | không có bằng chứng |
| Cờ admin `:104` | 5 từ `is_*` | 0 / 0 | không có bằng chứng |
| | `admin` (ứng viên từ corpus) | 3 / 3 | rớt bootstrap (58,5%) |
| Nạn nhân `:414` | `user` | 26 / 30 | giữ |
| | `member` | 7 / 10 | giữ |
| | `userid`, `user_id` | 9 / 12, 7 / 7 | qua luật, bỏ vì chứa `user` |
| | `username` | 4 / 9 | rớt tỉ lệ; `user` vẫn khớp nó ở runtime |
| | `principal` | 1 / 2 | thiếu dữ liệu |
| | `account` | 0 / 4 | không có trường dương |
| | `subject` | 0 / 0 | không có bằng chứng |
| Email `:415` | `email` | 3 / 12 | rớt tỉ lệ (0,25) |
| Tầng `id` | `id` | 30 / 39 | luật cấu trúc, không xét |

B (`:418`, `:419`), mô tả, không qua luật vì thiếu dữ liệu: mức thấp nhất của cả 9 enum chứa một từ thấp viết tay
(`viewer`, `user`, `read`, `member`, `guest` ×2, `read_only` ×2, `read_project`). Mức cao nhất chứa một từ cao viết tay ở
8/9 enum. Ngoại lệ là `guest < member` (windows.net): `member` ở đây là mức cao, còn danh sách thấp viết tay chứa `member`.

## 5. Thăm dò hậu kiểm

Chạy sau khi thấy §3; không phải kết quả khai trước (`exploratory.json`, lần lặp 1).

| Biến thể | M1 | M2 | M3 | So V |
|---|---|---|---|---|
| R bỏ `type` | 12/38 | 11/185 | 62/92 | M2 p = 0,016; M1 p = 0,63 |
| V bỏ `plan, level, tier` | 13/38 | 11/185 | 65/92 | M2 p = 0,016; M1 p = 1,0 |
| R cộng lại cờ admin và `email` viết tay | 12/38 | 57/185 | 62/92 | M2 p < 0,001 |

Bỏ `plan, level, tier` giảm báo nhầm 7 API và mất 1 API ở M1. Đây là một giả thuyết cho vòng đo sau, chưa là phát hiện.

## 6. Đề xuất cho luận văn

Viết thành: "danh sách nhận diện trường được đối chiếu với corpus gán nhãn mức operation; corpus đỡ được `role`,
`permission`, `user`, `member`; các từ còn lại giữ vì target thực tế, kèm số liệu thiếu bằng chứng". Không thay mã:
thay bằng danh sách rút làm báo nhầm tăng gấp ba và mất hai target neo. Lập luận chống lại: giữ các từ không có bằng
chứng tức là vẫn còn từ viết tay; nếu hội đồng đòi bỏ hết, biến thể "V bỏ `plan, level, tier`" ở §5 là ứng viên, nhưng nó
cần một lượt đo khai trước riêng.

## 7. Hạn chế

- Tập đo đã bị nhìn: L1 là phiên chính, đã thấy nhãn và kết quả hai vòng trước. Kiểm chéo đo quy trình rút, không đo
  trên dữ liệu chưa ai thấy.
- L1, L2 và người phân xử đều là model Anthropic (Opus 5.5, Sonnet 5.5, Opus 5.5). Kappa đo độ nhất quán, không đo tính
  đúng. Không có nhãn từ mã nguồn.
- Đơn vị nhỏ: 38 API cho M1, 9 op cho M4. KTC của M1 rộng ±0,13.
- Mô phỏng chưa đối chiếu với một lượt EvoMaster thật (§8).
- L2 sau 06:52 viết mỗi lô 5 khối trong 75–92 giây; không có Bash nên không tự đếm dòng. Số dòng đủ 75/khối;
  mức đọc thật không kiểm được.
- Vòng 1: khối 020 dòng 1–39 không được đọc, chưa ghi ở protocol vòng 1 (phát hiện khi trả lời câu hỏi Q6 của agent A).

## 8. Giả định của mô phỏng (`sim.py`)

Ghi ở đây thay vì đầu file vì luật không comment trong mã.
- Tên gene = tên lá của trường; body có `$ref` thêm một gene gốc mang tên schema (`RestActionBuilderV3.kt:779`).
- Loại gene: boolean; enum khi có danh sách enum; số; chuỗi; mảng; object. Kiểu khác không gán được.
- `transitionHay` = path + `METHOD:path` + tên trường body tầng đầu, hạ chữ thường.
- Gán nạn nhân thành công với gene chuỗi hoặc số không enum. Thứ tự: path rồi body, mỗi chỗ ba tầng; rồi query với
  từ cụ thể cộng `id`.
- Mảng vai trò luôn coi `minSize = 0`. `routeLooksMissing`, mã trạng thái và gene content-type bị bỏ qua.
- Thứ tự op trong một API là thứ tự `row_id`.

## 9. Lệch luật

- Protocol ghi 228 nhà cung cấp; `rows.jsonl` có 230 spec từ 230 nhà cung cấp. Mọi số dùng 230.
- L2 dừng ở khối 038 lúc 02:26 vì hết quota; chạy tiếp khối 039–053 lúc 06:52 bằng các phiên mới, cùng lời nhắc
  (`scratchpad/r3L2/log.txt`).
- Người phân xử chỉ được chọn X hoặc Y, không được sửa nhãn.
- Thêm M1 phụ (§3) và thăm dò hậu kiểm (§5), cả hai ghi rõ là ngoài protocol.
