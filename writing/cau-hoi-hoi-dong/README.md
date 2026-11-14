# Câu hỏi hội đồng

Mỗi chương một thư mục. Đã có: `chuong-1/`, `chuong-2/`, `chuong-3/`. Chưa làm: chương 4 tới 6.

Mỗi file `cau-hoi.md` gồm:
- Bảng khái niệm: mọi thuật ngữ chương đó đã viết, nghĩa trong một câu, kèm ví dụ. Quy định của bộ môn (diễn giải):
  khái niệm đã viết vào báo cáo mà không giải thích được thì bị coi là sao chép.
- Câu hỏi, chia theo mục của chương. Đoạn đầu mỗi câu là câu trả lời nói trong khoảng 30 giây; phần sau dùng khi bị
  hỏi tiếp; dòng `Nguồn` để tự tra lại.

Số liệu lấy từ jar M2, chạy ngày 2026-11-08 (`docs/results.md`).

## Còn mở trong khóa luận

Soát toàn bộ ngày 2026-11-10; các lỗi tìm được và phần mở rộng đã đưa vào khóa luận cùng ngày. Phần chính hiện khoảng
40 trang. Còn lại:

| # | Việc | Chỗ |
|---|---|---|
| 1 | Viết phần baseline sau khi chạy lại: mở đầu chương 5 gọi baseline là "EvoMaster v6.1.1", trong khi số ở mục 5.6 (vampi-seeded 0/20 lượt dựng được bộ ba, 17/20 lượt có F209) lấy từ batch cũ `infra/em-results/tier2-trials/`. Không ghi ngày hay jar vào khóa luận. | `chapters/chapter5.tex:8`, phần baseline |
| 2 | Viết kết quả pyLoad dev101 sau khi chạy. Câu về bản vá upstream đã sửa theo mã nguồn: nhà phát triển vá từ dev98 bằng cách xóa phiên, khóa luận không dùng bản vá đó làm đối chứng. | `chapters/chapter4.tex`, phần pyLoad |
| 3 | Commit mô hình M2 vào nhánh EvoMaster để GitHub khớp với số đo (HEAD còn M1). Chờ đồng ý. | repo EvoMaster |
| 4 | Chú thích trong `infra/pyload-cve/Dockerfile` và `patch_pyload.py` còn ghi upstream chưa vá. | `infra/pyload-cve/` |
| 5 | Chạy bộ kiểm ngữ cảnh `infra/context-eval/questions.md`, vì `docs/results.md` và `docs/metamorphic-authz-relations.md` đã đổi. | |
| 6 | Tùy chọn: bảng điều kiện hợp lệ của bộ ba viết lại theo mã, đặt ở mục 3.2. | `chapters/chapter3.tex` |

Nguồn của đoạn BACScan ở mục 2.4 là phần tóm tắt bài báo, đọc qua Semantic Scholar vì trang ACM chặn tải tự động; đoạn
GraphQLer dựa trên phần tóm tắt arXiv.

### Thực nghiệm chờ chạy (dự kiến 2026-11-11)

- pyLoad dev101, bản cài từ PyPI, cùng các điều chỉnh đã khai ở mục 4.2.3: kiểm tay bằng HTTP trước, rồi chạy công cụ.
  Câu hỏi: hạ quyền qua `/api/set_user_permission` thì cookie cũ còn dùng được không. Đọc mã cho thấy đường này chưa
  xóa phiên ở dev98–dev101; chưa chạy nên chưa khẳng định. Nếu lỗi còn, đó là bản vá upstream chưa phủ đủ.
- Chạy lại đủ arm baseline (tắt oracle thử nghiệm) với cùng thiết lập của đợt M2, để số ở mục 5.6 đo cùng đợt với mọi
  số khác. Chốt trước khi chạy: dùng jar M2 tắt oracle thử nghiệm hay jar EvoMaster v6.1.1 gốc.
