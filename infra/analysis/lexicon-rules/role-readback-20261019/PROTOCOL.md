# Trường vai trò có đọc lại được từ phản hồi GET không — giao thức, viết trước lượt chạy

Câu hỏi (user, 2026-10-19): hướng c thay `1, 0, 2` / `0, 1, 2` bằng giá trị đọc từ phản hồi của app (tầng 1). Tầng 1
chỉ có dữ liệu khi app trả bản ghi tài khoản chứa trường vai trò. Đo trên spec: bao lâu thì điều đó có thể xảy ra.

## Đơn vị

Trường vai trò đã gán nhãn trong op T, nhãn vòng 4 (`field-labelling-r4-20261006/final-all.csv`), nạp qua
`p2-model-20261012/derive_model.py`. Chính: 23 trường kiểu số (9 nhà cung cấp). Phụ, để so: mọi kiểu.

## Hai số

- **M1, có thuộc tính cùng tên:** spec có ít nhất một op `GET` mà schema phản hồi 2xx hoặc `default` chứa một thuộc
  tính có tên chuẩn hoá bằng tên lá chuẩn hoá của trường vai trò. Chuẩn hoá như `normalize` của builder
  (`RestSecurityBuilder.kt:1357`): chữ thường, chỉ giữ chữ và số. Duyệt qua `$ref`, `allOf`/`oneOf`/`anyOf`, `items`,
  `additionalProperties`, tối đa 6 tầng.
- **M2, có thể gắn vào một tài khoản:** như M1, và object chứa thuộc tính đó có thêm một thuộc tính kiểu chuỗi mà tên
  chứa `name`, `user`, `login` hoặc `mail`. Danh sách này chỉ dùng cho phép đo, không đi vào mã.

Đếm theo trường và theo nhà cung cấp (nhà cung cấp đạt khi có ít nhất một trường đạt).

## Giới hạn, viết trước

- Đây là cận trên của tầng 1. Lúc chạy còn cần search gọi đúng op `GET` đó, nhận 2xx, và phản hồi có bản ghi của tài
  khoản cần đọc.
- Trùng tên chưa chắc cùng nghĩa: `role` trong phản hồi có thể là một object khác.
- Spec lỗi hoặc không đọc được thì ghi thành một hàng hỏng, không bỏ qua.
- Tầng 2 (giá trị search đã gửi lên transition và nhận 2xx) chỉ đo được lúc chạy, không đo ở đây.
