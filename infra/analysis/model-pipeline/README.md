# Chuỗi xử lý dữ liệu của mô hình Naive Bayes (mô hình bỏ lặp, jar TR2)

Mọi file ở đây là symlink tới file gốc. Script tính đường dẫn từ chỗ của chính nó, nên chạy bằng đường dẫn gốc
(`readlink <file>`), không chạy qua symlink.

## scripts/ — theo thứ tự chạy

| # | Script | Đọc | Ra |
|---|---|---|---|
| 1 | `extract_fields.py`: trích trường path, query, body của mỗi op ghi; tối đa 80 trường, 12 giá trị enum, sâu 3 | spec | dùng bởi 2 và 4 |
| 2 | `build_rows.py` (r4) | `data/corpus-specs/` | `data/rows-all.jsonl`: 10.381 op học |
| 3 | `build_nhan_hoc_cuoi.py` | nhãn các vòng soát | `data/nhan-hoc-cuoi.csv` |
| 4 | `build_nop.py` | `data/test-specs/` | `data/op-thi.jsonl`: 8.674 op thi |
| 5 | `build_nhan_thi_cuoi.py` | nhãn các vòng soát | `data/nhan-thi-cuoi.csv` |
| 6 | `derive_nodup.py`: học mô hình | `rows-all.jsonl`, `nhan-hoc-cuoi.csv` | `data/stateful-authz-model.csv`, chép vào `EvoMaster/core/src/main/resources/` |
| 7 | `score_thi_nodup.py`: đánh giá trên nửa thi | `op-thi.jsonl`, `nhan-thi-cuoi.csv`, mô hình | `data/ket-qua-nua-thi.txt` |
| 8 | `compare_targets_nodup.py`: đánh giá trên bốn target | spec của target, mô hình | `data/ket-qua-target.out` |

## lib/ — hàm dùng chung

| File | Dùng cho |
|---|---|
| `extract_ops.py` | đọc spec, `deref`, `unwrap_envelope`, liệt kê op |
| `sim.py` | `load_ops`: đọc `rows-all.jsonl` thành op; `leaf`, `gene_kind` |
| `lexlib.py` | `tokens` |
| `derive_model.py` | feature của op và trường, Naive Bayes, bảng role/victim/low/high, ghi CSV |
| `sim_rank.py` | xếp hạng giá trị thấp/cao; `spec_ops` cho target |

## Giới hạn đã biết

- Hạng của artifact-keeper trong `ket-qua-target.out` (3 trong 4) là hạng offline: `victim_field` của script 8 nhận cả
  trường điểm âm. Kotlin chọn 2 trong 3 (`docs/results.md` §1, log TR2).
- Feature Python khác feature Kotlin trên một phần corpus: base path trong `servers`, giá trị enum `EVOMASTER`, kind
  của kiểu `any`. Trên bốn target thì giống nhau: 292/292 op.
