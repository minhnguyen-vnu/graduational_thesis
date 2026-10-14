# Squad — phiên tự chạy (đã tắt 2026-09-17)

Squad tắt ngày 2026-09-17: tốn token mà chất lượng không bằng một phiên tương tác. Hai plist đã `bootout`
khỏi launchd và chuyển sang `launchd-off/` để không nạp lại khi đăng nhập. Mục 1 và 2 không còn hiệu lực;
file này giữ để đọc sổ chạy cũ và kho đề bài. Bật lại: chuyển hai plist về `~/Library/LaunchAgents/`
rồi `launchctl bootstrap gui/$(id -u) <plist>`.

## 1. Lịch

| Lịch | Giờ | Chạy gì |
|---|---|---|
| `com.thesis.squad.night` | 00:05 | `squad-run.sh night` |
| `com.thesis.squad.report` | 18:00 | `squad-run.sh report` |

Plist nằm ở `~/Library/LaunchAgents/`, launchd nạp lại mỗi lần đăng nhập. Ban ngày không có lịch nào.

## 2. Lệnh cho người

| Lệnh | Việc |
|---|---|
| `squad status` | trạng thái, lịch đã nạp, 5 lần chạy gần nhất, việc nặng đang chạy, báo cáo và đề bài mới nhất |
| `squad pause` | tạo `infra/squad/PAUSE`; đến giờ job vẫn nổ nhưng thoát ngay, không gọi claude |
| `squad resume` | xoá `PAUSE` |
| `squad stop` | giết phiên tự động đang chạy |

## 3. Đề bài

- Một slot, một việc: `tasks/<ngày>-<slot>.md`.
- Nhiều việc trong một đêm: `tasks/<ngày>-<slot>-<số>-<tên>.md`. Script chạy theo thứ tự tên, **mỗi file một phiên riêng**, một dòng sổ riêng, một log riêng.
- Không có file nào: ghi `no task file`, thoát, không tốn gì.
- Dòng đầu file ghi được `model: sonnet` để chọn model cho phiên đó. Thiếu dòng này thì dùng `opus`.
- `tasks/staged/` là chỗ để đề bài chưa tới lượt: script không quét thư mục con.
- `tasks/done/` là chỗ cất đề bài đã dùng.

### Cách viết đề bài

- Việc code: câu đầu ghi thẳng `Giao cho thesis-coder`, kèm tiêu chí nghiệm thu. Không đưa gợi ý tra cứu
  (tên hàm, số dòng, từ khoá `grep`) vào đề bài: leader sẽ tự đi đọc source, rồi subagent đọc lại lần nữa,
  tiền đọc trả hai lần. Đêm 2026-09-16 leader mất 22 lượt như vậy.
- Leader chỉ đọc đề bài, gọi subagent, rồi viết báo cáo. Chỗ nào leader phải tự đọc file thì ghi rõ file nào.
- Mỗi đề bài ghi trần đọc: file nào được đọc cả, file nào chỉ đọc vùng khớp `grep -n`.

## 4. Sổ `reports/runs.csv`

Cột: `start,end,slot,task,exit,reason,cost_usd,turns,session`.

| `reason` | Nghĩa |
|---|---|
| `started <model>` | script đã gọi claude, chưa có kết quả |
| `ok` | phiên kết thúc mã 0 |
| `error` | claude trả lỗi, xem log |
| `paused` | có file `PAUSE` |
| `no task file` | đến giờ nhưng không có đề bài |
| `already run` | đề bài này đã có một lần kết thúc `ok` |
| `chain stopped on limit` | log chứa thông báo hết hạn mức, chuỗi dừng, không chạy tiếp file sau |

Không có dòng nào cho một ngày nghĩa là launchd chưa nổ. Có `started` mà không có dòng kết thúc nghĩa là phiên bị giết.

Chạy lại một đề bài đã `ok`: xoá dòng của nó trong sổ, hoặc đổi tên file đề bài.

## 5. Mặc định và biến ghi đè

| Biến | Mặc định | Việc |
|---|---|---|
| `SQUAD_MAX_TURNS` | 40 | trần số lượt của phiên |
| `SQUAD_DEADLINE_MIN` | 450 | trần thời gian, phút |
| `SQUAD_SETTING_SOURCES` | `project,local` | nguồn cấu hình được nạp |
| `SQUAD_MODEL` | `opus` | model khi đề bài không khai |
| `SQUAD_TASK` | rỗng | chạy thẳng một file đề bài, bỏ qua quy ước tên |

Phiên đêm chạy `--permission-mode acceptEdits`, nên lệnh Bash ngoài allowlist trong `.claude/settings.local.json` sẽ bị từ chối và việc đó chết. Thêm quyền trước, đừng để phiên đêm tự vấp.

## 6. Số đo ngày 2026-09-16

Cùng một đề bài thăm dò, chỉ đổi một biến, đo bằng `runs.csv` và `usage` trong log.

| Nhánh | Nguồn cấu hình | Model | Ngữ cảnh nền (token ghi cache) | Skill / agent thấy được | Giá |
|---|---|---|---|---|---|
| A | `user,project,local` | opus | 24.696 | 124 / 48 | 0.2965 |
| B | `project,local` | opus | 11.287 | 16 / 9 | 0.1203 |
| C | `project,local` | sonnet | 16.861 | 12 / 7 | 0.0723 |

Cả ba nhánh đều thấy `thesis-coder`, `em-batch` và `CLAUDE.md`. Nhánh A trả lời dài hơn hai nhánh sau (output 1.773 token so với 34), nên phần chênh do output là khoảng 0.04; phần còn lại là ngữ cảnh nền.

Phiên đêm 2026-09-16 chạy theo cấu hình cũ: 34 phút, 7.03 USD, dừng vì hết hạn mức phiên. Trong đó leader khoảng 1.22, ba subagent khoảng 5.8.
