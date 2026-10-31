# Thiết kế gán nhãn lại — bản nháp hợp nhất, 2026-10-31

Bản kế hoạch user đã duyệt ngày 2026-11-01, chưa khoá, chưa gán dòng nào. Bước kế tiếp: soạn phiếu để user duyệt. Hai phiên
Claude thiết kế độc lập rồi phản biện nhau theo yêu cầu của user. User yêu cầu giữ quy trình đơn giản, không thêm bước. Mọi cỡ mẫu
là ước lượng. Các phương pháp thống kê (Wilson, McNemar, Newcombe, positive agreement, rule of three) mới nêu theo trí
nhớ, phải mở tài liệu gốc trước khi vào luận văn. Hạ tầng và lý do: `../relabel-sensitivity-20261031/RESULTS.md`.

## 1. Ràng buộc đã chốt với user

- Một người gán, từ 12 giờ trở lên. Không có phép đo giữa hai người. Văn bản chỉ dùng vai `người gán`, không nêu tên.
- Chỉ dùng model Anthropic. Đây là một hạn chế phải viết.
- Gán lại đúng một lần.
- Đo trên mã mới nhất: jar SR, HEAD `1cd0d091f4`.

## 2. Ai làm gì

| Việc | Ai |
|---|---|
| Soạn phiếu, chạy script, khoá protocol, viết đáp án pilot | Phiên soạn phiếu; người gán không thấy đáp án |
| Gán T, A, B, C, `U` | Người gán, mù với nhãn máy, điểm mô hình, tầng, target |
| Hai lượt máy | `claude -p --safe-mode`, Sonnet và Opus, cách ly; phiên đã thấy nhãn không gán |
| Hai lượt máy lệch ở train | Người gán quyết trong phạm vi hàng đợi; phần vượt loại khỏi huấn luyện và đếm số |
| Hai lượt máy đồng ý, người lệch, ở train | Nhãn máy giữ nguyên; dòng chỉ được đếm vào số đo |
| Hai lượt máy đồng ý, người lệch, ở test | Dòng tranh chấp, báo hai cận như `U` |
| `U` ở test | Giữ `U`, báo hai cận: coi tất cả là T và coi tất cả là N |
| Phân xử | Không có bước này |

Người gán chỉ học từ phiếu. Câu hỏi ghi bằng văn bản, trả lời ở mức lớp, không bàn dòng nào.

Người gán có hai tác dụng: làm đáp án test độc lập với AI, và cho ra tỉ lệ nhãn đúng kèm khoảng tin cậy; đồng thời quyết
các dòng hai AI lệch nhau. Dòng hai AI đã đồng ý ở train giữ nguyên. Người gán thấy method, path, mô tả, danh sách trường,
điền ba ô A, B, C, và `victim`, `role` nếu là T. Người gán không thấy nhãn AI, vì thấy rồi dễ gật theo.

### Quy trình cụ thể

1. Viết phiếu, khoá danh sách test, viết protocol, commit bản nháp.
2. Thử 20 dòng train có đáp án sẵn, sửa phiếu nếu cần, commit bản khoá.
3. Test: AI-1 (Sonnet) và AI-2 (Opus) gán riêng khoảng 8.470 endpoint. Script chọn và trộn 268 dòng cho người gán: 130 AI
   gọi T, 80 top-4 P2f mà AI không gọi T, 42 ngẫu nhiên, 16 biết đáp án. Commit hash đáp án để niêm phong.
4. Train: AI-1, AI-2 gán riêng 10.381 endpoint. Dòng khớp thì chốt. Người gán làm 189 dòng trộn lẫn: 100 dòng lệch quyết
   nhãn, 89 dòng mẫu chỉ để đo (30 cùng T, 15 cũ T mới N, 44 N điểm cao). Học mô hình mới từ nhãn chốt.
5. Chạy thật P2f và mô hình mới trên target, chọn theo §6. Thêm 30 dòng top-4 của mô hình mới vào phần người gán ở test.
6. Mở test một lần: bộ API có op T theo đáp án người, op đó có nằm trong 4 ứng viên đầu không, Wilson 95%. Dòng người và AI
   lệch nhau tính cả hai cách.
7. Chọn mô hình mới thì chạy cổng hồi quy và đo lại các hàng không reset. Từ 18/11 chỉ viết.

Tổng người gán khoảng 507 dòng, khoảng 12 giờ.

## 3. Dữ liệu

- Train: 230 bộ đã có, 10.381 op ghi, gán lại toàn bộ.
- Test: nhà cung cấp chưa bốc trong số 371, bỏ nhà trùng công ty với tập đã bốc, xét bằng tên trong `list.json`, chưa mở
  spec. Ước lượng còn khoảng 350 nhà, khoảng 37 spec có op T, khoảng 8.470 op.
- Một script, một file `test-specs.json` có sha256 từng spec lúc tải, vì nguồn là URL sống. Spec test chỉ phiên gán cách
  ly đọc.
- Gộp công ty (1password, apigee, redhat) khi chia kiểm chéo.

## 4. Phiếu

Gán sự kiện nguyên tử, suy `T_core` bằng bảng ánh xạ khoá trước. Đổi phạm vi về sau chỉ đổi bảng, không gán lần hai.

| Trường | Giá trị |
|---|---|
| A, chủ thể | Tài khoản đã có được chỉ định / chính người gọi / tài khoản mới / group / không phải user / không có |
| B, hành động | Đặt giá trị vai trò, gỡ vai trò, cấp hoặc thu quyền, cờ admin, đổi vai trò thành viên, vô hiệu hoá, xoá tài khoản, định nghĩa role, credential, ACL tài nguyên, khác |
| C, chiều tác động | Hạ được / chỉ nâng / không rõ |
| `U` | Chữ trong spec không đủ |
| `victim`, `role`, `order` | Như cũ, khi `T_core` = 1 |

`T_core` = 1 khi A là tài khoản đã có hoặc người gọi, B thuộc nhóm vai trò, quyền, cờ admin, và C là hạ được hoặc không
rõ. Op chỉ nâng quyền có `T_core` = 0.
Căn cứ phải kiểm nguyên văn: MR-A1, BSR Draft §6.1, SCIM `roles`, `entitlements`, `active` (`../sources.md`).

- Vô hiệu hoá gán riêng, ngoài `T_core`. Lý do: C4 đòi lần replay cuối trả 403 bằng credential mới
  (`RestSecurityBuilder.kt:1156`), tài khoản bị khoá không đăng nhập lại được (`coverage.md` §4). Đã đối chiếu mã, chưa
  chạy thử trên app khoá tài khoản.
- `POST /users` có `role`: tài khoản mới, `T_core` = 0, vì MR-A1 cần trạng thái ALLOWED trước đó. Spec nói "tạo hoặc cập
  nhật" thì A là tài khoản đã có.

## 5. Hàng đợi người gán

Một thứ tự cố định, đi tới đâu hết giờ thì dừng. Test luôn đi trước, spec xếp ngẫu nhiên theo seed, dừng ở ranh giới spec.
Mốc theo 79 giây một dòng.

| Mục | Mốc 8 giờ | Mốc 12 giờ | Mốc 16 giờ |
|---|---|---|---|
| Pilot | 20 | 20 | 20 |
| Test: máy có phiếu T | 130 | 130 | 130 |
| Test: top-4 M1 chưa có phiếu T | 60 | 80 | 100 |
| Test: nhiễu 1:5 | 38 | 42 | 46 |
| Dòng biết đáp án, trộn vào test | 16 | 16 | 16 |
| Test: top-4 M2 bổ sung | 0 | 30 | 50 |
| Train: hai lượt cùng T | 30 | 30 | 80 |
| Train: cũ T, mới đều N | 15 | 15 | 15 |
| Train: hai lượt lệch | 16 | 100 | 100 |
| Train: băng điểm cao trong đồng thuận N | 0 | 44 | 120 |
| Tổng | 325 | 507 | 677 |

Pilot: 20 dòng train có đáp án viết sẵn, để phát hiện chỗ phiếu mơ hồ và kiểm người gán hiểu phiếu, không tính vào số đo.
Kiểm chất lượng duy nhất: 16 dòng biết đáp án trộn trong test.

## 6. Hai mô hình

- Jar nền: SR, HEAD `1cd0d091f4`. M2 đo trên các hàng không reset; cột có reset giữ làm số lịch sử trên P2f.
- M1: mô hình P2f, giữ nguyên làm phương án lùi.
- M2: công thức Naive Bayes cũ, ngưỡng ≥ 2 nhà cung cấp cũ, chỉ đổi nhãn. Mỗi arm một biến.
- Hash của M1, M2 commit trước khi mở test. Cả hai cùng lên test.
- Chọn bằng chạy thật trên cùng jar: target nào về 0 phát hiện, hoặc có FP mới, thì giữ M1. Không xét chênh lệch nhỏ hơn vì
  n nhỏ. Kiểm gồm cả arm bản vá, vì `RestSecurityOracle.kt:580`, `:599` dùng chung cổng điểm > 0. Offline chỉ để phát hiện
  mất điểm > 0 hoặc mất trường vai trò.
- Mốc M1 trên cùng jar phải đo trước: P2e, P2f chưa chạy Airflow, bamf; bản vá artifact-keeper mới có trên AF2.
- Tiêu chí theo từng target: Airflow là 2 TN, không có 970; bamf chỉ có 5/10 trên jar `ER`.
- Không bao giờ sửa nhãn theo target.

## 7. Số báo cáo

Số chính: tỉ lệ spec test có `T_core` do người xác nhận mà op đó nằm trong 4 ứng viên khả dụng đầu, Wilson 95%, khoảng
±0,15–0,17. Protocol ghi trần của số này và tách hai tầng xếp op, nhận trường, vì 77/199 op T không có trường vai trò.

Số phụ:
- M1 so M2 bằng McNemar chính xác; không có ý nghĩa thống kê không được viết thành tương đương.
- Ứng viên sai trên spec không có T.
- Số op top-4 người gán N mà điểm về ≤ 0 khi bỏ dấu hiệu có dưới 3 op T, chỉ mô tả.
- Độ lệch nhãn cũ so với `T_core`, viết là lệch, không viết là sai.
- Đồng thuận người–máy theo từng tầng; kết quả trên dòng biết đáp án.

8 app có đáp án (reports, vampi, pyLoad, artifact-keeper, Airflow, bamf, raouf, magic) đi qua cùng quy trình gán mù, không
vào train. Reports, vampi và spec pyLoad là của ta nên báo riêng. Các transition này được chọn vì builder đã tìm thấy, nên
số recall lạc quan, và không đo precision.

## 8. Lịch, ước lượng

| Ngày | Việc |
|---|---|
| 11-01 – 11-02 | Chốt jar nền, phiếu, pilot, khoá protocol |
| 11-03 – 11-06 | Test: tải, hai lượt máy, người gán, niêm phong |
| 11-03 – 11-09 | Train song song: hai lượt máy trước, người gán sau; M2 |
| 11-10 – 11-14 | Mốc M1, kiểm M2 trên target, chọn; mở test một lần |
| 11-15 – 11-17 | Nếu chọn M2: cổng và đo lại |
| Từ 11-18 | Chỉ viết |

Quota: khoảng 500 khối hai lượt, khoảng 7 cửa sổ quota theo tốc độ vòng 4.

## 9. Luật dừng

- Khối 001–005: Cohen trên T giữa hai lượt dưới 0,6 thì dừng, xem lại phiếu.
- Hết giờ người gán thì cắt train, không cắt test.
- API thiếu lượt gán lúc hết quota thì loại cả API và đếm.
- 11-15 chưa xong test: bỏ M2, giữ M1.
- Người gán không xong các dòng hai lượt máy lệch ở train: bỏ M2, giữ M1.

## 10. Đã chốt với user, 2026-10-31

1. Từ 12 giờ trở lên, nên giữ M2.
2. Jar nền là mã mới nhất.
3. Trường C giữ, `không rõ` vào `T_core`.

Còn thiếu: nền chuyên môn của người gán, ghi vào protocol.

## 11. Hạn chế phải viết

- Một người gán: sai số cá nhân chỉ được kiểm bằng dòng biết đáp án.
- Sự thật ở đây là chữ trong spec; mọi lượt máy cùng hãng.
- Recall của nhãn không chặn chặt: rule of three cho thấy dòng sạch khó chặn được phần bỏ sót của lớp hiếm.
- Test chỉ thuộc tầng ngẫu nhiên, n khoảng 37, và đo xếp hạng trên spec, không đo phát hiện lỗi trên app chạy thật.
- Luật chọn M1/M2 neo trên target phát triển.
- Mở mã nguồn chỉ được dùng làm số độ nhạy riêng, không đổi số chính.
