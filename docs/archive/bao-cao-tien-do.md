# Báo cáo tiến độ luận văn

**Đề tài:** Mở rộng EvoMaster bằng một oracle phát hiện lỗi phân quyền có trạng thái theo thời gian
**Cập nhật:** 09/08/2026 — phần hiện thực đã xong và đã đo xong; còn lại là viết luận văn.

---

## 1. Đề tài trong một câu

Thêm vào **EvoMaster** — công cụ fuzzing REST API mã nguồn mở dẫn đầu hiện nay — khả năng phát hiện
một lớp lỗi bảo mật mà **chưa công cụ fuzzing REST API nào tìm được**: *quyền vẫn còn hiệu lực sau khi
đã bị thu hồi*.

Một câu để hình dung sự khác biệt:

> Các công trình trước kiểm tra xem **người sai có đang giữ chìa khoá hay không**.
> Luận văn này kiểm tra xem **chìa khoá cũ có còn mở được cửa sau khi đã bị thu hay không**.

---

## 2. Lỗi cần bắt — ví dụ cụ thể

Kịch bản, đúng như nó xảy ra trong hệ thống thật:

1. alice là **ADMIN**. Cô ấy đăng nhập, nhận một token, và xoá được báo cáo. Bình thường.
2. Một admin khác **hạ quyền alice xuống VIEWER**. Về nguyên tắc, từ giây này alice không được xoá gì nữa.
3. alice dùng lại **đúng token cũ** đó — và **vẫn xoá được**.

Nguyên nhân gốc rất phổ biến: hệ thống tin vào role đã được ghi sẵn **bên trong JWT** lúc đăng nhập,
chứ không đọc lại quyền hiện tại của người dùng. Nên token cũ mang theo quyền ADMIN đã lỗi thời, và
nó vẫn còn hiệu lực cho tới khi hết hạn.

Đây không phải lỗi hiếm hay lỗi hàn lâm. Phân quyền là **lớp lỗ hổng API số 1 trong thực tế**
(OWASP API Security Top 10), và biến thể có trạng thái như trên là biến thể gây thiệt hại nặng nhất,
vì nó xảy ra đúng lúc tổ chức *tưởng* mình đã thu quyền xong.

---

## 3. Vì sao chưa ai làm được — khoảng trống nghiên cứu

Công trình đối chuẩn trực tiếp là **Şahin, Zhang & Arcuri (2026), arXiv:2604.00702** — chính nhóm tác
giả của EvoMaster. Họ vừa thêm 9 oracle bảo mật vào công cụ (mã lỗi F200–F210), trong đó có các oracle
về phân quyền.

Điểm mấu chốt: **cả 9 oracle đó đều so sánh giữa những người dùng khác nhau, tại một thời điểm đóng
băng.** Chúng gửi cùng một yêu cầu bằng hai tài khoản khác quyền rồi so kết quả. Không oracle nào mô
hình hoá một **phép chuyển đổi làm giảm quyền diễn ra theo thời gian**. Vì vậy chúng mù về mặt cấu trúc
với toàn bộ họ lỗi ở mục 2 — không phải vì cài đặt thiếu, mà vì mô hình của chúng không có trục thời gian.

Trục của họ và trục của luận văn này **vuông góc với nhau**, không cạnh tranh:

| | Trục so sánh | Câu hỏi |
|---|---|---|
| Şahin và cộng sự (đối chuẩn) | khác người, **cùng một thời điểm** | ai đang được phép? |
| **Luận văn này** | **cùng một người, khác thời điểm** | quyền đã thu có thật sự mất hiệu lực? |

Đã kiểm tra tài liệu trực tiếp (lần cuối 31/07/2026): **không công trình nào, học thuật hay thương mại,
chiếm đúng chỗ này.** Các láng giềng gần nhất đều lệch trên một trục nêu tên được:

- **BACScan** (CCS 2025) — đối thủ mạnh nhất về access control, nhưng nhắm web app truyền thống,
  vẫn là khác-người / một-thời-điểm, không có phép chuyển đổi quyền.
- **ARMeta** (2026) — gần nhất về *phương pháp* (cùng dùng metamorphic testing trên REST API), nhưng
  các quan hệ của nó thuần chức năng; phần nghiên cứu tình huống về RBAC **không định nghĩa quan hệ
  phân quyền nào**. Đúng con đường chưa ai đi.
- **BACFuzz** (2025) — fuzzer phân quyền cho ứng dụng PHP, không phải REST/OpenAPI; khác-người, một thời điểm.
- **AuthREST** (2025) — nhắm lỗi *xác thực* (authentication), không phải *phân quyền* (authorization).
- **Công cụ thương mại** (StackHawk, Invicti, Equixly...) — đều là ma trận so sánh chéo người dùng tại
  một thời điểm; không công cụ nào phát lại token cũ qua một lần hạ quyền.

---

## 4. Ý tưởng giải pháp — kiểm thử biến hình (metamorphic testing)

Vấn đề của mọi công cụ kiểm thử tự động là **oracle**: máy không biết câu trả lời đúng là gì. Với một
API lạ, không thể biết `DELETE /reports/9` *nên* trả về gì.

Kiểm thử biến hình lách qua chỗ đó: thay vì hỏi "kết quả này đúng không?", ta hỏi **"quan hệ giữa hai
kết quả có đúng không?"**. Không cần biết đáp án tuyệt đối, chỉ cần biết ràng buộc giữa chúng.

Quan hệ của luận văn — gọi là **MR-A1**:

> Một hành động **đòi hỏi đúng cái quyền vừa bị thu hồi**, một khi đã quan sát được là **ĐƯỢC PHÉP**,
> thì sau khi thu quyền phải trở thành **BỊ TỪ CHỐI** — với điều kiện dùng lại **cùng một credential**.

Cách thi hành, gọi là công thức **`cấp quyền → chuyển đổi → thử lại`**:

```
1. reset trạng thái                              (để biết chắc điểm khởi đầu)
2. alice đăng nhập          → giữ lấy token T
3. alice làm hành động A với T   → phải 2xx       (chứng minh A hoạt động khi còn quyền)
4. một admin khác hạ quyền alice → 2xx            (phép chuyển đổi làm giảm quyền)
5. alice làm lại A, VẪN dùng T   → quan sát       (KHÔNG đăng nhập lại)
6. kết luận:  bước 3 cho 2xx VÀ bước 5 cho 403  → ĐẠT
              bước 3 cho 2xx VÀ bước 5 cho 2xx  → LỖI
```

**Bước 5 là toàn bộ tinh thần của luận văn.** Nếu đăng nhập lại sau khi hạ quyền, ta nhận token VIEWER
mới và lỗi bị che đi hoàn toàn — mọi thứ trông như đúng. Chỉ khi phát lại token cũ thì lỗi mới hiện ra.
Đây chính xác là nước đi mà đối chuẩn không bao giờ thực hiện.

Hai chi tiết kỹ thuật quan trọng, không phải chi tiết vụn:

**Định nghĩa vận hành phải chặt.** ĐƯỢC PHÉP = HTTP 2xx. BỊ TỪ CHỐI = **403**. Không coi 404 là từ chối
(nhập nhằng: không rõ là bị chặn hay không tồn tại). **401 = không kết luận, không bao giờ là phán quyết** —
nếu token hết hạn giữa bộ ba thì phải huỷ bộ ba và làm lại, chứ để nó đọc thành "ĐẠT" là sai.

**Điều kiện canh quyền (guard) là bắt buộc.** Hành động A phải là hành động *thật sự cần* cái quyền vừa
bị thu. Nếu bỏ điều kiện này, quan hệ trở thành sai: `GET /reports` thì VIEWER cũng được đọc, nên nó
được phép cả trước lẫn sau khi hạ quyền — hoàn toàn bình thường, nhưng một quan hệ lỏng sẽ báo lỗi.
Đây không phải suy đoán lý thuyết; mục 7 dưới đây là bằng chứng thực nghiệm cho điều đó.

---

## 5. Đã hiện thực những gì

### 5.1 Mã nguồn — ngay bên trong EvoMaster

Toàn bộ đóng góp là **+362 dòng Kotlin, 3 file, thuần bổ sung** — không sửa một dòng nào của lõi thuật
toán tìm kiếm tiến hoá:

| Thành phần | Vai trò |
|---|---|
| `ExperimentalFaultCategory.kt` | thêm **một** mã lỗi mới: `970 SECURITY_STATEFUL_AUTHORIZATION` |
| `RestSecurityOracle.kt` | **bên phán đoán** — `handleStatefulAuthorization()`, tức bước 6 của công thức |
| `RestSecurityBuilder.kt` | **bên dựng ca kiểm thử** — tự động ghép bộ ba ở các bước 1–5 |

Bên dựng là phần khó và cũng là đóng góp chính. Nó phải tự suy ra kịch bản từ đặc tả OpenAPI, không
được hard-code: tìm endpoint chuyển đổi qua tín hiệu tên đường dẫn cộng tham số định danh người dùng
(ví dụ `PUT /users/{username}/role`), lấy một giá trị role thấp hơn từ từ vựng enum có trong schema,
chọn một phép ghi bị canh quyền và **không tiêu thụ tài nguyên** làm hành động nguồn (để lặp lại được
ở bước 5), rồi ghép tất cả thành một ca kiểm thử.

Oracle nằm ở **pha hậu xử lý sau khi fuzzing kết thúc** — đúng kiến trúc mà đối chuẩn đã dùng. Đây là
lý do lớn nhất khiến đề tài khả thi: **không cần hiểu hay can thiệp vào thuật toán tiến hoá của EvoMaster.**

### 5.2 Một phát hiện thuận lợi đáng kể

Trong lúc đọc mã nguồn EvoMaster, phát hiện một điều làm phần khó nhất trở thành miễn phí: **việc phát
lại token cũ là hành vi có sẵn của công cụ.** Mỗi ca kiểm thử, EvoMaster đăng nhập từng người dùng
**một lần duy nhất, trước** vòng lặp hành động, rồi tái sử dụng token đó cho mọi lời gọi.

Nghĩa là một ca `[alice ghi, admin hạ quyền alice, alice ghi lại]` sẽ tự động đăng nhập alice **một lần
khi cô ấy còn là ADMIN**, và áp token đó cho **cả hai** lần ghi. Bên dựng của luận văn không phải xử lý
gì về token — nó chỉ cần gán đúng người dùng cho từng hành động.

(Nhân đây cũng làm rõ một điểm dễ hiểu sai: nói "EvoMaster đăng nhập lại mỗi lần" là đúng ở phạm vi
*giữa các ca kiểm thử*, không phải *trong một ca*. Nên đó là lý do đối chuẩn không **dựng** được tình
huống, chứ không phải giới hạn của mô hình xác thực.)

### 5.3 Hai bia đo có đáp án biết trước

| | Là gì | Vai trò |
|---|---|---|
| **Tier-1** `reports-api` | Ứng dụng Spring Boot tự viết, cấy lỗi ở mục 2, **bật/tắt lỗi bằng một cờ cấu hình** | đáp án chuẩn hoàn toàn kiểm soát được |
| **Tier-2** `vampi-seeded` | Fork của VAmPI (ứng dụng lỗ hổng công khai), cấy thêm endpoint hạ quyền + lỗi tương ứng | kiểm tra khả năng tổng quát hoá |

Cùng một image, một biến môi trường quyết định có lỗi hay không → chạy hai cổng song song và **so sánh
vi phân**. Bản có lỗi phải bắn, bản đã sửa phải im. Cùng một oracle cho hai phán quyết trái ngược nhau
chỉ nhờ một cờ cấu hình — đó là cách chứng minh cả *dương tính thật* lẫn *âm tính thật* trong một phép đo.

**Một quyết định thiết kế có ý nghĩa:** ở Tier-2, các endpoint được đặt tên theo **ngữ pháp riêng của
VAmPI** (`PUT /users/v1/{username}/role`, `PUT /books/v1/{title}/secret`), **không sao chép** cách đặt
tên của app tự viết. Nhờ vậy, khi bên dựng suy luận thành công trên đó, đây là bằng chứng tổng quát hoá
thật — không phải chứng minh lại chính mình.

---

## 6. Kết quả thực nghiệm

Mỗi con số dưới đây là **20 lần chạy độc lập** (seed 1–20), cấu hình giữ nguyên hoàn toàn giữa hai công
cụ — khác biệt duy nhất là bật/tắt oracle của luận văn.

| | Tier-1 (`reports-api`) | Tier-2 (VAmPI-seeded) |
|---|---|---|
| **Phát hiện**, bản có lỗi | **16/20 = 80%** (CI 95%: 58–92%) | **4/20 = 20%** (CI 95%: 8–42%) |
| **Dương tính giả**, bản đã sửa | **0/20** (chặn trên 16%) | **0/20** (chặn trên 16%) |
| **Đối chuẩn Şahin**, cùng bản có lỗi | **0/20** | **0/20** |

Điểm đáng chú ý nhất: qua **cả 40 lần chạy Tier-1**, mã lỗi 970 bắn **khi và chỉ khi** lỗi có mặt.
Độ chính xác tuyệt đối trên cả hai bia đo.

### Sản phẩm đầu ra là một test chạy lại được

Công cụ không chỉ báo "có lỗi" — nó **xuất ra một ca kiểm thử thất bại, chạy lại được**, để lập trình
viên tự xác nhận. Ví dụ thật từ Tier-2 (seed 1):

```
1. PUT /books/v1/bookTitle3/secret   token superadmin  → 200   ← được phép khi còn quyền
2. PUT /users/v1/superadmin/role     token admin       → 200   ← hạ superadmin xuống "user"
3. PUT /books/v1/bookTitle3/secret   token superadmin  → 200   ← token CŨ, vẫn 200 = LỖI
```

Bước 3 dùng lại đúng biến token đã lấy ở bước 1, tức **trước** khi bị hạ quyền. Đáng lẽ phải 403.

**Mọi lần bắn đều được đọc tay để kiểm tra**, không tin vào con số thống kê. Cả 4 ca ở Tier-2 đều xác
nhận là bộ ba thật, đúng dạng `ghi(nạn nhân) → hạ quyền(người khác) → ghi lại cùng token(nạn nhân)`.
Đây là kỷ luật đã cứu phép đo một lần — xem mục 7.

### Chứng minh đối chuẩn mù về **cấu trúc**, không phải do cấu hình sai

Đây là phần đầu tư nhiều công nhất, vì **"đối chuẩn được 0" tự nó không chứng minh gì cả** — nó chạy với
oracle của luận văn tắt theo cấu hình, nên lập luận sẽ vòng vo. Nên đã dựng hai bằng chứng độc lập:

**Bằng chứng 1 — đối chuẩn vẫn đang hoạt động tốt.** Trên đúng bia đo đó, nó bắn F209 (rò rỉ stack trace)
ở **17/20 lần chạy**. Các oracle bảo mật của Şahin đang chạy bình thường và đang tìm ra lỗi bảo mật thật.
Vì vậy con số 0 trên lỗi có trạng thái **không thể quy cho cấu hình sai**.

**Bằng chứng 2 — đo trực tiếp *hình dạng* của test sinh ra**, hoàn toàn độc lập với mã lỗi. Viết một
script phân tích mã nguồn các test mà đối chuẩn sinh ra, đếm xem nó có bao giờ tự ghép được công thức
`ghi → hạ quyền → ghi lại cùng token` hay không. Kết quả trên **1.909 test** từ 20 lần chạy:

| Chỉ số | Số lượng |
|---|---|
| Lần ghi vào endpoint hạ quyền | 145 |
| Lần ghi vào endpoint bị canh quyền | 148 |
| Test chứa **cả hai** | 5 |
| Test ghép đúng thành **bộ ba** | **0** |

Đối chuẩn chạm vào cả hai mảnh ghép rất nhiều lần, thậm chí 5 lần có cả hai trong cùng một test — nhưng
**không lần nào** xếp đúng thứ tự để lỗi bộc lộ (thứ tự người dùng bị đảo lộn, nên công thức không hình
thành).

Kết luận rút ra rất mạnh: đối chuẩn không chỉ **không phán đoán được** lỗi này, nó còn **không dựng được**
tình huống để lỗi xuất hiện. **Vì vậy cả hai nửa của đóng góp đều cần thiết** — chỉ thêm oracle phán đoán
là không đủ, phải có cả bên dựng.

---

## 7. Một phát hiện phụ có giá trị học thuật

Khi mở rộng từ Tier-1 sang Tier-2, oracle bản đầu cho **dương tính giả**. Nó nhận *bất kỳ* lời gọi thành
công nào của một người dùng khác làm "phép chuyển đổi", nên đã báo lỗi trên chuỗi
`GET /me → GET /users/v1/_debug → GET /me` — một chuỗi **không có phép chuyển đổi nào cả**.

Lỗi này chỉ lộ ra ở Tier-2 vì app tự viết có quá ít đường đọc nhiều người dùng. Nó bị bắt nhờ một dấu
hiệu bất khả: số lần *bắn* nhiều hơn số lần *dựng được bộ ba* — điều không thể xảy ra nếu oracle đúng.

Bản sửa (+41 dòng) siết ba điều kiện: hành động can thiệp phải **thật sự trông như một phép giảm quyền**
(dùng chung một hàm kiểm tra với bên dựng, để hai bên không thể lệch nhau); hành động nguồn phải là một
phép **ghi** (một phép *đọc* vẫn đọc được thì không chứng minh gì về quyền *ghi* đã bị thu); và hành động
nguồn không được chính là endpoint chuyển đổi.

**Vì sao đây là nội dung luận văn, không chỉ là sửa bug:** nó là **bằng chứng thực nghiệm cho thấy điều
kiện canh quyền ở mục 4 là bắt buộc**, không phải chi tiết hình thức cho đẹp. Bỏ nó ra thì oracle báo sai
ngay trên một ứng dụng thật. Đây là loại lập luận mà hội đồng đánh giá cao hơn hẳn một khẳng định lý thuyết.

Sau khi sửa, đo lại toàn bộ: **số dương tính thật không giảm chút nào**, và lớp dương tính giả biến mất
hoàn toàn trên cả hai bia đo.

---

## 8. Hạn chế — báo cáo trung thực

**Recall ở Tier-2 là 20%, thấp hơn Tier-1 (80%).** Nguyên nhân đã xác định rõ, và nó **không phải oracle sai**:

Số lần bắn **khớp chính xác** số lần dựng được bộ ba (4 = 4). Trên một bia đo có lỗi, một bộ ba đã dựng
đúng sẽ bộc lộ lỗi một cách **tất định** — nên mỗi lần bỏ sót là một lần **không dựng được bộ ba nào**,
tức là hạn chế ở **giai đoạn dựng**, không phải ở giai đoạn phán đoán. Bên dựng phải suy luận endpoint
chuyển đổi trên một ứng dụng nó chưa từng được tinh chỉnh cho, dựa trên tín hiệu tên gọi — và nó thành
công trên 4/20 seed. Hướng cải thiện (mở rộng tập tín hiệu suy luận) đã viết vào phần hướng phát triển.

**Fuzzing hộp đen không reset được trạng thái giữa từng bộ ba.** Nên các bộ ba dùng chung trạng thái
server: một ca dựng trước đó có thể vô tình hạ quyền một người dùng mà ca sau cần dùng làm *người thực
hiện* phép hạ quyền, khiến phép đó bị 403 và bộ ba không hình thành. Quan trọng: cơ chế này chỉ gây
**bỏ sót**, **không bao giờ gây báo sai** — và phép so sánh vi phân (có lỗi bắn / đã sửa im) miễn nhiễm với nó.

**Phạm vi có ý thức.** Phần lõi cam kết duy nhất là biến thể hạ quyền theo vai trò (role downgrade), nơi
"phải bị từ chối" là không thể tranh cãi. Hai biến thể cùng họ — quyền còn sau khi chuyển giao sở hữu, và
gói dịch vụ còn hiệu lực sau khi hết hạn — đã được định nghĩa hình thức để chứng minh khung lý thuyết tổng
quát hoá được, nhưng chỉ hiện thực nếu còn thời gian. Oracle này **không** tìm lỗi khác-người (BOLA/BFLA) —
đó là trục của Şahin, và hai bên bổ sung cho nhau.

---

## 9. Trạng thái hiện tại và việc còn lại

**Đã xong:**

- ✅ Hình thức hoá quan hệ metamorphic (tài liệu sẵn sàng đưa vào luận văn)
- ✅ Oracle phán đoán, hiện thực trong EvoMaster core
- ✅ Bên dựng ca kiểm thử tự động — đóng góp chính
- ✅ Hai bia đo có đáp án biết trước, tái tạo được từ mã nguồn
- ✅ Đo lường đầy đủ: 40 lần chạy Tier-1 + 80 lần chạy Tier-2, đã kiểm tra tính toàn vẹn dữ liệu, mọi
  lần bắn đã đọc tay xác nhận
- ✅ Chứng minh đối chuẩn mù về cấu trúc, bằng hai bằng chứng độc lập

**Còn lại:** viết luận văn. Nguyên liệu cho chương phương pháp và chương thực nghiệm đã đầy đủ; phần mã
nguồn coi như đóng băng. Sát ngày bảo vệ sẽ kiểm tra lại tính mới một lần nữa (lần cuối 31/07/2026).

Toàn bộ mã nguồn và dữ liệu đo đều được lưu trữ và tái tạo được: bản vá EvoMaster kèm hướng dẫn áp dụng
lên một bản clone sạch, mã nguồn hai bia đo, script chạy thực nghiệm, và dữ liệu thô của cả 120 lần chạy.


