# Dấu hiệu trùng giữa `p:` và `f:` — kết quả, 2026-10-18

Giao thức: `PROTOCOL.md`, viết trước lượt chạy. Lệnh: `python3 dupcheck.py` (ra `dupcheck.out`), `python3 posthoc.py`
(ra `posthoc.out`), chạy trong thư mục này. Đo offline trên nhãn, không chạy jar nào. Kiểm tự thân qua: biến thể A ra
đúng 16 / 16 / 17 / 18 và 22 / 21 / 22 / 25 như `docs/naive-bayes.md` §3.

## 1. Theo luật đã chốt: chọn B

Mỗi ô là bốn lần lặp. p là McNemar chính xác hai phía so với A; ngưỡng 0,0125.

| Số | A | B | p, B so A | C | p, C so A |
|---|---|---|---|---|---|
| op T đứng đầu /47 | 16 / 16 / 17 / 18 | 16 / 16 / 16 / 17 | 1 / 1 / 1 / 1 | 14 / 14 / 15 / 15 | 0,50 / 0,63 / 0,63 / 0,25 |
| op T trong 4 đầu /47 | 22 / 21 / 22 / 25 | 22 / 21 / 22 / 24 | 1 / 1 / 1 / 1 | 22 / 20 / 21 / 24 | 1 / 1 / 1 / 1 |
| op T điểm > 0 /152 | 127 / 125 / 123 / 126 | 118 / 121 / 117 / 119 | 0,004 / 0,22 / 0,031 / 0,016 | 117 / 123 / 113 / 120 | 0,002 / 0,63 / 0,013 / 0,031 |
| op N điểm ≤ 0 /8.652 | 7.704 / 7.674 / 7.519 / 7.733 | 7.885 / 7.892 / 7.758 / 7.913 | < 0,0001 ×4 | 7.893 / 7.866 / 7.808 / 7.898 | < 0,0001 ×4 |

- B và C tốt hơn A ở op N điểm ≤ 0: cả 4 lần lặp, p < 0,0001.
- Op T điểm > 0 nghiêng về A ở cả 4 lần lặp với cả B và C. p < 0,0125 ở 1 trên 4 lần lặp, nên theo luật B và C không
  tệ hơn.
- B và C cùng đạt. Tổng op T đứng đầu: B 65, C 58. Luật chọn B.

## 2. Hậu kiểm, ngoài giao thức: B tương đương A với ngưỡng cao hơn

Viết sau khi thấy §1. Lý do: luật đo cổng ở ngưỡng cố định 0, mà bỏ dấu hiệu trùng làm tụt điểm của mọi op có tham số
path, tức là dời điểm vận hành. Luật không có phép kiểm tách hai việc này.

| Lần lặp | AUC A | AUC B | AUC C | Op N > 0 của B | Op N vượt ngưỡng của A, ngưỡng chọn để A giữ đúng số op T của B |
|---|---|---|---|---|---|
| 1 | 0,910 | 0,904 | 0,903 | 767 | 708 (ngưỡng 0,706) |
| 2 | 0,909 | 0,910 | 0,911 | 760 | 836 (ngưỡng 0,426) |
| 3 | 0,905 | 0,900 | 0,889 | 894 | 858 (ngưỡng 0,531; A giữ 118 op T, B 117) |
| 4 | 0,910 | 0,908 | 0,910 | 739 | 762 (ngưỡng 0,481) |

- AUC của ba biến thể chênh nhau tối đa 0,016.
- Cùng số op T vượt cổng, A để lọt ít op N hơn B ở lần lặp 1 và 3, nhiều hơn ở lần lặp 2 và 4.
- Ở ngưỡng 0, op có điểm > 0 là op T với tỉ lệ 9,8–12,1% (A) và 11,6–13,9% (B). Điểm > 0 chỉ là hậu nghiệm > 0,5
  trong mô hình; trên dữ liệu test, cả A và B đều thổi hậu nghiệm lên.

## 3. Trên target, mô hình học trên toàn bộ dữ liệu

| Biến thể | Số dấu hiệu | reports `PUT /users/{username}/role` | vampi | pyLoad `set_user_permission` | pyLoad `edit_package` |
|---|---|---|---|---|---|
| A | 166 | hạng 1, +8,504 | hạng 1, +8,504 | hạng 1/3, +5,613 | −4,581 |
| B | 153 | hạng 1, +6,707 | hạng 1, +6,707 | hạng 1/3, +5,548 | −4,615 |
| C | 152 | hạng 1, +6,587 | hạng 1, +6,587 | hạng 1/3, +2,959 | −4,581 |

Cả ba biến thể qua điều kiện kiểm.

Trên toàn bộ op ghi của ba target (`targetgate.py`, ra `targetgate.out`), tập op điểm > 0 trùng nhau ở A, B, C:
reports 1/6, vampi 6/8, pyLoad 4/62. Thứ tự chỉ đổi ở vampi:

| Hạng | A | B | C |
|---|---|---|---|
| 1 | `PUT …/role` | `PUT …/role` | `PUT …/role` |
| 2 | `PUT …/email` | `PUT …/email` | `POST /users/v1/register` |
| 3 | `PUT …/password` | `PUT …/password` | `PUT …/email` |
| 4 | `DELETE /users/v1/{username}` | `POST /users/v1/register` | `PUT …/password` |
| 5 | `POST /users/v1/register` | `DELETE /users/v1/{username}` | `POST /users/v1/login` |
| 6 | `POST /users/v1/login` | `POST /users/v1/login` | `DELETE /users/v1/{username}` |

Chưa chạy EvoMaster với B hay C.

## 4. Kết luận

- Theo luật viết trước: chọn B. Cái được là ít op N lọt cổng hơn (180–239 trên 8.652); cái mất là 4–9 trên 152 op T
  không qua cổng. Xếp hạng không đổi.
- Theo hậu kiểm: B không phân biệt T với N tốt hơn A. Phần được ở cổng của B có được bằng cách nâng ngưỡng của A.
- Chưa sửa mã. Đổi sang B cần sửa `derive_model.py` và `opFeatures`, học lại mô hình, dựng jar, chạy cổng 21 hàng, đo
  lại các arm.

## 5. Giới hạn

- 47 spec test đã bị nhìn nhiều lần: p-value là thăm dò.
- Hậu kiểm ở §2 viết sau khi thấy kết quả §1.
- Giao thức có lỗi đã biết trước khi chạy: trả lời trước đó trong cùng phiên đã nêu rằng bỏ dấu hiệu tương đương dời
  ngưỡng, nhưng luật vẫn chỉ đo cổng ở ngưỡng 0.
