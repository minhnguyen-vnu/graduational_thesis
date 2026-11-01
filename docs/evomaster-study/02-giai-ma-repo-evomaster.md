# Giải mã repo EvoMaster

Repo: `/Users/minhnguyen/IdeaProjects/EvoMaster`, nhánh `stateful-authz-oracle`, dựng trên tag `v6.1.1`. Đường dẫn trong
file này tính từ gốc repo. Ví dụ chạy thật lấy từ lượt Tier-1 `t1-vuln-seed1-r0` của batch
`infra/em-results/p2f-full-20261015/`, jar P2f:

- log: `infra/em-results/p2f-full-20261015/logs/t1-vuln-seed1-r0.log`;
- test sinh ra: `infra/em-results/p2f-full-20261015/tests/t1-vuln-seed1-r0/`.

Cú pháp Kotlin: `01-kotlin-cho-nguoi-viet-java.md`.

## Mục lục

1. [EvoMaster làm gì](#1-evomaster-làm-gì)
2. [Hai chế độ: black-box và white-box](#2-hai-chế-độ-black-box-và-white-box)
3. [Bản đồ repo](#3-bản-đồ-repo)
4. [Cài đặt](#4-cài-đặt)
5. [Chạy một lượt](#5-chạy-một-lượt)
6. [Một lượt chạy từ `main` tới file test](#6-một-lượt-chạy-từ-main-tới-file-test)
7. [Các component trong `core`](#7-các-component-trong-core)
8. [Mã của ta nằm ở đâu](#8-mã-của-ta-nằm-ở-đâu)
9. [Thứ tự đọc mã](#9-thứ-tự-đọc-mã)

---

## 1. EvoMaster làm gì

EvoMaster sinh test cho API web: REST, GraphQL, RPC, và giao diện web.

| | Ví dụ Tier-1 |
|---|---|
| Vào: schema của API | OpenAPI tại `http://localhost:8080/v3/api-docs`, 9 endpoint |
| Vào: API đang chạy | container `reports-api`, cổng 8080 |
| Vào: tài khoản đăng nhập | `infra/em-config/reports-auth.yaml`: alice, superadmin, bob |
| Vào: thời gian | `--maxTime 150s` |
| Ra: file test | 3 file Python, tổng 54 test |
| Ra: lỗi tìm thấy | `Potential faults: 2`, trong đó có một lỗi 970 |

EvoMaster gửi hàng trăm request, giữ lại những test chạm được mục tiêu mới (một mã trạng thái mới trên một endpoint, một
lỗi), rồi ghi các test đó ra file. Lượt Tier-1 chấm 150 test trong pha tìm kiếm (log dòng 576).

## 2. Hai chế độ: black-box và white-box

```
BLACK-BOX (luận văn dùng chế độ này)

  ┌──────────────────────┐        HTTP         ┌─────────────────────┐
  │ evomaster.jar (core) │ ──────────────────► │ API đang chạy       │
  │  đọc schema OpenAPI  │ ◄────────────────── │ (Java, Python, Go…) │
  └──────────────────────┘   mã trạng thái,    └─────────────────────┘
                             thân phản hồi

WHITE-BOX (chỉ cho ứng dụng chạy trên JVM)

  ┌──────────────────────┐  HTTP, cổng 40100   ┌─────────────────────────────────────────┐
  │ evomaster.jar (core) │ ──────────────────► │ driver (lớp Java người dùng tự viết,    │
  │                      │                     │ kế thừa EmbeddedSutController)          │
  │                      │                     │   ├─ khởi động / reset ứng dụng         │
  │                      │                     │   └─ instrumentation: đo nhánh, SQL     │
  │                      │        HTTP         │ ┌─────────────────────────────────────┐ │
  │                      │ ──────────────────► │ │ ứng dụng (Spring Boot…) cùng JVM    │ │
  └──────────────────────┘                     │ └─────────────────────────────────────┘ │
                                               └─────────────────────────────────────────┘
```

| | Black-box | White-box |
|---|---|---|
| Cần gì | schema + URL API | driver viết bằng Java, dùng thư viện `client-java` |
| Biết gì về ứng dụng | request và response | thêm: nhánh mã đã chạy, câu SQL đã chạy |
| Thuật toán mặc định | `SMARTS` (`core/src/main/kotlin/org/evomaster/core/EMConfig.kt:76`) | `MIO` (`EMConfig.kt:78`) |
| Mặc định từ v6.0.0 | có: `var blackBox = true` (`EMConfig.kt:1196`) | |
| Luận văn | dùng | không dùng |

Cổng driver mặc định 40100: `ControllerConstants.DEFAULT_CONTROLLER_PORT`
(`client-java/controller-api/src/main/java/org/evomaster/client/java/controller/api/ControllerConstants.java:5`).

Vì sao `core` viết bằng Kotlin còn `client-java` viết bằng Java, theo `docs/for_developers.md:20–24`:

> The core process of _EvoMaster_ is built in _Kotlin_, as we strongly prefer it over _Java_.
> However, the client libraries for JDK SUTs (e.g., not just _Java_, but also all other languages that do
> compile to JDK bytecode) are written in _Java_ instead of _Kotlin_.
> The main reason is that, being libraries, we do not want to also have to ship the _Kotlin_ runtime
> libraries with them.

Diễn giải: `client-java` được nhúng vào ứng dụng của người dùng, nên viết bằng Java để ứng dụng đó không phải kéo thêm thư
viện chạy của Kotlin.

---

## 3. Bản đồ repo

### 3.1 Thư mục gốc

Số file đếm ngày 2026-10-21, chỉ tính `src`.

| Thư mục | Là gì | Ngôn ngữ, cỡ | Luận văn |
|---|---|---|---|
| `pom.xml` | pom gốc Maven; liệt kê module ở `pom.xml:40–45` | | đọc |
| `core-parent/` | chỉ có `pom.xml`: cấu hình Maven chung cho `core`, `core-extra`, `core-tests` | | không |
| `core/` | **bộ sinh test**. Ra `core/target/evomaster.jar` | Kotlin: 688 file mã chính, 366 file test | **sửa ở đây** |
| `core-extra/dbconstraint/` | mô hình ràng buộc của bảng SQL (`UniqueConstraint`, `LikeConstraint`…), đọc bằng thư viện `jsqlparser` | Java | không (white-box, SQL) |
| `core-extra/solver/` | gọi bộ giải SMT Z3 chạy trong Docker (`Z3DockerExecutor.java`) để sinh dữ liệu SQL thoả ràng buộc | Java | không |
| `core-tests/` | test của chính EvoMaster: `e2e-tests/` (ứng dụng nhân tạo Spring, Dropwizard, Micronaut, Python), `integration-tests/`, `jdk-8/` | Kotlin 1.202, Java 978 file | không |
| `client-java/` | thư viện cho chế độ white-box (§3.3) | Java: 531 file mã chính, 362 file test | không |
| `test-utils/` | file tiện ích EvoMaster chép kèm test sinh ra: `test-utils-py/src/main/resources/em_test_utils.py`, `test-utils-js/`, `test-utils-java.txt` | | gián tiếp |
| `docs/` | tài liệu người dùng: `blackbox.md`, `options.md`, `auth.md`, `for_developers.md`… | Markdown | tra cứu |
| `pypi-distribution/` | gói `pip install evomaster` | | baseline `infra/em-venv/bin/evomaster` |
| `outdated/` | client cũ cho .NET và JavaScript, đã ngừng | | không |
| `scripts/`, `makeExecutable.sh`, `Dockerfile`, `version.py`, `release_notes.md` | đóng gói, phát hành | | không |
| `evomaster-*.jar` ở gốc | **của ta**: bản sao jar từng mốc (P2f, P2e, AF2…). `.gitignore:9` bỏ qua `*.jar` | | chạy batch |

`em_test_utils.py` trong thư mục test sinh ra trùng từng byte với file trong `test-utils-py` (`cmp`, 2026-10-21).

### 3.2 `core` dùng những module nào

`core/pom.xml` khai báo phụ thuộc:

```
core
 ├─ client-java/controller-api           DTO (lớp dữ liệu) trao đổi giữa core và driver
 ├─ client-java/instrumentation-shared   kiểu dữ liệu chung với phần đo mã
 ├─ client-java/controller               lớp driver, tiện ích auth và SQL
 ├─ client-java/ci-utils
 ├─ core-extra/dbconstraint              ràng buộc SQL
 └─ test-utils/test-utils-{java,js,py}   file tiện ích chép vào test sinh ra
```

Vì vậy `mvn -pl core -am` (§4.2) dựng cả các module này trước `core`.

### 3.3 `client-java`: 12 module con

| Module | File Java | Làm gì |
|---|---|---|
| `controller` | 400 | lớp cha cho driver: `EmbeddedSutController.java`, `ExternalSutController.java`, `SutHandler.java`; server REST mà core gọi tới |
| `controller-api` | 68 | DTO và hằng số chung (`ControllerConstants`) |
| `instrumentation` | 316 | Java agent sửa bytecode của ứng dụng lúc nạp class (`InstrumentingAgent.java`, `Instrumentator.java`) để đo nhánh, so sánh chuỗi, câu SQL |
| `instrumentation-shared` | 17 | kiểu dùng chung giữa agent và core |
| `sql`, `sql-dto` | 130, 21 | đo khoảng cách heuristic trên câu SQL, xử lý cơ sở dữ liệu |
| `distance-heuristics` | 5 | hàm khoảng cách nhánh |
| `client-util`, `ci-utils`, `dependencies`, `test-utils-java`, `test-old-libraries` | 1, 2, 0, 3, 7 | tiện ích, đóng gói, test tương thích |

Đếm gồm cả file test trong từng module. Chế độ black-box không nạp module nào trong số này vào ứng dụng bị test.

### 3.4 Bên trong `core/src/main/kotlin/org/evomaster/core/`

| Package | File `.kt` | Làm gì |
|---|---|---|
| `Main.kt` | 1 | điểm vào, điều phối các pha (§6) |
| `EMConfig.kt` | 1 | mọi tuỳ chọn dòng lệnh: 323 chỗ `@Cfg` |
| `BaseModule.kt` | 1 | đăng ký dịch vụ chung với Guice |
| `problem/` | 261 | mỗi loại API một package: `rest/` 109, `graphql/` 33, `rpc/` 12, `webfrontend/` 14; `httpws/` 14 (auth, HTTP chung); `security/` 6; `enterprise/` 19 |
| `search/` | 256 | lõi tìm kiếm, không biết gì về HTTP: `gene/` 110, `impact/` 47, `service/` 43 (Archive, Sampler, FitnessFunction, Minimizer…), `algorithms/` 28, `action/` 9 |
| `output/` | 68 | viết test ra file: `TestSuiteWriter`, writer theo ngôn ngữ |
| `sql/`, `mongo/`, `redis/` | 23, 5, 10 | xử lý cơ sở dữ liệu (white-box) |
| `remote/` | 7 | HTTP client gọi driver; `HttpClientFactory` |
| `solver/` | 5 | sinh ràng buộc SMT-LIB, gọi `core-extra/solver` |
| `llm/` | 11 | tuỳ chọn dùng LLM |
| `seeding/`, `taint/`, `parser/`, `config/`, `logging/`, `utils/` | | phụ trợ |

`problem/rest/` chia tiếp:

| Package | Làm gì | Lớp chính |
|---|---|---|
| `data/` | mô hình test REST | `RestIndividual`, `RestCallAction`, `RestCallResult`, `HttpVerb` |
| `param/` | tham số của một lời gọi | `PathParam`, `QueryParam`, `BodyParam`, `HeaderParam` |
| `schema/`, `builder/` | đọc OpenAPI, dựng action từ schema | `OpenApiAccess`, `RestActionBuilderV3` |
| `service/sampler/` | tạo test mới | `RestSampler`, `AbstractRestSampler` |
| `service/fitness/` | chạy test, chấm điểm | `BlackBoxRestFitness`, `AbstractRestFitness` |
| `service/module/` | cấu hình Guice cho từng chế độ | `BlackBoxRestModule`, `RestBaseModule` |
| `service/` | pha bảo mật | `RestSecurityBuilder` (**ta sửa**) |
| `oracle/` | phán lỗi từ kết quả | `RestSecurityOracle` (**ta sửa**), `HttpSemanticsOracle` |

---

## 4. Cài đặt

### 4.1 Cần gì

| Mục đích | Cần | Trên máy tác giả |
|---|---|---|
| Chạy jar có sẵn | JDK 17 | `/usr/libexec/java_home -v 17` ra `ms-17.0.19` |
| Dựng jar từ mã | thêm Maven 3.9 | Maven 3.9.16 Homebrew; mặc định chạy JDK 26, phải ép JDK 17 |
| Bật target | Docker | 8 container: `reports-api` :8080, `reports-api-fixed` :8081, `vampi-seeded` :5002, `vampi-seeded-fixed` :5003, `pyload-vuln` :8090, `pyload-fixed` :8091, `postgres-db`, `redis-stack` |
| Chạy test Python sinh ra | Python, `requests`, `timeout_decorator` | `infra/em-results/tier1-clean-remeasure/.replay-venv/` |

Phiên bản: `pom.xml:217–218` ghi `java.version` 17, `kotlin.version` 2.2.20.

`--add-opens`: Java 17 chặn truy cập phản chiếu vào `java.net` và `java.util`. `Main.main` kiểm ở
`JdkIssue.checkAddOpens()` (`Main.kt:82`). Chạy bằng `java -jar` thì không cần làm gì: theo thông báo trong
`JdkIssue.kt`, cờ đã ghi sẵn trong manifest của jar. Chạy `Main` từ IntelliJ thì phải thêm
`--add-opens java.base/java.net=ALL-UNNAMED --add-opens java.base/java.util=ALL-UNNAMED` vào VM options.

### 4.2 Dựng jar

Lệnh của skill `evomaster-build`:

```bash
JAVA_HOME=$(/usr/libexec/java_home -v 17) mvn -f /Users/minhnguyen/IdeaProjects/EvoMaster/pom.xml \
  -pl core -am package -Dmaven.test.skip=true
```

| Phần | Nghĩa |
|---|---|
| `JAVA_HOME=$(… -v 17)` | ép Maven chạy JDK 17 |
| `-pl core` | chỉ dựng module `core` |
| `-am` | "also make": dựng thêm các module `core` phụ thuộc (§3.2) |
| `package` | biên dịch và đóng gói jar |
| `-Dmaven.test.skip=true` | không biên dịch, không chạy test |

Kết quả: `core/target/evomaster.jar`, 114.961.432 byte (bản dựng 2026-10-14 23:57), khoảng 2,5 phút. Jar là "fat jar": plugin
`maven-shade-plugin` (`core/pom.xml:424–442`) gói mọi thư viện vào một file và ghi `Main-Class: org.evomaster.core.Main`.

Jar dùng cho số liệu được chép sang `evomaster-<nhãn>-<sha8>.jar` ở gốc repo, kèm `.sha256`. Nhận diện jar bằng tuỳ chọn
biên dịch trong `EMConfig`, theo skill `evomaster-build`:

```bash
unzip -p <jar> 'org/evomaster/core/EMConfig*.class' | strings | grep -o "statefulAuthz[A-Za-z]*" | sort -u
```

---

## 5. Chạy một lượt

### 5.1 Lệnh

Lệnh một lượt Tier-1 của skill `em-batch`:

```bash
curl -s -X POST http://localhost:8080/reset >/dev/null
JAVA_HOME=$(/usr/libexec/java_home -v 17) java -jar /Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-P2f-64ee8ffc.jar \
  --blackBox true --bbSwaggerUrl http://localhost:8080/v3/api-docs --bbTargetUrl http://localhost:8080 \
  --configPath infra/em-config/reports-auth.yaml \
  --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
  --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed 1 \
  --outputFolder infra/em-results/<thu-muc-moi>
```

| Cờ | Giá trị | Nghĩa | Mặc định |
|---|---|---|---|
| `--blackBox` | `true` | chế độ black-box | `true` |
| `--bbSwaggerUrl` | `…/v3/api-docs` | chỗ đọc schema OpenAPI | |
| `--bbTargetUrl` | `http://localhost:8080` | gốc URL gửi request | lấy từ schema |
| `--configPath` | file YAML | tài khoản đăng nhập (§5.2) | |
| `--useExperimentalOracles` | `true` | bật oracle thử nghiệm; 970 là thử nghiệm | `false` (`EMConfig.kt:3042`) |
| `--extraPhaseBudgetPercentage` | `0.6` | ngân sách mỗi pha sau tìm kiếm = 0,6 × `maxTime` | `0.10` (`EMConfig.kt:2756`) |
| `--outputFormat` | `PYTHON_UNITTEST` | ngôn ngữ test sinh ra | theo ngôn ngữ ứng dụng |
| `--ratePerMinute` | `120` | tối đa 120 request mỗi phút | `0`, không giới hạn |
| `--maxTime` | `150s` | thời gian **pha tìm kiếm** | `60s` (`EMConfig.kt:1227`) |
| `--seed` | `1` | hạt giống ngẫu nhiên | |
| `--outputFolder` | thư mục | nơi ghi test | |

`--security` mặc định `true` (`EMConfig.kt:3010`), `--minimize` mặc định `true` (`EMConfig.kt:2745`); lệnh không ghi lại.

Mọi cờ khác: `docs/options.md`. Tên cờ là tên property trong `EMConfig`; 3 cờ của ta ở `EMConfig.kt:3044–3077`.

### 5.2 File auth

`infra/em-config/reports-auth.yaml` (rút gọn):

```yaml
auth:
  - name: alice
    loginEndpointAuth:
      payloadUserPwd: { username: alice, password: "alicepass", usernameField: username, passwordField: password }
  - name: superadmin   # ...
  - name: bob          # ...
authTemplate:
  loginEndpointAuth:
    endpoint: /auth/login
    verb: POST
    contentType: application/json
    token:
      extractFrom: body
      extractSelector: /token
      sendIn: header
      sendName: Authorization
      sendTemplate: "Bearer {token}"
```

Nghĩa: mỗi test, với mỗi tài khoản nó dùng, EvoMaster gửi `POST /auth/login` thân `{"username":"alice","password":"alicepass"}`,
lấy `token` trong thân phản hồi (JSON Pointer `/token`), rồi gửi kèm `Authorization: Bearer <token>` trên mọi lời gọi của
tài khoản đó. Log dòng 11: `Loading configuration file from: …/reports-auth.yaml` (in ở `EMConfig.kt:595`).

### 5.3 Thời gian thật của lượt

`--maxTime` chỉ tính pha tìm kiếm. Các pha sau có ngân sách riêng. Lượt Tier-1:

| Pha | Log | Thời lượng |
|---|---|---|
| SEARCH | dòng 583 `Phase SEARCH lasted: 0h 2m 30s` | 150 s = `maxTime` |
| MINIMIZATION | dòng 596 | 40 s |
| SECURITY | dòng 602–603 `Phase 'SECURITY' has timed out after 90 seconds` | 93 s; 90 = 0,6 × 150 |
| WRITE_OUTPUT | dòng 608 | 0 s |
| Tổng | đầu file test: `Used time: 0h 4m 44s` | 284 s |

### 5.4 Output

`infra/em-results/p2f-full-20261015/tests/t1-vuln-seed1-r0/`:

| File | Nội dung |
|---|---|
| `EvoMaster_faults_Test.py` | 2 test có lỗi; `test_0_put_on_report_stillAllowedAfterPermissionRevoked` là lỗi 970 |
| `EvoMaster_successes_Test.py` | 22 test chỉ có phản hồi 2xx |
| `EvoMaster_others_Test.py` | 30 test còn lại (4xx…) |
| `em_test_utils.py` | hàm phụ, chép từ `test-utils/test-utils-py` |
| `report.json` | báo cáo máy đọc được: mục tiêu đã phủ, lỗi |
| `index.html`, `assets/`, `webreport.*` | báo cáo web |

2 + 22 + 30 = 54, khớp log dòng 605 `Going to save 54 tests`.

Chạy lại test: `python -m pytest EvoMaster_faults_Test.py` với ứng dụng đang chạy ở 8080 và đã reset (template
`infra/em-results/tier1-clean-remeasure/replay_t1.sh`).

---

## 6. Một lượt chạy từ `main` tới file test

### 6.1 Sơ đồ

```
Main.main (Main.kt:76)
 ├─ EMConfig.validateOptions(args)                        Main.kt:94    kiểm cờ
 └─ initAndRun(args)                                      Main.kt:138, :231
     ├─ init(args)                                        Main.kt:529
     │   ├─ BaseModule(args)                              Main.kt:533   đọc cờ + file YAML vào EMConfig
     │   ├─ chọn module Guice: BlackBoxRestModule         Main.kt:581
     │   └─ LifecycleInjector...createInjector()          Main.kt:626–629
     │        └─ tạo các dịch vụ; RestSampler.initialize() đọc schema → 9 endpoint
     └─ runAndPostProcess(injector)                       Main.kt:247
         ├─ run(injector, …)                              Main.kt:257, :883
         │   ├─ epc.markStartingSearch()                  Main.kt:887   "Starting phase SEARCH"
         │   ├─ chọn thuật toán: SMARTS                   Main.kt:895, EMConfig.kt:680–681
         │   └─ imp.search { … }                          Main.kt:906
         │        └─ while (time.shouldContinueSearch()) searchOnce()      SearchAlgorithm.kt:78–80
         │             └─ sample → chấm → archive.addIfNeeded
         ├─ phaseMinimizer                                Main.kt:269, :425
         ├─ phaseSecurity                                 Main.kt:273, :463
         │   └─ RestSecurityBuilder.applySecurityPhase()  Main.kt:479
         │        ├─ expandWithForbidden()
         │        ├─ addForStatefulAccessControl()        ← của ta, RestSecurityBuilder.kt:361–363
         │        ├─ addForAccessControl()
         │        ├─ addForInjections()
         │        └─ addForInfoLeakage()
         ├─ phaseHttpOracle                               Main.kt:274
         ├─ phaseFlaky                                    Main.kt:275
         └─ writeTests → TestSuiteWriter                  Main.kt:281, :1002
```

### 6.2 Từng bước, với log thật

| Bước | Mã | Log Tier-1 |
|---|---|---|
| 1. In logo, phiên bản | `Main.kt:80–81` | dòng 10 `EvoMaster version: 6.1.1` |
| 2. Đọc cấu hình | `BaseModule(args)`, `EMConfig.kt:595` | dòng 11 `Loading configuration file from: …` |
| 3. Không ghi `--problemType` thì mặc định REST | | dòng 12 `WARNING: You are doing Black-Box testing, but you did not specify the 'problemType'…` |
| 4. Tạo injector, đọc schema | `Main.kt:626`; `AbstractRestSampler.kt:337–346` | dòng 14 `Initializing...`, dòng 15 `There are 9 usable RESTful API endpoints…` |
| 5. Bắt đầu tìm kiếm | `Main.kt:887`; `ExecutionPhaseController.kt:164` | dòng 17 `Starting phase SEARCH` |
| 6. Vòng lặp SMARTS | `SearchAlgorithm.kt:78`, `SmartsAlgorithm.searchOnce` | `Covered targets` tăng từ 0 lên 104 |
| 7. Hết giờ tìm kiếm | | dòng 576 `Evaluated tests: 150`, dòng 583 `Phase SEARCH lasted: 0h 2m 30s` |
| 8. Thu gọn test | `Minimizer.applyPhase` | dòng 584–596 `Minimization progress: 0/7` tới `7/7` |
| 9. Pha bảo mật | `RestSecurityBuilder.applySecurityPhase` | dòng 597–603, gồm 4 dòng của oracle 970 |
| 10. Ghi test | `TestSuiteWriter` | dòng 605 `Going to save 54 tests…`, dòng 606 `Potential faults: 2` |

---

## 7. Các component trong `core`

### 7.1 `EMConfig`: mọi tuỳ chọn

`core/src/main/kotlin/org/evomaster/core/EMConfig.kt`, 323 property mang `@Cfg`. Mỗi property là một cờ dòng lệnh cùng
tên. Mọi dịch vụ nhận `EMConfig` qua `@Inject` và đọc cờ từ đó, ví dụ `config.statefulAuthzTransition`
(`RestSecurityOracle.kt:583`).

### 7.2 Guice: ai tạo ai

EvoMaster không dùng `new` cho các dịch vụ. Guice (thêm Governator để gọi `@PostConstruct`) tạo một bản duy nhất của mỗi
dịch vụ và gán vào các field `@Inject`. Diễn giải `docs/for_developers.md:98–108`: mọi dịch vụ là singleton, nằm trong
package tên `*.service`, đăng ký tay; mỗi loại bài toán đăng ký một bộ dịch vụ khác nhau.

Hai module Guice được ghép lúc chạy (`Main.kt:627`, `.withModules(base, problemModule)`):

| Module | Đăng ký | Ví dụ |
|---|---|---|
| `BaseModule` (`BaseModule.kt:27`) | dịch vụ chung | `ExecutionPhaseController`, `Randomness`, `IdMapper`, `Statistics`, `SearchTimeController` |
| `RestBaseModule` (`problem/rest/service/module/RestBaseModule.kt`) | dịch vụ REST chung | `TestSuiteWriter` :29, `Minimizer<RestIndividual>` :38, `Archive<RestIndividual>` :52, `RestSecurityOracle` :72, `RestSecurityBuilder` :75 |
| `BlackBoxRestModule` (kế thừa `RestBaseModule`) | chọn cài đặt cho black-box | bảng dưới |

`BlackBoxRestModule.configure()` (`problem/rest/service/module/BlackBoxRestModule.kt`):

| Khi ai đó `@Inject` kiểu | Guice đưa |
|---|---|
| `Sampler<RestIndividual>` | `RestSampler` |
| `FitnessFunction<RestIndividual>` | `BlackBoxRestFitness` |
| `Mutator<RestIndividual>` | `StandardMutator<RestIndividual>` |
| `RemoteController` | `RemoteControllerImplementation`, chỉ khi `bbExperiments` |

Ví dụ: `RestSecurityBuilder` khai báo `@Inject private lateinit var fitness: FitnessFunction<RestIndividual>`
(`RestSecurityBuilder.kt:293–294`). Ở black-box, Guice gán vào đó đối tượng `BlackBoxRestFitness`. Mã ta gọi
`fitness.computeWholeAchievedCoverageForPostProcessing(base)` (`RestSecurityBuilder.kt:969`) là đang gửi HTTP thật qua
`BlackBoxRestFitness`.

Java Spring tương đương: `@Configuration` với các `@Bean`, nhưng phải liệt kê tay, không quét package.

### 7.3 Mô hình dữ liệu: một test là gì

```
Individual                    một test                                 search/Individual.kt:40
 └─ RestIndividual            test REST                                problem/rest/data/RestIndividual.kt:33
     └─ Action (nhiều)        một lời gọi                              search/action/Action.kt:15
         └─ RestCallAction    verb + path + tham số + tài khoản         problem/rest/data/RestCallAction.kt:26
             ├─ auth          HttpWsAuthenticationInfo: alice / NoAuth
             └─ Param (nhiều) PathParam, QueryParam, BodyParam, HeaderParam  problem/api/param/Param.kt:7
                 └─ Gene      cây giá trị                              search/gene/Gene.kt:53
                     ├─ StringGene, IntegerGene, BooleanGene, EnumGene
                     ├─ ObjectGene (trường con), ArrayGene (phần tử con)
                     └─ OptionalGene (có/không gửi), ChoiceGene (một trong nhiều)

EvaluatedIndividual = Individual + kết quả từng action + FitnessValue    search/EvaluatedIndividual.kt:36
FitnessValue        = điểm trên từng mục tiêu                            search/FitnessValue.kt:28
Solution            = các test giữ lại để ghi ra file                    search/Solution.kt:14
```

Ví dụ: test 970 của lượt Tier-1 là một `RestIndividual` 4 action:

| Action | `verb`, `path` | `auth` | Param và gene |
|---|---|---|---|
| 0 | `POST /reports` | alice | `BodyParam`: `ObjectGene` { `title`: `StringGene` "Report 1", `classification`: `EnumGene` "PUBLIC" } |
| 1 | `PUT /reports/{id}` | alice | `PathParam id` lấy từ `Location` của action 0; `BodyParam` { "Report 4", "CONFIDENTIAL" } |
| 2 | `PUT /users/{username}/role` | superadmin | `PathParam username` = "alice"; `BodyParam` { `role`: `EnumGene` "VIEWER" } |
| 3 | `PUT /reports/{id}` | alice | như action 1 |

Giá trị lấy từ `EvoMaster_faults_Test.py:57–160`. Tên lớp gene của từng trường là suy ra từ schema (`allowableValues`
của `role` cho ra `EnumGene`), chưa in ra từ jar.

Đột biến (mutation) đổi giá trị gene; đột biến cấu trúc (`StructureMutator`) thêm, bớt action.

### 7.4 Sampler: tạo test mới

`RestSampler` (`problem/rest/service/sampler/RestSampler.kt`), cha là `AbstractRestSampler`.

**Đọc schema.** Ở black-box, `AbstractRestSampler.kt:337` tải OpenAPI từ `bbSwaggerUrl`, rồi `RestActionBuilderV3.addActionsFromSwagger`
(`:346`) dựng một `RestCallAction` mẫu cho mỗi endpoint vào `actionCluster`. Tier-1: 9 mẫu.

**Khởi động.** `customizeAdHocInitialIndividuals()` (`RestSampler.kt:322–346`) tạo trước một test một lời gọi cho mỗi
endpoint, mỗi tài khoản, cộng tài khoản rỗng `HttpWsNoAuth`:

```
createSingleCallOnEachEndpoint(HttpWsNoAuth())   9 test     thêm vào list trước
createSingleCallOnEachEndpoint(alice)            9 test
createSingleCallOnEachEndpoint(superadmin)       9 test
createSingleCallOnEachEndpoint(bob)              9 test     thêm vào list sau cùng
                                                 36 test
```

`smartSample()` lấy từ **cuối** list (`RestSampler.kt:46`, `removeAt(size - 1)`), nên 9 test đầu tiên được chấm là của
bob, tài khoản cuối trong file YAML. Hết 36 test này mới sang cách lấy mẫu khác. Ngân sách nhỏ hơn số endpoint × số tài
khoản thì tài khoản đầu file không bao giờ được thử: CLAUDE.md §2 ghi Grafana (309 endpoint) và Mattermost (623) mất
`victim` theo đúng cách này.

### 7.5 Fitness: chạy một test và chấm điểm

`BlackBoxRestFitness.doCalculateCoverage` (`problem/rest/service/fitness/BlackBoxRestFitness.kt:31`):

| Dòng | Làm gì | Ví dụ test 970 |
|---|---|---|
| 52–54 | đăng nhập mọi tài khoản test dùng, một lần cho cả test (`AuthUtils.getTokens`) | `POST /auth/login` cho alice và superadmin; giữ `token_alice`, `token_superadmin` |
| 67–77 | chạy từng action theo thứ tự (`handleRestCall`), dừng nếu một action hỏng | 4 lời gọi; action 3 vẫn dùng `token_alice` lấy ở dòng 52–54, trước transition |
| 79 | `analyzeResponseData`: biến kết quả thành mục tiêu | |

Vì đăng nhập chỉ một lần đầu test, follow-up dùng lại token cũ: đó là điều kiện để oracle 970 thấy lỗi.

**Mục tiêu (target).** Mỗi kết quả quan sát được thành một mục tiêu có tên, ví dụ:

| Tên mục tiêu | Tạo ở | Ví dụ |
|---|---|---|
| `"$status:$name"` | `AbstractRestFitness.kt:404` | `200:PUT:/reports/{id}` |
| `HTTP_SUCCESS:$name` / `HTTP_FAULT:$name` | `AbstractRestFitness.kt:605–606` | `HTTP_SUCCESS:POST:/reports` |
| mục tiêu lỗi | `idMapper.getFaultDescriptiveId(...)` | lỗi 970 trên `PUT:/reports/{id}` (`RestSecurityOracle.kt:613–618`) |

`IdMapper` đổi tên thành số nguyên. Log `Covered targets: 104` là số mục tiêu đã chạm.

**Oracle bảo mật chỉ chạy trên test của pha bảo mật** (`AbstractRestFitness.kt:1306–1307`):

```kotlin
if(config.security && individual.sampleType == SampleType.SECURITY){
    securityOracle.analyzeSecurityProperties(individual,actionResults,fv)
}
```

Mã ta gắn `SampleType.SECURITY` cho bộ ba trước khi chấm (`RestSecurityBuilder.kt:960`, `base.modifySampleType(SampleType.SECURITY)`).

### 7.6 Archive: giữ test nào

`Archive.addIfNeeded` (`search/service/Archive.kt:397`). Với mỗi mục tiêu test chạm được (điểm > 0):

- mục tiêu chưa có test nào: giữ test này (`:421–425`);
- đã có: so với các test đang giữ cho mục tiêu đó, giữ test tốt hơn hoặc ngắn hơn.

Test không chạm mục tiêu nào mới bị bỏ. `archive.extractSolution()` (`:101`) lấy ra tập test cuối cùng để ghi file.

### 7.7 Thuật toán tìm kiếm

Lớp cha `SearchAlgorithm.search` (`search/service/SearchAlgorithm.kt:72`):

```kotlin
while (time.shouldContinueSearch()) {    // :78, hết maxTime thì dừng
    searchOnce()                         // :80
    ...
}
```

Black-box mặc định `SMARTS` (`search/algorithms/SmartsAlgorithm.kt`):

```kotlin
override fun searchOnce() {
    val individual = sampler.sample(false)
    ff.calculateCoverage(individual, modifiedSpec = null)?.run { archive.addIfNeeded(this) }
}
```

Mỗi vòng: lấy một test mới từ sampler, chạy và chấm, đưa vào archive. Không đột biến test cũ.

White-box mặc định `MIO` (`search/algorithms/MioAlgorithm.kt:22–49`): với một xác suất thì lấy mẫu mới như trên, ngược lại
lấy một test trong archive (`archive.sampleIndividual()`) và đột biến nó (`mutateAndSave`). `--algorithm` chọn được 15
thuật toán khác (`Main.kt:828–880`).

### 7.8 Các pha sau tìm kiếm

`ExecutionPhaseController` (`search/service/time/ExecutionPhaseController.kt`) ghi pha hiện tại, đo giờ, và cho mỗi pha
`hasPhaseTimedOut()`. Mỗi pha sau tìm kiếm có ngân sách `extraPhaseBudgetPercentage × maxTime`.

| Pha | Lớp | Bật bằng | Làm gì |
|---|---|---|---|
| MINIMIZATION | `Minimizer` (`search/service/Minimizer.kt:26`) | `--minimize` | chạy lại từng test, bỏ action thừa mà vẫn giữ mục tiêu |
| SECURITY | `RestSecurityBuilder` | `--security` | dựng test mới trộn nhiều tài khoản, chấm với oracle bảo mật |
| HTTP oracle | `HttpSemanticsService` | `--httpOracles` | kiểm ngữ nghĩa HTTP |
| FLAKINESS | `FlakinessDetector` | `--handleFlakiness` | chạy lại để tìm assert không ổn định |

Pha SECURITY, `RestSecurityBuilder.applySecurityPhase()` (`RestSecurityBuilder.kt:352–384`):

| Bước | Hàm | Làm gì |
|---|---|---|
| 1 | `individualsInSolution = archive.extractSolution().individuals` | lấy test đã có |
| 2 | `expandWithForbidden()` | dựng thêm test có 403 bằng cách đổi tài khoản |
| 3 | `addForStatefulAccessControl()` | **của ta**: dựng bộ ba source, transition, follow-up cho 970 |
| 4 | `addForAccessControl()` | upstream: lỗi phân quyền giữa các tài khoản |
| 5 | `addForInjections()` | upstream: SQLi, XSS, SSRF |
| 6 | `addForInfoLeakage()` | upstream: lộ stack trace |

Mỗi bước chỉ chạy khi pha chưa hết giờ. Bộ ba của ta chạy trước các bước upstream. Lượt Tier-1 hết 90 s trong pha này
(log dòng 602), nên các bước sau có thể không chạy hết.

Lời gọi oracle: test bảo mật mới được chấm bằng `fitness.computeWholeAchievedCoverageForPostProcessing(...)`, đi qua
`BlackBoxRestFitness` (§7.5), tới `RestSecurityOracle.analyzeSecurityProperties` (`RestSecurityOracle.kt:99–117`), gồm
13 lời gọi `handle…`; lời gọi cuối là `handleStatefulAuthorization` của ta (`:116`). Chạy tay hàm này:
`01-kotlin-cho-nguoi-viet-java.md` §24.

### 7.9 Viết test ra file

`Main.writeTests` (`Main.kt:1002`) dùng `TestSuiteWriter` (`output/service/TestSuiteWriter.kt:45`). `TestSuiteSplitter`
(`output/TestSuiteSplitter.kt`) chia test thành 3 file faults / successes / others (§5.4). Writer theo ngôn ngữ trong
`output/service/` (`HttpWsTestCaseWriter`, `ApiTestCaseWriter`…) dịch từng `RestCallAction` thành mã, ví dụ action 2 của
test 970:

```python
headers["Authorization"] = auth_superadmin # superadmin
body = " { " + \
    " \"role\" : \"VIEWER\" " + \
    " } "
res_2 = requests \
        .put(self.baseUrlOfSut + "/users/alice/role",
            headers=headers, data=body, timeout=EM_HTTP_TIMEOUT_S, verify=False)

assert res_2.status_code == 200
```

Assert sinh từ phản hồi thật lúc chạy. Comment `# Fault970. …` đặt trên action mang lỗi.

---

## 8. Mã của ta nằm ở đâu

`git diff --stat v6.1.1..HEAD`: 6 file, 1.825 dòng thêm, 0 dòng xoá ở file upstream.

| File (dưới `core/src/main/`) | Dòng thêm | Nội dung | Nối vào upstream ở |
|---|---|---|---|
| `kotlin/org/evomaster/core/EMConfig.kt` | 35 | 3 cờ `statefulAuthz…` | `:3044–3077` |
| `kotlin/.../problem/enterprise/ExperimentalFaultCategory.kt` | 5 | hằng `SECURITY_STATEFUL_AUTHORIZATION(970, …)` | `:54–57` |
| `kotlin/.../problem/rest/oracle/RestSecurityOracle.kt` | 76 | `handleStatefulAuthorization` | gọi ở `:116` |
| `kotlin/.../problem/rest/service/RestSecurityBuilder.kt` | 1.349 | dựng bộ ba, mô hình Naive Bayes, D1, khôi phục quyền | gọi ở `:361–363` |
| `resources/stateful-authz-model.csv` | 261 | trọng số Naive Bayes | đọc ở `RestSecurityBuilder.kt:96` |
| `resources/stateful-authz-lexicon.csv` | 99 | bộ từ vựng của jar AF2; P2e trở đi không đọc | |

Ba điểm nối: một lời gọi trong `applySecurityPhase`, một lời gọi trong `analyzeSecurityProperties`, một hằng enum. Phần còn
lại dùng lại dịch vụ upstream qua `@Inject`: `archive`, `fitness`, `idMapper`, `config`, `randomness`.

Chi tiết từng thay đổi: `infra/evomaster-ext/README.md`.

---

## 9. Thứ tự đọc mã

Ba buổi, mở trong IntelliJ, `Cmd+B` để nhảy tới khai báo.

| Buổi | Đọc | Mục tiêu |
|---|---|---|
| 1 | `Main.kt:76–300`, `Main.kt:529–640`, `Main.kt:883–925`; `BaseModule.kt`; `RestBaseModule.kt`; `BlackBoxRestModule.kt` | vẽ lại được sơ đồ §6.1; biết ai được Guice tạo |
| 1 | `SearchAlgorithm.kt`, `SmartsAlgorithm.kt`, `MioAlgorithm.kt` | hiểu vòng tìm kiếm |
| 2 | `Individual.kt`, `RestIndividual.kt`, `RestCallAction.kt`, `Param.kt`, `Gene.kt`, `ObjectGene.kt`, `OptionalGene.kt` | biểu diễn được test 970 thành cây đối tượng (§7.3) |
| 2 | `RestSampler.kt`, `AbstractRestSampler.kt:94–150`, `:330–350` | schema thành action mẫu; 36 test khởi động |
| 2 | `BlackBoxRestFitness.kt:31–81`, `AbstractRestFitness.kt:389–450`, `:650–700`, `:1280–1312`; `Archive.kt:397–460` | một test được chạy và giữ lại thế nào |
| 3 | `RestSecurityBuilder.kt:352–400` (upstream), `:600–763` (`addForStatefulAccessControl`), `:912–1054` (`executeStatefulAuthzTriple`) | pha bảo mật và cách ta dựng bộ ba |
| 3 | `RestSecurityOracle.kt:99–117`, `:552–625` | phán quyết 970; đối chiếu với `01-…` §24 |
| 3 | log `t1-vuln-seed1-r0.log` dòng 576–608 và `EvoMaster_faults_Test.py` | khớp từng dòng log với mã |

Muốn thấy mã chạy thật: đặt breakpoint trong IntelliJ ở `RestSecurityOracle.kt:613`, chạy `org.evomaster.core.Main` với
đúng cờ §5.1 (thêm `--add-opens` vào VM options, §4.1) khi container `reports-api` đang chạy. Đây là một lượt EvoMaster
thật: CLAUDE.md §2 cho phép mỗi lúc một việc nặng.
