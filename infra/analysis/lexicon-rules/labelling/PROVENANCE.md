# Xuất xứ của từng lượt gán nhãn

Luật quy trình: `../rules-draft.md` §9.

| Lượt | Model | Effort | Ngữ cảnh khởi động | Ngày chạy |
|---|---|---|---|---|
| L1 | Claude Opus 5 (`claude-opus-5`) | mặc định của subagent, không đặt được qua công cụ spawn | lạnh, không thấy hội thoại của phiên gọi, không thấy L2 | 2026-09-17 |
| L2 | Claude Sonnet 5 (`claude-sonnet-5`) | mặc định của subagent | lạnh, không thấy hội thoại của phiên gọi, không thấy L1 | 2026-09-17 |
| H | người (Minh) | | phiếu `labelling-form.md` | 2026-09-17 trở đi |

Mỗi lượt LLM được mở đúng hai thứ: `labelling-form.md` và file CSV đang làm. Danh sách cấm ghi trong đề bài
của lượt đó, và mỗi lượt phải khai trong báo cáo nếu lỡ mở file ngoài danh sách.

## Chỗ lệch đã khai

- Hai lượt LLM cùng một nhà cung cấp. Đồng thuận L1–L2 đo tính nhất quán của một hệ thống, không đo độ tin cậy
  giữa hai người gán nhãn độc lập. Viết vào phần hạn chế.
- Cả hai lượt chạy trong thư mục dự án nên `CLAUDE.md` nằm trong ngữ cảnh của chúng. File đó không có quy tắc
  gán nhãn và không có nhãn mẫu, nhưng có mô tả oracle và bộ 56 từ cũ. Đề bài cấm dùng, không kiểm chứng được.
  Người gán nhãn không đọc `CLAUDE.md` lúc gán.
- Ba dòng `S034-0001` đến `S034-0003` người gán trước khi đổi quy trình. Giữ làm nhãn người, không tính vào
  mẫu soát.
- Lúc đưa dòng `S034-0002` cho người, hai tên trường `enabled` và `secured` bị in đậm, tức người gán được chỉ chỗ.

## Đợt 30 spec, 2026-09-18

318 operation trên 29 spec (`../../corpus/sampling-plan.md`). Mỗi lượt chia 3 mảnh chạy song song, mỗi mảnh một
phiên riêng, cùng model, cùng đề bài, chỉ khác danh sách spec được giao:

| Mảnh | Spec | Dòng |
|---|---|---|
| 1 | S100 S104 S107 S112 S122 S123 S132 S137 | 106 |
| 2 | S101 S105 S108 S114 S120 S124 S125 S133 S135 | 106 |
| 3 | S102 S103 S106 S109 S115 S116 S118 S119 S128 S130 S131 S136 | 106 |

L1 chạy trên Opus 5, L2 trên Sonnet 5. Chia mảnh là để một phiên không phải sinh 318 dòng CSV liền; các mảnh
không thấy nhau và không thấy lượt kia. Phải ghi vào phần hạn chế rằng một lượt gồm ba phiên chứ không phải một.

## Vòng 2, 2026-09-19/20

519 operation trên 29 spec, phiếu v2 (`../rules-changelog.md`, `../../corpus/sampling-plan.md` §1c). Nhãn ở
`../labelling-r2/`, không ở thư mục này. Mỗi lượt chia 6 mảnh, spec không bị cắt đôi (`../labelling-r2/SHARDS.md`).
L1 chạy 6 phiên Opus 5 song song 23:40–23:50 ngày 09-19; L2 chạy 6 phiên Sonnet 5 song song sau khi L1 xong.

Kiểm cấu trúc bằng `../verify_pass.py`: cả hai lượt đủ 519 dòng, 9 cột dữ liệu vào không đổi, nhãn và mã hợp lệ,
0 lỗi.

### Chỗ lệch đã khai, vòng 2

- Một lượt gồm 6 phiên, không phải một. Sáu phiên cùng model, cùng đề bài, chỉ khác danh sách spec.
- Sáu phiên L1 dùng chung một thư mục scratchpad và ghi đè script tạm của nhau. Ba phiên tự khai đã xem thư
  mục đó và thấy tên file tạm của mảnh khác (mảnh 1, 4, 5). Mảnh 5 `cat` nguyên script `fill.py` của phiên khác,
  mảnh 4 đọc 5 dòng đầu của `apply.py`, mảnh 1 thấy nội dung `fill.py` khi bị ghi đè. Không phiên nào khai đã mở
  dữ liệu nhãn của mảnh khác. Script tạm không chứa nhãn. Các phiên L2 được giao thư mục riêng `l2s1`…`l2s6`.
- Mảnh 2 của L2 (S108 S115 S116 S119 S130 S137) dừng vì lỗi 429 (giới hạn phiên) sau khi đã ghi đủ 6 file; nó
  đang sửa lại cột `note`. Sáu file qua kiểm cấu trúc; phần `note` có thể không dấu.
- Các phiên đều khai `CLAUDE.md` nằm sẵn trong ngữ cảnh, như vòng 1.
- Chi phí: L1 ~600 nghìn token, L2 trên 690 nghìn. Phần lớn là chi phí cố định theo phiên, nên vòng sau chia ít
  mảnh hơn.

**Vòng 2, lượt người (2026-09-20).** Mẫu soát đổi sang bốc phân tầng: 44 dòng lệch, 37 dòng hai máy cùng `R`
(toàn bộ), 40 dòng hai máy cùng `N` bốc bằng hạt giống `20260918`. Khai ở `infra/analysis/corpus/sampling-plan.md` §1d.
Worklist dựng bằng `stratify_r2.py`, 121 dòng.

**Lượt người vòng 2 (2026-09-20).** 121/121 dòng, kiểm cấu trúc 0 lỗi (`verify_human.py`). Ba dòng có câu giải
thích rơi vào cột `doubt_token`, đã chuyển sang cột `note`, nhãn không đổi. Theo yêu cầu của người gán, mô hình
đọc lại 43 dòng `N5`/`N6` và sửa 21 dòng, ghi ở `labelling-r2/model-revisions.csv`. Bốn dòng mô hình nêu nghi vấn
nhưng không sửa, để người gán quyết: `S108-0129`, `S124-0012`, `S112-0124`, `S123-0013`.

**Phân xử vòng 2 (2026-09-20).** 20 dòng tầng `agree-R` do mô hình phân xử, sổ `labelling-r2/adjudication.csv`:
17 dòng thành `R`, 3 dòng thành `U`. Hai dòng giữ nguyên nhãn người gán. Cột `label` không bị đè.
Bảy dòng mô hình từng đè lên `label` ngày 09-20 đã trả về nhãn gốc.

**Nhãn chốt vòng 2 (2026-09-20).** `labelling-r2/final.csv`, 519 dòng: 40 `R`, 470 `N`, 9 `U`.
Nguồn từng dòng ghi ở cột `nguon`: 398 dòng lấy nhãn hai máy trùng nhau không soát (`audited=0`), 54 dòng ba bên
trùng, 35 dòng nhãn người có một máy đồng tình, 32 dòng mô hình phân xử. Dựng bằng `build_final.py`.

## 2026-09-20 23:34 — rút bộ từ vựng lần 1
Luật: `rules-draft.md` §11, ghi lúc 23:31, trước khi `derive_lexicon.py` được viết.
Vào: `labelling-r2/final.csv` nửa train, 26 `R` / 215 `N`, 14 nhà cung cấp.
Ra: `lexicon-20260920/list-{1,2,3}.txt`, `candidates-{1,2,3}.csv`, `miss-{moi,cu}.csv`, `RESULTS.md`.
Đo trên nửa test chạy trước khi sửa extractor cho S131; ghi ở `RESULTS.md` §5.

## 2026-09-21 00:15 — dem 09-21
`rules-draft.md` §12 (00:02) truoc `rank_lexicon.py`. Ket qua: `lexicon-20260920/rank.txt`, `RESULTS.md` §10.
`corpus/extract_ops.py` them `unwrap_envelope`; 17 dong S131 doi, ban trich lai o `labelling-r3/S131.v2.csv`.
`corpus/sample_specs_ext.py` seed 20260921 boc 15 spec S200-S214 vao nua train; `cap_ext.py` cap 36; 249 dong.
Hai luot may mu chay tren 266 dong (249 moi + 17 S131), ket qua se o `labelling-r3/*.l1.csv` va `*.l2.csv`.
Patch nhap `infra/evomaster-ext/wip/lexicon-rank-20260921.patch`, chua ap, chua build.

## 2026-09-21 00:37 — hai luot may tren phan mo rong
L1 va L2 moi luot 266 dong, kiem doc lap bang `verify_r3.py`: 0 loi ca hai.
L1 18 R / 245 N / 3 U. L2 21 R / 241 N / 4 U. Dong thuan tho 0.959, pe 0.840, kappa 0.742.
`merge_r3.py` -> `labelling-r3/final.csv`: giu 253, loai 13 theo `sampling-plan.md` §1g.
`derive2.py` -> `lexicon-20260921/`: candidates-1.csv, rank.txt, stateful-authz-lexicon.csv, RESULTS.md.

## 2026-09-21 00:59 — gan bu de do hang chinh xac
41 dong chon theo `sampling-plan.md` §1h, ghi o `labelling-r4/`.
L1 14 R / 25 N / 2 U, L2 18 R / 21 N / 2 U, ca hai qua `verify_r3.py` 0 loi.
Dong thuan tho 0.854, pe 0.465, kappa 0.727. Giu 34, loai 7.
`rank-exact.txt`: nua test top-1 0.500, top-3 0.833, top-8 1.000. Ba con so nay sai, xem muc 2026-09-21 21:35.
41 dong nay khong vao phan rut tu vung.

## 2026-09-21 21:35 — lượt soát thứ ba trên phần mở rộng

Luật khai trước khi chạy ở `../../corpus/sampling-plan.md` §1i.

| Lượt | Model | Ngữ cảnh khởi động | Ngày chạy |
|---|---|---|---|
| audit-3 | một lượt riêng, mù | chỉ `labelling-form.md` v2 và `labelling-r34-audit/audit-in.csv` | 2026-09-21 |

Mẫu 56 dòng: toàn bộ 28 dòng `final_label = R` của `labelling-r3` và `labelling-r4`, cộng 28 dòng `N`
bốc bằng hạt giống `20260921` làm dòng nhiễu. Lượt gán không biết dòng nào thuộc nhóm nào.
Dữ liệu vào dựng bằng `../make_audit_in.py`; khoá ở `labelling-r34-audit/key.csv`.

Kiểm cấu trúc độc lập `../verify_audit3.py`: 56 dòng, 9 cột vào trùng từng byte, `annotator` là `llm`,
nhãn hợp lệ, mã thuộc bộ 15 mã và khớp chữ cái đầu, `rule_id` rỗng khi và chỉ khi `U`, `doubt_token`
khác rỗng khi và chỉ khi `U`. **0 lỗi.** Kết quả thô 25 `R` / 30 `N` / 1 `U`.

Gộp bằng `../merge_audit3.py`. Nhóm hai máy cùng `R`: 28 dòng, bỏ 1 dòng `U`, đồng thuận thô `0.926`,
`pe 0.926`, kappa `0.000`. Nhóm hai máy cùng `N`: 28 dòng, đồng thuận thô `1.000`. Cả 56 dòng:
đồng thuận thô `0.964`, `pe 0.501`, kappa `0.927`, bỏ 1 dòng `U`.

Kappa `0.000` ở nhóm đầu là hệ quả của cách bốc mẫu, không phải của lượt gán: trong một nhóm chỉ có một
lớp thì `pe = po`. Báo đồng thuận thô của từng nhóm cộng kappa của cả 56 dòng.

Ba dòng đổi, tất cả thuộc nửa train: `S210-0137` `R`→`N`, `S211-0008` `R`→`N`, `S214-0106` `R`→`U` và bị bỏ.
Bốn mươi mốt dòng của `labelling-r4` không đổi nhãn nào; chỉ `audited` lên `1` và `nguon` thành `audit-3`.

Nhãn chốt: `labelling-r3/final.v2.csv` (12 `R` / 240 `N` / 14 bỏ) và `labelling-r4/final.v2.csv`
(13 `R` / 21 `N` / 7 bỏ).

### Chỗ lệch đã khai, lượt soát thứ ba

- Lượt này không tìm được dòng `R` mà cả hai lượt máy cùng bỏ sót: mẫu chỉ gồm dòng hai máy đã đồng thuận.
  Nó đo tỉ lệ dương giả của nhãn `R` đồng thuận, không đo độ nhạy.
- Lượt soát vẫn là LLM, cùng nhà cung cấp với L1 và L2. Không có lượt người nào trên phần mở rộng.
- 240 dòng `N` của phần mở rộng vẫn `audited=0`.

## 2026-09-21 21:33 — rút lần 3 và sửa cách tách từ

`../derive3.py` chạy trên `labelling-r2/final.csv` nửa train cộng `labelling-r3/final.v2.csv`:
36 `R` / 441 `N`, 29 nhà cung cấp, 10 nhà cung cấp có `R`.
Ra: `lexicon-20260921-audited/`, `stateful-authz-lexicon.csv` 53 từ `path` và 45 từ `param`.

Sửa kèm: sinh ứng viên không hạ chữ thường trước khi tách camelCase, đúng `../rules-draft.md` §11.4.
Nửa `param` cũ giữ `permissiongroupid` và `policyid`; nửa `path` tái lập trùng từng byte.

`../rank_exact2.py` thay `rank_lexicon.py`: hạng báo thành khoảng tốt nhất–xấu nhất cộng một giá trị
phá hoà theo thứ tự spec. Nửa test: khoảng `0.333–0.667`, thứ tự spec `0.500` cho top-1.

Tái lập 2026-09-23: chạy lại `derive3.py` cho ra 7 file trùng từng byte với bản ghi ngày 09-21.

