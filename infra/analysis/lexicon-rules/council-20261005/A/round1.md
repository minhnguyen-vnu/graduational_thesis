# Vòng 1 — chuyên gia A

Viết tắt: `R1/` = `lexicon-rules/field-labelling-20261004/`, `R2/` = `lexicon-rules/field-labelling-r2-20261004/`,
`kt` = `code/RestSecurityBuilder.kt`. Tập: train = nửa train vòng 1 (90 nhà cung cấp), dev = nửa test vòng 1 (46),
test = vòng 2 (92). "R4" = luật đã chọn (top 5 theo điểm, `R2/common.py:55-56`); "R4 train+dev" là danh sách được đo
(`R2/results.json`); "R4 gộp" là danh sách rút trên cả ba tập (`R2/merged-lists.json`), chưa đo.

Script của tôi nằm trong `work/` và chỉ đọc dữ liệu. `work/w01_reproduce.py` tái lập đúng mọi số trong `select.json`,
`results.json`, `merged-lists.json`, nên các số dưới đây dùng cùng dữ liệu và nhãn cuối. `work/w07_runtime_sim.py`
là mô phỏng xấp xỉ logic của `kt`, chưa chạy EvoMaster thật. Các giả định của nó ghi ở đầu file. Số lấy từ mô phỏng
đều ghi là "(mô phỏng)".

## 1. Điểm yếu

### Mức cao

**Y1. Đo theo từng trường, trong khi runtime dùng danh sách theo operation, theo thứ tự ưu tiên và có tác dụng phụ.**
- Là gì: §6 đo P/R/F1 trên mọi trường của mọi operation ghi, mỗi trường một tài liệu độc lập. Ở `kt`, các danh sách
  được dùng khác hẳn:
  - `roleFieldSignals` lọc xem transition nào dùng được (`kt:523-529`, `:958-967`), và chỉ áp lên ≤ 8 ứng viên đã
    xếp bằng lexicon đường dẫn (`kt:76`, `:517`).
  - Danh sách nạn nhân dùng theo thứ tự path → body → query và cụ thể → email → `id` (`kt:1053-1077`). `id` chỉ là
    lớp dự phòng cuối.
  - `roleLow/High` chỉ xếp thứ tự giá trị enum của mọi gene trong op, không lọc (`kt:976-983`, `:988-996`).
- Ví dụ:
  - C, đo mức trường: R4 F1 0,224 so với viết tay 0,083; McNemar p≈0 (`R2/results.json` mục C). Mô phỏng chọn nạn
    nhân trên 24 op test có cả trường A và trường C cho kết quả ngược lại: viết tay chọn đúng 14, sai 10; R4 chọn
    đúng 10, sai 5, không chọn được 9 (`w07` §3).
  - B, đo mức trường: F1 viết tay 0,75, R4 0,571. Đo theo hạng của B_low trong danh sách ứng viên: viết tay đứng đầu
    4/8, R4 đứng đầu 1/8, vì R4 không nhận trường `role` nên op không có ứng viên (`w07` §5, mô phỏng).
- Ảnh hưởng: kết luận "tốt hơn/kém hơn" trong `results.json` và `mcnemar.json` không chuyển sang được hành vi runtime.
  Hướng có khi ngược lại.

**Y2. Tác dụng phụ của `ADMIN_FLAG_FIELD_SIGNALS` lên điểm transition không được đo.**
- Là gì: danh sách này còn được khớp chuỗi con trên `path + tên op + tên trường body` và cho điểm 0,6 (`kt:104-112`,
  `:120-121`). 0,6 cao hơn mọi điểm của lexicon đường dẫn, cao nhất là 0,5455 (`code/stateful-authz-lexicon.csv:2`).
  Tài liệu A-admin lại chỉ gồm trường boolean (`R1/derive_eval.py:92`).
- Ví dụ: trên 3.823 op ghi, thay bằng `['admin']` (R4) đẩy 131 op lên 0,6. Trong đó 48 op có điểm > 0 chỉ nhờ
  danh sách admin. `['admin','owner']` (R4 gộp) đẩy 279 op. Danh sách viết tay đẩy 1 op (`w07` §2, mô phỏng).
  `owner` lọt vào R4 gộp với precision 0,0588 (2 dương, 32 âm; `R2/merged-lists.json:82`, `:94-100`).
- Ảnh hưởng: thứ hạng transition của mọi API có `admin` trong đường dẫn bị thay đổi. Điều này không hiện ra trong
  bất kỳ số nào đã báo.

**Y3. Luật R4 bỏ từ cốt lõi, chọn từ hẹp; danh sách cuối gần như là một lần rút ngẫu nhiên.**
- Là gì: điểm `(df+ +1)/(df+ +df- +2) × ncc/(ncc+1)` không có thành phần độ phủ. Khớp chuỗi con làm từ dài hơn
  thường có precision cao hơn từ ngắn. R4 lấy 5 từ đầu, không có ngưỡng precision tối thiểu.
- Ví dụ:
  - Trên train+dev, `roles` có điểm 0,451 và đứng thứ 2; `role` (26 dương, 12 nhà cung cấp) có điểm 0,346 và đứng
    thứ 7. Danh sách A-role vì thế không có `role` (`w09` §2).
  - Neo: R4 train+dev không nhận `role` của reports-api, vampi, pyLoad; không nhận `email` của bamf, `id` của
    artifact-keeper; không nhận B thấp `VIEWER`, `user` (`R2/anchor.json`). R4 gộp trượt cả 6 trường C neo
    (`w16`).
  - Bootstrap theo nhà cung cấp trên train+dev (P1 đếm nhà cung cấp thật): danh sách A-role R4 tái hiện đúng trong
    1% lần rút; `role` được chọn 67%. Danh sách C tái hiện đúng 17% (`w08` §2).
  - Đổi nguồn nhãn (cuối / chỉ L1 / chỉ L2) làm danh sách đổi 1–3 từ, ví dụ L2 cho `roleid`, `login`
    (`w14`).
- Ảnh hưởng: từng từ khó bảo vệ là "có cơ sở dữ liệu", vì thêm hay bớt vài nhà cung cấp là danh sách đã khác.

**Y4. Chọn luật trên một dev quá nhỏ, lấy trung bình chung cho năm danh sách.**
- Ví dụ:
  - Dev có A-admin 2 dương từ 1 nhà cung cấp; B có 5 dương; A-role có 17 dương, trong đó 82% đến từ 3 nhà cung cấp
    (`w02` §4).
  - R4 thắng R1 hoàn toàn nhờ C (+0,189). Ở A-role, R4 còn kém hơn (−0,038) (`w08` §3). Bootstrap dev cho
    P(R4 thắng) = 0,69.
  - Kiểm chéo nhóm 5 phần × 4 lần trên cả 228 nhà cung cấp: A-role R4 có F1 trung bình 0,223, viết tay 0,318; R4
    thắng viết tay ở 6/20 phần, trong khi R1, R3 xấp xỉ viết tay (0,303; 0,298) (`w10`).
- Ảnh hưởng: luật đã chọn có thể là luật kém nhất cho danh sách quan trọng nhất (A-role).

**Y5. Nhãn A và C rộng hơn thứ runtime cần.**
- Là gì: A gồm cả trường định nghĩa quyền của role và cờ khả năng boolean (`R2/PROTOCOL.md:38`). C gồm cả client,
  API key, token (`R2/PROTOCOL.md:36`). Runtime cần trường gán vai trò cho một *user* đã tồn tại, nằm cùng op với
  trường nạn nhân; giá trị nạn nhân là tên đăng nhập (`kt:743`, `:1053-1058`).
- Ví dụ:
  - Trong dương A-role, perms boolean chiếm 86/161 ở train và 24/61 ở test (`w09` §4).
  - configcat.com góp 48/161 dương A-role của train, toàn kiểu `canCreateOrUpdateConfig` (`w02` §4, `w03` §2).
  - 92/167 trường A ở train nằm trong op không có trường C (`w12` §1).
  - Các từ `approve`, `restrict`, `privilege`, `groupids` đến từ những cờ này: `can_approve_pull_request_reviews`,
    `isTimesheetApprover`, `is_restricted`, `permissionGroupIds` (`w03` §1).
  - `clientid` vào danh sách C.
  - Số API có op chứa A role/admin cùng C trong một op chỉ là 12 (train), 3 (dev), 13 (test) (`w12` §1).
- Ảnh hưởng: từ được rút tối ưu cho một khái niệm khác với khái niệm runtime dùng. Cỡ mẫu hiệu dụng là khoảng 28 API,
  không phải 30.437 trường.

**Y6. Cỡ mẫu và cách kiểm định không đủ để kết luận.**
- Ví dụ:
  - CI 95% bootstrap theo nhà cung cấp cho hiệu F1 test (R4 − viết tay): A-role −0,059 [−0,229; 0,068], A-admin
    +0,334 [−0,267; 0,889], C +0,141 [0,042; 0,262], B-low −0,179 [−0,511; 0], B-high −0,145 [−0,600; 0]. B chỉ
    có 5 nhà cung cấp (`w08` §1).
  - McNemar tính trên từng trường, coi trường là độc lập (`R2/evaluate.py:78-92`) và đếm cả âm đúng. Với A-role
    nó cho p = 0,0026, nghiêng về R4, trong khi R4 có TP 13 so với 23 và F1 thấp hơn. Tách riêng trường dương thì
    viết tay đúng 10, R4 đúng 0 (`R2/exploratory.json`, `split_mcnemar`).
- Ảnh hưởng: các p-value đã báo không trả lời câu hỏi "danh sách nào tốt hơn".

**Y7. Danh sách định dùng có thể không phải danh sách đã đo.**
- Ví dụ: `merged-lists.json` tự ghi "không có tập đo held-out" (`:2`). Nó khác danh sách đã đo:
  - A-role: `groupids` thay cho `restrict`;
  - A-admin: thêm `owner`;
  - C: cả 5 từ khác hẳn (`collaborator, membershipid, principalid, useremail, userid` so với
    `clientid, member, user`).
- Ảnh hưởng: nếu bản gộp được đưa vào `kt`, không có số nào bảo chứng cho nó. Ở neo, nó kém bản đã đo (`w16`).

### Mức vừa

**Y8. Định dạng đầu ra chỉ ghi dòng dương, nên bỏ sót không phân biệt được với âm.**
- Là gì: "trường không có dòng = không A, không C" (`R1/PROTOCOL.md:83-85`). Vòng 1 có hai khối đọc qua grep
  (`R1/PROTOCOL.md:148-150`).
- Ví dụ: khối 028, 031 có 3.243 trường (7 spec, gồm Kubernetes và Bitbucket), cho 0 trường A và 6 trường C. Các khối
  khác có 11,8 A trên 1.000 trường. 3.177 trường của hai khối này nằm trong train (`w02` §5, `w04`).
- Ảnh hưởng: có thể có âm giả trong train, làm tăng df− của từ quyền. Mức độ không đo được vì không có dòng để kiểm.

**Y9. Phân xử và độ mù.**
- Là gì: phân xử do chính phiên L1 làm. L1 và L2 cùng nhà cung cấp model (`R1/PROTOCOL.md:79-81`). Vòng 2 bị lộ mù
  ở khối 020–022 (`R2/PROTOCOL.md:110-112`).
- Ví dụ:
  - Phân xử theo L1/L2: vòng 1 là 108/51, vòng 2 là 44/28. Ở test, lệch nhị phân C được phân xử 37 lần theo L1,
    12 lần theo L2 (`w02` §3).
  - Khối 020–022 chứa 27/78 trường A và 34/127 trường C của test (`w02` §5).
- Ảnh hưởng tới số: nhỏ. Thay nhãn cuối bằng chỉ L1, chỉ L2, hoặc bỏ khối đã lộ đều không đổi chiều so sánh nào
  (`w11` §1–2). Vấn đề còn lại là tính bảo vệ được của quy trình.

**Y10. Luật gán nhãn đổi giữa hai vòng nhưng train/dev không được gán lại.**
- Là gì: vòng 2 thêm 7 luật (`R2/PROTOCOL.md:33-44`) nhưng "nhãn train, dev giữ nguyên" (`:18`). Ví dụ luật
  `reset-target` chỉ có ở vòng 2 (`w12` §2).
- Ảnh hưởng: train và test đo hai khái niệm hơi khác nhau. Không đo được mức lệch.

**Y11. B: không có độ đồng thuận, dữ liệu rất ít, danh sách nhị phân không biểu diễn được thứ tự tương đối.**
- Ví dụ:
  - Chỉ có 19 trường (vòng 1) và 10 trường (vòng 2) được cả hai lượt gán role/perms kèm enum (`w02` §2). Kappa
    không tính cho B (`R1/kappa-raw.json`).
  - S131 `roles`: L1 cho `READ_ONLY/ADMIN`, L2 cho `unordered`, nhãn cuối là `READ_ONLY/ACCOUNT_HOLDER`, khác cả
    hai.
  - windows.net `userType ∈ {Member, Guest}` có B_high = `Member`, nhưng `member` nằm trong cả B-low viết tay lẫn
    B-low R4 (`w03` §5).
- Ảnh hưởng: B-low/B-high rút từ 29 enum không có cơ sở thống kê. Một từ có thể thấp ở API này, cao ở API khác.

**Y12. Giới hạn của bước sinh ứng viên.**
- Là gì:
  - Token phải ≥ 4 ký tự (`R1/derive_eval.py:6`, `:40`), nên không thể sinh `id`, `uid`, `key`, `r`, `rw`.
  - Không chuẩn hoá số ít/số nhiều.
  - Hạ chữ thường trước khi tách camelCase (`R1/derive_eval.py:31-32`, `:35-42`), trái với chữ "tách camelCase" ở
    `R1/PROTOCOL.md:101`.
- Ví dụ:
  - 24/127 trường C dương ở test (19%) không có token ≥ 4 ký tự, gồm `id` ×13 và `ids` ×4. Giá trị B dương `r`, `rw`
    cũng vậy (`w13`).
  - Tách camelCase đúng làm đổi 38 ứng viên A-role. Danh sách R4 A-role không đổi; C mất `clientid`, F1 test từ
    0,224 thành 0,221 (`w03` §2).
- Ảnh hưởng: trần recall do cấu trúc (vừa). Lỗi camelCase có ảnh hưởng thấp.

**Y13. Biểu diễn chỉ bằng tên lá có trần thấp, và corpus khác phân phối đích.**
- Ví dụ:
  - Nếu mỗi tên lá được gán nhãn theo đa số của chính nó trên test, F1 tối đa là C 0,56, A-role 0,82. 20/39 tên lá C
    dương cũng xuất hiện làm âm (`w08` §4).
  - Chỉ 17/61 trường A-role dương ở test có tên lá từng dương ở train+dev.
  - Spec cũ tầng giàu (S100–S214) góp 125/201 trường A của train+dev (`w09` §1).
  - Target tự host bị loại khỏi corpus có chủ ý (`corpus/sample_specs_field.py:8-9`).
- Ảnh hưởng: mọi danh sách tên, viết tay hay rút, đều bị chặn trên. Kết quả trên APIs.guru có thể không áp được cho
  loại target mà luận văn nhắm.

**Y14. Bằng chứng một chiều cho từ viết tay.**
- Ví dụ: trên cả ba tập (df+/df−/số nhà cung cấp; `w03` §3):
  - `plan` 0/26/0, `tier` 0/5/0, `level` 6/28/2, `subject` 0/34/0;
  - `is_admin`, `is_superuser`, `is_superadmin`, `is_staff` 0/0;
  - `basic`, `free`, `restrict`, `limited`, `super`, `root`, `edit`, `power` (B) 0/0.
- Ảnh hưởng: corpus không xác nhận cũng không bác được phần lớn từ viết tay. Riêng `plan`, `tier`, `subject` có
  bằng chứng âm. Đây là dữ kiện về phạm vi của corpus, không phải kết luận rằng từ đó sai.

**Y15. Có dấu hiệu trích trường bỏ sót body (suy luận, chưa kiểm vì không có spec thô).**
- Ví dụ: 42 op PUT/POST/PATCH có summary hoặc path nói về role/permission/admin nhưng không có trường body nào được
  trích, 25 op trong số đó ở test. Ví dụ: jira `PUT /api/2/role/{id}`, fecru
  `PUT .../permissions/groups`, Bitbucket `PUT .../permissions-config/groups/{group_slug}` (`w06`, `w05`).
- Ảnh hưởng: có thể mất trường A dương. Chưa xác định được.

### Mức thấp

- **Y16.** Gán nhãn và rút A-active dù builder không có danh sách tương ứng; precision test 0,036 (`R2/results.json`).
  Đây là chi phí thừa.
- **Y17.** Bộ phân loại B-low chỉ loại trừ từ cao với danh sách viết tay (`R1/derive_eval.py:136-138`), trong khi
  runtime luôn loại trừ (`kt:709-712`). Trên dữ liệu này không đổi số nào (`w11` §3).
- **Y18.** Các luật R0–R4 được thiết kế sau khi đã thấy nửa test vòng 1, tức dev (`R2/PROTOCOL.md:6-8`, `:53-62`).
  Tác giả đã ghi nhận. Việc chọn trên dev vì thế có phần lạc quan.

## 2. Đề xuất

Kết quả hiện có cho hai chiều. Viết tay hơn ở A-role và B; R4 hơn ở A-admin; ở C, kết quả phụ thuộc vào đơn vị đo
(Y1, Y4, Y6). Vì vậy các đề xuất dưới đây nhằm đo cho đúng trước, không giả định bên nào thắng.

**Đ1. Gán nhãn và đo ở đơn vị runtime dùng.**
- Gán nhãn hai tầng.
  - Tầng 1: mỗi op ghi được hỏi "op này có đổi quyền của một user đã tồn tại không" (có/không), đọc path, summary,
    tên trường.
  - Tầng 2: chỉ với op có, gán trường nạn nhân, trường vai trò hoặc cờ admin, toàn bộ thứ tự giá trị enum (không chỉ
    thấp nhất và cao nhất), và kiểu dữ liệu có đặt được không.
  - Tách nhãn phụ cho "định nghĩa role", "cờ khả năng", "credential". Giữ các nhãn này nhưng không trộn vào lớp dương.
- Đo bằng bộ mô phỏng logic `kt` (bản nháp: `work/w07_runtime_sim.py`). Mỗi danh sách một chỉ số chính, khai trước:
  - top-1 transition đúng ở mức API;
  - số API báo nhầm;
  - nạn nhân top-1 đúng;
  - hạng của giá trị hạ quyền;
  - số op bị đổi điểm transition.
- Cổng cuối là chạy EvoMaster với từng phiên bản danh sách trên 6 target. Đối chiếu bảng neo ở
  `R2/PROTOCOL.md:76-83`.
- Chi phí:
  - Tầng 1 trên 3.823 op đã trích: 2 lượt + phân xử, khối lượng gần một vòng cũ nhưng mỗi mục rẻ hơn.
  - Tầng 2 chỉ cho khoảng 3% số op (121/3.823 op có trường A role/perms/admin; `w07` §4).
  - Làm chắc bộ mô phỏng: khoảng 1 ngày.
  - Chạy EvoMaster: 6 target × số phiên bản × số seed.
- Phản biện:
  - Mô phỏng vẫn xấp xỉ: tên gene, khả năng `setFromStringValue`, logic 404. Có nguy cơ tối ưu theo bộ mô phỏng.
  - Nhãn mức op mất thông tin mức trường.
  - Op dương hiếm, nên cỡ mẫu vẫn nhỏ.
  - Target không phải held-out, vì chúng đã định hình danh sách viết tay.

**Đ2. Bốc mẫu theo số API dương, không theo số trường.**
- Mục tiêu khoảng 97 API dương để CI 95% của một tỉ lệ có nửa độ rộng 0,10. Với tỉ lệ API dương 14–23% đã quan sát,
  cần bốc ngẫu nhiên khoảng 420–690 API (`w15`).
- Phương án rẻ hơn là bốc hai pha:
  - Pha 1: LLM sàng lọc ở mức spec, chỉ dùng `info.description`, tags và danh sách path, không dùng tên trường, để
    tránh vòng lặp với từ cần rút.
  - Pha 2: gán nhãn đầy đủ các API được chọn. Bỏ trần 36 op, hoặc ưu tiên mọi op dưới path có user/member.
  - Giữ trọng số nghịch đảo xác suất để ước lượng precision cho quần thể.
- Thêm một tầng riêng gồm ứng dụng tự host có RBAC, không trùng target, nếu quần thể đích là loại này (xem câu hỏi
  mở Q1).
- Khoá một tập test có ít nhất 40 API dương, chia theo nhà cung cấp.
- Chi phí: sàng lọc vài trăm spec (một lượt rẻ); gán nhãn khoảng 100 API dương.
- Phản biện:
  - Tầng giàu của APIs.guru đã cạn: vòng 2 lấy hết 37 nhà cung cấp còn lại (`corpus/sample_specs_field_r2.py:36`,
    `:43-44`). Nguồn ngoài APIs.guru đặt ra câu hỏi về xuất xứ.
  - Bộ sàng lọc cùng họ model có thể mang cùng thiên lệch với người gán.
  - Mẫu làm giàu làm tăng tỉ lệ dương, nên phải đánh trọng số. Nếu không, precision báo ra sẽ cao giả.

**Đ3. Quy trình gán nhãn kiểm được.**
- Đầu ra:
  - Bắt buộc ghi một dòng cho mọi mục, kể cả âm.
  - Thêm script so số dòng với `rows/`, để bỏ sót bị phát hiện bằng máy thay vì bằng lời cam kết (khắc phục Y8).
- Người gán:
  - L2 từ họ model khác, hoặc ít nhất prompt và thứ tự dòng khác.
  - Phân xử do một phiên mới, không biết nhãn nào của ai; hoặc 3 người gán, lấy đa số.
  - Mục không ngã ngũ để riêng và báo độ nhạy, như `w11`.
- Luật gán chốt trước mọi lượt. Nếu đổi luật thì gán lại mọi tập, ít nhất phần trường bị luật mới ảnh hưởng
  (khắc phục Y10).
- Cho người gán thấy mô tả trường, response, tags, scopes; hiện các thứ này bị ẩn (`R1/PROTOCOL.md:36-37`). Nhãn là
  sự thật nền, không cần mù như runtime.
- Báo cáo đồng thuận: kappa theo lớp, đồng thuận dương `2a/(2a+b+c)` (như `w02` §1), và đồng thuận thứ tự cho B
  (khớp đúng; Kendall τ trên toàn thứ tự).
- Chi phí: khoảng 1,5 lần chi phí LLM của một vòng (thêm một người gán) và vài giờ viết script.
- Phản biện:
  - Model khác họ có thể lệch vì văn phong chứ không vì sự thật, làm kappa thấp đi mà không làm nhãn tốt lên.
  - Thêm ngữ cảnh làm nhãn đúng hơn nhưng nới khoảng cách với thứ tên lá biểu diễn được (trần ở Y13).
  - Thu hẹp lớp dương làm ít dương hơn nữa.

**Đ4. Luật rút riêng cho từng danh sách, chọn bằng kiểm chéo nhóm, giữ từ theo độ ổn định.**
- Sinh ứng viên:
  - Tách camelCase trên tên gốc rồi mới hạ chữ.
  - Gộp số ít/số nhiều (`role`/`roles`).
  - Token ngắn (`id`, `uid`, `key`) chỉ dùng khớp nguyên tên và chỉ ở lớp dự phòng.
- Mục tiêu theo vai trò runtime:
  - `roleFieldSignals`: recall trong ứng viên transition, có sàn precision.
  - `ADMIN_FLAG`: đo cả trên chuỗi hay, tức tác dụng phụ ở Y2. Hoặc tách thành hai danh sách nếu được sửa mã
    (xem Q3).
  - C: danh sách có thứ tự, đo bằng nạn nhân top-1.
  - B: điểm thứ bậc học từ các cặp so sánh trong cùng enum, đo bằng hạng của giá trị thấp.
- Chọn siêu tham số (k, ngưỡng) bằng kiểm chéo nhóm theo nhà cung cấp trên train, riêng cho từng danh sách
  (như `w10`), không lấy trung bình chung năm danh sách.
- Giữ một từ khi nó được chọn trong ít nhất khoảng 70% số lần bootstrap nhà cung cấp, và in tần suất cạnh từ đó. Con
  số này chính là "cơ sở dữ liệu" của từ (khắc phục Y3).
- Chỉ triển khai danh sách đã đo. Nếu fit lại trên toàn bộ dữ liệu thì ghi rõ là không có ước lượng held-out
  (khắc phục Y7).
- Chi phí: 1–2 ngày viết script; tính toán không đáng kể.
- Phản biện:
  - Luật linh hoạt hơn dễ khớp quá với khoảng 30 API dương.
  - Lọc theo độ ổn định có thể cho danh sách gần rỗng. Với ngưỡng 0,7 trên dữ liệu hiện có: A-role chỉ còn
    `permission` (0,70; `role` 0,67); A-admin không còn từ nào (`admin` 0,68); C chỉ còn `user` (1,00) (`w08` §2).
  - Mục tiêu riêng từng danh sách làm tăng số lựa chọn của người làm nghiên cứu, nên phải khai trước.

**Đ5. Thống kê đúng với dữ liệu có cụm.**
- Bootstrap theo nhà cung cấp cho mọi CI.
- So sánh ghép đôi ở mức API (McNemar hoặc kiểm định dấu trên API), không ở mức trường.
- Đặt câu hỏi dạng không-kém-hơn, với ngưỡng δ chọn trước, thay cho "khác nhau có ý nghĩa".
- Báo riêng dương và âm.
- Chi phí: thấp.
- Phản biện: với khoảng 20 API dương, gần như mọi kiểm định đều không kết luận được. Ngưỡng δ là lựa chọn chủ quan,
  cần lập luận từ chi phí của một lần thử sai (giới hạn 8 lần thử, `kt:126`).

**Đ6. Phương án lai có luật khai trước (một lựa chọn, không phải khuyến nghị mặc định).**
- Dùng corpus làm bảng chứng cứ cho mọi từ, viết tay cũng như rút được: df+, df−, số nhà cung cấp, tần suất
  bootstrap, kết quả neo.
- Áp một luật thêm/bớt khai trước, ví dụ:
  - bỏ từ nếu df+ = 0 và df− ≥ 10;
  - thêm từ nếu độ ổn định ≥ 0,7 và precision mức op ≥ θ.
- Đo danh sách thu được theo Đ1 và Đ5.
- Chi phí: thấp, dùng lại script của Đ4.
- Phản biện:
  - Trái mục tiêu "mọi từ rút từ corpus".
  - Giữ những từ không có hỗ trợ (`is_admin` xuất hiện 0 lần) có thể bị hội đồng xem là chọn lọc.
  - Luật thêm/bớt phải chốt trước khi nhìn test, nếu không sẽ thành chỉnh theo kết quả.

## 3. Câu hỏi còn mở

- **Q1.** Danh sách cần tổng quát hoá cho quần thể nào: API công khai trên APIs.guru, hay ứng dụng tự host có
  quản lý user/role như các target? Câu trả lời quyết định cách bốc mẫu (Đ2) và cách đọc Y13.
- **Q2.** Tác giả định đưa vào `kt` bản R4 train+dev (đã đo) hay bản gộp (chưa đo, kém hơn ở neo)?
- **Q3.** Có được sửa mã không, chẳng hạn tách hai cách dùng của `ADMIN_FLAG_FIELD_SIGNALS` hay chuẩn hoá số
  nhiều? `R1/PROTOCOL.md:8` ghi "Không sửa mã EvoMaster".
- **Q4.** Ràng buộc "tác giả không tự gán nhãn" có cho phép tác giả *rà soát* một mẫu nhãn hoặc quyết định phân xử
  không, hay rà soát cũng phải do LLM làm?
- **Q5.** Lấy được spec thô không, để kiểm 42 op có vẻ thiếu body (Y15) và Bitbucket/Kubernetes ở khối 028/031?
- **Q6.** Theo các mốc ở `R1/PROTOCOL.md:130`, `:139`, `:144`, rows xong lúc 23:06, gán xong khoảng 23:21: hai
  lượt trên 20.216 trường trong khoảng 15 phút. Ngoài khối 028/031, mọi dòng có được đọc hết không? Có log phiên
  để kiểm không?
- **Q7.** Chỉ số chính và mức chênh chấp nhận được so với danh sách viết tay là gì? Mất `role` ở 3 target neo có
  được coi là thất bại tự động không?
- **Q8.** 44 spec cũ (S100–S214) được chọn thế nào ở `labelling-r2/`, `labelling-r3/`? Các thư mục này không có
  trong gói, mà nhóm này góp 130/201 trường A của train+dev, trong đó 125 từ tầng giàu (`w09` §1).
- **Q9.** Với B (29 enum trên cả ba tập), corpus có bao giờ đủ không? Nếu không, có chấp nhận một nguồn khác cho B
  (tài liệu RBAC, giá trị mặc định của framework), kèm xuất xứ, thay cho rút từ corpus không?
- **Q10.** APIs.guru còn bao nhiêu nhà cung cấp chưa dùng? `apis-guru-list.json` không có trong gói nên tôi không
  tính được trần cho Đ2.
