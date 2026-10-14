# Giá trị hạ "mảng vai trò rỗng" — 2026-09-30

Cây trước: `95ddb7b4` (jar `EP-9007f79a`), lưu ở `pre-emptyroles-20260930.patch`. Cây sau: `fe0dca8a`
(`emptyroles-20260930.patch`), jar `EvoMaster/evomaster-ER-06b48c30.jar`, build 12:37. Self-test: `selftest/empty-roles.sh`.
Nguồn lỗi: self-test `email-param.sh` lần 3 trên bamf (`em-results/emailparam-selftest-20260930-120947/`).

## Lỗi

bamf, transition `PATCH /api/v1/users/{email}`, body `UserUpdate.roles` là mảng tên vai trò có thật. Giá trị hạ
`[user, viewer, guest, member, basic]` (danh sách chuỗi cố định) không có vai trò nào tồn tại: 10 lần transition 400
(`Role 'user' not found`), bộ ba VOID `200/400/200`. Bamf nhận `{"roles": []}` (gỡ hết vai trò, kiểm tay 09:35).

## Sửa

| Chỗ | Làm gì |
|---|---|
| `roleArrays` | Các `ArrayGene` trong body có tên khớp `roleFieldSignals` và `minSize` 0. |
| `harvestReducedRoleCandidates` | Transition có mảng vai trò thì thêm giá trị `[]`, sau các giá trị enum quyền thấp, trước giá trị số và chuỗi. |
| `setRoleFieldToReduced`, `clearRoleArrays` | Giá trị `[]`: xoá hết phần tử của mảng vai trò, bật các wrapper cha (`OptionalGene`, `NullableGene`, chọn nhánh `ChoiceGene`). |

Theo luật 09-17, gỡ một subject khỏi vai trò là thao tác hạ quyền.
Tier-1, Tier-2, pyLoad: trường vai trò không phải mảng, danh sách giá trị không đổi.

## Giới hạn

- Chỉ hạ được về "không vai trò"; hạ từ `admin` xuống một vai trò thấp hơn có tên riêng vẫn cần giá trị enum hoặc giá trị
  đọc từ response.
- Airflow (`roles` là mảng object) nay cũng thử `[]` ở vị trí thứ hai.
