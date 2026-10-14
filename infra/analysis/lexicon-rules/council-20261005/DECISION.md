# Phân xử sau hai vòng (2026-10-06 ~02:10)

Nguồn: `A/round1.md`, `B/round1.md`, `A/round2.md`, `B/round2.md`. Hai agent: `claude -p --safe-mode`, Opus 5.5,
effort xhigh, mỗi agent một bản sao dữ liệu; không thấy CLAUDE.md, memory, `RESULTS.md`, handoff (`BRIEF.md`).
Người phân xử: phiên chính, cũng là L1 của hai vòng gán; đây là một hạn chế.

## 1. Điểm yếu hai bên cùng xác nhận (đã kiểm chéo bằng script của nhau)

| # | Điểm yếu | Bằng chứng chính |
|---|---|---|
| W1 | Đo mức trường trên mọi op; runtime dùng danh sách trong transition, theo thứ tự tầng | mô phỏng `A/work/w07` trên 24 op test: nạn nhân đúng viết tay 14, R4 10; thêm tầng email/id vào R4 thì bằng viết tay |
| W2 | R4 không ổn định, mất `role` | bootstrap nhà cung cấp: danh sách A-role tái hiện 1%, `role` vào 67–73% |
| W3 | Chọn luật trên dev nhỏ, trung bình F1 năm danh sách | dev A-admin 2 dương 1 nhà cung cấp; B cùng F1 ở cả năm luật |
| W4 | Nhãn rộng hơn nhu cầu runtime | 100/177 dương A-role train+dev ở op không có C; configcat 48 dương từ 4 op |
| W5 | `ADMIN_FLAG_FIELD_SIGNALS` cũng cộng 0,6 vào điểm transition, chưa đo | thay bằng `admin`: 131 op lên 0,6 (mô phỏng) |
| W6 | B quá ít dữ liệu | 18 enum có thứ tự trên cả ba tập |
| W7 | McNemar mức trường coi trường độc lập, đếm âm đúng | A-role p 0,0026 nghiêng về R4 nhờ 36 âm; trên dương viết tay 10/0 |
| W8 | Độ đúng của nhãn chưa đo; phân xử theo khối chỉ số, câu lý do mẫu | `R1/adjudicate.py:5-26`; S104-0025 23 dòng quyết chung |
| W9 | Đầu ra chỉ ghi dòng dương; bỏ sót không phát hiện được | khối 028/031: 0 A trên 3.243 trường |
| W10 | Luật gán đổi giữa hai vòng, train/dev không gán lại | r2 `PROTOCOL.md:18`, `:33-44` |
| W11 | MIN_LEN 4, hạ chữ trước khi tách camelCase | 24/127 dương C test không có token ≥ 4 ký tự |

Phiên chính kiểm thêm một câu hỏi B nêu: gene gốc của body mang tên schema `$ref`
(`RestActionBuilderV3.kt:779`), nên `roleFieldSignals` còn khớp tên schema như `RoleUpdateRequest`. Phần trích
corpus không có tên schema.

## 2. Bất đồng và phân xử

| Bất đồng | A | B | Chọn | Lý do |
|---|---|---|---|---|
| Từ viết tay làm ứng viên | tuỳ chọn, sợ neo | mặc định | B, kèm báo thêm biến thể chỉ-corpus | mọi từ cuối cùng qua cùng một luật; biến thể chỉ-corpus cho thấy phần do neo |
| Bỏ từ viết tay | df+ = 0, df− ≥ 10 trên corpus | cần bằng chứng âm trong op T | B | corpus loại target; df− ngoài op T không phải ngữ cảnh runtime |
| B (thứ tự enum) | học thứ bậc theo cặp | báo "corpus không đủ" | B | 18 enum; luật đủ dữ liệu khai trước: ≥ 15 enum từ ≥ 10 nhà cung cấp |
| Chọn ngưỡng | kiểm chéo nhóm | dev rồi đổi sang kiểm chéo | kiểm chéo nhóm cho phép đo; ngưỡng cố định khai trước | 6 op T ở dev; ngưỡng cố định bớt một bậc tự do |
| Cỡ mẫu hiệu dụng | ~28 API | 28–45 tuỳ perms | ghi 28–45 | phụ thuộc định nghĩa |
| B thứ hạng | viết tay 19/29, R4 13/29 | đã rút câu 5/8 | A | B tự sửa ở vòng 2 |
| Op thiếu body | 42 | 11–12 đáng ngờ | B | A tính cả op khớp chữ `admin` trong path |

## 3. Quyết định làm ngay (không sửa mã EvoMaster)

1. Gán lại toàn bộ 3.823 op ghi của hai vòng theo một luật duy nhất, mức op (W4, W8–W10): mỗi op một dòng, kể cả âm.
2. Rút theo luật mới khai trước (W2, W3, W11), đếm theo nhà cung cấp trong op T, từ viết tay qua cùng luật.
3. Đo bằng mô phỏng runtime (nền `A/work/w07`), kiểm chéo nhóm theo nhà cung cấp trên 228 nhà cung cấp, so ghép đôi mức
   API, KTC bootstrap theo nhà cung cấp (W1, W7). Đo thêm tác dụng phụ điểm transition (W5).
4. Phân xử chỗ lệch L1/L2 bằng một phiên mới mù nguồn, từng dòng có lý do.

Chưa làm đêm nay, ghi thành việc còn lại: chuẩn từ mã nguồn API mở để đo độ đúng của nhãn (A-B2c, B-B4); bốc spec mới
ngoài APIs.guru; chạy EvoMaster với các phiên bản danh sách.
