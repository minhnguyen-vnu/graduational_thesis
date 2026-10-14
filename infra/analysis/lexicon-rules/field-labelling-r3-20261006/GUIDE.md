# Hướng dẫn gán nhãn mức operation (vòng 3)

Mỗi khối `rows/chunk-NNN.txt` chứa tối đa 75 operation ghi (POST, PUT, PATCH, DELETE) của các REST API công khai.
Mỗi operation: mã dòng, method, path, mô tả (400 ký tự đầu), `schema:` tên schema của body nếu có, rồi danh sách trường
`vị trí:tên kiểu enum[...]`. Trường lồng ghi `a.b`, phần tử mảng ghi `a[].b`.

## Câu hỏi cho mỗi operation

**T = 1** khi operation này cấp, đổi hoặc gỡ vai trò, quyền, hoặc tư cách admin của **một tài khoản người dùng đã tồn
tại**, và tài khoản đó được chỉ định trong chính request (path, query hoặc body), hoặc là chính người gọi.

Tính là T = 1:
- đặt hoặc đổi role, quyền, cấp truy cập, cờ admin của một user, member, collaborator, account;
- gán hoặc gỡ một role, một quyền cho một user (kể cả khi role nằm trên path);
- đổi vai trò của một thành viên trong tổ chức, dự án, nhóm, repo, workspace.

Tính là T = 0 (ghi mã phụ ở cột `sub` nếu operation có trường kiểu vai trò/quyền):
- `def`: định nghĩa hoặc sửa quyền của một role, nhóm quyền, policy (không chỉ định user);
- `cred`: tạo hoặc sửa token, API key, client, app và scope của nó;
- `nonuser`: gán vai trò cho chủ thể không phải tài khoản người dùng (group, client, API key, service, device);
- `create`: tạo mới hoặc mời một user (kể cả khi kèm role);
- `status`: khoá, mở khoá, kích hoạt, vô hiệu, xoá user mà không đổi vai trò;
- `resource`: quyền hoặc chia sẻ trên một tài nguyên mà không đổi vai trò của user trong hệ thống (ví dụ chia sẻ file
  cho user, ACL của một tài liệu). Nếu operation đặt cấp truy cập của một user cụ thể lên một repo, dự án, workspace,
  tổ chức thì là T = 1, không phải `resource`.
- để trống nếu không có trường nào kiểu vai trò/quyền.

## Cột cần điền khi T = 1

- `victim`: các trường chỉ tài khoản bị tác động, ghi đúng `vị trí:tên` như trong khối, ngăn cách bằng `|`.
  Ghi `self` nếu đối tượng là chính người gọi (ví dụ `/me`). Để trống nếu request không chỉ ra.
- `role`: các trường mang giá trị vai trò, quyền hoặc cờ admin mới, ghi `vị trí:tên`, ngăn cách bằng `|`. Mảng quyền
  mà phần tử là object thì ghi trường mảng (`body:roles`), không ghi trường con. Để trống nếu thao tác không mang giá
  trị (ví dụ `DELETE /orgs/{org}/admins/{user}`).
- `order`: nếu một trường `role` có enum: các giá trị từ quyền thấp tới quyền cao, ngăn cách bằng `<`, giá trị ngang
  nhau ghi chung bằng `=`; ghi `unordered` nếu không xếp được. Bỏ qua giá trị không phải quyền (`none` vẫn là mức thấp
  nhất nếu nghĩa là không có quyền). Để trống nếu không có enum.

## Đầu ra

`<thư mục của bạn>/chunk-NNN.csv`, header `row_id,T,victim,role,order,sub`, **một dòng cho mọi operation trong khối**,
kể cả T = 0. Đọc hết mọi dòng của khối; khối dài thì đọc theo đoạn. Không lọc bằng grep. Giá trị có dấu phẩy thì đặt
trong ngoặc kép.

Ví dụ:
```
row_id,T,victim,role,order,sub
S900-0001,1,path:username,body:role,viewer<editor<admin,
S900-0002,0,,,,def
S900-0003,1,path:userId,body:isAdmin,,
S900-0004,0,,,,
S900-0005,1,path:username,,,
```
S900-0005 là `DELETE /orgs/{org}/owners/{username}`: `path:org` không chỉ tài khoản nên không ghi vào `victim`.
