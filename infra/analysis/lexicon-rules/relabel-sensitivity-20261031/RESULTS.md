# Nhãn đổi thì transition của target có giữ được không — kết quả, 2026-10-31

Giao thức: `PROTOCOL.md`, viết trước lượt chạy. Lệnh: `python3 sensitivity.py`, ra `sensitivity.out`. Offline, không chạy
jar nào. Kiểm thiết bị đo đạt: 166 dấu hiệu `op` trùng `stateful-authz-model.csv`, lệch lớn nhất 0; artifact-keeper ra 4
trên 7 như log P2f.

## 1. Kết luận

- Mọi phép đo, 8/8 target: điểm op của transition luôn > 0.
- reports, vampi, pyLoad, Airflow, bamf đứng đầu ở cả 6 tổ hợp lượt gán. magic đứng đầu ở 5 trên 6, hạng 2 ở tổ hợp còn lại.
- artifact-keeper là chỗ yếu về xếp hạng: 4/7, 4/7, 4/7, 4/8 và 6/11 hai lần.
- raouf là chỗ yếu về trường vai trò: 4 trên 6 tổ hợp không nhận ra `roleCode`. raouf vốn đã 0 bộ ba khi chạy tự động,
  nên đây không phải một phát hiện bị mất.

## 2. E1, nhãn riêng của từng lượt gán, pos / số ứng viên khả dụng

| Vòng 3 + vòng 4 | Op T | reports | vampi | pyLoad | Airflow | artifact-keeper | bamf | raouf | magic |
|---|---|---|---|---|---|---|---|---|---|
| L1 + LA | 175 | 1/1 | 1/1 | 1/3 | 1/4 | 4/7 | 1/3 | 1/2 | 1/2 |
| L1 + LB | 145 | 1/1 | 1/1 | 1/3 | 1/2 | 4/8 | 1/3 | 1/2 | 2/3 |
| L1 + LM | 174 | 1/1 | 1/1 | 1/3 | 1/2 | 6/11 | 1/3 | -/0 | 1/3 |
| L2 + LA | 205 | 1/1 | 1/1 | 1/3 | 1/4 | 4/7 | 1/3 | -/1 | 1/2 |
| L2 + LB | 175 | 1/1 | 1/1 | 1/3 | 1/2 | 4/7 | 1/3 | -/1 | 1/2 |
| L2 + LM | 204 | 1/1 | 1/1 | 1/3 | 1/2 | 6/11 | 1/3 | -/0 | 1/3 |

## 3. E2 và E3, số lần `pos ≤ 4`

| Target | E2 bootstrap /200 | E3 lật 10% /100 | E3 lật 20% /100 | E3 lật 30% /100 |
|---|---|---|---|---|
| reports-api | 200 | 100 | 100 | 100 |
| vampi-seeded | 200 | 100 | 100 | 100 |
| pyLoad | 198 | 100 | 100 | 100 |
| Airflow | 192 | 100 | 100 | 100 |
| artifact-keeper | 146 | 95 | 85 | 73 |
| bamf | 192 | 100 | 100 | 100 |
| raouf | 108 | 38 | 26 | 26 |
| magic | 197 | 100 | 100 | 100 |

## 4. `pos ≤ 4` là ngưỡng thận trọng

Trên P2f, cả 5 seed của artifact-keeper dùng đúng 10 lần thử bị loại trước bộ ba đầu tiên ở ứng viên 4
(`em-results/artifactkeeper-machine-20261014/fixjar-vuln-seed*.log`), và seed 1 còn đi hết 7 ứng viên. Ứng viên hỏng nhanh
tốn ít hơn 5 lần thử, nên trần 20 lần tới xa hơn 4. Seed 1 tốn 2, 3, 4 lần ở ba ứng viên đầu, và nổ ở lần thứ hai của ứng viên 4, tức lần thử 11.

Ngoại suy cho vị trí 6, chưa được đo: thêm hai ứng viên đứng trước, mỗi ứng viên tốn 3 lần thì bộ ba ở lần 17; mỗi ứng
viên tốn đủ trần 5 lần thì ở lần 21, quá trần 20 một lần.

## 5. Giới hạn

Như `PROTOCOL.md`. Các lượt gán của E1 cùng một phiếu; một phiếu mới có thể làm kết quả đổi nhiều hơn.
