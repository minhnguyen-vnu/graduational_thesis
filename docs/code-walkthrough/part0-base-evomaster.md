# Part 0 — Kiểu dữ liệu nền của EvoMaster

Hai class này là dữ liệu mà mọi đoạn code sau đọc và ghi. Không nắm hình dạng của chúng thì
không đọc được các part sau.

- `RestIndividual` = **một test case**. Một danh sách lời gọi HTTP có thứ tự.
- `Solution<RestIndividual>` = **cả bộ test**. Một danh sách `EvaluatedIndividual<RestIndividual>`.
- `ActionResult` = **kết quả của một lời gọi**. Cặp đôi của `RestCallAction`.
- `actionDefinitions` = **danh mục endpoint** lấy từ OpenAPI. Mẫu để dựng action mới.
- `EvaluatedIndividual<T>` = một individual **cộng kết quả chạy nó** (status code, coverage).

Toàn bộ dữ liệu dưới đây lấy từ một run thật: `infra/em-results/audit-batch/`, run
`t1-vuln-seed1-r0` (reports-api :8080 bản lỗi, seed 1, jar `R`).

---

## 1. `RestIndividual` — một test case

File: `core/src/main/kotlin/org/evomaster/core/problem/rest/data/RestIndividual.kt`, dòng 33–55.

### 1.1 Vật thật trông thế nào

Test `test_16_put_on_report_showsFaults_101_970` trong
`audit-batch/tests/t1-vuln-seed1-r0/EvoMaster_faults_Test.py` (dòng 1065). EvoMaster tự sinh
comment liệt kê nội dung individual ngay trên nó (dòng 1059–1063):

```
# 1 - (201) POST:/reports
# 2 - (200) PUT:/reports/{id}
# 3 - (200) PUT:/users/{username}/role
# 4 - (200) PUT:/reports/{id}
```

Bốn dòng đó chính là `individual.seeMainExecutableActions()`: `List<RestCallAction>`, size = 4.
Trải ra từng phần tử, giá trị đọc thẳng từ file test:

| idx | `verb` | `path` | `auth.name` | URL / body thật trong test | status |
|---|---|---|---|---|---|
| 0 | POST | `/reports` | `alice` | `/reports` body `{"title":"Report 3"}` | 201 |
| 1 | PUT | `/reports/{id}` | `alice` | `/reports/44` body `{ }` | 200 |
| 2 | PUT | `/users/{username}/role` | `superadmin` | `/users/alice/role` body `{"role":"VIEWER"}` | 200 |
| 3 | PUT | `/reports/{id}` | `alice` | `/reports/44` body `{ }` | 200 |

Đây đúng là bộ ba MR-A1: idx 1 là source, idx 2 là transition, idx 3 là follow-up. idx 0 chỉ để
tạo ra report 44 cho các bước sau dùng.

Trong file test, `auth.name` hiện ra thành biến token:

```python
token_alice      = res_alice.json()["token"]        # login alice   MỘT lần, lúc còn ADMIN
token_superadmin = res_superadmin.json()["token"]
...
headers["Authorization"] = auth_alice        # idx 1, source
headers["Authorization"] = auth_superadmin   # idx 2, transition
headers["Authorization"] = auth_alice        # idx 3, follow-up, CÙNG token với idx 1
```

Individual không chứa token. Nó chỉ chứa `auth.name = "alice"`. Token do EvoMaster login một lần
ở đầu test rồi dùng lại cho mọi action mang tên đó. Đó là lý do idx 3 dùng lại token cũ của idx 1.

### 1.2 Từng tham số constructor, giá trị thật ở test_16

| Dòng | Tham số | Kiểu | Giá trị trong test_16 |
|---|---|---|---|
| 34 | `sampleType` | `SampleType` | `SECURITY`. Đặt ở `RestSecurityBuilder.kt:632` `base.modifySampleType(SampleType.SECURITY)` |
| 35 | `sampleSpec` | `SamplerSpecification?` | `null` (chỉ dùng cho sampler theo resource) |
| 36 | `trackOperator` | `TrackOperator?` | `null` (tracking tắt mặc định) |
| 37 | `index` | `Int` | `-1` (không bật tracking thì không đánh số) |
| 38 | `allActions` | `MutableList<out ActionComponent>` | 4 phần tử, đúng bảng 1.1 |
| 39 | `mainSize` | `Int` | `4`. Số action nghiệp vụ |
| 40 | `sqlSize` | `Int` | `0`. Black-box không chèn SQL |
| 41–45 | `mongoSize`, `redisSize`, `dnsSize`, `scheduleSize`, `cleanupSize` | `Int` | `0` hết |
| 46–47 | `groups` | `GroupsOfChildren<StructuralElement>` | Một nhóm `MAIN` chứa cả 4 action, các nhóm `INITIALIZATION_SQL` / `CLEANUP` rỗng |

`sqlSize` và các size khác chia danh sách `allActions` thành từng nhóm theo thứ tự: SQL chạy trước,
MAIN ở giữa, CLEANUP cuối. Ở đây mọi size khác đều 0 nên `allActions` = MAIN = 4 lời gọi HTTP.

### 1.3 Code nào tạo ra individual này

`RestSecurityBuilder.kt` dòng 621–632, chạy trong pha SECURITY:

| Dòng | Code | Việc nó làm với test_16 |
|---|---|---|
| 621 | `base.addMainActionInEmptyEnterpriseGroup(action = transition)` | Thêm idx 2 (`PUT /users/alice/role`) vào cuối `base` |
| 623 | `val followUp = source.copy() as RestCallAction` | Nhân bản idx 1 thành idx 3 |
| 624 | `followUp.resetLocalIdRecursively()` | Cấp localId mới, nếu không idx 3 trùng id với idx 1 |
| 626 | `followUp.auth = victimAuth` | Gán `auth.name = "alice"` |
| 627 | `followUp.usePreviousLocationId = source.usePreviousLocationId` | Để idx 3 trỏ vào cùng report 44 mà idx 0 tạo |
| 629 | `base.addMainActionInEmptyEnterpriseGroup(action = followUp)` | Thêm idx 3, `mainSize` thành 4 |
| 632 | `base.modifySampleType(SampleType.SECURITY)` | Đánh dấu individual sinh ở pha SECURITY |

`base` trước dòng 621 là lát cắt lấy từ archive, gồm idx 0 và idx 1.

### 1.4 Cha của nó: `ApiWsIndividual`

`RestIndividual` kế thừa `ApiWsIndividual` (dòng 48–55) và truyền vào
`childTypeVerifier = EnterpriseChildTypeVerifier(RestCallAction::class.java, RestResourceCalls::class.java)`.
Đó là ràng buộc: con của một `RestIndividual` chỉ được là `RestCallAction` hoặc `RestResourceCalls`.
Thêm nhầm một `SqlAction` vào nhóm MAIN sẽ ném lỗi ngay lúc `verifyValidity()` (gọi ở dòng 635).

---

## 2. `RestCallAction` — một lời gọi HTTP

File: `core/src/main/kotlin/org/evomaster/core/problem/rest/data/RestCallAction.kt`, dòng 26–77.

Một `RestCallAction` = một dòng `requests.put(...)` trong file test. Nó **không** giữ token,
**không** giữ status code, **không** giữ URL đã ghép sẵn. Nó giữ verb, path template, danh sách
param và tên user.

### 2.1 Từng tham số constructor, giá trị thật ở idx 2 của test_16

idx 2 là `PUT /users/alice/role`, body `{"role":"VIEWER"}`, do `superadmin` gọi.
Giá trị dưới đây đối chiếu ba nguồn: file test đã sinh, OpenAPI `/v3/api-docs` của reports-api
(đọc live), và `infra/em-config/reports-auth.yaml`.

| Dòng | Tham số | Kiểu | Giá trị ở idx 2 |
|---|---|---|---|
| 31 | `id` | `String` | `"PUT:/users/{username}/role"`, đúng dạng `verb:path` mô tả ở comment dòng 28 |
| 32 | `verb` | `HttpVerb` | `PUT` |
| 33 | `path` | `RestPath` | `/users/{username}/role`. Còn nguyên `{username}`, chưa thay giá trị |
| 34 | `parameters` | `MutableList<Param>` | 3 phần tử: `PathParam(username)`, `QueryParam(caller)`, `BodyParam(RoleUpdateRequest)` |
| 35 | `auth` | `HttpWsAuthenticationInfo` | `name = "superadmin"`. Mặc định là `HttpWsNoAuth()`, tên `"NoAuth"` |
| 36 | `isCleanUp` | `Boolean` | `false` |
| 44 | `saveLocation` | `Boolean` | `false`. PUT này không tạo resource mới |
| 59 | `usePreviousLocationId` | `String?` | `null` |
| 60 | `produces` | `List<String>` | `["*/*"]`. Spec khai `responses.200.content` là `*/*`, nên test ghi `headers['Accept'] = "*/*"` |
| 61 | `responseRefs` | `MutableMap<String,String>` | rỗng |
| 62 | `skipOracleChecks` | `Boolean` | `false` |
| 66 | `operationId` | `String?` | `"changeRole"`, lấy từ spec |
| 67 | `links` | `List<RestLink>` | rỗng. Spec của reports-api không khai `links` |
| 68 | `backwardLinkReference` | `BackwardLinkReference?` | `null` |
| 76 | `weakReference` | `RestCallAction?` | `null` |

Ba param ở dòng 34, đọc thẳng từ spec và từ URL trong test:

| Param | Loại | Giá trị thật | Xuất hiện ở đâu trong test |
|---|---|---|---|
| `username` | `PathParam` | `"alice"` | `/users/alice/role` |
| `caller` | `QueryParam` | `{"username":"54LZkf9VOS","effectiveRole":"ADMIN"}` | `?caller=%7B%22username%22%3A%2254LZkf9VOS%22...` |
| body | `BodyParam` | `{"role":"VIEWER"}` | `body = " { \"role\" : \"VIEWER\" } "` |

`caller` là param rác do springdoc sinh nhầm (CLAUDE.md §7.2). App không đọc nó. Nó vẫn là một
`QueryParam` thật trong individual, nên vẫn bị search đột biến và vẫn hiện trong URL.

### 2.2 `path` là template, `resolvedPath()` mới là URL

| Dòng | Code | Với idx 2 |
|---|---|---|
| 33 | `val path: RestPath` | `/users/{username}/role` |
| 159–161 | `fun resolvedPath() = path.resolve(parameters)` | `/users/alice/role?caller=%7B...%7D` |
| 163–165 | `fun resolvedOnlyPath() = path.resolveOnlyPath(parameters)` | `/users/alice/role`, bỏ query |

Vì `path` là template nên hai action khác victim vẫn dùng chung một `path`. Đổi victim là đổi
`PathParam`, không đổi `path`.

### 2.3 `getName()` là khoá mà oracle dùng để ghép source với follow-up

| Dòng | Code | Giá trị |
|---|---|---|
| 147–149 | `override fun getName() = "$verb:$path"` | idx 1: `"PUT:/reports/{id}"`. idx 3: `"PUT:/reports/{id}"`. idx 2: `"PUT:/users/{username}/role"` |

`RestSecurityOracle.kt:584` lọc follow-up bằng đúng chuỗi đó:

```kotlin
if (followUp.getName() != source.getName() || followUp.auth.isDifferentFrom(source.auth)) continue
```

Trong test_16 idx 1 và idx 3 có `getName()` giống nhau vì idx 3 sinh ra bằng `source.copy()`
(`RestSecurityBuilder.kt:623`), mà `copyContent()` (dòng 129–145) giữ nguyên `id`, `verb`, `path`
và chỉ copy `parameters`. Điều kiện ghép của oracle thoả mãn theo cách dựng, không phải may.

### 2.4 `auth` chứa công thức đăng nhập, không chứa token

`HttpWsAuthenticationInfo.kt:16–22`. Field: `name`, `headers`, `endpointCallLogin`,
`requireMockHandling`, `createUsers`. Không có field nào giữ token.

Với `auth.name = "superadmin"`, `endpointCallLogin` dựng từ `infra/em-config/reports-auth.yaml`:

```yaml
- name: superadmin
  loginEndpointAuth:
    payloadUserPwd: { username: superadmin, password: "superpass", ... }
authTemplate:
  loginEndpointAuth:
    endpoint: /auth/login
    verb: POST
    token: { extractFrom: body, extractSelector: /token, sendTemplate: "Bearer {token}" }
```

Lúc chạy, EvoMaster login một lần cho mỗi tên user ở **đầu** test rồi map `name -> token`. Đó là
lý do idx 1 và idx 3 cùng `auth.name = "alice"` thì dùng chung một token, dù giữa hai bước đó
alice đã bị hạ quyền ở idx 2. Bằng chứng trong file test: chỉ có **một** lần
`post(baseUrlOfSut + "/auth/login")` cho alice, đặt ở trên cùng, trước cả idx 0.

`HttpWsNoAuth` là `HttpWsAuthenticationInfo("NoAuth", listOf(), null, false, null)`. Oracle loại
nó ngay ở dòng 574 `source.auth is NoAuth`, vì một lời gọi ẩn danh không có quyền nào để mất.

### 2.5 Chuỗi location: cách idx 3 trỏ đúng vào report 44

Trong file test:

```python
res_0 = requests.post(self.baseUrlOfSut + "/reports?caller=...")          # idx 0
location_reports__2 = "/reports" + "/" + str(res_0.json()['id'])
res_1 = requests.put(resolve_location(location_reports__2, ...))          # idx 1
res_3 = requests.put(resolve_location(location_reports__2, ...))          # idx 3
```

Tên biến `location_reports__2` sinh ra từ ba hàm, chạy tay ngược lại:

| Dòng | Code | Giá trị |
|---|---|---|
| 88 | `var saveCreatedResourceLocation = saveLocation` | idx 0: `true` |
| 90–92 | ném lỗi nếu verb không thuộc `[PUT, POST]` | idx 0 là POST, qua |
| 122 | `return path.lastElement() + "_" + k` với `k = getLocalId()` | `"reports" + "_" + "ACTION_COMPONENT_2"` |
| `RestTestCaseWriter.kt:129` | `id.replace("ACTION_COMPONENT", "")` | `"reports__2"` |
| `RestTestCaseWriter.kt:130` | `return "location_$suffix"` | `"location_reports__2"` |

Khớp đúng tên biến trong file test đã sinh. Từ đó suy ra localId của idx 0 là `ACTION_COMPONENT_2`
(`Individual.kt:115` `"${prefix}_$counter"`).

`RestSecurityBuilder.kt:627` `followUp.usePreviousLocationId = source.usePreviousLocationId` là
dòng làm idx 3 dùng lại đúng biến đó. Thiếu dòng này, idx 3 sẽ đánh vào `/reports/44` cứng và
follow-up có thể trúng resource không tồn tại, thành 404 thay vì 200 hoặc 403.

### 2.6 `seeTopGenes()` là phần search được phép đột biến

| Dòng | Code | Với idx 2 |
|---|---|---|
| 151–153 | `override fun seeTopGenes() = parameters.flatMap { it.seeGenes() }` | gene của `username`, `caller`, và `role` trong body |

`verb`, `path`, `id`, `auth` là `val`, không nằm trong gene. Search đổi được giá trị param, không
đổi được endpoint hay user của một action. Đổi user là việc của builder, gán thẳng
`action.auth = ...` (`RestSecurityBuilder.kt:626`).

---

## 3. `ActionResult` — kết quả của một lời gọi

File: `core/src/main/kotlin/org/evomaster/core/search/action/ActionResult.kt`, dòng 5–64. Cả file
63 dòng.

`RestCallAction` ở mục 2 là **request**. `ActionResult` là **response**. Một `EvaluatedIndividual`
giữ cả hai danh sách song song.

### 3.1 Điều quan trọng nhất: nó lưu MỌI THỨ vào một `Map<String,String>`

Class này **không có** field `statusCode`, **không có** field `body`. Chỉ có đúng một map,
dòng 35:

```kotlin
private val results : MutableMap<String, String> = mutableMapOf()
```

Status code được cất vào map đó dưới khoá `"STATUS_CODE"`, ép về chuỗi.
`HttpWsCallResult.kt` dòng 93–103:

```kotlin
fun setStatusCode(code: Int) {
    addResultValue(STATUS_CODE, code.toString())      // 200 thành "200"
}

fun getStatusCode(): Int? = getResultValue(STATUS_CODE)?.toInt()
```

**Đây là lý do gốc của mọi `Int?` trong code luận văn.** `getResultValue` trả `String?` vì map có
thể không có khoá đó; `?.toInt()` giữ nguyên tính nullable. Nên `statusOf()` ở
`RestSecurityOracle.kt:564` bắt buộc trả `Int?`, và dòng 568 phải có `?: return false`.

Danh sách khoá được khai báo trong companion của `HttpWsCallResult`, dòng 28–45: `STATUS_CODE`,
`BODY`, `BODY_TYPE`, `ERROR_MESSAGE`, `TOO_LARGE_BODY`, `INFINITE_LOOP`, `TIMEDOUT`,
`LAST_STATEMENT_WHEN_500`, `TCP_PROBLEM`, `INVALID_HTTP`, `APPLIED_LINK`, `LOCATION`, `ALLOW`,
`RESPONSE_TIME_MS`, `HTTP_HEADER_`, `VULNERABLE_SSRF`, `VULNERABLE_SQLI`.

Đánh đổi của thiết kế này: thêm một loại thông tin mới chỉ cần thêm một `const val`, không phải
sửa class. Đổi lại mất kiểu tĩnh, mọi thứ đọc ra đều là `String?`.

### 3.2 Ba tham số constructor

| Dòng | Tham số | Kiểu | Mặc định | Nghĩa |
|---|---|---|---|---|
| 9 | `sourceLocalId` | `String` | không có | localId của action sinh ra kết quả này |
| 12 | `stopping` | `Boolean` | `false` | kết quả này có làm dừng các action sau không |
| 22 | `deathSentence` | `Boolean` | `false` | cả `EvaluatedIndividual` bị loại, không vào archive |

`sourceLocalId` là **khoá ghép** giữa action và result. Không phải chỉ số. Lý do xem mục 6.

Khối `init` dòng 25–29 chặn id rỗng ngay lúc tạo:

```kotlin
init{
    if(sourceLocalId == StructuralElement.NONE_LOCAL_ID){
        throw IllegalArgumentException("Action results must have a valid id of the source action")
    }
}
```

`init` là khối chạy sau constructor chính. Giải thích cú pháp ở `kotlin-co-ban.md`.

### 3.3 Vật thật: result của action idx 3 trong test_16

Action idx 3 là `PUT /reports/44` do alice gọi, chính là follow-up mang fault 970. Đọc từ
`audit-batch/tests/t1-vuln-seed1-r0/EvoMaster_faults_Test.py` dòng 1157–1165:

```python
res_3 = requests.put(... "/reports/44?caller=..." , headers=headers, data=body, ...)

assert res_3.status_code == 200
assert "application/json" in res_3.headers["content-type"]
assert res_3.json()["title"] is None
assert res_3.json()["owner"] == "alice"
assert res_3.json()["classification"] is None
```

Object `RestCallResult` tương ứng:

| Chỗ chứa | Khoá | Giá trị thật |
|---|---|---|
| `results` | `STATUS_CODE` | `"200"` (chuỗi, không phải số) |
| `results` | `BODY_TYPE` | `"application/json"` |
| `results` | `BODY` | JSON có `owner` = `"alice"`, `title` = null, `classification` = null |
| `detectedFaults` | — | 1 phần tử `DetectedFault(SECURITY_STATEFUL_AUTHORIZATION, "PUT:/reports/{id}", null)` |
| constructor | `stopping` | `false`, vì test chạy tiếp tới res_4 |
| constructor | `sourceLocalId` | chưa đo, localId không in ra file test |

`getStatusCode()` trên object này trả `200`. Đường đi: đọc `results["STATUS_CODE"]` ra `"200"`,
`?.toInt()` thành `200`.

### 3.4 Chuỗi kế thừa: bốn tầng, mỗi tầng thêm một việc

`RestSecurityOracle` khai tham số kiểu `List<ActionResult>` (tầng 1) rồi ép xuống `RestCallResult`
(tầng 4) khi cần status. Bốn tầng đó là:

| Tầng | Class | File | Thêm gì |
|---|---|---|---|
| 1 | `open class ActionResult` | `search/action/ActionResult.kt:5` | map `results`, `sourceLocalId`, `stopping` |
| 2 | `abstract class EnterpriseActionResult` | `problem/enterprise/EnterpriseActionResult.kt:6` | `detectedFaults`, `addFault()`, `getFaults()` |
| 3 | `abstract class HttpWsCallResult` | `problem/httpws/HttpWsCallResult.kt:16` | các khoá HTTP, `getStatusCode()`, `setStatusCode()` |
| 4 | `class RestCallResult` | `problem/rest/data/RestCallResult.kt:13` | `getResourceId()`, chuỗi location |

Tầng 2 là nơi fault 970 được ghi vào. `EnterpriseActionResult.kt` dòng 16–20:

```kotlin
private val detectedFaults = mutableListOf<DetectedFault>()

fun addFault(fault: DetectedFault){
    detectedFaults.add(fault)
}
```

Code luận văn gọi đúng hàm đó, `RestSecurityOracle.kt` dòng 612–614:

```kotlin
result.addFault(
    DetectedFault(ExperimentalFaultCategory.SECURITY_STATEFUL_AUTHORIZATION, followUp.getName(), null)
)
```

Nên fault không nằm trong individual, không nằm trong log. Nó nằm trong **result của đúng action
gây lỗi**. Đó là lý do file test sinh ra đặt comment `# Fault970` ngay trên `res_3` chứ không phải
đầu test.

Tầng 1 và tầng 4 có hai hàm `open` để tầng dưới ghi đè, dòng 42 và 63:

```kotlin
open fun copy() : ActionResult { return ActionResult(this) }
open fun matchedType(action: Action) = true
```

`RestCallResult` ghi đè cả hai, dòng 25 và 56. Từ khoá `open` giải thích ở `kotlin-co-ban.md`.

### 3.5 Ghép action với result: theo `localId`, không theo chỉ số

Danh sách action và danh sách result **không nhất thiết dài bằng nhau**. Test bị dừng giữa chừng
thì `results` ngắn hơn. Vì vậy mọi chỗ trong code luận văn đều ghép theo `sourceLocalId`:

```kotlin
actionResults.find { it.sourceLocalId == a.getLocalId() }
```

Ghép theo chỉ số `actionResults[i]` sẽ lệch ngay khi có một action không chạy. Chi tiết ở mục 6.

---

## 4. `actionDefinitions` — danh mục endpoint lấy từ OpenAPI

File khai báo: `RestSecurityBuilder.kt` dòng 156. Kiểu `List<RestCallAction>`.

Ba mục trên là **dữ liệu của một test đã chạy**. Mục này là thứ khác hẳn: **danh mục mẫu**, một
phần tử cho mỗi endpoint trong schema, không thuộc test nào.

### 4.1 Nó từ đâu ra

| Bước | Code | Việc |
|---|---|---|
| 1 | `RestActionBuilderV3.addActionsFromSwagger(schemaHolder, actionCluster, ...)` | đọc OpenAPI, dựng một `RestCallAction` cho mỗi endpoint |
| 2 | `Sampler.kt:45` `actionCluster: MutableMap<String, Action>` | cất vào map, khoá là tên endpoint |
| 3 | `Sampler.kt:54` `getActionDefinitions()` | trả `actionCluster.values.map { it.copy() }` |
| 4 | `RestSecurityBuilder.kt:174` | `actionDefinitions = sampler.getActionDefinitions() as List<RestCallAction>` |

Bước 4 nằm trong hàm `postInit()` đánh dấu `@PostConstruct` (dòng 171), nên nó chạy **một lần**,
ngay sau khi Guice tiêm xong các field, trước cả search.

Bước 3 trả **bản sao** (`it.copy()`). Sửa một phần tử trong `actionDefinitions` không đụng tới
danh mục gốc của sampler.

### 4.2 Kích thước thật, ba target

| Target | `actionDefinitions.size` | Nguồn |
|---|---|---|
| `reports-api` | **9** | `audit-batch/logs/t1-vuln-seed1-r0.log` dòng 15 |
| `vampi-seeded` | 16 | `docs/tier2-seeded-benchmark-plan.md` |
| pyLoad | **105** | `tier2b-restore-trials/logs/vuln-noreset-seed1.log` dòng 16 |

Log in ra nguyên văn: `There are 9 usable RESTful API endpoints defined in the schema configuration`.

Chín phần tử của `reports-api`, đọc live từ `http://localhost:8080/v3/api-docs`:

```
POST /auth/login      GET /users/me        PUT /users/{username}/role
GET  /reports         POST /reports        POST /reset
GET  /reports/{id}    PUT  /reports/{id}   DELETE /reports/{id}
```

### 4.3 Quan hệ với ba kiểu ở mục 1, 2, 3

Cùng kiểu `RestCallAction` với mục 2, khác **vai trò**:

| | `actionDefinitions` | action trong một `RestIndividual` |
|---|---|---|
| Số lượng | 9, cố định cả run | 4 ở test_16, thay đổi theo test |
| `path` | `/reports/{id}` còn nguyên template | vẫn là template, nhưng gene đã có giá trị `44` |
| Gene | giá trị mặc định, chưa đột biến | đã bị search đột biến |
| `auth` | `NoAuth` | `alice` / `superadmin` |
| Có `ActionResult` không | **không**, chưa bao giờ được gọi | có, ghép theo `localId` |

Một câu: **`actionDefinitions` là thực đơn, `RestIndividual` là bữa ăn đã gọi, `ActionResult` là
hoá đơn.** Không có `ActionResult` nào ứng với `actionDefinitions`, vì danh mục không được gửi đi.

Đường đi của một endpoint:

```
OpenAPI /v3/api-docs
   PUT /users/{username}/role
        |  addActionsFromSwagger
        v
   actionDefinitions[i]   RestCallAction, auth=NoAuth, gene mặc định
        |  copy() rồi gán auth, gán gene
        v
   action idx 2 trong test_16   PUT /users/alice/role, auth=superadmin
        |  gửi đi, nhận response
        v
   RestCallResult   results["STATUS_CODE"]="200"
```

### 4.4 Code luận văn dùng nó ở đâu

Hai chỗ, cả hai đều là **suy diễn từ schema**, không phải từ test đã chạy:

**a. Tìm endpoint transition.** `RestSecurityBuilder.kt` dòng 711–725:

```kotlin
private fun findPermissionReducingTransition(): RestCallAction? {
    val preferredOrder = listOf(HttpVerb.PUT, HttpVerb.PATCH, HttpVerb.POST, HttpVerb.DELETE)
    return actionDefinitions
        .filter { it.verb in preferredOrder }
        .sortedBy { preferredOrder.indexOf(it.verb) }
        .firstOrNull { a -> ... }
}
```

Quét cả 9 endpoint của `reports-api`, chọn `PUT /users/{username}/role`. Đây là lý do suy diễn
transition **không phụ thuộc vào search**: schema luôn có đủ 9 mục, kể cả khi search chưa gọi
endpoint đó lần nào.

**b. Lấy từ vựng enum để đoán giá trị role.** Dòng 729 và 751:

```kotlin
val enumVocab = (allGenes(transition) + actionDefinitions.flatMap { allGenes(it) })
```

Gom gene của **mọi** endpoint để tìm các giá trị enum kiểu `ADMIN` / `VIEWER`. Trên pyLoad cách
này thất bại vì `role` khai kiểu `integer`, không có enum để gom — chính là blocker R2 ở
`docs/tier2b-pyload-target.md`.

### 4.5 Vì sao mục này quan trọng với luận văn

`actionDefinitions` là **cầu nối giữa schema và bộ ba MR-A1**. Ba mục trên chỉ mô tả những gì
search đã làm; muốn dựng một transition mà search chưa từng gọi thì phải lấy mẫu từ đây. Đó là
điều `RestSecurityBuilder` làm và Şahin baseline không làm.

---

## 5. `Solution<T>` — cả bộ test

File: `core/src/main/kotlin/org/evomaster/core/search/Solution.kt`, dòng 14–22.

### 5.1 Từng tham số, giá trị thật ở run `t1-vuln-seed1-r0`

| Dòng | Tham số | Kiểu | Giá trị thật |
|---|---|---|---|
| 15 | `individuals` | `MutableList<EvaluatedIndividual<T>>` | **54** phần tử lúc vào pha MINIMIZATION, **63** lúc ghi ra đĩa |
| 16 | `testSuiteNamePrefix` | `String` | `"EvoMaster"` (`EMConfig.kt:1293`, mặc định) |
| 17 | `testSuiteNameSuffix` | `String` | `"Test"` (`EMConfig.kt:1300`, mặc định) |
| 18 | `termination` | `Termination` | `NONE` khi `extractSolution()` trả về (`Archive.kt:108`) |
| 19 | `individualsDuringSeeding` | `List<EvaluatedIndividual<T>>` | rỗng, không dùng seeding |
| 20 | `targetsDuringSeeding` | `List<Int>` | rỗng |

Hai con số 54 và 63 đọc từ `audit-batch/logs/t1-vuln-seed1-r0.log`:

```
537: * Recomputing full coverage for 54 tests      <- archive lúc vào MINIMIZATION
552: * Starting phase SECURITY
553: * Assembled a stateful-authorization (MR-A1) triple on PUT:/reports/{id} (victim 'alice', operator 'superadmin', ...)
558: * Going to save 63 tests
```

### 5.2 `termination` quyết định tên file, kiểm chứng được trên đĩa

`getFileName()` (dòng 42–53): `baseName = testSuiteNamePrefix + termination.suffix`, rồi nối
`testSuiteNameSuffix` bằng dấu `_`.

`TestSuiteSplitter.kt:269–294` chia một `Solution` termination `NONE` thành ba `Solution` mới:

| `Solution` | `termination` | `.suffix` | Tên file sinh ra | Số test đếm thật |
|---|---|---|---|---|
| faults | `FAULTS` | `"_faults"` | `EvoMaster_faults_Test.py` | 48 |
| successes | `SUCCESSES` | `"_successes"` | `EvoMaster_successes_Test.py` | 15 |
| remainder | `OTHERS` | `"_others"` | không sinh, list rỗng | 0 |

48 + 15 = 63, khớp dòng log 558. Đếm bằng `grep -c "def test_"` trên hai file.

### 5.3 Khối `init` cộng dồn fitness

Dòng 30–36:

| Dòng | Code | Với run này |
|---|---|---|
| 31 | `individuals.forEach {` | Duyệt 63 phần tử |
| 32 | `overall.merge(it.fitness)` | Gộp coverage của từng test thành coverage toàn bộ. Kết quả in ra log dòng 560: `8 endpoints out of 9 (89%)` |
| 33 | `overall.size += it.individual.size()` | Cộng số action. test_16 góp 4 |

---

## 6. `EvaluatedIndividual<T>` — individual cộng kết quả

File: `core/src/main/kotlin/org/evomaster/core/search/EvaluatedIndividual.kt`, dòng 36–54.

| Dòng | Field | Kiểu | Với test_16 |
|---|---|---|---|
| 37 | `fitness` | `FitnessValue` | Tập target mà 4 lời gọi này phủ được |
| 38 | `individual` | `T` = `RestIndividual` | Đúng object ở mục 1 |
| 44 | `results` | `List<ActionResult>` | 4 `RestCallResult`, status `201, 200, 200, 200` |

Chú thích ngay tại dòng 40–43 của source nói rõ: test có thể bị dừng giữa chừng, nên
**`results` có thể ít phần tử hơn `individual`**. Vì vậy code không được ghép action với result
theo chỉ số. Nó ghép theo `localId` — `RestSecurityOracle.kt:564–565`:

```kotlin
fun statusOf(a: RestCallAction): Int? =
    (actionResults.find { it.sourceLocalId == a.getLocalId() } as RestCallResult?)?.getStatusCode()
```

Trả `null` khi action không có result. Dòng 568 biến `null` thành `isAllowed = false`, nên một
lời gọi không chạy được không bao giờ bị đọc nhầm thành 2xx.

---

## 7. Đường đi của dữ liệu, gói lại một câu mỗi bước

| Bước | Object | Số đo thật ở `t1-vuln-seed1-r0` |
|---|---|---|
| Search sinh test | `Archive` giữ các `EvaluatedIndividual` | 54 test |
| `archive.extractSolution()` | `Solution<RestIndividual>` termination `NONE` | `individuals` 54 phần tử |
| `applySecurityPhase()` dòng 194 đọc ra | `individualsInSolution: List<EvaluatedIndividual<RestIndividual>>` | 54 phần tử |
| Builder cắt lát rồi ghép thêm 2 action | một `RestIndividual` mới, `sampleType = SECURITY` | 4 action, chính là test_16 |
| Oracle đọc `individual` + `results` | ghép theo `localId` | `200 / 200 / 200`, phát fault 970 |
| `TestSuiteSplitter` chia | 3 `Solution` theo `termination` | 48 + 15 + 0 |
| Ghi đĩa | file `.py` | `EvoMaster_faults_Test.py` chứa test_16 |

Fault 970 của run này nằm trong `report.json`:

```json
{ "operationId": "PUT:/reports/{id}",
  "testCaseId": "EvoMaster_faults_Test.py#test_16_put_on_report_showsFaults_101_970",
  "faultCategories": [ {"code": 101}, {"code": 101}, {"code": 970} ] }
```
