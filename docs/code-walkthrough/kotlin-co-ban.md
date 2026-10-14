# Kotlin cơ bản cho người viết Java

Tài liệu tra cứu, không phải một part của walkthrough. Đọc file này trước Part 1–5 nếu chưa
viết Kotlin bao giờ.

Mọi đoạn code trong file này lấy nguyên văn từ hai file thật:

- `B` = `core/src/main/kotlin/org/evomaster/core/problem/rest/service/RestSecurityBuilder.kt`
- `O` = `core/src/main/kotlin/org/evomaster/core/problem/rest/oracle/RestSecurityOracle.kt`

Repo `/Users/minhnguyen/IdeaProjects/EvoMaster`, branch `stateful-authz-oracle`, HEAD `007e5e09f9`.
Số dòng là số dòng của HEAD này.

---

## 1. `companion object` — chỗ chứa `static` của Kotlin

Kotlin **không có từ khoá `static`**. Muốn có thành viên thuộc về class chứ không thuộc về
instance thì bỏ nó vào một khối `companion object` bên trong class. Mỗi class có tối đa một khối.

Code thật, `B` dòng 62–77:

```kotlin
class RestSecurityBuilder : TimeBoxedPhase {

    companion object {
        private val log: Logger = LoggerFactory.getLogger(RestSecurityBuilder::class.java)

        private val TRANSITION_PATH_SIGNALS =
            listOf("role","permission","member","subscription","plan","owner","grant","access")

        private val TRANSITION_VERBS =
            listOf(HttpVerb.PUT, HttpVerb.PATCH, HttpVerb.POST, HttpVerb.DELETE)

        private const val MAX_STATEFUL_TRIPLE_ATTEMPTS = 8

        private const val MAX_STATEFUL_TRIPLE_ATTEMPTS_DECLARED = 40

        private const val MAX_PRIVILEGE_RESTORES = 3
```

Đối chiếu từng dòng với Java:

| Dòng | Kotlin | Java tương đương |
|---|---|---|
| 62 | `class RestSecurityBuilder : TimeBoxedPhase {` | `class RestSecurityBuilder implements TimeBoxedPhase {` |
| 64 | `companion object {` | không có dòng nào; nó chỉ là cái hộp |
| 65 | `private val log: Logger = ...` | `private static final Logger log = ...` |
| 65 | `RestSecurityBuilder::class.java` | `RestSecurityBuilder.class` |
| 67–68 | `private val TRANSITION_PATH_SIGNALS = listOf(...)` | `private static final List<String> ... = List.of(...)` |
| 73 | `private const val MAX_STATEFUL_TRIPLE_ATTEMPTS = 8` | `private static final int ... = 8` |

Dấu `:` sau tên class ở dòng 62 làm cả hai việc của Java: `extends` và `implements`. Kotlin phân
biệt bằng cái đứng sau là class hay interface, người viết không phải chọn từ khoá.

### 1.1 `val` trong companion khác `const val` thế nào

| | `val` (dòng 65, 67, 70) | `const val` (dòng 73, 75, 77) |
|---|---|---|
| Tính lúc nào | lúc class được nạp, chạy code khởi tạo | lúc biên dịch, giá trị nhúng thẳng vào bytecode |
| Kiểu cho phép | bất kỳ | chỉ `String` và kiểu nguyên thuỷ |
| Java tương đương | `static final` | `static final` hằng biên dịch |

`TRANSITION_PATH_SIGNALS` phải là `val` vì `listOf(...)` là một lời gọi hàm, không phải hằng biên
dịch. `MAX_STATEFUL_TRIPLE_ATTEMPTS = 8` là số nguyên nên dùng được `const val`.

### 1.2 Gọi từ ngoài trông y hệt Java

`O` dòng 577 gọi hàm nằm trong companion của `B`:

```kotlin
|| RestSecurityBuilder.looksLikePermissionReducingTransition(source, config.statefulAuthzTransition)) {
```

Viết `TenClass.tenHam(...)`, giống hệt gọi static method Java. Không phải viết
`RestSecurityBuilder.Companion.looksLike...` trừ khi gọi từ file Java thật.

Đây là lý do hàm này nằm trong companion: nó là **vị từ dùng chung** giữa dựng bộ ba (`B`) và
phán xử (`O`). Để nó là method thường thì `O` phải giữ một tham chiếu tới một instance của `B`.

### 1.3 Companion còn chứa được cả class con

`B` dòng 90–94, ngay trong companion:

```kotlin
data class DeclaredTransition(
    val verb: HttpVerb,
    val path: String,
    val bindings: Map<String, String>
)
```

Tương đương `static class DeclaredTransition` lồng trong Java. Đọc tiếp mục 9 về `data class`.

---

## 2. `val` và `var`

| Kotlin | Java |
|---|---|
| `val x = 5` | `final var x = 5` |
| `var x = 5` | `var x = 5` |

`val` là mặc định nên dùng nhiều hơn hẳn. Trong `handleStatefulAuthorization` (`O` 552–617) có
8 chỗ `val` và 0 chỗ `var`.

Kiểu được suy ra, không phải ghi:

```kotlin
val actions = individual.seeMainExecutableActions()   // O:562
```

`actions` có kiểu `List<RestCallAction>`, trình biên dịch tự lấy từ kiểu trả về của hàm. Ghi rõ
kiểu vẫn được, cú pháp là `val actions: List<RestCallAction> = ...`. Ở `B` dòng 65 người ta ghi
rõ `: Logger` mặc dù suy ra được.

## 3. `lateinit var` — dành cho dependency injection

`B` dòng 120–151 có 11 field kiểu này:

```kotlin
@Inject
private lateinit var archive: Archive<RestIndividual>

@Inject
private lateinit var config: EMConfig
```

Vấn đề nó giải: Kotlin bắt mọi biến non-null phải có giá trị lúc khởi tạo. Field do Guice tiêm
vào thì lúc constructor chạy chưa có gì. `lateinit` là lời hứa "tôi sẽ gán trước khi đọc".

| Tính chất | Hệ quả |
|---|---|
| Phải là `var` | `lateinit val` không biên dịch được |
| Không dùng cho kiểu nguyên thuỷ | `lateinit var x: Int` không biên dịch được |
| Đọc trước khi gán | ném `UninitializedPropertyAccessException` lúc chạy |

Java không cần thứ này vì field mặc định là `null`. Kotlin thì `Archive<RestIndividual>` là kiểu
non-null nên `null` không hợp lệ.

### 3.1 `by lazy` — khởi tạo trễ, cách khác

`B` dòng 387, code của luận văn:

```kotlin
private val resetClient: Client by lazy { HttpClientFactory.createTrustingJerseyClient() }
```

Khối `{ }` chỉ chạy ở **lần đọc `resetClient` đầu tiên**, kết quả được nhớ lại cho các lần sau.
Run nào không bật cờ `--statefulAuthzResetEndpoint` thì `resetSutState()` thoát ở dòng 392 trước
khi chạm tới `resetClient`, nên HTTP client không bao giờ được tạo.

| | `lateinit var` | `val ... by lazy { }` |
|---|---|---|
| Ai gán giá trị | code bên ngoài, ví dụ Guice | chính khối `{ }` |
| `val` hay `var` | bắt buộc `var` | bắt buộc `val` |
| Chạy khối lúc nào | không có khối | lần đọc đầu tiên |

Java tương đương phải tự viết `if (field == null) field = ...` trong getter.

---

## 4. Null — phần khác Java nhiều nhất

Kotlin chia mọi kiểu làm hai: `Int` không bao giờ null, `Int?` có thể null. Trình biên dịch ép
kiểm tra. Bốn toán tử phải thuộc.

### 4.1 `?` — khai báo kiểu có thể null

`O` dòng 564:

```kotlin
fun statusOf(a: RestCallAction): Int? =
    (actionResults.find { it.sourceLocalId == a.getLocalId() } as RestCallResult?)?.getStatusCode()
```

`Int?` nói thẳng: hàm này có thể trả về `null`. Người gọi bắt buộc phải xử lý. Trong Java chữ ký
là `Integer statusOf(...)` và không có gì ép người gọi làm gì cả.

### 4.2 `?.` — gọi an toàn

`x?.foo()` nghĩa là: `x` null thì cả biểu thức là `null`, không gọi `foo()`, không ném NPE.
Trong dòng 565 trên, nếu `find` không tìm thấy thì `as RestCallResult?` cho `null`, `?.` chặn
lại, kết quả là `null`.

Viết bằng Java thì phải:

```java
RestCallResult ar = (RestCallResult) actionResults.stream()...findFirst().orElse(null);
return ar == null ? null : ar.getStatusCode();
```

### 4.3 `?:` — toán tử Elvis, thay giá trị mặc định

`a ?: b` nghĩa là "`a` nếu khác null, ngược lại `b`". Giống `a != null ? a : b` của Java.

Vế phải được phép là `return` hoặc `continue`, đây là chỗ Java không có. `O` dòng 568:

```kotlin
fun isAllowed(a: RestCallAction): Boolean {
    val code = statusOf(a) ?: return false
    return StatusGroup.G_2xx.isInGroup(code)
}
```

Đọc là: lấy status; không có thì thoát hàm trả `false` luôn. Sau dòng 568, `code` có kiểu `Int`
chứ không phải `Int?`, nên dòng 569 dùng thẳng được.

`O` dòng 601–604 dùng dạng `?: continue`:

```kotlin
val result = actionResults
    .filterIsInstance<RestCallResult>()
    .find { it.sourceLocalId == followUp.getLocalId() }
    ?: continue
```

Không tìm thấy kết quả thì bỏ qua vòng lặp này.

Dạng thứ ba, giá trị thường, `B` dòng 654:

```kotlin
.joinToString("/") { it?.toString() ?: "-" }
```

Status null thì in ra dấu gạch.

### 4.4 `as` và `as?` — ép kiểu

| Cú pháp | Sai kiểu thì |
|---|---|
| `x as RestCallResult` | ném `ClassCastException` |
| `x as RestCallResult?` | ép sang kiểu nullable, `null` đi qua được |
| `x as? RestCallResult` | trả `null`, không ném |

`B` dòng 647 dùng `as?`:

```kotlin
(ei.seeResult(a.getLocalId()) as? RestCallResult)?.getStatusCode()
```

`O` dòng 565 dùng `as ... ?`. Hai cách này khác nhau: `as?` nuốt cả trường hợp đúng-là-không-null
nhưng sai kiểu; `as X?` vẫn ném nếu đối tượng khác kiểu.

### 4.5 `!!` — bắt trình biên dịch im

`x!!` khẳng định `x` khác null, sai thì ném NPE. Trong 699 dòng của luận văn có **đúng một** chỗ
dùng nó. Kiểm chứng:

```
$ git diff v6.1.1..HEAD | grep -n '^+.*!!'
548:+        if (StatusGroup.G_2xx.isInGroup(followUpCode!!)
```

Chỗ đó là `B` dòng 672. Lý do nó phải có, đọc ngược lên `B` dòng 660–662:

```kotlin
val valid = sourceCode != null && StatusGroup.G_2xx.isInGroup(sourceCode)
    && transitionCode != null && StatusGroup.G_2xx.isInGroup(transitionCode)
    && followUpCode != null && followUpCode != 401

if (!valid) {
    ...
    return false
}

if (StatusGroup.G_2xx.isInGroup(followUpCode!!)      // dòng 672
```

Dòng 662 đã kiểm tra `followUpCode != null`, nhưng kết quả kiểm tra đó bị cất vào biến `valid`.
Trình biên dịch không lần được từ `valid == true` ngược về `followUpCode != null`, nên tới dòng
672 nó vẫn coi `followUpCode` là `Int?`. `!!` là chỗ người viết nhận trách nhiệm.

Ép kiểu thông minh chỉ chạy khi phép kiểm tra nằm trực tiếp trong `if`, ví dụ `B` dòng 656:

```kotlin
if (transitionCode != null && StatusGroup.G_2xx.isInGroup(transitionCode)) {
```

Ở đây `transitionCode` sau dấu `&&` đã tự có kiểu `Int`, không cần `!!`.

---

## 5. `fun` — khai báo hàm

### 5.1 Dạng đầy đủ

`O` dòng 552–556:

```kotlin
private fun handleStatefulAuthorization(
    individual: RestIndividual,
    actionResults: List<ActionResult>,
    fv: FitnessValue
) {
```

Ba khác biệt so với Java: từ khoá `fun`; kiểu đứng **sau** tên, ngăn bởi `:`; không ghi kiểu trả
về nghĩa là trả `Unit`, tương đương `void`.

### 5.2 Dạng biểu thức, dùng dấu `=`

`O` dòng 564:

```kotlin
fun statusOf(a: RestCallAction): Int? =
    (actionResults.find { ... } as RestCallResult?)?.getStatusCode()
```

Thân hàm là một biểu thức duy nhất nên bỏ `{ }` và `return`. Java 21 không có dạng này cho method.

### 5.3 Hàm lồng trong hàm

`statusOf` và `isAllowed` (`O` 564–570) khai báo **bên trong** `handleStatefulAuthorization`.
Chúng nhìn thấy biến `actionResults` của hàm ngoài mà không cần truyền vào. Java phải dùng
lambda gán vào biến, hoặc tách thành private method rồi truyền thêm tham số.

### 5.4 Tham số mặc định

Cú pháp là `ten: Kieu = giaTri`. `B` dòng 79 khai báo một cái:

```kotlin
fun looksLikePermissionReducingTransition(a: RestCallAction, declared: String = ""): Boolean {
```

Cả repo chỉ có 2 nơi gọi hàm này, `O` dòng 577 và `O` dòng 595, và **cả hai đều truyền đủ 2 tham
số**. Giá trị mặc định `""` chưa bao giờ được dùng tới:

```
$ grep -rn "looksLikePermissionReducingTransition" core/src/
...RestSecurityBuilder.kt:79:        fun looksLikePermissionReducingTransition(a: RestCallAction, declared: String = ""): Boolean {
...RestSecurityOracle.kt:577:                || RestSecurityBuilder.looksLikePermissionReducingTransition(source, config.statefulAuthzTransition)
...RestSecurityOracle.kt:595:                        && RestSecurityBuilder.looksLikePermissionReducingTransition(t, config.statefulAuthzTransition)
```

Ví dụ tham số mặc định **có** chạy thật nằm ở hàm gốc của EvoMaster,
`EnterpriseIndividual.kt` dòng 284:

```kotlin
fun addMainActionInEmptyEnterpriseGroup(relativePosition: Int = -1, action: MainAction){
```

`B` gọi nó 3 lần, dòng 621, 629 và một lần trong nhánh operator restore:

```kotlin
base.addMainActionInEmptyEnterpriseGroup(action = transition)
```

Bỏ qua tham số thứ nhất, lấy mặc định `-1`. `EnterpriseIndividual.kt` dòng 288 đọc `-1` là
"nối vào cuối danh sách", nên transition rơi đúng vào cuối individual. Muốn bỏ tham số **đứng
trước** thì bắt buộc phải gọi tham số sau theo tên, đó là lý do có chữ `action =`.

Java phải viết hai overload cho việc này.

### 5.5 Tham số gọi theo tên

`B` dòng 81:

```kotlin
a.path.toString().equals(it.path, ignoreCase = true)
```

`ignoreCase = true` ghi rõ tên tham số ngay tại chỗ gọi. `B` dòng 111 cũng vậy:
`p.split("=", limit = 2)`.

---

## 6. Chuỗi — template thay cho nối bằng `+`

`$ten` chèn giá trị một biến. `${bieu.thuc}` chèn một biểu thức.

`RestCallAction.kt` dòng 147–149:

```kotlin
override fun getName(): String {
    return "$verb:$path"
}
```

Với action `POST /json/status` thì `verb` là `POST`, `path` là `/json/status`, kết quả là chuỗi
`"POST:/json/status"`. Đây chính là cái xuất hiện trong log thật
`infra/em-results/tier2b-restore-trials/logs/vuln-noreset-seed1.log` dòng 3411.

`B` dòng 666–667, template nhiều biến:

```kotlin
"Discarded a VOID stateful-authorization (MR-A1) attempt on ${source.getName()}" +
    " (victim '${victimAuth.name}', operator '${operator.name}', codes $observed)"
```

Cho ra đúng dòng log 3411:

```
Discarded a VOID stateful-authorization (MR-A1) attempt on POST:/json/status (victim 'pyload', operator 'alice', codes 200/401/200)
```

Muốn in dấu `$` thật thì viết `\$`.

---

## 7. Lambda và collection

### 7.1 `it` — tham số ngầm định

Lambda một tham số không cần đặt tên, Kotlin gọi nó là `it`.

`B` dòng 87:

```kotlin
return TRANSITION_PATH_SIGNALS.any { hay.contains(it) }
```

`it` ở đây là một chuỗi trong danh sách 8 signal. Java: `.anyMatch(s -> hay.contains(s))`.

### 7.2 Lambda cuối được đưa ra ngoài ngoặc

`list.any { ... }` thực ra là `list.any({ ... })`. Kotlin cho phép kéo lambda cuối cùng ra sau
dấu `)`, và nếu lambda là tham số duy nhất thì bỏ luôn `()`.

`B` dòng 654 là trường hợp có hai tham số:

```kotlin
.joinToString("/") { it?.toString() ?: "-" }
```

Dạng đầy đủ là `joinToString("/", transform = { ... })`.

### 7.3 Khi nào dùng `it`, khi nào phải đặt tên

**Luật: `it` chỉ tồn tại một cái.** Lambda lồng trong lambda thì `it` bên trong **che** `it` bên
ngoài, và cái ngoài mất luôn, không có cú pháp nào gọi lại được. Nên hễ cần dùng biến của lambda
ngoài ở bên trong, lambda ngoài **bắt buộc** phải đặt tên.

Số đo trong 699 dòng của luận văn: **31 lambda dùng `it`**, **13 lambda đặt tên tay**.

#### Ví dụ đủ ba tầng — `B` dòng 474–482

```kotlin
fun guardedCandidatesFor(verbs: List<HttpVerb>) = verbs.flatMap { verb ->
    RestIndividualSelectorUtils.getAllActionDefinitions(actionDefinitions, verb)
        .filter { op ->
            op.path != transition.path
                && RestIndividualSelectorUtils.findIndividuals(
                    individualsInSolution, verb, op.path, status = 403
                ).isNotEmpty()
        }
        .map { verb to it }
}
```

| Lambda | Tham số | Kiểu | Vì sao tên đó |
|---|---|---|---|
| `flatMap` dòng 474 | `verb` | `HttpVerb` | **bắt buộc**: dòng 479 dùng nó bên trong lambda `filter` |
| `filter` dòng 476 | `op` | `RestCallAction` | **bắt buộc**: nếu để `it` thì che mất `verb` |
| `map` dòng 482 | `it` | `RestCallAction` | không lồng gì nữa, để `it` được |

Dòng 479 là chỗ chốt. Nếu dòng 474 viết `verbs.flatMap { ... }` không đặt tên, thì tới dòng 479
`it` đã là tham số của `filter` rồi, không cách nào lấy lại verb.

#### Ví dụ hai tầng — `B` dòng 716–723

```kotlin
.firstOrNull { a ->
    val hay = (a.path.toString() + " " + a.getName()).lowercase()
    val pathSignal = transitionPathSignals.any { hay.contains(it) }
    val hasUserParam = allGenes(a).any { g ->
        val n = g.name.lowercase()
        transitionUserParamSignals.any { n == it || n.contains(it) }
    }
    pathSignal && hasUserParam
}
```

| Dòng | Lambda | Tham số | Kiểu |
|---|---|---|---|
| 716 | `firstOrNull` | `a` | `RestCallAction` |
| 718 | `any` | `it` | `String`, một signal |
| 719 | `any` | `g` | `Gene` |
| 721 | `any` | `it` | `String`, một signal |

Bốn lambda, hai cái ngoài đặt tên, hai cái trong cùng để `it`. Cứ đi từ trong ra: cái trong cùng
luôn được `it`.

#### Ba lý do phải đặt tên

| Lý do | Ví dụ thật |
|---|---|
| Có lambda lồng, cần biến ngoài ở trong | `B` 474 `verb`, 476 `op`, 716 `a`, 719 `g`, 734 `v`, 761 `g` |
| Huỷ cấu trúc, hai giá trị nên `it` không đủ | `B` 878 `{ (name, raw) -> ... }` |
| Thân lambda dài, đọc `it` khó lần | `B` 530 `{ o -> ... }`, 5 dòng, không lồng gì cả |

#### Tên đặt theo chữ cái đầu của kiểu

Đây là quy ước của code EvoMaster, không phải luật Kotlin. Thống kê 13 chỗ đặt tên:

| Tên | Số lần | Kiểu | Đọc là |
|---|---|---|---|
| `v` | 4 | `String` | value |
| `g` | 4 | `Gene` | gene |
| `a` | 1 | `RestCallAction` | action |
| `o` | 1 | `AuthenticationDto` | operator |
| `op` | 1 | `RestCallAction` | operation |
| `p` | 1 | `String` | part |
| `verb` | 1 | `HttpVerb` | verb |

Lambda ngắn thì một chữ. Cần rõ nghĩa thì viết đủ như `verb`.

#### Ngược lại: chỗ nào để `it` cho gọn

`it` hợp khi lambda **một dòng, không lồng**. `B` dòng 529:

```kotlin
.filter { !privilegeReducedInPhase.contains(it.name) }
```

Đặt tên ở đây chỉ làm dài dòng.

### 7.4 Các hàm collection dùng trong code luận văn

Không cần `.stream()` và `.collect(...)`, gọi thẳng trên `List`.

| Kotlin | Java Stream | Trả về | Dùng ở |
|---|---|---|---|
| `.any { }` | `.anyMatch()` | `Boolean` | `B` 87, `O` 591 |
| `.filter { }` | `.filter()` | `List` | `B` 529 |
| `.map { }` | `.map()` | `List` | `B` 482 |
| `.find { }` | `.filter().findFirst().orElse(null)` | `T?` | `O` 565 |
| `.firstOrNull { }` | như trên | `T?` | `B` 445 |
| `.lastOrNull()` | không có sẵn | `T?` | `B` 521 |
| `.mapNotNull { }` | `.map().filter(Objects::nonNull)` | `List` | `B` 111 |
| `.filterIsInstance<T>()` | `.filter(x -> x instanceof T).map(x -> (T) x)` | `List<T>` | `O` 602 |
| `.joinToString(sep) { }` | `.map().collect(joining(sep))` | `String` | `B` 654 |
| `.associate { k to v }` | `.collect(toMap())` | `Map` | `B` 112 |
| `.drop(n)` | `.skip(n)` | `List` | `B` 110 |
| `.sortedBy { }` | `.sorted(comparing())` | `List` | `B` 503 |
| `.distinct()` | `.distinct()` | `List` | `B` 768 |

`listOf(...)` tạo list bất biến, `mutableListOf(...)` tạo list sửa được, `mutableSetOf<String>()`
tạo set rỗng có ghi kiểu (`B` dòng 376).

### 7.5 `to` — tạo cặp

`B` dòng 112:

```kotlin
.associate { it[0] to it[1] }
```

`a to b` tạo `Pair(a, b)`. `associate` nhận list các Pair và dựng `Map`. `to` không phải từ khoá,
nó là một hàm infix bình thường của thư viện chuẩn.

### 7.6 `.let`, `.also`, `.takeIf`

| Hàm | Nhận | Trả về | Ví dụ thật |
|---|---|---|---|
| `x?.let { }` | `x` qua `it` | kết quả của khối | `B` 80 |
| `x.also { }` | `x` qua `it` | chính `x` | `B` 415 |
| `x.takeIf { }` | `x` qua `it` | `x` nếu điều kiện đúng, ngược lại `null` | `B` 111 |

`B` dòng 80–82, `let` chạy chỉ khi khác null:

```kotlin
parseDeclaredTransition(declared)?.let {
    return a.verb == it.verb && a.path.toString().equals(it.path, ignoreCase = true)
}
```

Đọc là: nếu có khai báo transition thì so khớp theo khai báo rồi thoát hàm luôn; không có thì
chạy tiếp xuống dòng 83.

`B` dòng 415, `also` dùng để chen một tác dụng phụ vào giữa chuỗi:

```kotlin
r.status.also { r.close() }
```

Giá trị của biểu thức là `r.status`. `r.close()` chạy sau khi đã lấy status.

---

## 8. `when`, `try`, dải số, huỷ cấu trúc

### 8.1 `when` — `switch` mạnh hơn, và là biểu thức

`B` dòng 405–414, trong hàm `resetSutState()` bắt đầu ở dòng 389:

```kotlin
val r = when (verb.uppercase()) {
    "GET" -> b.get()
    "POST" -> b.post(empty)
    "PUT" -> b.put(empty)
    "DELETE" -> b.delete()
    else -> {
        LoggingUtil.uniqueUserWarn("Ignoring statefulAuthzResetEndpoint: unsupported verb '$verb'")
        return
    }
}
```

Khác `switch` của Java: không có `break`, không rơi xuống nhánh dưới, kết quả gán thẳng vào `val r`,
và nhánh `else` được phép `return` ra khỏi cả hàm.

### 8.2 `try` cũng là biểu thức

`B` dòng 104–109:

```kotlin
val verb = try {
    HttpVerb.valueOf(parts[0].uppercase())
} catch (e: IllegalArgumentException) {
    LoggingUtil.uniqueUserWarn("Ignoring statefulAuthzTransition: unsupported verb '${parts[0]}'")
    return null
}
```

Kotlin không có checked exception, nên không có `throws` trên chữ ký hàm.

### 8.3 Huỷ cấu trúc

`B` dòng 400:

```kotlin
val (verb, url) = parts
```

`parts` là `List<String>` hai phần tử. Một dòng tạo hai biến. Java phải viết
`var verb = parts.get(0); var url = parts.get(1);`.

### 8.4 Dải số và `in`

| Cú pháp | Nghĩa |
|---|---|
| `200..299` | 200 tới 299, **bao gồm** 299 |
| `(a) until (b)` | a tới b, **không** gồm b, giống `for(i=a;i<b;i++)` |
| `list.indices` | `0 until list.size` |
| `x in y` | `y.contains(x)` |
| `x !in y` | `!y.contains(x)` |

`B` dòng 423: `if (status in 200..299)`.

`O` dòng 572 và 581:

```kotlin
for (srcIndex in actions.indices) {
    ...
    for (followUpIndex in (srcIndex + 1) until actions.size) {
```

`O` dòng 576: `source.verb !in listOf(HttpVerb.PUT, HttpVerb.PATCH, HttpVerb.POST, HttpVerb.DELETE)`.

---

## 9. Class

### 9.1 Constructor chính viết ngay sau tên class

`B` dòng 90–94:

```kotlin
data class DeclaredTransition(
    val verb: HttpVerb,
    val path: String,
    val bindings: Map<String, String>
)
```

Ba dòng tham số vừa là tham số constructor vừa là field, vì có `val` đứng trước. Không có thân
class thì bỏ luôn `{ }`.

`data` cho miễn phí `equals`, `hashCode`, `toString`, `copy`, và huỷ cấu trúc. Gần giống `record`
của Java 16, khác ở chỗ `data class` cho phép `var` và cho phép kế thừa từ class khác.

### 9.2 `enum class` với tham số

`ExperimentalFaultCategory.kt` dòng 5–10:

```kotlin
enum class ExperimentalFaultCategory(
    private val code: Int,
    private val descriptiveName: String,
    private val testCaseLabel: String,
    private val fullDescription: String,
) : FaultCategory {
```

Rồi hằng số của luận văn, dòng 54–57:

```kotlin
SECURITY_STATEFUL_AUTHORIZATION(970,
    "Stateful Authorization: privilege persists after a permission-reducing transition",
    "stillAllowedAfterPermissionRevoked",
    "An action requiring a privilege, once observed ALLOWED, ..."),
```

Giống hệt enum có constructor của Java. Hai chi tiết Kotlin: dấu phẩy thừa sau tham số cuối
(dòng 9) là hợp lệ; danh sách hằng kết thúc bằng `;` riêng một dòng (dòng 85) trước phần method.

### 9.3 `is` và ép kiểu thông minh

`O` dòng 574:

```kotlin
if (source.auth is NoAuth
```

`is` là `instanceof`. Sau khi `is` đúng thì trong nhánh đó biến tự có kiểu hẹp, không cần ép.
`O` dòng 164 dùng dạng phủ định `it.auth !is NoAuth`.

### 9.4 Property thay cho getter/setter

Kotlin gọi `a.path`, `r.status`, `victimAuth.name` chứ không `getPath()`, `getStatus()`.
Kotlin cũng tự nhận ra getter Java: `ar.getStatusCode()` viết được thành `ar.statusCode`. Code
EvoMaster giữ dạng `getStatusCode()` cho nhất quán với phần Java của nó.

Gán cũng vậy, `B` dòng 626: `followUp.auth = victimAuth` gọi setter.

### 9.5 `open` — Kotlin khoá kế thừa lại, ngược với Java

**Trong Kotlin, mọi class là `final` mặc định.** Muốn cho kế thừa phải xin phép bằng `open`.
Java thì ngược lại: mọi class kế thừa được, muốn cấm mới gõ `final`.

```kotlin
class A                 // KHÔNG kế thừa được. Tương đương "final class A" của Java
open class B            // kế thừa được
```

Method cũng vậy:

```kotlin
class C {
    fun x() {}          // KHÔNG ghi đè được, dù C có open đi nữa
    open fun y() {}     // ghi đè được
}
```

Hai tầng khoá này độc lập. Class `open` mà method không `open` thì kế thừa được nhưng không ghi đè
được method đó.

### 9.6 Ví dụ thật: `ActionResult`

`ActionResult.kt` dòng 5, 42 và 63:

```kotlin
open class ActionResult(          // dòng 5,  cho kế thừa
        val sourceLocalId: String,
        ...
) {
    open fun copy() : ActionResult { ... }              // dòng 42, cho ghi đè
    fun addResultValue(name: String, value: String){ }  // dòng 46, KHÔNG cho ghi đè
    fun getResultValue(name: String) : String? { }      // dòng 50, KHÔNG cho ghi đè
    open fun matchedType(action: Action) = true         // dòng 63, cho ghi đè
}
```

Đọc ra ý đồ của tác giả: **cách lưu trữ thì cấm sửa, cách sao chép và cách nhận diện kiểu thì cho
sửa.** `addResultValue` và `getResultValue` là cổng duy nhất vào map `results`, nên khoá lại để
lớp con không phá bất biến đó.

`RestCallResult` ghi đè đúng hai hàm được phép, dòng 25 và 56:

```kotlin
override fun copy(): RestCallResult { return RestCallResult(this) }
override fun matchedType(action: Action): Boolean { ... }
```

Chuỗi kế thừa đầy đủ, xem `part0-base-evomaster.md` mục 3.4:

| Class | Từ khoá | Kế thừa được? | Tự tạo object được? |
|---|---|---|---|
| `ActionResult` | `open class` | được | được |
| `EnterpriseActionResult` | `abstract class` | được | **không** |
| `HttpWsCallResult` | `abstract class` | được | **không** |
| `RestCallResult` | `class` | **không** | được |

### 9.7 `abstract` không cần thêm `open`

`abstract` đã hàm ý cho kế thừa, nên viết `open abstract class` là thừa:

```kotlin
abstract class EnterpriseActionResult : ActionResult{     // dòng 6, không có open
```

Method `abstract` cũng tự động ghi đè được.

### 9.8 `override` là từ khoá bắt buộc, không phải annotation

Java: `@Override` là annotation, quên vẫn biên dịch được.
Kotlin: `override` là **từ khoá**, quên là lỗi biên dịch.

```kotlin
override fun copy(): RestCallResult { ... }
```

Đổi lại có một bẫy ngược: **hàm đã `override` thì tự động `open` cho tầng dưới nữa.** Muốn chặn
phải gõ `final override`. Trong `core` có 3 chỗ làm vậy, ví dụ `Param.kt` dòng 50:

```kotlin
final override fun copy(): Param {
```

Đọc là: tao ghi đè `copy()` của cha, và cấm mọi lớp con của tao ghi đè tiếp.

### 9.9 Vì sao Kotlin chọn mặc định `final`

Vấn đề gọi là *fragile base class*. Class cha viết ra không lường trước ai kế thừa; sửa một
method là gãy lớp con ở nơi khác. Bắt phải gõ `open` buộc tác giả trả lời câu "class này có thiết
kế để kế thừa không" ngay lúc viết.

Số đo trong `core` của EvoMaster:

```
class thường (final) : 424
abstract class       :  69
open class           :  33
```

33 trên 526, tức khoảng 6% class là mở. Con số đó nói đúng bản chất: **kế thừa là ngoại lệ, không
phải mặc định.**

### 9.10 Bảng tra

| Java | Kotlin |
|---|---|
| `class A` | `open class A` |
| `final class A` | `class A` |
| `abstract class A` | `abstract class A` |
| `void f()` | `open fun f()` |
| `final void f()` | `fun f()` |
| `abstract void f()` | `abstract fun f()` |
| `@Override void f()` | `override fun f()` |
| `@Override final void f()` | `final override fun f()` |

Cột trái sang phải: chỗ nào Java **không** gõ gì thì Kotlin phải gõ `open`, và ngược lại.

---

## 10. Chạy tay 1 — `parseDeclaredTransition`

Đầu vào thật, lấy từ `infra/em-results/tier2b-declared-trials/tier2b_declared_trials.sh` dòng 37:

```
spec = "POST /api/set_user_permission user=<victim> role=1 permission=0"
```

Code `B` dòng 96–114. Giá trị sau mỗi dòng:

| Dòng | Code | Giá trị thật sau khi chạy dòng đó |
|---|---|---|
| 96 | `fun parseDeclaredTransition(spec: String): DeclaredTransition? {` | `spec` = chuỗi 63 ký tự ở trên |
| 97 | `if (spec.isBlank()) return null` | `isBlank()` = `false`, đi tiếp. Batch inference truyền `""` thì dừng ngay ở đây |
| 98 | `val parts = spec.trim().split(Regex("\\s+"))` | `List<String>`, 5 phần tử: `["POST", "/api/set_user_permission", "user=<victim>", "role=1", "permission=0"]` |
| 99 | `if (parts.size < 2) {` | `5 < 2` = `false`, nhảy qua khối cảnh báo |
| 104 | `val verb = try {` | mở khối, kết quả khối sẽ gán vào `verb` |
| 105 | `HttpVerb.valueOf(parts[0].uppercase())` | `parts[0]` = `"POST"`, `uppercase()` = `"POST"`, `valueOf` = hằng enum `HttpVerb.POST`. Không ném, nhánh `catch` không chạy |
| 110 | `val bindings = parts.drop(2)` | bỏ 2 phần tử đầu, còn `["user=<victim>", "role=1", "permission=0"]` |
| 111 | `.mapNotNull { p -> p.split("=", limit = 2).takeIf { it.size == 2 } }` | 3 lần lặp. `p="user=<victim>"` cho `["user","<victim>"]` size 2, `takeIf` giữ. Tương tự `["role","1"]` và `["permission","0"]`. Kết quả `List<List<String>>` 3 phần tử, 0 phần tử bị loại |
| 112 | `.associate { it[0] to it[1] }` | `Map<String,String>` 3 cặp: `{"user"="<victim>", "role"="1", "permission"="0"}` |
| 113 | `return DeclaredTransition(verb, parts[1], bindings)` | object với `verb=POST`, `path="/api/set_user_permission"`, `bindings` = map 3 cặp ở trên |

Cú pháp Kotlin xuất hiện trong 8 dòng này: kiểu trả về nullable `DeclaredTransition?` (dòng 96),
`return` sớm một dòng không ngoặc (97), suy kiểu cho `val` (98), template chuỗi trong cảnh báo
(100), `try` là biểu thức (104), lambda đặt tên tham số vì có lambda lồng (111), tham số gọi theo
tên `limit = 2` (111), `takeIf` (111), `to` tạo Pair (112), gọi constructor không có `new` (113).

---

## 11. Chạy tay 2 — `looksLikePermissionReducingTransition` trên hai action thật

Code `B` dòng 79–88. Chạy với `declared = ""` (batch inference của Tier-2b, không truyền cờ).

Action 1: `POST /json/status`, chính là `source` trong log dòng 3411.

| Dòng | Code | Giá trị thật |
|---|---|---|
| 80 | `parseDeclaredTransition(declared)?.let {` | `declared` = `""`, hàm trả `null` ở dòng 97, `?.` chặn, khối `let` **không chạy** |
| 83 | `if (a.verb !in TRANSITION_VERBS) {` | `a.verb` = `POST`. `TRANSITION_VERBS` chứa `POST` nên `!in` = `false`, đi tiếp |
| 86 | `val hay = (a.path.toString() + " " + a.getName()).lowercase()` | `"/json/status"` + `" "` + `"POST:/json/status"`, hạ chữ thường, ra `"/json/status post:/json/status"` |
| 87 | `return TRANSITION_PATH_SIGNALS.any { hay.contains(it) }` | duyệt 8 signal, không cái nào nằm trong `hay`. Trả `false` |

Action 2: `POST /api/set_user_permission`, chính là `transition` trong log dòng 3414.

| Dòng | Code | Giá trị thật |
|---|---|---|
| 80 | `parseDeclaredTransition(declared)?.let {` | như trên, không chạy |
| 83 | `if (a.verb !in TRANSITION_VERBS) {` | `POST` có trong danh sách, đi tiếp |
| 86 | `val hay = ...` | `"/api/set_user_permission post:/api/set_user_permission"` |
| 87 | `TRANSITION_PATH_SIGNALS.any { hay.contains(it) }` | signal index 0 `"role"` không khớp; index 1 `"permission"` khớp. `any` dừng ngay tại đây, trả `true` |

Hai kết quả này là lý do log dòng 3414 ghi `POST:/json/status` ở vị trí source và
`POST:/api/set_user_permission` ở vị trí transition.

---

## 12. Chạy tay 3 — `joinToString` dựng chuỗi `"200/401/200"`

Code `B` dòng 653–654, trong lần thử đầu của run `vuln-noreset-seed1`:

```kotlin
val observed = listOf(sourceCode, transitionCode, followUpCode)
    .joinToString("/") { it?.toString() ?: "-" }
```

| Dòng | Code | Giá trị thật |
|---|---|---|
| 648 | `val sourceCode = statusOf(source)` | `200` (kiểu `Int?`) |
| 649 | `val transitionCode = statusOf(transition)` | `401` |
| 650 | `val followUpCode = statusOf(followUp)` | `200` |
| 653 | `listOf(sourceCode, transitionCode, followUpCode)` | `List<Int?>` 3 phần tử `[200, 401, 200]` |
| 654 | `.joinToString("/") { it?.toString() ?: "-" }` | lặp 3 lần: `it=200` khác null nên `"200"`; `it=401` nên `"401"`; `it=200` nên `"200"`. Nối bằng `/`, ra `"200/401/200"` |

Chuỗi đó chạy tiếp vào template dòng 668 `codes $observed` và in ra log thật dòng 3411:

```
... (victim 'pyload', operator 'alice', codes 200/401/200)
```

Nhánh `?: "-"` chưa xuất hiện trong log của run này vì cả 3 status đều có. Nó chỉ chạy khi action
không có kết quả, ví dụ test bị dừng giữa chừng.

---

## 13. Bảng tra nhanh Java sang Kotlin

| Java | Kotlin |
|---|---|
| `static final X x = ...` | `val x = ...` trong `companion object` |
| `static final int N = 8` | `const val N = 8` trong `companion object` |
| `final var x = 5` | `val x = 5` |
| `var x = 5` | `var x = 5` |
| `String s` có thể null | `String?` |
| `s == null ? d : s` | `s ?: d` |
| `s == null ? null : s.f()` | `s?.f()` |
| `x instanceof T` | `x is T` |
| `(T) x` ném nếu sai | `x as T` |
| `x instanceof T ? (T)x : null` | `x as? T` |
| `X.class` | `X::class.java` |
| `new X(a)` | `X(a)` |
| `implements I` / `extends C` | `: I` / `: C` |
| `void f()` | `fun f()` |
| `int f(String s)` | `fun f(s: String): Int` |
| `"a" + b + "c"` | `"a${b}c"` |
| `List.of(1,2)` | `listOf(1,2)` |
| `new ArrayList<>()` | `mutableListOf<T>()` |
| `list.stream().filter(p).toList()` | `list.filter { p(it) }` |
| `switch` | `when` |
| `for(int i=0;i<n;i++)` | `for (i in 0 until n)` |
| `throws IOException` | không có, Kotlin bỏ checked exception |
| `;` cuối dòng | bỏ được |
