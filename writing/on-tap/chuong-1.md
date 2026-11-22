# Chương 1. Giới thiệu: khái niệm cần ôn

Mọi khái niệm xuất hiện trong `latex/chapters/chapter1.tex`, xếp theo thứ tự đọc. Mỗi mục giải thích khái niệm, đưa ví dụ
(ưu tiên ví dụ thật trong khóa luận) và kết thúc bằng một dòng tham khảo để tra khi cần. Số liệu lấy từ jar TR2
(`docs/results.md`).

Ví dụ xuyên suốt: reports-api là ứng dụng quản lý báo cáo do khóa luận tự viết. Nó có ba tài khoản: `alice` (quản trị,
là người sẽ bị hạ quyền), `superadmin` (quản trị, không bao giờ bị hạ) và `bob` (`VIEWER`, chỉ được đọc).

---

## 1. Phân quyền, phiên và token

### Xác thực (authentication) và phân quyền (authorization)

Hai bước này hay bị gộp làm một nhưng trả lời hai câu hỏi khác nhau. Xác thực hỏi "người gọi là ai": máy chủ kiểm mật
khẩu, rồi cấp cho client một bằng chứng (token hoặc cookie) để những lần gọi sau không phải gửi lại mật khẩu. Phân quyền
hỏi "người này được làm gì": với mỗi yêu cầu, máy chủ xem vai trò của người gọi rồi cho làm hoặc từ chối.

Ví dụ trên reports-api:
```
POST /auth/login  {"username":"alice","password":"alicepass"}   -> 200, {"token": "eyJ..."}   xác thực
PUT  /reports/4   Authorization: Bearer eyJ...                    -> 200                         phân quyền: ADMIN được sửa
PUT  /reports/4   Authorization: Bearer <token của bob>           -> 403                         phân quyền: VIEWER không được sửa
```

Lỗi khóa luận tìm nằm ở bước phân quyền. Máy chủ vẫn nhận đúng người gọi là `alice`, nhưng quyết định dựa trên vai trò
cũ của cô.

*Tham khảo:* OWASP Authorization Cheat Sheet, https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html

### Vai trò, kiểm soát truy cập theo vai trò (RBAC)

Thay vì gán từng quyền cho từng người, hệ thống gom quyền thành vai trò rồi gán vai trò cho người dùng. Muốn đổi quyền
của một người thì đổi vai trò của người đó. Cách làm này gọi là RBAC (Role-Based Access Control).

Ví dụ: reports-api có hai vai trò. `ADMIN` được đọc, tạo, sửa, xóa báo cáo và đổi vai trò người khác. `VIEWER` chỉ được
đọc. Ba ứng dụng còn lại cũng có vai trò, chỉ khác cách lưu: vampi-seeded dùng vai trò `admin`/`user`, artifact-keeper
dùng cờ `is_admin` (`true`/`false`), pyLoad dùng trường số `role` (0 là quản trị, 1 là người dùng thường).

*Tham khảo:* Ferraiolo và cộng sự, *Proposed NIST Standard for Role-Based Access Control*, ACM TISSEC 2001, https://doi.org/10.1145/501978.501980

### Thu hồi quyền, hạ quyền

Thu hồi quyền là gỡ một quyền khỏi tài khoản. Trong RBAC, cách thường gặp là hạ vai trò, tức đổi sang vai trò ít quyền
hơn. Khóa luận gọi thao tác làm việc này là thao tác hạ quyền (hay thao tác chuyển trạng thái, transition).

Ví dụ, mỗi ứng dụng có một thao tác hạ quyền riêng:
```
reports-api      PUT   /users/alice/role                                    {"role": "VIEWER"}
vampi-seeded     PUT   /users/v1/{username}/role                            {"role": "user"}
artifact-keeper  PATCH /api/v1/users/{id}                                   {"is_admin": false}
pyLoad           POST  /api/set_user_permission?user=pyload&permission=1&role=1
```

### Thu hồi quyền "có hiệu lực ngay"

Câu hỏi then chốt của đề tài: sau khi bị hạ quyền, những phiên đăng nhập đang mở có mất quyền ngay không? Chuẩn RBAC
không bắt buộc điều đó. Bản nháp chuẩn INCITS 359 (§6.1.1, lệnh `DeassignUser`) để phía cài đặt tự chọn: chờ phiên tự
kết thúc, buộc phiên kết thúc, hoặc vô hiệu vai trò trong phiên. Nguyên văn: *"It is an implementation decision how to
proceed with the sessions in which the session user is user and one of his/her active roles is role. The RBAC system
could wait for such a session to terminate normally, could force its termination, or could inactivate the role."*

Hệ quả: một ứng dụng để phiên cũ giữ quyền tới khi hết hạn chưa chắc đã sai. Khóa luận chỉ gọi là lỗi khi chính ứng dụng
cam kết thu hồi ngay, và bằng chứng của cam kết đó là bản vá của nhà phát triển (artifact-keeper, pyLoad) hoặc biến thể
đã vá có chủ đích (hai ứng dụng tự gieo). Đây là câu hội đồng dễ hỏi: "Dựa vào đâu mà nói đây là lỗi?"

*Tham khảo:* bản nháp BSR INCITS 359, 4/4/2003, https://csrc.nist.gov/CSRC/media/Projects/Role-Based-Access-Control/documents/rbac-std-ncits.pdf (trích bản nháp, không trích bản ANSI 2004 trả phí)

### Thông tin xác thực (credential): token và cookie

Thông tin xác thực là thứ client gửi kèm mỗi yêu cầu để máy chủ nhận ra mình, cấp ra sau khi đăng nhập. Có hai dạng:

- Token: một chuỗi client tự gắn vào header, dạng `Authorization: Bearer <token>`. reports-api, vampi-seeded và
  artifact-keeper dùng dạng này.
- Cookie phiên: máy chủ gửi về một mã phiên qua header `Set-Cookie`, và trình duyệt tự gửi lại mã này ở mọi yêu cầu sau.
  pyLoad dùng dạng này.

Khóa luận hay nói "thông tin xác thực cấp trước lần thay đổi quyền", nghĩa là token hoặc cookie client nhận được trước khi
bị hạ quyền, gọi tắt là token cũ. Cả bài toán xoay quanh việc token cũ còn dùng được hay không.

*Tham khảo:* MDN, HTTP cookies, https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies

### Phiên (session)

Phiên là trạng thái đăng nhập máy chủ giữ cho một client. Client chỉ giữ mã phiên trong cookie, còn dữ liệu của phiên
(như người dùng là ai, vai trò gì) nằm phía máy chủ. Nếu máy chủ chép vai trò vào phiên lúc đăng nhập rồi sau đó chỉ đọc
bản chép, mọi thay đổi vai trò trong cơ sở dữ liệu sẽ không tới được phiên đang mở.

Ví dụ: đây chính là lỗi của pyLoad. Hàm `set_session()` chép `role` và `permission` vào phiên lúc đăng nhập. Khi kiểm
quyền, pyLoad đọc `session.get("role")`. Hàm `set_user_permission()` ghi vai trò mới vào cơ sở dữ liệu nhưng không xóa
phiên nào. Kết quả: admin bị hạ vẫn làm được việc của admin cho tới khi đăng xuất hoặc phiên hết hạn.

*Tham khảo:* OWASP Session Management Cheat Sheet, https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html

### JWT (JSON Web Token), claim, hạn token

JWT là token tự chứa thông tin. Nó gồm ba phần nối bằng dấu chấm, `header.payload.signature`. Payload là một đối tượng
JSON chứa các claim, tức cặp khóa–giá trị mô tả người dùng. Máy chủ ký token bằng khóa bí mật, nên client đọc được claim
nhưng không sửa được (sửa thì chữ ký sai). Nhờ đó máy chủ có thể tin claim mà không cần tra cơ sở dữ liệu ở mỗi yêu cầu.

Tiện lợi này đi kèm rủi ro: claim được ghi lúc đăng nhập và không đổi cho tới khi token hết hạn (claim `exp`). Nếu máy
chủ lấy vai trò từ claim, vai trò cũ sống cùng token.

Ví dụ: token reports-api cấp cho `alice` mang claim `sub: "alice"` và `role: "ADMIN"`, sống 1 giờ. Biến thể có lỗ hổng
đọc vai trò từ claim `role`, nên sau khi `alice` bị hạ xuống `VIEWER`, token cũ vẫn nói `ADMIN`. Biến thể đã vá bỏ qua
claim và tra vai trò hiện tại trong kho dữ liệu. artifact-keeper có cùng lỗi với claim `is_admin`, token sống 30 phút.

*Tham khảo:* RFC 7519, https://www.rfc-editor.org/rfc/rfc7519

---

## 2. Lớp lỗ hổng và các danh mục

### OWASP API Security Top 10 (2023)

OWASP là tổ chức phi lợi nhuận về an toàn ứng dụng. Danh sách API Security Top 10 xếp 10 nhóm rủi ro bảo mật API phổ biến
nhất, bản mới nhất năm 2023. Hai nhóm phân quyền đứng ở vị trí 1 và 5: API1 Broken Object Level Authorization (BOLA) và
API5 Broken Function Level Authorization (BFLA). Khóa luận dẫn danh sách này để cho thấy lỗi phân quyền là rủi ro hàng đầu
của API.

*Tham khảo:* https://owasp.org/API-Security/editions/2023/en/0x11-t10/

### BOLA và BFLA: lỗi phân quyền phi trạng thái

BOLA (mức đối tượng): người dùng truy cập được đối tượng không thuộc về mình, thường chỉ bằng cách đổi id trong đường dẫn.
BFLA (mức chức năng): người dùng gọi được chức năng dành cho vai trò cao hơn.

Ví dụ (giả định, reports-api không có hai lỗi này):
```
BOLA:  bob  GET /reports/4        -> 200   dù báo cáo 4 của alice và bob không được xem
BFLA:  bob  PUT /users/alice/role -> 200   dù bob chỉ là VIEWER
```

Hai lỗi này là phi trạng thái: chỉ cần một yêu cầu, ở một thời điểm bất kỳ, là lộ ra. Vì vậy công cụ phát hiện được
bằng cách so hai tài khoản cùng lúc. Lỗi của khóa luận thì không: trước khi hạ quyền, mọi yêu cầu của `alice` đều đúng
là được phép. Lỗi chỉ lộ ra khi so cùng một tài khoản ở hai thời điểm, trước và sau khi hạ quyền.

*Tham khảo:* API1 https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/, API5 https://owasp.org/API-Security/editions/2023/en/0xa5-broken-function-level-authorization/

### Broken Access Control và lỗ hổng phân quyền có trạng thái

Broken Access Control là thuật ngữ chuẩn của OWASP (mục A01 của OWASP Top 10 2021) cho mọi lỗi cho phép người dùng làm
việc ngoài quyền. Chữ "có trạng thái" (stateful) là khóa luận thêm vào. OWASP và CWE không có mục nào mang đúng tên này.

Định nghĩa của khóa luận (mục 1.2): hệ thống vẫn chấp nhận một thao tác cần quyền đã bị thu hồi, khi thao tác đó được
gửi bằng thông tin xác thực cấp trước lần đổi quyền. "Có trạng thái" vì kết quả phụ thuộc vào lịch sử: cùng một yêu
cầu, cùng một token, nhưng đúng hay sai tùy việc hạ quyền đã xảy ra chưa.

Hình 1.1 vẽ ba giai đoạn:
```
1. alice  PUT /reports/4  token c  -> 200      còn quyền, đúng
2. superadmin hạ alice xuống VIEWER            token c vẫn còn hạn
3. alice  PUT /reports/4  token c  -> ?        máy chủ tra lại vai trò: 403 (đúng)
                                               máy chủ tin token cũ:   200 (lỗ hổng)
```

*Tham khảo:* OWASP Top 10 2021, A01, https://owasp.org/Top10/A01_2021-Broken_Access_Control/

### CWE, CWE-1464, CWE-613

CWE (Common Weakness Enumeration) là danh mục các loại điểm yếu phần mềm do MITRE duy trì. Mỗi mục CWE mô tả một loại lỗi
chung, không gắn với sản phẩm nào. Ví dụ CWE-863 Incorrect Authorization là "kiểm quyền sai" nói chung.

CWE-1464 Improper Session Invalidation là loại lỗi gần nhất với đề tài. Mô tả của MITRE: *"The product establishes a
session for an authenticated user, but it does not properly invalidate or terminate the session when it is required."*
Tức hệ thống không hủy phiên khi lẽ ra phải hủy. Khóa luận viết "có thể thuộc" CWE-1464, vì cụm "when it is required"
chỉ đúng khi hệ thống cam kết hủy phiên lúc đổi quyền (xem mục "có hiệu lực ngay" ở trên).

CWE-613 Insufficient Session Expiration là mục cũ, nay MITRE đã đánh dấu DEPRECATED vì chưa đủ rõ, nên khóa luận không
dùng. Điểm hội đồng có thể hỏi: bản ghi CVE-2026-41133 của pyLoad vẫn gắn CWE-613. Câu trả lời là CWE-1464 thay cho mục
đã bị loại đó.

*Tham khảo:* https://cwe.mitre.org/data/definitions/1464.html, https://cwe.mitre.org/data/definitions/613.html

### CVE và CVSS

CVE là mã định danh cho một lỗ hổng cụ thể trong một sản phẩm cụ thể, dạng `CVE-năm-số`. So với CWE: CWE là loại lỗi
("không hủy phiên khi cần"), còn CVE là một lần loại lỗi đó xuất hiện trong một phần mềm ("pyLoad tới bản 0.5.0b3.dev97
không hủy phiên khi đổi quyền").

CVSS là thang điểm 0–10 đo mức nghiêm trọng của lỗ hổng, tính từ một vector gồm nhiều chỉ số. CVE-2026-41133 có điểm
CVSS 3.1 là 8,8 (mức HIGH), vector `AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H`. Đọc từng chỉ số:

| Chỉ số | Giá trị | Nghĩa |
|---|---|---|
| AV:N | Network | tấn công qua mạng |
| AC:L | Low | không cần điều kiện đặc biệt |
| PR:L | Low | cần một tài khoản, quyền thấp là đủ (tài khoản vừa bị hạ) |
| UI:N | None | không cần người khác thao tác |
| S:U | Unchanged | ảnh hưởng nằm trong chính pyLoad |
| C:H, I:H, A:H | High | ảnh hưởng cao tới bảo mật, toàn vẹn và tính sẵn sàng |

*Tham khảo:* bản ghi CVE https://cve.org/CVERecord?id=CVE-2026-41133, đặc tả CVSS 3.1 https://www.first.org/cvss/v3.1/specification-document

---

## 3. Hai ứng dụng có lỗi thật

### pyLoad

pyLoad là trình quản lý tải mã nguồn mở viết bằng Python, có giao diện web để thêm link tải, quản lý người dùng và phân
quyền. Lỗi CVE-2026-41133 nằm ở cách pyLoad lưu vai trò trong phiên (mục "Phiên" ở trên).

Ví dụ kiểm tay trong khóa luận, ba yêu cầu source, transition, follow-up:
```
biến thể có lỗ hổng   200 / 200 / 200     role của alice sau khi hạ: 1 (người dùng thường)
biến thể đã vá        200 / 200 / 403
```
Biến thể đã vá do khóa luận tự viết. Bản vá của nhà phát triển xóa phiên thay vì trả 403, nên không dùng làm đối chứng 403
được.

*Tham khảo:* https://github.com/pyload/pyload

### artifact-keeper và artifact registry

Artifact registry là máy chủ lưu và phân phối gói phần mềm: thư viện npm, gói Maven, ảnh Docker và các loại tương tự.
Một nhóm phát triển đẩy gói lên registry, còn máy build kéo gói về. artifact-keeper là một registry mã nguồn mở như vậy.

Lỗi: lúc đăng nhập, artifact-keeper ghi `is_admin` vào claim của JWT, rồi kiểm quyền bằng claim đó. Admin bị hạ
(`PATCH /api/v1/users/{id}` với `{"is_admin": false}`) vẫn giữ quyền admin tới khi token hết hạn sau 30 phút. Nhà phát triển
vá bằng cách vô hiệu hóa token khi quyền đổi (commit đóng issue #1821). Sau bản vá, token cũ nhận 401, không phải 403.

*Tham khảo:* commit vá, https://github.com/artifact-keeper/artifact-keeper/commit/e64cc5c608df4afdd0b35feae5f140a9d809a8f3

### Vì sao chọn hai ứng dụng này

Hai ứng dụng dùng hai cơ chế xác thực khác nhau (pyLoad dùng phiên, artifact-keeper dùng JWT) nhưng chung một nguyên
nhân: quyền được đọc từ bản sao tạo lúc đăng nhập thay vì từ trạng thái hiện tại. Cả hai lỗi do nhà phát triển của chính
ứng dụng viết, không do khóa luận cài vào. Câu cuối mục 1.1 của chương nói đúng ý này.

---

## 4. Kiểm thử REST API

### REST API, thao tác, thao tác ghi

REST là kiểu thiết kế API web: mỗi tài nguyên có một URL, còn client thao tác lên tài nguyên bằng phương thức HTTP. `GET`
để đọc, `POST` để tạo, `PUT`/`PATCH` để sửa, `DELETE` để xóa. Khóa luận gọi mỗi cặp phương thức và đường dẫn mẫu là một
thao tác (operation), ví dụ `PUT /reports/{id}`. Thao tác ghi là thao tác làm đổi dữ liệu, tức mọi phương thức trừ `GET`.

Ví dụ: `GET /reports/4` đọc báo cáo 4. `PUT /reports/4` kèm thân JSON mới thì sửa nó, nên là thao tác ghi. MR-A1 chỉ xét
thao tác ghi.

*Tham khảo:* https://en.wikipedia.org/wiki/REST

### Mã trạng thái HTTP: 2xx, 401, 403

Mỗi phản hồi HTTP mang một mã ba chữ số; chữ số đầu cho biết nhóm. `2xx` là thành công (200 OK, 201 Created, 204 No
Content). `4xx` là lỗi phía client. Hai mã quan trọng nhất của đề tài:

- 401 Unauthorized: máy chủ không biết bạn là ai, do thiếu token, token sai hoặc token bị vô hiệu.
- 403 Forbidden: máy chủ biết bạn là ai nhưng không cho làm.

Khóa luận coi `2xx` là cho phép, 403 là từ chối vì thiếu quyền, còn 401 là chưa kết luận được. Lý do là 401 không nói gì
về quyền: token cũ nhận 401 có thể vì quyền đã bị thu hồi, cũng có thể chỉ vì token hết hạn. Vì vậy bản vá của
artifact-keeper, trả 401, nằm ngoài phán quyết (điều kiện 3 ở mục 1.3 của chương).

Ví dụ trên reports-api: gửi `PUT /reports/4` không kèm token thì nhận 401; `bob` gửi kèm token của mình thì nhận 403.

*Tham khảo:* RFC 9110, mục 15.5.4, https://www.rfc-editor.org/rfc/rfc9110#name-403-forbidden

### Đặc tả OpenAPI

Đặc tả OpenAPI là một file JSON hoặc YAML mô tả toàn bộ API: có những đường dẫn nào, mỗi đường dẫn nhận phương thức gì,
tham số và thân yêu cầu có kiểu gì, và trả về những mã nào. Nó giống mục lục kèm hướng dẫn sử dụng của API. Công cụ hộp
đen như EvoMaster không đọc được mã nguồn, nên mọi hiểu biết về API đều lấy từ đặc tả.

Ví dụ: đặc tả của reports-api (`/v3/api-docs`) ghi `PUT /users/{username}/role` nhận thân có trường `role` với
`enum: ["ADMIN","VIEWER"]`. Từ đó công cụ biết `VIEWER` là giá trị hạ quyền hợp lệ.

*Tham khảo:* https://spec.openapis.org/oas/v3.0.3

### Ca kiểm thử (test case)

Một ca kiểm thử là một chuỗi lời gọi HTTP kèm lệnh kiểm tra kết quả. EvoMaster xuất ca kiểm thử thành mã Python: mỗi ca là
một hàm, gửi lần lượt các yêu cầu và `assert` mã trạng thái nhận được.

Ví dụ: ca 970 của reports-api seed 2 (Hình 4.3 của khóa luận) gồm ba lời gọi `PUT /reports/4`, `PUT /users/alice/role`,
`PUT /reports/4`, và kiểm rằng lời gọi cuối nhận 200, đúng mã đã quan sát khi chạy.

### Kiểm thử dựa trên tìm kiếm (search-based software testing)

Ý tưởng: coi việc sinh ca kiểm thử là bài toán tối ưu. Thuật toán sinh ca, chạy thử, chấm điểm theo những mục tiêu ca đó
đạt được (phủ thêm một dòng mã, nhận thêm một mã trạng thái mới trên một thao tác…), rồi giữ ca tốt và sinh tiếp ca mới.
Lặp tới khi hết thời gian.

Ví dụ (minh họa): ban đầu EvoMaster chỉ gọi `PUT /reports/4` bằng thân JSON ngẫu nhiên và nhận 400. Sau nhiều vòng, nó tìm được thân
hợp lệ và nhận 200. Ca nhận 200 đạt mục tiêu mới nên được giữ lại.

*Tham khảo:* McMinn, *Search-based software test data generation: a survey*, STVR 2004, https://doi.org/10.1002/stvr.294

### EvoMaster, upstream, nhánh chính

EvoMaster là công cụ mã nguồn mở tự sinh ca kiểm thử cho REST, GraphQL và RPC API theo cách tìm kiếm ở trên. Khóa luận
dùng chế độ hộp đen: EvoMaster chỉ đọc đặc tả OpenAPI và gửi yêu cầu HTTP tới ứng dụng đang chạy, không đụng mã nguồn ứng
dụng. Phần mở rộng của khóa luận dựa trên phiên bản 6.1.1.

Upstream là bản EvoMaster do chính các tác giả của nó duy trì trên GitHub, còn nhánh chính là nhánh phát triển mới nhất
của bản đó. Chương 1 nhắc việc chạy nhánh chính upstream trên một ứng dụng có lỗi, để cho thấy công cụ gốc không báo lỗi
này (kết quả ở mục 5.6).

*Tham khảo:* https://github.com/WebFuzzing/EvoMaster; Arcuri, ACM TOSEM 2019, https://doi.org/10.1145/3293455

### Oracle kiểm thử và bài toán oracle

Oracle là cơ chế quyết định kết quả một ca kiểm thử là đúng hay có lỗi. Oracle đơn giản nhất của EvoMaster: phản hồi mã
500 là lỗi, vì máy chủ không bao giờ nên sập.

Với lỗi phân quyền, mã trạng thái một mình không đủ. `PUT /reports/4` nhận 200 có thể đúng (`alice` còn là `ADMIN`) hoặc
sai (`alice` vừa bị hạ). Nhìn riêng một phản hồi, không thể biết. Khó khăn "không biết kết quả đúng là gì để so" gọi là
bài toán oracle (oracle problem). Kiểm thử biến hình (mục 5) là một cách giải.

*Tham khảo:* Barr và cộng sự, *The Oracle Problem in Software Testing: A Survey*, IEEE TSE 2015, https://doi.org/10.1109/TSE.2014.2372785

### Các oracle phân quyền hiện có của EvoMaster

Şahin và cộng sự thêm vào EvoMaster 9 oracle bảo mật, chạy trong một pha sau pha tìm kiếm. Các oracle phân quyền trong số
đó xét từng yêu cầu ở một thời điểm và so các tài khoản hoặc các phương thức với nhau.

Ví dụ: oracle mã 206 (`SECURITY_WRONG_AUTHORIZATION`, đánh số của EvoMaster 6.1.1) báo lỗi khi cùng một tài khoản, trên cùng một tài nguyên, bị từ chối `PUT` (403) nhưng lại `DELETE`
được (`2xx`). Tình huống đó mâu thuẫn ở ngay một thời điểm. Lỗi của khóa luận không mâu thuẫn ở thời điểm nào: trước khi hạ
quyền, 200 là đúng; sau khi hạ quyền, chỉ có một yêu cầu bằng token cũ. Muốn thấy lỗi phải nhớ rằng lần trước được phép và
giữa hai lần đã có một lần hạ quyền, điều các oracle hiện có không làm. Khóa luận coi các oracle này là baseline.

*Tham khảo:* Şahin, Zhang, Arcuri, arXiv:2604.00702, https://arxiv.org/abs/2604.00702v1

---

## 5. Phương pháp của khóa luận

### Kiểm thử biến hình và quan hệ biến hình (metamorphic relation)

Khi không biết kết quả đúng của một lần chạy, ta vẫn kiểm được quan hệ giữa kết quả của nhiều lần chạy có liên quan.
Quan hệ đó gọi là quan hệ biến hình.

Ví dụ kinh điển: kiểm hàm `sin`. Không cần biết `sin(1,234)` chính xác bằng bao nhiêu, nhưng biết chắc
`sin(x) = sin(π − x)`. Chạy hai lần với `x` và `π − x`, nếu hai kết quả khác nhau thì hàm có lỗi.

Áp vào đề tài: không cần biết `PUT /reports/4` lẽ ra phải trả gì. Chỉ cần biết nếu lần đầu được phép (200), rồi quyền bị
gỡ, thì lần sau bằng cùng token phải bị từ chối (403). Hai lần chạy liên quan với nhau qua thao tác hạ quyền ở giữa.

*Tham khảo:* Chen và cộng sự, *Metamorphic Testing: A Review of Challenges and Opportunities*, ACM Computing Surveys 2018, https://doi.org/10.1145/3143561; bài gốc Chen, Cheung, Yiu, HKUST-CS98-01, 1998

### MR-A1

Quan hệ biến hình của khóa luận, phát biểu: một thao tác ghi cần đúng quyền bị gỡ, đã nhận `2xx` khi còn quyền, phải nhận
403 sau khi quyền đó bị gỡ, nếu vẫn dùng thông tin xác thực cũ.

Ba chữ trong câu cần để ý:
- "cần đúng quyền bị gỡ": `GET /reports` không tính, vì `VIEWER` cũng được đọc. Sau khi hạ quyền, nó vẫn nhận 200 và
  điều đó đúng.
- "đã nhận `2xx` khi còn quyền": nếu lần đầu đã thất bại thì không có gì để so.
- "thông tin xác thực cũ": nếu `alice` đăng nhập lại sau khi bị hạ, token mới mang `VIEWER` và lỗi bị che mất.

A1 là quan hệ đầu tiên của nhóm A (hạ vai trò). A2 (chuyển quyền sở hữu) và A3 (quyền hết hạn) đã định nghĩa nhưng khóa
luận chưa kiểm chứng.

### Oracle 970

Phần phán quyết khóa luận thêm vào EvoMaster. 970 là mã lỗi gán cho vi phạm, tên trong mã là
`SECURITY_STATEFUL_AUTHORIZATION`. Khi một bộ ba vi phạm MR-A1, ca kiểm thử xuất ra có dòng chú thích `970` ngay trước
follow-up, và `report.json` ghi một lỗi mã 970.

Điểm hội đồng có thể hỏi: từ v6.2.0, upstream đã gán 970 cho `RPC_INTERNAL_ERROR`. Số 970 chỉ đúng trên nền v6.1.1, và
phải đổi nếu đưa mã lên bản mới hơn.

### Pha tìm kiếm và pha kiểm thử bảo mật

Một lượt chạy EvoMaster đi qua ba pha theo thứ tự: tìm kiếm (sinh ca kiểm thử như mô tả ở mục 4), rút gọn (bỏ những lời
gọi thừa), rồi kiểm thử bảo mật, nơi công cụ lấy các ca đã có để dựng thêm ca mới nhắm vào lỗi bảo mật.

Oracle 970 chạy trong pha kiểm thử bảo mật. Vì thế khóa luận không sửa thuật toán tìm kiếm: mọi ca tìm kiếm sinh ra giống
hệt EvoMaster gốc, phần mở rộng chỉ thêm việc sau đó.

### Kho lưu trữ ca kiểm thử (archive)

Trong lúc tìm kiếm, EvoMaster giữ một kho lưu trữ: với mỗi mục tiêu đã đạt, kho giữ một ca đạt mục tiêu đó (ưu tiên ca
ngắn). Khi bật pha kiểm thử bảo mật, mục tiêu tính theo từng tài khoản, ví dụ "`alice` gọi `PUT /reports/{id}` và nhận
`2xx`".

Ví dụ: bộ dựng MR-A1 tìm trong kho một ca có `alice` gọi thao tác ghi và nhận `2xx`. Ca đó trở thành source, kèm theo các
lời gọi chuẩn bị dữ liệu đứng trước nó.

*Tham khảo:* Arcuri, *Many Independent Objective (MIO) Algorithm for Test Suite Generation*, SSBSE 2017, https://doi.org/10.1007/978-3-319-66299-2_1

### Cấu hình xác thực và quan sát HTTP

Cấu hình xác thực là file YAML khai cho EvoMaster các tài khoản và cách đăng nhập của từng tài khoản. Ví dụ
`infra/em-config/reports-auth.yaml` ghi: đăng nhập qua `POST /auth/login` với `{username, password}`, lấy token ở trường
`token`, với ba tài khoản `alice`, `superadmin`, `bob`. Bộ dựng cần file này để biết ai có thể làm nạn nhân và ai làm tài
khoản quản trị.

Quan sát HTTP là các cặp yêu cầu–phản hồi EvoMaster đã gửi và nhận trong lúc chạy. Bộ dựng đọc chúng để biết tài khoản nào
từng gọi được thao tác nào.

### Ba điều kiện áp dụng

Phương pháp chỉ dùng được khi đủ ba điều kiện, mỗi điều kiện gắn với một bước:

1. Thao tác hạ quyền gọi được qua REST API, vì công cụ phải tự gọi transition. Nếu hạ quyền chỉ làm được bằng tay trong
   cơ sở dữ liệu, công cụ không dựng được bộ ba.
2. Tài khoản bị hạ quyền đăng nhập lại được, vì bước đăng nhập lại cần token mới. Thao tác xóa tài khoản không thỏa:
   tài khoản đã xóa thì không đăng nhập được.
3. Máy chủ trả 403 khi từ chối vì thiếu quyền, vì phán quyết đọc 403 là từ chối. Bản vá của artifact-keeper trả 401
   nên không thỏa.

### Bộ ba source, transition, follow-up

Ba lời gọi dựng một lần kiểm MR-A1:
- source: nạn nhân gọi thao tác ghi khi còn quyền, bằng token T;
- transition: tài khoản quản trị hạ quyền nạn nhân;
- follow-up: nạn nhân gửi lại đúng source, vẫn bằng token T.

Ví dụ thật, reports-api seed 2:
```
alice       PUT /reports/4                      token T   -> 200   source
superadmin  PUT /users/alice/role  VIEWER                 -> 200   transition
alice       PUT /reports/4                      token T   -> 200   follow-up: vi phạm 970
```
Trên biến thể đã vá, follow-up nhận 403: không vi phạm.

### Điều kiện tiền đề và bộ ba bị hủy (VOID)

Không phải bộ ba nào cũng phán quyết được. Bộ ba chỉ có giá trị khi source nhận `2xx` (lần đầu thật sự được phép),
transition nhận `2xx` (việc hạ quyền thật sự xảy ra) và follow-up nhận một mã khác 401. Bộ ba không thỏa bị hủy (VOID) và
không là bằng chứng cho chiều nào.

Ví dụ: trên vampi-seeded, pha tìm kiếm đã xóa mất tài khoản kiểm thử, nên source nhận 401. Bộ ba đó bị hủy, không được đếm
là vi phạm hay không vi phạm.

### Naive Bayes và xếp hạng thao tác chuyển trạng thái

Công cụ phải tự tìm thao tác hạ quyền trong đặc tả, mà artifact-keeper có tới 216 thao tác ghi. Khóa luận dùng Naive Bayes,
một mô hình phân loại đơn giản: mỗi đặc trưng (một từ trong đường dẫn, tên trường, phương thức) có một trọng số học từ dữ
liệu gán nhãn, rồi điểm của thao tác là tổng các trọng số. Chữ "naive" (ngây thơ) là vì mô hình giả định các đặc trưng độc
lập với nhau.

Ví dụ: `PUT /users/{username}/role` có các từ `users`, `role` và phương thức `PUT`, đều thường gặp ở thao tác hạ quyền
trong dữ liệu học, nên được điểm cao và xếp hạng 1 trên reports-api. Trên artifact-keeper, `PATCH /api/v1/users/{id}`
xếp hạng 3 trong 4 ứng viên dùng được. Mô hình học từ 10.381 thao tác ghi, trong đó 209 thao tác hạ quyền. Công cụ thử lần
lượt từ ứng viên điểm cao nhất xuống.

*Tham khảo:* scikit-learn, https://scikit-learn.org/stable/modules/naive_bayes.html; cách tính của khóa luận ở `docs/naive-bayes.md`

### Trường vai trò và trường định danh tài khoản nạn nhân

Tìm được thao tác hạ quyền mới là một nửa. Công cụ còn phải biết gửi gì vào đâu:
- trường vai trò là chỗ đặt giá trị quyền mới;
- trường định danh nạn nhân là chỗ ghi tài khoản nào bị hạ.

| Ứng dụng | Trường định danh nạn nhân | Trường vai trò, giá trị hạ quyền |
|---|---|---|
| reports-api | `{username}` trong `/users/{username}/role` | `role` = `VIEWER` |
| artifact-keeper | `{id}` trong `/api/v1/users/{id}` | `is_admin` = `false` |
| pyLoad | tham số `user` | `permission`, `role` = `1` |

Mô hình chọn cả hai trường. Ứng viên không có trường định danh nạn nhân bị loại, vì không biết hạ quyền ai.

### Bước đăng nhập lại

Follow-up nhận `2xx` chưa đủ để báo lỗi. Có thể transition thật ra không hạ quyền (một endpoint tên "role" vẫn có thể
nâng quyền tùy giá trị gửi kèm), hoặc quyền bị gỡ không phải quyền mà source cần. Bước đăng nhập lại kiểm hai khả năng đó.

Cách làm: nạn nhân đăng nhập lại lấy token mới, rồi chạy lại chuỗi lời gọi của mình tới source. Bộ ba chỉ được giữ khi
đủ ba điều:
1. source nhận 403 với token mới, chứng tỏ vai trò hiện tại thật sự không được làm thao tác này;
2. mỗi lời gọi đứng trước source giữ nguyên nhóm mã (`2xx` vẫn `2xx`, `4xx` vẫn `4xx`) như trong bộ ba, chứng tỏ source
   chạy trên cùng trạng thái dữ liệu;
3. gửi source không kèm thông tin xác thực nhận mã khác 403, chứng tỏ 403 ở điều 1 đến từ vai trò chứ không phải máy chủ
   chặn mọi người.

Ví dụ reports-api seed 2: token mới của `alice` gọi `PUT /reports/4` nhận 403; gửi không token nhận 401. Bộ ba được giữ, và
Oracle 970 báo vi phạm.

Bước này chỉ chạy khi follow-up nhận `2xx`. Trong 100 lượt chạy, nó được áp cho 59 bộ ba, giữ 35 và hủy 24. Cả 24 bộ ba bị
hủy đều trên reports-api, do một lời gọi đứng trước source đổi nhóm mã.

---

## 6. Đánh giá

### Lỗi tự gieo: reports-api và vampi-seeded

Lỗi tự gieo là lỗi cố ý cài vào ứng dụng để biết trước đáp án, dùng kiểm xem công cụ có tìm ra không.

reports-api do khóa luận tự viết (Spring Boot). Hai biến thể chạy cùng một bản build, khác nhau ở một cờ cấu hình: biến
thể có lỗ hổng đọc vai trò từ claim JWT, biến thể đã vá đọc từ kho dữ liệu.

vampi-seeded dựng trên VAmPI, một API cố ý có lỗ hổng (viết bằng Flask) dùng để thử công cụ bảo mật. Khóa luận thêm vào
VAmPI một thao tác đổi vai trò và lỗi phân quyền có trạng thái.

*Tham khảo:* VAmPI, https://github.com/erev0s/VAmPI

### Biến thể có lỗ hổng và biến thể đã vá

Hai bản của cùng một ứng dụng, khác nhau đúng ở chỗ lỗi. Chạy trên biến thể có lỗ hổng để đo khả năng phát hiện: công cụ
nên báo lỗi. Chạy trên biến thể đã vá để đo báo động giả: công cụ không được báo lỗi. Vì mọi thứ khác giống nhau, chênh
lệch kết quả giữa hai biến thể chỉ có thể đến từ chỗ lỗi.

### Lượt chạy và seed

Một lượt là một lần chạy EvoMaster trên một biến thể. Seed là số khởi tạo bộ sinh ngẫu nhiên: cùng seed thì EvoMaster đưa ra
cùng chuỗi lựa chọn ngẫu nhiên, khác seed thì khám phá khác đi. Chạy nhiều seed để kết quả không phụ thuộc vào may rủi của
một lần.

Ví dụ: reports-api và vampi-seeded mỗi biến thể chạy 20 seed, pyLoad và artifact-keeper mỗi biến thể 5 seed, tổng cộng
(20 + 20 + 5 + 5) × 2 = 100 lượt.

### Phát hiện, bỏ sót, báo động giả (TP, FN, FP, TN)

Bốn loại kết quả của một lượt:

| | Có cảnh báo 970 | Không có cảnh báo |
|---|---|---|
| Biến thể có lỗ hổng | phát hiện (TP) | bỏ sót (FN) |
| Biến thể đã vá | báo động giả (FP) | âm tính thật (TN), nếu có bộ ba để phán quyết |

Kết quả của khóa luận: phát hiện ở 28/50 lượt trên biến thể có lỗ hổng (reports-api 12/20, vampi-seeded 6/20, pyLoad 5/5,
artifact-keeper 5/5). Trên biến thể đã vá có 0 báo động giả trong 50 lượt, và 31 lượt trong đó dựng được bộ ba. Cả 22 lượt
bỏ sót đều do không dựng được bộ ba hợp lệ, không có lượt nào dựng được bộ ba mà phán quyết sai.
