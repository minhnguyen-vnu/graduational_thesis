# Đề bài

Bạn là một trong hai chuyên gia phân tích độc lập. Đọc dữ liệu trong thư mục này và tự rút kết luận.

## Bối cảnh

Một luận văn mở rộng EvoMaster (công cụ sinh test cho REST API) với một oracle phát hiện lỗi phân quyền có trạng thái:
một tài khoản (nạn nhân) vẫn dùng được quyền cũ sau khi bị hạ quyền, khi dùng lại thông tin đăng nhập cấp trước lúc hạ.
Để dựng ca thử, `code/RestSecurityBuilder.kt` phải tự tìm trong OpenAPI spec của một API lạ:

- operation "transition" làm hạ quyền một user;
- trường chỉ user bị tác động (nạn nhân);
- trường vai trò/quyền, hoặc cờ admin boolean;
- trong enum của trường vai trò: giá trị quyền thấp và giá trị quyền cao.

Việc nhận diện các trường này dựa vào danh sách từ viết tay trong `code/RestSecurityBuilder.kt`:

| Danh sách | Dòng |
|---|---|
| `ADMIN_FLAG_FIELD_SIGNALS` | 104 |
| `transitionUserParamSignals`, `userEmailParamSignals` | 414, 415 |
| `roleFieldSignals` | 417 |
| `roleLowPrivSignals`, `roleHighPrivSignals` | 418, 419 |

Cách các danh sách được dùng lúc chạy: đọc mã (tìm tên danh sách trong file). `code/stateful-authz-lexicon.csv` là bộ từ
cho một phần khác (chấm điểm operation transition), đã được rút từ corpus trước đó; nó nằm ngoài phạm vi.

Tác giả muốn thay các danh sách viết tay trên bằng danh sách rút từ một corpus OpenAPI đã gán nhãn mức trường, sao cho
mỗi từ có cơ sở dữ liệu và bảo vệ được trước hội đồng. Ràng buộc của tác giả: nhãn do LLM gán, tác giả không tự gán nhãn.

## Đã làm (hai vòng, 2026-10-04)

- Vòng 1: `lexicon-rules/field-labelling-20261004/` — đọc `PROTOCOL.md` trước.
- Vòng 2: `lexicon-rules/field-labelling-r2-20261004/` — đọc `PROTOCOL.md` trước.
- Bốc spec: `corpus/sample_specs_field*.py`, `corpus/sample-*.json`. Spec thô không có trong gói; trường đã trích nằm
  trong `rows.jsonl` của từng vòng.
- Nhãn: `L1/`, `L2/` (hai lượt gán), `disagreements.csv`, `adjudication.csv`, `kappa-raw.json`.
- Rút và đo: `derive_eval.py`, `mcnemar.py` (vòng 1); `common.py`, `select_rule.py`, `evaluate.py`, `exploratory.py`,
  `merge_lists.py` (vòng 2). Kết quả: `results.json`, `mcnemar.json`, `select.json`, `anchor.json`,
  `exploratory.json`, `merged-lists.json`, `lists/`.
- `final.csv` chỉ chứa trường có nhãn dương; `rows.jsonl` chứa mọi trường, kể cả âm.
- Script chạy được trong thư mục này (`python3`). Chúng ghi đè file kết quả trong chính thư mục này; đây là bản sao
  riêng của bạn.

Bản báo cáo diễn giải của tác giả (`RESULTS.md`), các file bàn giao, và file luật dự án được giữ lại có chủ ý để bạn
không bị neo theo cách hiểu có sẵn. Protocol có nhắc tới các file đó; bỏ qua.

## Việc của bạn

1. Nêu các điểm yếu của phiên gán nhãn và rút từ (cả hai vòng) cần cải thiện.
2. Đề xuất cách gán nhãn và rút từ tối ưu hơn, cho ra một bộ từ có ý nghĩa và có cơ sở hơn.

Yêu cầu:
- Mỗi khẳng định kèm bằng chứng truy được: file và dòng, hoặc con số tự tính kèm lệnh/script đã chạy. Lưu script của
  bạn trong `work/`. Chỗ nào là suy luận chưa kiểm thì ghi rõ là suy luận.
- Mỗi điểm yếu: nó là gì, ví dụ cụ thể từ dữ liệu, ảnh hưởng tới bộ từ cuối, mức nặng (cao/vừa/thấp).
- Mỗi đề xuất: làm cụ thể thế nào (bốc mẫu, gán nhãn, luật rút, cách đo), chi phí ước lượng, và lập luận chống lại
  chính đề xuất đó.
- Giữ trung lập. Không giả định trước kết luận nào, kể cả việc danh sách rút từ corpus phải tốt hơn hay kém hơn danh
  sách viết tay.
- Viết tiếng Việt, ngắn, nêu sự thật. Không sửa file nào ngoài `work/` và file đầu ra của bạn.
