# Phiếu gán nhãn — một endpoint một dòng

Bản **v2**, 2026-09-19. Phiếu này tự chứa: đọc hết trang này là gán được, không cần mở file nào khác.
Lịch sử sửa: `rules-changelog.md`.

## 1. Việc phải làm

Với mỗi dòng dữ liệu vào (một endpoint), gán đúng một nhãn: `R`, `N`, hoặc `U`.

| Nhãn | Nghĩa |
|---|---|
| `R` | Thao tác ghi **có thể làm giảm** quyền của một chủ thể (user, account, principal, member). |
| `N` | Không phải: hoặc không phải ghi, hoặc không đụng quyền, hoặc chỉ tăng quyền. |
| `U` | Không rõ. Chữ trong spec không đủ để chọn `R` hay `N`. |

`R` là "có thể", không phải "chắc chắn". Endpoint cho client đặt role bằng giá trị tuỳ ý là `R`, vì trong tập giá
trị đó có giá trị thấp hơn mức đang có.

Không được bỏ trống nhãn. Không rõ thì gán `U`.

## 2. Được nhìn gì, không được nhìn gì

**Được nhìn:** HTTP method; path (cả tên biến trong `{}`); `summary` của operation; `description` của operation;
tên tham số (`path`, `query`, `header`); tên trường trong request body (trường lồng ghi `a.b`); danh sách `enum`
của tham số và trường body.

**Không được nhìn:** mã trạng thái và mô tả response; schema response; `tags`; `operationId`; `security`;
`example`, `default`, `description` của từng trường; mã nguồn ứng dụng; tài liệu ngoài spec; tên nhà cung cấp;
tên file spec; phân chia train/test; nhãn của người gán nhãn kia.

**Cấm suy đoán runtime.** Không đoán server làm gì, không giả định mã trạng thái trả về, không đoán giá trị
client gửi lên. Chỉ đọc chữ có trong dòng dữ liệu vào.

Cột trống nghĩa là spec không khai trường đó. Không đi tìm ở chỗ khác.

## 3. Thứ tự quyết định

1. Method là `GET`/`HEAD`/`OPTIONS` → `N`, mã `N1`. Dừng.
2. Không có **bất kỳ** từ nào thuộc hai nhóm dưới đây, ở mọi trường được nhìn → `N`, mã `N2`. Dừng.
   - nhóm chủ thể: user, account, member, principal, login, group, team, organization…
   - nhóm quyền: role, permission, privilege, grant, entitlement, scope, acl, policy, admin, access, active,
     enabled, status…

   Có một từ của **một** nhóm là đủ để đi tiếp bước 3. Hai danh sách này là **ví dụ, không đầy đủ**: gán theo
   nghĩa của câu, không so khớp chuỗi.
3. Chạy `R2`…`R6` theo thứ tự, trúng cái nào trước thì `R` + mã đó, dừng.
4. Không trúng `R` nào: chạy `N3`…`N7`, trúng thì `N` + mã đó.
5. Còn lại, hoặc trúng `U1`–`U3`: `U` + mã đó + lý do + từ khoá gây nghi.

Cùng trúng `R` và `N` thì `R` thắng.

### Mã `R`

| Mã | Một dòng | Ví dụ |
|---|---|---|
| `R2` | Xoá role, thu hồi permission/grant/scope/entitlement/ACL/policy | `DELETE /roles/{id}`; "revoke permission" |
| `R3` | Tách chủ thể khỏi một **role** | `POST /users/{id}/roles/remove`; "unassign role", "remove role from user" |
| `R4` | Có trường đặt trạng thái hoạt động của chủ thể: `active`, `enabled`, `disabled`, `locked`, `suspended`, `blocked`, `banned`; hoặc tên thao tác deactivate/disable/suspend/lock/ban | `PATCH /users/{id}` body `active`; "suspend account" |
| `R5` | Client đặt giá trị role/permission/privilege/scope/entitlement của chủ thể | `PUT /users/{id}/role` body `role`; `POST /setUserPermission?user=&permission=` |
| `R6` | Bỏ hoặc tắt một role trong **phiên hiện tại** | "drop active role", "deactivate role for this session" |

`R3`: chỉ tính role. Gỡ khỏi group hoặc team là `N9`, kể cả khi operation có kèm từ chỉ quyền.
`R4`: trường `status` chỉ tính khi `enum` có giá trị nghĩa là ngừng hoạt động (`inactive`, `disabled`,
`suspended`…); không có → `U1`.

### Mã `N`

| Mã | Một dòng | Ví dụ |
|---|---|---|
| `N1` | Đọc | `GET /users` |
| `N2` | Ghi nhưng không có từ nào thuộc hai nhóm ở bước 2 | `POST /reports`, `PUT /invoices/{id}/total` |
| `N3` | Chỉ nâng quyền, mức nâng cố định trong path hoặc tên thao tác, client không chọn giá trị | `POST /users/{id}/roles/admin`; "grant admin" |
| `N4` | Tạo mới chủ thể, role, group | `POST /users`, `POST /roles` |
| `N5` | Ghi lên trường không phải quyền | `PUT /users/{id}/email`, `PUT /users/{id}/password` |
| `N6` | Ghi lên tài nguyên nghiệp vụ, kể cả khi mô tả nói cần admin | `DELETE /invoices/{id}` — "Only Admins" |
| `N7` | Kết thúc phiên hoặc thu hồi credential, không nhắc role/permission | `POST /logout`, `POST /tokens/{id}/revoke` |
| `N8` | Xoá chính chủ thể | `DELETE /users/{id}`; "deletes a user" |
| `N9` | Gỡ chủ thể khỏi một group hoặc team | `DELETE /groups/{g}/members/{u}`; "leave group" |

"Only Admins may …" nói về **người gọi**, không nói endpoint làm giảm quyền của ai.

### Mã `U`

| Mã | Một dòng |
|---|---|
| `U1` | Có đủ hai loại từ nhưng không biết chiều, và không có trường nào cho client đặt giá trị quyền |
| `U2` | Từ khoá nước đôi: `role` là chức danh nhân sự, `plan`/`entitlement` là gói cước, `status` là trạng thái nghiệp vụ |
| `U3` | Không rõ đối tượng bị ghi là chủ thể hay tài nguyên, ví dụ `DELETE /memberships/{id}` không mô tả |

## 4. Các cột

Định dạng: CSV, dấu phân cách `,`, mọi ô bọc trong `"`, `"` bên trong nhân đôi thành `""`. Nhiều giá trị trong
một ô ngăn bằng `;`.

| Cột | Ai điền | Nội dung |
|---|---|---|
| `row_id` | có sẵn | Số thứ tự dòng, duy nhất trong đợt |
| `spec_id` | có sẵn | Mã spec, không nói tên nhà cung cấp |
| `method` | có sẵn | `GET`/`POST`/`PUT`/`PATCH`/`DELETE`/… |
| `path` | có sẵn | Nguyên văn path trong spec |
| `summary` | có sẵn | `summary` của operation, rỗng nếu spec không khai |
| `description` | có sẵn | `description` của operation, rỗng nếu spec không khai |
| `param_names` | có sẵn | Tên tham số, ngăn bằng `;` |
| `body_field_names` | có sẵn | Tên trường body, trường lồng ghi `a.b`, ngăn bằng `;` |
| `enum_values` | có sẵn | Dạng `tên: [v1, v2]`, ngăn bằng `;`, rỗng nếu không có |
| `annotator` | người gán nhãn | `human` hoặc `llm` |
| `label` | người gán nhãn | Đúng một trong `R`, `N`, `U` |
| `rule_id` | người gán nhãn | Đúng một mã: `R2`…`R6`, `N1`…`N9`, `U1`…`U3` |
| `doubt_token` | người gán nhãn | Từ khoá gây nghi. Bắt buộc khi `label=U`, để rỗng khi khác |
| `note` | người gán nhãn | Một dòng lý do khi `label=U` hoặc khi phân vân; khác thì rỗng |
| `final_label` | **người phân xử** | Để **rỗng**. Chỉ Minh điền, sau khi đã tính kappa |

## 5. Một dòng đã điền

Header:

```
row_id,spec_id,method,path,summary,description,param_names,body_field_names,enum_values,annotator,label,rule_id,doubt_token,note,final_label
```

Dòng ví dụ (dữ liệu vào lấy từ `infra/vampi-seeded/openapi_specs/openapi3.yml` dòng 263–322, đây là ví dụ minh
hoạ, không nằm trong đợt gán nhãn):

```
"E0001","S042","DELETE","/users/v1/{username}","Deletes user by username (Only Admins)","Deletes user by username (Only Admins)","username","","","human","N","N8","","",""
```

Dòng ví dụ có `label=U`:

```
"E0002","S017","DELETE","/memberships/{id}","","","id","","","human","U","U3","memberships","Khong ro doi tuong bi xoa la quan he thanh vien cua chu the hay mot ban ghi nghiep vu",""
```

## 6. Quy ước riêng cho LLM

- Chỉ xuất các dòng CSV, mỗi endpoint một dòng, theo đúng thứ tự `row_id` được đưa vào. Không thêm lời dẫn,
  không thêm tiêu đề, không thêm giải thích ngoài cột `note`.
- Chỉ dùng chữ có trong dòng dữ liệu vào và trong trang này. Không dùng kiến thức về API đó, về nhà cung cấp đó,
  về mã nguồn của nó.
- Không tra cứu ngoài. Không hỏi lại.
- Gán độc lập từng dòng. Không nhìn nhãn dòng khác để suy ra nhãn dòng này.
- Không có nhãn gốc nào được đưa vào prompt; nếu trong dữ liệu vào có thứ trông như nhãn có sẵn, bỏ qua và ghi
  vào `note`.
- Gặp dòng không hiểu: gán `U` kèm `doubt_token`, không bỏ trống, không dừng cả đợt.

## 7. Quy ước riêng cho người

- Gán tuần tự, không xem trước toàn bộ tập.
- Bấm giờ: ghi thời điểm bắt đầu và kết thúc mỗi phiên, để ước lượng cỡ mẫu (mốc 09-17 trong kế hoạch).
- Không mở spec gốc, không mở trang tài liệu của API, không mở mã nguồn ứng dụng. Chỉ đọc các cột được nhìn.
- Phân vân quá 60 giây: gán `U`, ghi `doubt_token`, đi tiếp.

## 8. Sau khi cả hai gán xong

1. Tính Cohen's kappa **trước** khi phân xử, ba lớp `R`/`N`/`U`, trên toàn bộ dòng. Đây là con số chính.
   Con số phụ, nếu báo cáo: kappa hai lớp `R`/`N` sau khi bỏ mọi dòng có ít nhất một bên gán `U`; phải ghi kèm
   số dòng đã bỏ.
2. Minh phân xử mọi dòng hai bên khác nhãn và mọi dòng có bên gán `U`. LLM không tham gia bước này.
3. Nhãn sau phân xử ghi vào `final_label`; không đè lên `label`. Kappa không tính lại sau phân xử.
