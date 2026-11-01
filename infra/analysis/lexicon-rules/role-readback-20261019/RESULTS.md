# Trường vai trò có đọc lại được từ phản hồi GET không — kết quả, 2026-10-19

Giao thức: `PROTOCOL.md`, viết trước lượt chạy. Lệnh: `python3 readback.py` trong thư mục này, ra `readback.out`.
Đo trên spec, offline, không chạy jar nào. Không spec nào hỏng.

## 1. Trường vai trò kiểu số: 23 trường, 9 nhà cung cấp

| | Trường /23 | Nhà cung cấp /9 |
|---|---|---|
| M1, script | 15 | 6 |
| M2, script | 14 | 5 |
| M2 sau khi đọc tay đường dẫn khớp | 11 | 4 |

Đọc tay viết sau khi thấy số script: 3 trường `id` của atlassian khớp `GET /rest/api/3/application-properties`, không
phải bản ghi tài khoản; bungie khớp `/CommunityContent/…` và đã trượt M2.

| Nhà cung cấp | Trường | GET trả bản ghi tài khoản có trường đó | Giá trị là |
|---|---|---|---|
| gitlab.com | `access_level` ×6 | `GET /v3/groups/{id}/members` | cấp |
| noosh.com | `role_id` ×2 | `GET /v1/workgroups/{workgroup_id}/projects/{project_id}/memberroles/{user_id}` | id object vai trò |
| appveyor.com | `roleId` ×2 | `GET /collaborators` | id object vai trò |
| watchful.li | `groupid` ×1 | `GET /ssousers` | id nhóm |

12 trường không có:

| Nhà cung cấp | Trường | Vì sao |
|---|---|---|
| jira.local | `id` ×5 (path, `/role/{id}`) | spec không khai schema phản hồi: 0 trên 153 op GET |
| atlassian.com | `id` ×3 (path) | chỉ khớp nhầm `application-properties` |
| dracoon.team | `role_id` ×2 (path) | phản hồi có object vai trò nhưng gọi khoá là `id`, khác tên trường |
| sinao.app | `policy_profile_id` | không GET nào trả thuộc tính cùng tên |
| bungie.net | `memberType` (path) | chỉ khớp một object nội dung, không có tên tài khoản |

16 trên 23 trường là id của một object vai trò hoặc nhóm (`role_id`, `roleId`, `groupid`, `policy_profile_id`, `id`);
6 là cấp (`access_level`); 1 là mã loại thành viên (`memberType`).

pyLoad không nằm trong corpus. Theo spec, `GET /api/get_all_userdata` trả `name`, `role`, `permission` cho từng tài
khoản, nên pyLoad đạt M2.

## 2. Để so: mọi kiểu trường vai trò, script, chưa đọc tay

| Kiểu | Trường | M1 | M2 |
|---|---|---|---|
| bool | 66 | 52 | 47 |
| chuỗi | 39 | 23 | 23 |
| mảng | 28 | 25 | 22 |
| số | 23 | 15 | 14 |
| enum | 21 | 18 | 18 |
| object | 7 | 5 | 5 |
| tổng | 184 | 138 | 129 |

Theo nhà cung cấp: M1 42/52, M2 38/52. Tên chung như `id` làm số script cao hơn thật, như ở §1.

## 3. Giới hạn

- Cận trên của tầng 1: lúc chạy còn cần search gọi đúng op GET đó, nhận 2xx, và phản hồi có bản ghi của tài khoản cần
  đọc. Ngược lại, spec không khai schema phản hồi (jira.local) thì đo ra 0 dù app có thể vẫn trả dữ liệu.
- Khớp theo tên trường: dracoon có dữ liệu vai trò nhưng tên khoá khác, nên cả phép đo này lẫn builder đều không thấy.
- Đọc tay ở §1 là một người đọc, viết sau khi thấy số script.
- Tầng 2 chỉ đo được lúc chạy.
