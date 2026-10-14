# Vòng 1 — phản biện phiên gán nhãn và rút từ (chuyên gia B)

Cách kiểm: mọi số tự tính nằm trong `work/` (chạy `cd work && python3 sNN_*.py`). `work/lib.py` nạp dữ liệu chỉ đọc
(không gọi `build()`/`r2_fields()` vì hai hàm đó ghi đè `final.csv`) và dùng lại đúng hàm `tokens/docs/classify/prf/
candidates/select` của tác giả. `s02` tái lập đúng danh sách và số test trong `results.json` của hai vòng.
Viết tắt: "op T" = operation ghi có ít nhất một trường A (`role`/`perms`/`admin`) **và** một trường C — dạng
operation mà builder cần (định nghĩa của tôi, xem câu hỏi 12). "R4 cuối" = danh sách trong `r2/lists/`.

## 1. Điểm yếu

**Y1. Đơn vị đo không phải đơn vị builder dùng — cao.**
- Là gì: hai vòng đo P/R/F1 trên từng lần xuất hiện của trường, gộp mọi trường của mọi op ghi (r1 `PROTOCOL.md:110-112`,
  `derive_eval.py:142-150`). Lúc chạy, danh sách chỉ được dùng bên trong một op transition đã chọn: cần ít nhất một
  trường khớp `roleFieldSignals` mới có ứng viên (`RestSecurityBuilder.kt:958-967`); mọi trường khớp đều bị ghi đè
  (`:1290-1316`); trường nạn nhân chọn theo thứ tự path→body, specific→email→`id` (`:1053-1077`).
- Ví dụ: 30.437 trường × 2 lượt = 60.874 nhãn trường chỉ cho 75 op T; test vòng 2 có 24 op T từ 18 nhà cung cấp
  (`s14`). Trên 24 op đó (`s07`, mô phỏng): R4 cuối bắt đúng trường A ở 6/24 op, danh sách viết tay 10/24; chọn đúng
  trường nạn nhân ở lượt đầu: R4 10/24, viết tay 14/24. Ngược lại, ở F1 mức trường thì R4 hơn ở C (0,224 so với 0,083),
  vì danh sách viết tay bị phạt cho chữ `id`: 1.869/2.060 cặp lệch của McNemar C chỉ do `id` (`s09` §4), trong khi
  lúc chạy `id` chỉ được thử sau cùng.
- Ảnh hưởng: kết luận "rút tốt hơn hay kém hơn" đổi chiều theo đơn vị đo. Số hiện có không trả lời câu hỏi lúc chạy.
- Giới hạn: `s07` là suy luận có mô phỏng. Tôi giả định tên gene = tên lá và không chạy EvoMaster.

**Y2. Danh sách cuối thiếu từ cốt lõi và không ổn định — cao.**
- A-role cuối = `approve, permission, privilege, restrict, roles`. `"roles"` không phải chuỗi con của `"role"`, nên trường
  `role` của reports-api, vampi và pyLoad không khớp (`r2/anchor.json`). `role` có 26 dương từ 12 nhà cung cấp
  (`r2/lists/candidates-A-role.csv:43`) nhưng chỉ xếp thứ 7. `privilege` (5 dương, 4 trong số đó từ id4i.de) đứng
  đầu (`:2`).
- Bootstrap theo nhà cung cấp trên train+dev, 200 lần (`s06` §2): `role` vào R4 ở 73% số lần, `roles` 20%, `approve` 31%,
  `privilege` 38,5%; với C, `clientid` 36%. Danh sách cuối là một kết quả ít khả năng xảy ra.
- Lúc rút trên train (lúc chọn luật), R4 A-role vẫn có `role` (`select.json`). Thêm dev vào thì mất `role`.
  `merged-lists.json` (R4 trên cả ba tập) đổi hẳn C thành `collaborator, membershipid, principalid, useremail, userid`;
  danh sách này không khớp trường nạn nhân nào của 6 target (`s09` §5).
- C cuối không có `email` và không thể có `id`, nên bamf (`email`) và artifact-keeper (`id`) trượt (`anchor.json`).

**Y3. Luật được chọn dựa chủ yếu vào nhiễu — cao.**
- Tiêu chí là F1 trung bình của 5 danh sách, mỗi danh sách nặng như nhau (`select_rule.py:16`). Trên dev, A-admin chỉ có
  2 dương từ 1 nhà cung cấp, F1 bằng 0,8 hoặc 0, tức chiếm 0,16 của trung bình. B-low và B-high có F1 như nhau ở cả 5
  luật, nên không phân biệt được luật nào (`s13`).
- Bootstrap trên dev (`s06` §1): R4 đứng đầu ở 73% số lần; hiệu R4−R1 có KTC95% [−0,038; 0,133], P(R4≤R1)=0,22. Trên test
  (`exploratory.json`, hậu kiểm): R1 = R3 = 0,451 > R4 0,431 > viết tay 0,413.

**Y4. B quá ít dữ liệu và đo sai dạng — cao (riêng B).**
- B có thứ tự: train 16 trường (9 enum khác nhau, 5 nhà cung cấp, riêng configcat 6/16), dev 5, test 8 (5 enum)
  (`s03` §3). Chỉ 4 ứng viên thấp và 2 ứng viên cao qua P1 (`s06` §3).
- Vòng 1, hai lượt trùng B_low 17/27, trùng B_high 20/27 (`s12`). Với apple.com `roles`, L1 gán READ_ONLY/ADMIN, L2 gán
  `unordered`, còn phân xử chọn giá trị thứ ba ACCOUNT_HOLDER (`r1/adjudicate.py:28`). Enum ấy có đúng 12 giá trị, đúng
  mức cắt `MAX_ENUM` (`extract_fields.py:11`, `s09` §3), nên "cao nhất" được chọn trên một enum có thể đã bị cắt.
- Lúc chạy, danh sách B dùng để xếp hạng giá trị của mọi enum trong op (`:970-983`) và trong toàn API (`:988-996`). Hai
  vòng lại chỉ đo nhị phân trên enum của trường role. Mô phỏng thứ hạng (`s08`) cho kết quả trên test: B_low đứng đầu ở
  4/8 trường (viết tay) và 5/8 (R4); B_high 3/8 và 2/8. Bootstrap theo cụm cho KTC F1 của B rộng gần [0; 1] (`s11`).
- Ảnh hưởng: `member, none, only, read` / `admin, full` không có cơ sở. Luật "corpus không đủ" (r1 §7) chỉ kích hoạt khi
  có 0 từ qua P1, không kích hoạt khi n rất nhỏ.

**Y5. Phạm vi nhãn rộng hơn nhu cầu lúc chạy — vừa đến cao.**
- A bao gồm cả định nghĩa role hay nhóm quyền (r2 `PROTOCOL.md:38`) và cài đặt mặc định. C bao gồm cả API key, client,
  token (r2 `:36`). Trong khi đó nạn nhân lúc chạy là một tài khoản user (`:1053-1058`, `:1154-1158`).
- Có 100/177 dương A-role ở train+dev nằm trong op không có C; riêng configcat (định nghĩa nhóm quyền,
  `cancreateorupdate*`) chiếm 47 (`s10`). Một số từ R0 đến chủ yếu từ nhóm này: `create` 18/21, `delete` 10/13, `members` 11/13.
- Dương C nằm trên path của chủ thể không phải người dùng: 18% (train+dev), 22% (test) (`s09` §2). `clientid` đến từ
  `apikeys/{clientId}` của maif.local (5/6), `privilege` từ `apikeys/{key}/privileges` của id4i (4/5) (`s04`). `approve`
  đến từ cờ năng lực (`can_approve_pull_request_reviews`, `isTimesheetApprover`), không phải tên trường vai trò.

**Y6. Luật rút làm mất cấu trúc mà builder dựa vào — cao nếu thay `ADMIN_FLAG_FIELD_SIGNALS`, vừa với phần còn lại.**
- `MIN_LEN=4` (`derive_eval.py:6,40`) khiến `id`, `uid`, `is_admin` không thể thành từ. Có 32/193 dương C (train+dev) và
  24/127 (test) có tên lá không chứa token nào dài từ 4 ký tự, nên không danh sách rút nào bắt được (`s04`).
- Danh sách C gộp `:414` và `:415`, nên mất thứ tự specific→email→`id` (`:1061-1062`).
- `ADMIN_FLAG_FIELD_SIGNALS` còn được dùng trong `transitionScore` (`:104-112`, điểm 0,6, cao hơn mọi điểm path trong
  lexicon; max 0,5455). Nếu thay bằng `admin`, 67 op không có A trong 10 spec test (fecru.local 30 op) và 46 op trong 9
  spec train+dev sẽ được điểm 0,6 (`s08` §2, `s09` §6; hay được xấp xỉ bằng path cộng tên trường body cấp 1). Hai vòng
  chỉ đo trên trường boolean (`derive_eval.py:92`).
- Khi đo, B-low rút được phân loại bằng `any(w in v)` (`derive_eval.py:136-139`), trong khi lúc chạy là "chứa từ thấp
  và không chứa từ cao" (`:711`).
- Trường con của mảng quyền (`roles[].id`, `.name`, `.type`) được gán dương theo tên lá: có 14 trường như vậy ở
  train+dev (`s04`). Lúc chạy, mảng object được nhận qua tên cha (`:1199-1206`, `:1294-1303`).

**Y7. Cách đếm và điểm thiên về nhà cung cấp lặp nhiều — vừa.**
- Đếm theo lần xuất hiện, không theo nhà cung cấp: configcat chiếm 48/177 dương A-role ở train+dev (27%) (`s03` §2).
- Điểm = precision làm mịn × ncc/(ncc+1) (`derive_eval.py:126`). Hệ số này chỉ là 0,67 với 2 nhà cung cấp và 0,92 với 12,
  nên precision áp đảo: `privilege` (2 nhà cung cấp) được 0,571, `role` (12 nhà cung cấp) chỉ 0,346.
- P2 của R0 là precision ≥ 2× tỉ lệ nền (≈0,018), nên `type`, `create`, `default` đều lọt (`r2/results.json`, mục `r0`).
- Precision tính trên mọi op ghi. Âm của `role` gồm `clientrole` (keycloak, 11), `role` của network-service-config, v.v.
  (`s04`), là các ngữ cảnh builder không gặp sau bước chọn transition.

**Y8. Chưa đo độ đúng của nhãn, chỉ đo độ nhất quán giữa hai model cùng nhà cung cấp — vừa.**
- Kappa A/C: vòng 1 là 0,774/0,803, vòng 2 là 0,890/0,801 (`s02`, khớp `kappa-raw.json`). Cả hai lượt cùng là
  Anthropic (r1 `PROTOCOL.md:79`).
- Phân xử do chính phiên L1 làm: vòng 1 có 108 theo L1, 51 theo L2, 2 khác cả hai; vòng 2 có 44/28. Phân xử theo luật gán
  cho từng dải chỉ số, lý do là câu mẫu (`r1/adjudicate.py:5-26`), không có bằng chứng riêng từng dòng.
- Trường cả hai lượt cùng gán âm thì không ai kiểm. Có 26 trường (vòng 1) và 12 (vòng 2) với tên lá rất rõ nghĩa
  (`role`, `roles`, `permissions`, `scopes`, `isAdmin`…) mà nhãn cuối âm. Nhiều trường trong số đó mơ hồ thật, ví dụ
  appveyor `roleAces[].isAdmin`, n-auth `/servers/{id}/permissions/{roleid}` (`s05`).
- Khối 028 và 031 chỉ được đọc qua grep (r1 `PROTOCOL.md:148-150`): 3.243 trường, 0 A (`s05`). L1 tự đặt quy ước C riêng
  (`:151-153`). Vòng 2 lộ mù ở khối 020–022 (r2 `PROTOCOL.md:110-112`).

**Y9. Quy ước nhãn và tỉ lệ nền khác nhau giữa train, dev và test — vừa.**
- Train và dev giữ nhãn vòng 1, không gán lại; test vòng 2 dùng luật mới (r2 `PROTOCOL.md:18, 33-44`).
- Tỉ lệ A: phần cũ 2,36%, train mới 0,50%, dev 0,29%, test 0,65%. Tỉ lệ C: 1,95%, 0,62%, 0,58%, 1,24% (`s09` §1). Phần cũ là
  các op đã chọn ở những vòng gán mức op trước đó (nhãn cũ: 51 R, 669 N, …), không phải mẫu ngẫu nhiên.
- Ảnh hưởng: ngưỡng tương đối với tỉ lệ nền (R0) và precision không chuyển được từ tập này sang tập khác.

**Y10. Kiểm định thống kê coi các trường là độc lập — vừa.**
- McNemar tính trên từng trường (`evaluate.py:78-92`). Với A-role, p=0,0026: R4 đúng hơn ở 36 trường, nhưng cả 36 đều là
  âm. Xét riêng dương thì danh sách viết tay đúng hơn ở 10 trường, R4 ở 0 (`exploratory.json`, `split_mcnemar`).
  Bootstrap theo nhà cung cấp cho hiệu F1 A-role (R4 − viết tay) = −0,059, KTC [−0,225; 0,066] (`s11`).

**Y11. Người gán thiếu ngữ cảnh — thấp đến vừa.**
- Người gán không thấy mô tả từng trường, header, operationId, tên schema (r1 `PROTOCOL.md:36`); enum bị cắt ở 12 giá
  trị, độ sâu tối đa 3, tối đa 80 trường một op (`extract_fields.py:9-11`). Ví dụ: Bitbucket `PUT …/permissions-config/
  groups/{group_slug}` chỉ nêu giá trị quyền trong phần mô tả, body không trích được (`r1/rows/chunk-028.txt:1598-1603`).

**Y12. Protocol và code khác nhau ở bước tách camelCase — thấp.**
- r1 `PROTOCOL.md:101` ghi "tách camelCase", nhưng `leaf()` hạ chữ thường trước khi tách (`derive_eval.py:31-42`), nên
  `accessType` thành một token `accesstype` (`s03` §1); 94/177 dương A-role có tên camelCase. Nếu sửa: A-role R4
  không đổi, C mất `clientid` (`s15`). Tác động lên danh sách nhỏ, nhưng là chỗ dễ bị hỏi trước hội đồng.

**Y13. Có sản phẩm hậu kiểm nhưng chưa khai trước danh sách nào sẽ vào mã — vừa.**
- `exploratory.json` và `merged-lists.json` được làm sau khi đã xem test (r2 `PROTOCOL.md:114-116`). Nếu dùng danh sách
  merged thì không còn tập đo nào, và C merged không khớp trường nạn nhân nào của các target (Y2).

Để trung lập: danh sách viết tay cũng có những từ không có chỗ dựa trong corpus. Trong op T của train+dev, `plan`,
`tier`, `subject`, `principal` có 0 nhà cung cấp dương (`s16`). `is_admin` và các biến thể có 0 dương ở train+dev
(`results.json`, `hard_word_support`). Lợi thế của danh sách viết tay trên neo không phải bằng chứng held-out
(r2 `PROTOCOL.md:74`).

## 2. Đề xuất

Thứ tự gợi ý: Đ1 và Đ4 trước (dùng nhãn sẵn có, rẻ). Nếu KTC vẫn quá rộng thì làm Đ3 và Đ2. Đ5 làm song song. Đ6 dùng cho
kết luận cuối. Không giả định trước kết quả: Đ1 và Đ4 có thể cho thấy danh sách viết tay, danh sách rút, hoặc hợp của
hai danh sách là tốt nhất.

**Đ1. Đo lại theo đơn vị lúc chạy, trên nhãn sẵn có.**
- Cách làm: lấy tập op T từ nhãn hiện có (51 op ở train+dev, 24 ở test). Viết bộ mô phỏng sát các hàm của builder
  (`:958-983`, `:986-1006`, `:1053-1077`, `:1255-1265`, `:1290-1316`, `:104-112`). Đo cho mỗi op: có bắt đúng trường
  vai trò không; số trường không phải vai trò bị ghi đè; trường nạn nhân có được chọn đúng ở lượt đầu không; B_low và
  B_high có đứng đầu không; và số lần kích hoạt nhầm `transitionScore` ở op không phải T. Gộp theo nhà cung cấp, báo KTC
  bằng bootstrap theo cụm. `s07` và `s08` là bản nháp của bộ mô phỏng này.
- Chi phí: 1–2 ngày viết script, không cần nhãn mới.
- Phản biện: n nhỏ (24 op, 18 nhà cung cấp) nên KTC rộng, có thể không tách được các danh sách. Mô phỏng dựa trên giả định
  về tên và kiểu gene, cần đối chiếu với mã EvoMaster. Thước đo gắn với phiên bản builder hiện tại, đổi builder là phải đo lại.

**Đ2. Gán nhãn hai tầng ở mức operation, bốc mẫu có mục tiêu và có trọng số.**
- Bốc mẫu: tầng giàu của APIs.guru đã hết (r2 `PROTOCOL.md:24`), nên cần thêm nguồn spec mới (ứng dụng tự host giống
  target, benchmark REST). Phân tầng theo khả năng "API có quản lý user". Khả năng này do LLM chấm từ `info.description`
  và danh sách path, không dùng từ của danh sách để tránh vòng lặp. Lấy hết tầng cao, lấy ngẫu nhiên khoảng 20% tầng
  thấp, rồi ước lượng có trọng số nghịch đảo xác suất chọn.
- Tầng 1, mức op, một lượt: LLM trả lời có cấu trúc: op có đổi role, quyền, cờ admin hay trạng thái của một user đã tồn
  tại không; trường nào chỉ user; trường nào mang vai trò; thứ tự đầy đủ của enum. Đầu vào thêm mô tả trường, tên schema
  và enum không cắt.
- Tầng 2: gán hai lượt mọi trường của op T, cộng khoảng 5% op không phải T chọn ngẫu nhiên để ước lượng op T bị bỏ sót.
- Mục tiêu: ít nhất 100 op T từ ít nhất 40 nhà cung cấp trên tập test (hiện có 24 op, 18 nhà cung cấp). Lọc path thô ở
  test vòng 2 giữ 30/92 spec nhưng chứa 17/21 spec có A (`s09` §8), tức sản lượng tăng khoảng 2,5 lần.
- Chi phí ước lượng (suy luận): tầng 1 đọc khối lượng chữ tương đương một lượt của vòng hiện tại (hiện là 1,17 MB +
  0,68 MB văn bản đầu vào mỗi lượt); tầng 2 nhỏ. Nếu nguồn ngoài APIs.guru cần thu thập tay thì tốn thêm vài ngày.
- Phản biện: bước sàng lọc bằng LLM có thể bỏ sót đều đặn những API đặt tên lạ, và danh sách rút sẽ thừa hưởng thiên lệch
  đó. Trọng số chỉ đúng khi biết xác suất chọn. Thêm nguồn thì dữ liệu kém đồng nhất hơn. Nhãn vẫn do LLM gán.

**Đ3. Định nghĩa nhãn theo vai trò lúc chạy; nhãn cũ giữ làm tầng phụ.**
- Cách làm: tách A thành A-gán (đặt vai trò cho một chủ thể đã tồn tại trong op này), A-định-nghĩa và A-credential.
  Tách C thành C-user và C-phi-user. Ghi thêm "tên builder sẽ so" (với `roles[].id` là tên mảng cha). Chỉ rút từ A-gán
  và C-user. Các loại còn lại đưa vào làm âm, hoặc loại khỏi phép tính và ghi rõ là đã loại.
- Chi phí: gán lại khoảng 570 trường dương (252 A + 320 C, `s09` §1) và op chứa chúng, hai lượt; nhỏ so với một vòng.
- Phản biện: số dương còn ít hơn (77 trường A trong op T ở train+dev, 27 nhà cung cấp), nên ước lượng nhiễu hơn. Định
  nghĩa có nguy cơ bị may đo theo builder hiện tại.

**Đ4. Luật rút minh bạch, đếm theo nhà cung cấp, giữ cấu trúc, khai trước.**
- Ứng viên: token tách camelCase trên tên gốc (sửa Y12), cộng các từ viết tay. Như vậy từ viết tay cũng phải qua kiểm,
  không được mặc định giữ.
- Bằng chứng mỗi từ (ra một bảng): số nhà cung cấp có dương trong op T, số nhà cung cấp có âm trong op T, ví dụ cụ thể;
  mỗi cặp (nhà cung cấp, tên lá) chỉ đếm một lần.
- Luật giữ từ (khai trước): ít nhất 3 nhà cung cấp dương trong op T của train; precision theo nhà cung cấp vượt một ngưỡng
  khai trước; có mặt ở ít nhất 80% số lần bootstrap. Báo riêng ba nhóm: "đủ bằng chứng", "không có bằng chứng" và "bị dữ
  liệu bác bỏ".
- Giữ cấu trúc: C ba tầng; `id` là luật dự phòng ngoài từ vựng; danh sách admin cho `transitionScore` tách riêng và được đo
  bằng số lần kích hoạt nhầm. B: báo "corpus không đủ" khi dưới một ngưỡng khai trước (ví dụ 15 enum từ 10 nhà cung cấp).
- Tính khả thi trên dữ liệu hiện có (`s16`, chỉ train+dev): trong op T, `role` có 10 nhà cung cấp dương, `roles` 4,
  `permission` 3, `type` 4 nhưng 6 nhà cung cấp có âm. Với C: `user` 14, `id` 20 (21 nhà cung cấp có âm), `userid` và
  `user_id` mỗi từ 5, `email` 3.
- Chọn giữa các phương án: dùng thước đo Đ1 trên dev cùng KTC theo cụm; nếu hoà thì chọn danh sách ngắn hơn.
- Chi phí: 1–2 ngày viết script.
- Phản biện: ngưỡng 3 nhà cung cấp và 80% là tùy ý. Với dữ liệu hiện có, danh sách sẽ co lại còn vài từ. Đưa từ viết tay
  vào làm ứng viên có thể bị xem là neo theo danh sách cũ. Tiêu chí bootstrap thêm một lớp khó giải thích.

**Đ5. Kiểm độ đúng của nhãn mà tác giả không phải gán.**
- Cách làm:
  - (a) Một model khác nhà cung cấp gán lại một mẫu phân tầng: mọi dương, mọi âm có tên rõ nghĩa (Y8), và 500 âm ngẫu
    nhiên. Báo mức đồng ý theo từng tầng.
  - (b) Phân xử bởi một phiên mới, không biết nhãn nào của L1 hay L2 (đảo thứ tự ngẫu nhiên), xét từng dòng và trích bằng chứng.
  - (c) Lấy chuẩn từ mã nguồn của API mã mở có trong corpus hoặc target (keycloak, gitea, gitlab, superset, apicurio…):
    một agent đọc DTO và controller, trích file:dòng, so với nhãn để ước lượng precision và recall của nhãn.
  - (d) Đọc trọn khối 028 và 031.
- Chi phí: (a) khoảng 1,5 nghìn trường, một lượt; (b) khoảng 230 dòng lệch; (c) 1–3 giờ agent mỗi API, 5–10 API;
  (d) 2 khối.
- Phản biện: các họ model có thể chung dữ liệu huấn luyện và thiên lệch. Chuẩn từ mã chỉ có ở API mã mở, nên lệch về ứng
  dụng tự host. Cách này vẫn không có nhãn của người, và tốn thêm chi phí cho nhà cung cấp model thứ hai.

**Đ6. Đo xuôi dòng trên target chạy được (ablation).**
- Cách làm: chạy builder với từng biến thể danh sách (viết tay, rút, hợp) trên 6 target cộng 2–4 API mã mở chạy được bằng
  docker và chưa từng dùng để viết danh sách. Ghi lại: có tìm được transition, có đặt đúng nạn nhân, có hạ quyền được, có
  khôi phục quyền được, oracle 970 có báo. Mỗi cấu hình chạy ít nhất 10 seed.
- Chi phí: cao, khoảng 10 target × 3 biến thể × 10 seed × thời gian một lần chạy.
- Phản biện: 6 target đã định hình danh sách viết tay nên không phải held-out. Số target nhỏ. EvoMaster không tất định.
  Kết quả còn phụ thuộc các phần khác như lexicon transition và cấu hình xác thực.

## 3. Câu hỏi còn mở

1. Mục tiêu là danh sách tốt cho builder hiện tại (đo ở mức op) hay một bộ từ vựng chung (đo ở mức trường)?
2. Quần thể đích là SaaS trên APIs.guru hay ứng dụng tự host giống các target? Tầng giàu của APIs.guru đã hết.
3. Hội đồng cần "mỗi từ có bằng chứng" hay "không kém danh sách viết tay trên target"? Hai yêu cầu này có thể xung đột,
   như trường hợp `role` có bằng chứng nhưng bị R4 loại.
4. Có được giữ các luật cấu trúc ngoài từ vựng không (`id` dự phòng, thứ tự ưu tiên, cổng kiểu boolean)?
5. Từ viết tay có được đưa vào làm ứng viên không?
6. Trong EvoMaster, tên gene của trường lồng, của phần tử mảng và của gene gốc body là gì? Nếu gene gốc mang tên schema
   (ví dụ `RoleUpdateRequest`) thì danh sách cũng khớp tên schema, mà phần trích corpus không có tên schema. Chưa kiểm,
   vì gói không có mã EvoMaster.
7. Có được dùng model của nhà cung cấp khác không (chi phí, chính sách dữ liệu)?
8. Spec thô, `corpus/extract_ops.py`, `apis-guru-list.json`, `labelling-r2/`, `labelling-r3/` không có trong gói, nên
   không tái lập được bước trích trường. Các file này có được lưu trữ không?
9. Danh sách nào sẽ đưa vào mã: bản cuối (train+dev) hay bản merged (cả ba tập)?
10. Builder không dùng A-active (r1 `PROTOCOL.md:96`). Có cần tiếp tục gán nhãn này không?
11. APIs.guru còn bao nhiêu nhà cung cấp chưa dùng ở tầng ngẫu nhiên?
12. Định nghĩa op T của tôi (có A và C) có khớp ý tác giả không? Nó bỏ qua transition mà nạn nhân là chính người gọi
    hoặc nằm trong header.
