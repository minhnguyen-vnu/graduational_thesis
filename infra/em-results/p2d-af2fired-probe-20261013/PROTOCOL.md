# P2d trên các hàng AF2 nổ, 2026-10-13

Jar `EvoMaster/evomaster-P2d-2e0dbd4d.jar`. Thay phần còn lại của remeasure P2d đã dừng
(`p2d-night-20261012/STOPPED.md`). Mục đích: tìm lỗi khác ngoài lỗi restore `EVOMASTER` trước khi viết sửa C.
Không trích số từ batch này.

## Hàng

Các hàng có det970 = 1 trên AF2 (`af2-full-remeasure-20261003/runs.csv`) mà remeasure P2d chưa chạy, rút gọn
theo user (11:33, trước khi có hàng nào; lần khởi động đầu không ghi hàng, lưu ở `archive-start1/`):

| Thứ tự | Arm | Seed | Lượt | Đường AF2 đi qua |
|---|---|---|---|---|
| 1 | vampi ours-vuln :5002 có reset | 1 3 5 7 8 9 10 11 12 16 17 19 20 | 13 | không restore (0 lượt ở cả 13 hàng) |
| 2 | pyLoad vuln :8090 không reset | 1–3 | 3 | restore 1 lượt thành công mỗi hàng |

Bỏ pyLoad vuln có reset và seeds 4–5 không reset. Mỗi lượt pyLoad mất ~18,7 phút trên AF2. Năm hàng AF2
không reset giống nhau (assembled 1, VOID 2, restore 1/0, 200/200/200), nên một lỗi có hệ thống hiện ra ngay ở
3 seed đầu. Lỗi phụ thuộc seed còn sót sẽ lộ ra ở lượt đo đầy đủ sau sửa C.

Hàm `t2`, `t2b` trùng từng byte với `af2_full_remeasure.sh` (đã diff); chỉ `JAR` và `BASE` khác.

## Luật dừng (viết trước lượt chạy)

Kiểm sau mỗi hàng:
- 2 hàng liên tiếp det970 = ERR trong một arm;
- 3 hàng đầu của một arm đều assembled = 0;
- 3 hàng đầu của một arm đều det970 = 0;
- có `Entering Sleep` mới trong `pmset -g log`.

Luật nổ thì dừng batch, ghi lệch luật, tìm nguyên nhân trong log.

## Sau batch

So từng hàng với AF2 cùng arm, cùng seed. Hàng nào lệch: so các dòng restore, VOID, Assembled với log AF2 cùng
seed. Nếu các dòng đó chưa đủ chỉ ra nguyên nhân, chạy lại đúng seed đó trên cả AF2 và P2d với log builder mức
`debug`, như `p2c-vs-af2-debug-20261012/`.
