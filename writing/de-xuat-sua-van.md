# Đề xuất sửa văn khóa luận, bản PDF ngày 23/11/2026

Danh sách câu đề xuất sửa trong `writing/KLTN_NguyenLeMinh.pdf`. Trang là số in ở chân trang. Câu viết theo chữ hiển thị trên PDF: `Mục 2.1`, `Hình 1.1` là tham chiếu chéo, `[sahin2024bola]` là trích dẫn. Góp ý theo số mục.

Mỗi mục được gắn một hoặc nhiều nhãn lỗi:

- `:` là dấu hai chấm đặt giữa câu;
- `V/A` là lẫn tiếng Việt và tiếng Anh trong tên thuật ngữ;
- `()` là ngoặc giải thích lặp lại hoặc thừa.

## Quy ước áp dụng

- Dấu `:` chỉ dùng trước danh sách xuống dòng, trước câu trích nguyên văn, và trong nhãn của bảng hoặc hình.
- Thuật ngữ thân bài dùng bằng tiếng Anh thì tên Anh đứng ngoài, chú giải tiếng Việt nằm trong ngoặc.
- Mỗi thuật ngữ chỉ được giải thích bằng ngoặc một lần, ở lần xuất hiện đầu tiên. Tóm tắt đọc độc lập nên có chú giải riêng.
- Bốn bước của kịch bản kiểm thử là setup, source, transition, follow-up. Chú giải cho source, transition, follow-up đặt ở Mục 1.4. Setup xuất hiện lần đầu ở Mục 3.3.1 nên chú giải ở đó.
- `transition` là lời gọi hạ quyền trong một bộ ba. "Thao tác chuyển trạng thái" là thao tác ứng viên mà mô hình xếp hạng (Mục 3.4, Chương 5), nên giữ nguyên.
- Thuật toán 3.1 giữ mã giả tiếng Anh.

## Tóm tắt

### 1. tr.ii · `abstract_vi.tex:11` · `:`

- Hiện tại: Giải pháp dựa trên quan hệ MR-A1: nếu một thao tác cần đúng quyền vừa bị thu hồi và đã thành công trước khi tài khoản bị hạ quyền, thì khi gửi lại bằng cùng token sau đó, thao tác phải bị từ chối.
- Đề xuất: Giải pháp dựa trên quan hệ MR-A1, theo đó nếu một thao tác cần đúng quyền vừa bị thu hồi và đã thành công trước khi tài khoản bị hạ quyền, thì thao tác đó phải bị từ chối khi được gửi lại bằng cùng token sau lần hạ quyền.

### 2. tr.ii · `abstract_vi.tex:11` · `:` `V/A`

- Hiện tại: Mỗi kịch bản kiểm thử gồm bộ ba thao tác: thao tác gốc, thao tác chuyển trạng thái và thao tác kiểm chứng.
- Đề xuất: Mỗi kịch bản kiểm thử gồm bộ ba thao tác source (thao tác gốc), transition (thao tác chuyển trạng thái) và follow-up (thao tác kiểm chứng).

### 3. tr.ii · `abstract_vi.tex:11` · `V/A`

- Hiện tại: Khi thao tác kiểm chứng thành công, bước đăng nhập lại loại các bộ ba mà thao tác chuyển trạng thái chưa được xác nhận là hạ quyền.
- Đề xuất: Khi follow-up thành công, bước đăng nhập lại loại các bộ ba có transition chưa được xác nhận là hạ quyền.

## Danh mục viết tắt

### 4. tr.viii · `abbreviations.tex:28` · `:`

- Hiện tại: Quan hệ biến hình: thao tác cần quyền đã thu hồi phải bị từ chối khi dùng lại thông tin xác thực cũ
- Đề xuất: Quan hệ biến hình, theo đó thao tác cần quyền đã thu hồi phải bị từ chối khi dùng lại thông tin xác thực cũ

## Chương 1

### 5. tr.1 · `chapter1.tex:13` · `()`

- Hiện tại: Các oracle phân quyền hiện có trong EvoMaster (oracle là cơ chế phán quyết kết quả kiểm thử) đối chiếu hành vi giữa các tài khoản có quyền khác nhau [sahin2024bola].
- Đề xuất: Các oracle phân quyền hiện có trong EvoMaster đối chiếu hành vi giữa các tài khoản có quyền khác nhau [sahin2024bola].
- Ghi chú: oracle đã được định nghĩa ở Mục 2.2 và trong danh mục viết tắt.

### 6. tr.1 · `chapter1.tex:13` · `()`

- Hiện tại: Khóa luận chạy nhánh chính của EvoMaster upstream (bản do các tác giả EvoMaster duy trì) trên hai ứng dụng mang lỗi phân quyền có trạng thái.
- Đề xuất: Khóa luận chạy nhánh chính của EvoMaster upstream trên hai ứng dụng mang lỗi phân quyền có trạng thái.
- Ghi chú: câu này kết đoạn mà chưa nêu kết quả. Nếu muốn thêm, Mục 5.6 có sẵn kết quả: không mã lỗi nào báo quyền còn sót lại sau lần hạ quyền.

### 7. tr.2 · `chapter1.tex:18` · `:`

- Hiện tại: Hình 1.1 minh họa ba giai đoạn của lỗ hổng: thao tác ghi ban đầu, thao tác hạ quyền và tái sử dụng token cũ.
- Đề xuất: Hình 1.1 minh họa ba giai đoạn của lỗ hổng, gồm thao tác ghi ban đầu, thao tác hạ quyền và tái sử dụng token cũ.

### 8. tr.3 · `chapter1.tex:48` · `V/A`

- Hiện tại: Quan hệ được cài đặt bằng bộ ba thao tác gồm thao tác gốc (source), thao tác chuyển trạng thái (transition) và thao tác kiểm chứng (follow-up), cùng điều kiện tiền đề.
- Đề xuất: Quan hệ được cài đặt bằng bộ ba thao tác gồm source (thao tác gốc), transition (thao tác chuyển trạng thái) và follow-up (thao tác kiểm chứng), cùng điều kiện tiền đề.
- Ghi chú: đây là chỗ duy nhất giữ chú giải cho ba tên này trong thân bài.

### 9. tr.4 · `chapter1.tex:51` · `:`

- Hiện tại: Hai ứng dụng còn lại là ứng dụng mã nguồn mở mang lỗi thật: pyLoad với lỗ hổng CVE-2026-41133, và artifact-keeper với một lỗi đã được nhà phát triển vá.
- Đề xuất: pyLoad và artifact-keeper là hai ứng dụng mã nguồn mở mang lỗi thật, lần lượt là lỗ hổng CVE-2026-41133 và một lỗi đã được nhà phát triển vá.

## Chương 2

### 10. tr.5 · `chapter2.tex:4` · `:`

- Hiện tại: Phát hiện vi phạm phân quyền sau khi quyền thay đổi cần kết hợp ba nền tảng: kiểm thử REST API dựa trên tìm kiếm, kiểm thử biến hình và kiểm soát truy cập.
- Đề xuất: Phát hiện vi phạm phân quyền sau khi quyền thay đổi cần kết hợp ba nền tảng là kiểm thử REST API dựa trên tìm kiếm, kiểm thử biến hình và kiểm soát truy cập.

### 11. tr.6 · `chapter2.tex:15` · `:`

- Hiện tại: Khi pha kiểm thử bảo mật được bật, EvoMaster ghi thêm mục tiêu theo tài khoản: một tài khoản gọi một thao tác và nhận kết quả 2xx, 401 hoặc 403.
- Đề xuất: Khi pha kiểm thử bảo mật được bật, EvoMaster ghi thêm mục tiêu theo tài khoản. Mỗi mục tiêu loại này là một tài khoản gọi một thao tác và nhận kết quả 2xx, 401 hoặc 403.

### 12. tr.7 · `chapter2.tex:39` · `()`

- Hiện tại: Một quan hệ biến hình (metamorphic relation) phát biểu mối liên hệ kỳ vọng giữa đầu vào và đầu ra của các lần thực thi đó.
- Đề xuất: Một quan hệ biến hình phát biểu mối liên hệ kỳ vọng giữa đầu vào và đầu ra của các lần thực thi đó.
- Ghi chú: giữ ngoặc ở lần dùng đầu tiên, Mục 1.3, tr.3.

### 13. tr.8 · `chapter2.tex:44` · `()`

- Hiện tại: Lớp lỗi khóa luận xét gần nhất với mục API5 (BFLA) của danh sách, vì sau khi bị hạ quyền, tài khoản đã là người dùng thường nhưng vẫn gọi được chức năng của quản trị viên.
- Đề xuất: Lớp lỗi khóa luận xét gần nhất với BFLA, mục API5 của danh sách, vì sau khi bị hạ quyền, tài khoản đã là người dùng thường nhưng vẫn gọi được chức năng của quản trị viên.

### 14. tr.8 · `chapter2.tex:46` · `()` · đi cùng mục 33

- Hiện tại: Với token JWT, máy chủ ghi tên tài khoản và các thuộc tính như vai trò vào phần claim của token rồi ký token [rfc7519].
- Đề xuất: Với token JWT, máy chủ ghi tên tài khoản và các thuộc tính như vai trò vào các claim, tức các trường thông tin mang trong token, rồi ký token [rfc7519].
- Ghi chú: claim xuất hiện lần đầu ở câu này, còn lời giải thích hiện nằm ở tr.29.

### 15. tr.8 · `chapter2.tex:50` · `()`

- Hiện tại: Khác với các oracle này, khóa luận xét lỗ hổng phân quyền có trạng thái (Stateful Broken Access Control), khi cùng một chủ thể vẫn được chấp nhận sau khi quyền bị thu hồi.
- Đề xuất: Khác với các oracle này, khóa luận xét lỗ hổng phân quyền có trạng thái, khi cùng một chủ thể vẫn được chấp nhận sau khi quyền bị thu hồi.
- Ghi chú: giữ ngoặc ở Mục 1.1, tr.1.

### 16. tr.8 · `chapter2.tex:50` · `:` · đề xuất giữ

- Hiện tại: Theo mục 6.1.1 của bản dự thảo, bên triển khai có thể chọn cách xử lý các phiên đang mở có vai trò bị hủy gán: *"The RBAC system could wait for such a session to terminate normally, could force its termination, or could inactivate the role"*.
- Đề xuất: giữ nguyên, vì dấu `:` ở đây dẫn vào câu trích nguyên văn.

### 17. tr.9 · `chapter2.tex:55` · `V/A`

- Hiện tại: Nhóm oracle này có sẵn trong EvoMaster và là phương án đối sánh (baseline) của khóa luận.
- Đề xuất: Nhóm oracle này có sẵn trong EvoMaster và là baseline (phương án đối sánh) của khóa luận.
- Ghi chú: Chương 5 dùng "baseline".

## Chương 3

### 18. tr.10 · `chapter3.tex:8` · `()`

- Hiện tại: Chương này trình bày phương pháp từ quan hệ biến hình (metamorphic relation) MR-A1 đến kịch bản kiểm thử chạy được trong EvoMaster.
- Đề xuất: Chương này trình bày phương pháp từ quan hệ biến hình MR-A1 đến kịch bản kiểm thử chạy được trong EvoMaster.

### 19. tr.10 · `chapter3.tex:17` · `()`

- Hiện tại: Bộ dựng tạo các bộ ba thao tác [source/transition/follow-up] và giữ những bộ ba thỏa mãn các điều kiện ở Mục 3.3.3.
- Đề xuất: Bộ dựng tạo các bộ ba thao tác source, transition, follow-up và giữ những bộ ba thỏa mãn các điều kiện ở Mục 3.3.3.

### 20. tr.10 · `chapter3.tex:29` · `()`

- Hiện tại: MR-A1 là một quan hệ biến hình (Mục 2.2) giữa hai lần thực hiện một thao tác, trước và sau khi thu hồi quyền.
- Đề xuất: MR-A1 là một quan hệ biến hình giữa hai lần thực hiện một thao tác, trước và sau khi thu hồi quyền.
- Ghi chú: Mục 3.1, cùng trang, đã trỏ tới Mục 2.2.

### 21. tr.12 · `chapter3.tex:31` · `()`

- Hiện tại: Trạng thái s là cấu hình phân quyền của hệ thống tại lúc quan sát, và một tài khoản quản trị đổi trạng thái này bằng thao tác T (transition) để hạ vai trò hoặc thu hồi quyền của p.
- Đề xuất: Trạng thái s là cấu hình phân quyền của hệ thống tại lúc quan sát, và một tài khoản quản trị đổi trạng thái này bằng transition T để hạ vai trò hoặc thu hồi quyền của p.

### 22. tr.14 · `chapter3.tex:97–100` · `V/A` `()`

Hiện tại:

1. Khởi tạo (setup): các lời gọi trong ca kiểm thử ban đầu của nạn nhân, chạy trước thao tác gốc để tạo tài nguyên cần thao tác. Bước này không bắt buộc nếu tài nguyên đã có sẵn trong hệ thống.
2. Source (thao tác gốc): tài khoản nạn nhân, trước khi bị hạ quyền, gọi một thao tác ghi có kiểm soát phân quyền và nhận mã 2xx.
3. Transition (thao tác chuyển trạng thái): tài khoản quản trị hạ vai trò hoặc thu hồi quyền tương ứng của nạn nhân.
4. Follow-up (thao tác kiểm chứng): nạn nhân gọi lại thao tác source với cùng tham số và cùng token cũ.

Đề xuất:

1. Setup (khởi tạo): các lời gọi trong ca kiểm thử ban đầu của nạn nhân, chạy trước source để tạo tài nguyên cần thao tác. Bước này không bắt buộc nếu tài nguyên đã có sẵn trong hệ thống.
2. Source: tài khoản nạn nhân, trước khi bị hạ quyền, gọi một thao tác ghi có kiểm soát phân quyền và nhận mã 2xx.
3. Transition: tài khoản quản trị hạ vai trò hoặc thu hồi quyền tương ứng của nạn nhân.
4. Follow-up: nạn nhân gọi lại source với cùng tham số và cùng token cũ.

- Ghi chú: thân bài vẫn gọi bước đầu là "lời gọi khởi tạo"; Thuật toán 3.1 đã viết "setup of a".

### 23. tr.16 · `chapter3.tex:138` · `:`

- Hiện tại: Mỗi trường vai trò khi đó nhận giá trị nâng quyền theo kiểu của trường: trường liệt kê nhận giá trị mà mô hình chấm quyền cao nhất, trường logic nhận `true` và trường số nhận `0`.
- Đề xuất: Giá trị nâng quyền khi đó phụ thuộc kiểu của trường vai trò. Trường liệt kê nhận giá trị mà mô hình chấm quyền cao nhất, trường logic nhận `true` và trường số nhận `0`.

### 24. tr.17 · `chapter3.tex:152` · `:`

- Hiện tại: Bộ dựng ước lượng điều kiện này bằng dấu hiệu HTTP ở hai thời điểm: khi chọn source và ở bước đăng nhập lại.
- Đề xuất: Bộ dựng ước lượng điều kiện này bằng dấu hiệu HTTP ở hai thời điểm là lúc chọn source và lúc chạy bước đăng nhập lại.

### 25. tr.19 · `chapter3.tex:195` · `V/A` `()`

- Hiện tại: Khi một lần thử thất bại, bộ dựng chọn bước kế tiếp dựa trên mã trạng thái của source và của thao tác chuyển trạng thái (Bảng 3.4).
- Đề xuất: Khi một lần thử thất bại, bộ dựng chọn bước kế tiếp dựa trên mã trạng thái của source và của transition (Bảng 3.4).

### 26. tr.19 · `chapter3.tex:195` · `()`

- Hiện tại: Các luật ở Bảng 3.4 cho phép bỏ qua ứng viên hoặc cặp thao tác chuyển trạng thái và nạn nhân dựa trên các phản hồi đã quan sát.
- Đề xuất: Các luật trong bảng cho phép bỏ qua ứng viên hoặc cặp thao tác chuyển trạng thái và nạn nhân dựa trên các phản hồi đã quan sát.
- Ghi chú: mục 25, cách câu này một câu, đã trỏ tới Bảng 3.4.

### 27. tr.21 · `chapter3.tex:258` · `:`

- Hiện tại: Điểm của một thao tác op được tính theo Công thức 3.2:
- Đề xuất: Điểm của một thao tác op được tính theo Công thức 3.2.
- Ghi chú: câu dẫn vào Công thức 3.1 ở tr.12 kết bằng dấu chấm.

## Chương 4

### 28. tr.23 · `chapter4.tex:9` · `()`

- Hiện tại: Phần mở rộng của Oracle 970 được viết bằng Kotlin (ngôn ngữ của phần core EvoMaster), ngay trong mã nguồn EvoMaster 6.1.1 [evomaster611].
- Đề xuất: Phần mở rộng của Oracle 970 được viết bằng Kotlin, ngay trong mã nguồn EvoMaster 6.1.1 [evomaster611].

### 29. tr.23 · `chapter4.tex:14` · `()`

- Hiện tại: Phần mở rộng chạy ở pha kiểm thử bảo mật, sau pha tìm kiếm và pha rút gọn (Mục 2.1).
- Đề xuất: Phần mở rộng chạy ở pha kiểm thử bảo mật, sau pha tìm kiếm và pha rút gọn.
- Ghi chú: câu cuối của đoạn ngay trên đã trỏ tới Mục 2.1.

### 30. tr.27 · `chapter4.tex:147` · `()`

- Hiện tại: Bộ ba dựa vào cơ chế xác thực có sẵn của EvoMaster (Mục 2.1).
- Đề xuất: Bộ ba dựa vào cơ chế xác thực có sẵn của EvoMaster.
- Ghi chú: Mục 3.3.1 ở tr.14 đã giải thích vì sao follow-up dùng lại được token cũ.

### 31. tr.27 · `chapter4.tex:156` · `V/A`

- Hiện tại: Source và follow-up là `POST /api/v1/admin/analytics/snapshot`, còn thao tác chuyển trạng thái là `PATCH /api/v1/users/{id}`, với `id` của nạn nhân.
- Đề xuất: Source và follow-up là `POST /api/v1/admin/analytics/snapshot`, còn transition là `PATCH /api/v1/users/{id}`, với `id` của nạn nhân.

### 32. tr.28 · `chapter4.tex:158–160` · `:` `V/A`

Hiện tại:

- Ca 1 chứa bộ ba: source và follow-up dùng token T1 của nạn nhân, thao tác chuyển trạng thái dùng token T2 của tài khoản quản trị. Cả ba lời gọi nhận 200, và bộ phán quyết gắn lỗi 970 vào follow-up.
- Ca 2 là ca đăng nhập lại: source được gửi với token mới T3 của nạn nhân và nhận 403.
- Ca 3 là ca đối chứng ẩn danh: source được gửi không kèm token và nhận 401.

Đề xuất:

- Ca 1 chứa bộ ba. Source và follow-up dùng token T1 của nạn nhân, còn transition dùng token T2 của tài khoản quản trị. Cả ba lời gọi nhận 200, và bộ phán quyết gắn lỗi 970 vào follow-up.
- Ca 2 là ca đăng nhập lại. Source được gửi với token mới T3 của nạn nhân và nhận 403.
- Ca 3 là ca đối chứng ẩn danh. Source được gửi không kèm token và nhận 401.

### 33. tr.29 · `chapter4.tex:197` · `()` · đi cùng mục 14

- Hiện tại: Ở biến thể có lỗ hổng, máy chủ đọc vai trò từ claim (trường thông tin mang trong JWT) thay vì tra vai trò hiện tại trong cơ sở dữ liệu, nên với token cấp trước khi đổi vai trò, tài khoản đã bị hạ quyền vẫn ghi được dữ liệu.
- Đề xuất: Ở biến thể có lỗ hổng, máy chủ đọc vai trò từ claim của JWT thay vì tra vai trò hiện tại trong cơ sở dữ liệu, nên với token cấp trước khi đổi vai trò, tài khoản đã bị hạ quyền vẫn ghi được dữ liệu.

### 34. tr.29 · `chapter4.tex:204` · `()`

- Hiện tại: Bản fork (bản sao tách nhánh) vampi-seeded của dự án mã nguồn mở VAmPI dùng để thử Oracle 970 trên mã nguồn của bên thứ ba, và bản fork cũng dùng để thử công cụ với quy ước đặt đường dẫn của dự án.
- Đề xuất: Bản fork vampi-seeded của dự án mã nguồn mở VAmPI dùng để thử Oracle 970 trên mã nguồn của bên thứ ba và để thử công cụ với quy ước đặt đường dẫn của dự án.

### 35. tr.31 · `chapter4.tex:250` · `()`

- Hiện tại: Máy chủ lưu trữ gói phần mềm (artifact registry) artifact-keeper là dự án mã nguồn mở viết bằng Rust [artifactkeeper1821].
- Đề xuất: Máy chủ lưu trữ gói phần mềm artifact-keeper là dự án mã nguồn mở viết bằng Rust [artifactkeeper1821].
- Ghi chú: giữ ngoặc ở Mục 1.1, tr.1.

### 36. tr.31 · `chapter4.tex:254` · `()`

- Hiện tại: Nạn nhân là `victim`, tài khoản quản trị là `operator` (tên đăng nhập `admin`), và hai tài khoản đăng nhập qua `POST /api/v1/auth/login` để nhận token JWT.
- Đề xuất: Nạn nhân là `victim`, tài khoản quản trị là `operator`, và hai tài khoản đăng nhập qua `POST /api/v1/auth/login` để nhận token JWT.
- Ghi chú: giữ ngoặc ở Mục 4.1.3, tr.27.

## Chương 5

### 37. tr.33 · `chapter5.tex:8` · `:`

- Hiện tại: Chương này đánh giá năm vấn đề: số lượt Oracle 970 phát hiện vi phạm trên biến thể có lỗ hổng và số lượt báo động giả trên biến thể đã vá, khả năng tự nhận diện thao tác chuyển trạng thái từ đặc tả, khả năng phát hiện lỗi thật do nhà phát triển khác viết, nguyên nhân của các lượt bỏ sót, và kết quả của EvoMaster khi không kèm Oracle 970 trên cùng lớp lỗi.

Đề xuất, chuyển thành danh sách xuống dòng:

Chương này đánh giá năm vấn đề:

1. số lượt Oracle 970 phát hiện vi phạm trên biến thể có lỗ hổng và số lượt báo động giả trên biến thể đã vá;
2. khả năng tự nhận diện thao tác chuyển trạng thái từ đặc tả;
3. khả năng phát hiện lỗi thật do nhà phát triển khác viết;
4. nguyên nhân của các lượt bỏ sót;
5. kết quả của EvoMaster khi không kèm Oracle 970 trên cùng lớp lỗi.

### 38. tr.33 · `chapter5.tex:13` · `()`

- Hiện tại: Biến thể có lỗ hổng dùng để đo tỷ lệ phát hiện vi phạm phân quyền có trạng thái, còn trên biến thể đã vá, mọi cảnh báo phát sinh đều được tính là báo động giả (false positive, FP).
- Đề xuất: Biến thể có lỗ hổng dùng để đo tỷ lệ phát hiện vi phạm phân quyền có trạng thái, còn trên biến thể đã vá, mọi cảnh báo phát sinh đều được tính là báo động giả.
- Ghi chú: Mục 5.2 ở tr.34 chú giải FP cùng TP, FN, TN; danh mục viết tắt có "False Positive".

### 39. tr.36 · `chapter5.tex:109` · `:`

- Hiện tại: Người dùng không phải khai báo thao tác hạ quyền: mô hình xếp thao tác thật ở hạng 1 với ba ứng dụng và hạng 3 với artifact-keeper, sau đó bộ dựng tự chọn được thao tác này khi chạy trên cả bốn ứng dụng.
- Đề xuất: Người dùng không phải khai báo thao tác hạ quyền. Mô hình xếp thao tác thật ở hạng 1 với ba ứng dụng và hạng 3 với artifact-keeper, sau đó bộ dựng tự chọn được thao tác này khi chạy trên cả bốn ứng dụng.

### 40. tr.37 · `chapter5.tex:127` · `:`

- Hiện tại: Hai nhóm còn lại thuộc vampi-seeded: 8 lượt có lần thử nhưng mọi lần thử đều bị hủy, và 6 lượt bộ dựng không thử lần nào, với nhật ký ở mức mặc định của EvoMaster không ghi lý do cụ thể.
- Đề xuất: Hai nhóm còn lại thuộc vampi-seeded. Nhóm thứ hai gồm 8 lượt có lần thử nhưng mọi lần thử đều bị hủy. Nhóm thứ ba gồm 6 lượt mà bộ dựng không thử lần nào, và nhật ký ở mức mặc định của EvoMaster không ghi lý do cụ thể.
- Ghi chú: hai câu trước đó đã mở bằng "Nhóm thứ nhất gồm 8 lượt…".

### 41. tr.37 · `chapter5.tex:129` · `()` `V/A`

- Hiện tại: Ở 8 lượt vampi-seeded có lần thử, bộ dựng hủy tổng cộng 21 lần thử, trong đó 10 lần vì source nhận mã 401 (token của nạn nhân bị từ chối) và 11 lần vì thao tác chuyển trạng thái nhận mã 401 (token của tài khoản quản trị bị từ chối).
- Đề xuất: Ở 8 lượt vampi-seeded có lần thử, bộ dựng hủy tổng cộng 21 lần thử, trong đó 10 lần vì source của nạn nhân nhận mã 401 và 11 lần vì transition của tài khoản quản trị nhận mã 401.

### 42. tr.39 · `chapter5.tex:172` · `:`

- Hiện tại: Ở seed 11 trên reports-api, ca `test_25` chỉ có một lời gọi: `superadmin` gửi `PUT /users/alice/role` với vai trò `VIEWER` và nhận mã 200.
- Đề xuất: Ở seed 11 trên reports-api, ca `test_25` chỉ gồm lời gọi `PUT /users/alice/role` do `superadmin` gửi với vai trò `VIEWER`, và lời gọi này nhận mã 200.

## Chương 6

### 43. tr.41 · `chapter6.tex:17` · `:` `()`

- Hiện tại: Thứ tư, trong 100 lượt chạy, Oracle 970 báo vi phạm ở 28/50 lượt trên biến thể có lỗ hổng: 12/20 với reports-api, 6/20 với vampi-seeded, 5/5 với pyLoad và 5/5 với artifact-keeper. Trong 50 lượt trên biến thể đã vá, công cụ dựng được bộ ba ở 31 lượt và không báo động giả ở lượt nào. Lỗi trên pyLoad (CVE-2026-41133) và artifact-keeper nằm trong mã của nhà phát triển ứng dụng.
- Đề xuất: Thứ tư, trong 100 lượt chạy, Oracle 970 báo vi phạm ở 28/50 lượt trên biến thể có lỗ hổng, gồm 12/20 với reports-api, 6/20 với vampi-seeded, 5/5 với pyLoad và 5/5 với artifact-keeper. Trong 50 lượt trên biến thể đã vá, công cụ dựng được bộ ba ở 31 lượt và không báo động giả ở lượt nào. Lỗi trên pyLoad và artifact-keeper nằm trong mã của nhà phát triển ứng dụng.
- Ghi chú: mã CVE đã nêu ở tóm tắt, Mục 1.1, 1.4 và 4.2.3.
