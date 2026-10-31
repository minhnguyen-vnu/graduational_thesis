# Nhãn đổi thì transition của target có giữ được không — giao thức, viết trước lượt chạy

Câu hỏi (user, 2026-10-31): gán lại nhãn có giữ được transition của các app ta đang bắt được không.
Đo offline, không chạy jar nào, không sửa mã EvoMaster.

## Mô phỏng

Học lại bảng `op` và `role` bằng công thức của `p2-model-20261012/derive_model.py`, rồi chấm từng target như builder:
- ứng viên: verb ghi, điểm op > 0 (`RestSecurityBuilder.kt:1196`), giữ thứ tự spec khi hoà;
- khả dụng: có trường không nằm ở path với điểm `role` > 0 (`:1212`);
- `pos`: vị trí của transition thật trong danh sách khả dụng.

Builder tới được khoảng 4 ứng viên: trần 20 lần thử, 5 lần cho mỗi ứng viên chưa chứng minh (`:343`, `:345`). Ứng viên
hỏng nhanh tốn ít lần thử hơn, nên `pos > 4` chưa chắc mất phát hiện.

## Tám target

reports-api, vampi-seeded, pyLoad, Airflow, artifact-keeper, bamf, raouf, magic. Transition: `measure.py` `TARGETS`,
cộng raouf `PUT /v1/users/{id}/role` và magic `DELETE /magic/system/magic/users_roles`.

## Kiểm thiết bị đo

Trên nhãn `final-all.csv`, mô phỏng phải cho trọng số bảng `op` trùng `stateful-authz-model.csv`, và artifact-keeper phải
ra 4 trên 7 như log P2f (`em-results/artifactkeeper-machine-20261014/fixjar-vuln-seed1.log`). Không đạt thì dừng, sửa mô
phỏng trước khi đọc số nào khác.

## Ba phép đo

| Mã | Làm gì | Lặp |
|---|---|---|
| E1 | Thay nhãn đa số bằng nhãn riêng của từng lượt: vòng 3 lấy L1 hoặc L2, vòng 4 lấy LA, LB hoặc LM | 6 tổ hợp |
| E2 | Bootstrap theo nhà cung cấp | 200, seed 20261031 |
| E3 | Lật ngẫu nhiên x% op T thành N và cùng số op N thành T, x = 10, 20, 30 | 100 mỗi mức, seed 20261031 |

E1 là phép gần nhất với một đợt gán lại, vì đó là các lượt gán thật. E3 là nhiễu ngẫu nhiên, không phải sai có hệ thống.

Báo cho mỗi target: tỉ lệ lần lặp có điểm op > 0, tỉ lệ `pos ≤ 4`, trung vị `pos`.

## Giới hạn, viết trước

- Không có dữ liệu của 371 nhà cung cấp mới, nên không đo được tác động của chúng.
- Chỉ chấm thứ hạng và trường vai trò, không chạy EvoMaster: giá trị hạ quyền, source và search không nằm trong phép đo.
- Mọi lượt gán trong E1 đều là model Anthropic và cùng phiếu, nên E1 chưa cho biết phiếu mới làm kết quả đổi tới đâu.
