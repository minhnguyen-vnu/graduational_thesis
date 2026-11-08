# Các hàm của oracle 970 (jar SR)

Mã: `EvoMaster/core/src/main/kotlin/org/evomaster/core/problem/rest/service/RestSecurityBuilder.kt` (gọi tắt **B**) và
`.../rest/oracle/RestSecurityOracle.kt` (gọi tắt **O**). Số dòng là của jar SR (`evomaster-SR-77465fe5.jar`, bản vá
`infra/evomaster-ext/wip/refactor-simplify-20261027.patch`). HEAD `9c4be5b1dc` (nền của jar M2) xoá thêm mã thừa, giữ
hành vi và log, nên số dòng ở đây lệch HEAD và vài nhánh nhắc ở đây đã gộp hoặc bỏ
(`infra/evomaster-ext/wip/redundant-code-20261103.md`).

Mỗi mục gồm: **Làm gì**, **Ai gọi**, **Vào và ra**, **Ví dụ**. Ví dụ chạy tay lấy từ lượt self-test thật
`infra/em-results/refactor-simplify-pilot-20261027/cand/restore-budget-refA.log` (stub `candidate_stub.py`, mode
`restore-budget`; tài khoản alice, boss, bob).

## 1. Luồng tổng

```
applySecurityPhase                          B:431
 └ addForStatefulAccessControl              B:641   chọn transition, duyệt source, duyệt nạn nhân
    ├ rankPermissionReducingTransitions     B:1195  xếp op có thể là transition
    ├ routeLooksMissing                     B:1779  bỏ op mà route có vẻ không tồn tại
    ├ harvestReducedRoleCandidates          B:1302  op còn giá trị hạ quyền nào không
    ├ guardedSources / anyAuthenticatedSuccess  B:766 / B:784  chọn source bị chặn bởi quyền
    ├ victimSlicesOn                        B:797   mỗi tài khoản một lát cắt nạn nhân
    └ buildStatefulAuthzTriple              B:838   thử dựng bộ ba cho một nạn nhân
       ├ operatorsFor                       B:815   ai làm operator, theo thứ tự nào
       ├ tryReducedRoles                    B:906   thử từng giá trị hạ quyền với một operator
       │  └ executeStatefulAuthzTriple      B:1018  dựng và chạy source, transition, follow-up
       │     └ reLoginProbeConfirmsPrivilegeRemoved  B:1155  probe C4
       └ restoreOperatorsAndRetry           B:942   operator bị hạ trước đó thì nâng lại rồi thử lại
          └ restorePrivilege                B:1381
fitness → RestSecurityOracle.handleStatefulAuthorization  O:552  gắn lỗi 970 nếu follow-up vẫn 2xx
```

Chạy tay rút gọn của lượt `restore-budget`:

| Bước | Dòng log | Hàm |
|---|---|---|
| 1 | `transition candidate PUT:/users/{username}/role score 8.50 roleField body:role victimField path:username reducedRoleValues 3` | `addForStatefulAccessControl` B:670 |
| 2 | `transition chosen: PUT:/users/{username}/role (candidate 1 of 2)` | B:687 |
| 3 | `guarded source candidates: 4 [PUT:/docs/{id}, PUT:/notes/{id}, PUT:/files/{id}, PUT:/permissions/{username}]` | `guardedSources` |
| 4 | `source PUT:/docs/{id} victims [alice]` | `victimSlicesOn` |
| 5 | `victim 'alice' operators [boss, bob]` | `operatorsFor` |
| 6 | `reduced role values [VIEWER, EVOMASTER, ADMIN]` | `reducedRoleValues` |
| 7 | `VOID ... operator 'boss', codes 200/403/200` | `executeStatefulAuthzTriple` |
| 8 | `VOID ... operator 'bob', codes 200/403/200` | như trên |
| 9 | `Privilege-restore accepted for 'boss' by 'alice' with role 'ADMIN' ... -> 200` | `restorePrivilege` |
| 10 | `anonymous control: PUT:/docs/{id}=401` | `reLoginProbeConfirmsPrivilegeRemoved` |
| 11 | `Assembled ... statuses 200/200/200` rồi `Constructed ... revealing privilege persistence` | B:1120, B:1136 |

## 2. Mô hình Naive Bayes (companion object)

### `loadModel` — B:91
- **Làm gì**: đọc `stateful-authz-model.csv`, mỗi dòng có dạng `bảng,đặc trưng,trọng số`, rồi gom thành `bảng → (đặc trưng → trọng số)`.
  Thiếu bảng nào thì log `warn`.
- **Ai gọi**: khởi tạo `MODEL` (B:126), một lần cho mỗi JVM.
- **Vào và ra**: không có tham số vào. Ra một `Map<String, Map<String, Double>>`. Nếu đặc trưng trùng thì dòng sau thắng, nhưng vẫn giữ vị trí
  lần xuất hiện đầu.
- **Ví dụ**: dòng `op,f:access,1.4663370687934267` cho `MODEL["op"]["f:access"] = 1.466…`.

### `tokens` — B:130
- **Làm gì**: tách một chuỗi thành tập từ thường. Tách theo ký tự không phải chữ hoặc số, tách tiếp theo camelCase, bỏ từ ngắn hơn
  `minLength` và từ chỉ gồm chữ số.
- **Ai gọi**: `SchemaField.features`, `opFeatures`, `hasIdToken`.
- **Ví dụ**: `tokens("/users/{username}/role")` cho `{users, username, role}`. `tokens("isAdmin", 1)` cho `{is, admin}`.

### `SchemaField` — B:156
- **Làm gì**: mô tả một trường của một op: vị trí `loc` (path, query hoặc body), tên đầy đủ `name`, tên lá `leaf`,
  loại `kind` (bool, enum, num, array, object, str) và các giá trị enum.
- **Ví dụ**: body `{"role": "ADMIN"}` với `role` là enum cho `loc=body`, `name=role`, `kind=enum`,
  `enumValues=[ADMIN, VIEWER, …]`, `key="body:role"`.

### `SchemaField.features` — B:191
- **Làm gì**: biến một trường thành tập đặc trưng để chấm điểm: `k:` loại, `l:` vị trí, `w:` tên lá, `n:` từ trong tên,
  `a:` từ trong trường cha, `e:` từ trong tối đa 12 giá trị enum.
- **Ví dụ**: trường `body:role` (enum ADMIN, VIEWER) cho `{k:enum, l:body, w:role, n:role, e:admin, e:viewer}`.

### `valueGene`, `alternatives`, `objectFields`, `walkBody`, `schemaFields` — B:210–291
- **Làm gì**: duyệt cây gene của một op để liệt kê mọi trường. `valueGene` bóc các lớp wrapper (Optional, Nullable,
  Choice). `alternatives` liệt kê các nhánh của `ChoiceGene`. `objectFields` lấy trường của mọi nhánh object và bỏ tên trùng.
  `walkBody` đi xuống body tới độ sâu 3. `schemaFields` ghép path, query rồi body, cắt ở 80 trường.
- **Ai gọi**: `opFeatures`, `roleField`, `victimField`, `restoreFields`, `keepOnlyTargetFields`, …
- **Ví dụ**: `PUT /users/{username}/role` với body `{role}` cho `[path:username, body:role]`.

### `opFeatures`, `transitionScore`, `fieldScore`, `valueScore` — B:293–338
- **Làm gì**: chấm điểm Naive Bayes dưới dạng log. `điểm = prior(bảng) + tổng trọng số các đặc trưng có trong bảng`.
  `opFeatures` gồm verb `v:`, từ trong path `p:` và từ trong tên trường `f:`. `valueScore(bảng, giá trị)` lấy trọng số lớn nhất
  trong số các khoá của bảng nằm trong giá trị; không khoá nào khớp thì trả 0.
- **Ví dụ**: `transitionScore(PUT /users/{username}/role) = 8.50`, `transitionScore(PUT /permissions/{username}) = 5.38`
  (dòng 1 của log). `valueScore("low", "viewer")` lớn hơn 0 vì bảng `low` có khoá chứa trong "viewer".

### `looksLikePermissionReducingTransition` — B:349
- **Làm gì**: trả true khi verb là PUT, PATCH, POST hoặc DELETE và `transitionScore > 0`.
- **Ai gọi**: oracle O:580 (để loại source trông giống transition) và O:599 (để nhận ra transition giữa source và follow-up).

## 3. Chọn transition và source

### `addForStatefulAccessControl` — B:641
- **Làm gì**: điều phối toàn bộ việc dựng bộ ba.
  1. Cần bật 970 và có ít nhất 2 tài khoản.
  2. Xếp các op ứng viên (`rankPermissionReducingTransitions`). Bỏ op có route có vẻ không tồn tại. Chỉ giữ op còn giá trị hạ
     quyền (`viable`).
  3. Với từng transition, đặt lại các bộ đếm, chọn source, rồi duyệt `source × nạn nhân`.
  4. Dừng cả hàm khi hết giờ hoặc đủ 20 lần thử. Bỏ sang transition kế tiếp khi một transition chưa được chứng minh đã tốn 5 lần
     thử, hoặc khi transition trả 404 sau một source 2xx.
- **Vòng lặp**: dựng được một bộ ba thì thoát vòng nạn nhân và sang **source kế tiếp**. Khi `candidateCapReached()` hoặc
  `transitionNotFoundSeen` thì đặt `stopSources = true` để thoát cả vòng source.
- **Ví dụ**: các bước 1–5 ở bảng §1.

### `rankPermissionReducingTransitions` — B:1195
- **Làm gì**: lọc op có verb ghi và `transitionScore > 0`, rồi xếp theo điểm giảm dần. Sort ổn định nên các op bằng điểm giữ thứ
  tự trong spec.
- **Ví dụ**: `[PUT /users/{username}/role (8.50), PUT /permissions/{username} (5.38)]`.

### `routeLooksMissing` — B:1779
- **Làm gì**: trả true khi path kết thúc bằng `{param}`, path cha đã được gọi, và mọi lời gọi có xác thực lên path hoặc path cha
  đều trả 404.
- **Ví dụ**: `PUT /items/{id}` với mọi lời gọi `GET /items` và `PUT /items/{id}` đều trả 404 cho true, nên op này bị bỏ.

### `harvestReducedRoleCandidates` — B:1302
- **Làm gì**: lấy các giá trị hạ quyền của trường role khi chưa biết vai trò hiện tại. Danh sách rỗng nghĩa là op bị loại.
  Giá trị lấy ra chỉ để quyết định `viable` và để in log. Giá trị dùng thật được tính lại cho từng nạn nhân ở B:863.
- **Ví dụ**: `[VIEWER, EVOMASTER, ADMIN]`.

### `guardedSources` — B:766
- **Làm gì**: liệt kê các op của những verb đã cho mà có ít nhất một user từng nhận 403 trên đó (nghĩa là op bị chặn bởi quyền),
  trừ chính path của transition.
- **Ví dụ**: verb PUT và PATCH cho `[PUT /docs/{id}, PUT /notes/{id}, PUT /files/{id}, PUT /permissions/{username}]`.

### `anyAuthenticatedSuccess` — B:784
- **Làm gì**: trả true khi có ít nhất một op trong danh sách đã từng được một user đã đăng nhập gọi thành công 2xx.
- **Ai gọi**: B:698. Nếu không có PUT/PATCH nào như vậy thì chuyển sang source POST.

### `victimSlicesOn` — B:797
- **Làm gì**: lấy các test có lời gọi 2xx lên source, cắt sau lời gọi đó, xếp từ ngắn tới dài, và giữ lát ngắn nhất cho mỗi
  tài khoản.
- **Ví dụ**: source `PUT /docs/{id}` cho `[lát của alice]`, log in `victims [alice]`.

## 4. Dựng bộ ba cho một nạn nhân

### `operatorsFor` — B:815
- **Làm gì**: liệt kê các tài khoản khác nạn nhân và chưa bị hạ quyền trong phase. Tài khoản từng gọi transition thành công
  đứng trước; trong mỗi nhóm giữ thứ tự của file auth.
- **Ví dụ**: nạn nhân alice cho `[boss, bob]`.

### `buildStatefulAuthzTriple` — B:838
- **Làm gì**: bỏ qua nạn nhân nếu cặp (transition, nạn nhân) đã bị từ chối hết, hoặc nếu nạn nhân đã bị hạ trong phase. Sau đó
  tính danh sách giá trị hạ quyền theo vai trò hiện tại (`victimRoleValues` rồi `reducedRoleValues`) và gọi
  `tryReducedRoles` với từng operator. Nếu lần thử cuối có source 2xx nhưng transition trả 401 hoặc 403 (operator đã mất quyền)
  thì gọi `restoreOperatorsAndRetry`. Nếu có lần bị từ chối (`victimRefused`) thì ghi cặp vào `refusedTransitionVictims`.
- **Ra**: true khi dựng được một bộ ba hợp lệ.
- **Ví dụ**: các bước 5–11 ở bảng §1.

### `tryReducedRoles` — B:906 và enum `RoleAttempt` — B:631
- **Làm gì**: thử lần lượt từng giá trị hạ quyền với một operator. Trả về:
  - `TRIPLE_BUILT`: đã dựng được một bộ ba;
  - `STOP_VICTIM`: dừng nạn nhân này (hết giờ, hết lượt, không ghi được mã trạng thái, nạn nhân đã bị hạ, hoặc cặp đã bị từ
    chối). Bên gọi trả false ngay và **không** ghi cặp bị từ chối;
  - `NEXT`: chuyển sang operator kế tiếp. Khi được gọi từ `restoreOperatorsAndRetry` thì chuyển sang kế hoạch restore kế tiếp.
- **Ví dụ**: boss với VIEWER cho 200/403/200. Mã 403 không phải lỗi giá trị nên trả `NEXT`, và bob được thử tiếp.

### `restoreOperatorsAndRetry` — B:942
- **Làm gì**: với mỗi operator, lập kế hoạch nâng quyền (`restorePlans`), thực hiện (`restorePrivilege`, do nạn nhân làm), rồi
  gọi lại `tryReducedRoles`. Dừng khi đã dùng hết 3 lần restore của transition này.
- **Ví dụ**: bước 9 rồi 10–11 ở bảng §1.

### `executeStatefulAuthzTriple` — B:1018
- **Làm gì**: dựng một test gồm lát cắt nạn nhân (kết thúc bằng source), rồi transition do operator gọi lên nạn nhân với giá
  trị hạ quyền, rồi follow-up là bản sao của source với **token cũ** của nạn nhân. Chạy test với
  `statefulTripleUnderEvaluation = true` để oracle O:552 biết đây là bộ ba. Sau đó phân loại kết quả:
  - **VOID**: source không 2xx, transition không 2xx, hoặc follow-up null hay 401. Nếu chỉ follow-up là 401 thì log thêm
    `REVOKED`;
  - **UNCONFIRMED**: follow-up 2xx nhưng probe C4 không cho thấy quyền đã bị gỡ;
  - còn lại là **Assembled**: thêm test vào archive.
  Transition 2xx thì ghi nạn nhân vào `privilegeReducedInPhase`. Follow-up 403 hoặc 2xx thì transition được coi là đã chứng
  minh.
- **Ví dụ**: codes `200/403/200` là VOID. Statuses `200/200/200` là Assembled và oracle nổ 970.

### `reLoginProbeConfirmsPrivilegeRemoved` (C4) — B:1155
- **Làm gì**: chạy lại lát cắt nạn nhân như một test mới, nghĩa là nạn nhân **đăng nhập lại** và nhận token mới. Lời gọi cuối
  phải trả 403. Sau đó chạy đối chứng ẩn danh (bỏ mọi credential): nếu ẩn danh cũng 403 thì kết luận INCONCLUSIVE, vì 403
  không đến từ quyền. Ẩn danh trả mã khác thì xác nhận quyền đã bị gỡ.
- **Ví dụ**: login mới gửi `PUT /docs/{id}` nhận 403, ẩn danh nhận 401, nên trả true (bước 10).

### `statusIn`, `lastRecordedStatus` — B:1010, B:1144
- **Làm gì**: `statusIn` lấy mã HTTP của một action trong một test đã chạy. `lastRecordedStatus` lấy mã cuối cùng khác null
  trong test.

### `noStatusRecorded`, `transitionRefusedAfterSource`, `transitionRejectedRoleValue` — B:992–1008
- **Làm gì**:
  - `transitionRejectedRoleValue`: transition trả 4xx hoặc 5xx khác 401, 403, 404, nghĩa là server từ chối **giá trị**;
  - `transitionRefusedAfterSource`: source 2xx và transition bị từ chối (401, 403 hoặc lỗi giá trị);
  - `noStatusRecorded`: log `warn` khi một lần thử không ghi được mã nào.
- **Ví dụ**: transition 422 làm `transitionRejectedRoleValue` trả true, nên thử giá trị kế tiếp với cùng operator.

## 5. Trường role, trường nạn nhân, giá trị

### `roleField`, `victimField` — B:1211, B:1227
- **Làm gì**: `roleField` chọn trường ngoài path có `fieldScore("role")` lớn nhất và lớn hơn 0. `victimField` chọn trường str
  hoặc num, khác trường role, có `fieldScore("victim")` lớn nhất (không yêu cầu lớn hơn 0). Khi bằng điểm thì giữ trường đứng
  trước.
- **Ví dụ**: `PUT /users/{username}/role` cho role `body:role` và nạn nhân `path:username`.

### `reducedRoleValues` — B:1256
- **Làm gì**: sinh giá trị hạ quyền theo loại trường:
  - enum: các giá trị thiên "low" đứng trước, xếp theo `low − high` giảm dần;
  - bool: đảo giá trị hiện tại (mặc định `false`);
  - array: `[]`;
  - num: `1, 0, 2`;
  - str: bảng `lowstr`.
  Sau đó bỏ các giá trị nạn nhân đang giữ mà không thiên "low", và bỏ giá trị trùng.
- **Ví dụ**: enum `[ADMIN, VIEWER, EVOMASTER]` khi chưa biết vai trò hiện tại cho `[VIEWER, EVOMASTER, ADMIN]`.

### `restoreFields`, `restoreValues`, `restorePlans` — B:1307, B:1317, B:1346
- **Làm gì**: chuẩn bị giá trị **nâng** quyền cho operator. Nếu biết giá trị cũ của operator (`victimSnapshot`) và giá trị đó
  không thiên "low" thì dùng lại nó. Nếu không thì sinh theo loại trường (enum thiên "high", bool `true`, num `0, 1, 2`, str
  bảng `highstr`). Mỗi kế hoạch gán một giá trị cho mỗi trường role; tối đa 3 kế hoạch.
- **Ví dụ**: `[[("body:role", "ADMIN")]]`.

### `restorePrivilege` — B:1381
- **Làm gì**: `restorer` (là **nạn nhân**, vẫn còn quyền) gọi transition lên `target` (là **operator** đã bị hạ ở bộ ba trước)
  với giá trị nâng. Nhận 2xx thì xoá target khỏi hai tập "đã hạ" và xoá `refusedTransitionVictims`. Mỗi transition có tối
  đa 3 lần.
- **Ví dụ**: `Privilege-restore accepted for 'boss' by 'alice' with role 'ADMIN' -> 200`.

## 6. Tìm dữ liệu của nạn nhân trong traffic

### `loginKeys`, `identityKeys` — B:1481, B:1507
- **Làm gì**: tìm tên các khoá trong payload đăng nhập có giá trị bằng tên tài khoản, rồi chuẩn hoá (chữ thường, chỉ chữ và số).
- **Ví dụ**: `{"username":"alice","password":"alicepass"}` cho `{username}`.

### `victimObjects`, `findVictimObjects`, `compareVictimObjects` — B:1520, B:1535, B:1563
- **Làm gì**: quét mọi phản hồi 2xx có chứa tên nạn nhân, thu các object JSON có một khoá định danh mang tên nạn nhân, rồi xếp
  theo ba khoá: path cùng tiền tố với transition đứng trước, rồi GET đứng trước, rồi object khớp nhiều khoá hơn đứng trước. Kết
  quả được cache theo `nạn nhân|lá|path`.
- **Ví dụ**: `GET /users` trả `[{"id":7,"username":"alice","role":"ADMIN"}]` cho object `{id:7, username:alice, role:ADMIN}`.

### `matchingKeys`, `collectVictimObjects`, `objectValue`, `victimId` — B:1577–1620
- **Làm gì**:
  - `matchingKeys` đếm số khoá định danh khớp tên nạn nhân;
  - `collectVictimObjects` đệ quy thu các object khớp;
  - `objectValue` lấy giá trị vô hướng của khoá đầu tiên trùng tên;
  - `victimId` lấy theo tên lá, nếu không có thì lấy theo `id`.
- **Ví dụ**: `victimId(objects, "userid")` không có khoá `userid`, nên lấy `id = 7`.

### `hasIdToken`, `getObjects`, `victimSnapshot`, `victimRoleValues`, `scalarsForRoleKey` — B:1621–1689
- **Làm gì**:
  - `hasIdToken` cho biết tên trường có từ `id` hoặc `ids` hay không;
  - `getObjects` giữ object lấy từ phản hồi GET;
  - `victimSnapshot` lấy giá trị hiện tại của các trường role;
  - `victimRoleValues` lấy vai trò hiện tại của nạn nhân;
  - `scalarsForRoleKey` lấy giá trị vô hướng hoặc phần tử mảng dưới khoá role.
- **Ví dụ**: object `{role: "ADMIN"}` cho `victimRoleValues = [ADMIN]`.

### `setUserTargetToVictim`, `placeVictimValue` — B:1690, B:1718
- **Làm gì**: đặt nạn nhân vào trường nạn nhân của transition. Thứ tự thử: giá trị từ traffic, rồi id (nếu trường là số), rồi
  id hoặc tên (nếu tên trường có `id`), rồi tên. Nếu trường nạn nhân không nằm ở path thì đặt thêm id vào path param có điểm
  "victim" cao nhất.
- **Ví dụ**: `PATCH /users/{id}` với body `username` cho `body:username = alice` và `path:id = 7`.

### `setRoleFieldToReduced`, `keepOnlyTargetFields`, `setUserNameFieldsToVictim` — B:1735–1778
- **Làm gì**:
  - `setRoleFieldToReduced` ghi giá trị hạ quyền (mảng thì xoá rỗng);
  - `keepOnlyTargetFields` tắt các trường optional không liên quan để transition chỉ đổi role;
  - `setUserNameFieldsToVictim` ghi tên nạn nhân vào các trường str trong body trùng khoá đăng nhập.

### `setField`, `activateAncestors`, `clearArray`, `trySetFromStringValue`, `normalize` — B:1449–1480, B:1811
- **Làm gì**:
  - `setField` ghi giá trị vào gene lá rồi bật mọi wrapper phía trên (Optional bật, Choice chọn nhánh chứa lá);
  - `clearArray` xoá mọi phần tử nếu mảng cho phép rỗng;
  - `trySetFromStringValue` nuốt exception và trả false;
  - `normalize` đổi `User_Name` thành `username`.

## 7. Oracle

### `RestSecurityOracle.handleStatefulAuthorization` — O:552
- **Làm gì**: chỉ chạy khi builder đang đánh giá một bộ ba (`statefulTripleUnderEvaluation`). Hàm tìm `source` là lời gọi ghi
  2xx có xác thực và không trông giống transition, rồi tìm `follow-up` là cùng op, cùng credential, 2xx. Giữa hai lời gọi phải có
  một lời gọi 2xx của tài khoản khác trông giống transition. Có đủ thì gắn lỗi 970 vào follow-up.
- **Ví dụ**: `PUT /docs/1 [alice] 200`, rồi `PUT /users/alice/role [boss] 200`, rồi `PUT /docs/1 [alice] 200` cho 970.

## 8. Trạng thái của builder — B:602–631

| Biến | Nghĩa | Đặt lại khi |
|---|---|---|
| `privilegeReducedInPhase` | nạn nhân đã nhận một transition 2xx | `retainAll(ByProof)` mỗi transition; restore thành công |
| `privilegeReducedByProof` | nạn nhân của bộ ba hợp lệ có follow-up 403 hoặc 2xx | restore thành công |
| `refusedTransitionVictims` | cặp (transition, nạn nhân) đã bị từ chối hết | restore thành công thì xoá hết |
| `statefulTripleAttempts` | số bộ ba đã chạy, tối đa 20 | không đặt lại |
| `candidateAttempts`, `candidateProven`, `candidateIsLast` | bộ đếm của transition hiện tại | mỗi transition |
| `privilegeRestoreAttempts` | số lần restore của transition hiện tại, tối đa 3 | mỗi transition |
| `lastSourceCode`, `lastTransitionCode` | mã của lần thử gần nhất | mỗi lần thử |
| `transitionNotFoundSeen` | transition chưa chứng minh trả 404 sau source 2xx | mỗi transition |
| `victimRefused` | trong lượt của nạn nhân hiện tại có lần bị từ chối | đầu mỗi `buildStatefulAuthzTriple` |

## 9. Từ điển `RestIndividualSelectorUtils` (upstream)

Mã: `EvoMaster/core/src/main/kotlin/org/evomaster/core/problem/rest/builder/RestIndividualSelectorUtils.kt` (gọi tắt
**U**). Đây là một `object` của Kotlin, tương đương một class Java chỉ có method static. Mọi hàm tìm trong archive
những test hoặc lời gọi khớp một bộ điều kiện.

### Tên gốc

| Tên | Nghĩa |
|---|---|
| `RestIndividual` | một test: danh sách `RestCallAction`, chưa có kết quả |
| `EvaluatedIndividual<RestIndividual>` | một test đã chạy: test cộng kết quả của từng lời gọi |
| `EvaluatedAction` | một lời gọi đã chạy: cặp `(action, result)` |
| `evaluatedMainActions()` | danh sách `EvaluatedAction` của một test, theo thứ tự gọi |
| `individualsInSolution` | các test trong archive, lấy từ `archive.extractSolution()` (B:650) |
| op trong spec | một `RestCallAction` lấy từ `actionDefinitions`, chỉ dùng làm khuôn để so; chưa từng chạy |
| khuôn path | `RestPath` như `/docs/{id}`; mọi lời gọi `PUT /docs/5`, `PUT /docs/9` đều mang cùng khuôn này |

### Archive minh hoạ dùng cho mọi ví dụ

Archive này tự dựng để minh hoạ, không lấy từ lượt chạy nào.

| Test | [0] | [1] | [2] |
|---|---|---|---|
| T1 | `GET /docs` alice 200 | `PUT /docs/{id}` id=5 bob 403 | |
| T2 | `POST /docs` alice 201 | `PUT /docs/{id}` id=9 alice 200 | `DELETE /docs/{id}` id=9 alice 204 |
| T3 | `PUT /docs/{id}` id=3 boss 200 | `PUT /notes/{id}` id=2 không đăng nhập 401 | |

Op trong spec: `GET /docs`, `POST /docs`, `PUT /docs/{id}`, `DELETE /docs/{id}`, `PUT /notes/{id}`.

### `checkIfActionSatisfiesConditions` — U:22 (private)
- **Làm gì**: kiểm một lời gọi đã chạy có khớp mọi điều kiện không. Điều kiện để `null` thì bỏ qua.

  | Tham số | So với |
  |---|---|
  | `verb` | `action.verb` |
  | `path` | `action.path.isEquivalent(path)`: so từng đoạn khuôn và dấu `/` cuối (`RestPath.kt:176`) |
  | `status` | mã trả về bằng đúng số này |
  | `statusGroup` | mã trả về thuộc nhóm, ví dụ `G_2xx` |
  | `statusCodes` | mã trả về nằm trong tập |
  | `authenticated` | `true`: `action.auth` không phải `NoAuth`; `false`: ngược lại |
  | `authenticatedWith` | `action.auth.name` bằng tên tài khoản |
- **Ai gọi**: mọi hàm `find…` bên dưới.
- **Ví dụ**: lời gọi T1[1] (`PUT /docs/{id}` id=5 bob 403):
  - `verb=PUT, path=/docs/{id}, status=403` cho true;
  - `verb=PUT, path=/docs/{id}, status=200` cho false;
  - `authenticatedWith="alice"` cho false.

  Lời gọi T3[1] (không đăng nhập) với `authenticated=true` cho false.

### `findIndividuals` — U:164
- **Làm gì**: trả các **test** có ít nhất một lời gọi khớp (`any`). Trả cả test, không chỉ lời gọi khớp.
- **Ai gọi**: `guardedSources` B:773, `anyAuthenticatedSuccess` B:786, `operatorsFor` B:825; upstream
  `expandWithForbidden` B:477–501 và các oracle khác.
- **Vào và ra**: điều kiện như trên, ra `List<EvaluatedIndividual>`. Truyền cả `status` lẫn `statusGroup` thì ném
  `IllegalArgumentException`; truyền `authenticated=false` cùng `authenticatedWith` cũng ném.
- **Ví dụ**:
  - `(PUT, /docs/{id}, status=403)` cho `[T1]`;
  - `(PUT, /docs/{id}, statusGroup=G_2xx, authenticated=true)` cho `[T2, T3]`;
  - `(PUT, /docs/{id}, statusGroup=G_2xx, authenticatedWith="boss")` cho `[T3]`.

### `findAndSlice` — U:193
- **Làm gì**: gọi `findIndividuals`, rồi với mỗi test tìm lời gọi khớp **đầu tiên** (`findIndexOfAction`) và bỏ mọi
  lời gọi sau nó (`RestIndividualBuilder.sliceAllCallsInIndividualAfterAction`, `RestIndividualBuilder.kt:63`).
- **Ai gọi**: `victimSlicesOn` B:798.
- **Vào và ra**: ra `List<RestIndividual>`, là bản sao đã cắt; bản sao không mang kết quả.
- **Ví dụ**: `(PUT, /docs/{id}, statusGroup=G_2xx, authenticated=true)` cho:
  - T2 cắt sau [1]: `[POST /docs, PUT /docs/{id} id=9]`;
  - T3 cắt sau [0]: `[PUT /docs/{id} id=3]`.

  `victimSlicesOn` xếp theo độ dài, ra `[T3', T2']`, rồi lấy tài khoản của lời gọi cuối: boss, alice.

### `findIndexOfAction` — U:297
- **Làm gì**: trả vị trí của lời gọi khớp đầu tiên trong một test, `-1` khi không có.
- **Ai gọi**: `findAndSlice` U:207; upstream `handleCandidatesFor403` B:524.
- **Ví dụ**: `(PUT, /docs/{id}, statusGroup=G_2xx)` trên T2 cho `1`, trên T1 cho `-1`.

### `getIndexOfAction` — U:286 (deprecated)
- **Làm gì**: gọi thẳng `findIndexOfAction` với `verb`, `path`, `status` bắt buộc.
- **Ví dụ**: `(T1, PUT, /docs/{id}, 403)` cho `1`.

### `findEvaluatedActions` — U:139
- **Làm gì**: trả mọi **lời gọi** khớp, gom từ tất cả test theo thứ tự archive. Không nhận `statusCodes` và
  `authenticatedWith`.
- **Ai gọi**: `findVictimObjects` B:1545, `routeLooksMissing` B:1790.
- **Ví dụ**:
  - `(authenticated=true)` cho 6 lời gọi: T1[0], T1[1], T2[0], T2[1], T2[2], T3[0];
  - `(statusGroup=G_2xx)` cho 5 lời gọi: T1[0], T2[0], T2[1], T2[2], T3[0].

### `findEvaluatedAction`, `findAction` — U:92, U:78
- **Làm gì**: lấy phần tử đầu của `findEvaluatedActions`, `null` khi rỗng. `findEvaluatedAction` trả cặp
  `(action, result)`; `findAction` chỉ trả `RestCallAction`.
- **Ai gọi**: upstream B:2521.
- **Ví dụ**: `(verb=PUT, statusGroup=G_2xx)` cho T2[1]: T1 không có lời gọi khớp, T2[1] là lời gọi khớp đầu.

### `findActionsInIndividual` — U:110
- **Làm gì**: như `findEvaluatedActions` nhưng trên một test, nhận test và danh sách kết quả tách rời. Ghép lời gọi với
  kết quả theo `sourceLocalId`; lời gọi không có kết quả (test dừng giữa chừng) bị bỏ.
- **Ai gọi**: B không gọi.
- **Ví dụ**: T2 với `(verb=DELETE)` cho `[T2[2]]`.

### `getAllActionDefinitions` — U:216
- **Làm gì**: lọc op **trong spec** theo verb. Không đọc archive.
- **Ai gọi**: `guardedSources` B:769; upstream B:2370, B:2494.
- **Ví dụ**: verb `PUT` cho `[PUT /docs/{id}, PUT /notes/{id}]`.

### `findIndividualWithEndpointCreationForResource` — U:235
- **Làm gì**: tìm test đã tạo ra một resource. Thử trước `PUT` trên chính path với mã 201; không có thì thử `POST` trên
  path cha với mã 2xx. Trả test ngắn nhất cùng endpoint đã tạo, `null` khi không có.
- **Ai gọi**: B không gọi.
- **Ví dụ**: `(/docs/{id}, mustBeAuthenticated=true)`: không có `PUT /docs/{id}` nào trả 201 (T2[1], T3[0] trả 200),
  nên xét `POST /docs` 2xx, ra `(T2, POST /docs)`.
