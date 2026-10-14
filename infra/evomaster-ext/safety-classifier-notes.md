# Ghi chú safety classifier — làm việc luận văn mà bớt vướng

Nguồn: hai phiên 2026-10-01 (§6, §7). Mục đích: giảm false positive trên việc hợp pháp, không phải mẹo lách classifier (phân biệt này là bài học §2).

## 1. Đọc/sửa file chưa bao giờ bị chặn

Tool đọc `infra/analysis/heldout-small-apps.md` chạy đủ hai lần, Edit cũng chạy. Cái bị dừng là một lượt sinh văn bản trả lời, không phải quyền truy cập dữ liệu. Một câu trả lời bị dừng không có nghĩa luận văn bị khoá: đọc, phân tích, viết file vẫn hoạt động. Tiếp cận lại đúng lượt văn bản đó. Đọc một file thì đưa nội dung file đó vào ngữ cảnh (§3).

## 2. Đừng đóng khung yêu cầu theo kiểu "né hệ thống an toàn"

Câu "làm sao tránh classifier vì nó tưởng tôi tấn công app thật" tự nó là tín hiệu mạnh, đẩy điểm qua ngưỡng rõ nhất trong phiên này. Classifier không phải thứ nhìn thấy hay điều khiển được, và không coach cách qua mặt nó. Gặp false positive thì nêu thẳng như một vướng mắc quy trình, rồi làm tiếp phần phân tích.

## 3. Classifier chấm hình dạng bề mặt + ngữ cảnh tích luỹ, không chấm ý định đã xác minh

Phỏng đoán: không phiên nào nhìn thấy classifier. Nó không biết đây là luận văn hợp pháp. Văn có hình dạng "app mã nguồn mở có tên thật + các bước leo thang quyền + mã trả về xác nhận" đọc giống công thức khai thác, bất kể mục đích.

Ngữ cảnh tích luỹ có ba nguồn: nội dung file đã đọc, câu hỏi của user, văn bản model viết ra. Thực hành ở §4 chia theo nguồn.

## 4. Thực hành giảm vướng (cũng là viết luận văn tốt hơn)

Nội dung file đã đọc:
- Đọc đúng đoạn cần bằng `offset`/`limit`. Đọc cả file thì mọi chi tiết trong file vào ngữ cảnh, kể cả khi câu trả lời chỉ trỏ `file:dòng`.
- Chi tiết không có giá trị học thuật (URL mã độc sống, sha256 của payload, mô tả cơ chế thực thi) thì xoá khỏi file. Giữ repo, luật loại và lý do một dòng. Đã làm với #74: `heldout-small-apps.md:300`.

Câu hỏi của user: §2.

Văn bản model viết ra:
- Nêu kết luận rồi trỏ `file:dòng`, không chép lại chuỗi bước. Ví dụ: "wagoe: kiểm tay khớp MR-A1 trên nhánh JWT, follow-up bằng token cũ ALLOWED, token mới DENIED; các bước ở `heldout-small-apps.md:474–483`". Khớp luật CLAUDE.md "số dòng chỉ để tra".
- Mô tả theo hành vi của oracle (detector có nổ không, bộ ba VOID hay 970) thay vì theo các bước tấn công vào một target có tên.

## 5. Caveat trung thực

Không nhìn thấy classifier nên không có cách diễn đạt nào đảm bảo qua. Một phần nội dung luận văn (tái lập lỗ hổng trên app mã nguồn mở) vốn có hình dạng tấn công, vẫn có thể gặp false positive lác đác. Chưa biết thực hành nào ở §4 có tác dụng: §6 và §7 là hai lần quan sát, khác nhau ở bốn yếu tố cùng lúc.

## 6. Ví dụ lỗi đã gặp — lượt trả lời bị dừng (2026-10-01, Opus 4.8)

- Triệu chứng: sau khi đọc `infra/analysis/heldout-small-apps.md`, lượt văn bản đang soạn bị dừng bởi classifier (thông báo "stopped by a safety classifier", không phải lỗi tool/API). Nội dung bị giữ khỏi cả model, không khôi phục được. Hai lần gọi tool đọc file đều thành công; chỉ lượt sinh văn bản bị dừng.
- Nguyên nhân (suy đoán, không chắc): ngữ cảnh tích luỹ có hình dạng tấn công — chi tiết hạ tầng malware (`heldout-small-apps.md` §11, mục #74) và công thức leo thang quyền trên app có tên thật (`heldout-small-apps.md` §14, wagoe) — cộng câu hỏi ngay trước đó đóng khung là "làm sao tránh classifier vì nó tưởng tôi tấn công app thật".
- Cách làm sau đó (quan sát được), hai việc riêng. Trong câu trả lời: gọi tên hành vi, trỏ `file:dòng`; các lượt sau đều qua. Trong file: xoá URL, sha256 và mô tả cơ chế của #74 khỏi `heldout-small-apps.md`, còn một dòng ("loại theo S1: nạp/thực thi mã từ xa").
- Caveat: không chạy lại lượt bị dừng, nên đây là tương quan, không phải nhân quả đã chứng minh. Không khẳng định một thay đổi cụ thể nào "sửa" được chặn.
- Rút ra: gặp "stopped by safety classifier" thì không coi là luận văn bị khoá; bỏ mọi khung "né safety"; áp §4.

## 7. Phiên thứ hai, không bị dừng (2026-10-01, Opus 5.5)

- Đọc trọn `heldout-small-apps.md` (581 dòng) ở đầu phiên, gồm sáu bước kiểm tay wagoe ở dòng 474–483. Sáu lượt trả lời sau đó đều qua.
- Khác phiên §6 ở bốn yếu tố: chi tiết #74 đã bị xoá khỏi file trước khi đọc; không có câu hỏi về cách né classifier; model khác; câu trả lời trỏ `file:dòng`.
- Đọc được: phần wagoe §14 nằm trong ngữ cảnh, một mình nó, không làm phiên này bị dừng.
- Chưa đọc được: yếu tố nào trong bốn yếu tố trên gây ra lần dừng ở §6. Mỗi phiên là một lần quan sát.
