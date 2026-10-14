# Quy tắc gán nhãn: endpoint có phải "thao tác ghi làm giảm quyền" không

Bản nháp 2026-09-16. Dùng chung cho người và cho LLM gán nhãn mù. Đọc một lượt rồi gán được.

## 1. Đơn vị gán nhãn

Một dòng = một **operation** = một cặp (HTTP method, path) trong một spec OpenAPI.
Cùng path, khác method → hai dòng, gán độc lập.

## 2. Chỉ được nhìn những thứ này

| Được nhìn | Không được nhìn |
|---|---|
| HTTP method | Mã trạng thái và mô tả của response |
| Path (cả tên biến trong `{}`) | Schema của response |
| `summary` của operation | `tags`, `operationId` |
| `description` của operation | `security`, scheme xác thực |
| Tên tham số (`path`, `query`, `header`) | Mã nguồn ứng dụng, tài liệu ngoài spec |
| Tên trường trong request body (kể cả trường lồng, ghi dạng `a.b`) | Nhãn của người gán nhãn kia, nhãn gốc |
| Danh sách `enum` của tham số và trường body (xem §7) | Tên nhà cung cấp, tên file spec, phân chia train/test |

**Cấm suy đoán runtime.** Không được đoán server làm gì, không được giả định mã trạng thái nào trả về, không
được đoán giá trị client gửi lên. Chỉ đọc chữ trong spec.

Nếu một cột trống trong phiếu thì coi như spec không khai; không đi tìm ở chỗ khác.

## 3. Ba nhãn

| Nhãn | Nghĩa |
|---|---|
| `R` | Thao tác ghi **có thể làm giảm** quyền của một chủ thể (user, account, principal, member). |
| `N` | Không phải: hoặc không phải ghi, hoặc không đụng quyền, hoặc chỉ tăng quyền. |
| `U` | Không rõ. Chữ trong spec không đủ để chọn `R` hay `N`. |

`R` là "có thể", không phải "chắc chắn". Một endpoint cho client đặt role thành giá trị tuỳ ý là `R`, vì trong
số các giá trị đó có giá trị thấp hơn hiện tại.

## 4. Thứ tự áp dụng

1. Cổng **G1** rồi **G2**. Cổng chặn thì dừng, gán `N`.
2. Chạy `R2`…`R6` theo thứ tự. Trúng quy tắc nào trước thì gán `R`, ghi mã quy tắc đó, dừng.
3. Không trúng `R` nào: chạy `N1`…`N7`. Trúng thì gán `N`, ghi mã.
4. Không trúng gì, hoặc trúng `U1`–`U3`: gán `U`, ghi mã và một dòng lý do.

`R` thắng `N` khi cả hai cùng trúng. Ví dụ: một endpoint vừa nâng vừa hạ role trúng cả `R5` lẫn `N3` → `R`.

### G1 — có phải ghi không

Method thuộc `POST`, `PUT`, `PATCH`, `DELETE` → qua. `GET`, `HEAD`, `OPTIONS` → `N`, mã `N1`.

### G2 — có đụng tới quyền của chủ thể không

Trong path, `summary`, `description`, tên tham số hoặc tên trường body có ít nhất một từ chỉ **chủ thể**
(user, account, member, principal, employee, customer, login…) **và** ít nhất một từ chỉ **quyền**
(role, permission, privilege, grant, entitlement, scope, acl, policy, admin, access, active,
enabled, status…); hoặc chính chủ thể là đối tượng bị xoá.

Không có → `N`, mã `N2`.

Hai danh sách từ trên là **ví dụ, không đầy đủ**. Gán nhãn theo nghĩa của câu, không theo phép so khớp chuỗi.
Gặp từ đồng nghĩa không có trong danh sách mà nghĩa rõ ràng thì vẫn tính.

## 5. Năm quy tắc cho `R`

Cột "Nguồn" trỏ tới phạm trù trong `sources.md`.

### R2 — xoá role, thu hồi permission (nguồn: B3 `DeleteRole`, B5 `RevokePermission`)

Ghi mà đối tượng bị xoá hoặc bị thu hồi là một role, permission, privilege, grant, scope, entitlement, ACL
entry, policy: `DELETE /roles/{id}`, `POST /revokePermission`, `DELETE /acl/{id}`.

### R3 — tách chủ thể khỏi một role (nguồn: B4 `DeassignUser`)

Ghi mà chữ trong spec nói lấy một chủ thể ra khỏi một **role**: `POST /users/{id}/roles/remove`,
`DELETE /users/{id}/roles/{role}`, summary "unassign role", "remove role from user".

Gỡ chủ thể khỏi một group hoặc team là `N9`, kể cả khi operation có kèm từ chỉ quyền.

### R4 — tắt trạng thái hoạt động của chủ thể (nguồn: A1 `active`)

Ghi lên một chủ thể, trong đó có trường hoặc tham số đặt được trạng thái hoạt động: `active`, `enabled`,
`disabled`, `locked`, `suspended`, `blocked`, `banned`, `status`; hoặc tên thao tác nói deactivate, disable,
suspend, lock, ban, revoke access.

Vì phiếu không cho nhìn giá trị client gửi, quy tắc là **endpoint có phơi ra trường đó** thì đủ để gán `R`.
Riêng `status` chỉ tính khi có `enum` chứa một giá trị nghĩa là ngừng hoạt động (`inactive`, `disabled`,
`suspended`…); `enum` không có giá trị như vậy → `U`, mã `U1`.

### R5 — đặt role/permission/entitlement bằng giá trị client đưa (nguồn: A3 `entitlements`, A4 `roles`)

Ghi mà giá trị của role, permission, privilege, scope, entitlement của một chủ thể do client đặt,
qua tham số hoặc trường body: `PUT /users/{id}/role` với body `role`, `PATCH /users/{id}` với body `roles`,
`POST /setUserPermission?user=&permission=`.

Đây là trường hợp "vừa nâng vừa hạ": tập giá trị đặt được chứa cả giá trị thấp hơn.

Phân biệt với `N3`: nếu quyền được nâng đã cố định trong path hoặc trong tên thao tác và không có trường nào
cho client chọn giá trị (`POST /users/{id}/roles/admin`, summary "grant admin"), thì là `N3`.

### R6 — bỏ một role khỏi session đang hoạt động (nguồn: B6 `DropActiveRole`)

Ghi mà chữ trong spec nói bỏ, tắt, hạ một role **trong phiên hiện tại**: "drop active role",
"deactivate role for this session", "switch off role".

Đăng xuất hoặc thu hồi token mà không nhắc tới role/permission nào → `N7`.

## 6. Ranh giới — bảy quy tắc cho `N`

| Mã | Trường hợp | Ví dụ |
|---|---|---|
| `N1` | Đọc | `GET /users`, `HEAD /roles/{id}` |
| `N2` | Ghi nhưng không có cả hai loại từ ở G2 | `POST /reports`, `DELETE /orders/{id}` |
| `N3` | Chỉ nâng quyền, giá trị cố định trong path hoặc tên thao tác | `POST /users/{id}/roles/admin`, "grant permission", "add member" |
| `N4` | Tạo mới chủ thể, role, group | `POST /users`, `POST /roles`, `POST /groups` |
| `N5` | Ghi lên trường không phải quyền của chủ thể | `PUT /users/{id}/email`, `PUT /users/{id}/password`, `PATCH /users/{id}` chỉ có `name`, `avatar`, `locale` |
| `N6` | Ghi lên tài nguyên nghiệp vụ, dù cần quyền admin | `DELETE /invoices/{id}` với summary "only admins" |
| `N7` | Kết thúc phiên hoặc thu hồi credential, không nhắc role/permission | `POST /logout`, `DELETE /sessions/{id}`, `POST /tokens/{id}/revoke` |
| `N8` | Xoá chính chủ thể | `DELETE /users/{id}`, "deletes a user", "remove account" |
| `N9` | Gỡ chủ thể khỏi một group hoặc team | `DELETE /groups/{gid}/members/{uid}`, "leave group", "remove member" |

`N5` và `N6` là chỗ dễ nhầm nhất. Câu "Only Admins may …" nói về **người gọi**, không nói endpoint làm giảm quyền
của ai.

`N7` để riêng vì thu hồi credential khác thu hồi quyền: credential cũ mất hiệu lực, còn tập quyền của chủ thể
không đổi.

`N8` và `N9` là hai nhóm mà người chốt loại ra ngày 2026-09-17, xem §8. Chúng vẫn là thao tác giảm quyền theo
nghĩa thông thường; ở đây gán `N` vì lý do đo đạc, không phải vì định nghĩa.

## 7. `enum`

Được nhìn `enum` của tham số và của trường body, vì `R4` và `R5` cần nó (một tập `['admin','user']` cho biết
giá trị đặt được có cả mức thấp). Không được nhìn `example`, `default`, `description` của từng trường.

Cột này mở rộng danh sách "được nhìn" mà nhiệm vụ nêu ban đầu. Người chốt đồng ý ngày 2026-09-17. Người và LLM
phải nhìn đúng một lượng thông tin như nhau, nhìn lệch thì kappa giữa hai người gán nhãn mất nghĩa.

## 8. Đã chốt ngày 2026-09-17

| Trường hợp | Chốt | Lý do |
|---|---|---|
| xoá một user | `N8` | Các lần chạy của ta không reset và dùng một bộ tài khoản cố định. Xoá trúng một tài khoản trong bộ đó thì mọi individual sau không đăng nhập được, hỏng phần còn lại của lần chạy. |
| đặt `active: false` | `R4` | Nhóm lớn nhất trong khảo sát CVE, 29 trên 85. Khi báo cáo phải tách số theo mã quy tắc, vì khoá tài khoản không hạ role. |
| rời một group hoặc team | `N9` | Chữ "group" trong API đời thật phần lớn không mang quyền. Giữ nó lại thì từ vựng nuốt một từ quá phổ biến, đúng kiểu hỏng của bộ 56 từ cũ. |
| gỡ chủ thể khỏi một role | `R3` | Đây là lệnh `DeassignUser` của RBAC, gần quan hệ A1 nhất trong năm lệnh. |
| một endpoint vừa nâng vừa hạ role | `R5` | Cả ba target của ta hạ quyền theo đúng kiểu này. Bỏ thì từ vựng trượt chính ca mà oracle sinh ra để bắt. |
| người gán nhãn được nhìn `enum` | có | Thiếu nó thì `status` và `role` rơi hết vào `U`. Người và LLM nhìn như nhau. |

Danh sách `group` của SCIM (`sources.md` A2) vì thế nằm ngoài phạm vi đợt này. Nguồn vẫn giữ trong `sources.md`.

Nhãn nào đã gán trước 2026-09-17 theo bản nháp cũ thì bỏ, không trộn với nhãn theo bản này.

## 9. `U` và cách phân xử

### Khi nào gán `U`

| Mã | Trường hợp |
|---|---|
| `U1` | Có từ chỉ chủ thể và từ chỉ quyền, nhưng không biết chiều và không có trường nào cho client đặt giá trị. Ví dụ: `POST /users/{id}/access` với summary rỗng. |
| `U2` | Từ khoá nước đôi giữa nghĩa phân quyền và nghĩa nghiệp vụ: `role` là chức danh nhân sự, `plan`/`entitlement` là gói cước, `status` là trạng thái đơn hàng. |
| `U3` | Không xác định được đối tượng bị ghi là chủ thể hay là tài nguyên. Ví dụ: `DELETE /memberships/{id}` không có mô tả. |

Gán `U` phải kèm một dòng lý do và **từ khoá gây nghi** (cột `doubt_token` trong phiếu).

`U` là nhãn thật, không phải bỏ trống. Bỏ trống một dòng là lỗi quy trình, phải gán lại.

### Ba lượt gán nhãn — chốt 2026-09-17

Thay cho thiết kế cũ (một người, một LLM, người gán toàn bộ). Lý do: người gán toàn bộ mất nhiều giờ hơn ngân sách,
mà phần lớn dòng là dòng dễ.

| Lượt | Ai | Gán gì |
|---|---|---|
| L1 | một LLM, gán mù | toàn bộ dòng |
| L2 | một LLM khác model, gán mù, không thấy L1 | toàn bộ dòng |
| H | người (Minh) | mọi dòng L1 khác L2 hoặc có bên gán `U`, cộng mẫu soát |

L1 và L2 chạy trong hai phiên rời, mỗi phiên chỉ mở `labelling-form.md` và file CSV của mình, không thấy hội thoại
nào khác và không thấy nhãn của lượt kia. Model và mức effort của từng lượt ghi vào `labelling/PROVENANCE.md`.

**Mẫu soát.** Nhóm L1 trùng L2 tách theo nhãn. Nhóm cùng `R` soát toàn bộ, vì từ vựng rút ra từ chính các dòng
này. Nhóm cùng `N` bốc 40 dòng, hạt giống cố định `20260918`, bốc **trước khi** người nhìn dòng nào. Chi tiết và
cách quy đổi ước lượng: `infra/analysis/corpus/sampling-plan.md` §1d. Mẫu này là chỗ duy nhất ước lượng được
tỉ lệ sai của phần không ai soát, bỏ nó thì nhóm trùng không còn bằng chứng nào.

**Bốn con số phải báo cáo.**

1. Đồng thuận L1–L2: tỉ lệ thô và kappa ba lớp, trên toàn bộ dòng.
2. Kappa người–LLM trên mẫu soát, trọng số theo xác suất vào mẫu. Đây là con số chính về độ tin cậy của nhãn.
3. Tỉ lệ người khác LLM trên tầng lệch, tính riêng, không trộn vào (2).
4. Tỉ lệ sai ước lượng của phần trùng không soát, suy từ (2), kèm khoảng Wilson 95% quy về cả tầng trùng.

Đồng thuận L1–L2 **không phải** độ tin cậy giữa hai người gán nhãn độc lập: hai lượt cùng nhà cung cấp chia nhau
cùng một kiểu đọc sai, sai giống nhau thì kappa vẫn cao. Nó đo tính nhất quán của một hệ thống. Viết đúng như
vậy trong phần hạn chế; chỗ neo vào dữ liệu không do model sinh ra là mẫu soát và tầng lệch.

**Phiếu và file.** Mỗi lượt một file: `<spec>.l1.csv`, `<spec>.l2.csv`, `<spec>.human.csv`, cùng số dòng và cùng
thứ tự `row_id` như bản gốc. Phân xử ghi ra `<spec>.final.csv`: `row_id, l1, l2, human, stratum, final_label,
audited`, trong đó `stratum` là `agree-R`, `agree-N` hoặc `disagree`, `audited` là `1` khi người đã gán dòng đó.

### Ai phân xử, lúc nào

1. L1 và L2 gán xong độc lập. Tính đồng thuận L1–L2 và chốt hai tầng **trước khi** người gán dòng nào.
2. Bốc mẫu soát theo hạt giống đã khai. Người gán tầng lệch cộng mẫu soát, không xem nhãn của L1 và L2.
3. Tính kappa người–LLM **trước khi** phân xử, trên nhãn thô, ba lớp `R`/`N`/`U`. Con số phụ, nếu cần: kappa
   hai lớp `R`/`N` sau khi bỏ mọi dòng có ít nhất một bên gán `U`; ghi rõ số dòng đã bỏ.
4. Người (Minh) phân xử mọi dòng mình đã gán mà lệch với L1 hoặc L2, và mọi dòng có bên gán `U`. LLM không
   phân xử, không được hỏi ý kiến ở bước này.
5. Dòng thuộc tầng trùng mà không nằm trong mẫu soát: `final_label` lấy nhãn hai lượt đã trùng, `audited` để `0`.
   Mọi con số tính trên `final_label` phải ghi kèm tỉ lệ sai ước lượng của nhóm này.
6. Nhãn sau phân xử ghi vào `final_label`, không đè lên nhãn thô. Kappa không tính lại sau phân xử.
7. Phân xử mà thấy quy tắc thiếu thì ghi vào `rules-changelog`; quy tắc chỉ đổi giữa hai vòng gán nhãn, không
   đổi giữa chừng một vòng.

**Bấm giờ.** Phép đo tốc độ để chốt cỡ mẫu giờ đo trên tầng người thực sự phải gán, tức tầng lệch cộng mẫu soát,
không phải trên toàn bộ dòng.

## 10. Ba ví dụ đã áp dụng thử

Ba ví dụ lấy từ ba target của đề tài. Ba target này nằm ngoài corpus gán nhãn.

### Ví dụ 1 — reports-api (Tier-1)

Nguồn: **mã nguồn**, không phải spec. App phục vụ spec lúc chạy; đêm nay không khởi động app, và trong
`infra/em-results/` không có bản lưu nào (`find … -iname "*openapi*"` chỉ ra `OpenApiConfig.java`,
`OpenApiContractTest.java`). Dòng dưới đây dựng lại từ:
`infra/reports-api/src/main/java/com/thesis/reportsapi/web/UserController.java:32` (`@PutMapping("/users/{username}/role")`),
`:48–49` (`@PathVariable String username`, `@RequestBody RoleUpdateRequest`),
`infra/reports-api/src/main/java/com/thesis/reportsapi/dto/RoleUpdateRequest.java:7`
(`@Schema(allowableValues = {"ADMIN", "VIEWER"}) String role`).

| Cột | Giá trị |
|---|---|
| method | `PUT` |
| path | `/users/{username}/role` |
| summary/description | (trống — không có `@Operation` nào trong `src/main/java`, `grep -rn "Operation("` không ra dòng nào) |
| param_names | `username` |
| body_field_names | `role` |
| enum_values | `role: [ADMIN, VIEWER]` |
| label | `R` |
| rule_id | `R5` |

Đường đi: G1 `PUT` qua. G2 path có `users` (chủ thể) và `role` (quyền), qua. `R2` không. `R3` không (không có chữ remove/unassign). `R4` không. `R5` trúng: client đặt `role` bằng giá trị
trong `[ADMIN, VIEWER]`, tập này có `VIEWER` thấp hơn `ADMIN`.

### Ví dụ 2 — vampi-seeded (Tier-2)

Nguồn: `infra/vampi-seeded/openapi_specs/openapi3.yml`, path ở dòng 263, `delete:` ở dòng 307, `summary` dòng 312,
`description` dòng 313, tham số `username` dòng 316–322.

| Cột | Giá trị |
|---|---|
| method | `DELETE` |
| path | `/users/v1/{username}` |
| summary/description | `Deletes user by username (Only Admins)` / `Deletes user by username (Only Admins)` |
| param_names | `username` |
| body_field_names | (không có) |
| enum_values | (không có) |
| label | `N` |
| rule_id | `N8` |

Đường đi: G1 `DELETE` qua. G2 có `users`/`user` và `Admins`, qua. Không quy tắc `R` nào trúng: đối tượng bị xoá
không phải role hay permission, không có chữ unassign, không có trường trạng thái, client không đặt giá trị role.
`N8` trúng: đối tượng bị xoá là chính chủ thể. Cụm `(Only Admins)` nói về người gọi, không đổi nhãn.

### Ví dụ 3 — pyLoad (Tier-2b)

Nguồn: `infra/pyload-cve/openapi-merged.json`, path `/api/set_user_permission` dòng 2346, `post` dòng 2347,
`summary` dòng 2348, `description` dòng 2349, tham số `user` dòng 2355, `permission` dòng 2363, `role` dòng 2371.

| Cột | Giá trị |
|---|---|
| method | `POST` |
| path | `/api/set_user_permission` |
| summary/description | `No documentation available` / `No documentation available` |
| param_names | `user`, `permission`, `role` |
| body_field_names | (không có) |
| enum_values | (không có; `permission` và `role` đều `type: integer`) |
| label | `R` |
| rule_id | `R5` |

Đường đi: G1 `POST` qua. G2 path và tên tham số có `user` và `permission`/`role`, qua. `R2`–`R4` không trúng.
`R5` trúng: client đặt `permission` và `role` bằng số nguyên tuỳ ý, trong đó có số thấp hơn giá trị đang có.
Mô tả rỗng (`No documentation available`) không kéo về `U1`, vì tên tham số đã đủ cho `R5`.

## 11. Luật rút bộ từ vựng — chốt 2026-09-20, viết trước khi chạy

### 11.1 Cổng chặn ở runtime nhìn thấy gì

`RestSecurityBuilder.looksLikePermissionReducingTransition` (`RestSecurityBuilder.kt:79`) dựng chuỗi
`hay = (a.path.toString() + " " + a.getName()).lowercase()` rồi hỏi `TRANSITION_PATH_SIGNALS.any { hay.contains(it) }`.
`RestCallAction.getName()` (`RestCallAction.kt:147`) trả `"$verb:$path"`. Cổng chặn chỉ đọc path và verb:
tên tham số, tên trường thân và phần mô tả không tới được nó. Đây là lý do `PATCH /auth/fab/v1/users/{username}`
của Airflow bị bỏ sót: quyền nằm ở trường thân `roles`.

So khớp là `contains`, không phải bằng token. `role` trúng `roles`, `rolemappings`, `controller`.

### 11.2 Rút danh sách nào

| # | Danh sách | Dòng | Rút từ | Trong lần này |
|---|---|---|---|---|
| 1 | `transitionPathSignals` | `:68` | token trong `path` của dòng `R` | có |
| 2 | `transitionUserParamSignals` | `:363` | token trong `param_names` của dòng `R` | có, kèm suy đoán ở 11.6 |
| 3 | `roleFieldSignals` | `:364` | token trong `body_field_names` của dòng `R` | có, kèm suy đoán ở 11.6 |
| 4 | `roleLowPrivSignals` | `:365` | — | không |
| 5 | `roleHighPrivSignals` | `:366` | — | không |
| 6 | `numericRoleCandidates` | `:368` | — | không |
| 7 | `stringRoleCandidates` | `:370` | — | không |
| 8 | `elevatedNumericRoleCandidates` | `:372` | — | không |
| 9 | `elevatedStringRoleCandidates` | `:374` | — | không |

Danh sách 4–9 cần biết giá trị nào là quyền thấp và giá trị nào là quyền cao. Corpus có `enum_values`
nhưng không có nhãn nào nói thứ tự giữa các giá trị đó. Sáu danh sách này giữ nguyên và ghi thành hạn chế.

### 11.3 Dữ liệu vào

Nửa train của `labelling-r2/final.csv`: 14 spec, 14 nhà cung cấp, 26 dòng `R` và 215 dòng `N`.
Dòng `U` (5) bị loại khỏi cả tử số lẫn mẫu số. Nửa test không được mở ở bước này.

Chỉ 5 trong 14 nhà cung cấp có dòng `R`: keycloak 10, gitlab 8, configcat 4, appcenter 3, authentiq 1.

198 trong 246 dòng train mang nhãn hai máy cùng gán mà không ai soát (`audited=0`).

### 11.4 Sinh ứng viên

Từ `path`, `param_names`, `body_field_names` của các dòng `R`, theo thứ tự:

1. cắt trên mọi ký tự không phải chữ hoặc số; `{realm}` cho token `realm`;
2. cắt tiếp ở ranh giới camelCase: `roleMappings` cho `role` và `mappings`;
3. hạ chữ thường;
4. bỏ token toàn chữ số;
5. bỏ token ngắn hơn 4 ký tự.

Bước 5 cắt `id`, `v1`, `api`, `org`. Dưới ngữ nghĩa `contains`, một token 2–3 ký tự trúng quá rộng.

### 11.5 Ba điều kiện nhận một từ

Với từ `w`, đếm bằng đúng phép so của runtime: dòng trúng `w` khi trường tương ứng, hạ chữ thường,
chứa `w` như chuỗi con.

- **P1 — hai nhà cung cấp.** `w` phải trúng ít nhất một dòng `R` ở hai nhà cung cấp khác nhau.
  P1 kéo theo `w` trúng ít nhất 2 dòng `R`.
- **P2 — gấp đôi tỉ lệ nền.** `dfR(w) / (dfR(w) + dfN(w)) >= 2 * p`, với `p` là tỉ lệ dòng `R`
  trên nửa train, `p = 26/241 = 0.1079`, ngưỡng `0.2158`. Ngưỡng là công thức, không phải số chọn tay.
- **P3 — không giữ từ thừa.** Nếu `a` và `b` cùng được nhận và `a` là chuỗi con của `b`, bỏ `b`.
  `role` đã trúng mọi chỗ `roles` trúng.

P1 là điều kiện quyết định của lần rút này. Không có nó, các từ điểm cao nhất đều là từ riêng của Keycloak.

### 11.6 Chỗ luật này suy đoán

Corpus gán nhãn theo endpoint, không gán theo từng trường. Không có nhãn nào nói trường nào là
định danh chủ thể và trường nào là mức quyền. Việc lấy danh sách 2 từ `param_names` và danh sách 3
từ `body_field_names` là một suy đoán: định danh chủ thể thường nằm ở path hoặc query, mức quyền
thường nằm ở thân. Precision và recall chỉ được công bố cho danh sách 1, vì chỉ danh sách 1 quyết định
một dòng có được chọn hay không. Danh sách 2 và 3 công bố dưới dạng ứng viên.

### 11.7 Đo trên nửa test

Một dòng test được dự đoán `R` khi verb thuộc `PUT/PATCH/POST/DELETE` và ít nhất một từ của
danh sách 1 là chuỗi con của `path` hạ chữ thường. So với `final_label`, bỏ dòng `U`.
Nửa test: 14 dòng `R`, 255 dòng `N`, tỉ lệ nền `0.0520`.

Báo cáo precision, recall, số dòng dự đoán, và danh sách dòng `R` bị bỏ sót kèm lý do.
Bộ 56 từ chạy trên cùng nửa test làm kiểm tra phát triển. Không có bảng nào trong luận văn
đặt hai bộ cạnh nhau: bộ 56 từ do ta tự đặt, không phải đường cơ sở.

### 11.8 Đã thấy gì trước khi viết luật này

Ngày 2026-09-20, trước khi mục 11 được viết, một bản xem trước đã chạy trên nửa train và in ra:
`subscription` 0/28, `plan` 0/0, `grant` 1/28, `owner` 3 dòng `R` so với 26 dòng `N`, và các từ
mới `permissions`, `composites`, `mappings`, `roles`, `enabled`. Ba từ điểm cao nhất khi đó —
`realm`, `containerid`, `clientrole` — chỉ có ở Keycloak, và đó là lý do P1 tồn tại.
Ngưỡng P2 và P3 chọn theo công thức ở 11.5, không theo bảng điểm đó. Hai con số trong bản xem
trước lệch với 11.3 vì bản đó chạy trước khi 12 dòng cuối được chốt.

## 12. Xếp hạng thay cho lọc — chốt 2026-09-21, viết trước khi chạy

### 12.1 Vì sao đổi

`RestSecurityBuilder.findPermissionReducingTransition` (`RestSecurityBuilder.kt:809`) sắp endpoint theo
thứ tự verb `PUT, PATCH, POST, DELETE` rồi lấy `firstOrNull`. Runtime chọn đúng một endpoint làm transition.
Câu hỏi thật không phải "từ nào được vào danh sách" mà "endpoint nào được chọn".

Bộ lọc §11 mua precision `0.098` lên `0.156` bằng recall `0.857` xuống `0.500` trên nửa test
(`lexicon-20260920/RESULTS.md` §8). Với oracle này bỏ sót là mất hẳn một lỗi, còn nổ nhầm chỉ tốn ngân sách
và không thành 970 vì còn phải qua bộ ba và D1.

### 12.2 Điểm

Giữ cả 32 ứng viên của danh sách 1. P1, P2, P3 của §11 không áp ở đây.

```
diem(w)        = (df_R + 1) / (df_R + df_N + 2)  ×  ncc / (ncc + 1)
diem(endpoint) = max diem(w) trên các từ w trúng chuỗi so của runtime, 0 nếu không từ nào trúng
```

Vế trái là precision làm mượt Laplace: một từ 2 dòng `R` và 0 dòng `N` được `0.75`, không được `1.000`.
Vế phải biến P1 từ chặn thành phạt: từ ở một nhà cung cấp nhân `1/2`, từ ở bốn nhà cung cấp nhân `4/5`.
`df_R`, `df_N`, `ncc` đếm trên nửa train, đúng phép so chuỗi con của runtime.

### 12.3 Hai biến thể

- **A** — xếp hạng chỉ bằng `diem(endpoint)`.
- **B** — như A, nhưng loại endpoint không có tên tham số nào trúng danh sách 2.
  Runtime đòi cả hai điều kiện (`:816`, `:817`).
- **C** — như A, nhưng khi bằng điểm thì endpoint có tham số trúng danh sách 2 đứng trước.
  Thêm lúc 00:52 ngày 09-21, sau khi thấy kết quả của A và B, để khớp với cách patch nháp
  `lexicon-rank-20260921.patch` thực sự xếp hạng.

### 12.4 Thước đo

Trong mỗi spec, sắp mọi endpoint ghi (`PUT PATCH POST DELETE`) theo điểm giảm dần. Bằng điểm thì
theo thứ tự verb `PUT, PATCH, POST, DELETE`, rồi theo thứ tự xuất hiện trong spec, đúng như runtime.

Báo `top-k` = số spec có ít nhất một endpoint `R` nằm trong `k` endpoint đầu, chia cho số spec có
ít nhất một endpoint `R`. Báo `k = 1, 3, 8`. `k = 1` là hành vi hôm nay. `k = 3` và `k = 8` chỉ có
nghĩa sau khi patch cho builder thử endpoint kế tiếp.

Spec không có endpoint `R` nào không vào mẫu số, và số đó được báo riêng.

### 12.5 Nửa test không còn sạch

Mục 12 được thiết kế sau khi đã thấy kết quả nửa test ở `RESULTS.md` §2 và §8. Con số của §12 trên
nửa test là số phát triển, không phải ước lượng trên dữ liệu giữ riêng. Ước lượng sạch chỉ có được từ
spec gán nhãn sau ngày hôm nay.

## 13. Cổng chặn đọc thêm tên trường thân yêu cầu — chốt 2026-09-23, viết trước khi chạy

### 13.1 Vì sao

`looksLikePermissionReducingTransition` (`RestSecurityBuilder.kt:105`) và `transitionHay`
(`:850`) đều dựng chuỗi so bằng `path + " " + getName()`, mà `getName()` là `"$verb:$path"`
(`RestCallAction.kt:147`). Cổng đọc đúng path và verb. Endpoint đặt quyền trong thân yêu cầu không
có chữ nào để trúng: `PATCH /auth/fab/v1/users/{username}` của Airflow mang quyền ở trường `roles`
và bị bỏ qua hoàn toàn (`infra/em-results/airflow-debug-20260920/`).

Danh sách 3 (`roleFieldSignals`) đã rút được 23 từ từ `body_field_names` của các dòng `R`
(`lexicon-20260921-audited/RESULTS.md` §3) nhưng chưa có đường nào tới cổng.

### 13.2 Chuỗi so mới

```
pathHay(a)  = (path + " " + verb + ":" + path)                lowercase   — như cũ
fieldHay(a) = các tên gene thân yêu cầu của a, nối bằng dấu cách, lowercase
```

`fieldHay` chỉ lấy tên gene của `BodyParam`, không lấy path param và không lấy query param:
tham số người dùng đã có danh sách 2 lo, và mục này chỉ nhắm chỗ quyền nằm trong thân.

### 13.3 Ba biến thể

- **V0** — không đổi. `diem(a) = diem_path(pathHay(a))`. Đây là bản đang chạy trong jar `L`.
- **V1** — một bộ từ vựng. `diem(a) = diem_path(pathHay(a) + " " + fieldHay(a))`.
  Không thêm dữ liệu vào file từ vựng; từ của nửa `path` được dùng lại để chấm tên trường.
- **V2** — hai bộ từ vựng. Thêm loại `field` vào `stateful-authz-lexicon.csv`, điểm tính bằng
  đúng công thức §12.2 trên `body_field_names` của nửa train.
  `diem(a) = max(diem_path(pathHay(a)), diem_field(fieldHay(a)))`.

Không có biến thể nào nhân hệ số cho vế trường: chưa có căn cứ chọn hệ số.

### 13.4 Chọn biến thể ở đâu, báo ở đâu

Chọn giữa V1 và V2 bằng **top-1 theo thứ tự spec trên nửa train**. Bằng nhau thì lấy V1, vì nó không
thêm dữ liệu vào file từ vựng.

Nửa test chỉ chạy **một lần**, cho biến thể đã chọn và cho V0, và chỉ để báo cáo. Nếu nửa test xấu
đi thì báo nguyên con số đó, không đổi luật để cứu.

### 13.5 Điều kiện nhận

Đổi cổng chỉ được đưa vào patch khi cả ba đúng:

1. Nửa train: top-1 theo thứ tự spec của biến thể đã chọn **không thấp hơn** V0.
2. `PATCH /auth/fab/v1/users/{username}` của Airflow qua được cổng, tức `diem > 0`.
3. Trên cả ba target của luận văn, transition thật vẫn đứng hạng 1.

Điều kiện 3 là điều kiện chặn: nếu thêm tên trường đẩy một transition thật xuống hạng, bỏ mục này
và ghi lại vì sao.

### 13.6 Thước đo

Giống §12.4, không sửa: xếp mọi endpoint ghi của spec, báo `top-k` với `k = 1, 3, 8`, kèm khoảng
tốt nhất–xấu nhất và giá trị phá hoà theo thứ tự spec như `lexicon-20260921-audited/RESULTS.md` §5.

### 13.7 Đã thấy gì trước khi viết luật này

Đã biết: 23 từ của danh sách 3 và điểm của chúng (`candidates-3.csv`); Airflow bị bỏ sót và lý do;
thứ hạng của ba target dưới V0. Chưa chạy V1 hay V2 trên spec nào.
