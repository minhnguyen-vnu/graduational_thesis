# Chương 2. Cơ sở lý thuyết và nghiên cứu liên quan: khái niệm cần ôn

Mọi khái niệm trong `latex/chapters/chapter2.tex`, theo thứ tự bốn mục của chương. Mỗi mục giải thích khái niệm, đưa ví
dụ (ưu tiên giá trị thật của khóa luận) và kết thúc bằng một dòng tham khảo. Khái niệm đã giải thích kỹ ở `chuong-1.md`
chỉ nhắc lại ngắn, rồi đi sâu vào phần chương 2 nói thêm.

Ví dụ xuyên suốt vẫn là reports-api với ba tài khoản `alice` (ADMIN, sẽ bị hạ), `superadmin` (ADMIN, không bị hạ) và
`bob` (VIEWER). Chi tiết mã nguồn EvoMaster đối chiếu trên tag `v6.1.1`.

---

## 1. Kiểm thử REST API dựa trên tìm kiếm (mục 2.1)

### Kiểm thử dựa trên tìm kiếm

Nhắc lại (`chuong-1.md` mục 4): công cụ coi việc sinh ca kiểm thử là bài toán tối ưu. Nó sinh ca, chạy thử, xem ca đạt
được mục tiêu nào, giữ ca có ích và sinh tiếp, tới khi hết thời gian. "Tìm kiếm" ở đây là tìm trong không gian rất lớn
của mọi chuỗi yêu cầu HTTP có thể gửi, chứ không phải tìm kiếm văn bản.

*Tham khảo:* Arcuri, *RESTful API Automated Test Case Generation with EvoMaster*, ACM TOSEM 2019, https://doi.org/10.1145/3293455

### Chế độ hộp đen và hộp trắng

EvoMaster có hai chế độ:

| | Hộp trắng (white-box) | Hộp đen (black-box) |
|---|---|---|
| EvoMaster thấy gì | Mã nguồn đã được gắn đo (biết dòng nào chạy qua) | Chỉ đặc tả OpenAPI và phản hồi HTTP |
| Cần gì từ ứng dụng | Viết driver, chạy ứng dụng trên JVM | Chỉ cần ứng dụng đang chạy ở một URL |
| Mục tiêu tìm kiếm | Phủ dòng, nhánh, mã trạng thái… | Mã trạng thái trên từng thao tác |

Khóa luận dùng hộp đen. Bốn ứng dụng viết bằng Java (reports-api), Python (vampi-seeded, pyLoad) và Rust
(artifact-keeper); hộp đen chỉ cần ứng dụng đang chạy nên dùng chung được cho cả bốn. Lệnh chạy thật cho reports-api:

```
java -jar evomaster-TR2-3beccb00.jar --blackBox true \
  --bbSwaggerUrl http://localhost:8080/v3/api-docs --bbTargetUrl http://localhost:8080 \
  --configPath infra/em-config/reports-auth.yaml --maxTime 150s --seed 1 ...
```

`--bbSwaggerUrl` là chỗ lấy đặc tả, `--bbTargetUrl` là chỗ gửi yêu cầu. EvoMaster không biết gì thêm về ứng dụng.

*Tham khảo:* Arcuri và cộng sự, *Tool report: EvoMaster*, Automated Software Engineering 2025, https://doi.org/10.1007/s10515-024-00478-1

### Thuật toán SMARTS: lấy mẫu thay vì biến đổi

Thuật toán tìm kiếm có hai cách tạo ca mới:
- **biến đổi (mutation):** lấy một ca đã có rồi sửa một chút (đổi một tham số, thêm một lời gọi);
- **lấy mẫu (sampling):** dựng hẳn một ca mới từ đầu.

Ở chế độ hộp trắng, EvoMaster mặc định dùng MIO, thuật toán vừa lấy mẫu vừa biến đổi. Ở chế độ hộp đen, mặc định là
SMARTS (Smart Sampling): mỗi vòng lặp chỉ lấy mẫu một ca mới, không biến đổi ca cũ (`defaultAlgorithmForBlackBox =
Algorithm.SMARTS` trong `EMConfig.kt`).

"Smart" là ở cách lấy mẫu. Với xác suất 0,95 (`probOfSmartSampling = 0.95` trong `EMConfig.kt` của v6.1.1), ca mới dựng
theo một chiến lược có cấu trúc, dựa trên quan hệ giữa các thao tác trong đặc tả. Với xác suất 0,05 còn lại, ca là chuỗi
lời gọi ngẫu nhiên.

Ví dụ chiến lược có cấu trúc trên reports-api: muốn thử `DELETE /reports/{id}` thì `id` ngẫu nhiên gần như chắc chắn
không tồn tại và nhận 404. Nên SMARTS dựng:

```
POST   /reports        {"title": "...", ...}   -> 201, báo cáo mới có id 12
DELETE /reports/12                              -> 204   (xóa đúng tài nguyên vừa tạo)
```

Khóa luận không đổi thuật toán: mọi lượt chạy đều dùng SMARTS mặc định.

*Tham khảo:* mã nguồn EvoMaster v6.1.1, `core/src/main/kotlin/org/evomaster/core/EMConfig.kt`, https://github.com/WebFuzzing/EvoMaster/tree/v6.1.1

### Ca kiểm thử, lời gọi, thao tác

Ba từ này lồng nhau:
- **thao tác (operation):** một cặp phương thức và đường dẫn trong đặc tả, ví dụ `PUT /reports/{id}`. reports-api có các
  thao tác `GET /reports`, `GET /reports/{id}`, `POST /reports`, `PUT /reports/{id}`, `DELETE /reports/{id}`,
  `PUT /users/{username}/role`, `GET /users/me`, cùng `POST /auth/login` và `POST /reset`;
- **lời gọi (call):** một lần gửi thao tác đó với giá trị cụ thể, ví dụ `PUT /reports/4` bằng token của `alice`;
- **ca kiểm thử (test case):** một chuỗi lời gọi chạy theo thứ tự.

Ví dụ: ca 970 của seed 2 là một ca gồm ba lời gọi, trên hai thao tác (`PUT /reports/{id}` xuất hiện hai lần):

```
# 1 - (200) PUT:/reports/{id}
# 2 - (200) PUT:/users/{username}/role
# 3 - (200) PUT:/reports/{id}
```

### Tài khoản trong ca kiểm thử và tệp cấu hình xác thực

Mỗi lời gọi có thể gửi bằng một tài khoản, hoặc không kèm tài khoản (ẩn danh). Danh sách tài khoản và cách đăng nhập nằm
trong tệp cấu hình xác thực. Phần chính của `infra/em-config/reports-auth.yaml`:

```yaml
auth:
  - name: alice       # mỗi tài khoản: tên và mật khẩu
    ...
authTemplate:         # cách đăng nhập, dùng chung cho mọi tài khoản
  loginEndpointAuth:
    endpoint: /auth/login
    verb: POST
    token:
      extractSelector: /token          # lấy token ở trường "token" của phản hồi
      sendIn: header
      sendName: Authorization
      sendTemplate: "Bearer {token}"   # gửi kèm dạng "Authorization: Bearer eyJ..."
```

Ở đầu mỗi ca, EvoMaster đăng nhập mỗi tài khoản mà ca dùng đúng một lần, rồi gắn token nhận được vào mọi lời gọi của tài
khoản đó trong ca. Hệ quả quan trọng cho khóa luận: trong một ca, `alice` chỉ có một token. Lời gọi thứ 3 của ca seed 2
dùng đúng token đã cấp trước khi `alice` bị hạ quyền ở lời gọi 2. Follow-up "dùng token cũ" có được là nhờ cơ chế này.

pyLoad khác ba ứng dụng kia ở chỗ đăng nhập trả về cookie phiên (`expectCookies: true` trong `pyload-auth.yaml`) thay vì
token trong thân phản hồi. EvoMaster xử lý hai kiểu giống nhau: đăng nhập một lần, gửi kèm mọi lời gọi.

*Tham khảo:* EvoMaster docs, Authentication, https://github.com/WebFuzzing/EvoMaster/blob/master/docs/auth.md

### Ca khởi tạo

Trước khi lấy mẫu kiểu SMARTS, EvoMaster chạy một loạt ca khởi tạo. Mỗi ca khởi tạo chỉ có một lời gọi. Mỗi thao tác có
một ca cho từng tài khoản, cộng một ca ẩn danh.

Ví dụ (minh họa) trên reports-api có 3 tài khoản, với thao tác `PUT /reports/{id}` có 4 ca khởi tạo:

```
PUT /reports/{id}   bằng bob          -> 403
PUT /reports/{id}   bằng superadmin   -> 200 hoặc 404 tùy id
PUT /reports/{id}   bằng alice        -> 200 hoặc 404 tùy id
PUT /reports/{id}   ẩn danh           -> 401
```

Nhờ các ca này, ngay từ đầu kho lưu trữ đã biết mỗi tài khoản nhận mã gì trên mỗi thao tác. Tài khoản cuối trong tệp
cấu hình chạy trước, nên ngân sách quá nhỏ có thể không chạy tới tài khoản đầu (`RestSampler.kt:322–346`).

### Mục tiêu (target) và mục tiêu theo tài khoản

Sau mỗi ca, EvoMaster ghi lại các mục tiêu mà ca đạt được. Ở chế độ hộp đen, mục tiêu điển hình là "thao tác X nhận mã Y",
hoặc "oracle phát hiện một lỗi". Ca nào đạt được mục tiêu mới thì có ích và được giữ.

Khi bật pha kiểm thử bảo mật, EvoMaster thêm mục tiêu theo tài khoản: "tài khoản A gọi thao tác X và nhận `2xx`", "… nhận
401", "… nhận 403". Ví dụ:

| Mục tiêu thường | Mục tiêu theo tài khoản |
|---|---|
| `PUT /reports/{id}` nhận 200 | `alice` gọi `PUT /reports/{id}` nhận `2xx` |
| | `superadmin` gọi `PUT /reports/{id}` nhận `2xx` |
| `PUT /reports/{id}` nhận 403 | `bob` gọi `PUT /reports/{id}` nhận 403 |

Không có mục tiêu theo tài khoản thì chỉ cần một ca 200 (của bất kỳ ai) là mục tiêu "nhận 200" đã đạt, và ca của `alice`
có thể bị bỏ. Có cột bên phải thì kho giữ riêng một ca cho `alice`, một ca cho `superadmin`.

### Kho lưu trữ ca kiểm thử (archive)

Kho lưu trữ giữ, với mỗi mục tiêu, một ca đã đạt mục tiêu đó. Hai ca cùng đạt một mục tiêu thì giữ ca ngắn hơn.

Ví dụ: ca A gồm 5 lời gọi và ca B gồm 2 lời gọi đều có `alice` gọi `PUT /reports/{id}` nhận 200. Kho giữ B.

Kho quan trọng với khóa luận vì mọi thứ sau pha tìm kiếm (pha rút gọn, pha bảo mật, bộ ca cuối) chỉ lấy ca từ kho. Bộ dựng
MR-A1 tìm source trong kho: một ca có `alice` gọi một thao tác ghi và nhận `2xx`. Nếu kho không có ca đó, không dựng
được bộ ba. Đây là lý do các lượt bỏ sót ở chương 5 đều là lượt thiếu bộ ba.

*Tham khảo:* Arcuri, *Many Independent Objective (MIO) Algorithm for Test Suite Generation*, SSBSE 2017, https://doi.org/10.1007/978-3-319-66299-2_1

### Pha rút gọn (minimization)

Khi hết thời gian tìm kiếm, pha rút gọn chạy lại các ca trong kho và bỏ những lời gọi không cần cho mục tiêu mà ca đã đạt.

Ví dụ (minh họa):

```
trước:  GET /reports  ->  GET /users/me  ->  PUT /reports/4 (alice, 200)
sau:    PUT /reports/4 (alice, 200)
```

Hai lời gọi `GET` đầu không ảnh hưởng tới việc `PUT` nhận 200, nên bị bỏ.

Pha bảo mật đòi pha rút gọn bật trước (`--security` cần `--minimize`), nên khóa luận không tắt được pha rút gọn để tiết
kiệm thời gian.

### Quỹ thời gian của các pha sau tìm kiếm

Mỗi pha sau tìm kiếm (rút gọn, bảo mật) có quỹ thời gian riêng và dừng khi hết quỹ. Mặc định quỹ bằng 10% thời gian tìm
kiếm (`extraPhaseBudgetPercentage = 0.10`), có thể cấu hình.

Ví dụ thật: reports-api chạy `--maxTime 150s` và `--extraPhaseBudgetPercentage 0.6`, nên mỗi pha sau tìm kiếm có tối đa
0,6 × 150 = 90 giây. Với mặc định 10%, pha bảo mật chỉ có 15 giây; skill `em-batch` ghi rằng dưới khoảng 0,6 ở 150 giây
thì bộ dựng MR-A1 thiếu thời gian.

### Tệp kết quả

Hết các pha, EvoMaster ghi bộ ca kiểm thử ra file. Ở chế độ hộp đen, mặc định là mã Python, chia ba tệp:

| Tệp | Chứa |
|---|---|
| `EvoMaster_faults_Test.py` | ca phát hiện lỗi (có oracle báo), gồm ca 970 |
| `EvoMaster_successes_Test.py` | ca mà mọi lời gọi đều thành công |
| `EvoMaster_others_Test.py` | các ca còn lại |

Kèm theo là `report.json`, nơi ghi danh sách lỗi và mã lỗi. Ví dụ ở `infra/em-results/tr2-wave1-20261121/tests/<run>/`.

### Pha kiểm thử bảo mật và bốn bước của nó

Pha này chạy sau pha rút gọn. Nó lấy ca có sẵn trong kho, dựng thêm ca nhắm vào lỗi bảo mật, chạy chúng, rồi lưu ca nào
đạt mục tiêu mới vào kho. Thứ tự bốn bước lấy từ hàm `applySecurityPhase` trong `RestSecurityBuilder.kt` (v6.1.1):

**Bước 1, sinh phản hồi 403** (`expandWithForbidden`). Pha tìm kiếm hiếm khi trộn nhiều tài khoản trong một ca, nên ít
gặp 403. Với thao tác đã nhận `2xx` và 401 nhưng chưa nhận 403 lần nào, EvoMaster lấy lời gọi từng nhận `2xx` rồi gửi
lại bằng tài khoản khác. Điều kiện "đã nhận 401" cho biết thao tác có kiểm xác thực, đáng thử.

```
có sẵn:   POST /reports  (alice)  -> 201 tạo báo cáo 12
          DELETE /reports/12 (alice) -> 204
dựng:     POST /reports  (alice)  -> 201 tạo báo cáo 12
          DELETE /reports/12 (bob)   -> 403    mục tiêu mới: "bob nhận 403 trên DELETE"
```

**Bước 2, kiểm tra quyền giữa các tài khoản.** Từ một ca kết thúc bằng 403 (có sẵn trong kho hoặc vừa dựng), tìm mâu
thuẫn. Ví dụ: `bob` nhận 403 khi xóa báo
cáo do `alice` tạo, nhưng `PUT` hoặc `PATCH` chính báo cáo đó lại được 200. Một chính sách hợp lý không cấm xóa mà cho
sửa. Bước này cũng tìm lời gọi đã đăng nhập mà vẫn nhận 401 (máy chủ không nhận ra token hợp lệ), và lời gọi ẩn danh mà
vẫn được chấp nhận (quên kiểm xác thực).

**Bước 3, kiểm tra injection.** Gửi giá trị độc vào tham số: SQL injection (chuỗi như `' OR '1'='1`), XSS (chuỗi
`<script>` được trả lại nguyên văn), SSRF (tham số URL khiến máy chủ gọi tới một địa chỉ do EvoMaster dựng).

**Bước 4, kiểm tra lộ thông tin.** Phản hồi chứa stack trace (lộ cấu trúc mã nguồn); hoặc trả 404 thay cho 403, khiến kẻ
tấn công phân biệt được "tài nguyên không tồn tại" với "tài nguyên có nhưng bạn không được xem".

Ca do pha này dựng được đánh dấu là ca kiểm thử bảo mật. Sau mỗi ca, EvoMaster gọi oracle bảo mật để xét mã trạng thái và
nội dung phản hồi.

Oracle 970 của khóa luận cũng chạy trong pha này. Giống bước 1, bộ dựng MR-A1 lấy một ca từ kho, cắt bỏ các lời gọi sau
source, rồi nối thêm transition và follow-up.

*Tham khảo:* Şahin, Zhang, Arcuri, arXiv:2604.00702, https://arxiv.org/abs/2604.00702v1; mã nguồn
`core/src/main/kotlin/org/evomaster/core/problem/rest/service/RestSecurityBuilder.kt` tại v6.1.1

### Mã lỗi và nhóm oracle thử nghiệm

Mỗi loại lỗi mang một mã số, ghi vào `report.json` và vào chú thích của ca kiểm thử. Mã của pha bảo mật trong v6.1.1 (thư
viện `com.webfuzzing:commons` 0.6.0):

| Mã | Tên | Bước |
|---|---|---|
| 200 | `SQL_INJECTION` | 3 |
| 201 | `XSS` | 3 |
| 202 | `SSRF` | 3 |
| 204 | `SECURITY_EXISTENCE_LEAKAGE` (404 thay cho 403) | 4 |
| 205 | `SECURITY_NOT_RECOGNIZED_AUTHENTICATED` (đã đăng nhập vẫn 401) | 2 |
| 206 | `SECURITY_WRONG_AUTHORIZATION` (cấm xóa nhưng cho sửa) | 2 |
| 207 | `SECURITY_IGNORE_ANONYMOUS` (ẩn danh vẫn được chấp nhận) | 2 |
| 208 | `SECURITY_ANONYMOUS_MODIFICATIONS` (ẩn danh sửa được dữ liệu) | 2 |
| 209 | `SECURITY_LEAKED_STACK_TRACES` | 4 |

Bản EvoMaster mới hơn dùng thư viện commons mới hơn và đánh số lại (ví dụ bài arXiv viết F900/F901). Khi trích một mã,
phải nói rõ mã của phiên bản nào.

Ngoài nhóm trên còn nhóm thử nghiệm (`ExperimentalFaultCategory.kt`, mã 911–980), là các oracle chưa được kiểm chứng đủ.
Nhóm này chỉ chạy khi bật `--useExperimentalOracles true`, mặc định tắt. Khóa luận đặt 970 vào nhóm thử nghiệm, nên mọi
lượt chạy đều phải bật cờ này. Không bật thì 970 không bao giờ báo.

---

## 2. Kiểm thử biến hình (mục 2.2)

### Oracle kiểm thử (test oracle)

Oracle là cơ chế quyết định một lần chạy là đúng hay có lỗi, bằng cách so kết quả với hành vi kỳ vọng hoặc một tiêu chí
cho trước.

```
add(2, 3) -> 5          oracle: "phải bằng 5"                  so với giá trị kỳ vọng
GET /reports -> 500     oracle của EvoMaster: "không được 500"  so với tiêu chí chung
```

*Tham khảo:* Barr và cộng sự, *The Oracle Problem in Software Testing: A Survey*, IEEE TSE 2015, https://doi.org/10.1109/TSE.2014.2372785

### Bài toán thiếu oracle (test oracle problem)

Khi không biết kết quả đúng, hoặc muốn biết thì quá tốn công, ta không phán được một lần chạy là đúng hay sai. Đó là bài
toán thiếu oracle.

| Chương trình | Đầu ra | Vì sao không phán được |
|---|---|---|
| `sin(1.234)` | `0.9438182...` | Muốn biết đúng tới chữ số cuối phải có một bản cài đặt khác đáng tin |
| Công cụ tìm kiếm, gõ "REST API" | 1.253 kết quả | Không ai biết con số đúng |
| `PUT /reports/4` bằng token cũ của `alice` | 200 | Đặc tả không ghi thao tác này phải trả mã gì với từng tài khoản ở từng trạng thái quyền |

Hàng cuối là vấn đề của khóa luận. EvoMaster sinh hàng nghìn lời gọi tự động. Muốn có oracle kiểu "giá trị kỳ vọng" thì
phải viết tay mã đúng cho mọi tổ hợp thao tác × tài khoản × trạng thái quyền. Chương 3 mở đầu bằng đúng ý này: máy chủ có
thể trả 200 cho một thao tác mà chính sách cấm, và nhìn riêng mã 200 thì không biết.

### Kiểm thử biến hình (metamorphic testing)

Kiểm thử biến hình giải bài toán trên bằng cách đổi câu hỏi. Không hỏi "đầu ra này có đúng không?" (không trả lời được),
mà hỏi "đầu ra của hai lần chạy có liên quan có giữ đúng quan hệ không?" (trả lời được).

Hai lần chạy có tên riêng:
- **source test case:** lần chạy gốc;
- **follow-up test case:** lần chạy suy ra từ lần gốc bằng một phép biến đổi đầu vào.

Hai chữ source và follow-up trong bộ ba của khóa luận lấy từ đây. Khóa luận chỉ thêm transition (bước hạ quyền) vào giữa.

*Tham khảo:* Chen, Cheung, Yiu, *Metamorphic Testing: A New Approach for Generating Next Test Cases*, HKUST-CS98-01, 1998

### Quan hệ biến hình (metamorphic relation)

Quan hệ biến hình phát biểu: đầu vào của hai lần chạy liên quan với nhau thế nào thì đầu ra phải liên quan với nhau thế
nào.

Ví dụ kinh điển với `sin`, dựa trên đẳng thức `sin(x) = sin(π − x)`:

```
source:     sin(1.234)       -> 0.9438182
follow-up:  sin(π − 1.234)   -> 0.9438182    quan hệ giữ
            nếu ra 0.51                       quan hệ vi phạm: chắc chắn có lỗi
```

Vẫn không biết `0.9438182` có đúng không, nhưng hai kết quả buộc phải bằng nhau.

Ví dụ với công cụ tìm kiếm: kết quả của "REST AND API" phải là tập con của kết quả "REST". Truy vấn hẹp hơn mà ra nhiều
kết quả hơn thì có lỗi.

Áp vào khóa luận, MR-A1:

```
source:      PUT /reports/4   token cũ của alice (ADMIN)    -> 200   được phép
transition:  PUT /users/alice/role {"role":"VIEWER"}        -> 200   gỡ quyền
follow-up:   PUT /reports/4   vẫn token cũ đó               -> phải là 403
```

Không biết `PUT /reports/4` lẽ ra phải trả gì, nhưng biết: thao tác được phép nhờ quyền ADMIN, quyền đó vừa bị gỡ, nên
lần sau phải bị từ chối. Follow-up nhận 200 là vi phạm.

### Điều kiện áp dụng và ý nghĩa của một vi phạm

Một quan hệ chỉ đúng trong điều kiện nhất định. `GET /reports` thì `VIEWER` cũng được đọc, nên sau khi hạ quyền mà vẫn 200
là đúng. Nếu áp MR-A1 lên `GET /reports` thì sẽ báo lỗi sai. Vì vậy chương 2 viết: chỉ khi các quan sát **thỏa điều kiện
áp dụng** mà vẫn vi phạm quan hệ thì đó mới là bằng chứng có lỗi. Với MR-A1, điều kiện là source phải là thao tác ghi cần
đúng quyền bị gỡ, và cả source lẫn transition phải thành công. Không đủ điều kiện thì bộ ba bị hủy (VOID, chương 3).

Điểm hội đồng có thể hỏi, về hai chiều của kết luận:
- quan hệ bị vi phạm (khi điều kiện thỏa) là bằng chứng có lỗi;
- quan hệ được giữ không chứng minh chương trình đúng. `sin` có thể sai giống nhau ở cả hai lần. Với MR-A1, follow-up
  403 chỉ nói thao tác đó, ở lần đó, đã bị chặn.

*Tham khảo:* Chen và cộng sự, *Metamorphic Testing: A Review of Challenges and Opportunities*, ACM Computing Surveys 2018, https://doi.org/10.1145/3143561

---

## 3. Lỗ hổng kiểm soát truy cập trong REST API (mục 2.3)

### Kiểm soát truy cập (access control)

Kiểm soát truy cập trả lời: chủ thể nào được làm thao tác nào trên tài nguyên nào. Ba thành phần:

| Thành phần | Nghĩa | Ví dụ reports-api |
|---|---|---|
| Chủ thể (subject) | ai gửi yêu cầu | `alice`, `bob` |
| Thao tác | làm gì | sửa (`PUT`), xóa (`DELETE`) |
| Tài nguyên (đối tượng) | trên cái gì | báo cáo số 4 |

Một quyết định phân quyền là một bộ ba như "`bob` sửa báo cáo 4: cấm".

*Tham khảo:* OWASP Authorization Cheat Sheet, https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html

### BOLA và BFLA, vì sao lớp lỗi của khóa luận gần API5

Nhắc lại (`chuong-1.md` mục 2): BOLA là thiếu kiểm quyền trên một **đối tượng** cụ thể (đổi id là xem được dữ liệu người
khác); BFLA là thiếu kiểm quyền gọi một **chức năng** (người thường gọi được chức năng quản trị).

Hai lỗi khác nhau ở chỗ máy chủ quên kiểm cái gì:

```
BOLA (giả định):  bob  GET /reports/4         -> 200   bob được đọc báo cáo, nhưng không phải báo cáo này
BFLA (giả định):  bob  PUT /users/alice/role  -> 200   bob không được gọi chức năng đổi vai trò
```

Lỗi của khóa luận gần BFLA (API5) hơn. Sau khi bị hạ, `alice` đã là `VIEWER` mà vẫn gọi được `PUT /reports/4`, chức năng
sửa vốn chỉ ADMIN có, và báo cáo nào cũng bị như vậy, nên lỗi nằm ở mức chức năng.

*Tham khảo:* API5 BFLA, https://owasp.org/API-Security/editions/2023/en/0xa5-broken-function-level-authorization/

### Thông tin xác thực: token JWT và phiên phía máy chủ

Sau khi đăng nhập, client nhận một thông tin xác thực để gửi kèm các yêu cầu sau. Hai kiểu, khác nhau ở chỗ dữ liệu nằm
đâu:

| | Token JWT | Phiên phía máy chủ |
|---|---|---|
| Client giữ | cả token, trong đó có claim (tên, vai trò, hạn) | chỉ một mã phiên trong cookie |
| Dữ liệu tài khoản nằm | trong token, có chữ ký | trên máy chủ, trong bảng phiên |
| Mỗi yêu cầu, máy chủ làm | kiểm chữ ký, đọc claim, không cần tra cơ sở dữ liệu | dùng mã phiên tra bảng phiên |
| Ứng dụng trong khóa luận | reports-api, vampi-seeded, artifact-keeper | pyLoad |

Ví dụ payload JWT mà reports-api cấp cho `alice` (`JwtService.java:32` ghi claim `role`):

```json
{ "sub": "alice", "role": "ADMIN", "exp": <1 giờ sau lúc đăng nhập> }
```

Ưu điểm của JWT là nhanh, không tra cơ sở dữ liệu. Nhược điểm là claim đóng băng từ lúc đăng nhập.

*Tham khảo:* RFC 7519, https://www.rfc-editor.org/rfc/rfc7519; OWASP Session Management Cheat Sheet, https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html

### Quyết định quyền theo vai trò lúc đăng nhập: gốc của lỗi

Nếu máy chủ lấy vai trò từ claim của token (hoặc từ dữ liệu phiên ghi lúc đăng nhập), thì đổi vai trò trong cơ sở dữ liệu
không ảnh hưởng tới token đã cấp. Token cũ vẫn nói `ADMIN` cho tới khi hết hạn.

Mã thật của reports-api, `AuthFilter.java:80–95`, cho thấy hai biến thể chỉ khác một nhánh `if`:

```java
if (statefulRoleCheck) {                                   // biến thể đã vá
    Optional<User> user = userStore.findByUsername(username);
    effectiveRole = user.get().role();                     //   tra vai trò HIỆN TẠI
} else {                                                   // biến thể có lỗ hổng
    effectiveRole = Role.valueOf(claims.get("role", String.class));  // tin vai trò trong token
}
```

Sau khi `alice` bị hạ, cơ sở dữ liệu ghi `VIEWER`. Biến thể đã vá đọc `VIEWER` và trả 403. Biến thể có lỗ hổng đọc
`ADMIN` từ token và trả 200.

### Hai hướng khắc phục

Chương 2 nêu hai cách sửa:

1. **Tra lại vai trò hiện tại ở mỗi yêu cầu.** Chính là nhánh `statefulRoleCheck` ở trên. Token vẫn hợp lệ, nhưng quyền
   lấy từ cơ sở dữ liệu. Hệ quả: token cũ nhận **403**. Biến thể đã vá của pyLoad do khóa luận viết theo hướng này: nó
   áp cho nhánh phiên đúng phép tra cơ sở dữ liệu mà nhánh `X-API-Key` của pyLoad vốn đã làm.
2. **Thu hồi thông tin xác thực cấp trước lần đổi vai trò.** Hệ quả: token cũ nhận **401** (máy chủ không còn nhận nó).
   Bản vá của artifact-keeper (`e64cc5c608`, #1821) thêm cột `privileges_changed_at`; token cấp trước thời điểm đó bị
   từ chối. Bản vá upstream của pyLoad (dev98) cũng theo hướng này: xóa mọi phiên của người bị đổi quyền.

Điểm hội đồng có thể hỏi: vì sao không dùng bản vá upstream của pyLoad làm biến thể đã vá? Vì nó trả 401, mà oracle 970
cần 403 để phán "bị từ chối". Khóa luận khai lệch này trong `docs/tier2b-pyload-target.md` §3.

Khác biệt 403 với 401 ảnh hưởng trực tiếp tới kết quả. Oracle 970 coi 403 là bị từ chối và 401 là không kết luận được,
nên trên bản vá của artifact-keeper, mọi bộ ba đều bị hủy và không có lượt TN nào (chương 5).

### Lỗ hổng phân quyền có trạng thái và chính sách thu hồi có hiệu lực ngay

Các oracle BOLA/BFLA so hai tài khoản khác nhau ở cùng một lúc. Khóa luận so cùng một tài khoản ở hai lúc: trước và sau
khi quyền bị thu hồi. Đó là lý do có chữ "có trạng thái": kết quả đúng hay sai phụ thuộc vào việc thu hồi đã
xảy ra hay chưa.

Lỗi chỉ là lỗi khi hệ thống có chính sách thu hồi có hiệu lực ngay: sau khi thu hồi, mọi yêu cầu dựa vào quyền vừa gỡ phải
bị từ chối. Một hệ thống tuyên bố "quyền mới có hiệu lực khi đăng nhập lại" thì token cũ được 200 là đúng thiết kế.

Ví dụ hai chính sách trên cùng một chuỗi lời gọi:

```
alice PUT /reports/4 (token c) -> 200 ; superadmin hạ alice ; alice PUT /reports/4 (token c) -> 200
  chính sách "có hiệu lực ngay":         vi phạm
  chính sách "hiệu lực khi đăng nhập lại": đúng thiết kế
```

Khóa luận lấy chính sách từ chính ứng dụng: biến thể đã vá (reports-api, vampi-seeded), bản vá CVE (pyLoad), bản vá của
nhà phát triển (artifact-keeper). Bản vá tồn tại chứng tỏ nhà phát triển muốn thu hồi ngay.

### Chuẩn RBAC INCITS 359 và lệnh DeassignUser

INCITS 359 là chuẩn Mỹ về kiểm soát truy cập theo vai trò, dựa trên mô hình RBAC của NIST. Khóa luận trích bản dự thảo
năm 2003, bản công khai miễn phí trên trang NIST (bản chính thức 2004 phải trả phí). Chuẩn định nghĩa các lệnh quản trị, trong đó có:
- `DeassignUser(user, role)`: hủy gán người dùng khỏi một vai trò (đúng thao tác transition của khóa luận);
- thu hồi quyền khỏi vai trò (`RevokePermission`).

Mục 6.1.1 của bản dự thảo nói về phiên đang mở khi người dùng bị hủy gán vai trò: *"The RBAC system could wait for such a
session to terminate normally, could force its termination, or could inactivate the role"*. Tức là chuẩn để bên cài đặt
chọn: chờ phiên tự kết thúc, buộc kết thúc phiên, hoặc vô hiệu vai trò trong phiên.

Vì vậy khóa luận không nói "chuẩn RBAC bắt buộc thu hồi ngay". Câu trả lời cho hội đồng: chuẩn cho phép chờ, nên lỗi chỉ
là lỗi so với chính sách của ứng dụng, và bằng chứng về chính sách là bản vá. Khi chính sách đòi kết thúc hoặc cập nhật
phiên mà hệ thống không làm, lỗi có thể xếp vào CWE-1464 (`chuong-1.md` mục 2).

*Tham khảo:* NIST, *Role Based Access Control (Draft)*, BSR INCITS 359, 2003, https://csrc.nist.gov/CSRC/media/Projects/Role-Based-Access-Control/documents/rbac-std-ncits.pdf

---

## 4. Các công trình nghiên cứu liên quan (mục 2.4)

### Oracle bảo mật của Şahin, Zhang và Arcuri (baseline)

Nhóm tác giả EvoMaster thêm các oracle bảo mật dưới dạng pha hậu xử lý, chạy sau pha tìm kiếm. Đó chính là pha kiểm thử
bảo mật ở mục 1. Có hai bài: bản hội nghị ISSRE 2025 (đã qua phản biện) và bản arXiv 2026 mở rộng (mô tả chi tiết 9
oracle). Các oracle phân quyền so nhiều tài khoản ở cùng một thời điểm, ví dụ mã 206 ở bảng trên.

Khóa luận dùng nhóm oracle này làm baseline (mục 5.6). 20 lượt baseline trên biến thể có lỗ hổng của vampi-seeded không
dựng được bộ ba nào dùng lại token cũ. Bản upstream chạy thêm 20 seed trên reports-api có lỗ hổng không báo lỗi nào thuộc
lớp MR-A1.

*Tham khảo:* Arcuri, Şahin, Zhang, ISSRE 2025, https://doi.org/10.1109/ISSRE66568.2025.00025; Şahin, Zhang, Arcuri, arXiv:2604.00702

### RESTler

RESTler (Microsoft) là công cụ kiểm thử REST API có trạng thái: nó đọc đặc tả, suy ra thao tác nào tạo tài nguyên mà thao
tác khác cần (ví dụ `POST /reports` tạo `id` mà `DELETE /reports/{id}` cần), rồi dựng chuỗi lời gọi theo thứ tự đó. Sau
mỗi chuỗi, các bộ kiểm tra (checker) tìm lỗi. Theo tài liệu của RESTler (mới đọc qua bản tóm tắt, chưa đối chiếu nguyên
văn), có checker tìm tài nguyên đã xóa mà vẫn truy cập được và checker tìm người dùng khác truy cập được tài nguyên. Không
checker nào xét quyền sau khi bị hạ.

*Tham khảo:* Atlidakis, Godefroid, Polishchuk, *RESTler: Stateful REST API Fuzzing*, ICSE 2019, https://doi.org/10.1109/ICSE.2019.00083

### BACScan

BACScan (CCS 2025) quét lỗ hổng kiểm soát truy cập trong ứng dụng web ở chế độ hộp đen. Với lỗi đọc trái phép, phản hồi
của chính yêu cầu đã cho biết kẻ tấn công có đọc được dữ liệu hay không. Với lỗi sửa trái phép, phản hồi không cho biết
dữ liệu có bị đổi hay không. BACScan gửi lại yêu cầu sửa bằng phiên của kẻ tấn công, rồi mở các trang hiển thị dữ liệu đó
để xem dữ liệu đã bị sửa chưa. Bài báo gọi lỗi đọc là RBAC (read-based) và lỗi sửa là MBAC (modification-based). Chữ RBAC
trong bài này khác RBAC theo vai trò mà khóa luận dùng ở mục 2.3. Các phiên của kẻ tấn công và nạn nhân cố định từ đầu,
không có bước đổi quyền, nên đây là kiểu so chéo tài khoản.

*Tham khảo:* Liu và cộng sự, CCS 2025, https://doi.org/10.1145/3719027.3744825

### GraphQLer, IDOR và chuỗi tạo–xóa–đọc

GraphQLer kiểm thử API GraphQL bằng chuỗi lời gọi nhiều bước. Hai kiểu chuỗi đáng nhớ:

- **IDOR (Insecure Direct Object Reference):** phát lại yêu cầu của người dùng A bằng thông tin xác thực của người dùng B.
  B đọc được dữ liệu của A thì có lỗi. IDOR gần như cùng nghĩa với BOLA, là tên cũ hơn.
- **Chuỗi tạo, xóa, đọc:** tạo tài nguyên, xóa nó, rồi đọc lại. Vẫn đọc được thì có lỗi dùng tài nguyên sau khi xóa.

Chuỗi tạo–xóa–đọc giống khóa luận ở chỗ có yếu tố thời gian: trước và sau một sự kiện. Khác ở chỗ cái thay đổi là gì:

| | Sự kiện ở giữa | Cái thay đổi |
|---|---|---|
| GraphQLer tạo–xóa–đọc | xóa tài nguyên | tài nguyên |
| MR-A1 | hạ quyền tài khoản | quyền của chủ thể |

*Tham khảo:* GraphQLer, arXiv:2504.13358v2, https://arxiv.org/abs/2504.13358v2

### Khoảng trống khóa luận nhắm tới

Chương 2 kết bằng ba cơ chế mà chưa oracle nào trong EvoMaster upstream có đủ:

| Cơ chế | Oracle BOLA/BFLA của EvoMaster | Oracle 970 |
|---|---|---|
| Tự dựng thao tác thu hồi quyền | không | có (Naive Bayes chọn từ đặc tả) |
| Dùng lại token cấp trước khi thu hồi | không (mỗi tài khoản một token, không có sự kiện đổi quyền) | có (follow-up dùng token của source) |
| Phán quyết bằng quan sát trước và sau | không (so các tài khoản cùng lúc) | có (so source với follow-up) |

Nhận định "upstream chưa có" dựa trên đọc mã nguồn, nên khóa luận kiểm thêm bằng thực nghiệm baseline ở mục 5.6.
