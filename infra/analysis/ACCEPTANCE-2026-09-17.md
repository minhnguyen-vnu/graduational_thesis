# Nghiệm thu hai việc đêm 2026-09-16 → 17

Đề bài: `infra/squad/tasks/done/2026-09-17-night.md`. Đêm đó không có báo cáo, nên file này thay báo cáo.
Người đối chiếu: phiên tương tác 2026-09-17 sáng. Mọi dòng dưới đây kèm lệnh đã chạy.

## Việc 1 — corpus

| Tiêu chí | Kết quả | Lệnh và kết quả |
|---|---|---|
| JSON đọc được bằng `json.load` | ĐẠT | `json.load` trả 2529 khoá |
| `PROVENANCE.md` có sha256, kích thước, giờ tải, lệnh đếm, kết quả đếm | ĐẠT | sha256 tính lại `dfac835d2d1f13df…` trùng dòng 16; kích thước 8855894 bytes trùng dòng 17 |
| `wfd-inventory.md` liệt kê từng file với đường dẫn thật | ĐẠT | lấy 8 đường dẫn đầu, cả 8 tồn tại trên đĩa; clone exit=0 |

Bảng đó đã bị thay ngày 2026-09-17, xem mục dưới.

Ngoài tiêu chí, một lỗ hổng chặn việc lấy mẫu: bảng có 145 dòng, 63 dòng nằm trong `/test/` hoặc `/samples/`.
Đó là fixture của microcks (`cars-openapi.yaml`, `stripe-spec3.yaml`), không phải API được kiểm thử.

Đã xử lý cùng ngày: WFD tự gom một spec một SUT trong `wfd/openapi-swagger/`, đúng 36 file, khớp con số "36 WFD
specs" của `CLAUDE.md` §6. Bảng mới `corpus/wfd-suts.md` đọc cả 36, đếm đường dẫn và operation ghi. Bảng quét cũ
đã xoá; script sinh ra nó vẫn còn.

## Việc 2 — quy tắc gán nhãn

| Tiêu chí | Kết quả | Lệnh và kết quả |
|---|---|---|
| Mỗi phạm trù có trích dẫn nguyên văn kèm nguồn | ĐẠT | `sources.md` có A1–A4 (RFC 7643) và B2–B6 (dự thảo INCITS); đối chiếu 5 câu bằng `pdftotext -layout` và `rfc7643.txt`, cả 5 khớp đúng một lần |
| Có nhãn "không rõ" và quy tắc phân xử | ĐẠT | `rules-draft.md` §3 nhãn `U`, §9 cách phân xử |
| Đúng 3 ví dụ đã áp dụng thử, lấy từ ba target của ta | ĐẠT | §10: reports-api, vampi-seeded, pyLoad |
| Form dùng được cho cả người lẫn LLM, không cần đọc thêm | ĐẠT | `labelling-form.md` không tham chiếu file nào khác |

Năm câu đã đối chiếu nguyên văn:
`could wait for such a session to terminate normally`, `revokes the permission to perform an operation on an object`,
`deletes a role from the active role set of a session` (dự thảo INCITS);
`value of false implies that the user's account has been suspended`, `No vocabulary or syntax is specified…` (RFC 7643).

Hai điểm ngoài tiêu chí:

1. `sources.md` tiêu đề mục B vẫn ghi `ANSI INCITS 359-2004 §6.1`. `CLAUDE.md` §3 nay cấm trích bản ban hành.
   Mục B0 và B1 đã nói rõ bản ban hành không truy cập được, chỉ riêng tiêu đề còn sai nhãn.
2. `rules-draft.md` §8: bốn trường hợp "counts as reducing" đã được chốt trong ngày 2026-09-17. Xoá chủ thể và
   rời group chuyển thành `N8`, `N9`; `active: false` và đặt giá trị role giữ là `R`; người gán nhãn được nhìn
   `enum`. Quy tắc và phiếu đã sửa theo.
