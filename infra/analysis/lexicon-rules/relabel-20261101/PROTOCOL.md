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
- 2026-11-01 15:11, user đổi sang tài khoản Claude khác khi tài khoản đầu hết quota 5 giờ; driver khởi động lại để bỏ
  lượt chờ. Cùng CLI 2.1.316, model, effort, phiếu. Mọi lời gọi từ 15:12:44 dùng tài khoản mới: train A từ khối 109, B
  từ khối 088 (`run.log`, `usage.csv`).
- 2026-11-01 15:33 phần AI xong, 0 khối hỏng; số thật ở `AI-REPORT.md`. User giữ `member_remove` trong `T_core`: 94 dòng
  train chỉ là T nhờ mã này, nhãn cũ ghi 46 T, 48 N.
- Gói bàn giao `ban-giao-gan-nhan-20261101.zip`, dựng bằng `pack_handover.sh` từ `ban-giao/`. Gồm: phiếu chép nguyên văn,
  hướng dẫn làm việc, công cụ HTML chạy offline, câu hỏi về nền chuyên môn của người gán. Người gán có thêm 18 ví dụ đã
  giải mà hai lượt AI không có: dòng train hai AI khớp hoàn toàn, nằm ngoài mọi hàng đợi. Luật cho người gán: làm một
  mình, chỉ dựa vào chữ hiển thị, không dùng công cụ AI hay công cụ dịch. File đổi tên, nội dung trùng sha256 trong
  `SEALS.txt`: `pilot.csv` thành `dot-1-thu.csv`, `test-queue.csv` thành `dot-2.csv`, `train-queue.csv` thành
  `dot-3.csv`. Self-test công cụ `selftest/handover_tool_test.js`: 52/52.
- Hai mục trên thêm sau khi niêm phong; bỏ chúng thì `PROTOCOL.md` khớp mã băm trong `SEALS.txt`. Nhãn AI, `sealed/`,
  `AI-REPORT.md`, `rows-known.jsonl` không vào git tới khi người gán xong, vì người gán có thể đọc repo; bản sao ở
  `~/thesis-backups/relabel-20261101-sealed-20261101-1632/`. `SEALS.txt` vào git để giữ mốc thời gian.

## 10. Đợt 4, chốt 2026-11-06 trước khi gán

Phạm vi dùng (user, 2026-11-05 và 11-06): bỏ mọi tầng chọn theo nhãn cũ hoặc theo M1 và pilot. Bỏ: train `cu_T_moi_N`
15, `N_diem_cao` 23; test `top4` 80, `biet` 16; pilot 20. Còn dùng: train `lech` 66, `cung_T` 30; test `T` 176, `nhieu` 51.

Cỡ mẫu theo quy ước mức chắc 95%, độ rộng ±5 điểm: n = ⌈384,16 / (1 + 383,16 / N)⌉, N là cỡ nhóm (công thức Cochran,
chưa kiểm trên nguồn gốc). Nhóm 173 dòng ra 120, gần cả nhóm, nên xem hết.

| Tầng đợt 4 | Nhóm | Cỡ nhóm | Luật | Dòng |
|---|---|---|---|---|
| `cung_T_con_lai` | Train, hai AI cùng T, khớp `victim`, `role`, `order` | 173 | Mọi dòng chưa xem, trừ 8 dòng là ví dụ trong `HUONG-DAN.html` | 135 |
| `N_ngau_nhien_hoc` | Train, hai AI cùng N | 10.142 | Ngẫu nhiên, seed `SEED + 30`, từ 10.132 dòng (trừ 10 dòng ví dụ) | 371 |
| `N_ngau_nhien_thi` | Test, hai AI cùng N | 8.498 | Ngẫu nhiên, seed `SEED + 31`, từ chỗ bốc của 51 dòng `nhieu` (8.382 dòng) trừ 51 dòng đó | 317 |

- 51 + 317 = 368 dòng là một mẫu ngẫu nhiên của 8.382 dòng. Chỗ bốc vẫn trừ 116 dòng top-4 M1 như lần đầu; số 2 nói về
  8.382 dòng đó.
- Trộn bằng seed `SEED + 32`. Phiếu `handover/dot-4.csv`, khoá `sealed/key-dot-4.csv`, script `select_dot4.py` (16 kiểm
  tra PASS, gồm bốc lại seed cũ ra đúng 51 dòng `nhieu`).
- 18 ví dụ trong hướng dẫn là dòng train hai AI khớp hoàn toàn: 8 dòng trong nhóm 173, 10 dòng trong nhóm 10.142. Người
  gán đã thấy lời giải nên không đưa vào đợt 4. Câu cũ "lấy từ các API không thuộc ba đợt" sai: op nằm ngoài hàng đợi
  nhưng API thì không (S210, S213, S514, S532, S626 có op trong đợt 3). Bản mới ghi "Không ví dụ nào nằm trong các đợt
  của bạn".
- 371 dòng train có 1 dòng trùng hàng đợi đợt 3 (tầng đã bỏ) và 1 dòng trùng pilot; 135 dòng có 6 dòng pilot. Các dòng
  này dùng nhãn đợt 4.
- Dòng 188 (`S506-N0018`, train) có 2 trường tên chứa dấu cách. Công cụ hiện nguyên dòng chữ và vẫn gán xong được; hai
  lượt AI thấy cùng chữ.
- Gói `ban-giao-gan-nhan-20261106.zip` dựng bằng `pack_dot4.py` từ `ban-giao/` vào `ban-giao-dot4/`. Định nghĩa, phiếu
  và 18 ví dụ giữ nguyên; chỉ đổi phần quy trình: 8 chỗ trong `HUONG-DAN.html`, 1 câu trong công cụ. Bỏ đợt 1 và
  `thong-tin-nguoi-gan.txt`. `da-gan/` giữ 227 dòng đợt 2 và 96 dòng đợt 3 cùng kết quả, theo `stt` gốc. Kết quả đợt 2
  được lọc theo `stt` bằng script; không in nhãn nào, phần test vẫn chưa mở. Bản người gán trả về nguyên vẹn ở `tra-ve/`.
  Self-test `selftest/dot4_pack_check.sh`: 6/6. Mã băm: `SEALS-dot4.txt`.
- Ước lượng 823 × 80 giây, khoảng 18 giờ.

## 11. Nhãn cuối và ba số, 2026-11-07 tới 11-08

Quyết định của user:

- Bỏ `U` (2026-11-04). Nhãn cuối chỉ dùng A, B, C để suy T, cùng `victim`, `role`, `order` của op T. Khác mã trong 6 mã B
  của §3 không tính là lệch; luận văn không báo cáo theo từng mã.
- Op người gán đã xem lấy nhãn người. Op người khác cả hai AI (khác T/N, hoặc cùng T nhưng khác `victim`, `role`, `order`
  sau khi tách `|` và sắp xếp) được user soát lại và chọn người, hai AI, Sonnet hoặc Opus; lúc soát chỉ hiện nhãn người
  và hai AI. Op chưa xem lấy nhãn Sonnet; ở mọi op này hai AI cùng T/N, op T cùng trường.
- Khoảng tin cậy: Clopper–Pearson 95%, mẫu đếm theo nhãn cuối.
- Không báo cáo: kappa (2026-11-06), hai cận, nhóm nào chọn theo nhãn cũ hoặc theo M1.
- Không dùng commit làm mốc thời gian. `../m2-model-20261107/derive_m2.py` dựng lại M2 từ `nhan-hoc-cuoi.csv`, trùng
  từng byte; đầu vào không có dòng phần thi.

| Phần | File | Op soát | Chọn | Op | T |
|---|---|---|---|---|---|
| Học | `nop-hoi-dong/nhan-hoc-cuoi.csv` (`b00e4a1623f73079…`) | 66 | người 14, hai AI 35, Opus 17 | 10.381 | 209 |
| Thi | `nop-hoi-dong/nhan-thi-cuoi.csv` (`bc716bb8194e57b5…`) | 53, rồi 44 | người 6, hai AI 20, Opus 25, Sonnet 2; lần sau đổi 4 | 8.674 | 153 |

- Dựng bằng `build_nhan_hoc_cuoi.py` (17 kiểm tra), `build_nhan_thi_cuoi.py` (15 kiểm tra); lựa chọn ở
  `review-lech-hoc/review-66.csv`, `review-lech-thi/review-thi.csv`. 8 op ví dụ trong hướng dẫn ghi nguồn `hai_AI`.
- Phần học: 0/371 op ngẫu nhiên hai AI cùng N là T; số op T sót trong 9.771 op chưa xem 0–97.
- M2: `../m2-model-20261107/stateful-authz-model.csv` (`b2deef150bf88837…`), cùng công thức và mã với M1. So offline với
  M1 trên 5 target (`../m2-model-20261107/compare_targets.out`): transition giữ hạng, trường role, victim và giá trị hạ;
  artifact-keeper có 6 op ra khỏi guard.
- Lệch luật: trong lúc soát phần học, một lệnh in 2 dòng nhãn người phần thi (đợt 2, tầng T).
- Lệch luật, 2026-11-08: sau khi chấm M2 và đã in điểm vài op thi, user soát lại 44 op một AI gọi T, một AI gọi N
  (`review-lech-thi/soat-so1.csv`; lúc soát chỉ hiện nhãn người và hai AI). 40 op giữ; 4 op đổi N sang T: `E004-N0071`
  theo Sonnet, `E219-N0016`, `E219-N0024`, `E219-N0033` theo Opus. Nguồn `sonnet_soat_lai`, `opus_soat_lai`. Bản nhãn
  trước lần này: `~/thesis-backups/relabel-20261101-nhan-thi-cuoi-20261107-2345/` (`a6b847299e2f5dd9…`).

Ba số phần thi (`cham-thi/score_thi.py`; trước soát lại `cham-thi/ket-qua.txt`, sau `cham-thi/ket-qua-sau-soat-lai.txt`). Điểm op = prior + tổng trọng số bảng `op` của M2, tính
bằng `derive_model.op_feats` trong Python, chưa qua jar; ứng viên khi điểm > 0.

| Số | Định nghĩa | Kết quả |
|---|---|---|
| 1 | Trong 176 op ít nhất một AI gọi T, op có nhãn cuối T | 153/176 (trước 149/176): hai AI cùng T cùng trường 102/102, cùng T lệch trường 30/30, một AI T 21/44 (trước 17/44) |
| 2 | Trong 368 op ngẫu nhiên hai AI cùng N, op có nhãn cuối T | 0/368; sót 0–80 trong 8.014 op chưa xem |
| 3 | Bắt được: op T có điểm > 0 | 117/153 = 76,5%, CP 68,9–82,9% (trước 116/149 = 77,9%, CP 70,3–84,2%); nếu 80 op sót đều điểm ≤ 0: 117/233 |
| 3 | Báo nhầm: op điểm > 0 có nhãn cuối N | 763/880 (trước 764/880); 727 op nhãn AI chưa xem, 93 op thuộc 116 op top-4 P2f |

- Mẫu ngẫu nhiên không có op T nên Số 3 có trọng số hay không như nhau.
- Số 3 không đo việc chọn trường role, victim.
