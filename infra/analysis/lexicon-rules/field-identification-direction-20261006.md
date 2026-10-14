# Hướng nhận diện trường và ba chế độ chạy — 2026-10-06

Quyết định của user ngày 2026-10-06. Thay quyết định "giữ nhóm nhận diện viết tay, không đổi mã" của
`field-identification-hardcode-20261004.md`. Chưa sửa mã EvoMaster. Nền: `field-labelling-r3-20261006/RESULTS.md`,
`council-20261005/DECISION.md`.

## 1. Ba chế độ

| Chế độ | Thông tin transition đến từ | Câu hỏi nó trả lời | Danh sách từ nhận diện | Trạng thái |
|---|---|---|---|---|
| A1 | Người kiểm thử khai báo `--statefulAuthzTransition "<VERB> <PATH> name=value ..."` (`EMConfig.kt:3065`) | Oracle có bắt được lỗi khi biết transition | Không gọi | Tuỳ chọn đã có; đã dùng ở pyLoad §5.2 (`docs/tier2b-pyload-target.md` §3, dòng 6) |
| A2 | Script ngoài EvoMaster gửi OpenAPI spec cho LLM, nhận về đúng dòng khai báo của A1 | LLM có thay được người khai báo | Không gọi | Chưa làm; thuộc nhánh E của `docs/plan-october.md` |
| B, chính | Builder tự suy ra trong lúc chạy | EvoMaster tự dựng được bộ ba trên API lạ (recall black-box) | Rút từ corpus gán nhãn (§2) | Đang làm |

A1 và A2, khi bật D1 (`--statefulAuthzTwoCredentialJudgment`):
- Transition, trường nạn nhân, giá trị quyền lấy từ dòng khai báo (`RestSecurityBuilder.kt:500–509`, `:736–741`,
  `:1347–1360`).
- Source chọn theo mã 403 và 2xx đã quan sát (`:551–572`); nạn nhân là tài khoản gọi source được 2xx (`:590–595`).
- Không khôi phục quyền (`:679`, điều kiện `declared == null`).
- Phán quyết bỏ điều kiện từ vựng (`RestSecurityOracle.kt:580–583`, `:597–599`).
- Danh sách `:104`, `:414–427` chỉ chạy ở nhánh tự suy ra (`RestSecurityBuilder.kt:742–753`).

Hạn chế đã biết:
- A1 và A2 không đo recall black-box (`EMConfig.kt:3062–3064`). Số của chúng báo riêng, không gộp với B.
- `<victim>` được thay bằng tên tài khoản trong file auth (`:1355`). API cần id thì dòng khai báo phải mang id thật;
  A2 chưa có cách điền id đó.
- bamf: path param chứa email có dấu chấm không nhận giá trị nạn nhân trong EvoMaster v6.1.1 (`CLAUDE.md` §6), độc
  lập với từ vựng.

## 2. Từ vựng cho chế độ B: gán nhãn vòng 4

Khung. Protocol đầy đủ viết và chốt trước khi gán dòng nào.

| Bước | Cách làm |
|---|---|
| Dữ liệu | Mọi operation ghi của 230 API vòng 3: 10.381 op. Vòng 3 đã gán 3.972; gán thêm 6.409 op mà trần 36 op/spec bỏ qua (`field-labelling-20261004/extract_fields.py:12`) |
| Phiếu | `field-labelling-r3-20261006/GUIDE.md`, không đổi |
| Gán | L1 và L2 là hai phiên `claude -p --safe-mode` cách ly (Opus 5.5, Sonnet 5.5), mù với nhau và với mọi nhãn cũ. Phân xử mù từng dòng bằng một phiên mới, có lý do |
| Dừng sớm | Kappa T trên 5 khối đầu dưới 0,6 thì dừng, sửa phiếu, ghi lệch luật |
| Rút | Luật vòng 3 (`field-labelling-r3-20261006/PROTOCOL.md` §5) trên toàn bộ 10.381 op. Một thay đổi: ứng viên là token tách từ corpus cộng tên thuộc tính SCIM RFC 7643 §4.1 và thuật ngữ BSR INCITS 359 (`sources.md`); bỏ từ viết tay khỏi ứng viên. Cờ admin và trường vai trò dùng cùng luật, tách theo kiểu boolean như vòng 3. Thấp/cao rút khi có ≥ 15 enum có thứ tự từ ≥ 10 nhà cung cấp; không đủ thì giữ danh sách `:418–419` và ghi là phần viết tay còn lại, kèm độ phủ trên corpus |
| Đo | Mô phỏng runtime và kiểm chéo nhóm như vòng 3: M1–M5, McNemar chính xác, KTC bootstrap theo nhà cung cấp; so với bộ viết tay |
| Dùng | Danh sách rút được vào jar nguyên vẹn, dù kết quả đo thế nào |
| Sau đó | Một thay đổi mã chỉ thay nội dung danh sách; self-test; cổng hồi quy; đo lại bảng `CLAUDE.md` §4; chạy B trên artifact-keeper và bamf |

Nhãn vòng 4 còn làm tham chiếu khi đo A2 offline trên corpus. Cả nhãn lẫn A2 đều do LLM, nên phép đo đó là độ khớp
giữa hai LLM.

Hạn chế mang theo: 3.972 op cũ có L1 là phiên chính, đã thấy dữ liệu hai vòng trước; 6.409 op mới có L1 cách ly.

## 3. Luật chống vòng lặp

- Không đổi luật rút sau khi thấy số.
- Hạn chót gán: 2026-10-09 12:00. Chưa xong thì dùng danh sách vòng 3
  (`field-labelling-r3-20261006/lists/final-lists.json`) và ghi lệch luật.
- Không mở lại bàn phương pháp cho phần này trước khi viết xong chương.

## 4. Lịch, ước lượng

| Ngày | Việc |
|---|---|
| 10-06 | Protocol vòng 4; user duyệt |
| 10-06 – 10-09 | Gán 6.409 op, chạy đêm; ban ngày: A1 trên reports-api, vampi, pyLoad, artifact-keeper, bamf (mỗi lúc một việc nặng) |
| 10-09 | Rút, đo, `RESULTS.md` |
| 10-10 – 10-11 | Thay mã (duyệt trước), self-test, cổng hồi quy |
| 10-12 – 10-14 | Đo lại bảng §4 trên jar mới; B trên artifact-keeper, bamf |
| Từ 10-15 | A2 (nhánh E) và phần còn lại của `docs/plan-october.md` |
