# Vòng 2 — chuyên gia A đọc bài chuyên gia B

Cách kiểm: tôi chạy lại các script `peer-work/s05`, `s06`, `s07`, `s08`, `s09`, `s10`, `s11`, `s12`, `s13`, `s14`, `s16`
(đều chỉ đọc dữ liệu). Mọi số họ trích từ các script này đều khớp với đầu ra tôi nhận được. Tôi đọc thêm
`R1/adjudicate.py` và `R1/rows/chunk-028.txt:1598-1603`. Những chỗ cần tách nguyên nhân, tôi viết script riêng:
`work/w17_peer_checks.py`. Viết tắt giữ như `round1.md`. "Op T" theo định nghĩa của B: op ghi có cả trường A
(role/perms/admin) lẫn trường C.

## 1. Đồng ý

- **Y1 (đơn vị đo).** Đồng ý.
  - Đã chạy `s07`. Trên 24 op T của test, R4 bắt đúng trường A ở 6 op, viết tay ở 10 op. Nạn nhân chọn đúng ngay lượt
    đầu: R4 10/24, viết tay 14/24. Hai số nạn nhân này khớp `w07` §3 của tôi.
  - `s09` §4: trong 2.060 cặp lệch McNemar của C, có 1.869 cặp chỉ do `id`.
  - Đây là bằng chứng mạnh nhất rằng phép đo mức trường bị chi phối bởi một từ mà runtime chỉ dùng làm dự phòng.
- **Y2, Y3 (không ổn định; chọn luật theo nhiễu).** Đồng ý.
  - Bootstrap của họ (`s06`) và của tôi (`w08`) cho cùng hình ảnh. `role` vào danh sách R4 ở 73% số lần (tôi tính
    được 67%). R4 đứng đầu trên dev ở 73% số lần (tôi tính được 69%).
  - `s13` xác nhận B-low và B-high cho cùng F1 ở cả năm luật, nên không phân biệt được luật nào. Chênh lệch giữa các
    luật đến từ C và A-admin.
- **Y5 (phạm vi nhãn).** Đồng ý.
  - `s10`: 100/177 dương A-role ở train+dev nằm trong op không có C. Các từ `create` (18/21 dương), `delete` (10/13),
    `members` (11/13) đến từ nhóm này.
  - Tôi kiểm thêm (`w17` §3): 48 dương của configcat chỉ đến từ 4 op, trong đó 2 op góp 23 dương mỗi op.
- **Y6 (cấu trúc bị mất).** Đồng ý.
  - `admin` trong `transitionScore` khớp 46 op không có A ở train+dev và 67 op ở test. Riêng fecru.local là 30 op
    (`s08`, `s09` §6). Tổng là 131 op, khớp `w07` §2 của tôi.
  - Việc gộp `:414` với `:415` làm mất thứ tự specific → email → `id`. Đây là điểm tôi chưa nói rõ.
- **Y7 (điểm thiên về precision).** Đồng ý. Hệ số ncc/(ncc+1) quá yếu. `privilege` (2 nhà cung cấp, 4/5 dương từ
  id4i) xếp trên `role` (12 nhà cung cấp), xem `s04`.
- **Y8 (độ đúng của nhãn chưa được đo).** Đồng ý, và đây là điểm tôi bỏ sót. `R1/adjudicate.py:5-26` quyết phân xử
  theo danh sách chỉ số, mỗi luật một câu lý do mẫu. Ví dụ: 23 dòng của một op configcat (S104-0025) được quyết
  chung "theo L2" (`R1/adjudication.csv:11-33`). Không có bằng chứng riêng cho từng dòng.
- **Y9 (tỉ lệ nền khác nhau giữa các tập).** Đồng ý. Đã chạy `s09` §1: tỉ lệ A là 2,36% (phần cũ), 0,50% (train
  mới), 0,29% (dev), 0,65% (test). Phần cũ có nhãn cũ 51 R / 669 N.
- **Y10, Y12, Y13.** Đồng ý. KTC của họ cho hiệu F1 A-role là [−0,225; 0,066], của tôi là [−0,229; 0,068].
- **Y4, phần thực trạng dữ liệu.** Đồng ý.
  - B có rất ít dữ liệu: 9 enum với 5 nhà cung cấp ở train, 5 enum ở test (`s03` §3).
  - Đồng thuận B: 17/27 về B_low và 20/27 về B_high khi tính cả trường chỉ một lượt gán (`s12`). Con số này bổ sung
    cho 17/19 của tôi, vốn chỉ tính trường cả hai lượt cùng gán.
  - apple.com `roles` có đúng 12 giá trị, bằng `MAX_ENUM` (`s09` §3), nên enum có thể đã bị cắt. Đây là suy luận:
    gói không có spec thô để kiểm.
- **Các đề xuất.**
  - Đ1 (đo lại trên nhãn sẵn có trước): đồng ý, và tôi đổi thứ tự của mình theo (xem mục 3).
  - Đ3 (tách A-gán, A-định-nghĩa, A-credential; C-user, C-phi-user): đồng ý.
  - Đ5(c) (lấy chuẩn từ mã nguồn API mở): đồng ý. Đây là cách duy nhất trong cả hai bài đo được độ *đúng* của nhãn mà
    tác giả không phải tự gán.
  - Câu hỏi 6 (gene gốc của body có thể mang tên schema như `RoleUpdateRequest`, và khi đó khớp `role`) là điểm tôi
    chưa nghĩ tới. Nó phải được kiểm trước khi tin bất kỳ bộ mô phỏng nào.

## 2. Không đồng ý hoặc cần sửa

- **Y4, kết quả B theo thứ hạng (`s08`): R4 5/8 so với viết tay 4/8 trên test. Con số đúng nhưng dễ đọc sai.**
  - 2 trong 5 lần R4 đứng đầu là adafruit `r|w|rw`. Ở đó không giá trị nào khớp danh sách R4, nên `r` đứng đầu chỉ vì
    thứ tự enum. Tính riêng các lần đứng đầu do danh sách quyết định: viết tay 4, R4 3 (`w17` §1).
  - Trên train+dev, vốn là dữ liệu R4 được rút ra, viết tay đúng 15/21, R4 đúng 10/21 (`s08` cũng in ra số này
    nhưng bài không nêu).
  - Gộp cả hai tập, phần do danh sách quyết định là 19/29 cho viết tay và 13/29 cho R4. n vẫn rất nhỏ.
- **Y5: "dương C trên path của chủ thể không phải người dùng 22% (test)" là ước lượng hơi cao.**
  - Regex của `s09` §2 bắt cả những trường mà chủ thể thật ra là user: `ownerObjectId` ×2, `url` trong
    `$links/owners` ×2, `principalId` của `oauth2PermissionGrants`, `pwdreset.authorizables` (`w17` §2).
  - Bỏ khoảng 6 trường đó (đây là cách tôi đọc path, chưa kiểm bằng nguồn), tỉ lệ còn khoảng 22/127 ≈ 17%.
  - Kết luận định tính không đổi.
- **Y6: "14 trường con của mảng quyền (`roles[].id`, `.name`, `.type`) được gán dương theo tên lá" là nói quá.**
  - `s04` đếm 14 dương A-role có tên lá chung chung, nhưng chỉ 9 trường nằm trong object hoặc mảng.
  - Phần còn lại, như `name` của keycloak `role-mappings`, là trường cấp 1 của body dạng mảng.
- **Y8: 26 + 12 "âm có tên rõ nghĩa" (`s05`) không phải bằng chứng nhãn sai.**
  - Tôi đọc cả 38 dòng. Đa số là âm đúng theo luật: role của tài nguyên (superset dashboard, netbox IP, daniweb
    position, ix-api network config); `permission` của consent (apisetu, nbg); trường tạo credential (launchdarkly
    token, fire.com app).
  - Chỉ vài dòng thật sự tranh cãi được, ví dụ conjur `role` khi xoay API key.
  - Danh sách này nên dùng làm mẫu để kiểm, không nên dùng làm ước lượng tỉ lệ lỗi.
- **Y3: so trung bình F1 mức trường trên test ("R1 = R3 0,451 > R4 0,431 > viết tay 0,413") dùng đúng thước đo mà
  Y1 của chính họ bác bỏ.** Thước đo đó gồm C, nơi viết tay bị phạt vì `id`. Không nên dùng nó để xếp viết tay đứng
  cuối.
- **Đ2: ước lượng "sản lượng tăng 2,5 lần" dựa trên một bộ lọc path dùng chính từ của danh sách.**
  - Bộ lọc khớp `users`, `members`, `roles`, `permissions` (`s09` §8). Điều này trái với nguyên tắc "không dùng từ của
    danh sách" mà chính họ nêu trong Đ2.
  - Bộ lọc này bỏ sót 4/21 spec có A (19%), và chính những spec đó mang từ vựng lạ mà ta cần tìm.
  - Cần đo recall của bộ sàng lọc thật (dùng LLM, không dùng từ khoá) trên 228 spec đã có nhãn trước khi ước lượng
    sản lượng.
- **Đ4: "chọn bằng thước đo Đ1 trên dev" không khả thi.** Dev chỉ có 6 op T từ 5 nhà cung cấp (`s07`). Nên chọn
  bằng kiểm chéo nhóm theo nhà cung cấp trên toàn bộ train+dev (51 op T, 27 nhà cung cấp; `s16`), như `w10`.
- **Y1: câu "60.874 nhãn chỉ cho 75 op T" ngầm coi nhãn âm là lãng phí.** Để đo báo nhầm mức API (`w07` §1:
  viết tay báo nhầm ở 8 API test, R4 ở 3), vẫn cần nhãn âm ở mức op cho mọi op ghi. Phần thừa là nhãn âm mức
  *trường* ở các op không phải T, không phải mọi nhãn âm.

## 3. Tự sửa (round1.md)

- **Y1, ví dụ B ("viết tay đứng đầu 4/8, R4 1/8"): rút lại với vai trò bằng chứng về danh sách B.**
  - Con số 1/8 đo cả chuỗi xử lý. Nó thấp vì danh sách A-role của R4 không nhận trường `role`, nên op không có ứng
    viên. Danh sách B không phải nguyên nhân.
  - Nếu đo riêng danh sách B thì xem mục 2: test 4 so với 3 (do danh sách quyết định), train+dev 15 so với 10.
  - Con số 1/8 chỉ còn giá trị như ví dụ về lỗi A-role lan sang bước sau.
- **Y8 (khối 028/031): hạ mức ảnh hưởng tới danh sách từ "vừa" xuống "thấp".**
  - Các âm có từ khoá mà tôi liệt kê (`w04`) và mà B liệt kê (`s05`) phần lớn là âm đúng theo luật: `ownerReferences`,
    `author.username`, `creator.username`.
  - Chỗ có khả năng bỏ sót (Bitbucket `permissions-config`) lại không trích được body.
  - Điểm cấu trúc vẫn giữ: định dạng chỉ ghi dòng dương làm việc bỏ sót không phát hiện được.
- **Y9 (phân xử): sửa.**
  - Tôi viết "ảnh hưởng tới số: nhỏ; còn lại là tính bảo vệ được". Câu đó đúng về số nhưng bỏ sót điều chính: phân
    xử được quyết theo khối chỉ số với câu lý do mẫu (`adjudicate.py`). Mức tôi đánh giá cho tính bảo vệ được nâng
    lên cao.
  - Về số, tôi đã kiểm khối lớn nhất (S104-0025, 23 dòng): nếu quyết theo L1 thì dương A-role giảm từ 178 xuống 155,
    nhưng các danh sách R4 không đổi (`w17` §3).
- **Thứ tự đề xuất.** Đ1 của tôi mở đầu bằng gán nhãn lại mức op. Tôi đổi theo B: đo lại trên nhãn sẵn có trước, vì
  rẻ hơn và quyết định được có cần gán thêm hay không.
- **Đ3 của tôi.** Bỏ "L2 khác họ model" khỏi vai trò kiểm độ đúng. Đồng thuận giữa các model chỉ là đồng thuận,
  không phải độ đúng. Kiểm độ đúng bằng chuẩn lấy từ mã nguồn (Đ5(c) của B) có giá trị hơn.
- **Số nạn nhân của R4 trên test: 10 đúng, 5 sai, 9 không chọn (của tôi) so với 10/6/8 (của B).** Chênh 1 op vì tôi
  coi gene object/array/boolean không đặt được giá trị. Đây không phải lỗi, chỉ là giả định của mô phỏng, nhưng cho
  thấy kết quả nhạy với giả định về kiểu.

## 4. Đề xuất hợp nhất

Mục tiêu là đo đúng trước, sau đó mới quyết có cần thêm dữ liệu không. Không giả định trước danh sách nào thắng.

**B0. Chốt khung trước khi đo** (nửa ngày).
- Cách làm: trả lời bằng văn bản các câu hỏi sau:
  - quần thể đích là API công khai hay ứng dụng tự host;
  - thước đo chính cho từng danh sách, gồm: transition top-1 ở mức API, bắt được trường A trong op T, nạn nhân top-1,
    hạng B do danh sách quyết định, số op `transitionScore` báo nhầm;
  - ngưỡng không-kém-hơn δ so với danh sách viết tay;
  - danh sách nào sẽ vào mã, và chỉ danh sách đã đo mới được vào.
- Phản biện: chốt sớm có thể chọn sai thước đo. Nếu đổi sau đó thì phải ghi lệch luật và đo lại mọi thứ.

**B1. Bộ mô phỏng và đo lại trên nhãn sẵn có** (1–2 ngày).
- Cách làm:
  - Hợp `w07` với `s07`/`s08` thành một bộ mô phỏng.
  - Kiểm trên mã EvoMaster: tên gene gốc của body, tên phần tử mảng, `setFromStringValue` cho từng kiểu.
  - So viết tay, R4, và hợp của hai danh sách. Bootstrap theo nhà cung cấp, chọn tham số bằng kiểm chéo nhóm.
- Phản biện:
  - Mô phỏng vẫn xấp xỉ: tôi và B lệch 1/24 op chỉ vì giả định về kiểu.
  - n nhỏ (75 op T; 27 nhà cung cấp ở train+dev, 18 ở test), nên có thể không tách được các danh sách.

**B2. Kiểm toán nhãn, tác giả không gán** (khoảng 1–2 ngày agent).
- Cách làm:
  - (a) Phân xử lại toàn bộ khoảng 233 dòng lệch, mỗi dòng một quyết định, do một phiên mới làm, không biết nhãn nào
    của L1 hay L2, và có trích bằng chứng. Phương án này thay cho cách quyết theo khối chỉ số.
  - (b) Đọc trọn khối 028 và 031 với định dạng ghi cả dòng âm, kèm script so số dòng.
  - (c) Lấy chuẩn từ mã nguồn cho 5–10 API mở có trong corpus (keycloak, gitea, gitlab, superset, apicurio). Agent
    trích file:dòng, rồi ước lượng precision và recall của nhãn.
  - (d) Báo độ nhạy: kết luận ở B1 có đổi chiều không khi dùng nhãn cuối, chỉ L1, chỉ L2, hoặc nhãn sau kiểm toán.
- Phản biện:
  - Vẫn là LLM.
  - Chuẩn từ mã nguồn lệch về ứng dụng tự host.
  - Nếu (d) cho thấy kết luận không đổi (như `w11`), (a) và (b) chủ yếu chỉ để tăng tính bảo vệ được.

**B3. Gán lại lớp dương theo vai trò runtime** (khoảng 570 trường dương × 2 lượt, cộng một lượt có/không mức op
cho khoảng 3.800 op).
- Cách làm:
  - Tách A thành A-gán, A-định-nghĩa, A-credential; tách C thành C-user, C-phi-user.
  - Ghi "tên builder sẽ so" cho trường lồng.
  - Thêm nhãn mức op cho mọi op ghi, để đo báo nhầm.
  - Chỉ rút từ A-gán và C-user. Mọi tập dùng cùng một luật gán.
- Phản biện:
  - Số dương giảm còn khoảng 77 trường A trong op T ở train+dev.
  - Có nguy cơ định nghĩa bị may đo theo builder hiện tại.

**B4. Luật rút khai trước, mỗi từ có thẻ bằng chứng** (1–2 ngày).
- Cách làm:
  - Ứng viên: token tách camelCase trên tên gốc, gộp số ít và số nhiều, cộng các từ viết tay. Từ viết tay cũng phải qua
    kiểm như mọi ứng viên khác.
  - Đếm theo cặp (nhà cung cấp, tên lá), chỉ trong op T.
  - Luật giữ từ:
    - ≥ 3 nhà cung cấp dương;
    - precision theo nhà cung cấp ≥ θ;
    - ổn định ≥ 0,7 qua bootstrap.
  - θ và k chọn bằng kiểm chéo nhóm, riêng cho từng danh sách.
  - Giữ cấu trúc của builder:
    - C ba tầng, `id` là dự phòng ngoài từ vựng;
    - danh sách admin cho `transitionScore` đo bằng số op báo nhầm.
  - B: báo "corpus không đủ" nếu có dưới 15 enum từ 10 nhà cung cấp. Hiện chỉ có 18 enum trên cả ba tập, nên B rất
    có thể ra "không đủ".
  - Đầu ra là bảng xếp từ vào ba nhóm: đủ bằng chứng, không có bằng chứng, bị dữ liệu bác.
- Phản biện:
  - Các ngưỡng là tùy ý.
  - Danh sách sẽ ngắn. Với dữ liệu hiện có, A-role chỉ còn khoảng `role`, `roles`, `permission`, có thể thêm `allow`
    (3 nhà cung cấp dương, 1 có âm). C còn `user`, `userid`, `user_id`; `email` (3 dương, 6 có âm) còn hay không tùy
    θ (`s16`).
  - Đưa từ viết tay vào làm ứng viên có thể bị xem là neo theo danh sách cũ.

**B5. Bốc thêm, chỉ khi KTC ở B1–B4 rộng hơn δ.**
- Cách làm:
  - Sàng lọc spec bằng LLM, không dùng từ khoá của danh sách. Trước hết đo recall của bộ sàng lọc trên 228 spec đã có
    nhãn.
  - Bốc hai pha có trọng số nghịch đảo xác suất chọn.
  - Mục tiêu: một tập test khoá có khoảng 100 op T từ ít nhất 40 nhà cung cấp.
- Chi phí: sàng lọc vài trăm spec, gán nhãn khoảng 100 API. Nguồn ngoài APIs.guru tốn thêm vài ngày.
- Phản biện:
  - Tầng giàu của APIs.guru đã cạn.
  - Bộ sàng lọc có thể bỏ sót đều đặn API đặt tên lạ.
  - Nguồn mới làm dữ liệu kém đồng nhất.

**B6. Cổng cuối: chạy EvoMaster** (cao).
- Cách làm: chạy viết tay, danh sách rút, và hợp của hai danh sách trên 6 target cộng 2–4 ứng dụng mã mở chạy bằng
  docker chưa dùng để viết danh sách, mỗi cấu hình ≥ 10 seed.
- Phản biện: 6 target không phải held-out. Số target nhỏ. Kết quả còn phụ thuộc lexicon transition và cấu hình xác
  thực.

## 5. Bất đồng còn lại

- Về B: dữ liệu hiện có, đo riêng danh sách B, nghiêng về viết tay (19/29 so với 13/29). B không đọc ngang hoặc
  nghiêng về R4 như cách trình bày 5/8 so với 4/8.
- Chọn luật hay ngưỡng phải bằng kiểm chéo nhóm trên train+dev. Dev đơn lẻ (6 op T) không đủ, kể cả khi dùng thước
  đo mức op.
- Ước lượng sản lượng bốc mẫu phải dựa trên bộ sàng lọc không dùng từ của danh sách. Con số 2,5 lần của B chưa thỏa
  điều kiện này.
- Nhãn âm mức op cho mọi op ghi vẫn cần, để đo báo nhầm mức API và tác dụng phụ của `transitionScore`. Không coi
  chúng là phần thừa.
- Danh sách "âm có tên rõ nghĩa" (`s05`) không đủ để nói về độ đúng của nhãn. Chỉ chuẩn từ mã nguồn (B2c) làm được
  việc đó.
- Tỉ lệ C phi-user ở test vào khoảng 17%, không phải 22%. Đây là chênh lệch về con số, kết luận giữ nguyên.
