# Gộp logic lặp trên HEAD `9c4be5b1dc`, 2026-11-12

Yêu cầu của user: cắt phần mã có thể cắt mà không đổi logic, giữ vòng `for`, không đổi sang stream, giữ mọi comment
`THESIS` trong cây. Danh sách 9 mục đến từ hai lượt soát độc lập (phiên chính và một agent `thesis-debater-high`).
Chưa commit.

- Bản vá chỉ gồm phần đổi: `shorten-logic-20261112.patch` (−70/+33 dòng; tính cả 2 dòng `THESIS` dời chỗ và 1 dòng
  `THESIS` mới cho `bestField`).
- Bản vá cả cây so với HEAD, gồm comment `THESIS`: `shorten-logic-20261112-tree.patch`. Diễn tập rollback trên bản
  này: áp lại trùng từng byte.
- Trạng thái cây trước khi sửa (chỉ có comment `THESIS`): `thesis-comments-pre-shorten-20261112.patch`.
- Jar: `EvoMaster/evomaster-SL-c01cb6d6.jar`, cùng model M1 với jar DC.
- Self-test: `selftest/shorten-logic-20261112.sh`, stub mới `selftest/array_body_stub.py`.

Ký hiệu: `B` = `RestSecurityBuilder.kt`, `O` = `RestSecurityOracle.kt`. Tên hàm dùng để tra.

| # | Chỗ | Trước | Sau | Vì sao giống hệt |
|---|---|---|---|---|
| 1 | B `roleField`, `setUserTargetToVictim` | hai vòng chọn trường điểm cao nhất, khởi đầu 0.0, so `>` | `bestField(a, model, onPath)`; `roleField = bestField(a, "role", false)`, path field = `bestField(action, "victim", true)` | cùng thứ tự duyệt `schemaFields`, cùng ngưỡng 0.0, cùng `>` nên trường đầu tiên thắng khi hoà; `(f.loc == "path") != onPath` bỏ đúng các trường mà mỗi vòng cũ bỏ |
| 2 | B `buildStatefulAuthzTriple` | hai `if` cho `TRIPLE_BUILT`, `STOP_VICTIM`, ở hai chỗ | `if (outcome != NEXT) return outcome == TRIPLE_BUILT` | `RoleAttempt` có đúng 3 giá trị |
| 3 | B `victimObjects` | get, tính, put bằng tay | `victimObjectCache.getOrPut(key) { findVictimObjects(...) }` | `getOrPut` của `MutableMap` làm đúng get, tính và put khi thiếu; giá trị là `List`, không bao giờ null |
| 4 | B `setField` | gọi `trySetFromStringValue` (một chỗ gọi) | `try { f.value.setFromStringValue(value) } catch (e: Exception) { false }` ngay trong hàm | cùng biểu thức, cùng `catch` |
| 5 | B `walkBody` | `if`/`else` với hai vòng giống nhau | `container`, `prefix` rồi một vòng | mảng: `objectFields(v.template)`, tên `"$name[]."`; còn lại: `objectFields(g)`, tên `"$name."`; như cũ |
| 6 | B `victimSnapshot`, `victimRoleValues` | mỗi hàm tự lấy `victimField(...)?.leaf` rồi `getObjects(victimObjects(...))` | `victimGetObjects(victimAuth, transition)` | cùng lời gọi, cùng thứ tự; `normalize(role.leaf)` đổi chỗ với `victimField` nhưng cả hai không có tác dụng phụ |
| 7 | O `handleStatefulAuthorization` | hai `if ... continue` liên tiếp cho follow-up | một `if` với `\|\|` | `\|\|` dừng sớm, thứ tự kiểm giữ nguyên, các kiểm không có tác dụng phụ |
| 8 | B `transitionScore` | gọi `transitionEvidence` (một chỗ gọi) | `prior("op") + opEvidenceCache.getOrPut(...)` | cùng biểu thức; `git grep` không thấy `transitionEvidence` ngoài file |
| 9 | B `tryReducedRoles`, `restoreOperatorsAndRetry` | hai dòng `return STOP_VICTIM` | một dòng với `\|\|` | `\|\|` dừng sớm, `hasPhaseTimedOut()` vẫn được gọi trước |

Không đụng: `doInitialize(randomness)`, thứ tự lời gọi HTTP, `archive.addIfNeeded`, mọi lệnh log.

Đã cân nhắc và không làm:

- Gộp phần chuẩn bị transition và phần hoàn tất individual: lợi 0–1 dòng; phần hoàn tất của bộ ba có thêm
  `Lazy.assert { verifyValidity() }` mà nhánh restore không có.
- Gộp `noStatusRecorded`, `victimId` vào chỗ gọi: tên hàm giúp đọc.
- Gộp `victimField` vào `bestField`: `victimField` nhận cả điểm âm và loại trường vai trò.
