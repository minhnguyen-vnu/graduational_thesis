# Chương 3. Phương pháp đề xuất: câu hỏi hội đồng

Đoạn đầu mỗi câu là câu trả lời nói trong khoảng 30 giây. Phần sau dùng khi bị hỏi tiếp. Dòng `Nguồn` để tự tra lại.
`B:` là `EvoMaster/core/src/main/kotlin/org/evomaster/core/problem/rest/service/RestSecurityBuilder.kt`, `O:` là
`.../problem/rest/oracle/RestSecurityOracle.kt`, repo `/Users/minhnguyen/IdeaProjects/EvoMaster`, HEAD `9c4be5b1dc`.
Mã được trỏ bằng tên hàm, vì cây làm việc còn các dòng `// THESIS` chưa commit nên số dòng lệch với HEAD.

Ví dụ dùng xuyên chương: reports-api bản lỗi, seed 1, jar M2. Test:
`infra/em-results/m2-wave1-20261108/tests/t1-vuln-seed1/EvoMaster_faults_Test.py`; log:
`infra/em-results/m2-wave1-20261108/logs/t1-vuln-seed1.log:570–573`.

## Khái niệm phải giải thích được

| Khái niệm | Nghĩa | Ví dụ |
|---|---|---|
| Oracle 970 | Bộ phát hiện do khóa luận thêm; gắn lỗi mã 970 vào follow-up của bộ ba vi phạm MR-A1. | Lỗi gắn vào lời gọi thứ tư `PUT /reports/505`. |
| Dải mã 9xx | Dải EvoMaster 6.1.1 dành cho oracle thử nghiệm; chỉ chạy khi bật `--useExperimentalOracles true`. | 970 là số còn trống. |
| Chủ thể p, nạn nhân | Tài khoản bị hạ quyền. | alice. |
| Thông tin xác thực c | Token hoặc cookie phiên cấp lúc đăng nhập. | JWT của alice. |
| Thao tác a | Một lời gọi HTTP: phương thức và đường dẫn mẫu. | `PUT /reports/{id}`. |
| Trạng thái s, s' | Trạng thái phân quyền trên server trước và sau transition. | s: alice là ADMIN; s': alice là VIEWER. |
| Transition T | Thao tác đổi trạng thái phân quyền; ở MR-A1 là hạ quyền. | `PUT /users/alice/role {"role":"VIEWER"}`. |
| Operator | Tài khoản gọi transition. Khóa luận gọi là tài khoản quản trị; trong mã là mọi tài khoản khác nạn nhân. | superadmin. |
| Obs(a, c, s) | Kết quả khi dùng c gọi a ở trạng thái s, đọc từ mã HTTP. | 200 là ALLOWED. |
| ALLOWED, DENIED, INCONCLUSIVE | Lần lượt là 2xx, 403, 401. | 401 không bao giờ là phán quyết. |
| Điều kiện tiền đề Pre(a, T), guard | a cần đúng quyền mà T gỡ. | `GET /reports` không cần ADMIN nên không thỏa. |
| Bộ ba | Source, transition, follow-up. | 200/200/200. |
| Setup | Các lời gọi đứng trước source trong test gốc, thường để tạo tài nguyên. | `POST /reports` 201. |
| Bộ dựng | Phần mã chọn, dựng và chạy bộ ba trong pha bảo mật. | `addForStatefulAccessControl` (B). |
| Bộ phán quyết | Phần mã đọc kết quả test và gắn lỗi 970. | `handleStatefulAuthorization` (O). |
| Bộ ba hợp lệ | Bộ ba qua mọi điều kiện hủy; được đếm và đưa vào kho lưu trữ. | Dòng log `Assembled …`. |
| Bộ ba bị hủy (VOID) | Bộ ba không là bằng chứng cho chiều nào. | pyLoad `200/401/200`. |
| Bước đăng nhập lại (probe C4) | Chạy lại chuỗi của nạn nhân bằng token mới (cần 403), rồi không token (cần mã khác 403). | alice: 403, rồi 401. |
| UNCONFIRMED | Bước đăng nhập lại không xác nhận quyền đã mất; bộ ba bị bỏ. | |
| Khôi phục quyền | Dùng token của nạn nhân nâng lại quyền cho operator đã bị hạ trong pha tìm kiếm. | pyLoad: `pyload` nâng `alice`. |
| N, K, R | Trần số lần thử: 20 bộ ba mỗi pha, 5 lần cho một transition chưa chứng minh, 3 lần khôi phục mỗi transition. | |
| Transition đã chứng minh | Transition đã cho một bộ ba hợp lệ (follow-up 403, hoặc 2xx đã qua bước đăng nhập lại). | `PUT /users/{username}/role` ở seed 1. |
| Naive Bayes | Bộ phân loại xác suất theo định lý Bayes, giả định các đặc trưng độc lập khi biết nhãn. | |
| Đặc trưng | Token tách từ đường dẫn (`p:`), tên trường hoặc tham số (`f:`), và phương thức (`v:`). | `p:role`, `f:username`, `v:PUT`. |
| Tiên nghiệm, hậu nghiệm | Xác suất của lớp trước và sau khi thấy đặc trưng. | Tiên nghiệm M2: ln(209/10.172) = −3,885. |
| Trọng số w(t) | Logarit tỉ lệ tần suất của đặc trưng t giữa lớp T và lớp N. | w(`p:role`) = 2,755. |
| Làm trơn Laplace | Cộng 1 vào tử, 2 vào mẫu để đặc trưng chưa gặp ở một lớp không cho ln 0. | |
| score(op) | Tiên nghiệm cộng trọng số các đặc trưng có mặt; > 0 tương đương hậu nghiệm > 0,5. | `PUT /users/{username}/role`: 7,32. |
| Nhãn T, N | T: thao tác đổi vai trò hay quyền của một tài khoản đã tồn tại, trừ loại chỉ làm quyền tăng. N: phần còn lại. | Thao tác chỉ cấp thêm quyền là N. |
| Nhà cung cấp API | Công ty phát hành spec; dùng để lọc đặc trưng và để tách tập học, tập thi. | |
| M2 | Mô hình Naive Bayes trong jar đo số liệu, học từ nhãn cuối. | sha256 `b2deef150bf8…`. |

## A. Tổng quan và kiến trúc (mục 3.1)

### 3.1 Tóm tắt phương pháp.

Bộ dựng chạy trong pha bảo mật, sau pha tìm kiếm. Nó xếp hạng các thao tác ghi bằng mô hình Naive Bayes để tìm thao tác
hạ quyền, chọn một thao tác ghi bị chặn theo quyền làm source, rồi chạy bộ ba trong một test: nạn nhân ghi, operator hạ
quyền nạn nhân, nạn nhân ghi lại bằng token cũ. Follow-up còn 2xx thì bước đăng nhập lại kiểm quyền đã thật sự mất; qua
được thì 970.
- Ví dụ thật: alice `PUT /reports/505` 200; superadmin `PUT /users/alice/role {"role":"VIEWER"}` 200; alice
  `PUT /reports/505` cùng token 200. Token mới của alice nhận 403, lời gọi không token nhận 401. Kết quả: 970.
- Bản vá cùng seed: `200/200/403`, không báo lỗi.

Nguồn: test và log ở đầu file; `logs/t1-fixed-seed1.log:582`.

### 3.2 Vì sao tách bộ dựng và bộ phán quyết?

Để đếm riêng hai kiểu thất bại: không dựng được bộ ba, và dựng được mà không thấy vi phạm. Trên 50 lượt bản lỗi, 36
lượt dựng được bộ ba và cả 36 báo 970; 14 lượt không dựng được. Mọi FN thuộc kiểu đầu, nên chỗ cần cải thiện là bộ dựng.
- Bộ phán quyết tự tìm lại bộ ba trong test: source đã đăng nhập, 2xx, phương thức ghi; follow-up cùng thao tác, cùng
  tài khoản, 2xx; giữa hai lời gọi có transition của tài khoản khác, 2xx, điểm > 0. Nó chỉ xét test do bộ dựng tạo
  (cờ `statefulTripleUnderEvaluation`); test của pha tìm kiếm không bao giờ bị xét.
- 36/36 "phát hiện khi đã có bộ ba" gần như đúng theo định nghĩa, vì điều kiện hợp lệ dùng chính mã của follow-up.
  Không trích như độ chính xác. Số đo độc lập là 0 báo nhầm trên 30 bộ ba dựng trên mã đã vá.

Nguồn: `docs/results.md` §1a, §2; `infra/evomaster-ext/README.md` §1; `handleStatefulAuthorization` (O).

### 3.3 Oracle 970 khác các oracle so chéo tài khoản ở đâu?

Oracle so chéo dùng nhiều tài khoản tại một thời điểm và hỏi người không có quyền có vào được không. Oracle 970 dùng một
tài khoản ở hai thời điểm, trước và sau khi hạ quyền, cùng token, và hỏi quyền đã gỡ còn được chấp nhận không (bảng 3.2).
- Baseline không phán được: các mã 204–208 so người dùng ở một thời điểm, không có khái niệm quyền vừa bị gỡ.
- Baseline cũng không dựng được: trên vampi-seeded, 0/20 lượt baseline có chuỗi ghi, hạ quyền, ghi lại với cùng biến
  xác thực. Upstream master `ab983ba338`, reports-api bản lỗi, seed 1–20: 0/20 lượt báo lỗi lớp A1.
- 970 không bắt BOLA, BFLA. Hai bên bổ sung nhau.

Nguồn: `docs/results.md` §8.

### 3.4 Vì sao là mã 970?

Xem câu 1.23. Mục 3.1 của khóa luận ghi: EvoMaster 6.1.1 dành dải 9xx cho oracle thử nghiệm, 970 là mã còn trống.

### 3.5 Giải thích hình 3.1.

Cột trái là bộ ba. Sau source và sau transition có câu hỏi "2xx?"; không thì hủy. Follow-up rẽ ba nhánh: 403 là phù hợp
MR-A1, 401 là hủy, 2xx sang bước đăng nhập lại ở cột phải. Bước đó chạy lại chuỗi của nạn nhân bằng token mới (cần
403) và không token (cần mã khác 403). Đạt cả hai thì Oracle 970 báo vi phạm; không thì hủy.
- Nhánh 403 của follow-up gộp cả mã khác (ví dụ 404, 500): bộ ba được giữ, không báo vi phạm. Câu 3.20.

## B. Quan hệ MR-A1 (mục 3.2)

### 3.6 Đọc công thức 3.1 với giá trị thật.

Obs(a, c, s) = ALLOWED ∧ Pre(a, T) ⟹ Obs(a, c, s') = DENIED. Với seed 1: a là `PUT /reports/{id}`, c là JWT của alice,
s là lúc alice còn ADMIN, T là lệnh superadmin hạ alice xuống VIEWER. Vế trái đúng: lần đầu 200, và sửa báo cáo chỉ
ADMIN được làm, đúng quyền T gỡ. Vế phải đòi lần sau là 403. Bản lỗi trả 200 nên vi phạm; bản vá trả 403.
- c giữ nguyên ở cả hai vế. Đổi c thì quan hệ không còn kiểm lỗi này (câu 3.8).

Nguồn: `infra/reports-api/README.md` (bảng quyền); `docs/metamorphic-authz-relations.md` §2.

### 3.7 Vì sao cần điều kiện tiền đề Pre(a, T)?

Bỏ nó thì quan hệ sai. `GET /reports` VIEWER cũng được gọi: trước khi hạ 200, sau khi hạ 200 là đúng, nhưng không có Pre
thì đọc thành lỗi.
- Đã xảy ra thật: khi chưa có guard, 970 nổ trên VAmPI với test không hề có transition (`GET /me`, `GET /_debug` của
  tài khoản khác, rồi `GET /me`). Guard không làm mất TP nào.
- Hộp đen không đọc được Pre; bộ dựng ước lượng nó (câu 3.17).

Nguồn: `docs/metamorphic-authz-relations.md` §2.3; `docs/results.md` §7.

### 3.8 Vì sao follow-up phải dùng token cũ? Đăng nhập lại thì sao?

Lỗi nằm ở token cũ: server đọc vai trò từ token hoặc phiên cấp trước lúc hạ. Đăng nhập lại sau khi hạ thì nhận token
mang vai trò VIEWER, bị từ chối đúng, và lỗi bị che.
- Kịch bản tấn công: người bị hạ quyền giữ token đang có và dùng tiếp tới khi token hết hạn (artifact-keeper: 30 phút).
- Token mới vẫn được dùng, ở một bước khác cho một câu hỏi khác: kiểm quyền đã thật sự mất (câu 3.23).

Nguồn: `docs/metamorphic-authz-relations.md` §2.3; `docs/results.md` §5.

### 3.9 MR-A1 có phải tính đơn điệu không?

Không. Xem câu 2.14. alice sửa được trước và vẫn sửa được sau, nên quyền không tăng. Điều bị vi phạm là việc thực thi
lệnh gỡ quyền trên token đã cấp.

### 3.10 2xx chưa chứng minh dữ liệu đã đổi. Có làm báo nhầm không?

Có thể, nếu app trả 2xx mà bỏ qua thao tác. Khóa luận ghi rõ 2xx chỉ là chấp nhận ở tầng HTTP, và oracle chỉ đọc mã
trạng thái. Trên 30 bộ ba dựng trên mã đã vá không có trường hợp nào như vậy.
- Trên reports-api, test sinh ra còn kiểm thân phản hồi của follow-up: `title` "Report 4", `classification`
  "CONFIDENTIAL", tức thay đổi đã ghi. Phán quyết không dựa vào phần này.
- Kiểm dữ liệu cần biết nghiệp vụ của từng app; một oracle hộp đen dùng chung không có thông tin đó.

Nguồn: test ở đầu file (các dòng `assert res_3`); `docs/results.md` §1.

### 3.11 Vì sao chỉ 403 là DENIED? 401 và 404 thì sao?

Xem câu 1.13. Thêm cho chương này: 401 mang nghĩa khác nhau theo app. pyLoad trả 401 cho phiên không phải admin ở
`/api/*` và 403 ở `/json/*`; VAmPI trả 401 khi token không hợp lệ; bản vá artifact-keeper trả 401 cho token đã thu hồi.
Vì vậy 401 giữ là INCONCLUSIVE, và mã từ chối chưa cấu hình được.
- 404 bị loại vì bốn app kiểm quyền trước khi kiểm tồn tại. reports-api kiểm theo thứ tự 401, 400, 403, 404.

Nguồn: `docs/results.md` §7; `infra/reports-api/README.md`.

### 3.12 Vì sao chỉ viết "có thể thuộc CWE-1464"?

Chuẩn RBAC để phía cài đặt chọn cách xử lý phiên đang mở khi gỡ vai trò: chờ phiên kết thúc, buộc kết thúc, hoặc vô hiệu
vai trò. Vi phạm MR-A1 chỉ là lỗi khi chính sách của app đòi thu hồi có hiệu lực ngay. Bốn app có căn cứ cho chính sách
đó (câu 2.20).

### 3.13 Giải thích hình 3.2.

Hai trạng thái: s (vai trò quản trị, token c) và s' = T(s) (vai trò thấp hơn, vẫn token c). Vòng lặp ở s là source nhận
2xx. Từ s', follow-up 403 là nhánh phù hợp, 2xx là nhánh vi phạm (khung viền đậm).

### 3.14 Tên MR-A1 nghĩa là gì?

Xem câu 1.11. Mục 3.2 của khóa luận ghi: A là nhóm quan hệ phân quyền (authorization), 1 là quan hệ đầu tiên.

## C. Bộ ba và điều kiện tiền đề (mục 3.3)

### 3.15 Bộ ba gồm những lời gọi nào? Cho ví dụ thật.

Test 970 của seed 1 có bốn lời gọi:

| # | Tài khoản | Lời gọi | Mã | Vai trò trong kịch bản |
|---|---|---|---|---|
| 1 | alice | `POST /reports` | 201 | setup: tạo một báo cáo |
| 2 | alice | `PUT /reports/{id}` lên báo cáo đó | 200 | source |
| 3 | superadmin | `PUT /users/alice/role {"role":"VIEWER"}` | 200 | transition |
| 4 | alice, cùng token | `PUT /reports/{id}`, cùng tài nguyên, cùng thân | 200 | follow-up, mang lỗi 970 |

- Lời gọi 1–2 lấy nguyên từ một test trong kho lưu trữ, cắt tới source. Transition là bản sao mới của thao tác, được
  trỏ vào nạn nhân và đặt trường vai trò thành giá trị hạ. Follow-up là bản sao của source.

Nguồn: `executeStatefulAuthzTriple` (B); test ở đầu file.

### 3.16 Follow-up dùng lại token cũ bằng cách nào? Có sửa phần xác thực của EvoMaster không?

Không sửa. EvoMaster đăng nhập mỗi tài khoản một lần ở đầu mỗi test và dùng token đó cho mọi lời gọi trong test
(`AuthUtils.getTokens()`). Đặt cả bộ ba vào một test thì follow-up tự mang token cấp trước transition.
- Jar đo số liệu không thêm tùy chọn dòng lệnh nào; `EMConfig.kt` trùng v6.1.1.
- Hệ quả: muốn có token mới phải chạy một test khác (câu 3.24).
- EvoMaster còn cache token giữa các test, nên target được reseed trước mỗi lượt chạy.

Nguồn: `infra/evomaster-ext/README.md` §2.

### 3.17 Bộ dựng ước lượng Pre(a, T) thế nào?

Bằng dấu hiệu HTTP ở hai thời điểm. Khi chọn source: thao tác từng nhận 403 trong kho lưu trữ, và nạn nhân từng gọi nó
thành công (2xx, có đăng nhập). Ở bước đăng nhập lại: token mới của nạn nhân nhận 403.
- Trong mã, dấu hiệu 403 không lọc theo người gọi: chỉ cần một lời gọi tới thao tác đó nhận 403. Với thao tác chưa
  có 403, bước sinh 403 của pha bảo mật tạo thêm: nó lấy test có 2xx rồi gửi lại bằng tài khoản khác. Mục 3.3.2 viết đúng như vậy.
- Cặp 403 và 2xx chỉ là dấu hiệu, vì 403 có thể đến từ quyền sở hữu tài nguyên. Bước đăng nhập lại mới xác nhận.
- Thao tác cùng đường dẫn với transition không được làm source. Bộ phán quyết cũng bỏ source có điểm > 0.

Nguồn: `guardedSources`, `victimSlicesOn`, `expandWithForbidden` (B).

### 3.18 Vì sao ưu tiên PUT, PATCH? Khi nào dùng POST? Sao không dùng DELETE?

Follow-up lặp lại source trên cùng tài nguyên. PUT, PATCH gọi lần hai vẫn có nghĩa; POST thường tạo bản ghi mới hoặc
vướng ràng buộc trùng. POST chỉ được xét khi không thao tác PUT, PATCH nào có 2xx đã đăng nhập. DELETE không bao giờ làm
source: xóa xong thì follow-up không còn tài nguyên.
- Hai app thật rơi vào nhánh POST: pyLoad dùng `POST /json/status`, artifact-keeper dùng
  `POST /api/v1/admin/analytics/snapshot`.
- "Thao tác ghi" ở đây xác định theo phương thức HTTP (PUT, PATCH, POST, DELETE). `POST /json/status` của pyLoad thật
  ra chỉ đọc trạng thái máy chủ, chặn bằng quyền `LIST` (16); sau khi hạ, tài khoản còn `permission=1` (chỉ `ADD`) nên
  bản vá trả 403. Mục 3.3.2 và phụ lục A ghi đúng điều này.

Nguồn: `addForStatefulAccessControl` (bước 4), `guardedSources` (B); `docs/results.md` §4, §5.

### 3.19 Follow-up trỏ cùng tài nguyên hay tài nguyên khác?

Cùng tài nguyên, cùng thân: follow-up là bản sao của source, gắn lại tham số đường dẫn theo source. Ở seed 1, cả hai lời
gọi sửa cùng một báo cáo với cùng `title` và `classification`. PUT ghi đè, nên còn quyền thì lần hai vẫn 2xx.
- `docs/metamorphic-authz-relations.md` §3 và §5.4 còn ghi follow-up dùng tài nguyên khác. Mã dùng cùng tài nguyên, và
  khóa luận viết theo mã.

Nguồn: `executeStatefulAuthzTriple` (B), dòng `followUp.bindBasedOn(source.path, …)`.

### 3.20 Khi nào bộ ba bị hủy?

Theo mã: source không 2xx, transition không 2xx, follow-up không ghi được mã, hoặc follow-up 401. Follow-up 2xx mà bước
đăng nhập lại không xác nhận thì cũng bỏ (UNCONFIRMED). Còn lại là bộ ba hợp lệ: follow-up 403 (phù hợp) hoặc 2xx đã
xác nhận (970).
- Follow-up 404 hay 500 không bị hủy: bộ ba được đếm và không báo vi phạm. Trong 98 lượt, mọi bộ ba hợp lệ là
  `200/200/200` hoặc `200/200/403`, nên chưa gặp trường hợp này. Mục 3.3.3 và hình 3.1 viết đúng như vậy.
- Nếu hỏi "404 không phải lời từ chối, sao lại không báo vi phạm": vì oracle chỉ báo khi follow-up 2xx; 404 không cho
  biết quyền còn hay mất, nên không là bằng chứng vi phạm. Điểm yếu thật: bộ ba như vậy vẫn được đếm như một bộ ba hợp lệ.
- Ví dụ hủy thật: pyLoad 20 lần `200/401/200` (transition nhận 401); bản vá artifact-keeper `200/200/401`.

Nguồn: `executeStatefulAuthzTriple` (B); `docs/results.md` §1, §4.

### 3.21 Vì sao bộ ba bị hủy không tính là âm tính đúng?

Bộ ba bị hủy khi một bước tiền đề không xảy ra: chưa ghi được, chưa hạ được, hoặc token cũ bị từ chối như chưa đăng
nhập. Lúc đó không biết app đúng hay sai. Đếm nó là TN thì độ đặc hiệu bị thổi lên.
- Bản vá artifact-keeper hạ quyền thành công và trả 401 cho token cũ. Khóa luận ghi: 3 lượt không báo nhầm, không dựng
  được bộ ba, 0 TN.

Nguồn: `docs/results.md` §1, §2.

### 3.22 Khôi phục quyền là gì? Có làm sai kết quả không?

Pha tìm kiếm gọi transition với dữ liệu ngẫu nhiên, nên có thể đã hạ quyền các operator trước khi pha bảo mật chạy. Khi
mọi operator bị 401 hoặc 403 ở transition mà source của nạn nhân vẫn 2xx, nạn nhân còn quyền quản trị. Bộ dựng dùng
token của nạn nhân gọi transition theo chiều nâng cho operator, rồi thử lại bộ ba. Tối đa 3 lần cho mỗi transition.
- Không tạo báo nhầm: khôi phục chạy trong một test riêng, còn bộ ba sau đó vẫn phải qua mọi điều kiện hủy và bước đăng
  nhập lại.
- Số lần khôi phục được nhận (bị từ chối): reports-api 5 (0) bản lỗi, 6 (0) bản vá; vampi-seeded 5 (8) mỗi bản;
  pyLoad 5 (0) mỗi bản, mỗi lượt một lần, `pyload` nâng `alice`.
- Giới hạn: chỉ đảo được việc hạ quyền, không phục hồi tài khoản đã bị xóa. Trên VAmPI, test sinh ra gọi
  `DELETE /users/v1/{username}` 75 lần trên `name1`.
- Khi chạy lại test đã rút gọn, test có thể thiếu lần khôi phục: reports-api seed 16 thiếu lần đó nên follow-up thành
  403.

Nguồn: `restoreOperatorsAndRetry`, `restorePrivilege` (B); `docs/results.md` §1, §3, §7.

### 3.23 Bước đăng nhập lại làm gì? Vì sao cần?

Chỉ chạy khi follow-up 2xx. Bộ dựng chạy lại chuỗi của nạn nhân (setup và source) trong test mới, tức với token mới, và
đọc mã của lời gọi cuối cùng có mã. Cần 403. Sau đó gửi cùng chuỗi không kèm token; cần mã khác 403. Đạt cả hai thì giữ
bộ ba.
- Cần vì tên thao tác chưa chứng minh nó hạ quyền: cùng một endpoint có thể nâng hay hạ tùy giá trị gửi kèm.
- Ví dụ pyLoad: transition gửi `permission=1` cùng giá trị `role` do tìm kiếm để lại (373, 282, 883, 488, 946 ở seed
  1–5). pyLoad coi role 0 là admin, giá trị khác là không, nên lần hạ có hiệu lực, nhưng công cụ không suy ra điều đó.
  Bước đăng nhập lại xác nhận từng lần.
- Bước này thay cho việc người dùng khai báo transition. Jar đo số liệu không có tham số khai báo nào.

Nguồn: `reLoginProbeConfirmsPrivilegeRemoved` (B); `docs/metamorphic-authz-relations.md` §5.6; `docs/results.md` §4.

### 3.24 Vì sao bước đăng nhập lại chạy sau follow-up và trong test riêng?

Ở app chỉ giữ một phiên cho mỗi tài khoản, đăng nhập lại trước sẽ hủy token cũ và biến follow-up thành 401. EvoMaster
lại chỉ đăng nhập ở đầu mỗi test, nên token mới phải lấy bằng test thứ hai.

Nguồn: `docs/metamorphic-authz-relations.md` §5.6.

### 3.25 Lượt gửi không token để làm gì?

Để loại 403 không phụ thuộc người gọi. Nếu gửi không token cũng ra 403, thì 403 của token mới không nói gì về quyền của
nạn nhân. reports-api kiểm 401 trước 403, nên lượt không token ở seed 1 nhận 401 và bộ ba được giữ.

Nguồn: log seed 1 dòng 570 (`anonymous control: …=401`); `infra/reports-api/README.md`.

### 3.26 Trên reports-api, 403 của bước đăng nhập lại đến từ lời gọi nào?

Từ `POST /reports`, lời gọi setup. EvoMaster hộp đen dừng chuỗi ở lời gọi tạo tài nguyên đầu tiên thất bại, nên source
không được gọi lại. 34 trong 39 test 970 của reports-api (jar AF2) có `POST /reports` trước source.
- `POST /reports` cũng chỉ ADMIN được gọi, nên 403 vẫn cho thấy token mới mất quyền ghi. Không được nói bước này thử lại
  chính source trên reports-api.

Nguồn: `docs/results.md` §7.

### 3.27 Một cảnh báo 970 đúng với điều kiện nào?

Hai giả định: 403 phản ánh quyết định phân quyền, và token mới mang quyền hiện hành. Nếu giả định thứ hai sai, tức token
mới vẫn mang quyền cũ, bước đăng nhập lại không thấy 403 và bỏ bộ ba. Hậu quả là bỏ sót lỗi. Bước đăng nhập lại chỉ
bỏ bộ ba, nên nó không thể sinh báo nhầm.

Nguồn: mục 3.3.3 của khóa luận; `docs/metamorphic-authz-relations.md` §5.6.

### 3.28 Đọc thuật toán 3.1 trên seed 1.

Thuật toán có ba vòng lồng nhau: duyệt transition theo hạng, duyệt thao tác ghi ứng viên làm source, rồi dựng
I = [setup, a(c_v), T(c_o, v), a(c_v)] và chạy. Bộ ba hợp lệ thì vào tập kết quả và bộ dựng sang source kế; transition
bị 401 hoặc 403 thì khôi phục operator.

| Bước | Giá trị ở seed 1 |
|---|---|
| RankTransitions | `PUT /users/{username}/role`, điểm 7,32, ứng viên duy nhất |
| CandidateWrites | `PUT /reports/{id}` |
| Nạn nhân, operator | alice; superadmin |
| Giá trị hạ | VIEWER; ADMIN bị bỏ vì là vai trò hiện tại của alice |
| Execute | `200/200/200` |
| Discarded | không: token mới 403, không token 401 |
| Kết quả | một bộ ba hợp lệ, 970 |

- Thuật toán ở dạng rút gọn. Mã còn duyệt nạn nhân, operator và giá trị hạ; miễn trần K cho transition đã chứng minh
  và cho ứng viên cuối; không dùng lại tài khoản đã bị hạ trong pha làm nạn nhân hay operator.

Nguồn: log seed 1 dòng 571; `addForStatefulAccessControl`, `buildStatefulAuthzTriple` (B).

### 3.29 Vì sao N = 20, K = 5, R = 3?

Chọn tay để giới hạn thời gian của pha; chưa có khảo sát độ nhạy. Pha bảo mật còn bị chặn bởi ngân sách thời gian
(0,6 × `--maxTime`; artifact-keeper 0,25).
- K miễn cho transition đã chứng minh và cho ứng viên cuối, để không bỏ dở một transition đúng.
- Nếu hỏi tăng N có tăng recall không: chưa đo. Nguyên nhân bỏ sót đã ghi nhận là tìm kiếm phá tiền đề của bộ ba (hạ
  quyền, xóa tài khoản); chưa có bằng chứng nào cho thấy trần là nguyên nhân.

Nguồn: hằng `MAX_STATEFUL_TRIPLE_ATTEMPTS`, `MAX_UNPROVEN_CANDIDATE_ATTEMPTS`, `MAX_PRIVILEGE_RESTORES` (B);
`docs/results.md` §0, §7.

### 3.29a Một lần thử thất bại thì bộ dựng làm gì tiếp?

Đổi tổ hợp theo thứ tự: giá trị hạ quyền kế tiếp, nhưng chỉ khi máy chủ từ chối chính giá trị đó (4xx, 5xx khác 401,
403, 404); tài khoản quản trị kế tiếp (ai từng gọi transition thành công trong kho đứng trước); khôi phục quyền rồi thử
lại khi mọi tài khoản quản trị bị 401, 403; rồi nạn nhân, source, transition kế tiếp.
- Bỏ qua: tài khoản đã bị hạ trong pha không dùng lại; cặp transition và nạn nhân bị từ chối ở mọi lần thử không thử
  lại; transition chưa chứng minh mà trả 404 sau source 2xx thì bỏ cả transition; ứng viên có đường dẫn và đường dẫn
  cha luôn 404 bị loại trước khi thử; lần thử không dựng được lời gọi (không đặt được nạn nhân hay giá trị) không tính
  vào trần.
- Lý do: trần 20 lần thử mỗi pha, nên lần thử chắc chắn thất bại không được tiêu lượt.
- Khóa luận trình bày phần này ở bảng 3.4 (mục 3.3.4).

Nguồn: `tryReducedRoles`, `buildStatefulAuthzTriple`, `operatorsFor`, `routeLooksMissing`, `executeStatefulAuthzTriple`
(B).

### 3.30 Một lượt chạy có cho nhiều bộ ba không?

Có thể: mỗi source cho tối đa một bộ ba hợp lệ, rồi bộ dựng sang source kế. Trong 98 lượt, mỗi lượt có bộ ba chỉ có một.
Tài khoản đã bị hạ trong pha không được dùng lại, nên số bộ ba còn bị chặn bởi số tài khoản (reports-api có ba: alice,
superadmin, bob).
- File xác thực phải có ít nhất 2 tài khoản; ít hơn thì bộ dựng không chạy.

Nguồn: `addForStatefulAccessControl`, `privilegeReducedInPhase` (B); `docs/results.md` §1.

### 3.31 Bộ dựng tốn bao nhiêu lời gọi?

Mỗi lần thử là một test 3–4 lời gọi. Bộ ba có follow-up 2xx thêm hai test (token mới, không token). Mỗi lần khôi phục
thêm một test. Tối đa 20 lần thử mỗi pha, trong ngân sách thời gian của pha. Thời gian riêng của bộ dựng chưa được đo.

## D. Nhận diện thao tác hạ quyền (mục 3.4)

### 3.32 Vì sao phải tự nhận diện thao tác hạ quyền?

Công cụ chỉ có đặc tả OpenAPI; không ai khai báo thao tác nào hạ quyền. Một app có thể có hàng trăm thao tác ghi
(artifact-keeper 216) trong khi một pha chỉ có 20 lần thử, nên phải thử thao tác khả năng cao trước.

Nguồn: `infra/analysis/lexicon-rules/m2-model-20261107/compare_targets.out`.

### 3.33 Naive Bayes là gì? Vì sao chọn nó?

Bộ phân loại theo định lý Bayes, giả định các đặc trưng độc lập khi biết nhãn. Điểm là tổng trọng số nên đọc được:
nhìn bảng là biết vì sao một thao tác đứng đầu. Nó học được từ 209 mẫu dương và chạy trong jar, không cần mạng.
- Đã so ba luật trên 47 spec kiểm chéo theo nhà cung cấp: lấy điểm từ khóa cao nhất, noisy-OR, Naive Bayes. Không chênh
  nào có p < 0,05. Naive Bayes được chọn vì thao tác đúng luôn nằm trong tầm thử: số thao tác phí lớn nhất ở một spec
  là 1–3, so với 2–76 của luật từ khóa và 4–31 của noisy-OR. Ví dụ netbox: luật từ khóa đẩy thao tác đúng xuống hạng 77.
- 47 spec đó đã bị xem nhiều lần khi chọn mô hình, nên các số này là thăm dò.
- Đổi từ danh sách từ khóa sang Naive Bayes không mất phát hiện 970 nào trên ba target benchmark.
- Nếu hỏi sao không gọi mô hình ngôn ngữ lớn ngay trong công cụ: chưa thử, không có số đo. Mô hình ngôn ngữ chỉ dùng để
  gán nhãn khởi đầu cho dữ liệu học.

Nguồn: `infra/evomaster-ext/wip/p2-design-20261012.md` §1; `docs/naive-bayes.md` §3; `docs/results.md` §6.

### 3.34 Tính tay công thức 3.2 cho một thao tác.

`PUT /users/{username}/role` của reports-api, trọng số M2:

| Đặc trưng | Trọng số | Cộng dồn |
|---|---|---|
| tiên nghiệm ln(209/10.172) | −3,885 | −3,885 |
| `p:users` | +2,135 | −1,750 |
| `p:username` | +2,449 | +0,699 |
| `p:role` | +2,755 | +3,454 |
| `f:username` | +1,717 | +5,171 |
| `f:role` | +1,898 | +7,069 |
| `v:PUT` | +0,250 | **+7,32**, ứng viên |

`PUT /reports/{id}`: `p:reports`, `f:title`, `f:classification` không có trong bảng, `id` dưới 4 ký tự nên bị bỏ. Điểm
= −3,885 + 0,250 = −3,64 < 0. Thao tác này không là ứng viên transition, nên được phép làm source.
- Trọng số một đặc trưng: w(t) = ln((d_T + 1)/(N_T + 2)) − ln((d_N + 1)/(N_N + 2)), với d là số thao tác của lớp có
  chứa t, N là cỡ lớp.

Nguồn: `infra/analysis/lexicon-rules/m2-model-20261107/stateful-authz-model.csv`, `compare_targets.out`.

### 3.35 Vì sao cộng 1 và 2 trong công thức?

Làm trơn Laplace cho đặc trưng có hai giá trị (có, không). Một đặc trưng chưa gặp ở lớp T sẽ cho xác suất 0 và ln 0;
cộng 1 vào tử và 2 vào mẫu (hai giá trị có thể) tránh điều đó.

### 3.36 Vì sao điểm > 0 thì là ứng viên? "Chưa hiệu chuẩn" nghĩa là gì?

Điểm là logarit tỉ số hậu nghiệm hai lớp. Điểm > 0 nghĩa là hậu nghiệm của lớp T lớn hơn 0,5, ranh giới quyết định chuẩn
của Naive Bayes. Chưa hiệu chuẩn nghĩa là con số hậu nghiệm không khớp tần suất thật: điểm 7,32 ứng với hậu nghiệm
0,9993, nhưng trên tập thi chỉ 117 trong 880 thao tác điểm dương mang nhãn T (13%).
- Vì vậy điểm chỉ dùng để xếp thứ tự thử.

Nguồn: `docs/naive-bayes.md` §2; `docs/results.md` §7.

### 3.37 Đặc trưng gồm gì? Vì sao lọc theo ít nhất hai nhà cung cấp?

Ba nhóm: token đường dẫn (`p:`), token tên lá của tham số và trường thân (`f:`), phương thức (`v:`). Tách token: cắt ở ký
tự ngoài chữ cái và chữ số, tách camelCase, chữ thường, bỏ token toàn số và token dưới 4 ký tự. Chỉ giữ đặc trưng xuất hiện
trong thao tác T của ít nhất 2 nhà cung cấp, để mô hình không học thuộc từ riêng của một công ty.
- Đặc trưng được giữ vẫn có thể mang trọng số âm, ví dụ `v:POST` −1,019.

Nguồn: `docs/naive-bayes.md` §2; `stateful-authz-model.csv`.

### 3.38 Giả định độc lập bị vi phạm ở đâu? Ảnh hưởng thế nào?

Các token về người dùng thường đi cùng nhau: `user`, `username`, `email`, `password`. Mô hình cộng từng cái như bằng
chứng riêng. Ở ví dụ câu 3.34, `p:users`, `p:username`, `f:username` góp 6,30 trong 7,32 điểm. Hệ quả là điểm quá tự tin
(câu 3.36); thứ tự xếp hạng ít bị ảnh hưởng hơn, và trên bốn target thao tác đúng vẫn nằm trong danh sách thử.

Nguồn: `docs/naive-bayes.md` §6; mục 3.4 của khóa luận.

### 3.39 Dữ liệu học lấy từ đâu? Nhãn T định nghĩa thế nào?

10.381 thao tác ghi của 230 bộ API. Nhãn T khi thao tác nhắm một tài khoản đã tồn tại (hoặc chính người gọi), đổi vai
trò, quyền, cờ admin hoặc vai trò thành viên, và không thuộc loại chỉ làm quyền tăng. Thao tác chỉ cấp thêm quyền, thao
tác tạo tài khoản mới, thao tác khóa tài khoản đều là N. Tập cuối có 209 thao tác T.
- Quy trình: hai lượt gán độc lập bằng hai mô hình ngôn ngữ lớn khác nhau cho nhãn khởi đầu; em soát tay 602
  thao tác: mọi thao tác hai lượt lệch nhau (66), gần hết thao tác hai lượt cùng gọi T (165 trong 173), và 371 thao
  tác ngẫu nhiên hai lượt cùng gọi N. Trong 371 thao tác đó không có thao tác T nào.
- Ở 66 thao tác có nhãn soát tay khác cả hai lượt máy, em xem lại lần hai và chọn: giữ nhãn soát tay 14, theo hai lượt
  máy 35, theo một lượt 17. Đây là điểm yếu nếu bị hỏi: chỉ một người soát nhãn, và nhãn cuối của các thao tác này do
  em quyết.
- Mục 3.4 chỉ ghi định nghĩa nhãn, 602 thao tác soát tay và mẫu ngẫu nhiên 371 thao tác. Chi tiết 66 thao tác xem lại
  lần hai không có trong khóa luận; dùng để trả lời khi bị hỏi.

Nguồn: `infra/analysis/lexicon-rules/relabel-20261101/PROTOCOL.md` §1, §3, §10, §11; `GUIDE.md`.

### 3.40 Dữ liệu lệch (2% là T) có làm hỏng mô hình không?

Lệch lớp làm tiên nghiệm âm (−3,885), nên một thao tác cần nhiều dấu hiệu mới có điểm dương. Công cụ chỉ cần xếp thứ tự
thử, và mọi lựa chọn sai bị chặn ở sau: transition không hạ quyền thì bước đăng nhập lại không thấy 403. Trên tập thi,
763 trong 880 thao tác điểm dương mang nhãn N, mà trên mã đã vá vẫn 0 báo nhầm.

Nguồn: `docs/results.md` §1, §7.

### 3.41 Mô hình được đánh giá thế nào? Có rò rỉ dữ liệu không?

Chấm trên tập thi riêng: 365 công ty chưa từng được bốc vào tập học, mỗi công ty một spec; 237 spec có thao tác ghi,
8.674 thao tác, 153 thao tác T. 117/153 thao tác T có điểm dương (76,5%, Clopper–Pearson 68,9–82,9%). Các con số nằm ở
mục 5.3 của khóa luận.
- Tách theo công ty để spec của cùng công ty không nằm ở cả hai tập. Transition của các target nằm trong một tệp riêng,
  không vào tập học. Spec của artifact-keeper bị loại khỏi corpus.
- Lệch quy trình đã ghi: sau khi chấm và đã in điểm vài thao tác thi, 44 thao tác hai lượt máy lệch nhau được soát lại,
  4 thao tác đổi từ N sang T. Trước lần soát: 116/149 (77,9%).
- Số này không đo việc chọn trường vai trò và trường nạn nhân.

Nguồn: `relabel-20261101/PROTOCOL.md` §1, §11; `docs/results.md` §5, §7.

### 3.42 Ngoài thao tác hạ quyền, mô hình còn chọn gì?

Trường vai trò, trường nạn nhân và giá trị hạ, nâng.

| Target | Trường vai trò | Trường nạn nhân | Giá trị hạ |
|---|---|---|---|
| reports-api | `body:role` (enum) | `path:username` | VIEWER |
| pyLoad | `query:permission` (số) | `query:user` | 1, 0, 2 |
| artifact-keeper | `body:is_admin` (bool) | `path:id` | false |

- Còn viết tay: thứ tự `1, 0, 2` cho trường số (nâng: `0, 1, 2`), và token `id` khi điền giá trị nạn nhân.
- Enum: chọn giá trị mô hình chấm thấp, bỏ giá trị bằng vai trò hiện tại của nạn nhân. Bool: đảo. Mảng: `[]`.

Nguồn: `compare_targets.out`; `infra/evomaster-ext/README.md` §3; `docs/naive-bayes.md` §6.

### 3.43 Vì sao bộ phán quyết cũng dùng điểm > 0?

Bộ phán quyết dùng cùng vị từ cho hai việc: lời gọi ở giữa phải có điểm > 0, và source không được có điểm > 0. Cùng một
vị từ, cùng ngưỡng, nên bộ dựng không dựng bộ ba mà bộ phán quyết từ chối.
- Ngưỡng được chọn sau một lần cổng hồi quy bắt lỗi: bản đầu dùng tổng trọng số không tính tiên nghiệm (Σw > 0), và
  `PUT /reports/{id}` có Σw = +0,43 chỉ nhờ `v:PUT`, nên bị loại khỏi vai source; 2/2 hàng reports-api bản lỗi mất 970.
  Dùng điểm đầy đủ thì source này được −3,51 (M1).
- Cái giá: thao tác hạ quyền có điểm ≤ 0 thì không bao giờ được thử. Trên tập thi, 36/153 thao tác T rơi vào trường hợp
  này.

Nguồn: `infra/evomaster-ext/wip/p2-design-20261012.md` §7; `docs/naive-bayes.md` §1.

### 3.44 Mô hình chọn sai thì có báo nhầm không?

Không. Thao tác được chọn mà không hạ quyền thì follow-up 2xx một cách chính đáng, nhưng token mới cũng không nhận 403,
nên bước đăng nhập lại bỏ bộ ba. Thao tác khóa hay xóa tài khoản làm token mới không đăng nhập được, cũng bị bỏ. Lựa
chọn sai chỉ tốn lượt thử.

Nguồn: `reLoginProbeConfirmsPrivilegeRemoved` (B); `docs/results.md` §1.

### 3.45 Mô hình xếp hạng thao tác đúng thế nào trên bốn target?

| Target | Thao tác hạ quyền | Hạng trong các thao tác dựng được bộ ba |
|---|---|---|
| reports-api | `PUT /users/{username}/role` | 1 trên 1 |
| vampi-seeded | `PUT /users/v1/{username}/role` | 1 trên 1 |
| pyLoad | `POST /api/set_user_permission` | 1 trên 3 |
| artifact-keeper | `PATCH /api/v1/users/{id}` | 4 trên 5 |

- Đường dẫn `/role` của reports-api và vampi-seeded do em đặt, nên hạng của hai app này không chứng minh khả năng
  khái quát. Hai app thật là pyLoad và artifact-keeper. Bộ dựng tới được hạng 4 ở artifact-keeper vì thử mọi ứng viên.

Nguồn: `compare_targets.out`; `docs/results.md` §5, §7, §9.

### 3.46 Hai thao tác cùng điểm thì sao?

Giữ thứ tự xuất hiện trong spec để kết quả lặp lại được. Trên corpus, thao tác T hòa điểm với thao tác sai ở 1 trên
26–28 spec.

Nguồn: `p2-design-20261012.md` §8.

### 3.47 Giải thích hình 3.3.

Đặc tả OpenAPI cho danh sách thao tác ghi; mỗi thao tác được tách đặc trưng (đường dẫn, tên trường, phương thức); Naive
Bayes tính điểm; thao tác có điểm > 0 được xếp hạng. Đầu ra cho bộ dựng: thứ tự thao tác hạ quyền, trường vai trò và
giá trị hạ, trường nạn nhân.
