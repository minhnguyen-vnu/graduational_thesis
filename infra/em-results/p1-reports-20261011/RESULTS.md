# P1 trên reports-api — kết quả

Jar `EvoMaster/evomaster-P1-80024675.jar`. Chạy 2026-10-11 18:03:53–21:16:46, 40 hàng, `caffeinate -dims`; `pmset -g log`
có 185 dòng trong khoảng này, không có `Entering Sleep` nào (lần cuối 09:18:03). Jar chưa qua cổng hồi quy: không trích số
từ thư mục này.

## Kết luận

Cả 40 hàng trùng hàng tương ứng của `af2-full-remeasure-20261003/runs.csv` ở mọi cột chung: `det970`, `assembled`,
`void_count`, `resets`, `restores_ok`, `restores_no`, `faults`, và chuỗi `statuses` tính lại từ dòng Assembled.

| Arm | 970 nổ | Lần thử mỗi lượt |
|---|---|---|
| vuln, không reset | 10/10 | 1 (seed 1–3, 5–7), 3 (seed 4, 8–10) |
| fixed, không reset | 0/10 | 1 (seed 1–3, 5–7), 3 (seed 4, 8–10) |
| vuln, có reset | 10/10 | 1 |
| fixed, có reset | 0/10 | 1 |

- Luật mới không chạm vào lượt nào: `cut5`, `refused`, `revoked` bằng 0 ở cả 40 hàng; `proven` bằng 1 ở cả 40 hàng.
  reports-api có một op khả dụng, và bộ ba hợp lệ đầu tiên tới ở lần thử 1 hoặc 3.
- Soát cấu trúc (`audit970.out`): 20/20 test 970 qua, 0 trượt; 20 lượt fixed có một bộ ba hợp lệ không nổ. Trùng từng hàng
  với `af2-full-remeasure-20261003/audit970.out`.
- Toàn vẹn: không có 970 nào thiếu bộ ba hợp lệ; không có stack trace của `org.evomaster` trong log.
- Chưa replay các test 970.

## Lệch so với protocol

- Cột `statuses` trong `runs.csv` có hai mục cho mỗi bộ ba vì dòng log mới "proven by an attempt with statuses …" cũng
  khớp mẫu đếm của harness. Không sửa harness giữa chừng; phép so ở trên tính lại chuỗi từ dòng Assembled.
