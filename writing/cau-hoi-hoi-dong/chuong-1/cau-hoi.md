# Chương 1. Giới thiệu: câu hỏi hội đồng

Đoạn đầu mỗi câu là câu trả lời nói trong khoảng 30 giây. Phần sau dùng khi bị hỏi tiếp. Dòng `Nguồn` để tự tra lại.
Số liệu: jar M2, chạy ngày 2026-11-08.

## Khái niệm phải giải thích được

| Khái niệm | Nghĩa | Ví dụ |
|---|---|---|
| Xác thực (authentication) | Xác định người gọi là ai. | alice đăng nhập bằng mật khẩu và nhận token. |
| Phân quyền (authorization) | Quyết định người gọi được làm thao tác nào. | VIEWER đọc được báo cáo nhưng không sửa được. |
| Thông tin xác thực | Thứ client gửi kèm mỗi request để server nhận ra mình. | Header `Authorization: Bearer <JWT>` hoặc cookie phiên. |
| JWT | Token tự chứa thông tin (claim) và có chữ ký của server. | JWT của artifact-keeper mang claim `is_admin`. |
| Phiên (session) | Trạng thái đăng nhập server giữ, client chỉ giữ mã phiên trong cookie. | pyLoad chép `role` vào session lúc đăng nhập. |
| Thu hồi quyền, hạ quyền | Gỡ một quyền hoặc hạ vai trò của tài khoản. | `PUT /users/alice/role` với `{"role": "VIEWER"}`. |
| Lỗ hổng phân quyền có trạng thái | Server vẫn chấp nhận thao tác theo quyền đã thu hồi khi client dùng thông tin xác thực cấp trước lúc thu hồi. | Token cũ của admin vừa bị hạ vẫn sửa được báo cáo. |
| OWASP API Security Top 10 | Danh sách 10 nhóm rủi ro API phổ biến, bản năm 2023. | API1 là BOLA, API5 là BFLA. |
| CWE | Danh mục loại điểm yếu do MITRE duy trì. | CWE-613, nay được thay bằng CWE-1464. |
| CVE | Mã của một lỗ hổng cụ thể trong một sản phẩm cụ thể. | CVE-2026-41133 của pyLoad. |
| Oracle | Cơ chế quyết định kết quả của một test là đúng hay sai. | Quy tắc "mã 500 là lỗi". |
| Quan hệ biến hình | Quy luật ràng buộc kết quả của nhiều lần chạy có liên quan. | sin(x) = sin(π − x). |
| MR-A1 | Thao tác cần quyền X đã nhận 2xx khi còn X thì phải nhận 403 sau khi X bị gỡ, nếu vẫn dùng token cũ. | Câu 1.18. |
| Bộ ba source, transition, follow-up | Ba lời gọi dựng một lần kiểm MR-A1. | Câu 1.19. |
| Điều kiện tiền đề | Điều phải đúng thì bộ ba mới được phán quyết. | source 2xx và transition 2xx. |
| Oracle 970 | Phần phán quyết của khóa luận, báo lỗi mang mã 970. | Test `test_0_put_on_report_stillAllowedAfterPermissionRevoked`. |
| EvoMaster | Công cụ mã nguồn mở tự sinh test cho REST, GraphQL và RPC API. | Phiên bản dùng: 6.1.1. |
| Pha kiểm thử bảo mật | Pha của EvoMaster chạy sau tìm kiếm, dựng thêm test bảo mật từ các test đã có. | Bộ dựng MR-A1 chạy trong pha này. |
| Kho lưu trữ (archive) | Nơi EvoMaster giữ test tốt nhất cho từng mục tiêu. | Bộ dựng lấy source từ đây. |
| Đặc tả OpenAPI | File mô tả endpoint, tham số và kiểu dữ liệu của API. | `/v3/api-docs` của reports-api. |
| Cấu hình xác thực | File khai báo tài khoản và cách đăng nhập cho EvoMaster. | `infra/em-config/reports-auth.yaml`. |
| Naive Bayes | Mô hình chấm điểm bằng tổng trọng số logarit của từng đặc trưng. | `PUT /users/{username}/role` của reports-api được 7,32 điểm. |
| Bước đăng nhập lại | Tài khoản nạn nhân đăng nhập lại để xác nhận quyền đã mất thật. | Token mới phải nhận 403. |
| Lỗi gieo | Lỗi cố ý cài vào app để biết trước đáp án. | reports-api, vampi-seeded. |
| Biến thể có lỗ hổng, đã vá | Hai bản của cùng một app, khác nhau đúng ở chỗ lỗi. | pyLoad có lỗ hổng và pyLoad đã vá. |
| Lượt chạy | Một lần chạy EvoMaster với một seed. | reports-api seed 1, 150 giây. |
| Báo động giả (FP) | 970 báo lỗi trên biến thể đã vá. | 0 trong 48 lượt. |

Nguồn: điểm Naive Bayes ở `infra/analysis/lexicon-rules/m2-model-20261107/compare_targets.out`; tên test ở
`infra/em-results/m2-wave1-20261108/tests/t1-vuln-seed1/EvoMaster_faults_Test.py:57`.

## A. Bài toán và động lực

### 1.1 Trình bày bài toán trong một phút.

Khi admin hạ quyền một tài khoản, có hệ thống chỉ ghi vai trò mới vào cơ sở dữ liệu. Token hoặc phiên đã cấp vẫn mang
vai trò cũ, nên tài khoản đó dùng lại token cũ và vẫn làm được việc của admin. Các oracle phân quyền có sẵn trong
EvoMaster so nhiều tài khoản tại cùng một lúc, nên không thấy lỗi này. Khóa luận thêm vào EvoMaster một oracle tự dựng
kịch bản ba bước: làm thao tác khi còn quyền, hạ quyền, rồi làm lại bằng token cũ. Bước cuối vẫn nhận 2xx thì báo lỗi 970.

Ví dụ thật trên reports-api, seed 1:
```
alice       PUT /reports/505                 token T        -> 200
superadmin  PUT /users/alice/role {"role":"VIEWER"}         -> 200
alice       PUT /reports/505                 vẫn token T    -> 200   lỗi 970, đúng ra phải 403
```
Nguồn: `infra/em-results/m2-wave1-20261108/tests/t1-vuln-seed1/EvoMaster_faults_Test.py:105–151`.

### 1.2 "Có trạng thái" nghĩa là gì? Đây có phải thuật ngữ chuẩn không?

"Broken Access Control" là thuật ngữ chuẩn của OWASP. "Có trạng thái" là chữ khóa luận thêm vào: quyết định truy cập
chỉ sai sau một lần đổi trạng thái phân quyền. Gọi thao tác đó vào một thời điểm bất kỳ trước khi hạ quyền thì không thấy
lỗi. Không có danh mục chính thức nào của OWASP hay CWE mang tên này. Khóa luận định nghĩa nó ở mục 1.2 và 2.3.

### 1.3 Vì sao lỗi này xảy ra?

Server chép vai trò vào token hoặc phiên lúc đăng nhập, sau đó đọc vai trò từ bản sao đó thay vì từ cơ sở dữ liệu.
Lệnh hạ quyền chỉ sửa cơ sở dữ liệu nên bản sao cũ vẫn còn.
- pyLoad: `set_session()` chép `role` và `permission` vào session Flask; kiểm quyền đọc `session.get("role")`;
  `set_user_permission()` ghi vai trò mới vào cơ sở dữ liệu mà không hủy phiên nào.
- artifact-keeper: ghi `is_admin` vào JWT lúc đăng nhập và đọc lại từ claim, không tra cơ sở dữ liệu.
- Hai app lỗi gieo cùng cơ chế: vai trò nằm trong claim của JWT.

Nguồn: `docs/tier2b-pyload-target.md` §2; `docs/results.md` §5, §7.

### 1.4 Lỗi này có thật và có nghiêm trọng không?

Có. pyLoad có CVE-2026-41133, điểm CVSS 8.8; bản ghi CVE mô tả người dùng giữ quyền đã bị thu hồi "until logout/session
expiry". Ở artifact-keeper, admin bị hạ vẫn giữ quyền admin tới khi token hết hạn sau 30 phút; nhà phát triển đã vá
bằng commit `e64cc5c608`. Cả hai lỗi không do em viết.

Nguồn: bản ghi CVE `https://cveawg.mitre.org/api/cve/CVE-2026-41133`; `docs/results.md` §5.

### 1.5 Sửa lỗi này thế nào?

Có hai cách chính. Cách thứ nhất là đọc vai trò từ cơ sở dữ liệu ở mỗi request: bản pyLoad đã vá do em viết làm
đúng như vậy, giống nhánh `X-API-Key` sẵn có của pyLoad. Cách thứ hai là làm token cũ mất hiệu lực khi quyền đổi:
artifact-keeper thêm mốc `privileges_changed_at`, token cấp trước mốc đó bị trả 401.
- Đánh đổi: JWT được chọn để server khỏi tra cơ sở dữ liệu ở mỗi request. Cách sửa nào cũng thêm một lần tra hoặc một
  danh sách thu hồi.
- Rút ngắn thời hạn token chỉ thu hẹp khoảng thời gian bị khai thác, không xóa được lỗi.

Nguồn: `docs/tier2b-pyload-target.md` §3 (lệch luật 2); `docs/results.md` §5.

### 1.6 Vì sao một request HTTP riêng lẻ không đủ để phán quyết?

`PUT /reports/505` trả 200 là đúng nếu alice đang là ADMIN, là sai nếu alice vừa bị hạ xuống VIEWER. Nhìn riêng request
đó không biết được vai trò hiện hành của alice. Phải có kết quả của cùng thao tác trước và sau khi hạ quyền, kèm bằng
chứng quyền đã mất thật. Đây là bài toán thiếu oracle, giải bằng kiểm thử biến hình (chương 2, câu 2.10).

### 1.7 Token, cookie và JWT khác nhau thế nào?

Token là chuỗi server cấp lúc đăng nhập, client gửi lại trong header `Authorization`. JWT là một loại token tự chứa
thông tin như tên và vai trò, có chữ ký để không sửa được; server đọc claim mà không cần tra cơ sở dữ liệu. Cookie phiên
chỉ chứa mã phiên; dữ liệu phiên nằm ở server (pyLoad dùng session Flask).
- Lỗi có thể xảy ra với cả hai: JWT mang claim cũ, phiên mang bản sao vai trò cũ.
- Trong bốn app: reports-api, vampi-seeded và artifact-keeper dùng JWT Bearer; pyLoad dùng cookie phiên.

### 1.8 CWE-1464 là gì? Vì sao khóa luận viết "có thể thuộc"?

CWE-1464 "Improper Session Invalidation": hệ thống "does not properly invalidate or terminate the session when it is
required". Khóa luận viết "có thể thuộc" vì chỉ là lỗi khi chính sách của hệ thống yêu cầu thu hồi có hiệu lực ngay;
chuẩn RBAC để việc này cho phía cài đặt.
- Nếu hỏi vì sao bản ghi CVE của pyLoad ghi CWE-613: MITRE ngừng dùng CWE-613 "Insufficient Session Expiration" từ
  CWE 5.0 (2026-10-27), trang của nó ghi "Usage PROHIBITED" và gợi ý CWE-1463, CWE-1464. Bản ghi CVE công bố tháng
  4/2026, trước thay đổi này. Mục 4.2.3 của khóa luận ghi cả hai mã.

Nguồn: `https://cwe.mitre.org/data/definitions/613.html`, `.../1464.html`, đọc ngày 2026-11-09.

### 1.9 OWASP API Security Top 10 là gì? Lỗi của em thuộc mục nào?

Đó là danh sách 10 nhóm rủi ro API phổ biến do OWASP công bố, bản năm 2023. Khóa luận chỉ trích API1 (BOLA) và API5
(BFLA) vì baseline của Şahin và cộng sự nhắm đúng hai lớp này. Lớp lỗi khóa luận xét không có mục riêng. Gần nhất là API5:
trang API5 hỏi "Can a regular user access administrative endpoints?", và sau khi bị hạ quyền alice là người dùng thường
mà vẫn gọi được chức năng của admin. Khác biệt là lỗi chỉ hiện ra với token cấp trước lúc hạ quyền.
- Nếu hỏi "sao không phải API2 Broken Authentication": danh sách của API2 gồm credential stuffing, brute force, mật khẩu
  yếu, JWT `alg: none`, không kiểm hạn JWT, không nhắc việc giữ phiên sau khi đổi vai trò. Ở lỗi này, xác thực vẫn đúng:
  token thật, đúng chữ ký, còn hạn. Chỗ sai là quyền được đọc từ bản sao cũ.

Nguồn: `https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/`, `.../0xa5-...`, đọc ngày 2026-11-09.

## B. Mục tiêu và phạm vi

### 1.10 Mục tiêu cụ thể của khóa luận là gì, đo bằng gì?

Mở rộng EvoMaster để tự phát hiện vi phạm MR-A1 ở chế độ hộp đen, không cần người khai báo thao tác hạ quyền. Đo bằng
số lượt phát hiện trên biến thể có lỗ hổng (36/50) và số báo động giả trên biến thể đã vá (0/48), tách theo từng app.

### 1.11 Vì sao chỉ làm MR-A1? "A1" nghĩa là gì?

MR là metamorphic relation (quan hệ biến hình). A1 là quan hệ đầu trong nhóm ba quan hệ phân quyền đã định nghĩa trong
tài liệu thiết kế, khác nhau ở thứ bị gỡ: A1 là vai trò, A2 là quyền sở hữu, A3 là hiệu lực của quyền (hết hạn). Khóa
luận làm A1 vì hạ vai trò gọi được qua API và có lỗi thật để kiểm (pyLoad, artifact-keeper). A2 và A3 nằm ở hướng phát
triển (mục 6.3).
- A2, A3 cần cách dựng khác: ở A2 chính chủ thể tự chuyển quyền sở hữu, và follow-up phải dùng lại đúng đối tượng cũ
  vì quyền sở hữu tính theo từng đối tượng.
- Mục 3.2 của khóa luận ghi: chữ A chỉ nhóm quan hệ phân quyền (authorization), số 1 chỉ quan hệ đầu tiên.
- MR-A1 không liên quan tới mục "A01:2021 Broken Access Control" của OWASP.

Nguồn: `docs/metamorphic-authz-relations.md` §4.

### 1.12 Ba điều kiện áp dụng là gì, vì sao cần từng điều kiện?

| Điều kiện | Vì sao cần | Ví dụ ngoài phạm vi |
|---|---|---|
| Thao tác hạ quyền gọi được qua REST API | Công cụ chỉ gửi HTTP. | Admin đổi quyền bằng lệnh SQL trực tiếp. |
| Đăng nhập lại được sau khi hạ quyền | Bước đăng nhập lại cần token mới để xác nhận quyền đã mất. | Thao tác xóa tài khoản: không còn tài khoản để đăng nhập. |
| Từ chối bằng mã 403 | Oracle chỉ đọc 403 là từ chối. | Bản vá của artifact-keeper trả 401 cho token cũ. |

Nguồn: `docs/argument.md`, mục "Ranh giới phải viết".

### 1.13 Vì sao chỉ nhận 403 là từ chối? 401 và 404 thì sao?

403 nghĩa là server biết người gọi là ai và từ chối vì quyền. 401 nghĩa là server không nhận thông tin xác thực, thường
do token hết hạn giữa chừng; khi đó không biết quyền còn hay mất, nên bộ ba bị hủy (VOID). 404 có thể là "không có tài
nguyên" hoặc "giấu tài nguyên"; hai nghĩa không tách được. Bốn app được kiểm là kiểm quyền trước khi kiểm tồn tại.
- Hệ quả đã thấy: bản vá của artifact-keeper trả 401 cho token cũ, nên 3 lượt trên bản vá không dựng được bộ ba nào.
  Không báo nhầm, nhưng cũng không đếm được là âm tính đúng.
- Mã từ chối chưa cấu hình được. Đây là hạn chế đã ghi ở chương 6.

Nguồn: `docs/metamorphic-authz-relations.md` §5.1; `docs/results.md` §1.

### 1.14 "Giữ nguyên thuật toán tìm kiếm" nghĩa là gì? Sao không sửa thuật toán?

Phần mở rộng chỉ thêm mã vào pha kiểm thử bảo mật, chạy sau khi tìm kiếm và rút gọn test đã xong. Mã của thuật toán tìm
kiếm không đổi dòng nào.
- Vì sao không đưa vào tìm kiếm: mục tiêu của tìm kiếm hộp đen là các cặp mã trạng thái và endpoint. Một chuỗi "làm,
  hạ quyền, làm lại bằng token cũ" không phải mục tiêu mà tìm kiếm tự nhắm tới; dựng nó có chủ đích sau tìm kiếm thì
  chắc hơn và không làm lệch kết quả tìm kiếm của baseline.
- Thuật toán tìm kiếm ở đây là SMARTS, mặc định của chế độ hộp đen (chương 2, câu 2.3).

Nguồn: `EvoMaster/core/src/main/kotlin/org/evomaster/core/Main.kt:269–273`.

### 1.15 Vì sao chọn EvoMaster?

Ba lý do kiểm được: mã nguồn mở; có sẵn pha kiểm thử bảo mật và các oracle phân quyền của Şahin và cộng sự để làm
baseline trong cùng công cụ; kho lưu trữ chứa sẵn những request hợp lệ (đúng tham số, đúng tài khoản) để dựng bộ ba.
Chạy hộp đen được trên app viết bằng bất kỳ ngôn ngữ nào.

### 1.16 Vì sao chạy hộp đen mà không hộp trắng?

Hộp trắng của EvoMaster chỉ hỗ trợ app chạy trên JVM, vì nó phân tích bytecode. pyLoad viết bằng Python, artifact-keeper
viết bằng Rust. Oracle 970 chỉ cần mã trạng thái HTTP, nên hộp đen đủ.
- README của EvoMaster ghi hộp đen "can run on any API (regardless of its programming language...)"; hỗ trợ hộp trắng
  cho JavaScript và C# đã bị bỏ.

Nguồn: `EvoMaster/README.md:113–121`.

## C. Đóng góp

### 1.17 Em đã viết những gì vào EvoMaster?

So với v6.1.1, nhánh `stateful-authz-oracle` thêm 1.537 dòng Kotlin vào ba file có sẵn, không xóa dòng nào, và thêm một
file trọng số:
| File | Dòng thêm | Vai trò |
|---|---|---|
| `RestSecurityBuilder.kt` | 1.464 | Bộ dựng: chọn source, xếp hạng transition, dựng bộ ba, đăng nhập lại |
| `RestSecurityOracle.kt` | 68 | Bộ phán quyết: đọc mã trạng thái của bộ ba |
| `ExperimentalFaultCategory.kt` | 5 | Khai báo mã lỗi 970 |
| `stateful-authz-model.csv` | file mới | Trọng số Naive Bayes |

- Không đổi thuật toán tìm kiếm, không đổi `EMConfig.kt`, không thêm tùy chọn dòng lệnh.
- Khi demo: số liệu của khóa luận dùng `EvoMaster/evomaster-M2-917c57dd.jar`. File trọng số trong cây mã vẫn là mô hình
  M1, nên dựng lại từ mã sẽ ra jar khác jar đã đo.

Nguồn: `git diff --stat v6.1.1 9c4be5b1dc -- core/src/main` trong repo EvoMaster; `CLAUDE.md` §5.

### 1.18 MR-A1 khác gì cách so hai tài khoản của các oracle có sẵn?

Oracle có sẵn hỏi "người không có quyền có vào được không, ngay lúc này". MR-A1 hỏi "chìa khóa cũ của đúng người đó còn
mở được cửa sau khi bị thu hồi không". Một bên so nhiều người tại một thời điểm, bên kia so một người ở hai thời điểm,
giữ nguyên token.

| | Oracle có sẵn | MR-A1 |
|---|---|---|
| So theo | tài khoản | thời gian, trước và sau transition |
| Token | mỗi tài khoản một token | giữ nguyên token cũ |

- EvoMaster đăng nhập lại mọi tài khoản ở đầu mỗi test, nên baseline luôn cầm token mới nhất và không bao giờ dùng token
  cũ.

Nguồn: `docs/metamorphic-authz-relations.md` §2.4; `docs/results.md` §8.

### 1.19 Cho một ví dụ bộ ba thật.

pyLoad, mọi lượt M2:
```
source     pyload  POST /json/status                                     -> 200
transition alice   POST /api/set_user_permission
                   (user=pyload, permission=1, role=373 ở seed 1)          -> 200
follow-up  pyload  POST /json/status, cookie cũ                           -> 200 (bản lỗi), 403 (bản vá)
```
pyLoad coi `role=0` là admin, giá trị khác là không phải admin, nên `role=373` là hạ quyền.
Nguồn: `docs/results.md` §4.

### 1.20 Điều kiện tiền đề là gì? Khi nào bộ ba bị hủy?

Bộ ba chỉ được phán quyết khi source 2xx, transition 2xx và follow-up có mã khác 401. Source hoặc transition không 2xx,
hay follow-up 401, thì bộ ba VOID, không tính cho chiều nào. Thêm một điều kiện: source phải là thao tác ghi cần đúng
quyền bị gỡ. Không có điều kiện này thì `GET /reports`, thao tác VIEWER cũng được làm, sẽ bị đọc thành lỗi.
- Chi tiết theo mã: chương 3, câu 3.20.

Nguồn: `docs/metamorphic-authz-relations.md` §2.3, §3; `executeStatefulAuthzTriple` trong `RestSecurityBuilder.kt`.

### 1.21 Vì sao cần tự nhận diện thao tác hạ quyền? Naive Bayes làm gì?

Mỗi API đặt tên thao tác hạ quyền khác nhau: `PUT /users/{username}/role`, `POST /api/set_user_permission`,
`PATCH /api/v1/users/{id}` với `{"is_admin": false}`. Bắt người dùng khai báo thì công cụ không còn tự động. Naive Bayes
tách đường dẫn, tên trường và phương thức HTTP thành token, cộng trọng số của từng token thành điểm, rồi xếp hạng các
thao tác ghi. Bộ dựng thử lần lượt các ứng viên.
- Học từ 10.381 thao tác ghi đã gán nhãn, trong đó 209 là thao tác hạ quyền. Trên nửa dữ liệu để thi: 117/153 thao tác
  hạ quyền có điểm dương (76,5%), nhưng 763/880 thao tác điểm dương không phải hạ quyền. Điểm chỉ dùng để chọn ứng viên.
- Trên bốn app: thao tác đúng đứng hạng 1 ở reports-api, vampi-seeded, pyLoad và hạng 4/5 ở artifact-keeper.
- Vì sao không dùng LLM: Naive Bayes chạy offline, không tốn phí gọi API, cho cùng kết quả mỗi lần và trọng số đọc
  được. LLM nằm ở hướng phát triển (mục 6.3).
- Chi tiết thuộc chương 3.

Nguồn: `CLAUDE.md` §6; `infra/analysis/lexicon-rules/m2-model-20261107/compare_targets.out`.

### 1.22 Bước đăng nhập lại để làm gì? Bỏ đi thì sao?

Nó xác nhận transition đã thật sự lấy mất quyền. Khi follow-up nhận 2xx, tài khoản nạn nhân đăng nhập lại, chạy lại các
lời gọi của mình bằng token mới; token mới phải nhận 403. Thiếu bước này, một transition trả 2xx nhưng không hạ quyền
thật cũng sinh ra chuỗi 2xx, 2xx, 2xx và bị báo nhầm. Ví dụ thật: trên pyLoad, giá trị `role` gửi đi là số do tìm kiếm
để lại (373, 282, 883...), công cụ không tự suy ra; chính bước này xác nhận ở từng lượt rằng quyền đã mất.
- Chạy thêm lần không kèm thông tin xác thực: nếu cũng 403 thì 403 không phụ thuộc người gọi, bộ ba bị loại.
- Chạy sau follow-up vì có hệ thống chỉ cho mỗi tài khoản một phiên; đăng nhập lại trước sẽ làm token cũ thành 401.
- Giới hạn: nếu token mới vẫn mang quyền cũ thì bước này loại nhầm một lỗi thật. Hệ quả là bỏ sót, không báo nhầm.
- Trên reports-api, mã 403 ở bước này đến từ `POST /reports` đứng trước source. Không nói bước này gọi lại đúng thao
  tác được bảo vệ.

Nguồn: `docs/metamorphic-authz-relations.md` §5.6.

### 1.23 Vì sao gọi là Oracle 970?

EvoMaster đánh số mỗi loại lỗi. File `ExperimentalFaultCategory.kt` ghi `//9xx for experimental, work-in-progress
oracles`. Ở v6.1.1 các số đã dùng là 911–921, 940–944, 950–965 và 980; 970 là số tròn còn trống. Vì thuộc nhóm thử
nghiệm, oracle chỉ chạy khi bật `--useExperimentalOracles true`.
- Từ v6.2.0 upstream dùng 970 cho `RPC_INTERNAL_ERROR`. Muốn đưa vào upstream thì phải đổi số.

Nguồn: `ExperimentalFaultCategory.kt:12` (v6.1.1); `docs/related-work.md` §2a.

### 1.24 36/50 nghĩa là gì? Vì sao không phải 50/50?

50 lượt trên biến thể có lỗ hổng: reports-api 20, vampi-seeded 20, pyLoad 5, artifact-keeper 5. Oracle 970 báo lỗi ở 19,
7, 5 và 5 lượt. Cả 14 lượt bỏ sót đều là lượt không dựng được bộ ba; bộ ba nào dựng được trên bản lỗi cũng ra 970.
- vampi-seeded thấp (7/20) vì tìm kiếm phá điều kiện tiền đề: test sinh ra gọi `DELETE /users/v1/{username}` xóa
  tài khoản nạn nhân `name1`, hoặc hạ quyền khiến source nhận 403. Hai việc này làm giảm tỷ lệ phát hiện, không gây
  báo nhầm.

Nguồn: `docs/results.md` §1a, §7.

### 1.25 0 báo động giả trên 48 lượt, sao lại nói 30?

48 lượt chạy trên biến thể đã vá, 30 lượt dựng được bộ ba (reports-api 19, vampi-seeded 6, pyLoad 5, artifact-keeper 0).
18 lượt không dựng được bộ ba thì oracle không có gì để phán, nên không phải bằng chứng. Con số có nghĩa là 0 báo nhầm
trên 30 bộ ba chạy trên mã đã vá; khoảng tin cậy Clopper–Pearson 95% của tỷ lệ báo nhầm là 0–11,6%.

Nguồn: `docs/results.md` §1.

### 1.26 Em tự gieo lỗi rồi tự phát hiện, có thiên vị không?

Có rủi ro đó, nên khóa luận thêm hai lỗi em không viết: pyLoad (CVE do bên thứ ba công bố) và artifact-keeper (lỗi
nhà phát triển tự vá). Hai app lỗi gieo dùng để đo trên mã kiểm soát được, mỗi app có bản đã vá để đếm báo nhầm.
- Vẫn phải nói: pyLoad và artifact-keeper là app dùng trong lúc phát triển bộ dựng. Năm bản sửa bộ dựng được viết khi
  chạy pyLoad, ba bản khi chạy artifact-keeper. Mã công cụ không chứa chuỗi nào riêng của hai app, nhưng khóa luận
  không khẳng định tỷ lệ phát hiện trên app chưa từng chạy.
- Đường dẫn `/role` của vampi-seeded do em đặt.

Nguồn: `docs/argument.md` K2, K3.

### 1.27 Biến thể đã vá do ai viết?

reports-api và vampi-seeded: em viết. pyLoad: em viết; bản vá đọc vai trò từ cơ sở dữ liệu như nhánh `X-API-Key` sẵn
có của pyLoad. artifact-keeper: bản vá của nhà phát triển, commit `e64cc5c608`.
- pyLoad có bản vá upstream từ dev98 (commit `e95804fb`, 2026-04-13): xóa mọi phiên của người dùng khi quyền đổi qua
  `/json/update_users`, khi đổi mật khẩu hay xóa tài khoản. Ghi chép cũ trong repo ("upstream never fixed") sai: nó chỉ
  so hàm `is_authenticated`, còn bản vá nằm ở `json_blueprint.py`.
- Nếu hỏi sao không dùng bản vá upstream làm đối chứng: bản vá đó xóa phiên, nên ở đường nó phủ, cookie cũ không cho
  mã 403 mà oracle cần (giống bản vá artifact-keeper). Thêm nữa, đọc mã wheel trên PyPI: ở dev98–dev101,
  `set_user_permission` của tầng API, đường công cụ dùng, chưa xóa phiên; nhánh `develop` đã thêm. Chưa chạy công cụ
  trên dev98–dev101, nên không khẳng định lỗi còn ở các bản đó.

Nguồn: `docs/tier2b-pyload-target.md` §3; `docs/results.md` §5; advisory GHSA-66hx-chf7-3332 và commit
`pyload/pyload@e95804fb`, đọc ngày 2026-11-10.

### 1.28 Vì sao reports-api và vampi-seeded chạy 20 lượt mỗi biến thể, hai app kia ít hơn?

Một lượt pyLoad chạy 10 phút, một lượt artifact-keeper chạy 1.200 giây; hai app lỗi gieo chỉ 150 giây. pyLoad chạy 5 lượt
mỗi biến thể; artifact-keeper 5 lượt bản lỗi và 3 lượt bản vá. Số lượt đó vẫn đủ cho kiểm định Fisher một phía giữa bản
lỗi và bản vá: pyLoad p = 0,004; artifact-keeper p = 0,018.

Nguồn: `docs/results.md` §0, §1.

### 1.29 Giải thích hình 1.1.

Ba ô trên là ba bước: tài khoản quản trị gửi thao tác ghi bằng token c và nhận 2xx; quản trị viên khác hạ vai trò của tài
khoản này, token c vẫn còn hạn; tài khoản gửi lại thao tác bằng token c. Ô quyết định hỏi máy chủ có tra lại vai trò hiện
hành không. Có thì trả 403, đúng. Không thì trả 2xx, đó là lỗ hổng.
