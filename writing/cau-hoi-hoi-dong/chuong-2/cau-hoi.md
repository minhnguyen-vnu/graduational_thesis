# Chương 2. Cơ sở lý thuyết và công việc liên quan: câu hỏi hội đồng

Đoạn đầu mỗi câu là câu trả lời nói trong khoảng 30 giây. Phần sau dùng khi bị hỏi tiếp. Dòng `Nguồn` để tự tra lại.
Đường dẫn bắt đầu bằng `EvoMaster/` là repo `/Users/minhnguyen/IdeaProjects/EvoMaster`, nhánh `stateful-authz-oracle`.

## Khái niệm phải giải thích được

| Khái niệm | Nghĩa | Ví dụ |
|---|---|---|
| Kiểm thử dựa trên tìm kiếm (SBST) | Coi việc sinh test là bài toán tối ưu: thuật toán tìm kiếm sinh test và giữ test theo một hàm đánh giá. | EvoMaster giữ test làm hiện ra một mã trạng thái mới. |
| Mục tiêu (testing target) | Thứ quá trình tìm kiếm cố đạt tới. | Mã 403 của `PUT /reports/{id}`. |
| Hàm fitness | Điểm cho biết một test đạt hoặc tiến gần mục tiêu tới đâu. | Ở hộp đen, chạm được mục tiêu thì điểm 1. |
| MIO | Thuật toán mặc định của EvoMaster ở chế độ hộp trắng, giữ một quần thể test riêng cho từng mục tiêu. | Mô tả ở câu 2.2. |
| SMARTS | Thuật toán mặc định ở chế độ hộp đen: mỗi vòng sinh một test mới, phần lớn bằng chiến lược dựng chuỗi lời gọi liên kết. | Cả 98 lượt chạy của khóa luận dùng SMARTS. |
| Kho lưu trữ (archive) | Nơi EvoMaster giữ test tốt nhất cho từng mục tiêu. | Mục tiêu đã đạt chỉ giữ một test, ưu tiên test ngắn hơn. |
| Hộp đen, hộp trắng | Hộp đen chỉ dùng đặc tả và HTTP; hộp trắng phân tích cả mã của app. | Hộp trắng của EvoMaster chỉ cho app JVM. |
| Rút gọn test (minimization) | Pha bỏ các lời gọi thừa khỏi test giữ lại. | Chạy trước pha bảo mật. |
| Pha kiểm thử bảo mật | Pha chạy sau tìm kiếm, dựng thêm test bảo mật từ kho lưu trữ. | Bộ dựng MR-A1 chạy trong pha này. |
| Oracle kiểm thử | Cơ chế quyết định kết quả của test là đúng hay sai. | Quy tắc "mã 500 là lỗi". |
| Bài toán thiếu oracle | Không biết, hoặc rất tốn công mới biết, kết quả đúng của một test. | Không biết `PUT /reports/505` nên trả 200 hay 403. |
| Kiểm thử biến hình | Kiểm quan hệ giữa kết quả của nhiều lần chạy thay vì kiểm từng kết quả. | sin(x) = sin(π − x). |
| Quan hệ biến hình | Quy luật ràng buộc đầu vào và đầu ra của các lần chạy liên quan. | MR-A1. |
| Source test, follow-up test | Lần chạy gốc và lần chạy sau khi biến đổi có chủ đích. | Source: `PUT /reports/505` trước khi hạ quyền. |
| Kiểm soát truy cập | Cơ chế quyết định chủ thể nào được làm thao tác nào trên tài nguyên nào. | alice được sửa báo cáo 505. |
| BOLA | API không kiểm quyền của chủ thể trên đúng đối tượng được yêu cầu. | Đổi id tài khoản trong URL và đọc được sao kê của người khác. |
| BFLA | API không kiểm quyền gọi một chức năng. | VIEWER gọi được `DELETE /admin/users/42`. |
| Oracle so chéo tài khoản | So phản hồi của nhiều tài khoản cho cùng thao tác tại cùng thời điểm. | Các oracle của Şahin và cộng sự. |
| RBAC | Mô hình gán quyền cho vai trò, rồi gán vai trò cho người dùng. | Vai trò ADMIN có quyền sửa báo cáo. |
| DeassignUser, RevokePermission | Hai lệnh thu hồi của chuẩn RBAC: gỡ người dùng khỏi vai trò, gỡ quyền khỏi vai trò. | Gỡ alice khỏi ADMIN. |
| CWE-613, CWE-1464 | Loại điểm yếu về phiên; 613 đã ngừng dùng, 1464 là "Improper Session Invalidation". | Lỗi của pyLoad. |
| RESTler | Công cụ kiểm thử REST API của Microsoft, sinh chuỗi lời gọi từ quan hệ tạo và dùng tài nguyên. | ICSE 2019. |
| Checker | Bộ kiểm lỗi của RESTler chạy sau một chuỗi lời gọi. | `UseAfterFreeChecker`. |
| Baseline | Phương pháp có sẵn dùng để so sánh. | Các oracle phân quyền có sẵn trong EvoMaster v6.1.1. |
| Upstream | Bản EvoMaster do nhóm phát triển EvoMaster duy trì. | `WebFuzzing/EvoMaster`, nhánh `master`. |

## A. Kiểm thử REST API dựa trên tìm kiếm (mục 2.1)

### 2.1 Kiểm thử dựa trên tìm kiếm là gì?

Coi việc sinh test là bài toán tối ưu. Ta định nghĩa các mục tiêu cần đạt và một hàm đánh giá; thuật toán tìm kiếm sinh
và biến đổi test, giữ những test đạt nhiều mục tiêu nhất trong ngân sách thời gian. Với EvoMaster ở chế độ hộp đen, mỗi
cặp mã trạng thái và endpoint là một mục tiêu; ngân sách của khóa luận là `--maxTime 150s` cho reports-api.

### 2.2 MIO hoạt động thế nào?

MIO giữ một quần thể test nhỏ riêng cho từng mục tiêu. Mỗi vòng, với xác suất Pr nó sinh một test ngẫu nhiên mới; còn lại
nó chọn một mục tiêu chưa đạt, lấy một test trong quần thể của mục tiêu đó và đột biến. Test mới được chạy, rồi được
đưa vào quần thể của những mục tiêu nó cải thiện. Càng về sau càng tập trung: Pr giảm dần từ 0,8 về 0 và kích thước
quần thể từ 10 về 1, cho tới khi dùng hết 80% ngân sách.
- Mục tiêu đã đạt chỉ giữ một test; test mới ngắn hơn sẽ thay test cũ.
- Mục tiêu được chọn dựa trên bộ đếm số lần chọn mà không cải thiện; bộ đếm về 0 khi có cải thiện.
- Các giá trị trên là mặc định của EvoMaster 6.1.1.

Nguồn: `EvoMaster/core/src/main/kotlin/org/evomaster/core/search/algorithms/MioAlgorithm.kt`;
`EMConfig.kt:1542` (`archiveTargetLimit = 10`), `:1546` (`probOfRandomSampling = 0.8`),
`:1550` (`focusedSearchActivationTime = 0.8`); `search/service/Archive.kt:169–217`.

### 2.3 Các lượt chạy của em có dùng MIO không?

Không. Ở chế độ hộp đen, khi không truyền `--algorithm`, EvoMaster 6.1.1 chọn SMARTS; MIO là mặc định của chế độ hộp
trắng. Harness của khóa luận chạy `--blackBox true` và không truyền `--algorithm`, nên cả 98 lượt dùng SMARTS. Khóa luận
ghi điều này ở mục 2.1 và 4.1.
- SMARTS không đột biến test cũ. Mỗi vòng nó sinh một test mới: 95% bằng chiến lược thông minh, tức dựng chuỗi lời gọi
  liên kết với nhau, chẳng hạn một DELETE lên đúng tài nguyên vừa được POST tạo ra; còn lại sinh ngẫu nhiên. Test đạt
  mục tiêu mới thì vào kho lưu trữ, giống MIO.
- Nếu hỏi sao không chạy MIO: chạy được bằng `--algorithm MIO`, nhưng khóa luận giữ mặc định của công cụ cho cả baseline
  lẫn phần mở rộng, và chưa đo với MIO. Pha bảo mật chỉ đọc kho lưu trữ, không phụ thuộc thuật toán nào lấp đầy kho.

Nguồn: `EMConfig.kt:76–78` (`defaultAlgorithmForBlackBox = Algorithm.SMARTS`), `:680–681`, `:1917`
(`probOfSmartSampling = 0.95`); `search/algorithms/SmartsAlgorithm.kt`; `problem/rest/service/sampler/RestSampler.kt:40–56`;
`infra/em-results/m2-wave1-20261108/m2_wave1.sh:64–97`.

### 2.4 Ở chế độ hộp đen, "mục tiêu" cụ thể là gì?

Mỗi cặp mã trạng thái và endpoint là một mục tiêu, chẳng hạn 403 của `PUT /reports/{id}`. Ngoài ra còn các lỗi phát
hiện được (như mã 500) và một số mục tiêu về xác thực. Test chạm mục tiêu thì được giữ.
- Hệ quả cho bài toán: một VIEWER gọi `PUT /reports/{id}` nhận 403 là đã đạt mục tiêu đó. Chuỗi "200, hạ quyền, 200
  bằng token cũ" không làm hiện ra mục tiêu mới nào, nên tìm kiếm không có lý do giữ nó. Vì vậy phải dựng có chủ đích
  sau tìm kiếm.

Nguồn: `problem/rest/service/fitness/AbstractRestFitness.kt:389–410` (dòng `handleLocalTarget("$status:$name")`).

### 2.5 Hộp đen và hộp trắng khác nhau thế nào?

Hộp đen chỉ có đặc tả OpenAPI và địa chỉ của app đang chạy; chỉ thấy request và response. Hộp trắng phân tích bytecode
của app để đo độ phủ mã và dùng thông tin trong mã dẫn đường cho tìm kiếm. EvoMaster chỉ hỗ trợ hộp trắng cho app JVM;
pyLoad (Python) và artifact-keeper (Rust) chỉ chạy được hộp đen.

Nguồn: `EvoMaster/README.md:113–121`.

### 2.6 Kho lưu trữ là gì? Pha bảo mật lấy gì từ đó?

Kho lưu trữ ánh xạ mỗi mục tiêu tới vài test tốt nhất cho mục tiêu đó; mục tiêu đã đạt chỉ giữ một test. Bộ test xuất
ra cuối cùng lấy từ kho này. Pha bảo mật đọc toàn bộ test trong kho, dùng chúng làm nguyên liệu (request hợp lệ, đúng
tham số, đúng tài khoản), dựng test mới rồi đưa test mới vào lại kho.

Nguồn: `RestSecurityBuilder.kt:134` ở v6.1.1 (`archive.extractSolution()`); `Archive.kt` (`addIfNeeded`).

### 2.7 Pha kiểm thử bảo mật chạy lúc nào? Ngân sách bao nhiêu?

Thứ tự trong EvoMaster: tìm kiếm, rút gọn test, pha bảo mật, các oracle HTTP, kiểm test chập chờn, rồi xuất test. Mỗi pha
sau tìm kiếm có trần thời gian bằng `--extraPhaseBudgetPercentage` nhân với `--maxTime`, không tính vào `--maxTime`.
Khóa luận đặt 0,6 cho reports-api, vampi-seeded, pyLoad và 0,25 cho artifact-keeper. Ví dụ reports-api: pha bảo mật
tối đa 0,6 × 150 giây = 90 giây.
- Comment của upstream giải thích vì sao pha bảo mật chạy trước các oracle HTTP: mã 403 hiếm khi xuất hiện trong lúc tìm
  kiếm mà được tạo ra có chủ đích trong pha bảo mật "by mixing different users in the same test".

Nguồn: `Main.kt:269–274`; `EMConfig.kt:2748–2756`; `docs/results.md` §0.

### 2.8 Vì sao gắn oracle vào pha bảo mật mà không biến nó thành mục tiêu tìm kiếm?

Ba lý do. Chuỗi cần dựng có cấu trúc cố định (source, transition, follow-up với cùng token), dựng thẳng thì chắc hơn chờ
tìm kiếm ngẫu nhiên gặp. Pha bảo mật có sẵn kho lưu trữ chứa request hợp lệ. Không đổi tìm kiếm thì baseline và phần mở
rộng chạy cùng một quá trình tìm kiếm, khác biệt chỉ nằm ở oracle.

### 2.9 Giải thích hình 2.1.

Hàng trên là pha tìm kiếm: đặc tả OpenAPI vào thuật toán SMARTS, thuật toán gửi request qua bộ thực thi HTTP tới app
và giữ test vào kho lưu trữ. Hàng dưới là pha bảo mật: bước sinh phản hồi 403 và các oracle có sẵn, rồi tới hai khối do
khóa luận thêm (viền đậm, ghi "khóa luận bổ sung"): bộ dựng MR-A1 gửi bộ ba HTTP tới app, bộ phán quyết Oracle 970 đọc
kết quả và ghi lỗi vào bộ test xuất ra.

## B. Kiểm thử biến hình (mục 2.2)

### 2.10 Oracle là gì? Bài toán thiếu oracle là gì? Bài toán của em gặp nó ở đâu?

Oracle là cơ chế quyết định kết quả của một test là đúng hay sai. Bài toán thiếu oracle là khi không biết, hoặc rất tốn
công mới biết, kết quả đúng. Ở đây: `PUT /reports/505` trả 200 đúng hay sai tùy alice đang có vai trò gì, mà đặc tả
OpenAPI không ghi ai được gọi thao tác nào. Kiểm thử biến hình né bài toán này bằng cách so hai lần gọi với nhau.
- Oracle chính của EvoMaster là oracle ngầm định: mã 500 là lỗi, không cần biết kết quả đúng.
- Tóm tắt của khảo sát Barr và cộng sự (2015) nêu các kỹ thuật tự động hóa oracle: mô hình hóa, đặc tả, lập trình theo
  hợp đồng và kiểm thử biến hình. Khi không kỹ thuật nào đủ, con người là nguồn oracle cuối cùng.

Nguồn: tóm tắt bài, DOI `10.1109/TSE.2014.2372785`.

### 2.11 Kiểm thử biến hình là gì? Cho ví dụ kinh điển.

Thay vì kiểm từng kết quả, ta kiểm một quy luật giữa kết quả của nhiều lần chạy. Ví dụ kinh điển: không biết sin(1,234)
đúng bằng bao nhiêu, nhưng biết sin(x) phải bằng sin(π − x); chạy hai lần và so, lệch thì chương trình có lỗi.
- Ví dụ khác: đường đi ngắn nhất từ a tới b trên đồ thị vô hướng phải bằng từ b tới a.
- Khái niệm do Chen và cộng sự đưa ra năm 1998. "Biến hình" là cách khóa luận dịch chữ "metamorphic".

### 2.12 MR-A1 ứng với các phần của kiểm thử biến hình thế nào?

| Phần | Trong MR-A1 | Ví dụ reports-api |
|---|---|---|
| Source test | Thao tác a với token c, trước khi hạ quyền | alice `PUT /reports/505` nhận 200 |
| Biến đổi | Transition T hạ quyền của chủ thể | superadmin `PUT /users/alice/role` sang VIEWER |
| Follow-up test | Cùng thao tác a, cùng token c, sau T | alice `PUT /reports/505`, token cũ |
| Quan hệ | Source 2xx, a cần quyền mà T gỡ, thì follow-up phải 403 | Nhận 200 là vi phạm |

Nguồn: `docs/metamorphic-authz-relations.md` §2.2–2.3.

### 2.13 Kiểm thử biến hình khác kiểm thử so sánh (differential testing) thế nào?

Kiểm thử so sánh đưa cùng một đầu vào cho hai bản cài đặt, hoặc hai tài khoản, rồi so kết quả. Kiểm thử biến hình chạy
cùng một hệ thống với hai đầu vào có liên quan, rồi kiểm quy luật giữa hai kết quả. Oracle của Şahin và cộng sự gần với
kiểm thử so sánh: so các tài khoản. MR-A1 là biến hình: một tài khoản, một token, hai trạng thái phân quyền.

### 2.14 MR-A1 có phải là tính đơn điệu, "gỡ quyền thì quyền truy cập không được tăng"?

Không. Với lỗi này, quyền truy cập của alice không tăng: trước khi hạ quyền alice sửa được báo cáo, sau đó vẫn sửa được.
Tính đơn điệu không bị vi phạm. Thứ bị vi phạm là việc thực thi lệnh thu hồi: quyền đã gỡ vẫn được chấp nhận qua token
đã cấp. Vì vậy MR-A1 cần điều kiện thao tác phải cần đúng quyền bị gỡ; nếu không, `GET /reports`, thao tác VIEWER cũng
được làm, sẽ bị đọc thành lỗi.

Nguồn: `docs/metamorphic-authz-relations.md` §2.3, đoạn "Note".

### 2.15 Vi phạm quan hệ biến hình có chắc là lỗi không?

Vi phạm là bằng chứng hệ thống không thỏa thuộc tính được kiểm. Thuộc tính đó có bắt buộc hay không tùy chính sách của
từng hệ thống (câu 2.20). Phía cài đặt, khóa luận chặn các nguồn báo nhầm: chỉ phán quyết khi source và transition đều
2xx, follow-up không phải 401, thao tác cần đúng quyền bị gỡ, và token mới của nạn nhân bị từ chối.

## C. Kiểm soát truy cập (mục 2.3)

### 2.16 Xác thực, phân quyền và kiểm soát truy cập khác nhau thế nào?

Xác thực trả lời "bạn là ai", ví dụ đăng nhập bằng mật khẩu. Phân quyền trả lời "bạn được làm gì". Kiểm soát truy cập là
toàn bộ cơ chế thực thi phân quyền trên từng tài nguyên. Lỗi của khóa luận nằm ở phân quyền: server nhận đúng alice, chỉ
đọc sai vai trò của alice.

### 2.17 BOLA và BFLA khác nhau thế nào? Cho ví dụ.

BOLA: đúng chức năng nhưng sai đối tượng.
```
GET /accounts/1001/statement   token của An -> 200, sao kê của An
GET /accounts/1002/statement   token của An -> 200, sao kê của Bình   BOLA
```
BFLA: sai chức năng.
```
DELETE /admin/users/42   token của một VIEWER -> 204   BFLA, đúng ra 403
```
- Trang API1 của OWASP phân biệt: vào được endpoint hay chức năng không được phép là BFLA, không phải BOLA.

Nguồn: `https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/`.

### 2.18 Oracle phân quyền có sẵn trong EvoMaster v6.1.1 gồm những gì? Vì sao không bắt được lỗi này?

Bộ oracle bảo mật của v6.1.1 có các mã 204–208 về phân quyền, ví dụ 206 (cùng một tài khoản bị chặn PUT, PATCH nhưng lại
DELETE được tài nguyên) và 208 (sửa dữ liệu mà không cần đăng nhập). Tất cả so tài khoản hoặc so các phương thức tại một
thời điểm, không mô hình hóa việc quyền bị gỡ. Thêm nữa, EvoMaster đăng nhập lại mọi tài khoản ở đầu mỗi test, nên
baseline luôn cầm token mới và không bao giờ dùng token cũ.
- Đo trên vampi-seeded: 0/20 lượt baseline có chuỗi ghi, hạ quyền, ghi lại cùng biến xác thực; baseline vẫn báo lỗi 209
  (lộ stack trace) ở 17/20 lượt, tức baseline đã được cấu hình đúng.
- Tên đầy đủ các mã: 204 `SECURITY_EXISTENCE_LEAKAGE`, 205 `SECURITY_NOT_RECOGNIZED_AUTHENTICATED`,
  206 `SECURITY_WRONG_AUTHORIZATION`, 207 `SECURITY_IGNORE_ANONYMOUS`, 208 `SECURITY_ANONYMOUS_MODIFICATIONS`.
- Ở upstream mới, các mã này đã dời sang dải 300.

Nguồn: `DefinedFaultCategory` trong `com.webfuzzing:commons:0.6.0`; `docs/results.md` §8; `docs/related-work.md` §2a.

### 2.19 RBAC là gì? Lệnh thu hồi nào được nhắc?

RBAC gán quyền cho vai trò và gán vai trò cho người dùng; người dùng có quyền thông qua vai trò. Chuẩn RBAC mô tả các
lệnh quản trị như gán người dùng vào vai trò (AssignUser), gỡ người dùng khỏi vai trò (DeassignUser), cấp quyền cho vai
trò (GrantPermission), gỡ quyền khỏi vai trò (RevokePermission). Hạ alice từ ADMIN xuống VIEWER tương ứng DeassignUser
khỏi ADMIN rồi AssignUser vào VIEWER.

### 2.20 Chuẩn RBAC để ngỏ chuyện phiên đang mở. Vậy pyLoad giữ quyền tới khi đăng xuất có phải lỗi không?

Theo chuẩn thì chưa chắc. Ở lệnh DeassignUser, bản dự thảo của chuẩn để phía cài đặt chọn: chờ phiên kết thúc tự nhiên,
buộc chấm dứt phiên, hoặc vô hiệu vai trò trong phiên. Vì vậy MR-A1 không phải quy luật cho mọi hệ thống; nó đúng khi
chính sách của chính app yêu cầu thu hồi có hiệu lực ngay. Với bốn app, chính sách đó có căn cứ:
- pyLoad: bản ghi CVE coi việc giữ quyền đã thu hồi tới khi đăng xuất là lỗ hổng.
- artifact-keeper: nhà phát triển tự vá, commit tên "invalidate tokens on admin/role privilege change".
- reports-api, vampi-seeded: em đặt chính sách.

Khóa luận viết điều này ở mục 2.3 và 3.2. Báo cáo 970 là một vi phạm cần đối chiếu với chính sách của app.

Nguồn: bản dự thảo BSR INCITS 359, trang 17, mục DeassignUser; `writing/latex/references.bib` (`artifactkeeper1821`).

### 2.21 Vì sao trích bản dự thảo năm 2003 của chuẩn RBAC?

Bản ban hành ANSI INCITS 359-2004 là tài liệu phải mua, em không có. NIST lưu công khai bản dự thảo BSR INCITS 359
đề ngày 4/4/2003, và khóa luận ghi rõ đó là bản dự thảo. Hai bản có thể khác nhau, nên khóa luận chỉ trích bản dự thảo.
- File PDF nằm ở `infra/analysis/lexicon-rules/nist-bsr-incits-359-draft-2003-04-04.pdf`; đoạn DeassignUser ở trang 17.

### 2.22 CWE-1464 trong mục 2.3 nghĩa là gì?

Xem chương 1, câu 1.8.

## D. Công trình liên quan (mục 2.4)

### 2.23 RESTler là gì? "Có trạng thái" của RESTler khác của em thế nào?

RESTler là công cụ kiểm thử REST API của Microsoft (ICSE 2019). Nó đọc đặc tả, suy ra quan hệ tạo và dùng giữa các
request (request B cần id do request A tạo ra thì B chạy sau A), sinh chuỗi lời gọi và dùng phản hồi để tránh những chuỗi
bị server từ chối. "Có trạng thái" ở RESTler là trạng thái tài nguyên: tạo rồi mới dùng được. Ở khóa luận là trạng thái
phân quyền: quyền của một tài khoản trước và sau khi bị hạ.
- Bài báo tự nhận RESTler là "the first stateful REST API fuzzer" và báo cáo 28 lỗi trên GitLab.

Nguồn: tóm tắt bài, DOI `10.1109/ICSE.2019.00083`.

### 2.24 RESTler có checker nào gần bài toán của em?

Hai checker gần nhất:
- `UseAfterFreeChecker`: "Detects that a deleted resource can still be accessed after deletion." Cũng theo thời gian,
  nhưng về tài nguyên đã xóa, không về quyền.
- `NameSpaceRuleChecker` (tắt theo mặc định): "Detects that an unauthorized user can access service resources." Dùng
  một tài khoản khác làm kẻ tấn công, tức so chéo tài khoản như baseline.

Không checker nào kiểm quyền truy cập sau khi quyền bị hạ.

Nguồn: `https://github.com/microsoft/restler-fuzzer/blob/main/docs/user-guide/Checkers.md`, đọc ngày 2026-11-09.

### 2.25 Sao không chạy RESTler để so sánh?

RESTler không có checker nào cho lớp lỗi này, nên chạy chỉ ra con số 0 đã biết trước. Baseline nằm trong cùng EvoMaster
thì hai bên cùng tìm kiếm, cùng ngân sách, khác nhau chỉ ở oracle, nên so sánh công bằng hơn. Khóa luận chưa chạy RESTler;
nói thẳng như vậy.

### 2.26 Şahin và cộng sự đã làm gì? Vì sao chọn họ làm baseline?

Şahin, Zhang và Arcuri thêm 9 oracle bảo mật vào EvoMaster, chạy như một pha hậu xử lý sau tìm kiếm; các kiểm tra phân
quyền so nhiều tài khoản trên từng request. Đó là phương pháp gần nhất, có sẵn trong EvoMaster v6.1.1, nên là baseline
tự nhiên.
- Bài arXiv:2604.00702 (2026) chưa qua bình duyệt. Bản tiền thân cùng kiến trúc đã đăng ở ISSRE 2025 (Arcuri, Şahin,
  Zhang), khóa luận trích cả hai.
- Mục 5.4 của bài arXiv gọi các endpoint sửa thông tin đăng nhập của người dùng là "currently a major issue for fuzzers
  in black-box testing". Đây là một lý do hướng này chưa được làm.
- Phần hướng phát triển của bài không nhắc tới phân quyền có trạng thái.

Nguồn: `docs/related-work.md` §2.

### 2.27 Căn cứ nào cho câu "trong EvoMaster chưa có oracle nào kết hợp ba cơ chế của MR-A1"?

Hai lần kiểm. Kiểm mã: ngày 2026-10-02, so `v6.1.1` với `master` của upstream trên hai file oracle bảo mật được 58 dòng
thay đổi, không dòng nào dựng transition hay dùng lại token cũ; tìm theo các từ `stateful`, `revok`, `demot`, `downgrad`
không trúng file oracle nào; tìm trong issue và pull request ra 0 kết quả. Kiểm bằng chạy: upstream `master`
`ab983ba338`, seed 1–20 trên reports-api bản lỗi, 0/20 lượt báo lỗi thuộc lớp A1.

Nguồn: `docs/related-work.md` §2a; `docs/results.md` §8.

### 2.28 Ba cơ chế của MR-A1 là gì?

1. Tự dựng thao tác thu hồi quyền: chọn transition từ đặc tả bằng Naive Bayes, không cần người khai báo.
2. Dùng lại token cấp trước khi thu hồi: follow-up không đăng nhập lại.
3. Phán quyết dựa trên quan sát trước và sau: source 2xx, follow-up 2xx trong khi token mới bị 403.

### 2.29 Ngoài EvoMaster đã có ai làm chưa?

Khóa luận chỉ khẳng định trong phạm vi EvoMaster. Theo khảo sát ngày 2026-08-24 trong tài liệu dự án, chưa thấy công
trình đã công bố nào kiểm quyền truy cập sau khi quyền bị hạ trong một công cụ fuzz REST API. Các công trình gần nhất đều
so chéo tài khoản tại một thời điểm, ví dụ BACScan (CCS 2025, ứng dụng web) và GraphQLer (GraphQL).
- Chỉ nói tới mức tên và một câu như trên; khóa luận không trích hai bài này.

Nguồn: `docs/related-work.md` §1, §3.

### 2.30 Phần công trình liên quan chỉ có hai công trình, có mỏng không?

Mục 2.4 chỉ giữ công trình được đối chiếu trực tiếp: RESTler, một công cụ kiểm thử REST API có trạng thái, và oracle của
Şahin và cộng sự, là baseline. Khẳng định về tính mới vì thế thu hẹp trong EvoMaster và được kiểm trên mã nguồn và bằng
chạy thật.
- Chỗ yếu thật: quy định bộ môn yêu cầu chương lý thuyết có công trình liên quan, và hội đồng có thể cho là mỏng. Cách
  bổ sung ít rủi ro: một đoạn ngắn về BACScan và GraphQLer, mỗi bài một câu.
