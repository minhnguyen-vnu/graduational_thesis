# Patch: cổng chặn đọc thêm tên trường thân yêu cầu

Chưa áp, chưa build. Cần OK trước khi `git apply`.

- Patch: `field-gate-20260923.patch`, `git apply --check -p1` đã qua trên cây làm việc hiện tại (jar `L`).
- Luật: `infra/analysis/lexicon-rules/rules-draft.md` §13, viết 12:42 ngày 09-23 trước khi đo.
- Số đo: `infra/analysis/lexicon-rules/field-gate-20260923/RESULTS.md`.
- Self-test: `infra/evomaster-ext/selftest/field-gate.sh`.
- File từ vựng **không đổi**. Patch này không thêm dữ liệu, chỉ đổi chuỗi được đem so.

## Sửa gì

| Chỗ | Trước | Sau |
|---|---|---|
| `:94` companion | không có | `bodyFieldNames(a)`, lấy tên trường cấp một của mỗi `BodyParam` |
| `:102` companion | không có | `transitionHay(a)` = `path + " " + verb:path + " " + tên trường`, lowercase |
| `:123` `looksLikePermissionReducingTransition` | `hay` dựng tại chỗ từ path và verb | gọi `transitionHay(a)` |
| `:857` instance `transitionHay` | bản riêng, chỉ path và verb | xoá, dùng bản companion |

Một định nghĩa chuỗi so cho cả hai chỗ. Trước patch, cổng của companion và hàm xếp hạng của instance dựng
chuỗi giống nhau bằng hai đoạn mã khác nhau.

## Đo được gì

| | Nửa train top-1 | Nửa test top-1 | Airflow |
|---|---|---|---|
| 8 từ cứng (trước jar `L`) | | | **không qua cổng** |
| V0, đang chạy trong jar `L` | 0.500 | 0.500 | hạng 4–13, điểm 0.2000 |
| **V1, patch này** | **0.500** | **0.667** | **hạng 1–5, điểm 0.3000** |

Ba target của luận văn giữ hạng 1 dưới V1 (Tier-1, Tier-2, pyLoad).
Biến thể V1 được chọn bằng luật phá hoà khai ở §13.4 trên nửa train, không bằng con số nửa test.

Biến thể V2 (bộ từ vựng `field` riêng, lấy max) bị loại: nửa test tụt xuống 0.333, S116 từ hạng 1 xuống 24–27.

## Chỗ phải soi

**Cổng này cũng gác phán quyết.** `RestSecurityOracle.kt:583` và `:602` gọi cùng
`looksLikePermissionReducingTransition`. Mở rộng chuỗi so làm rộng cả bộ lọc dựng bộ ba lẫn bộ lọc phán quyết.
Một endpoint có trường thân trúng từ nay vừa được chọn làm transition vừa được oracle công nhận là
transition. Hai mươi lần chạy bản đã vá là chỗ kiểm chứng: nếu có báo động giả, nó hiện ở đó.

**Số ứng viên qua cổng tăng.** Tier-1 từ 1 lên 2, pyLoad từ 8 lên 17, Airflow từ 17 lên 37.
Hôm nay không tốn gì vì `MAX_TRANSITION_CANDIDATES = 8` chưa có tác dụng lúc chạy. Nếu `local-harvest-20260923`
cũng vào thì mỗi ứng viên thêm là một lần dựng bộ ba, và con số này thành chi phí thật.

**Tên trường cấp một, không phải cả cây.** `bodyFieldNames` lấy `fields` của `ObjectGene` ngoài cùng, đúng
định nghĩa `body_field_names` của `extract_ops.py` mà số đo dựa vào. Mã xung quanh trong file này
(`setInParams`) duyệt cả cây bằng `flatView()`; chỗ này cố ý không làm thế, để chạy đúng luật đã đo.
Khác một chỗ: corpus bóc vỏ JSON:API (`data`/`attributes`), EvoMaster không.

## Chưa chứng minh

- Chưa build, chưa self-test, chưa qua cổng hồi quy, chưa chạy seed nào.
- Ba target và Airflow xếp hạng từ spec tĩnh, không phải từ `actionDefinitions` của EvoMaster.
- Chưa lần chạy EvoMaster nào trên Airflow. Kết luận "qua cổng" là kết luận trên giấy.
