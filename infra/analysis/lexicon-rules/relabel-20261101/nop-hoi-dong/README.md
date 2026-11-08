# Dữ liệu gán nhãn lại

Dựng ngày 2026-11-07 bằng `../build_nop.py`, 31/31 kiểm tra PASS. Chỉ gồm phần được dùng theo các quyết định tới
2026-11-07. Bản gốc của mọi phần ở thư mục cha `relabel-20261101/`.

## File

| File | Dòng | Nội dung |
|---|---|---|
| `op-hoc.jsonl` | 10.381 | Op ghi của 230 API phần học |
| `op-thi.jsonl` | 8.674 | Op ghi của 237 API phần thi |
| `nhan-ai-hoc.csv` | 10.381 | Nhãn hai lượt AI trên phần học, kèm nhóm |
| `nhan-ai-thi.csv` | 8.674 | Nhãn hai lượt AI trên phần thi, kèm nhóm và cột `cho_boc` |
| `nhan-nguoi-gan.csv` | 1.146 | Nhãn người gán |
| `nhan-hoc-cuoi.csv` | 10.381 | Nhãn cuối của phần học, dùng để học M2 |
| `review-66-lech.csv` | 66 | 66 op người khác cả hai AI, kèm lựa chọn cuối ở cột `chon` |
| `nhan-thi-cuoi.csv` | 8.674 | Nhãn cuối của phần thi, là đáp án để chấm M2 |
| `review-thi-lech.csv` | 53 | 53 op phần thi người khác cả hai AI, kèm lựa chọn cuối ở cột `chon` |
| `soat-lai-44-thi.csv` | 44 | 44 op phần thi một AI gọi T, một AI gọi N, soát lại sau khi chấm M2 |
| `huong-dan/HUONG-DAN.html` | | Hướng dẫn và phiếu cho người gán, bản đợt 4 |
| `huong-dan/CONG-CU-GAN-NHAN.html` | | Công cụ gán chạy trong trình duyệt |
| `huong-dan/phieu-cho-AI.md` | | Phiếu đưa cho hai lượt AI |
| `SHA256SUMS.txt` | | Mã băm mọi file trên |

Hai lượt AI: `sonnet_*` là Claude Sonnet 5.5 effort high, `opus_*` là Claude Opus 5.5 effort medium, mỗi lượt gán riêng,
không tool (`../PROTOCOL.md` §2).

Op hạ quyền (T): A thuộc `existing`, `self`; B thuộc `role_set`, `role_remove`, `perm`, `admin_flag`, `member_role`,
`member_remove`; C thuộc `down`, `unclear`.

## Nhóm và nhãn dùng

Phần học:

| `nhom` | Op | Người gán xem |
|---|---|---|
| `hai_AI_cung_T` | 173 | 30 (`cung_T`, đợt 3) + 135 (`cung_T_con_lai`, đợt 4) |
| `cung_T_lech_truong` | 25 | Hết (`lech`, đợt 3) |
| `lech_T` | 41 | Hết (`lech`, đợt 3) |
| `hai_AI_cung_N` | 10.142 | 371 ngẫu nhiên (`N_ngau_nhien_hoc`, đợt 4) |

- `hai_AI_cung_T`: hai lượt cùng gọi T và cùng `victim`, `role`, `order`. 8 op còn lại là ví dụ có lời giải trong hướng
  dẫn nên không đưa người gán.
- `cung_T_lech_truong`: hai lượt cùng gọi T, lệch `victim`, `role` hoặc `order`.
- `lech_T`: một lượt gọi T, lượt kia không.

Nhãn học cuối (`nhan-hoc-cuoi.csv`, dựng bằng `../build_nhan_hoc_cuoi.py`, cột `nguon`):

| `nguon` | Op | T | Luật |
|---|---|---|---|
| `nguoi` | 550 | 154 | Người đã xem: 536 op khớp ít nhất một AI, và 14 op trong 66 op lệch chốt theo người |
| `hai_AI` | 43 | 41 | 35 op trong 66 op lệch chốt theo hai AI, và 8 op ví dụ trong hướng dẫn (hai AI cùng T, người chưa xem) |
| `opus` | 17 | 14 | Op trong 66 op lệch chốt theo lượt Opus |
| `AI_chua_xem` | 9.771 | 0 | Chưa xem: op hai AI cùng N ngoài 371 op ngẫu nhiên |
| Cộng | 10.381 | 209 | |

- Lệch nghĩa là khác T/N, hoặc cùng T nhưng khác `victim`, `role`, `order`. 66 op lệch được xem lại và chốt ngày
  2026-11-07; lựa chọn ở cột `chon` của `review-66-lech.csv`.
- T = 1 khi A, B, C thoả định nghĩa T ở trên. Op N để trống `victim`, `role`, `order`.
- Op `AI_chua_xem` và op `hai_AI` ghi A, B, C theo lượt Sonnet. Hai lượt cùng T/N, và op T cùng `victim`, `role`, `order`.

Phần thi:

| `nhom` | `cho_boc` | Op | Người gán xem |
|---|---|---|---|
| `it_nhat_mot_AI_T` | 0 | 176 | Hết (`T`, đợt 2) |
| `hai_AI_cung_N` | 1 | 8.382 | 368 ngẫu nhiên: 51 (`nhieu`, đợt 2) + 317 (`N_ngau_nhien_thi`, đợt 4) |
| `hai_AI_cung_N` | 0 | 116 | Không |

116 op `cho_boc` = 0 được để riêng trước lần bốc 51 op đầu, vì là 4 ứng viên đầu của mô hình P2f
(`../sealed/test-top4-m1.json`). 368 op là mẫu ngẫu nhiên của 8.382 op còn lại.

Nhãn thi cuối (`nhan-thi-cuoi.csv`, dựng bằng `../build_nhan_thi_cuoi.py`, cùng luật với phần học):

| `nguon` | Op | T | Luật |
|---|---|---|---|
| `nguoi` | 493 | 103 | Người đã xem: 487 op khớp ít nhất một AI, và 6 op trong 53 op lệch chốt theo người |
| `hai_AI` | 20 | 20 | Op trong 53 op lệch chốt theo hai AI |
| `opus` | 25 | 24 | Op trong 53 op lệch chốt theo lượt Opus |
| `sonnet` | 2 | 2 | Op trong 53 op lệch chốt theo lượt Sonnet |
| `opus_soat_lai` | 3 | 3 | Op đổi ở lần soát lại 44 op, theo lượt Opus |
| `sonnet_soat_lai` | 1 | 1 | Op đổi ở lần soát lại 44 op, theo lượt Sonnet |
| `AI_chua_xem` | 8.130 | 0 | Chưa xem, hai AI cùng N: 8.014 op `cho_boc` = 1 và 116 op `cho_boc` = 0 |
| Cộng | 8.674 | 153 | |

- 53 op lệch được xem lại và chốt ngày 2026-11-07; lựa chọn ở cột `chon` của `review-thi-lech.csv`.
- 2026-11-08, sau khi đã chấm M2, 44 op một AI gọi T, một AI gọi N được soát lại (`soat-lai-44-thi.csv`, `chon` là `giu`
  hoặc nguồn mới): 40 op giữ, 4 op đổi N sang T (`../PROTOCOL.md` §11).
- 153 op T đều thuộc nhóm `it_nhat_mot_AI_T`; 368 op ngẫu nhiên không có op T.

## Cột

- `nhan-ai-*.csv`: `row_id`, `spec_id`, `method`, `path`, `nhom`, rồi A, B, C, `victim`, `role`, `order` của từng lượt.
- `nhan-nguoi-gan.csv`: `dot`, `stt` (số thứ tự trên phiếu đợt đó), `row_id`, `phan` (`hoc`, `thi`), `tang`, `method`,
  `path`, A, B, C, `victim`, `role`, `order`.
- Hai dòng đợt 4, `stt` 693 và 769, điền `order` cho trường role không có enum. Giữ nguyên như file trả về.

## Không đưa vào

- Cột `U` của mọi nhãn, cột ghi chú của người gán.
- Đợt 1 (20 op làm thử); tầng `top4` 80 op và `biet` 16 op ở đợt 2; tầng `cu_T_moi_N` 15 op và `N_diem_cao` 23 op ở
  đợt 3.
- 16 op biết đáp án và nhãn AI của chúng.
- Nhãn cũ và các cột `split`, `round`, `old_label` của op học; điểm mô hình P2f.

Hướng dẫn và phiếu chép nguyên văn nên còn ô `U`. Đợt 2 và 3 dùng bản hướng dẫn 2026-11-01; bản này khác ở 8 chỗ phần
quy trình, định nghĩa và 18 ví dụ giữ nguyên (`../PROTOCOL.md` §10).
