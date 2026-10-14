# Chuỗi jar `ER-06b48c30` (ghi 13:03 09-30, trước khi chạy)

Jar `EvoMaster/evomaster-ER-06b48c30.jar` = jar `NR-3c087e58` + low-priv (`wip/lowpriv-20260930.patch`, self-test
`low-priv-current.sh` 6/6 trên jar `LP-3cc44770`) + tham số `email` (`wip/email-param-20260930.md`) + mảng vai trò rỗng
(`wip/empty-roles-20260930.md`, self-test `empty-roles.sh` 10/10). Cây `fe0dca8a`, rollback diễn tập 13:05, trùng byte.
Self-test num-role, role-value, victim-id chạy trên jar `LP-3cc44770` (33/33 cùng low-priv), không chạy lại trên jar ER:
hai sửa sau chỉ thêm nhóm `email` sau các tên cũ và giá trị `[]` cho mảng vai trò; gate và seeds kiểm hồi quy.
Bọc `caffeinate -dims`; dòng có `Entering Sleep` thì dừng.

A. bamf seeds 1–10 (target phát triển), `bamf-dev-20260930d/`: target mới mỗi seed, chế độ `dotless`, spec bỏ 4 phần
   (§12 lệch luật 3–7), `--maxTime 600s`, rate 600. Dừng seed 1 nếu 0 lần thử bộ ba, thiếu đăng nhập một tài khoản,
   < 237 test, EvoMaster exit khác 0.
B. Gate 21 dòng (`core/target/evomaster.jar` = jar ER). Dừng chuỗi nếu có dòng bản đã sửa lệch.
C. Seeds 1–10: Tier-1, Tier-2 bản lỗi và bản đã sửa, pyLoad; cờ như `numrole-chain-20260930`.
   Dừng sớm: Tier-1 bản lỗi seeds 1–3 đều không có 970.
D. Truthy seeds 1–10 (`truthy-dev-20260930c/`).
Sao lưu sau C và D.

So sánh sau chạy: seeds 1–10 với jar `VI` từng dòng (970, bộ ba, VOID, mã); Tier-1 seed 10 là dòng jar NR mất.
