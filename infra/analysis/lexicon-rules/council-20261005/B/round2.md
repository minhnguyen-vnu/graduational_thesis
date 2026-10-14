# Vòng 2 — chuyên gia B đọc bài chuyên gia A

Cách kiểm: tôi đã chạy lại `peer-work/w01, w02, w03, w04, w06, w07, w08, w09, w10, w11, w12, w13, w14, w15, w16`. Các
script này chỉ in kết quả, không ghi file (đã grep: không có `open(...,'w')`, `json.dump`, `.write`). Script mới của
tôi: `work/s17_peer_checks.py`. Nhãn "Y" và "Đ" theo đánh số trong bài của từng người.

## 1. Đồng ý

- **A-Y1 (đo theo trường, nhưng runtime dùng theo op/API).** Chạy lại `w07` ra đúng số họ báo: chọn nạn nhân trên 24 op
  test, viết tay đúng 14, sai 10; R4 đúng 10, sai 5, không chọn được 9. B_low đứng đầu: viết tay 4/8, R4 1/8. Mô phỏng
  của họ đầy đủ hơn `s07`/`s08` của tôi: có xếp top-8 transition (`kt:517`), có cổng `harvestReducedRoleCandidates`
  (`kt:523-529`, tôi đã đọc lại mã), và có kiểm kiểu đặt được giá trị.
- **A-Y2 (`ADMIN_FLAG` làm thay đổi điểm transition).** `w07` §2 cho 131 op lên 0,6 với `admin`, 279 op với
  `admin, owner`, 1 op với danh sách viết tay. Số 131 khớp với cách đếm độc lập của tôi: 13 + 46 + 5 + 67
  (`s08` §2 vòng 1).
- **A-Y3 (R4 bỏ `role`; danh sách không ổn định).** `w08` §2: danh sách A-role R4 tái hiện đúng trong 1% số lần
  bootstrap, `role` được chọn 67%, danh sách C tái hiện 17%. `w14`: chỉ đổi nguồn nhãn L1/L2 là danh sách đổi 1–3 từ.
  Hướng giống `s06` của tôi.
- **A-Y4 (chọn luật trên dev quá nhỏ).** Đúng như họ nói: dev có A-role 17 dương, trong đó files.com chiếm 9, top-3
  nhà cung cấp chiếm 82% (`w02` §4). R4 thắng R1 hoàn toàn nhờ C (+0,189), còn A-role thì R4 kém hơn (−0,038). Chạy
  lại kiểm chéo nhóm `w10` ra đúng số: A-role R4 0,223, viết tay 0,318; R4 thắng 6/20 phần; R1 0,303, R3 0,298.
- **A-Y5, phần dữ kiện.** perms boolean chiếm 86/161 dương A-role ở train và 24/61 ở test; 92/167 trường A ở train
  nằm trong op không có C (`w09` §4, `w12` §1). Khớp hướng với `s10` của tôi (100/177 ở train+dev).
- **A-Y6.** Khoảng tin cậy (KTC) bootstrap theo cụm gần như trùng `s11` của tôi; ví dụ A-role −0,059 [−0,229; 0,068]
  của họ so với [−0,225; 0,066] của tôi.
- **A-Y7, Y10, Y12, Y14, Y16–Y18.** Đã kiểm số của `w03`, `w13`, `w16` và `merged-lists.json`. Đồng ý.
- **A-Y8 (đầu ra chỉ ghi dòng dương, nên bỏ sót không phân biệt được với âm).** Tôi chưa nêu ý này. Bằng chứng là
  r1 `PROTOCOL.md:83-85`; `w04` cho khối 028/031 có 0 A trên 1.000 trường, các khối khác 11,8. Đồng ý, mức vừa.
- **A-Y11 (B).** Khi cả hai lượt cùng gán role/perms có enum, B trùng 17/19 (`w02` §2). Ý về windows.net
  `userType ∈ {Member, Guest}` (Member là cao, nhưng `member` nằm trong cả hai danh sách B-low) là đúng và đáng nêu.
- **A-Y13.** Đồng ý rằng corpus khác phân phối của target: target bị loại có chủ ý (`corpus/sample_specs_field.py:8-9`),
  và spec cũ tầng giàu góp 125/201 dương A ở train+dev (`w09` §1). Phần "trần F1" xem mục 2.
- **A-Đ1, Đ3, Đ5.** Đồng ý về hướng. Riêng ý "nhãn là sự thật nền nên không cần mù như runtime, cho người gán xem mô
  tả trường và response" tốt hơn đề xuất của tôi.

## 2. Không đồng ý hoặc cần sửa

- **A-Y1, câu "roleLow/High chỉ xếp thứ tự, không lọc" (`kt:976-983, :988-996`): sai một phần.**
  - `harvestElevatedRoleCandidates` chỉ giữ giá trị enum chứa từ cao (`kt:993-996, :1005`), tức là lọc.
  - `isLowPrivRole` còn lọc vai trò hiện tại của nạn nhân lấy từ response GET (`kt:650-653`), và `victimRoleValues`
    dùng `roleFieldSignals` trên response (`kt:1092-1110`). Cả hai bài đều chưa đo cách dùng này.
  - Thiếu ở cả hai bài: khi có `statefulAuthzTransition` khai báo, builder bỏ qua danh sách nạn nhân và vai trò
    (`kt:509`, `:736-741`, `:1345-1361`). Danh sách chỉ có tác dụng khi target không khai báo transition.
- **A-Y1, ví dụ C: thiếu một kết luận quan trọng có ngay trong `w07` §3.** Thêm lớp dự phòng email/id vào R4 thì
  R4+fallback = viết tay = (14, 10, 0) trên test. Nghĩa là chênh lệch ở runtime đến hoàn toàn từ việc bỏ thứ tự
  email→id, không đến từ các từ cụ thể được rút.
- **A-Y5, "cỡ mẫu hiệu dụng khoảng 28 API": là cận dưới, phụ thuộc định nghĩa.** `w12` và `w15` chỉ tính A role/admin,
  bỏ hết perms, kể cả mảng `roles` như neo Airflow (`r2/PROTOCOL.md:82`) mà builder xử lý qua `roleArrays`
  (`kt:1199-1226`). `s17` §1: role/admin cho 28 API; thêm perms không phải boolean cho 42; mọi A cho 45.
- **A-Y15, "42 op thiếu body": phóng đại.** `s17` §2: 27/42 op chỉ khớp nhờ chữ `admin` trong path (fecru
  `admin/repositories-v1/*/reindex`, gamesparks `admin/snapshots` …). Trong 15 op còn lại có vài op vốn chỉ dùng path
  (conjur `PUT /authn/{account}/api_key`, iqualify `/users/{userEmail}/permissions/{permissionName}`). Op nhiều khả năng
  mất trường quyền thật khoảng 11–12 (jira ×3, fecru ×6, bitbucket, n-auth). Số này là suy luận từ danh sách in ra,
  chưa kiểm vì không có spec thô.
- **A-Y9, "ảnh hưởng tới số nhỏ": chỉ đúng với hướng phân xử và chỗ lộ mù.** `w11` chỉ đổi nhãn của test; danh sách vẫn
  rút từ nhãn cuối của train+dev. L1 và L2 cùng họ model, nên lỗi chung của hai lượt không lộ ra. Câu này không nói
  gì về độ đúng của nhãn.
- **A-Y13, trần F1 theo tên lá (C 0,56): là trần ở mức trường, không phải trần ở runtime.** Con số tính theo đa số
  trên chính test. Lúc chạy, sự mơ hồ của `id` được giải bằng vị trí (path trước) và thứ tự tầng: viết tay chọn đúng
  14/24 dù F1 mức trường chỉ 0,083.
- **Câu đầu A-Đ "R4 hơn ở A-admin": chưa có cơ sở.** Test chỉ có 5 dương từ 4 nhà cung cấp, KTC [−0,267; 0,889]
  (A-Y6). Kiểm chéo nhóm `w10` nghiêng về danh sách rút (14/20 phần), nhưng chỉ ở mức trường boolean và chưa trừ tác
  dụng phụ ở A-Y2.
- **A-Đ2, cỡ mẫu 97 API: thô.** Con số tính cho một tỉ lệ đơn với p=0,5 (`w15`). So sánh hai danh sách là ghép đôi, nên
  cỡ mẫu cần thiết phụ thuộc số cặp lệch. Tỉ lệ 14–23% đến từ mẫu có tầng giàu; tầng ngẫu nhiên thấp hơn (dev
  ngẫu nhiên chỉ 1/22 spec có A, `w09` §1).
- **A-Đ6, "bỏ từ nếu df+ = 0 và df− ≥ 10": không nên áp cho từ viết tay khi corpus đã loại target.** Đó chính là
  điều họ nêu ở Y13. Muốn bỏ một từ thì cần bằng chứng âm trong quần thể đích, hoặc trong op T, không phải df− trên
  toàn corpus.
- **Nhỏ.**
  - A-Y4 ghi P(R4 thắng) = 0,69, nhưng chạy lại `w08` §3 ra 0,718. Không đổi kết luận.
  - A-Q6 (15 phút cho hai lượt): r1 `PROTOCOL.md:146` cho thấy các mốc giờ đã phải sửa và lấy từ mtime. mtime là lúc
    ghi file, nên không suy ra được thời gian đọc. Câu hỏi hợp lệ nhưng bằng chứng yếu.

## 3. Tự sửa (round1.md)

- **Y4 (B): rút lại câu "mô phỏng: B_low đứng đầu 4/8 (viết tay) và 5/8 (R4)".** `s08` bỏ qua cổng nhận trường role.
  Có cổng thì R4 chỉ đúng 1/8, vì 7/8 op không có ứng viên (`w07` §5). Đây là bằng chứng chống R4, không phải "không
  phân biệt được".
- **Y4: sửa câu "hai lượt trùng B_low 17/27, B_high 20/27".** Mẫu số 27 gồm cả trường mà chỉ một lượt gán A. Khi cả
  hai lượt cùng gán A thì B trùng 17/19, và chỗ lệch thứ tự B thực chất chỉ có apple.com (`w02` §2). Lệch B chủ yếu là
  hệ quả của lệch A.
- **Y1: làm dịu kết luận "R4 kém hơn ở đơn vị op".** `s07` của tôi chỉ đo recall trên op T. Ở mức op trên toàn test,
  F1 tìm trường role gần như hoà: viết tay P 0,31, R 0,43, F1 0,36; R4 P 0,59, R 0,27, F1 0,37. Ở mức API, viết tay
  chọn đúng op A đầu tiên 9/21 nhưng có 8 API báo nhầm; R4 là 6/21 và 3 (`w07` §1, §4). Đúng hơn phải nói: R4 đánh đổi
  recall lấy precision. Chiều so sánh chỉ đảo rõ ở C và B. Số chọn nạn nhân của `s07` (10/6/8) được thay bằng số của
  `w07` (10/5/9), vì `w07` có kiểm kiểu.
- **Y9: hạ thành suy luận.** Câu "phần cũ không phải mẫu ngẫu nhiên" chưa kiểm được, vì gói không có `labelling-r2/`
  và `labelling-r3/`. Bằng chứng gián tiếp: mật độ A ở spec cũ tầng giàu là 125/4.298 trường, ở spec mới tầng giàu là
  30/4.773, gấp khoảng 4,6 lần (`w09` §1).
- **Đ2: số sản lượng "~2,5 lần" có tính vòng.** Con số dùng regex path chứa `users|roles|permissions`, tức chính những
  từ cần rút. Phải coi là ước lượng lạc quan.
- **Bổ sung những điểm tôi đã bỏ sót:**
  - đầu ra chỉ ghi dòng dương (A-Y8);
  - top-8 transition và cổng viable (`kt:517-531`);
  - lọc vai trò hiện tại (`kt:650-653`);
  - đường khai báo transition bỏ qua danh sách (`kt:509`).

## 4. Đề xuất hợp nhất (theo thứ tự làm)

**B0. Khai trước, trước mọi số mới.**
- Chốt các quyết định sau:
  - quần thể đích (A-Q1);
  - chỉ số chính cho từng danh sách: mức API cho transition và role, nạn nhân top-1, hạng B_low, số op bị đổi điểm
    transition;
  - ngưỡng không-kém-hơn δ;
  - danh sách nào sẽ vào mã;
  - các luật cấu trúc được giữ (`id` dự phòng, thứ tự tầng, cổng boolean);
  - có được tách hai cách dùng `ADMIN_FLAG` không.
- Chi phí: vài giờ.
- Phản biện: chốt sớm có thể khoá nhầm chỉ số. Nhưng không chốt thì mọi lựa chọn sau đều là chỉnh theo kết quả, như
  việc chọn R0–R4 sau khi đã xem dev.

**B1. Bộ mô phỏng runtime và đo lại trên nhãn sẵn có.**
- Cách làm:
  - Lấy `w07` làm nền. Thêm phần lọc vai trò hiện tại (`kt:650-653`), bộ lọc B-high (`kt:993-996`), và cờ "bỏ qua khi
    có khai báo".
  - Đo ở mức API (chính) và mức op (phụ). KTC bootstrap theo nhà cung cấp; báo riêng dương và âm.
  - Đối chiếu bộ mô phỏng với log debug thật của builder trên 6 target (`kt:524-527`, `:653`) để kiểm giả định
    tên gene.
- Chi phí: 2–3 ngày.
- Phản biện:
  - n nhỏ: 21 API test có A; 13–18 API có op chứa cả A và C.
  - Có nguy cơ tối ưu theo bộ mô phỏng.
  - Kết quả gắn với phiên bản builder hiện tại.

**B2. Luật rút mới, chạy lại trên nhãn sẵn có.**
- Sửa ứng viên:
  - tách camelCase trên tên gốc;
  - gộp số ít/số nhiều;
  - token ngắn (`id`, `uid`) chỉ dùng ở lớp dự phòng, khớp nguyên tên.
- Đếm mỗi cặp (nhà cung cấp, tên lá) một lần. Ứng viên gồm token từ corpus cộng từ viết tay; cả hai qua cùng một luật.
- Giữ từ khi thoả cả ba điều kiện:
  - ít nhất 3 nhà cung cấp dương trong op T;
  - precision theo nhà cung cấp vượt θ;
  - tần suất bootstrap ≥ 0,7.
- Mỗi từ in kèm bảng bằng chứng.
- Theo từng danh sách:
  - C: giữ ba tầng, `id` là luật cấu trúc.
  - `ADMIN_FLAG` cho `transitionScore`: đo riêng số op bị đổi điểm. Nếu không được sửa mã thì giữ bản viết tay.
  - B: báo "corpus không đủ" cho tới khi có ít nhất 15 enum từ 10 nhà cung cấp; danh sách B viết tay chỉ được đo bằng
    hạng.
- Chọn k và θ bằng kiểm chéo nhóm trên train, riêng cho từng danh sách.
- Chi phí: 1–2 ngày.
- Phản biện:
  - Ngưỡng là tùy ý.
  - Với dữ liệu hiện có, danh sách có thể chỉ còn vài từ: `role`, `permission`, `user` (`s16`, A-Đ4).
  - Đưa từ viết tay vào làm ứng viên có thể bị xem là neo theo danh sách cũ.

**B3. Gán nhãn lại có mục tiêu, chỉ làm nếu B1–B2 cho KTC quá rộng để quyết định.**
- Bốc mẫu:
  - LLM sàng lọc API chỉ dựa vào `info.description`, tags và path (không dùng tên trường).
  - Lấy hết tầng cao, 20% tầng thấp, giữ trọng số.
  - Thêm tầng ứng dụng tự host có RBAC (không trùng target) nếu B0 chọn quần thể đó.
  - Khoá một tập test có ít nhất 40 API dương.
- Gán nhãn:
  - Tầng 1 ở mức op. Tầng 2 chỉ cho op dương, gồm nạn nhân, trường vai trò, toàn bộ thứ tự enum.
  - Nhãn phụ tách riêng: định nghĩa role, cờ khả năng, credential, chủ thể phi-user.
  - Ghi mọi dòng, kể cả âm, và có script đối chiếu với `rows/`.
  - Người gán xem mô tả trường, tên schema, enum đầy đủ.
  - L2 khác prompt và thứ tự dòng (khác họ model nếu được).
  - Phân xử bởi một phiên mới, mù nguồn, xét từng dòng.
  - Gán lại cả train và dev theo luật mới.
- Chi phí: khoảng một vòng đọc LLM cho tầng 1 trên spec mới, cộng vài ngày thu thập spec ngoài APIs.guru.
- Phản biện:
  - Bộ sàng lọc cùng họ model có thể mang cùng thiên lệch.
  - Trọng số chỉ đúng khi biết xác suất chọn.
  - Nguồn mới có xuất xứ kém đồng nhất.

**B4. Kiểm độ đúng của nhãn, làm song song với B3.**
- Cách làm:
  - Một lượt gán thứ ba trên mẫu phân tầng: mọi dương, các âm có tên rõ nghĩa (`s05`), và 500 âm ngẫu nhiên.
  - Chuẩn từ mã nguồn cho 5–10 API mã mở trong corpus (keycloak, gitea, gitlab, superset, apicurio): agent trích
    file:dòng làm bằng chứng.
- Chi phí: vừa.
- Phản biện:
  - Các họ model có thể chung thiên lệch.
  - Chuẩn từ mã lệch về ứng dụng mã mở.
  - Vẫn không có nhãn của người (A-Q4).

**B5. Cổng cuối.**
- Cách làm: chạy EvoMaster không khai báo transition, với các phiên bản danh sách viết tay, rút, và hợp; trên 6 target
  cộng 2–4 API mã mở chưa dùng; ít nhất 10 seed. Kết luận theo δ đã khai ở B0.
- Chi phí: cao.
- Phản biện: target không phải held-out; ít target; EvoMaster không tất định.

## 5. Bất đồng còn lại

- Cỡ mẫu hiệu dụng: 28–45 API tuỳ cách tính perms, không phải "khoảng 28".
- B: không rút từ corpus ở cỡ hiện tại. A-Đ4 đề xuất học thứ bậc từ các cặp so sánh trên 29 enum; tôi cho là dễ khớp quá.
- Từ viết tay nên là ứng viên mặc định, qua cùng luật với từ rút (A coi đây là phương án tuỳ chọn, Đ6).
- Bỏ một từ viết tay cần bằng chứng âm trong op T hoặc quần thể đích, không phải df− trên toàn corpus (A-Đ6).
- Độ đúng của nhãn (A-Y9) là điểm yếu mức vừa; độ nhạy L1/L2 không thay được kiểm độc lập.
- A-Y15 nên ghi khoảng 11–12 op đáng ngờ, không phải 42.
- "R4 hơn ở A-admin" chưa đủ cơ sở để nêu ở phần tổng kết.
