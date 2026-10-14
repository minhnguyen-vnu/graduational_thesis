Đây là bài kiểm tra chuỗi kích hoạt tự động của squad. Không phải việc luận văn. Không đụng tới EvoMaster, docs, em-results.

Làm đúng ba bước rồi dừng:

1. Gọi Bash chạy đúng lệnh `date "+%F %T"`. Ghi lại kết quả, hoặc ghi lại nguyên văn thông báo nếu lệnh bị từ chối.
2. Gọi Bash chạy đúng lệnh `python3 -c "print(1+1)"`. Ghi lại kết quả, hoặc nguyên văn thông báo nếu bị từ chối.
3. Ghi file `infra/squad/reports/smoke-result.md` gồm các dòng:
   - `slot: smoke`
   - `model: <tên model của phiên này>`
   - `cwd: <thư mục làm việc hiện tại>`
   - `bash date: <kết quả hoặc thông báo từ chối>`
   - `bash python3: <kết quả hoặc thông báo từ chối>`
   - `subagent: <có hay không có quyền gọi công cụ Agent, chỉ trả lời theo danh sách công cụ bạn đang có, đừng gọi thử>`

Không làm gì khác. Không đọc thêm file. Không sửa file nào khác.
