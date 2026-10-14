# Code walkthrough — quy ước

Tài liệu giải thích **từng dòng** code của đóng góp luận văn. User paste code, mỗi đoạn được
giải thích trong file part tương ứng.

## Quy ước viết (bắt buộc)

- Kết luận trước, bằng chứng sau. Câu ngắn.
- **Mỗi khẳng định phải kèm dữ liệu thật.** Không có ví dụ = không được viết.
- **Chạy tay bắt buộc**: bảng `số dòng thật | dòng code | giá trị thật quan sát được`.
  Một dòng code = một hàng bảng.
- **Dòng nào có biến thì phải cho biết dữ liệu hình dạng gì.** Ghi đủ ba thứ: kiểu Kotlin,
  số phần tử đo được, một giá trị mẫu lấy từ run thật.
  Sai: `individualsInSolution = archive.extractSolution().individuals` — "đọc archive sau search".
  Đúng: `List<EvaluatedIndividual<RestIndividual>>`, 54 phần tử ở run `t1-vuln-seed1-r0`,
  phần tử thứ 16 là test 4 lời gọi `POST /reports` → `PUT /reports/44` → `PUT /users/alice/role` → `PUT /reports/44`.
- Kiểu dữ liệu nền của EvoMaster giải thích **một lần** ở `part0-base-evomaster.md`. Part sau chỉ trỏ về.
- Số liệu chỉ lấy từ file dưới `infra/em-results/` hoặc từ source thật. Không suy đoán.
  Chỗ nào không đo được thì ghi thẳng "chưa đo".
- Không dùng `⇒` `→` trong văn xuôi (trong bảng chạy tay thì được), không emoji, không IN HOA nhấn mạnh.
- Không câu tương phản `X, không phải Y`. Không mệnh đề đuôi `…, điều này cho thấy…`.
- Một ô bảng = một mệnh đề.

## Các part

| Part | File | Nội dung |
|---|---|---|
| — | `kotlin-co-ban.md` | Tra cứu cú pháp Kotlin cho người viết Java. Đọc trước Part 1 nếu chưa viết Kotlin |
| 0 | `part0-base-evomaster.md` | Kiểu dữ liệu nền: `RestIndividual`, `RestCallAction`, `ActionResult`, `actionDefinitions`, `Solution`, `EvaluatedIndividual` |
| 1 | `part1-vong-doi-pha-security.md` | Vòng đời: `Main` → pha SECURITY → `applySecurityPhase` |
| 2 | `part2-dung-bo-ba.md` | Dựng bộ ba: chọn victim/operator/guarded endpoint, vòng retry |
| 3 | `part3-suy-dien-va-gan-tham-so.md` | Suy diễn transition, gán tham số role, operator restore |
| 4 | `part4-kiem-chung-void-va-probe.md` | VOID, C4 re-login probe, reset state |
| 5 | `part5-phan-xu-oracle.md` | Phán xử: `RestSecurityOracle.handleStatefulAuthorization`, fault 970 |

## Nguồn code

- `/Users/minhnguyen/IdeaProjects/EvoMaster`, branch `stateful-authz-oracle`, HEAD `007e5e09f9`.
- Số dòng trong các file part là số dòng của HEAD hiện tại. Nếu code đổi, số dòng phải đo lại.
