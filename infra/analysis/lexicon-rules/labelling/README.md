# Gán nhãn — hai spec bấm giờ, tối 2026-09-17

Mục đích: đo mất bao lâu để gán nhãn một operation, từ đó chốt cỡ mẫu cho cả đợt.

## 1. Bạn mở đúng hai thứ

- `infra/analysis/lexicon-rules/labelling-form.md` — phiếu, tự đủ, không cần đọc gì khác.
- File CSV của spec đang làm.

Không mở `rules-draft.md`, không mở spec gốc, không mở Google. LLM gán nhãn cũng chỉ được đúng hai thứ trên,
hai bên nhìn lệch nhau thì kappa mất nghĩa.

## 2. Quy trình đã đổi, 2026-09-17

Người không gán toàn bộ nữa. Hai lượt LLM gán mù trước (L1, L2, khác model, không thấy nhau), rồi người gán
tầng lệch cộng 20% mẫu soát bốc từ tầng trùng. Luật đầy đủ ở `rules-draft.md` §9.

Điền bốn cột: `annotator` ghi `human`, `label` ghi `R`/`N`/`U`, `rule_id` ghi đúng một mã, `note` chỉ khi `U`.
Các cột khác để nguyên. Không quay lại sửa dòng đã điền sau khi đã xem dòng sau; nghĩ lại thì ghi vào `note`.

Ba dòng `S034-0001`, `S034-0002`, `S034-0003` đã gán tối 2026-09-17 theo quy trình cũ. Giữ lại làm nhãn người,
nhưng không được tính vào mẫu soát: mẫu soát chỉ gồm dòng bốc theo hạt giống `20260918`. Dòng `S034-0002` còn một
chỗ lệch nữa: lúc đưa dòng đó ra, hai tên trường `enabled` và `secured` bị in đậm, tức người gán được chỉ chỗ.
Viết vào phần hạn chế khi báo cáo kappa.

## 3. Đồng hồ

Không dừng đồng hồ giữa chừng. Đứng dậy đi đâu thì ghi số phút vào `breaks_minutes`.
Làm không hết thì vẫn ghi `rows_done` bằng số dòng đã điền; tốc độ tính trên số đó.

Tốc độ cần đo là tốc độ trên tầng người thực sự phải gán, tức tầng lệch cộng mẫu soát. Ba dòng đầu tiên đo được
245 s/dòng nhưng số đó gồm cả thời gian đọc luật lần đầu, không dùng để chốt cỡ mẫu.

## 4. Một con số nữa cần bạn cho

Bạn định bỏ tổng cộng bao nhiêu giờ cho việc gán nhãn cả đợt. Ghi vào `note` của dòng đầu trong `timing.csv`.
Không có con số đó thì không tính được cỡ mẫu.

## 5. Hai spec này là gì

Bốc theo luật phân tầng, hạt giống cố định `20260917`, khai báo trước khi bốc:
30 spec WFD có operation ghi chia hai tầng theo việc có hay không có operation lọt cổng `G2`;
mỗi tầng bốc một spec.

| File | Tầng | Operation ghi | Lọt cổng G2 |
|---|---|---|---|
| `S034.human.csv` | A | 14 | 11 |
| `S008.human.csv` | B | 10 | 0 |

Tầng A đo tốc độ áp quy tắc `R`, tầng B đo tốc độ loại nhanh ở cổng.

Lần bốc đầu tiên, trước khi có luật phân tầng, ra `rest-news.json` và `familie-ba-sak.json`. Bỏ lần bốc đó vì
cả hai đều không có operation nào lọt cổng, đo giờ sẽ không đo được phần đắt nhất của công việc. Ghi lại ở đây
để ai đọc cũng thấy có một lần bốc bị bỏ và vì sao.

Tên thật của spec nằm ở `infra/analysis/corpus/spec-map.csv`. Đừng mở lúc đang gán nhãn.

## 6. Một chỗ lệch giữa hai người gán nhãn, khai báo trước

LLM chạy trong thư mục dự án nên `CLAUDE.md` vẫn nằm trong ngữ cảnh của nó. File đó không chứa quy tắc gán nhãn
và không chứa nhãn mẫu nào, nhưng có mô tả oracle và bộ từ vựng cũ. Bạn thì không đọc `CLAUDE.md` lúc gán nhãn.
Đây là một chỗ lệch có lợi cho LLM, phải viết vào phần hạn chế khi báo cáo kappa.
