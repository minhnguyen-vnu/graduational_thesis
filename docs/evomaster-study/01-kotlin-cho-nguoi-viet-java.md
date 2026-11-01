# Kotlin cho người viết Java: đủ để đọc mã EvoMaster

Mục tiêu: đọc được mã ta thêm vào EvoMaster và mã upstream quanh nó. Mọi ví dụ "mã ta" lấy từ commit `f73010103b`
(jar P2f), nơi ta đã thêm 1.825 dòng vào 6 file, 1.349 dòng nằm ở `RestSecurityBuilder.kt`. Số dòng là số dòng ở commit
đó. HEAD `1cd0d091f4` đã gỡ reset, transition khai báo và D1, nên ví dụ về ba phần này chỉ đúng tới P2f.

| Viết tắt | File |
|---|---|
| `B` | `/Users/minhnguyen/IdeaProjects/EvoMaster/core/src/main/kotlin/org/evomaster/core/problem/rest/service/RestSecurityBuilder.kt` |
| `O` | `/Users/minhnguyen/IdeaProjects/EvoMaster/core/src/main/kotlin/org/evomaster/core/problem/rest/oracle/RestSecurityOracle.kt` |
| `EMConfig` | `/Users/minhnguyen/IdeaProjects/EvoMaster/core/src/main/kotlin/org/evomaster/core/EMConfig.kt` |
| CSV mô hình | `/Users/minhnguyen/IdeaProjects/EvoMaster/core/src/main/resources/stateful-authz-model.csv` |

Ba loại giá trị trong ví dụ:

- **(chạy thật)**: gọi hàm thật trong `evomaster-P2f-64ee8ffc.jar` bằng `jshell` hoặc xem bytecode bằng `javap`, ngày
  2026-10-21.
- **(log)**: dòng log thật trong `infra/em-results/p2f-full-20261015/logs/t1-vuln-seed1-r0.log`, jar P2f.
- **(chạy tay)**: tự lần theo mã. Giá trị đầu vào giả định thì ghi "giả sử".

Quy tắc ngôn ngữ theo tài liệu chính thức kotlinlang.org/docs. Mình viết từ hiểu biết, chưa trích từng câu từ đó.

## Mục lục

1. [Kotlin và Java](#1-kotlin-và-java)
2. [File, package, import](#2-file-package-import)
3. [val, var, const val](#3-val-var-const-val)
4. [Kiểu cơ bản](#4-kiểu-cơ-bản)
5. [Chuỗi](#5-chuỗi)
6. [Hàm](#6-hàm)
7. [Null safety](#7-null-safety)
8. [Kiểm kiểu và ép kiểu](#8-kiểm-kiểu-và-ép-kiểu)
9. [if và when là biểu thức](#9-if-và-when-là-biểu-thức)
10. [Range, vòng lặp, nhãn](#10-range-vòng-lặp-nhãn)
11. [Ngoại lệ và try](#11-ngoại-lệ-và-try)
12. [Class, constructor, property](#12-class-constructor-property)
13. [data class, Pair, destructuring](#13-data-class-pair-destructuring)
14. [companion object và object](#14-companion-object-và-object)
15. [enum class](#15-enum-class)
16. [Collection](#16-collection)
17. [Lambda](#17-lambda)
18. [Hàm trên collection](#18-hàm-trên-collection)
19. [Scope function: let, also, run, apply, takeIf](#19-scope-function-let-also-run-apply-takeif)
20. [Generic](#20-generic)
21. [Annotation](#21-annotation)
22. [Toán tử](#22-toán-tử)
23. [Kotlin gọi Java, Java gọi Kotlin](#23-kotlin-gọi-java-java-gọi-kotlin)
24. [Đọc trọn một hàm: `handleStatefulAuthorization`](#24-đọc-trọn-một-hàm-handlestatefulauthorization)
25. [Bẫy cho người viết Java](#25-bẫy-cho-người-viết-java)

---

## 1. Kotlin và Java

### 1.1 Cùng chạy trên JVM

Trình biên dịch Kotlin dịch file `.kt` ra file `.class`, cùng định dạng bytecode mà `javac` tạo ra. Vì vậy:

- jar EvoMaster chạy bằng `java -jar evomaster-P2f-64ee8ffc.jar`, với Java 17;
- mã Kotlin dùng thẳng thư viện Java: mã ta import Jackson (`com.fasterxml.jackson.databind.ObjectMapper`), Guice
  (`com.google.inject.Inject`), Jersey (`javax.ws.rs.client.Client`);
- mã Java gọi thẳng mã Kotlin.

Ví dụ: một dòng Kotlin ở `B:251–255`

```kotlin
data class DeclaredTransition(
    val verb: HttpVerb,
    val path: String,
    val bindings: Map<String, String>
)
```

`javap` mở class đã biên dịch trong jar P2f **(chạy thật)**:

```
public final class org.evomaster.core.problem.rest.service.RestSecurityBuilder$Companion$DeclaredTransition {
  public ...DeclaredTransition(HttpVerb, java.lang.String, java.util.Map<java.lang.String, java.lang.String>);
  public final HttpVerb getVerb();
  public final java.lang.String getPath();
  public final java.util.Map<java.lang.String, java.lang.String> getBindings();
  public final HttpVerb component1();
  public final java.lang.String component2();
  public final java.util.Map<java.lang.String, java.lang.String> component3();
  public final ...DeclaredTransition copy(HttpVerb, java.lang.String, java.util.Map<...>);
  public java.lang.String toString();
  public int hashCode();
  public boolean equals(java.lang.Object);
}
```

Năm dòng Kotlin sinh ra một class Java đầy đủ: constructor, 3 getter, `equals`, `hashCode`, `toString`, `copy`, và
`component1–3` cho destructuring (§13). `Map` của Kotlin thành `java.util.Map`.

Chiều ngược lại: từ `jshell` (Java) gọi hàm Kotlin trong jar **(chạy thật)**:

```java
RestSecurityBuilder.Companion.tokens("/users/{username}/role", 4)   // [users, username, role]
```

### 1.2 Trong EvoMaster

| Sự kiện | Nguồn |
|---|---|
| Java 17, Kotlin 2.2.20 | `/Users/minhnguyen/IdeaProjects/EvoMaster/pom.xml:217–218` |
| module `core`: 688 file `.kt` mã chính, 366 file `.kt` test, 0 file `.java` trong `src` | `find core/src/main -name '*.kt'`, ngày 2026-10-21 |
| module `client-java`: 531 file `.java` mã chính, 362 file `.java` test, 0 file `.kt` | `find client-java -path '*src/main*' -name '*.java'` |

`core` là bộ sinh test: sampler, thuật toán tìm kiếm, oracle, phần viết test ra file. Mọi thay đổi của ta nằm ở `core`.
`client-java` là driver và phần đo mã chạy trong JVM của ứng dụng bị test, dùng cho chế độ white-box. Luận văn chạy
black-box, nên không đụng `client-java`.

### 1.3 Bảng đối chiếu

| Chủ đề | Java | Kotlin | Mục |
|---|---|---|---|
| Biến không đổi | `final String s = "a";` | `val s = "a"` | §3 |
| Biến đổi được | `int n = 0;` | `var n = 0` | §3 |
| Dấu `;` | bắt buộc | bỏ | §2 |
| Null | mọi tham chiếu có thể null | `String` không null; `String?` có thể null | §7 |
| `int` / `Integer` | hai kiểu | một kiểu `Int`; `Int?` thành `Integer` | §4 |
| Tạo đối tượng | `new Foo()` | `Foo()` | §12 |
| Getter/setter | viết tay | property | §12 |
| `static` | `static` | `companion object` | §14 |
| Class mặc định | kế thừa được | `final`; muốn kế thừa phải `open` | §12 |
| `extends` / `implements` | hai từ khoá | dấu `:` | §12 |
| `@Override` | annotation, tuỳ chọn | từ khoá `override`, bắt buộc | §12 |
| `switch` | câu lệnh | `when`, là biểu thức | §9 |
| `a ? b : c` | toán tử ba ngôi | `if (a) b else c` | §9 |
| `instanceof` + cast | hai bước | `is` rồi tự ép kiểu | §8 |
| `==` | so tham chiếu | gọi `equals`; so tham chiếu là `===` | §22 |
| Checked exception | bắt buộc `throws`/`catch` | không có | §11 |
| Stream API | `list.stream().map(...).collect(...)` | `list.map { ... }` | §18 |
| Lambda | `x -> x + 1` | `{ x -> x + 1 }` hoặc `{ it + 1 }` | §17 |
| `void` | `void` | `Unit`, thường bỏ trống | §6 |
| `Foo.class` | `Foo.class` | `Foo::class.java` | §23 |
| Chuỗi ghép | `"a" + x + "b"` | `"a${x}b"` | §5 |

---

## 2. File, package, import

```kotlin
package org.evomaster.core.problem.rest.service

import com.fasterxml.jackson.databind.JsonNode
import com.fasterxml.jackson.databind.ObjectMapper
import com.google.inject.Inject
import org.evomaster.core.search.*
```

`B:1–5` và `B:39`. Giống Java, bỏ dấu `;`. `*` nhập mọi tên trong package.

Khác Java:

- Một file `.kt` chứa được nhiều class. `B` chứa `RestSecurityBuilder`, và lồng trong nó `SchemaField`,
  `DeclaredTransition`, `ScoredObject`. Sau biên dịch: `RestSecurityBuilder$Companion$SchemaField.class`,...
- Tên file được khác tên class.
- Gọi bằng tên đầy đủ, không import, ở ba chỗ trong mã ta:

```kotlin
private val opEvidenceCache = java.util.concurrent.ConcurrentHashMap<String, Double>()   // B:218
org.evomaster.core.Lazy.assert { base.verifyValidity(); true }                            // B:963
val v = try { java.net.URLDecoder.decode(kv[1], "UTF-8") } catch (e: Exception) { kv[1] } // B:1402
```

---

## 3. val, var, const val

| Kotlin | Java | Nghĩa |
|---|---|---|
| `val x = 1` | `final int x = 1;` | gán một lần |
| `var x = 1` | `int x = 1;` | gán lại được |
| `const val X = "a"` (trong `companion`/`object`) | `static final String X = "a";` | hằng lúc biên dịch, chỉ cho số và `String` |

Kiểu được suy ra từ vế phải. Ghi kiểu khi muốn: `val x: Int = 1`.

**Mã ta.**

```kotlin
private const val MODEL_RESOURCE = "/stateful-authz-model.csv"   // B:79
private var statefulTripleAttempts = 0                            // B:535, kiểu Int
statefulTripleAttempts++                                          // B:977
```

`javap` cho `statefulTripleAttempts` ra `private int statefulTripleAttempts;` **(chạy thật)**.

**`val` giữ tham chiếu cố định, nội dung vẫn đổi được nếu là collection mutable.**

```kotlin
private val privilegeReducedInPhase = mutableSetOf<String>()   // B:529
privilegeReducedInPhase.add(victimAuth.name)                   // B:1002
privilegeReducedInPhase.clear()                                // B:589
privilegeReducedInPhase = mutableSetOf()                       // lỗi biên dịch: val không gán lại được
```

Java tương đương: `private final Set<String> privilegeReducedInPhase = new LinkedHashSet<>();`

**Khai báo trước, gán sau một lần.**

```kotlin
val queue: List<Pair<RestCallAction, List<String>>>   // B:614
if (declared != null) {
    ...
    queue = listOf(transition to listOf(""))           // B:624
} else {
    ...
    queue = viable                                     // B:657
}
```

Trình biên dịch kiểm rằng mỗi nhánh gán đúng một lần. Java `final` biến cục bộ có luật giống vậy.

---

## 4. Kiểu cơ bản

| Kotlin | Java khi không null | Java khi `?` |
|---|---|---|
| `Int` | `int` | `Integer` |
| `Long` | `long` | `Long` |
| `Double` | `double` | `Double` |
| `Boolean` | `boolean` | `Boolean` |
| `Char` | `char` | `Character` |
| `String` | `String` | `String` |
| `Unit` | `void` | |
| `Any` | `Object` | |

Không có kiểu nguyên thuỷ trong mã nguồn Kotlin; trình biên dịch chọn `int` hay `Integer`. `javap` trên `B` **(chạy
thật)**:

```kotlin
private var statefulTripleAttempts = 0       // private int statefulTripleAttempts;
private var lastSourceCode: Int? = null      // private java.lang.Integer lastSourceCode;
var statefulTripleUnderEvaluation = false    // private boolean statefulTripleUnderEvaluation;
```

Hằng số đặc biệt dùng trong mã ta: `Double.NEGATIVE_INFINITY` (`B:214`), giống `Double.NEGATIVE_INFINITY` của Java.

---

## 5. Chuỗi

### 5.1 String template

`$ten` chèn một biến; `${bieu_thuc}` chèn một biểu thức.

```kotlin
val key: String get() = "$loc:$name"                                       // B:148
val fs = mutableSetOf("k:$kind", "l:$loc", "w:${leaf.lowercase()}")         // B:151
```

Chạy tay, giả sử `loc = "body"`, `name = "role"`, `kind = "enum"`, `leaf = "Role"`:

```
"$loc:$name"                 →  "body:role"
"k:$kind"                    →  "k:enum"
"w:${leaf.lowercase()}"      →  "w:role"
```

Java: `loc + ":" + name`, `"w:" + leaf.toLowerCase()`.

Một log có template trong mã ta, `B:1032–1034`:

```kotlin
"Assembled a stateful-authorization (MR-A1) triple on ${source.getName()}" +
    " (victim '${victimAuth.name}', operator '${operator.name}'," +
    " transition ${transition.getName()}, statuses $observed)"
```

ra **(log)**:

```
Assembled a stateful-authorization (MR-A1) triple on PUT:/reports/{id} (victim 'alice', operator 'superadmin', transition PUT:/users/{username}/role, statuses 200/200/200)
```

Chuỗi dài nối bằng `+` qua nhiều dòng, như Java. Escape như Java: `\"` (`EMConfig:3046`), `\'` (`B:1336`), `\\s` trong
regex (`B:259`).

### 5.2 Hàm chuỗi dùng trong mã ta

| Hàm | Vào | Ra | Chỗ dùng |
|---|---|---|---|
| `lowercase()` / `uppercase()` | `"PUT"` | `"put"` / `"PUT"` | `B:124`, `B:570` |
| `trim()` | `"  a b "` | `"a b"` | `B:259` |
| `isBlank()` | `"   "` | `true` | `B:258` |
| `isNotBlank()` | `"alice"` | `true` | `B:1411` |
| `isEmpty()` / `isNotEmpty()` | `""` | `true` / `false` | `B:123` |
| `startsWith(x)` | `"{id}".startsWith("{")` | `true` | `B:1595` |
| `contains(x)` | `"role_member".contains("member")` | `true` | `B:227` |
| `substringBefore(x)` | `"/reports/{id}".substringBefore("{")` | `"/reports/"` | `B:1427` |
| `substringAfterLast(x)` | `"/users/{username}/role".substringAfterLast("/")` | `"role"` | `B:1595` |
| `substringBeforeLast(x)` | `"/reports/{id}".substringBeforeLast("/")` | `"/reports"` | `B:1598` |
| `trimEnd('/')` | `"/reports/6/"` | `"/reports/6"` | `B:1103` |
| `replace(a, b)` | `"roles[]".replace("[]", "")` | `"roles"` | `B:129` |
| `equals(x, ignoreCase = true)` | `"/Reports".equals("/reports", ignoreCase = true)` | `true` | `B:243` |
| `toDoubleOrNull()` | `"0.5"` / `"weight"` | `0.5` / `null` | `B:105` |
| `split(",")` | `"op,f:role,2.11"` | `["op", "f:role", "2.11"]` | `B:103` |
| `split("=", limit = 2)` | `"a=b=c"` | `["a", "b=c"]` | `B:272` |
| `filter { }` | `"user_Name".lowercase().filter { it.isLetterOrDigit() }` | `"username"` | `B:1357` |

Ví dụ ghép: id tài nguyên lấy từ header `Location`, `B:1103`:

```kotlin
creation.getLocation()?.trimEnd('/')?.substringAfterLast('/')
```

Chạy tay, giả sử `Location: http://localhost:8080/reports/6/`:

```
"http://localhost:8080/reports/6/"
  .trimEnd('/')           → "http://localhost:8080/reports/6"
  .substringAfterLast('/') → "6"
```

### 5.3 Regex

```kotlin
private val TOKEN_PIECE = Regex("[^A-Za-z0-9]+")                          // B:91
private val TOKEN_PART = Regex("[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+")  // B:93
```

`Regex(...)` bọc `java.util.regex.Pattern`; cú pháp mẫu giống Java. Dùng với `split(regex)`, `findAll(text)`.

**Khác Java: `split` của Kotlin giữ chuỗi rỗng ở cuối** **(chạy thật)**:

```
Kotlin  Regex("[^A-Za-z0-9]+").split("/reports/{id}", 0)   →  [, reports, id, ]
Java    "/reports/{id}".split("[^A-Za-z0-9]+")              →  [, reports, id]
```

Cả hai giữ chuỗi rỗng ở đầu. Vì vậy `tokens()` có `.filter { it.isNotEmpty() }` ngay sau `split` (`B:123`). Chạy trọn
`tokens()` ở §18.3.

---

## 6. Hàm

### 6.1 Khai báo

```kotlin
fun ten(thamSo: Kieu, thamSo2: Kieu2): KieuTraVe {
    ...
    return giaTri
}
```

Kiểu đứng **sau** tên, sau dấu `:`. Hàm không trả gì có kiểu `Unit`, bỏ trống được.

```kotlin
private fun noStatusRecorded(transitionDef: RestCallAction, victim: String, operator: String) {   // B:894, trả Unit
    LoggingUtil.getInfoLogger().warn(...)
}
```

Java: `private void noStatusRecorded(RestCallAction transitionDef, String victim, String operator) { ... }`

### 6.2 Thân biểu thức `=`

Hàm chỉ có một biểu thức thì viết `= bieuThuc`, bỏ `{ return ... }`.

```kotlin
private fun normalize(s: String): String = s.lowercase().filter { it.isLetterOrDigit() }       // B:1357
private fun prior(name: String): Double = table(name)[PRIOR] ?: Double.NEGATIVE_INFINITY      // B:214
private fun candidateCapReached(): Boolean =
    !candidateProven && !candidateIsLast && candidateAttempts >= MAX_UNPROVEN_CANDIDATE_ATTEMPTS   // B:594–595
```

Java:

```java
private String normalize(String s) {
    return s.toLowerCase().chars().filter(Character::isLetterOrDigit)
            .collect(StringBuilder::new, StringBuilder::appendCodePoint, StringBuilder::append).toString();
}
```

Chạy tay `normalize("user_Name")`: `"user_name"` sau `lowercase()`, bỏ `_` sau `filter`, ra `"username"`.

Kiểu trả về suy ra được thì bỏ được, như hàm cục bộ ở `B:680`: `fun guardedCandidatesFor(verbs: List<HttpVerb>) = ...`
trả `List<Pair<HttpVerb, RestCallAction>>`.

### 6.3 Tham số mặc định

```kotlin
fun tokens(text: String, minLength: Int = MIN_TOKEN_LENGTH): Set<String> =   // B:121
```

Gọi `tokens(leaf)` thì `minLength = 4`. Gọi `tokens(leaf, 2)` thì `minLength = 2`. Java phải viết hai overload.

Bytecode **(chạy thật)**: Kotlin sinh một hàm đủ tham số và một hàm phụ `tokens$default`:

```
public final java.util.Set<java.lang.String> tokens(java.lang.String, int);
public static java.util.Set tokens$default(...Companion, java.lang.String, int, int, java.lang.Object);
```

Từ Java phải truyền đủ: `tokens(s, 4)`.

### 6.4 Tham số có tên

Truyền theo tên, bỏ qua được các tham số có mặc định ở giữa.

```kotlin
private fun distinctUsersOn(                 // B:1615–1620
    verb: HttpVerb,
    path: RestPath,
    statusGroup: StatusGroup? = null,
    status: Int? = null
): Int = ...

distinctUsersOn(it.first, it.second.path, statusGroup = StatusGroup.G_2xx)   // B:703
distinctUsersOn(it.first, it.second.path, status = 403)                      // B:704
```

Hàm upstream có nhiều mặc định được gọi kiểu này khắp nơi:

```kotlin
RestIndividualSelectorUtils.findIndividuals(
    individualsInSolution, verb, op.path,
    statusGroup = StatusGroup.G_2xx, authenticated = true      // B:695–696
)
```

Java: `findIndividuals(individualsInSolution, verb, op.path, null, StatusGroup.G_2xx, true, null, ...)`, phải nhớ đúng
thứ tự.

### 6.5 Hàm cục bộ

Hàm khai báo trong hàm khác, thấy được biến của hàm ngoài. Java không có; gần nhất là lambda gán vào biến.

```kotlin
private fun handleStatefulAuthorization(individual: RestIndividual, actionResults: List<ActionResult>, fv: FitnessValue) {
    ...
    fun statusOf(a: RestCallAction): Int? =                                                  // O:567
        (actionResults.find { it.sourceLocalId == a.getLocalId() } as RestCallResult?)?.getStatusCode()

    fun isAllowed(a: RestCallAction): Boolean {                                              // O:570
        val code = statusOf(a) ?: return false
        return StatusGroup.G_2xx.isInGroup(code)
    }
```

`statusOf` đọc `actionResults`, tham số của hàm ngoài. Thêm ví dụ: `B:680` (`guardedCandidatesFor` đọc `transitionOp`
của vòng `for` bao nó), `B:980`.

---

## 7. Null safety

Đây là khác biệt lớn nhất với Java. Kiểu `String` không nhận `null`; trình biên dịch báo lỗi. Muốn nhận null phải ghi
`String?`.

```kotlin
var a: String = "x"
a = null              // lỗi biên dịch
var b: String? = "x"
b = null              // được
b.length              // lỗi biên dịch: b có thể null
```

### 7.1 Năm toán tử

| Toán tử | Tên | Nghĩa | Java tương đương |
|---|---|---|---|
| `T?` | kiểu nullable | có thể null | mọi tham chiếu Java |
| `a?.f()` | safe call | `a` null thì ra `null`, không gọi `f` | `a == null ? null : a.f()` |
| `a ?: b` | Elvis | `a` null thì lấy `b` | `a != null ? a : b` |
| `a!!` | khẳng định không null | `a` null thì ném `NullPointerException` | `Objects.requireNonNull(a)` |
| `a as? T` | ép kiểu an toàn | sai kiểu thì ra `null` | `a instanceof T ? (T) a : null` |

### 7.2 `?:` với `return` và `continue`

Vế phải của `?:` có thể là `return` hoặc `continue`. Mẫu này có ở khắp mã ta.

```kotlin
val code = statusOf(a) ?: return false            // O:571
```

| Tình huống | `statusOf(a)` | Kết quả |
|---|---|---|
| action đã chạy, trả 200 | `200` | `code = 200`, chạy tiếp |
| action chưa chạy | `null` | hàm `isAllowed` trả `false` ngay |

Java:

```java
Integer code = statusOf(a);
if (code == null) return false;
```

Thêm ví dụ:

```kotlin
val victimAuth = victimSlice.seeMainExecutableActions().lastOrNull()?.auth ?: return false   // B:771
val result = actionResults.filterIsInstance<RestCallResult>()
    .find { it.sourceLocalId == followUp.getLocalId() }
    ?: continue                                                                              // O:608–611
for (plan in plans[operator.name] ?: emptyList()) { ... }                                    // B:847
return features.sumOf { t[it] ?: 0.0 }                                                       // B:211
```

### 7.3 Chuỗi `?.` nối `?:`

`B:1103–1106`:

```kotlin
val resourceId = creation.getLocation()?.trimEnd('/')?.substringAfterLast('/')
    ?: creation.getResourceId()?.value
    ?: return inconclusiveProbe(
        "the creating action ${creator.getName()} returned neither a location header nor an id in its body")
```

Chạy tay, ba tình huống giả sử:

| `getLocation()` | `getResourceId()?.value` | `resourceId` |
|---|---|---|
| `"/reports/6"` | không xét | `"6"` |
| `null` | `"6"` | `"6"` |
| `null` | `null` | hàm trả `false` và ghi log INCONCLUSIVE |

Java:

```java
String loc = creation.getLocation();
String resourceId = loc == null ? null : substringAfterLast(trimEnd(loc, '/'), '/');
if (resourceId == null) {
    ResourceId rid = creation.getResourceId();
    resourceId = rid == null ? null : rid.getValue();
}
if (resourceId == null) return inconclusiveProbe("...");
```

### 7.4 Smart cast sau khi kiểm null

Sau `x != null`, trình biên dịch coi `x` là kiểu không null trong phần còn lại của biểu thức hoặc khối.

```kotlin
if (transitionCode == 404 && sourceCode != null && StatusGroup.G_2xx.isInGroup(sourceCode)) {   // B:987
```

`sourceCode` có kiểu `Int?`. `isInGroup` nhận `Int`. Sau `sourceCode != null`, truyền `sourceCode` vào được, không cần ép.

### 7.5 `!!`

```kotlin
val valid = sourceCode != null && StatusGroup.G_2xx.isInGroup(sourceCode)
    && transitionCode != null && StatusGroup.G_2xx.isInGroup(transitionCode)
    && followUpCode != null && followUpCode != 401          // B:1005–1007
if (!valid) { ...; return false }                           // B:1009–1019
if (StatusGroup.G_2xx.isInGroup(followUpCode!!)             // B:1021
```

Tới `B:1021`, `valid == true` nên `followUpCode` chắc chắn khác null. Trình biên dịch không suy ra được điều đó qua biến
`valid`, nên mã ghi `!!`. Nếu sai, `!!` ném `NullPointerException`. Upstream dùng `!!` ở 518 dòng của `core`.

### 7.6 So `Boolean?` với `true`

```kotlin
listOf("op", "role", "victim").filter { model[it]?.containsKey(PRIOR) != true }   // B:108
```

`model[it]` có kiểu `Map<String, Double>?`, nên `model[it]?.containsKey(PRIOR)` có kiểu `Boolean?`: `true`, `false` hoặc
`null`. `!= true` đúng khi kết quả là `false` hoặc `null`, tức bảng thiếu hoặc bảng không có dòng `__prior__`.

### 7.7 `?.let`, `isNullOrEmpty`, `listOfNotNull`

```kotlin
parseDeclaredTransition(declared)?.let {                                       // B:242
    return a.verb == it.verb && a.path.toString().equals(it.path, ignoreCase = true)
}
```

Có transition khai báo thì so với nó và trả kết quả; `null` thì bỏ qua khối, chạy tiếp dòng 245.

```kotlin
listOf("low", "high", "lowstr", "highstr").filter { model[it].isNullOrEmpty() }  // B:109
listOfNotNull(id, victimName)                                                   // B:1548
```

`isNullOrEmpty()` đúng khi null hoặc rỗng. `listOfNotNull(null, "alice")` ra `["alice"]`.

---

## 8. Kiểm kiểu và ép kiểu

| Kotlin | Java |
|---|---|
| `x is T` | `x instanceof T` |
| `x !is T` | `!(x instanceof T)` |
| `x as T` | `(T) x`, sai kiểu ném `ClassCastException` |
| `x as? T` | `x instanceof T ? (T) x : null` |
| `x as T?` | `(T) x`; `x` null thì ra null, sai kiểu thì ném |
| `list.filterIsInstance<T>()` | `list.stream().filter(T.class::isInstance).map(T.class::cast).toList()` |

### 8.1 `is` và smart cast

```kotlin
if (victimAuth is NoAuth) return false                                              // B:772

if (f.loc == "body" && gene is OptionalGene && gene.isActive && "." !in f.name) {   // B:1565
    gene.isActive = false                                                           // B:1566
```

Sau `gene is OptionalGene`, `gene` được coi là `OptionalGene`; `gene.isActive` dùng được mà không ép. Java 17:

```java
if (f.getLoc().equals("body") && gene instanceof OptionalGene og && og.isActive() && !f.getName().contains(".")) {
    og.setActive(false);
```

### 8.2 `as`, `as?`, `as T?`

```kotlin
val base = victimSlice.copy() as RestIndividual                                   // B:919
(ei.seeResult(a.getLocalId()) as? RestCallResult)?.getStatusCode()                // B:981
(actionResults.find { ... } as RestCallResult?)?.getStatusCode()                  // O:568
```

- `copy()` khai báo trả kiểu cha; ta biết nó là `RestIndividual` nên ép thẳng.
- `as?`: kết quả không phải `RestCallResult` thì ra `null`, rồi `?.` bỏ qua lời gọi.
- `as RestCallResult?`: `find` không thấy thì `null` đi qua; thấy mà sai kiểu thì ném.

### 8.3 `filterIsInstance`

```kotlin
a.parameters.filterIsInstance<PathParam>().forEach { ... }    // B:192
```

`a.parameters` là `List<Param>` gồm `PathParam`, `QueryParam`, `BodyParam`, `HeaderParam`... `filterIsInstance<PathParam>()`
giữ các `PathParam` và trả `List<PathParam>`.

---

## 9. if và when là biểu thức

### 9.1 `if` trả giá trị

Kotlin không có `a ? b : c`. `if ... else` trả giá trị.

```kotlin
maxStatefulAttempts = if (declared != null) {         // B:660–664
    MAX_STATEFUL_TRIPLE_ATTEMPTS_DECLARED
} else {
    MAX_STATEFUL_TRIPLE_ATTEMPTS
}
return if (ok) listOf(f.key) else null                 // B:1557
```

Chạy tay: `declared = null` ra `20`; có khai báo ra `40` (`B:233`, `B:237`).

Khi dùng `if` làm biểu thức thì bắt buộc có `else`.

### 9.2 `when` có chủ thể

`when (x)` giống `switch (x)`, nhưng là biểu thức, không cần `break`, và `else` thay `default`.

```kotlin
val r = when (verb.uppercase()) {                       // B:570–579
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

Chạy tay với `--statefulAuthzResetEndpoint "POST http://localhost:8080/reset"`: `verb = "POST"`, nhánh 2, `r` là phản hồi
của `POST /reset`. Với `"PATCH ..."`: nhánh `else`, ghi cảnh báo và thoát hàm `resetSutState`.

`when` khớp được cả `null`:

```kotlin
when (anonymousCode) {                                  // B:1149–1153
    null -> inconclusiveProbe("the follow-up sent without credentials was not executed")
    403 -> inconclusiveProbe("the follow-up sent without credentials was also denied with 403")
    else -> true
}
```

| `anonymousCode` | Kết quả |
|---|---|
| `null` | `false`, log INCONCLUSIVE |
| `403` | `false`, log INCONCLUSIVE |
| `401` | `true` |

**(log)**: `Stateful-authorization anonymous control: PUT:/reports/{id}=401`, rơi vào nhánh `else`.

### 9.3 `when` không chủ thể

Mỗi nhánh là một điều kiện; nhánh đúng đầu tiên thắng. Thay chuỗi `if / else if`.

```kotlin
kind = when {                                           // B:138–145
    value is BooleanGene -> "bool"
    enum != null && enumValues.isNotEmpty() -> "enum"
    value is NumberGene<*> -> "num"
    value is ArrayGene<*> || value is TaintedArrayGene -> "array"
    value is ObjectGene || value is MapGene<*, *> || value is CycleObjectGene || value is LimitObjectGene -> "object"
    else -> "str"
}
```

Chạy tay trên Tier-1 `PUT /users/{username}/role`:

| Trường | `value` | Nhánh khớp | `kind` |
|---|---|---|---|
| path `username` | `StringGene` | `else` | `"str"` |
| body `role` (`allowableValues = {"ADMIN","VIEWER"}`) | `EnumGene` | 2 | `"enum"` |

### 9.4 `when` với `is`

```kotlin
private fun alternatives(g: Gene): List<Gene> = when (g) {          // B:168–172
    is ChoiceGene<*> -> g.getViewOfChildren().flatMap { alternatives(it) }
    is WrapperGene -> alternatives(g.getViewOfChildren().first())
    else -> listOf(g)
}
```

Trong nhánh `is ChoiceGene<*>`, `g` đã là `ChoiceGene`. Cùng mẫu ở `B:1369–1372` (`activateAncestors`).

### 9.5 `when` trả list

`B:1231–1247`, `reducedRoleValues`:

```kotlin
val raw = when (field.kind) {
    "enum" -> { ...; low + rest }
    "bool" -> when (current.firstOrNull()?.lowercase()) {
        "true" -> listOf("false")
        "false" -> listOf("true")
        else -> listOf("false")
    }
    "array" -> listOf(emptyRoleList)
    "num" -> numericRoleCandidates
    "str" -> tableValues("lowstr")
    else -> emptyList()
}
```

Nhánh dạng khối `{ ...; low + rest }` trả giá trị của dòng cuối. `when` lồng `when`. Chạy trọn nhánh `"enum"` ở §18.5.

---

## 10. Range, vòng lặp, nhãn

### 10.1 Range

| Kotlin | Gồm | Java |
|---|---|---|
| `1..5` | 1, 2, 3, 4, 5 | `i = 1; i <= 5` |
| `1 until 5` | 1, 2, 3, 4 | `i = 1; i < 5` |
| `list.indices` | `0 until list.size` | `i = 0; i < list.size()` |
| `list.lastIndex` | `list.size - 1` | `list.size() - 1` |
| `x in a..b` | `a <= x && x <= b` | |
| `'0'..'9'` | range ký tự | |

```kotlin
if (status in 200..299) {                                     // B:588
return code in 400..599 && code !in setOf(401, 403, 404)      // B:909
.filter { it.length >= minLength && !it.all { c -> c in '0'..'9' } }   // B:125
```

Chạy tay `B:909`:

| `code` | `in 400..599` | `!in {401,403,404}` | Kết quả |
|---|---|---|---|
| 422 | đúng | đúng | `true` |
| 403 | đúng | sai | `false` |
| 404 | đúng | sai | `false` |
| 500 | đúng | đúng | `true` |
| 200 | sai | | `false` |

### 10.2 `for`

Kotlin chỉ có `for (x in ...)`. Không có `for (int i = 0; ...; i++)`.

```kotlin
for (srcIndex in actions.indices) { ... }                          // O:577
for (followUpIndex in (srcIndex + 1) until actions.size) { ... }   // O:587
```

Java:

```java
for (int srcIndex = 0; srcIndex < actions.size(); srcIndex++) { ... }
for (int followUpIndex = srcIndex + 1; followUpIndex < actions.size(); followUpIndex++) { ... }
```

Range là một collection, nên gọi hàm collection lên nó được:

```kotlin
val hasTransition = (srcIndex + 1 until followUpIndex).any { ... }   // O:597
(0 until rounds).map { j -> ... }                                    // B:1290
```

### 10.3 `for` có destructuring và `withIndex`

```kotlin
for ((index, entry) in queue.withIndex()) {        // B:666
    val (transitionOp, reducedRoleCandidates) = entry   // B:667
    ...
    candidateIsLast = index == queue.lastIndex     // B:676
```

Chạy tay, giả sử `queue` có 2 phần tử `[(PUT:/users/{username}/role, [VIEWER]), (PATCH:/users/{id}, [false])]`:

| Vòng | `index` | `transitionOp` | `reducedRoleCandidates` | `candidateIsLast` |
|---|---|---|---|---|
| 1 | 0 | `PUT:/users/{username}/role` | `[VIEWER]` | `false` |
| 2 | 1 | `PATCH:/users/{id}` | `[false]` | `true` |

Thêm: `for ((verb, op) in ordered)` (`B:710`), `for ((k, v) in plan)` (`B:1312`).

### 10.4 Nhãn: `break@`, `continue@`, `return@`

Nhãn `ten@` đặt trước vòng lặp. `break@ten` thoát vòng có nhãn đó. Java có cùng khái niệm: `sources: for (...)` và
`break sources;`.

```kotlin
sources@ for ((verb, op) in ordered) {                 // B:710
    run {
        ...
        for (victimSlice in victimCandidates) {         // B:726
            ...
            if (candidateCapReached()) {
                break@sources                           // B:736: thoát cả vòng ngoài
            }
            if (buildStatefulAuthzTriple(...)) break    // B:738: chỉ thoát vòng victimSlice
            ...
        }
    }
}
```

`return@ten` trả giá trị **cho lambda**, thay vì thoát cả hàm. Nhãn là tên hàm nhận lambda:

```kotlin
private fun victimObjects(...): List<ScoredObject> = victimObjectCache.getOrPut("...") {   // B:1419–1423
    val idKeys = identityKeys(victimAuth, victimLeaf)
    if (idKeys.isEmpty()) return@getOrPut emptyList()      // B:1425
    ...
}
```

Chạy tay, `idKeys` rỗng: lambda trả `emptyList()`, `getOrPut` lưu `emptyList()` vào cache dưới khoá đó, `victimObjects`
trả `emptyList()`. Lần gọi sau với cùng khoá đọc cache, không chạy lambda.

### 10.5 `run { }` quanh thân vòng lặp

`B:711` bọc thân vòng `sources@` trong `run { ... }`. `run` chạy khối ngay và trả giá trị dòng cuối. `return` ở `B:715`
nằm trong khối `run` nhưng thoát hẳn `addForStatefulAccessControl`, vì `run` là hàm `inline` (§17.4). Khối `run` ở đây
không đổi hành vi; bỏ nó đi, mã chạy y hệt.

---

## 11. Ngoại lệ và try

### 11.1 Không có checked exception

Java bắt `catch` hoặc `throws` cho `IOException`, `JsonProcessingException`. Kotlin không bắt. `ObjectMapper().readTree(x)`
ném `JsonProcessingException`; trong Kotlin, gọi không có `try` vẫn biên dịch được.

### 11.2 `try` trả giá trị

```kotlin
val v = try { java.net.URLDecoder.decode(kv[1], "UTF-8") } catch (e: Exception) { kv[1] }   // B:1402
```

| `kv[1]` | `decode` | `v` |
|---|---|---|
| `"alice%40x.io"` | trả `"alice@x.io"` | `"alice@x.io"` |
| `"%zz"` | ném `IllegalArgumentException` | `"%zz"` |

```kotlin
val node = try { mapper.readTree(body) } catch (e: Exception) { continue }    // B:1434
```

Thân phản hồi không phải JSON: bỏ qua, sang phản hồi tiếp theo.

Một `try` dài hơn, `B:567–583`:

```kotlin
val status = try {
    val b = resetClient.target(url).request()
    val empty = Entity.entity("", MediaType.APPLICATION_JSON_TYPE)
    val r = when (verb.uppercase()) { ... }
    r.status.also { r.close() }
} catch (e: Exception) {
    LoggingUtil.getInfoLogger().warn("SUT state reset via $spec failed: ${e.message}")
    return
}
```

Giá trị của `try` là dòng cuối, `r.status` (§19.2). Lỗi mạng: ghi cảnh báo, thoát hàm. `e.message` là `e.getMessage()`.

### 11.3 `try / finally`

```kotlin
statefulTripleUnderEvaluation = true                                   // B:967
val ei = try {
    fitness.computeWholeAchievedCoverageForPostProcessing(base)
} finally {
    statefulTripleUnderEvaluation = false
}
```

`B:967–972`. Cờ bật trong lúc chấm bộ ba, và tắt kể cả khi chấm ném lỗi. Oracle đọc cờ này ở `O:561`.

### 11.4 Bắt một loại cụ thể

```kotlin
val verb = try {                                    // B:264–270
    HttpVerb.valueOf(parts[0].uppercase())
} catch (e: IllegalArgumentException) {
    LoggingUtil.uniqueUserWarn("Ignoring statefulAuthzTransition: unsupported verb '${parts[0]}'")
    return null
}
```

`HttpVerb.valueOf("FOO")` ném `IllegalArgumentException`, giống `Enum.valueOf` của Java.

### 11.5 `catch` rỗng

```kotlin
try {                                               // B:1391–1398
    val node = ObjectMapper().readTree(payload)
    ...
} catch (e: Exception) {
}
```

Payload đăng nhập không phải JSON thì bỏ qua lỗi, xuống `B:1399` thử đọc dạng form `a=b&c=d`.

---

## 12. Class, constructor, property

### 12.1 Primary constructor

```kotlin
class SchemaField(val loc: String, val name: String, val gene: Gene, val value: Gene) {   // B:128
```

Một dòng này khai báo 4 field `private final`, một constructor 4 tham số và 4 getter. Java:

```java
public final class SchemaField {
    private final String loc; private final String name; private final Gene gene; private final Gene value;
    public SchemaField(String loc, String name, Gene gene, Gene value) {
        this.loc = loc; this.name = name; this.gene = gene; this.value = value;
    }
    public String getLoc() { return loc; }
    ...
}
```

Tạo đối tượng không có `new`: `SchemaField("body", name, g, v)` (`B:179`).

Tham số có `val`/`var` thành property. Tham số không có `val`/`var` chỉ là tham số constructor. Upstream
`RestCallAction.kt:26–36`:

```kotlin
class RestCallAction(
    val id:String,                                         // property
    val verb: HttpVerb,                                    // property
    val path: RestPath,                                    // property
    parameters: MutableList<Param>,                        // chỉ là tham số, chuyển cho lớp cha
    auth: HttpWsAuthenticationInfo = HttpWsNoAuth(),       // tham số, có mặc định
    ...
    var usePreviousLocationId: String? = null,             // property gán lại được, nullable
```

### 12.2 Property có khởi tạo, `init`

```kotlin
class SchemaField(val loc: String, val name: String, val gene: Gene, val value: Gene) {
    val leaf: String = name.split(".").last().replace("[]", "")                    // B:129
    val parents: List<String> = name.split(".").dropLast(1).map { it.replace("[]", "") }   // B:130
    val enumValues: List<String>                                                    // B:131
    val kind: String                                                                // B:132

    init {                                                                          // B:134
        val inner = (value as? ArrayGene<*>)?.let { valueGene(it.template) }
        val enum = (value as? EnumGene<*>) ?: (inner as? EnumGene<*>)
        enumValues = enum?.values?.map { it.toString() } ?: emptyList()
        kind = when { ... }
    }
```

Thứ tự chạy khi tạo: `leaf`, `parents`, rồi khối `init`, theo thứ tự trong file. `enumValues` và `kind` là `val` chưa có
giá trị; `init` gán mỗi cái đúng một lần. `init` là thân constructor của Java.

Chạy tay, giả sử `name = "user.roles[]"`:

```
name.split(".")                → ["user", "roles[]"]
.last()                        → "roles[]"
.replace("[]", "")             → "roles"                 leaf
name.split(".").dropLast(1)    → ["user"]
.map { it.replace("[]", "") }  → ["user"]                parents
```

### 12.3 Getter tự viết

```kotlin
val key: String get() = "$loc:$name"     // B:148
```

Không có field. Mỗi lần đọc `f.key` thì tính lại. Java: `public String getKey() { return loc + ":" + name; }`.
`javap` thấy `public final java.lang.String getKey();` **(chạy thật)**.

### 12.4 `private set`

```kotlin
var statefulTripleUnderEvaluation = false   // B:549
    private set                             // B:550
```

Ngoài class chỉ đọc được; trong class ghi được. `javap` chỉ thấy getter công khai **(chạy thật)**:

```
private boolean statefulTripleUnderEvaluation;
public final boolean getStatefulTripleUnderEvaluation();
```

Oracle đọc: `if (!restSecurityBuilder.statefulTripleUnderEvaluation) return` (`O:561`). Từ Kotlin, đọc property là
`x.ten`, sau biên dịch thành `x.getTen()`.

### 12.5 `lateinit var` và `@Inject`

```kotlin
@Inject                                          // B:281
private lateinit var archive: Archive<RestIndividual>
...
private lateinit var actionDefinitions: List<RestCallAction>   // B:317
```

Property không null phải có giá trị lúc tạo đối tượng. `lateinit` hoãn việc đó. Guice tạo `RestSecurityBuilder` rồi gán
các field `@Inject`. Đọc trước khi gán thì ném `UninitializedPropertyAccessException`. `lateinit` chỉ dùng cho `var`,
kiểu không null, không phải kiểu nguyên thuỷ. Upstream `core` dùng `lateinit var` ở 282 dòng.

Java: `@Inject private Archive<RestIndividual> archive;`.

### 12.6 `by lazy`

```kotlin
private val resetClient: Client by lazy { HttpClientFactory.createTrustingJerseyClient() }   // B:552
```

Lần đầu đọc `resetClient` thì chạy khối và nhớ kết quả; lần sau trả lại đúng đối tượng đó. `javap` **(chạy thật)**:

```
private final kotlin.Lazy resetClient$delegate;
private final javax.ws.rs.client.Client getResetClient();
```

Chạy tay: lượt chạy không có `--statefulAuthzResetEndpoint` thì `resetSutState` thoát ở `B:557`, trước dòng `B:568` đọc
`resetClient`. HTTP client không bao giờ được tạo.

### 12.7 Kế thừa, interface, `override`, `open`

```kotlin
class RestSecurityBuilder : TimeBoxedPhase {         // B:74
    ...
    override fun applyPhase() {                      // B:340
        applySecurityPhase()
    }

    override fun hasPhaseTimedOut(): Boolean {       // B:344
        return epc.hasPhaseTimedOut(ExecutionPhaseController.Phase.SECURITY)
    }
```

`TimeBoxedPhase` là interface (`core/.../search/service/time/TimeBoxedPhase.kt:12`):

```kotlin
interface TimeBoxedPhase {
    fun applyPhase()
    fun hasPhaseTimedOut(): Boolean
}
```

Java: `public class RestSecurityBuilder implements TimeBoxedPhase { @Override public void applyPhase() { ... } }`.

Kế thừa class dùng cùng dấu `:` và gọi constructor cha ngay đó. Upstream `Action.kt:15`:

```kotlin
abstract class Action(children: List<StructuralElement>) : ActionComponent(children, ...)
```

Java: `public abstract class Action extends ActionComponent { public Action(List<StructuralElement> children) { super(children, ...); } }`.

Class và hàm Kotlin mặc định `final`. Muốn cho kế thừa phải ghi `open class`; `abstract class` thì tự mở. Trong `core`:
74 dòng `abstract class`, 33 dòng `open class`. Hai lớp gốc của kiến trúc: `abstract class Gene(` (`Gene.kt:53`),
`abstract class Individual(` (`Individual.kt:40`).

### 12.8 Visibility

| Kotlin | Java | Ghi chú |
|---|---|---|
| (bỏ trống) | `public` | Kotlin mặc định `public` |
| `private` | `private` | |
| `protected` | `protected` | Kotlin: chỉ lớp con, không gồm cùng package |
| `internal` | gần với package-private | thấy trong cùng module Maven |

---

## 13. data class, Pair, destructuring

### 13.1 data class

`data class` sinh `equals`, `hashCode`, `toString`, `copy`, `componentN` từ các property trong primary constructor (§1.1).

```kotlin
data class DeclaredTransition(val verb: HttpVerb, val path: String, val bindings: Map<String, String>)   // B:251
private data class ScoredObject(val verb: HttpVerb, val path: String, val node: JsonNode, val matches: Int)   // B:1415
```

`toString` **(chạy thật)**:

```
parseDeclaredTransition("POST /api/set_user_permission user=<victim> role=1 permission=0")
→ DeclaredTransition(verb=POST, path=/api/set_user_permission, bindings={user=<victim>, role=1, permission=0})
```

Java 17 gần nhất: `record DeclaredTransition(HttpVerb verb, String path, Map<String, String> bindings) {}`.

### 13.2 `Pair`, `Triple`, `to`

`Pair<A, B>` và `Triple<A, B, C>` là data class có sẵn. `a to b` tạo `Pair(a, b)`.

```kotlin
val pair = transitionDef.getName() to victimAuth.name        // B:774
private val refusedTransitionVictims = mutableSetOf<Pair<String, String>>()   // B:533
if (refusedTransitionVictims.contains(pair)) { ... }         // B:775
```

Chạy tay Tier-1: `pair = Pair("PUT:/users/{username}/role", "alice")`. `contains` dùng `equals` của data class, nên
một `Pair` mới tạo với cùng hai chuỗi vẫn được tìm thấy. `javap`:
`java.util.Set<kotlin.Pair<java.lang.String, java.lang.String>> refusedTransitionVictims` **(chạy thật)**.

Đọc phần tử: `pair.first`, `pair.second`; `triple.first`, `.second`, `.third` (`B:106`).

### 13.3 Destructuring

`val (a, b) = x` gọi `x.component1()`, `x.component2()`. Dùng được với data class, `Pair`, `List`, `Map.Entry`.

```kotlin
val parts = spec.trim().split(Regex("\\s+"), 2)    // B:559
val (verb, url) = parts                           // B:565
```

Chạy tay `spec = "POST http://localhost:8080/reset"`:

```
split(Regex("\\s+"), 2)  → ["POST", "http://localhost:8080/reset"]
val (verb, url)          → verb = "POST", url = "http://localhost:8080/reset"
```

Java:

```java
String[] parts = spec.trim().split("\\s+", 2);
String verb = parts[0];
String url = parts[1];
```

Destructuring trong `for` (§10.3) và trong tham số lambda (§17.2).

---

## 14. companion object và object

### 14.1 companion object

Kotlin không có từ khoá `static`. Thành viên thuộc về class (không thuộc về từng đối tượng) đặt trong `companion object`.

```kotlin
class RestSecurityBuilder : TimeBoxedPhase {
    companion object {                                                                    // B:76
        private val log: Logger = LoggerFactory.getLogger(RestSecurityBuilder::class.java)  // B:77
        private const val MODEL_RESOURCE = "/stateful-authz-model.csv"
        private val MODEL = loadModel()                                                   // B:117
        fun tokens(text: String, minLength: Int = MIN_TOKEN_LENGTH): Set<String> = ...
        fun looksLikePermissionReducingTransition(a: RestCallAction, declared: String = ""): Boolean { ... }
        ...
    }
```

Java:

```java
public class RestSecurityBuilder implements TimeBoxedPhase {
    private static final Logger log = LoggerFactory.getLogger(RestSecurityBuilder.class);
    private static final String MODEL_RESOURCE = "/stateful-authz-model.csv";
    private static final Map<String, Map<String, Double>> MODEL = loadModel();
    public static Set<String> tokens(String text, int minLength) { ... }
```

Gọi từ Kotlin như hàm static: `RestSecurityBuilder.looksLikePermissionReducingTransition(t, config.statefulAuthzTransition)`
(`O:602`).

Sau biên dịch, `companion object` là một đối tượng thật tên `Companion` **(chạy thật)**:

```
public static final org.evomaster.core.problem.rest.service.RestSecurityBuilder$Companion Companion;
```

Từ Java phải gọi `RestSecurityBuilder.Companion.tokens(...)`, trừ khi hàm có `@JvmStatic` (upstream dùng ở 9 dòng).

`MODEL = loadModel()` chạy một lần khi class được nạp, như khối `static {}` của Java. File CSV mô hình được đọc một lần
mỗi JVM.

### 14.2 object

`object Ten { ... }` khai báo một singleton: class và đối tượng duy nhất của nó. Upstream `core/.../Lazy.kt:3`:

```kotlin
object Lazy {
    fun assert(predicate: () -> Boolean) {
        if (javaClass.desiredAssertionStatus()) {
            assert(predicate.invoke())
        }
    }
}
```

Mã ta gọi: `org.evomaster.core.Lazy.assert { base.verifyValidity(); true }` (`B:963`). Lambda chỉ chạy khi JVM bật
`-ea`. Upstream có 76 dòng khai báo `object`.

---

## 15. enum class

```kotlin
enum class HttpVerb {           // core/.../problem/rest/data/HttpVerb.kt:6
    GET,
    POST,
    PUT,
    DELETE,
    ...
}
```

Enum có constructor, `ExperimentalFaultCategory.kt:5–10`:

```kotlin
enum class ExperimentalFaultCategory(
    private val code: Int,
    private val descriptiveName: String,
    private val testCaseLabel: String,
    private val fullDescription: String,
) : FaultCategory {
```

Hằng ta thêm, `ExperimentalFaultCategory.kt:54–57`:

```kotlin
SECURITY_STATEFUL_AUTHORIZATION(970,
    "Stateful Authorization: privilege persists after a permission-reducing transition",
    "stillAllowedAfterPermissionRevoked",
    "An action requiring a privilege, once observed ALLOWED, was still ALLOWED when ..."),
```

Dùng:

| Mã | Ra | Chỗ |
|---|---|---|
| `HttpVerb.valueOf("post".uppercase())` | `HttpVerb.POST` | `B:265` |
| `a.verb.name` với `a.verb = PUT` | `"PUT"` | `B:203`, feature `"v:PUT"` |
| `a.verb !in TRANSITION_VERBS` với `GET` | `true` | `B:245` |

Dấu phẩy cuối trong danh sách tham số (`fullDescription: String,`) được phép trong Kotlin.

---

## 16. Collection

### 16.1 Chỉ đọc và đổi được

| Chỉ đọc | Đổi được | Tạo | Java bên dưới |
|---|---|---|---|
| `List<T>` | `MutableList<T>` | `listOf(...)`, `mutableListOf(...)`, `emptyList()` | `java.util.List` |
| `Set<T>` | `MutableSet<T>` | `setOf(...)`, `mutableSetOf(...)`, `emptySet()` | `java.util.Set` (`LinkedHashSet`, giữ thứ tự chèn) |
| `Map<K, V>` | `MutableMap<K, V>` | `mapOf(k to v)`, `mutableMapOf()`, `emptyMap()` | `java.util.Map` (`LinkedHashMap`) |

`List<T>` không có `add`. Muốn thêm phải dùng `MutableList<T>`.

```kotlin
fun schemaFields(a: RestCallAction): List<SchemaField> {    // B:190
    val out = mutableListOf<SchemaField>()                  // đổi được bên trong hàm
    ...
    return out.take(MAX_FIELDS)                             // trả ra ngoài kiểu chỉ đọc
}
private fun walkBody(name: String, g: Gene, depth: Int, out: MutableList<SchemaField>)   // B:177: nhận list đổi được
```

### 16.2 Truy cập

| Mã | Nghĩa | Java |
|---|---|---|
| `actions[srcIndex]` | phần tử thứ `srcIndex` | `actions.get(srcIndex)` |
| `model[it]` | giá trị của khoá, `V?` | `model.get(it)` |
| `x in set` | có chứa | `set.contains(x)` |
| `list.size` | số phần tử | `list.size()` |
| `map.getOrPut(k) { ... }` | có khoá thì trả, chưa có thì tính, lưu, trả | `map.computeIfAbsent(k, k -> ...)` |
| `list1 + list2` | list mới nối hai list | |
| `set.retainAll(other)` | giữ phần chung | như Java |

```kotlin
fun transitionEvidence(a: RestCallAction): Double =
    opEvidenceCache.getOrPut(a.getName()) { evidence("op", opFeatures(a)) }    // B:220–221

low + rest                                // B:1236
keepOnlyTargetFields(transition, (targeted + reduced).toSet())   // B:946
privilegeReducedInPhase.retainAll(privilegeReducedByProof)       // B:678
```

Chạy tay `B:220`: lần đầu với `"PUT:/users/{username}/role"` tính `evidence` rồi lưu; các lần sau trong cùng JVM đọc
cache.

---

## 17. Lambda

### 17.1 Cú pháp

```kotlin
{ a: Int, b: Int -> a + b }     // hai tham số
{ x -> x.name }                 // một tham số
{ it.name }                     // một tham số, tên ngầm là it
{ base.verifyValidity(); true } // nhiều câu lệnh: giá trị là biểu thức cuối
```

Khi lambda là tham số cuối, đặt nó ra ngoài ngoặc; khi là tham số duy nhất, bỏ luôn ngoặc:

```kotlin
list.filter({ it.isNotEmpty() })   // được
list.filter() { it.isNotEmpty() }  // được
list.filter { it.isNotEmpty() }    // cách viết thường gặp
```

Java: `list.stream().filter(it -> !it.isEmpty())`.

Kiểu hàm: `() -> Boolean` là hàm không tham số trả `Boolean` (`Lazy.assert(predicate: () -> Boolean)`), `(Int) -> String`
là hàm nhận `Int` trả `String`.

### 17.2 Destructuring trong tham số lambda

```kotlin
node.fields().forEach { (k, v) -> if (v.isTextual && v.asText() == name) keys.add(k) }   // B:1394
.mapValues { (_, rows) -> rows.toMap() }                                                 // B:107
declared.bindings.all { (name, raw) -> ... }                                             // B:1637
```

`(k, v)` tách `Map.Entry` thành khoá và giá trị. `_` bỏ thành phần không dùng.

Java:

```java
node.fields().forEachRemaining(e -> { if (e.getValue().isTextual() && e.getValue().asText().equals(name)) keys.add(e.getKey()); });
```

Chạy tay `B:1394`, giả sử payload đăng nhập `{"username":"alice","password":"alicepass"}`, `name = "alice"`:

| `k` | `v` | `v.isTextual && v.asText() == name` | `keys` |
|---|---|---|---|
| `username` | `"alice"` | đúng | `{username}` |
| `password` | `"alicepass"` | sai | `{username}` |

### 17.3 Tên tham số tường minh khi lồng lambda

Lambda lồng nhau thì `it` của trong che `it` của ngoài. Mã ta đặt tên cho lambda trong:

```kotlin
.filter { it.length >= minLength && !it.all { c -> c in '0'..'9' } }    // B:125
.flatMap { TOKEN_PART.findAll(it).map { m -> m.value.lowercase() }.toList() }   // B:1480
```

### 17.4 `return` trong lambda

Trong lambda truyền vào hàm `inline` (`forEach`, `map`, `filter`, `let`, `run`,...), `return` trần thoát **hàm bao
ngoài**. Muốn chỉ kết thúc lambda, dùng `return@tenHam` (§10.4).

```kotlin
parseDeclaredTransition(declared)?.let {
    return a.verb == it.verb && ...     // B:243: thoát hẳn looksLikePermissionReducingTransition
}
```

Java lambda không làm được điều này; `return` trong lambda Java chỉ thoát lambda.

---

## 18. Hàm trên collection

Kotlin gọi thẳng các hàm này trên `List`, `Set`, `Map`, không cần `.stream()` hay `.collect(...)`. Mỗi bước tạo một list
mới (trừ khi dùng `asSequence()`, §18.8).

### 18.1 Bảng tra

| Hàm | Làm gì | Java Stream | Chỗ trong mã ta |
|---|---|---|---|
| `map { }` | biến đổi từng phần tử | `.map(...)` | `B:103` |
| `filter { }` | giữ phần tử thoả | `.filter(...)` | `B:104` |
| `mapNotNull { }` | biến đổi, bỏ kết quả null | `.map(...).filter(Objects::nonNull)` | `B:105` |
| `flatMap { }` | biến mỗi phần tử thành list rồi nối | `.flatMap(x -> f(x).stream())` | `B:124` |
| `filterIsInstance<T>()` | giữ phần tử kiểu `T` | `.filter(T.class::isInstance).map(T.class::cast)` | `B:192` |
| `forEach { }` | chạy cho từng phần tử | `.forEach(...)` | `B:152` |
| `any { }` | có ít nhất một thoả | `.anyMatch(...)` | `O:597` |
| `all { }` | mọi phần tử thoả | `.allMatch(...)` | `B:839` |
| `none { }` | không phần tử nào thoả | `.noneMatch(...)` | `B:1249` |
| `find { }` / `firstOrNull { }` | phần tử đầu thoả, hoặc `null` | `.filter(...).findFirst().orElse(null)` | `O:568`, `B:616` |
| `first()` / `last()` | đầu / cuối, rỗng thì ném | | `B:129`, `B:170` |
| `firstOrNull()` / `lastOrNull()` | đầu / cuối, rỗng thì `null` | | `B:771` |
| `count { }` | đếm phần tử thoả | `.filter(...).count()` | `B:1449` |
| `sumOf { }` | tổng | `.mapToDouble(...).sum()` | `B:211` |
| `maxOf { }` / `maxOfOrNull { }` | giá trị lớn nhất | `.mapToDouble(...).max()` | `B:1289`, `B:227` |
| `maxByOrNull { }` | phần tử có khoá lớn nhất | `.max(Comparator.comparing(...)).orElse(null)` | `B:1220` |
| `sortedBy { }` / `sortedByDescending { }` | sắp theo khoá | `.sorted(Comparator.comparing(...))` | `B:721`, `B:789` |
| `sortedWith(compareBy(...))` | sắp nhiều khoá | `.sorted(comparing(a).thenComparing(b))` | `B:701`, `B:1204` |
| `distinct()` | bỏ trùng | `.distinct()` | `B:1249` |
| `distinctBy { }` | bỏ trùng theo khoá, giữ cái đầu | | `B:722` |
| `groupBy({ k }, { v })` | gom thành `Map<K, List<V>>` | `Collectors.groupingBy(k, mapping(v, toList()))` | `B:106` |
| `associate { k to v }` | thành `Map<K, V>` | `Collectors.toMap(k, v)` | `B:273` |
| `associateBy { k }` | `Map<K, phần tử>` | `Collectors.toMap(k, x -> x)` | `B:1310` |
| `mapValues { }` | đổi giá trị của map | | `B:107` |
| `toMap()` / `toSet()` / `toMutableSet()` | đổi kiểu | `Collectors.toMap/toSet` | `B:107`, `B:126`, `B:1410` |
| `take(n)` / `drop(n)` / `dropLast(n)` | lấy n đầu / bỏ n đầu / bỏ n cuối | `.limit(n)` / `.skip(n)` | `B:197`, `B:271`, `B:130` |
| `joinToString(sep) { }` | nối thành chuỗi | `Collectors.joining(sep)` | `B:999` |
| `withIndex()` | cặp (chỉ số, phần tử) | | `B:666` |
| `indexOf(x)` | vị trí | `list.indexOf(x)` | `B:1206` |
| `isEmpty()` / `isNotEmpty()` | rỗng / không rỗng | | `B:653` |
| `asSequence()` | xử lý lười | `.stream()` | `B:1216` |

### 18.2 `loadModel`: đọc CSV thành bảng hai tầng

`B:95–118`. Hàm đọc file CSV mô hình thành `Map<String, Map<String, Double>>`: tên bảng, tên feature, trọng số.

```kotlin
val model = stream.bufferedReader().readLines()                                              // B:102
    .map { it.trim().split(",") }                                                            // B:103
    .filter { it.size == 3 }                                                                 // B:104
    .mapNotNull { row -> row[2].toDoubleOrNull()?.let { Triple(row[0], row[1], it) } }       // B:105
    .groupBy({ it.first }, { it.second to it.third })                                        // B:106
    .mapValues { (_, rows) -> rows.toMap() }                                                 // B:107
```

Chạy tay với 5 dòng đầu thật của CSV mô hình (dòng 1–2, 92, 248, 249):

```
table,feature,weight
op,__prior__,-3.935071909737789
op,f:role,2.119715440817776
low,viewer,0.3333333333333333
high,admin,0.7714285714285715
```

| Dòng | Sau bước | Giá trị |
|---|---|---|
| 102 | `readLines()` | 5 chuỗi |
| 103 | `map { split(",") }` | `[[table,feature,weight], [op,__prior__,-3.935…], [op,f:role,2.1197…], [low,viewer,0.3333…], [high,admin,0.7714…]]` |
| 104 | `filter { size == 3 }` | giữ cả 5 |
| 105 | `mapNotNull` | `"weight".toDoubleOrNull()` ra `null`, bỏ dòng tiêu đề; còn 4 `Triple`: `(op,__prior__,-3.935)`, `(op,f:role,2.1197)`, `(low,viewer,0.3333)`, `(high,admin,0.7714)` |
| 106 | `groupBy` | `{op=[(__prior__,-3.935), (f:role,2.1197)], low=[(viewer,0.3333)], high=[(admin,0.7714)]}` |
| 107 | `mapValues { toMap() }` | `{op={__prior__=-3.935, f:role=2.1197}, low={viewer=0.3333}, high={admin=0.7714}}` |

Java Stream tương đương:

```java
Map<String, Map<String, Double>> model = new BufferedReader(new InputStreamReader(stream)).lines()
    .map(l -> l.trim().split(","))
    .filter(r -> r.length == 3)
    .map(r -> { try { return new Object[]{r[0], r[1], Double.parseDouble(r[2])}; } catch (NumberFormatException e) { return null; } })
    .filter(Objects::nonNull)
    .collect(Collectors.groupingBy(t -> (String) t[0], LinkedHashMap::new,
             Collectors.toMap(t -> (String) t[1], t -> (Double) t[2], (a, b) -> b, LinkedHashMap::new)));
```

Ngay sau đó, `B:108–109` kiểm bảng nào thiếu:

```kotlin
val missing = listOf("op", "role", "victim").filter { model[it]?.containsKey(PRIOR) != true } +
    listOf("low", "high", "lowstr", "highstr").filter { model[it].isNullOrEmpty() }
```

Với model 5 dòng ở trên: `role`, `victim` không có bảng, `lowstr`, `highstr` không có bảng, nên
`missing = [role, victim, lowstr, highstr]` và `B:111` ghi cảnh báo. Với file thật: 0 trên 180 log của
`p2f-full-20261015` có dòng cảnh báo này (`grep -l 'carries no usable table'`).

### 18.3 `tokens`: tách tên thành từ

`B:121–126`:

```kotlin
fun tokens(text: String, minLength: Int = MIN_TOKEN_LENGTH): Set<String> =
    text.split(TOKEN_PIECE)
        .filter { it.isNotEmpty() }
        .flatMap { piece -> TOKEN_PART.findAll(piece).map { it.value.lowercase() }.toList() }
        .filter { it.length >= minLength && !it.all { c -> c in '0'..'9' } }
        .toSet()
```

Chạy tay `tokens("/api/users/{userId}/role")`, `minLength = 4`:

| Dòng | Bước | Giá trị |
|---|---|---|
| 122 | `split(TOKEN_PIECE)` | `["", "api", "users", "userId", "role"]` |
| 123 | `filter { isNotEmpty() }` | `["api", "users", "userId", "role"]` |
| 124 | `flatMap { findAll(TOKEN_PART) }` | `api → [api]`, `users → [users]`, `userId → [user, id]`, `role → [role]`; nối: `[api, users, user, id, role]` |
| 125 | `filter { length >= 4 && không toàn số }` | `[users, user, role]` |
| 126 | `toSet()` | `{users, user, role}` |

Kết quả **(chạy thật)**: `[users, user, role]`. Thêm **(chạy thật)**:

| Vào | Ra | Lý do |
|---|---|---|
| `"/users/{username}/role"` | `[users, username, role]` | `username` toàn chữ thường, một từ |
| `"HTTPServer"` | `[http, server]` | `[A-Z]+(?![a-z])` lấy `HTTP`, chừa `S` cho `Server` |
| `"/api/set_user_permission"` | `[user, permission]` | `api`, `set` dưới 4 ký tự |
| `"v2Items123"` | `[items123]` | `v2` dưới 4 ký tự |

`findAll` trả `Sequence<MatchResult>`; `.map { }` trên sequence cũng lười, nên cần `.toList()` để `flatMap` nhận list.

### 18.4 `opFeatures` và `transitionScore`: điểm Naive Bayes của một endpoint

```kotlin
fun opFeatures(a: RestCallAction): Set<String> {                                     // B:202–207
    val fs = mutableSetOf("v:${a.verb.name}")
    tokens(a.path.toString()).forEach { fs.add("p:$it") }
    schemaFields(a).forEach { f -> tokens(f.leaf).forEach { fs.add("f:$it") } }
    return fs
}
private fun evidence(name: String, features: Set<String>): Double {                  // B:209–212
    val t = table(name)
    return features.sumOf { t[it] ?: 0.0 }
}
fun transitionScore(a: RestCallAction): Double = prior("op") + transitionEvidence(a)  // B:223
```

Chạy tay trên Tier-1 `PUT /users/{username}/role`, trường: path `username`, body `role`. Trọng số lấy từ bảng `op` của CSV
mô hình, cộng bằng Python:

| Feature | Từ đâu | Trọng số |
|---|---|---|
| `v:PUT` | verb | 0,4248 |
| `p:users` | path | 2,3680 |
| `p:username` | path | 2,5984 |
| `p:role` | path | 3,1320 |
| `f:username` | path param `username` | 1,7958 |
| `f:role` | body `role` | 2,1197 |
| `sumOf` | | 12,4387 |
| `prior("op")` | `op,__prior__` | −3,9351 |
| `transitionScore` | | **8,5036** |

`8,5036 > 0`, nên `looksLikePermissionReducingTransition` trả `true` (`B:248`). Feature không có trong bảng thì
`t[it] ?: 0.0` cộng 0.

### 18.5 `reducedRoleValues`: chọn giá trị vai trò thấp hơn

```kotlin
fun valueScore(name: String, value: String): Double {                               // B:225–228
    val v = value.lowercase()
    return table(name).filter { v.contains(it.key) }.maxOfOrNull { it.value } ?: 0.0
}
```

`filter` trên `Map` nhận từng `Map.Entry`; `it.key`, `it.value`. Kết quả **(chạy thật)**:

| `value` | `valueScore("low", value)` | `valueScore("high", value)` | Khoá khớp |
|---|---|---|---|
| `VIEWER` | 0,3333 | 0,0 | `low.viewer`; bảng `high` không có khoá nào nằm trong `viewer`, `maxOfOrNull` ra `null`, `?: 0.0` |
| `ADMIN` | 0,0 | 0,7714 | `high.admin` |
| `ROLE_MEMBER` | 0,5625 | 0,125 | `member` có ở cả hai bảng |

Nhánh `"enum"` của `reducedRoleValues`, `B:1232–1249`:

```kotlin
"enum" -> {
    val keyed = field.enumValues.map { it to (valueScore("low", it) - valueScore("high", it)) }
    val low = keyed.filter { it.second > 0.0 }.sortedByDescending { it.second }.map { it.first }
    val rest = keyed.filter { it.second <= 0.0 }.sortedByDescending { it.second }.map { it.first }
    low + rest
}
...
val held = current.filter { valueScore("low", it) <= valueScore("high", it) }
return raw.filter { v -> held.none { it.equals(v, ignoreCase = true) } }.distinct()
```

Chạy tay Tier-1, `enumValues = [ADMIN, VIEWER]`, giả sử archive có phản hồi GET cho thấy alice đang `ADMIN`, nên
`current = [ADMIN]`:

| Dòng | Biến | Giá trị |
|---|---|---|
| 1233 | `keyed` | `[(ADMIN, −0,7714), (VIEWER, 0,3333)]` |
| 1234 | `low` | `[VIEWER]` |
| 1235 | `rest` | `[ADMIN]` |
| 1236 | `raw` | `[VIEWER, ADMIN]` |
| 1248 | `held` | `[ADMIN]` (0 ≤ 0,7714) |
| 1249 | kết quả | `[VIEWER]` |

Transition sinh ra là `PUT /users/alice/role` với thân `{"role":"VIEWER"}`, đúng lời gọi ở bước 4 của
`docs/handbook/tier1-reports-api.md`.

### 18.6 `sortedWith` nhiều khoá

```kotlin
private fun rankPermissionReducingTransitions(): List<RestCallAction> =       // B:1201–1207
    actionDefinitions
        .filter { it.verb in TRANSITION_VERBS && transitionScore(it) > 0.0 }
        .sortedWith(
            compareByDescending<RestCallAction> { transitionScore(it) }
                .thenBy { actionDefinitions.indexOf(it) }
        )
```

Điểm cao trước; bằng điểm thì endpoint đứng trước trong spec đi trước. Chạy tay, giả sử:

| Endpoint | Điểm | Vị trí trong spec |
|---|---|---|
| A | 8,5 | 5 |
| B | 8,5 | 2 |
| C | 3,1 | 1 |
| D | −1,0 | 0 |

`filter` bỏ D. Sắp: B, A, C.

Java: `.sorted(Comparator.comparingDouble((RestCallAction a) -> transitionScore(a)).reversed().thenComparingInt(defs::indexOf))`.

### 18.7 `associate`, `takeIf`, `drop`: phân tích `--statefulAuthzTransition`

`B:271–274`:

```kotlin
val bindings = parts.drop(2)
    .mapNotNull { p -> p.split("=", limit = 2).takeIf { it.size == 2 } }
    .associate { it[0] to it[1] }
return DeclaredTransition(verb, parts[1], bindings)
```

Chạy tay `spec = "POST /api/set_user_permission user=<victim> role=1 permission=0 foo"`:

| Bước | Giá trị |
|---|---|
| `parts` | `[POST, /api/set_user_permission, user=<victim>, role=1, permission=0, foo]` |
| `drop(2)` | `[user=<victim>, role=1, permission=0, foo]` |
| `split("=", limit = 2)` | `[user, <victim>]`, `[role, 1]`, `[permission, 0]`, `[foo]` |
| `takeIf { size == 2 }` | `[foo]` thành `null` |
| `mapNotNull` | bỏ `null`, còn 3 cặp |
| `associate` | `{user=<victim>, role=1, permission=0}` |

Không có `foo`, kết quả khớp `toString` **(chạy thật)** ở §13.1.

### 18.8 `asSequence`: xử lý lười

```kotlin
private fun roleField(a: RestCallAction): SchemaField? =      // B:1215–1220
    schemaFields(a).asSequence()
        .filter { it.loc != "path" }
        .map { it to fieldScore("role", it) }
        .filter { it.second > 0.0 }
        .maxByOrNull { it.second }?.first
```

`asSequence()` giống `.stream()`: các bước chạy lần lượt cho từng phần tử, không tạo list trung gian. Bước cuối
(`maxByOrNull`) kích hoạt việc chạy.

Chạy tay Tier-1. Điểm tính từ bảng `role` của CSV mô hình bằng Python; feature của body `role`: `k:enum`, `l:body`,
`w:role`, `n:role`, `e:admin`, `e:viewer`:

| Bước | Giá trị |
|---|---|
| `schemaFields` | `[path:username, body:role]` |
| `filter { loc != "path" }` | `[body:role]` |
| `map { it to fieldScore }` | `[(body:role, 8,4122)]` |
| `filter { second > 0 }` | giữ |
| `maxByOrNull { second }?.first` | `body:role` |

`victimField` (`B:1222–1225`) chọn trong các trường `kind` là `"str"` hoặc `"num"`: chỉ còn `path:username`, điểm
`victim` 5,1045. `body:role` là `"enum"` nên bị loại trước.

### 18.9 `joinToString`

```kotlin
val observed = listOf(sourceCode, transitionCode, followUpCode)   // B:998–999
    .joinToString("/") { it?.toString() ?: "-" }
```

| Vào | Ra |
|---|---|
| `[200, 200, 200]` | `"200/200/200"` (log) |
| `[200, null, null]` | `"200/-/-"` |

### 18.10 `distinctBy` sau `sortedBy`

```kotlin
val victimCandidates = RestIndividualSelectorUtils.findAndSlice(...)   // B:718–722
    .sortedBy { it.size() }
    .distinctBy { it.seeMainExecutableActions().last().auth.name }
```

Sắp các lát cắt theo số action tăng dần, rồi giữ lát đầu tiên của mỗi tài khoản. Chạy tay, giả sử 3 lát: alice (5 action),
bob (2), alice (3). Sau `sortedBy`: bob 2, alice 3, alice 5. Sau `distinctBy`: bob 2, alice 3.

### 18.11 `(0 until n).map` lồng `map`

```kotlin
val rounds = minOf(perField.maxOf { it.second.size }, MAX_PRIVILEGE_RESTORES)                 // B:1289
return (0 until rounds).map { j -> perField.map { (k, vs) -> k to vs[minOf(j, vs.size - 1)] } }   // B:1290
```

Chạy tay, giả sử `perField = [(body:role, [ADMIN, OWNER]), (body:admin, [true])]`:

```
maxOf { size }  = 2;  rounds = minOf(2, 3) = 2
j = 0:  [(body:role, ADMIN), (body:admin, true)]
j = 1:  [(body:role, OWNER), (body:admin, vs[minOf(1, 0)] = true)]
```

`minOf` là hàm cấp cao nhất, giống `Math.min`.

---

## 19. Scope function: let, also, run, apply, takeIf

Năm hàm nhỏ trong thư viện chuẩn, gọi được trên mọi đối tượng.

| Hàm | Trong khối, đối tượng là | Trả về | Dùng để |
|---|---|---|---|
| `x.let { }` | `it` | kết quả khối | biến đổi `x`, nhất là sau `?.` |
| `x.also { }` | `it` | chính `x` | làm thêm việc phụ, giữ nguyên giá trị |
| `run { }` | | kết quả khối | nhóm câu lệnh |
| `x.apply { }` | `this` | chính `x` | cấu hình đối tượng vừa tạo |
| `x.takeIf { }` | `it` | `x` nếu khối đúng, ngược lại `null` | lọc một giá trị |

### 19.1 `let`

```kotlin
.mapNotNull { row -> row[2].toDoubleOrNull()?.let { Triple(row[0], row[1], it) } }   // B:105
val inner = (value as? ArrayGene<*>)?.let { valueGene(it.template) }                 // B:135
```

`B:135`: `value` là `ArrayGene` thì `inner = valueGene(value.template)`; không phải thì `inner = null`.

Java:

```java
Gene inner = value instanceof ArrayGene<?> ag ? valueGene(ag.getTemplate()) : null;
```

### 19.2 `also`

```kotlin
r.status.also { r.close() }                                    // B:580
```

Đọc `r.status`, đóng `r`, trả giá trị status đã đọc. Java:

```java
int s = r.getStatus();
r.close();
return s;
```

```kotlin
(if (field == null) emptyList() else reducedRoleValues(field, current))
    .also { log.debug("Stateful-authorization victim '${victimAuth.name}' current roles $current, reduced role values $it") }   // B:800–801
```

Ghi log giá trị, rồi gán chính giá trị đó cho `roleValues`.

### 19.3 `run`

Xem §10.5.

### 19.4 `apply`

Mã ta không dùng. Upstream dùng ở 100 dòng. `Main.kt:110`:

```kotlin
val config = EMConfig().apply { updateProperties(options) }
```

Trong khối, `this` là đối tượng `EMConfig` vừa tạo; `updateProperties(options)` là `this.updateProperties(options)`.
`apply` trả chính đối tượng đó. Java:

```java
EMConfig config = new EMConfig();
config.updateProperties(options);
```

### 19.5 `takeIf` với `?:`

```kotlin
val putPatchCandidates = guardedCandidatesFor(listOf(HttpVerb.PUT, HttpVerb.PATCH))   // B:691
val candidates = putPatchCandidates.takeIf { l ->                                     // B:692–699
    l.any { (verb, op) ->
        RestIndividualSelectorUtils.findIndividuals(
            individualsInSolution, verb, op.path,
            statusGroup = StatusGroup.G_2xx, authenticated = true
        ).isNotEmpty()
    }
} ?: guardedCandidatesFor(listOf(HttpVerb.POST))
```

Có ít nhất một ứng viên PUT/PATCH từng được trả 2xx với một tài khoản đã đăng nhập thì dùng danh sách PUT/PATCH; ngược
lại, `takeIf` ra `null` và `?:` lấy danh sách POST.

Chạy tay Tier-1: `PUT /reports/{id}` có trong archive với 403 và 2xx, nên dùng danh sách PUT/PATCH. Log xác nhận source
được chọn là `PUT:/reports/{id}` **(log)**.

---

## 20. Generic

| Kotlin | Java | Chỗ |
|---|---|---|
| `List<Gene>` | `List<Gene>` | `B:168` |
| `Map<String, Map<String, Double>>` | như vậy | `B:95` |
| `ArrayGene<*>` | `ArrayGene<?>` | `B:135` |
| `MapGene<*, *>` | `MapGene<?, ?>` | `B:143` |
| `mutableSetOf<Pair<String, String>>()` | `new LinkedHashSet<Pair<String, String>>()` | `B:533` |
| `compareByDescending<RestCallAction> { }` | ghi rõ kiểu khi không suy ra được | `B:1205` |
| `class Minimizer<T: Individual>` | `class Minimizer<T extends Individual>` | upstream `Minimizer.kt:26` |
| `fun <T> compute(lambda: () -> T): T?` | `<T> T compute(Supplier<T> lambda)` | upstream `Lazy.kt` |

`<*>` (star projection): biết đó là `ArrayGene` nhưng không quan tâm kiểu phần tử.

Ép sang kiểu generic cụ thể không kiểm được lúc chạy, nên trình biên dịch cảnh báo; mã ta tắt cảnh báo:

```kotlin
@Suppress("UNCHECKED_CAST")                                       // B:1378
private fun clearArray(f: SchemaField): Boolean {
    val array = (f.value as? ArrayGene<Gene>) ?: return false     // B:1380
```

Java: `@SuppressWarnings("unchecked")`.

Lớp cốt lõi upstream đều có tham số kiểu: `Archive<RestIndividual>` (`B:282`), `FitnessFunction<RestIndividual>` (`B:294`),
`EvaluatedIndividual<RestIndividual>` (`B:324`). `Minimizer<T: Individual> : TimeBoxedPhase` là cùng dạng với
`RestSecurityBuilder : TimeBoxedPhase`, thêm tham số kiểu.

---

## 21. Annotation

Cú pháp như Java.

```kotlin
@Inject
private lateinit var config: EMConfig                  // B:302–303

@Suppress("UNCHECKED_CAST")                            // B:1378
```

Trên property cấu hình, `EMConfig:3044–3051`:

```kotlin
@Experimental
@Cfg("THESIS EXTENSION. Endpoint used to restore the SUT to a known state before each attempt at" +
        " building a stateful-authorization (MR-A1) triple, given as \"<VERB> <URL>\", eg" +
        ...)
var statefulAuthzResetEndpoint = ""
```

EvoMaster quét các property mang `@Cfg` trong `EMConfig` và nhận mỗi cái thành một cờ dòng lệnh cùng tên:
`--statefulAuthzResetEndpoint "POST http://localhost:8080/reset"`. Chuỗi trong `@Cfg` là phần mô tả của cờ. Ta thêm 3
property: `statefulAuthzResetEndpoint`, `statefulAuthzTransition`, `statefulAuthzTwoCredentialJudgment`
(`EMConfig:3044–3077`).

---

## 22. Toán tử

| Kotlin | Nghĩa | Java |
|---|---|---|
| `a == b` | `a.equals(b)`, an toàn với null | `Objects.equals(a, b)` |
| `a === b` | cùng đối tượng | `a == b` |
| `a != b` | `!a.equals(b)` | |
| `x in c` / `x !in c` | `c.contains(x)` | |
| `a..b`, `until` | range | |
| `a to b` | `Pair(a, b)` | |
| `a ?: b` | Elvis | |
| `a!!` | khẳng định không null | |
| `list1 + list2` | nối | |
| `c[i]`, `m[k]` | `get` | `c.get(i)`, `m.get(k)` |
| `i++` | như Java | |
| `&&`, `\|\|`, `!` | như Java | |

**Quan trọng với chuỗi:** `==` so nội dung.

```kotlin
if (v == name) keys.add(kv[0])                         // B:1403
if (followUp.getName() != source.getName() || ...)     // O:590
```

Java phải viết `v.equals(name)`, `!followUp.getName().equals(source.getName())`.

---

## 23. Kotlin gọi Java, Java gọi Kotlin

### 23.1 Kotlin gọi Java

| Java | Viết trong Kotlin | Chỗ |
|---|---|---|
| `new ObjectMapper()` | `ObjectMapper()` | `B:1392` |
| `r.getStatus()` | `r.status` | `B:580` |
| `e.getMessage()` | `e.message` | `B:582` |
| `node.isObject()` | `node.isObject` | `B:1393` |
| `v.isTextual()` | `v.isTextual` | `B:1394` |
| `v.asText()` | `v.asText()`; tên không theo dạng `getX`/`isX` nên giữ nguyên | `B:1394` |
| `RestSecurityBuilder.class` | `RestSecurityBuilder::class.java` | `B:77` |
| `getClass()` | `javaClass` | `Lazy.kt` |
| `Iterator<Map.Entry<K,V>>` | `forEach { (k, v) -> }` | `B:1394` |

Kotlin đổi `getX()` thành property `x`, `isX()` thành `isX`, `setX(v)` thành `x = v`.

Thư viện chuẩn Kotlin thêm hàm vào class Java có sẵn (extension function): `stream.bufferedReader().readLines()` (`B:102`)
gọi trên `java.io.InputStream`, nhưng `bufferedReader()` và `readLines()` là hàm của Kotlin. Mã ta không tự định nghĩa
extension function nào.

**Platform type.** Kotlin không biết hàm Java có trả `null` hay không. Kết quả mang kiểu "platform" (`InputStream!` trong
thông báo lỗi), dùng được như không null, và ném `NullPointerException` nếu thực tế là null. Phải tự kiểm:

```kotlin
val stream = RestSecurityBuilder::class.java.getResourceAsStream(MODEL_RESOURCE)   // B:96
if (stream == null) {                                                             // B:97
    log.warn("Stateful-authorization model $MODEL_RESOURCE is missing from the classpath: ...")
    return emptyMap()
}
```

`getResourceAsStream` trả `null` khi không thấy file trong classpath.

### 23.2 Java gọi Kotlin

| Kotlin | Java thấy | Bằng chứng |
|---|---|---|
| `val key: String get()` | `getKey()` | `javap` §12.3 |
| `var x ... private set` | chỉ `getX()` | `javap` §12.4 |
| `companion object { fun f() }` | `Foo.Companion.f()` | `javap` §14.1 |
| tham số mặc định | phải truyền đủ; thêm `f$default` | `javap` §6.3 |
| `data class` | constructor, getter, `componentN`, `copy`, `equals`, `hashCode`, `toString` | `javap` §1.1 |
| `List<T>` | `java.util.List<T>` | `javap` §1.1 |
| `by lazy` | field `x$delegate` kiểu `kotlin.Lazy`, hàm `getX()` | `javap` §12.6 |

---

## 24. Đọc trọn một hàm: `handleStatefulAuthorization`

`O:552–625`, oracle 970. `analyzeSecurityProperties` (`O:99–117`) gọi nó ở `O:116`, sau 12 lời gọi oracle bảo mật
khác. Chỉ làm việc khi
cờ `statefulTripleUnderEvaluation` đang bật, tức trong lúc builder chấm một bộ ba nó vừa dựng (`B:967–972`).

Đầu vào chạy tay: bộ ba Tier-1 trong log **(log)**:

```
Assembled a stateful-authorization (MR-A1) triple on PUT:/reports/{id} (victim 'alice', operator 'superadmin', transition PUT:/users/{username}/role, statuses 200/200/200)
```

`actions`, lấy từ test sinh ra `infra/em-results/p2f-full-20261015/tests/t1-vuln-seed1-r0/EvoMaster_faults_Test.py`,
`test_0_put_on_report_stillAllowedAfterPermissionRevoked`. Action 0–1 là lát cắt của nạn nhân lấy từ archive; action 2
là transition; action 3 là follow-up:

| Chỉ số | Action | `auth` | Status (assert trong test) |
|---|---|---|---|
| 0 | `POST:/reports` | alice | 201 |
| 1 | `PUT:/reports/{id}` | alice | 200 |
| 2 | `PUT:/users/{username}/role`, thân `{"role":"VIEWER"}` | superadmin | 200 |
| 3 | `PUT:/reports/{id}` | alice | 200 |

Giả sử thêm: category 970 đang bật; `statefulAuthzTransition` rỗng; `POST /reports` và `PUT /reports/{id}` có
`transitionScore ≤ 0`.

| Dòng | Mã | Giá trị |
|---|---|---|
| 558 | `if (!config.isEnabledFaultCategory(...)) return` | bật, đi tiếp |
| 561 | `if (!restSecurityBuilder.statefulTripleUnderEvaluation) return` | `true`, đi tiếp |
| 565 | `val actions = individual.seeMainExecutableActions()` | 4 action ở bảng trên |
| 567–573 | định nghĩa `statusOf`, `isAllowed` | |
| 575 | `val twoCredentialJudgment = config.statefulAuthzTwoCredentialJudgment` | giả sử `false` |
| 577 | `for (srcIndex in actions.indices)` | `srcIndex = 0` |
| 578 | `val source = actions[0]` | `POST:/reports`, alice |
| 579–585 | bốn điều kiện `continue` | 201 là 2xx, `POST` có trong list, không là transition: không `continue` |
| 587 | `for (followUpIndex in 1 until 4)` | 1, 2, 3 |
| 590 | `followUp.getName() != source.getName()` | cả ba action sau đều khác tên `POST:/reports`: `continue` cả ba lần |
| 577 | vòng ngoài tiếp | `srcIndex = 1` |
| 578 | `val source = actions[1]` | `PUT:/reports/{id}`, alice |
| 579 | `source.auth is NoAuth` | `false` |
| 580 | `!isAllowed(source)` | `statusOf = 200`, `isAllowed = true`, nên `false` |
| 581 | `source.verb !in listOf(PUT, PATCH, POST, DELETE)` | `PUT` có trong list, nên `false` |
| 582–583 | `!twoCredentialJudgment && looksLike…(source)` | `true && false`, nên `false` |
| 579–585 | `if (false \|\| false \|\| false \|\| false) continue` | không `continue` |
| 587 | `for (followUpIndex in 2 until 4)` | `followUpIndex = 2` |
| 588 | `val followUp = actions[2]` | `PUT:/users/{username}/role` |
| 590 | `followUp.getName() != source.getName()` | tên khác, `continue` |
| 587 | vòng tiếp | `followUpIndex = 3` |
| 588 | `val followUp = actions[3]` | `PUT:/reports/{id}`, alice |
| 590 | tên khác? auth khác? | cùng tên, cùng alice; không `continue` |
| 593 | `!isAllowed(followUp)` | 200, không `continue` |
| 597 | `(2 until 3).any { ... }` | xét `it = 2` |
| 598 | `val t = actions[2]` | `PUT:/users/{username}/role`, superadmin |
| 599 | `t.auth.isDifferentFrom(source.auth)` | superadmin khác alice: `true` |
| 600 | `isAllowed(t)` | 200: `true` |
| 601–602 | `twoCredentialJudgment \|\| looksLike…(t)` | `false \|\| (8,5036 > 0)`: `true` |
| 597 | `hasTransition` | `true` |
| 604 | `if (!hasTransition) continue` | không `continue` |
| 608–611 | `actionResults.filterIsInstance<RestCallResult>().find { ... } ?: continue` | kết quả của action 3 |
| 613–617 | `val scenarioId = idMapper.handleLocalTarget(idMapper.getFaultDescriptiveId(970, "PUT:/reports/{id}"))` | id mục tiêu cho lỗi 970 trên endpoint này |
| 618 | `fv.updateTarget(scenarioId, 1.0, followUpIndex)` | đánh dấu mục tiêu đã đạt, ở action 3 |
| 619–621 | `result.addFault(DetectedFault(970, "PUT:/reports/{id}", null))` | gắn lỗi 970 vào kết quả action 3 |
| 622 | `return` | thoát hàm: một test báo tối đa một lỗi 970 |

Trong file test, dòng comment `# Fault970. Stateful Authorization: ...` đứng ngay trên lời gọi `res_3`, đúng action 3. Cả
bốn lời gọi của alice dùng `token_alice` lấy một lần ở đầu test, trước transition.

Log ngay sau đó **(log)**:

```
Constructed a stateful-authorization (MR-A1) test revealing privilege persistence after a role downgrade on PUT:/reports/{id} (victim 'alice')
```

dòng `B:1047–1050` in ra khi `ExperimentalFaultCategory.SECURITY_STATEFUL_AUTHORIZATION in DetectedFaultUtils.getDetectedFaultCategories(ei)`
(`B:1046`) đúng.

Bản Java của vòng lặp chính, để so:

```java
for (int srcIndex = 0; srcIndex < actions.size(); srcIndex++) {
    RestCallAction source = actions.get(srcIndex);
    if (source.getAuth() instanceof NoAuth || !isAllowed(source)
            || !List.of(HttpVerb.PUT, HttpVerb.PATCH, HttpVerb.POST, HttpVerb.DELETE).contains(source.getVerb())
            || (!twoCredentialJudgment && RestSecurityBuilder.Companion.looksLikePermissionReducingTransition(source, transition))) {
        continue;
    }
    for (int followUpIndex = srcIndex + 1; followUpIndex < actions.size(); followUpIndex++) {
        RestCallAction followUp = actions.get(followUpIndex);
        if (!followUp.getName().equals(source.getName()) || followUp.getAuth().isDifferentFrom(source.getAuth())) continue;
        if (!isAllowed(followUp)) continue;
        final int s = srcIndex, f = followUpIndex;
        boolean hasTransition = IntStream.range(s + 1, f).anyMatch(i -> {
            RestCallAction t = actions.get(i);
            return t.getAuth().isDifferentFrom(source.getAuth()) && isAllowed(t)
                && (twoCredentialJudgment || RestSecurityBuilder.Companion.looksLikePermissionReducingTransition(t, transition));
        });
        if (!hasTransition) continue;
        RestCallResult result = actionResults.stream().filter(RestCallResult.class::isInstance).map(RestCallResult.class::cast)
            .filter(r -> r.getSourceLocalId().equals(followUp.getLocalId())).findFirst().orElse(null);
        if (result == null) continue;
        ...
        return;
    }
}
```

---

## 25. Bẫy cho người viết Java

| Bẫy | Ví dụ | Đúng là |
|---|---|---|
| `==` trên chuỗi | `v == name` (`B:1403`) | so nội dung; Kotlin không cần `.equals` |
| `split` giữ chuỗi rỗng cuối | `"/reports/{id}"` ra `[, reports, id, ]` (§5.3) | lọc `isNotEmpty()` |
| `return` trong lambda | `?.let { return ... }` (`B:242–244`) | thoát hàm bao ngoài; `return@ten` để thoát lambda |
| `val` của list đổi được | `val privilegeReducedInPhase = mutableSetOf()` | `val` chỉ cấm gán lại, vẫn `add`/`clear` được |
| Platform type từ Java | `getResourceAsStream` (`B:96`) | tự kiểm null |
| `!!` | `followUpCode!!` (`B:1021`) | ném NPE nếu null |
| `it` lồng nhau | `it.all { c -> ... }` (`B:125`) | đặt tên lambda trong |
| class mặc định `final` | `class SchemaField` | muốn kế thừa phải `open` |
| `if` biểu thức thiếu `else` | `val x = if (a) 1` | lỗi biên dịch |
| `List` không có `add` | `val l = listOf(1); l.add(2)` | dùng `mutableListOf` |
| `as` khác `as?` | `as RestCallResult?` (`O:568`) và `as? RestCallResult` (`B:981`) | `as` ném khi sai kiểu; `as?` ra `null` |
| Tham số mặc định từ Java | `tokens(s)` không có trong Java | Java gọi `tokens(s, 4)` |

### Số đếm upstream

Đếm dòng khớp mẫu trong `core/src/main/kotlin` bằng `grep -rE`, ngày 2026-10-21. Một dòng có hai lần xuất hiện vẫn đếm là 1.

| Mẫu | Dòng |
|---|---|
| `?:` | 862 |
| `!!` | 518 |
| `lateinit var` | 282 |
| `companion object` | 230 |
| `when (` | 195 |
| ` as? ` | 150 |
| `.let {` | 123 |
| `apply {` | 100 |
| `object ` đầu dòng | 76 |
| `abstract class` | 74 |
| `data class` | 71 |
| `.also {` | 56 |
| `open class` | 33 |
| `@JvmStatic` | 9 |
