# Đính chính: vampi seed 15 — dao động run-to-run, KHÔNG do trim-restore

Thay thế mục "== vampi seed 15 ==" trong `tr2-analysis.out` (phân tích ban đầu của phiên này SAI). Phiên
`graduational-thesis-54` chỉ ra; đã kiểm lại trực tiếp trên hai log
(`tr2-wave1-20261121/logs/t2-ours-vuln-seed15.log` và `cs2-wave1-20261121/logs/t2-ours-vuln-seed15.log`).

## Bằng chứng

1. **Lượt 2 không chạy ở cả hai lượt.** `grep -c "Privilege-restore"` = 0 ở cả CS2 và TR2 → bước nâng-lại-quyền
   (lượt 2) không thực thi. Thay đổi lượt-2 (một lời nâng mỗi operator) của trim-restore không thể là nguyên nhân hàng này.
2. **Lần thử đầu giống nhau.** Cả hai: victim `name1`, operator `admin`. Khác ở mã **source**:
   - CS2: admin source = **200** (VOID 200/403/200), rồi thử tiếp operator `superadmin` → Assembled 200/200/200 → det970=1.
   - TR2: admin source = **401** (VOID 401/403/401) → dừng, không dựng được bộ ba → det970=0.
3. **Lệch nằm ở pha search, TRƯỚC builder.** "Covered targets" tại cùng mốc ~1.7% ngân sách (dòng ~56 hai log):
   **12 (CS2) vs 24 (TR2)**. `Evaluated tests` cuối: **200 (CS2) vs 201 (TR2)**. Ngân sách tính theo thời gian
   (`--maxTime 150s`) nên số lượt phủ khác nhau giữa hai lượt chạy; builder nhận trạng thái credential khác → source
   200 vs 401.

## Kết luận

vampi 7→6 (seed 15) là **dao động giữa hai lượt chạy do ngân sách time-based**, không phải hiệu ứng của S2 hay R12
(trim-restore). McNemar TR2 vs CS2 vẫn p=1.0; kết luận "trim-restore không đổi số đo so với CS2" còn vững hơn vì hàng
khác biệt duy nhất là nhiễu search, không phải mã.

## Lỗi phân tích ban đầu (ghi lại để không lặp)

`tr2-analysis.out` quy hàng mất cho "lượt 2 rơi vào operator 'admin' thay 'superadmin'" — kết luận từ việc chỉ so dòng
Assembled (CS2) với dòng VOID (TR2), mà CHƯA kiểm: (a) lượt 2 có chạy không (0 Privilege-restore), (b) pha search có
lệch trước builder không (Covered targets 12 vs 24). Bài học: trước khi quy một khác biệt per-seed cho một thay đổi mã,
phải xác nhận đường mã đó có thực thi và loại trừ dao động search time-based.
