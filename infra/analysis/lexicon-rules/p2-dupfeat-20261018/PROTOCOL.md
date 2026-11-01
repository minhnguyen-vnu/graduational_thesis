# Dấu hiệu trùng giữa `p:` và `f:` của bảng `op` — giao thức, viết trước lượt chạy

Câu hỏi (user, 2026-10-18): tham số path `{username}` sinh cả `p:username` lẫn `f:username`, nên điểm transition cộng
cùng một bằng chứng hai lần. Đếm một lần hay hai lần, và nếu một lần thì giữ dấu hiệu nào. User duyệt đo luôn.

## Biến thể

| Biến thể | `p:` lấy từ | `f:` lấy từ |
|---|---|---|
| A, hiện tại (P2e, P2f) | token của toàn bộ path | tên lá của tham số path, query, trường thân |
| B | token của toàn bộ path | tên lá của tham số query, trường thân |
| C | token của path sau khi xoá mọi đoạn `{...}` | tên lá của tham số path, query, trường thân |

`v:` giữ nguyên. Mỗi biến thể học lại trọng số trong từng fold, công thức và `MIN_PROVIDERS = 2` như `derive_model.py`.

## Dữ liệu và kiểm chéo

Như `docs/naive-bayes.md` §3 và `nbcheck_all.py RF`: nhãn vòng 4, 10.381 op, kiểm chéo theo nhà cung cấp 5 phần × 4
lần lặp, seed 20261006, loại 29 spec cũ, bộ lọc nhóm B là `RF`.

Kiểm tự thân: biến thể A phải ra đúng 16 / 16 / 17 / 18 op T đứng đầu và 22 / 21 / 22 / 25 op T trong 4 đầu. Lệch thì
dừng, không đọc số của B và C.

## Bốn số, mỗi lần lặp

| Số | Đơn vị ghép đôi | Thành công |
|---|---|---|
| top-1 | spec test có op T | op T tới được đứng hạng 1 |
| top-4 | spec test có op T | op T tới được đứng trong 4 hạng đầu |
| T > 0 | op T của spec test | điểm > 0 |
| N ≤ 0 | op N của spec test | điểm ≤ 0 |

Spec test của cổng gồm mọi spec ngoài 29 spec cũ, có hay không có op T.

## Kiểm định và luật chọn

- McNemar chính xác hai phía, mỗi lần lặp, mỗi số, V so với A. Bốn số nên ngưỡng p = 0,05 / 4 = 0,0125.
- V tốt hơn A ở một số khi cả 4 lần lặp nghiêng về V và cả 4 có p < 0,0125. V tệ hơn A ở một số khi cả 4 lần lặp
  nghiêng về A và cả 4 có p < 0,0125.
- V thay A khi V tốt hơn ở ít nhất một số và không tệ hơn ở số nào. Không biến thể nào đạt: giữ A, giữ hạn chế đã ghi
  (`docs/naive-bayes.md:94`).
- B và C cùng đạt: chọn biến thể có tổng op T đứng đầu (4 lần lặp) lớn hơn; bằng nhau thì báo user.

## Điều kiện kiểm, không dùng để chọn

Mô hình học trên toàn bộ dữ liệu, mỗi biến thể: transition hạng 1 ở reports, vampi, pyLoad (cách xếp của
`p2-nb-20261012/targets_rf.py`), và `POST /json/edit_package` của pyLoad có điểm < 0. Các target này là target phát
triển.

## Giới hạn

47 spec test đã bị nhìn nhiều lần: p-value là thăm dò. Có 133 op mà tên trong `{...}` khác tên tham số path khai trong
spec, nên B và C bỏ token khác nhau ở các op đó.
