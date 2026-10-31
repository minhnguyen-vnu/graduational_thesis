# Gán nhãn lại, phần AI — protocol

Chốt 2026-11-01, trước khi gán dòng nào. Thiết kế: `../relabel-design-20261031/DESIGN-DRAFT.md`. Phiếu `GUIDE.md` do phiên
soạn phiếu chốt theo §4 của thiết kế; user uỷ quyền chốt và sẽ duyệt sau. Không sửa mã EvoMaster. Thay đổi sau khi chốt ghi ở §9.

## 1. Dữ liệu

- Train: 230 bộ API, 10.381 op ghi (`../field-labelling-r4-20261006/rows-all.jsonl`), 139 khối 75 op, thứ tự bộ xáo theo
  seed `20261101`.
- Test: trong 371 nhà cung cấp chưa bốc, bỏ `ably.io`, `bbc.co.uk` vì trùng công ty với tập đã bốc; gộp `apiz.ebay.com`
  vào `ebay.com`; gộp `google.home`, `googleapis.com`, `walletobjects.googleapis.com` vào `google.com`. Xét bằng tên trong
  `../../corpus/apis-guru-list.json`, chưa mở spec. Còn 365 công ty, mỗi công ty một bộ, seed `20261101` (`fetch_test.py`).
  Tải được 365/365, sha256 trong `test-specs.json`. 128 bộ không có op ghi; còn 237 bộ, 8.674 op, 116 khối (`build_rows.py`).
- Biết đáp án: transition của 8 target và một op cùng spec làm mồi, 16 dòng, 1 khối (`rows-known.jsonl`). Không vào train.
- Trích trường giống vòng 3, 4 (`extract_fields`), mô tả 400 ký tự, tối đa 80 trường, mỗi enum tối đa 12 giá trị.
- Không phiên nào đã thấy nhãn đọc spec test. Phiên soạn phiếu chỉ in số đếm.

## 2. Lượt gán

| Lượt | Lệnh |
|---|---|
| A | `claude -p --safe-mode --no-session-persistence --tools "" --model claude-sonnet-5-5 --effort high` |
| B | như A, `--model claude-opus-5-5 --effort medium` |

Mỗi khối một lời gọi. Phiếu đi qua `--system-prompt`, khối đi qua stdin, không có tool, thư mục chạy rỗng, gỡ biến môi
trường của phiên chính. Đầu ra CSV được kiểm: đủ mọi mã dòng, không mã lạ, A, B, C, `U` thuộc tập mã.

## 3. Suy `T_core`

`T_core` = 1 khi A thuộc `existing`, `self`; B thuộc `role_set`, `role_remove`, `perm`, `admin_flag`, `member_role`,
`member_remove`; C thuộc `down`, `unclear`. `U` ghi riêng, không đổi `T_core`. Đổi phạm vi về sau chỉ đổi bảng này.

## 4. Thứ tự chạy

Train khối 001–005, known, test toàn bộ, train còn lại. Hai lượt chạy song song, độc lập.

## 5. Luật dừng

Khi xong train 001–005: Cohen trên `T_core` giữa hai lượt dưới 0,6 thì dừng, xem lại phiếu. Kappa không xác định thì
chạy tiếp và ghi lại. Mục khác: §9 của thiết kế.

## 6. Hết quota và lỗi

`driver.py`, chạy bởi `run.sh` dưới `caffeinate`, tách khỏi phiên chat.

- Khối xong là một file `A|B/<phần>/chunk-NNN.csv`, ghi nguyên tử sau khi qua kiểm tra. Chạy lại thì bỏ qua khối đã xong.
- Sự kiện `rate_limit_event` trạng thái `rejected`, hoặc chữ báo hết hạn mức: cả hai lượt chờ tới `resetsAt` cộng 120
  giây; không có giờ reset thì thử lại sau 300 giây.
- Lỗi truyền: thử lại sau 300 giây, không giới hạn số lần.
- Đầu ra sai: thử lại tối đa 5 lần mỗi lượt quét, 2 lượt quét; vẫn sai thì ghi khối hỏng vào `STATUS.md`, đi tiếp.
- Driver chết thì `run.sh` khởi động lại sau 60 giây. Không có luật dừng theo quota tuần (user, 2026-11-01).
- Self-test: `selftest/selftest_driver.sh`, 15 kiểm tra trên `claude` giả.

## 7. Chọn dòng cho người gán

`select_queue.py`, chạy khi hai lượt xong. Số trong thiết kế là dự toán; số thật ghi ở `AI-REPORT.md`. Bộ thiếu nhãn ở một
lượt bị loại cả bộ và đếm.

| Hàng đợi | Tầng | Luật |
|---|---|---|
| Test | AI gọi T | Mọi dòng có ít nhất một lượt `T_core` = 1 |
| Test | top-4 P2f | Bộ test theo thứ tự seed, thêm top-4 khả dụng của `stateful-authz-model.csv` ngoài tầng trên, trần 80, dừng ở ranh giới bộ |
| Test | ngẫu nhiên | 1/5 tổng hai tầng trên, từ dòng còn lại, seed |
| Test | biết đáp án | 16 dòng |
| Train | hai AI lệch | Lệch `T_core` trước, rồi cùng T nhưng lệch `victim`, `role`, `order`, trần 100 |
| Train | cùng T | 30 dòng ngẫu nhiên trong nhóm khớp hoàn toàn |
| Train | cũ T, mới N | 15 dòng ngẫu nhiên, ít hơn thì lấy hết |
| Train | N điểm cao | Phần còn lại của ngân sách 507 dòng (đã trừ 30 dòng top-4 mô hình mới), tối đa 120, điểm Naive Bayes out-of-fold cao nhất, chia theo công ty |

Mỗi hàng đợi trộn theo seed. Người gán thấy `handover/*.csv`: số thứ tự, method, path, mô tả, schema, trường, ô trống. Mã
dòng và tầng nằm ở `sealed/`. `SEALS.txt` giữ sha256 mọi nhãn AI và hàng đợi.

## 8. Dừng ở đâu

Phần AI dừng tại hàng đợi người gán. Chưa học mô hình mới, chưa mở test.

## 9. Lệch so với thiết kế và thay đổi sau khi chốt

- Pilot người chạy sau lượt AI (user, 2026-11-01). Pilot làm đổi định nghĩa trên phiếu thì AI gán lại phần liên quan.
- Hai lượt AI không có tool; thiết kế ghi `claude -p --safe-mode`, vòng 4 có Read và Write.
- Thêm mã `member_remove` vào B và vào `T_core`: nhãn cũ có 25 T, 15 N trên các op `DELETE` gỡ thành viên, không nhất quán.
- Test 365 công ty, thiết kế ước lượng 350 nhà.
- Mã hoá A, B, C thành mã tiếng Anh ngắn để kiểm được đầu ra.
- 2026-11-01 01:05, sau train 001–005: Cohen `T_core` 0,856 trên 375 dòng, Sonnet 3, Opus 4 dòng T, lệch 1; `U` Sonnet 34,
  Opus 56. Không dừng. Năm khối này tốn khoảng 1,6% quota 5 giờ mỗi cặp nên từ khối 006 đặt `DISABLE_PROMPT_CACHING=1`:
  mỗi khối chỉ gọi một lần, cache không được dùng lại. Biến này không đổi prompt hay model.
