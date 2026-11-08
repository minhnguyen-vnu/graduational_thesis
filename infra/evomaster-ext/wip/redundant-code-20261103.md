# Xoá mã thừa trên HEAD `1cd0d091f4`, 2026-11-03

Yêu cầu của user: xoá dòng và logic thừa trong phần ta thêm vào, giữ vòng `for`, không gộp lại lambda. Hành vi và log
stateful giữ nguyên. Mọi dòng dưới đây nằm trong `git diff HEAD` của repo EvoMaster, chưa commit.

Ký hiệu: `B` = `RestSecurityBuilder.kt`, `O` = `RestSecurityOracle.kt`. Tên hàm dùng để tra, vì số dòng đã dịch.

## Nhánh không bao giờ chạy tới

| Chỗ | Đã xoá | Vì sao không chạy tới |
|---|---|---|
| B `buildStatefulAuthzTriple` | `lastOrNull()?.auth ?: return false`, `if (victimAuth is NoAuth) return false` | caller duy nhất lấy slice từ `victimSlicesOn`: `findAndSlice(..., authenticated = true)` cắt ngay sau action đã qua điều kiện đó, nên action cuối tồn tại và không phải `NoAuth` |
| B `executeStatefulAuthzTriple` | `?: return false`, `if (victimAuth is NoAuth) return false` | caller duy nhất nhận cùng slice đó |
| B `reLoginProbeConfirmsPrivilegeRemoved` | `lastOrNull()?.` trong log | cùng slice, không rỗng |
| B `buildStatefulAuthzTriple` | `if (field != null)` và hai `var` | `viable` chỉ giữ op có `harvestReducedRoleCandidates` khác rỗng, tức `roleField(op) != null`; `roleField` chỉ đọc schema. Còn `?: return false` để qua kiểu |
| B `restorePlans` | `if (fields.isEmpty())` | `restoreFields` dùng đúng điều kiện của `roleField`; ở đây `roleField != null` nên danh sách có phần tử. Xoá cũng không đổi kết quả: `perField` rỗng thì `rounds = 0` |
| B `restorePlans` | `if (perField.isEmpty())` | `longest = 0`, `rounds = 0`, vòng dựng `plans` không chạy, trả danh sách rỗng |
| B `restorePrivilege` | `if (privilegeRestoreAttempts >= MAX_PRIVILEGE_RESTORES) return false` | caller duy nhất kiểm cùng điều kiện ngay trước lời gọi và biến không đổi ở giữa |
| B `restoreOperatorsAndRetry` | `?: emptyList()` | vòng trên gán `plans[operator.name]` cho mọi operator, tên auth là duy nhất (`AuthSettings.kt:17`) |
| B `findVictimObjects`, `routeLooksMissing` | `action !is RestCallAction`, `result !is RestCallResult`, thành `as` | `findEvaluatedActions` lọc bằng `checkIfActionSatisfiesConditions`, hàm này đã ép `as RestCallAction`, `as RestCallResult` |
| B `loginKeys` | `node != null &&` | `node` null thì `node.isObject` ném NPE, `catch (e: Exception)` đưa tới đúng nhánh `node == null` cũ |
| B `findVictimObjects` | `if (idKeys.isEmpty())` | `matchingKeys` trả 0 với `idKeys` rỗng, `objects` rỗng |
| B `setUserNameFieldsToVictim` | `if (idKeys.isEmpty()) return` | `normalize(f.leaf) !in idKeys` luôn đúng, `set` rỗng, không log |
| B `compareVictimObjects` | `prefix.isNotEmpty() &&` | prefix rỗng thì `startsWith` đúng ở cả hai vế; hai cờ bằng nhau, cùng kết quả với false/false |
| B `collectVictimObjects` | `if (node.isContainerNode)` | `JsonNode.iterator()` của value node và missing node rỗng |
| B `SchemaField` | `enum != null &&` | `enumValues` chỉ có phần tử khi `enum != null` |
| B `scalarsForRoleKey` | `else if (v.isObject \|\| v.isArray)` thành `else` | nhánh còn lại chỉ là NullNode và MissingNode, lặp trên chúng rỗng |
| O `handleStatefulAuthorization` | `config.isEnabledFaultCategory(...)` | `statefulTripleUnderEvaluation` chỉ true trong `executeStatefulAuthzTriple`, mà `addForStatefulAccessControl` đã thoát khi category tắt; config không đổi lúc chạy |
| O `handleStatefulAuthorization` | `filterIsInstance`, `find`, `?: continue` của follow-up | `isAllowed(followUp)` đúng nghĩa là `resultOf(followUp)` khác null; thay bằng `!!` |

## Tính lại giá trị đã có

| Chỗ | Đã xoá | Vì sao giống hệt |
|---|---|---|
| B `addForStatefulAccessControl` | `individualsInSolution = archive.extractSolution().individuals` | `applySecurityPhase` vừa gán dòng này ngay trước lời gọi, caller duy nhất; giữa hai dòng archive không đổi; `extractSolution` không có tác dụng phụ |
| B `executeStatefulAuthzTriple` | `followUp.auth = victimAuth`, `followUp.usePreviousLocationId = ...` | `followUp = source.copy()`; `copyContent` chuyển cả hai trường (`RestCallAction.kt:138–139`), `victimAuth = source.auth` |
| B `tryReducedRoles`, `restoreOperatorsAndRetry` | tham số `pair` | dựng lại từ `transitionDef` và `victimAuth` đã có sẵn |
| B `victimField` | tham số `role` | cả 4 caller truyền `roleField` của chính action đó |
| B `placeVictimValue` | `victimId(...)` thành `objectValue(objects, "id")` | `id` chỉ được dùng khi `keyed == null`, lúc đó `victimId` rơi về đúng `objectValue(objects, "id")` |
| B `rankPermissionReducingTransitions` | điều kiện viết lại | đúng thân `looksLikePermissionReducingTransition` |
| O `handleStatefulAuthorization` | `listOf(PUT, PATCH, POST, DELETE)` | đúng `TRANSITION_VERBS`, bỏ `private` |
| B `addForStatefulAccessControl` | `TransitionCandidate`, `logModelScores`, `log.isDebugEnabled` | `reducedValues` chỉ dùng cho một dòng log, gọi lại hàm thuần `harvestReducedRoleCandidates`; log giữ nguyên chữ |
| B `reducedRoleValues`, `restoreValues` | `valueScore("low", x) - valueScore("high", x)` viết lại | dùng `lowMinusHigh`; `a <= b` tương đương `a - b <= 0.0`; `sortedByDescending { h - l }` tương đương `sortedBy { l - h }`, sort ổn định, các hiệu bằng 0 đều là +0.0, trọng số hữu hạn |

## Logic rút gọn

| Chỗ | Trước | Sau | Vì sao giống hệt |
|---|---|---|---|
| B `reducedRoleValues`, enum | chia `low`, `rest`, sort từng phần rồi nối | một `sortedByDescending` | `low` đều > 0, `rest` đều <= 0, nên sort toàn bộ cho cùng thứ tự; sort ổn định giữ thứ tự gốc khi bằng điểm |
| B `reducedRoleValues`, bool | `when` 3 nhánh | `if` | nhánh `"true"` và `else` cho cùng `["false"]` |
| B `roleField`, `setUserTargetToVictim` | `score > 0.0 && (best == null \|\| score > bestScore)` | `score > bestScore` | best null thì `bestScore = 0.0`; best khác null thì `bestScore > 0` |
| B `keepOnlyTargetFields` | hai `if` lặp thân | một `if` | điều kiện `loc` loại trừ nhau; `keep` thành `List`, chỉ dùng toán tử `in` |
| B `tokens` | tách theo `TOKEN_PIECE`, chạy `TOKEN_PART` trên từng mảnh | chạy `TOKEN_PART` trên cả chuỗi | `TOKEN_PART` chỉ khớp chữ và số nên không vượt qua dấu phân cách; lookahead `(?![a-z])` ở cuối mảnh thấy dấu phân cách hoặc hết chuỗi. `TokensEquiv.java`: 2.000.000 chuỗi, 0 khác biệt trên engine Java |
| B `scalarsForRoleKey` | `nk != leaf && !leaf.startsWith(nk)` | `!leaf.startsWith(nk)` | `nk == leaf` kéo theo `startsWith` đúng |

## Khác

- Xoá `core/src/main/resources/stateful-authz-lexicon.csv`: không code nào đọc từ `a544c996ac`; bản gốc còn ở
  `infra/analysis/lexicon-rules/lexicon-20260921-audited/`.
- Xoá import `Param`, `data` của `ScoredObject`.
- Hai self-test cũ `candidate-iteration.sh:21` và `field-gate.sh:78` đọc lexicon từ jar đang kiểm, nên không chạy được trên
  jar mới; chúng thuộc các jar cũ, không skill nào gọi.

## Cố ý giữ

- Các kiểm tra trần `statefulTripleAttempts`, `candidateCapReached` ở cả vòng trong và sau vòng: bỏ một vế làm đổi log hoặc
  chạy thêm bước dựng.
- `hasPhaseTimedOut()` đầu vòng source: nhánh còn sống. Xoá nó làm đổi dòng log trên đường đã hết giờ, gồm một dòng mức
  info, và cho vòng đi sang candidate sau. Reviewer `graduational-thesis-07` chỉ ra, đã khôi phục.
- `source.auth is NoAuth` trong oracle: `actions` gồm cả phần tiền tố của slice, có thể có cặp `NoAuth` qua được các điều
  kiện còn lại.
- `followUp.bindBasedOn`, `ensureFlattenedStructure`, `fixResourceForwardLinks`: chưa chứng minh được là thừa.
- `byKey[entry.first] ?: continue` trong `restorePrivilege`: khoá lấy từ action chưa khởi tạo, chưa chứng minh được luôn
  có trong bản đã khởi tạo.
