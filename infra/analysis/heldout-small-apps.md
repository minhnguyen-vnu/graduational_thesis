# App held-out nhỏ — luật chọn, ghi 2026-09-29 09:43, trước khi tìm

Mục đích: thêm app bên thứ ba, chưa chạy lần nào, để đo jar `VI-d2325da7` như Mattermost. Chỉ tìm và lọc bằng đọc
repo; chưa dựng Docker. Kết quả mong đợi không ghi ở đây. Mọi app đã xét đều vào bảng §3, kể cả app trượt.

## 1. Luật lọc

Một app qua khi đủ cả bảy, xét theo thứ tự S1 tới S7, dừng ở luật trượt đầu tiên:

| Mã | Luật | Kiểm bằng |
|---|---|---|
| S1 | Mã nguồn mở, chưa có trong `infra/` (loại pyLoad, Airflow, Vikunja, ZITADEL, NocoDB, FUXA, Grafana, Mattermost, VAmPI) | license trong repo |
| S2 | Dựng được không cần dịch vụ ngoài trả phí hay IdP: image chính thức hoặc Dockerfile/compose trong repo | repo |
| S3 | Có spec OpenAPI/Swagger: file trong repo, hoặc framework tự phục vụ spec (FastAPI, springdoc, NestJS Swagger, drf-spectacular…) | repo |
| S4 | Spec dưới 200 operation (ngân sách search, `CLAUDE.md` §2) | đếm trong spec; không có file thì đếm route |
| S5 | Đăng nhập bằng user/mật khẩu qua một endpoint, trả token hoặc cookie | mã nguồn |
| S6 | Có ít nhất hai mức quyền, và admin đổi vai trò của một user khác bằng một request REST JSON; user bị hạ vẫn đăng nhập lại được | mã nguồn, spec |
| S7 | Dưới 2000 sao GitHub; commit trong 24 tháng gần nhất | GitHub API |

## 2. Nguồn và thứ tự

Tìm qua GitHub REST API `search/repositories`, không đăng nhập, mỗi truy vấn chạy một lần, lưu JSON thô vào
`heldout-small-apps/raw/`. Truy vấn, theo thứ tự:

1. `topic:rbac stars:50..2000`
2. `topic:self-hosted openapi stars:50..2000`
3. `topic:fastapi admin role stars:50..2000`
4. `topic:spring-boot rbac stars:50..2000`

Mỗi truy vấn lấy trang đầu (30 repo), giữ thứ tự API trả (best match). Xét repo theo thứ tự truy vấn rồi thứ tự
trong truy vấn, bỏ trùng. Luật dừng: đủ 3 app qua lọc, hoặc 12:30 09-29, cái nào tới trước.

Truy vấn chạy 09:44: q1 247 kết quả (lấy 30), q2 14, q3 0, q4 18; 60 repo sau bỏ trùng.

Sửa 09:45, sau khi thấy danh sách tên, trước khi mở repo nào: kiểm S7 trước S1–S6 vì nó chỉ cần metadata đã tải.
App qua lọc vẫn phải đủ bảy luật; chỉ cột "luật trượt đầu tiên" đổi theo. Thêm cách đọc S2: thư viện, công cụ dòng
lệnh, operator Kubernetes và repo chỉ có frontend không phải app chạy được, trượt S2. Captcha ở endpoint đăng nhập
trượt S5.

## 3. Kết quả lọc

Xét 09:45–09:55 trên bản clone nông, commit mặc định ngày 09-29. Dừng lần đầu sau repo #33 với 3 app qua; hai app bị loại khi đọc lại (§4). Repo #34–#60 chưa
xét, trừ 8 repo trượt S7 từ metadata. Đếm sau §4: qua 1; S1 2, S2 14, S3 1, S4 2, S5 7, S7 13, S8 1 (tính cả #34–#60), tổng 41.

| # | Repo | Sao | Luật trượt đầu tiên | Lý do |
|---|---|---|---|---|
| 1 | dromara/MaxKey | 1960 | S4 | `maxkey-web-mgt`: 88 mapping có method, 72 `@RequestMapping` không method, springdoc tách mỗi cái thành 7 operation |
| 2 | apache/casbin-pycasbin | 1769 | S2 | thư viện |
| 3 | jianyan74/rageframe2 | 1704 | S7 | commit cuối 2023-08 |
| 4 | mateaix/matecloud | 1702 | S4 | 206 mapping có method |
| 5 | mikespook/gorbac | 1675 | S2 | thư viện |
| 6 | FairwindsOps/rbac-manager | 1670 | S2 | operator Kubernetes |
| 7 | lakekeeper/lakekeeper | 1468 | S2 | user chỉ đến từ IdP OIDC |
| 8 | cyberark/KubiScan | 1433 | S2 | công cụ dòng lệnh |
| 9 | corneliusweig/rakkess | 1401 | S7 | commit cuối 2023-04 |
| 10 | sighupio/permission-manager | 1376 | S7 | commit cuối 2024-05 |
| 11 | aserto-dev/topaz | 1361 | S5 | dịch vụ phân quyền, không có đăng nhập user (đọc README) |
| 12 | php-casbin/php-casbin | 1338 | S2 | thư viện |
| 13 | apache/casbin-Casbin.NET | 1337 | S2 | thư viện |
| 14 | warrant-dev/warrant | 1337 | S5 | dịch vụ phân quyền, xác thực bằng API key (đọc README) |
| 15 | apache/casbin-rs | 1142 | S2 | thư viện |
| 16 | liggitt/audit2rbac | 1111 | S7 | commit cuối 2023-02 |
| 17 | caoqianming/django-vue-admin | 1103 | S8 | qua lọc đầu; loại khi đọc lại, §4 |
| 18 | alcideio/rbac-tool | 1085 | S2 | công cụ dòng lệnh |
| 19 | jeremykenedy/laravel-roles | 1050 | S2 | package Laravel |
| 20 | AthenZ/athenz | 1009 | S5 | xác thực bằng chứng chỉ X.509 |
| 21 | seeden/rbac | 1006 | S2 | thư viện |
| 22 | 417511458/jbone | 1003 | S7 | commit cuối 2024-03 |
| 23 | FairwindsOps/rbac-lookup | 981 | S2 | công cụ dòng lệnh |
| 24 | wmhello/laravel_template_with_vue | 966 | S3 | không có spec, không có gói sinh spec |
| 25 | AlexKhymenko/ngx-permissions | 949 | S2 | thư viện Angular |
| 26 | aquasecurity/kubectl-who-can | 922 | S7 | commit cuối 2024-07 |
| 27 | kuangshp/nestjs-mysql-api | 904 | S7 | commit cuối 2024-05 |
| 28 | jzfai/vue3-admin-plus | 874 | S2 | chỉ frontend |
| 29 | Allen7D/mini-shop-server | 837 | S5 | qua lọc đầu; loại khi đọc lại, §4 |
| 30 | ThinkWatchProject/ThinkWatch | 814 | S1 | Business Source License 1.1 |
| 31 | vemonet/libre-chat | 171 | S5 | không có tài khoản người dùng |
| 32 | rustmailer/bichon | 1969 | S5 | đăng nhập giới hạn 10 lần rồi 1 lần/600 s mỗi IP (`crates/core/src/utils/rate_limit/mod.rs`); EvoMaster đăng nhập mỗi test |
| 33 | rasonyang/ai-native-callcenter | 156 | — | qua |
| 35 | helixml/helix | 812 | S1 | Helix Subscription Service Agreement (đọc khi quét, trước luật dừng) |
| 36 | itmaaa/mcp-proxy | 79 | S5 | chỉ có admin key (đọc khi quét, trước luật dừng) |
| 45, 46, 53, 55, 56, 59 | xem §2 | | S7 | commit cuối trước 2024-09-29 |

Xét tiếp 10:11–10:20 theo luật §5:

| # | Repo | Sao | Luật trượt đầu tiên | Lý do |
|---|---|---|---|---|
| 34 | venkyr77/jellarr | 177 | S2 | công cụ cấu hình Jellyfin |
| 37 | offendingcommit/openconcho | 181 | S2 | UI desktop/web cho Honcho |
| 38 | rustmailer/rustmailer | 507 | S1 | RustMailer License Agreement, cấm dịch vụ thương mại |
| 39 | 1337hero/faster-chat | 173 | S3 | không có spec; có `PUT /users/:id/role`, vai trò lưu trong session |
| 40 | ailinone/collective-intelligence | 209 | S4 | 264 operation trong `openapi-spec.json` |
| 41 | IslamHouse-API/… | 95 | S2 | không có mã |
| 42 | busabase/busabase | 264 | chưa xong | better-auth, vai trò thành viên workspace; chưa đếm được operation |
| 43 | bailinghub/bailinghub | 132 | chưa xong | chưa đọc |
| 44 | hasmcp/hasmcp-ce | 62 | S5 | OAuth |
| 47 | AnanthaRajuC/Spring-Boot-Application-Template | 163 | S6 | không có endpoint đổi vai trò |
| 48 | pig-mesh/pig-ui | 317 | S2 | chỉ frontend |
| 49 | publicdevop2019/mt-auth | 70 | S3 | không có spec, không có gói sinh spec |
| 50 | IMS94/spring-boot-jwt-authorization | 93 | S2 | không có Dockerfile/compose |
| 51 | feiyuchuixue/sz-boot-parent | 415 | S5 | mật khẩu mã hoá AES bằng khoá tạm từ `/auth/challenge` (`PasswordStrategy.java:54–56`) |
| 52 | however-yir/knowledgeops-agent | 197 | S5 | API key |
| 54 | apache/casbin-spring-boot-starter | 238 | S2 | thư viện |
| 57 | devlive-community/authx | 73 | S3 | không có spec, không có gói sinh spec |
| 58 | AirPowerTeam/AirPower4J | 95 | S2 | khung dựng, không có Dockerfile |
| 60 | godcheese/nimrod | 144 | S2 | không có Dockerfile/compose |

## 4. Ba app qua lọc lần đầu, đọc lại khi chuẩn bị dựng

Đọc lại mã khi viết cấu hình dựng, 09:59–10:03; chưa build image nào. Hai trong ba bị loại.

**mini-shop-server** (`Allen7D/mini-shop-server`, MIT, commit `bec4431898`): loại 10:00, S5. Token gửi qua HTTP
Basic, username là token (`app/core/token_auth.py:59–69`; Werkzeug 2.0.3 chỉ đọc Basic và Digest). EvoMaster chèn
token vào mẫu header, không mã hoá base64 được. Lúc lọc bỏ sót điểm này.

**django-vue-admin** (`caoqianming/django-vue-admin`, MIT, commit `849f9aafa5`): loại 10:03. `FitJSONRenderer`
(`utils/response.py:48–63`), renderer mặc định, đặt mọi response thành HTTP 200 và ghi mã thật trong thân
(`"code": 403`). Oracle đọc mã HTTP (CLAUDE.md §3): nguồn, transition và follow-up đều đọc 200 dù bị từ chối. File
dựng dở giữ ở `infra/djva-target/`. Điều đọc được trước khi loại: quyền nằm trong cache Redis theo username, sống
1 giờ (`apps/system/permission.py:21`, `:40`); signal làm mới cache khi `roles` đổi (`apps/system/signals.py`),
`is_superuser` không có signal.

**ai-native-callcenter** (`rasonyang/ai-native-callcenter`, Apache-2.0, commit `47116cf6ed`): còn lại.
- Go, spec `docs/openapi.json` OpenAPI 3, 93 operation. Compose: aicc, postgres, FreeSWITCH. Không cần key nhà cung
  cấp để khởi động: `aicc-mockprovider` và `OPENAI_API_KEY=not-a-key` (`cmd/aicc-mockprovider/main.go`). Chưa kiểm
  REST có phục vụ khi FreeSWITCH vắng không.
- Đăng nhập `POST /auth/login`, cookie `aicc_session`. Mọi request ghi bằng cookie cần header `X-AICC-Csrf`, giá trị
  khác rỗng nào cũng qua (mô tả `csrfHeader` trong spec): đặt bằng `--header0`.
- Transition: `PUT /users/{userId}` với `role`; spec ghi admin cuối cùng không hạ được. Spec ghi scope của phiên
  lấy từ vai trò lúc đăng nhập.
- Từ chối: `writeError(w, http.StatusForbidden, …)` ghi mã 403 lên dây (`internal/httpapi/errors.go:111`).

## 5. Sửa luật 10:03, sau hai lần loại ở §4, trước khi xét tiếp

Thêm S8, làm rõ S5; app còn lại và app xét sau phải qua cả hai. Xét tiếp từ repo #34, cùng luật dừng.

| Mã | Luật | Kiểm bằng |
|---|---|---|
| S5 | Như §1, và EvoMaster gửi được chứng chỉ: token trong header theo mẫu cố định, hoặc cookie | mã nguồn phần xác thực |
| S8 | Từ chối vì thiếu quyền trả HTTP 403 trên dây, không bọc trong thân 200 | mã nguồn phần renderer, error handler |

## 6. ai-native-callcenter, giao thức (ghi 10:11, trước lượt chạy đầu)

App chưa chạy EvoMaster lần nào; chưa đoạn code builder nào viết dựa trên nó. Target `infra/aicc-target/`: mã upstream
commit `47116cf6ed` (`src/`, `git archive`), Dockerfile của repo, image `aicc-target:47116cf6`, cổng 8097, không sửa
mã. Postgres 18 riêng, `AICC_SEED=demo`.

Sai lệch đã khai:
- Không chạy FreeSWITCH: app log `esl connect failed` và vẫn phục vụ REST. Endpoint gọi điện có thể trả lỗi.
- Nhà cung cấp giọng nói `openai`, key `not-a-key`: không có lời gọi AI nào thành công.
- `strip_spec.py` bỏ 5 operation: đăng xuất, đặt mật khẩu (luật 09-17), và 3 operation webhook (tránh app gửi request
  ra URL do fuzzer sinh). Spec `src/docs/openapi.json` (sha `b666c75603c95950`), sau lọc
  `aicc-47116cf6-nokill.json` (sha `15cb9bebdf7eb355`), 88 operation, đường dẫn đặt dưới `/api/v1`, server url `/`.
- `PUT /users/{userId}` vừa là transition vừa đổi được `username` và `status`; giữ trong spec. Search có thể đổi tên
  hoặc đình chỉ tài khoản cấu hình.
- Header `X-AICC-Csrf: 1` gửi ở mọi request (`--header0`).

Kiểm tay 10:08 (`infra/aicc-target/handcheck-20260929-1008.txt`, sau `up.sh`): `victim` (ADMIN) tạo user 201,
`viewer` (AGENT) 403; admin đặt victim `role=AGENT` 200; cookie cũ và cookie mới của victim đều 403 trên
`POST /users`.

Tài khoản (`up.sh`, container mới trước mỗi lượt): `admin` (ADMIN, từ seed demo), `victim` (ADMIN), `viewer`
(AGENT). Auth `infra/em-config/aicc-auth.yaml`, cookie từ `POST /api/v1/auth/login`.

Jar `VI-d2325da7`. Một nhánh `auto`. Seeds 1–10, `--maxTime 300s`, `--ratePerMinute 600`, cờ D1 tắt, qua proxy ghi
request. Đếm như `heldout-20260928.md` §3. Không có bản lỗi: mọi 970 là FP sau khi kiểm tay lại, mọi bộ ba hợp lệ
không 970 là TN. Harness `em-results/aicc-heldout-20260929/run.sh`.

Luật dừng sớm:
1. Sau seed 1: không có lần đăng nhập `victim` nào trong traffic, hoặc `Evaluated tests` dưới 352 (4 × 88), thì dừng.
2. 3 seed đầu cùng một mẫu và 0 bộ ba hợp lệ thì dừng, ghi sai lệch, tìm nguyên nhân.
3. Máy ngủ trong một lượt thì dừng.

Kết quả lượt 1 (`em-results/aicc-heldout-20260929/`): seed 1 xong 10:19, dừng tay 10:20 giữa seed 2. Builder chọn
`PUT /api/v1/users/{userId}`, giá trị `[ADMIN, AGENT, EVOMASTER, SUPERVISOR, ACTIVE, SUSPENDED]`; 15 nguồn có guard,
0 có nạn nhân, 0 lần thử bộ ba. Nguyên nhân: 462 response `403 missing X-AICC-Csrf header`. `--header0` tạo một
tài khoản thứ tư "Fixed Headers" (`HttpWsSampler.kt:64–90`, upstream), không gắn header vào ba tài khoản cấu hình;
mọi request ghi của `admin`, `victim`, `viewer` thiếu header.

### Lượt 2, sửa giao thức (ghi 10:21, trước lượt 2)

Chỉ đổi cách gửi header: bỏ `--header0`, thêm `fixedHeaders: X-AICC-Csrf: "1"` vào từng tài khoản trong
`aicc-auth.yaml`. Chạy thử 30 s, seed 1 (`em-results/aicc-heldout-20260929b/probe/`): 124 request, 0 response thiếu
header, 6 response `403 INSUFFICIENT_SCOPE`. Còn lại như §6. Thư mục `em-results/aicc-heldout-20260929b/`.

## 7. ai-native-callcenter thành target phát triển (ghi 16:24)

Lượt 2 dừng sau seed 1 (`em-results/aicc-heldout-20260929b/RESULTS.md`). User chọn sửa builder (16:20). Hai sửa lỗi
viết trên log lượt 2 của app này, nên từ đây callcenter là target phát triển như Grafana: kết quả trên nó cho thấy
builder chạy được ở đó, không cho thấy tổng quát. Jar mới đo held-out trên một app chưa từng chạy.

## 8. Tìm tiếp cho jar mới (ghi 16:27, trước khi mở repo nào)

Luật dừng §2 (12:30) đã qua. Tìm tiếp một app held-out cho jar sửa ở §7, luật S1–S8 như §5. Thứ tự: xét xong #42,
#43; rồi truy vấn mới, mỗi truy vấn chạy một lần, lưu JSON thô vào `heldout-small-apps/raw/`:
5. `topic:admin-dashboard fastapi stars:30..2000`
6. `topic:nestjs rbac stars:30..2000`
7. `topic:self-hosted user-management stars:30..2000`

Dừng khi 1 app qua, hoặc 19:00 09-29.

Kết quả 16:27–16:31. q5 7 kết quả, q6 18, q7 10. Xét theo thứ tự §2, dừng ở app qua đầu tiên (#73):

| # | Repo | Sao | Luật trượt đầu tiên | Lý do |
|---|---|---|---|---|
| 42 | busabase/busabase | 264 | S6 | spec `/api/v1` (132 route) không có endpoint user hay vai trò; vai trò thành viên đi qua better-auth, ngoài spec |
| 43 | bailinghub/bailinghub | 132 | S3 | không có spec cho API quản trị; spec duy nhất của chính nó có 2 operation |
| 61 | jowilf/starlette-admin | 1043 | S2 | thư viện |
| 62 | benavlabs/crudadmin | 455 | S2 | thư viện |
| 63 | codemation/easyauth | 622 | S7 | push cuối 2024-06-11 |
| 64 | vsdudakov/fastadmin | 331 | S2 | thư viện |
| 65 | dnsmin/dnsmin-api | 30 | S6 | `PUT /users/{user_id}` không có vai trò; vai trò gỡ bằng `DELETE /acl/principal-roles/{principal_id}/{role_id}`, không phải request JSON |
| 66 | mr-fatalyst/oxyde-admin | 41 | S2 | thư viện |
| 67 | jowilf/qwikcrud | 31 | S7 | push cuối 2023-12-18 |
| 68 | Mohammed-Abdelhady/nextjs-nestjs-oauth-rbac-boilerplate | 293 | S1 | repo không có license |
| 69 | sergey-telpuk/nestjs-rbac | 508 | S2 | thư viện |
| 70 | zclzone/isme-nest-serve | 233 | S2 | không có Dockerfile/compose |
| 71 | andrechristikan/ack-nestjs-boilerplate | 700 | S4 | 229 decorator route |
| 72 | josephgoksu/prime-nestjs | 492 | S6 | không có endpoint đổi vai trò (11 route) |
| 73 | gobeam/truthy | 606 | — | qua |

Truthy, commit `9b9a61be6c`, MIT, push cuối 2025-02-01. S2: `Dockerfile`, compose với Postgres 12 và Redis. S3:
`@nestjs/swagger`, `SwaggerModule.setup('api-docs')` trong `src/main.ts`. S4: 39 decorator route. S5:
`POST /auth/login` JSON `username`/`password`, trả `Set-Cookie` (`auth.controller.ts:57–79`). S6: `PUT /users/:id`
nhận `roleId` (`update-user.dto.ts`); đăng nhập không đọc vai trò. S8: `PermissionGuard` trả `false`, NestJS trả 403
(`permission.guard.ts`). Hai điểm phải xử lý khi dựng: throttle toàn cục 60 request/60 s mỗi IP
(`config/default.yml:48–51`), đổi được bằng biến môi trường `THROTTLE_LIMIT` (`src/config/throttle-config.ts`);
đăng nhập sai quá 5 lần theo cặp username+IP chặn cặp đó 3000 s (`auth.service.ts:145–175`).

## 9. truthy, giao thức (ghi 16:35, trước khi dựng)

- Thứ tự thời gian: code jar mới viết xong 16:24 (§7, `evomaster-ext/wip/role-value-20260929.md`), truthy tìm thấy
  16:31. Code không sửa sau khi đọc truthy. Sửa code sau khi chạy truthy thì truthy thành target phát triển.
- Target: `infra/truthy-target/`, `src/` là `git archive` của `9b9a61be6c`. Image dựng bằng `infra/truthy-target/Dockerfile`:
  các bước của stage `development` upstream cộng `apk add python3 make g++`, vì `bcrypt` 5.0.1 không có bản dựng sẵn cho linux-arm64-musl (lần dựng upstream bắt đầu 19:54 hỏng với `404 Not Found … bcrypt_lib-v5.0.1-napi-v3-linux-arm64-musl.tar.gz` và `gyp ERR! … Could not find any Python installation to use`; `build.log` của lần đó bị lần dựng sau ghi đè); chạy `yarn migrate && yarn seed && node dist/main`.
- Sai lệch khai báo: `NODE_ENV=development`, vì `src/main.ts:23–43` chỉ phục vụ spec ở chế độ này;
  `THROTTLE_LIMIT=1000000` (throttle toàn cục 60/60 s chặn EvoMaster). Tài khoản `victim` (superuser) và `viewer`
  (normal) do `admin` tạo qua `POST /users`, mật khẩu đặt qua `PUT /auth/reset-password` với token đọc từ DB.
- Jar: jar mới của §7 sau self-test. Một arm `auto`, seeds 1–10, `--maxTime 300s`, `--ratePerMinute 600`, D1 tắt,
  qua capture proxy, bọc `caffeinate -dims`, dừng khi có `Entering Sleep`.
- Dừng sớm: (1) sau seed 1, không có đăng nhập `victim` hoặc `Evaluated tests` dưới số operation × 3;
  (2) 3 seed đầu cùng mẫu và 0 bộ ba hợp lệ. Luật dừng thì dừng, tìm nguyên nhân trong log, không sửa code trên
  truthy khi còn gọi nó là held-out.
- Kiểm tay trước lượt chạy, ghi file, như callcenter.

### truthy, bổ sung trước lượt chạy (ghi 21:42)

- Dựng: `Dockerfile` của ta, `node:14-alpine` cộng 25 gói `.apk` tải trên host (`truthy-target/apks/`, kích thước
  khớp APKINDEX v3.17), vì mạng trong Docker tải từ Docker Hub và mirror Alpine chậm (lần `apk` trong Docker 41 phút
  rồi hỏng, `build-apk-20260929.log`). Postgres `16-alpine` và Redis `7-alpine` thay cho `postgres:12`, `redis:alpine`
  của compose, vì hai image kia chưa có trên máy.
- Tài khoản: tạo qua `POST /users` không đặt được mật khẩu (token hết hạn ngay khi tạo, `auth.service.ts:111–116`
  chỉ cộng 1 giờ ở luồng đăng ký). `up.sh` dùng `POST /auth/register`, `GET /auth/activate-account`, rồi `admin`
  đặt `roleId` qua `PUT /users/{id}`. Đăng nhập cần `remember` boolean: `truthy-auth.yaml` dùng `payloadRaw`.
- Kiểm tay 21:39 (`truthy-target/handcheck-20260929-2139.txt`): source `PUT /roles/2` victim 200, viewer 403;
  transition `PUT /users/2 {"roleId":2}` 200; cookie cũ 403; đăng nhập lại 204; cookie mới 403.
- Spec `truthy-9b9a61be.json` (sha `021712a8d015f4e5`), 39 operation. Bỏ `POST /logout` (như callcenter) và
  `PUT /twofa` (bật 2FA cho chính tài khoản): `truthy-9b9a61be-nokill.json`, 37 operation. Luật dừng 1:
  `Evaluated tests` dưới 111.
- Lượt `truthy-heldout-20260929/` (21:41): harness đếm sai dòng `login … 204` (up.sh in 4, harness đòi 3); target lên
  bình thường; dừng tay. Lượt `…b/` (21:42): luật 1 dừng sau seed 1. EvoMaster fuzz `POST /auth/login` với
  username `admin`, `victim` và mật khẩu sai, quá 5 lần thì cặp username+IP bị khoá 3000 s; các lần đăng nhập của
  tài khoản cấu hình sau đó nhận 429 (admin 17, victim 6). EvoMaster v6.1.1 xử lý 429 bằng
  `actionResults.removeLast()` (`AbstractRestFitness.kt:818`, upstream), hàm JDK 21, chạy trên JDK 17 thì
  `NoSuchMethodError`, exit 1.
- Sửa giao thức (21:44, trước lượt `…c/`): thêm `NODE_CONFIG='{"throttle":{"login":{"limit":1000000}}}'`, cơ chế ghi đè
  của node-config. Kiểm: 8 lần đăng nhập sai liên tiếp của `admin` đều 401, lần đúng sau đó 204.
- Lượt `…c/` (21:45): seed 1 qua luật 1 (1569 test, 779 lần đăng nhập `victim`); builder chọn `PUT /users/{id}`, 0
  source có guard, 0 lần thử bộ ba. Nguyên nhân: `PUT /auth/profile` đổi username của chính tài khoản đang đăng nhập;
  EvoMaster đổi tên `admin` ở dòng traffic 131, `victim` 312, `viewer` 470, sau đó mọi lần đăng nhập của ba tài
  khoản 401 và request ghi đều 401. Dừng tay 21:52 sau seed 1.
- Sửa giao thức (21:53, trước lượt `…d/`): bỏ thêm `PUT /auth/profile`, cùng loại với `POST /logout` và `PUT /twofa`:
  `truthy-9b9a61be-nokill2.json` (sha `683d5ee7418b9bcd`), 36 operation, luật 1 dưới 108 test. Đã rà các endpoint còn lại:
  `PUT /auth/change-password` cần mật khẩu cũ, `PUT /auth/reset-password` cần token; `PUT /users/{id}` là
  transition, giữ.
- Lượt `…d/` (21:53): dừng tay 22:01 sau seed 1; kết quả và nguyên nhân: `em-results/truthy-heldout-20260929d/RESULTS.md`.

## 10. truthy thành target phát triển (ghi 22:25)

User chọn sửa builder sau lượt `…d/`. Ba sửa (`evomaster-ext/wip/num-role-20260929.md`) viết trên log truthy, nên từ
đây truthy là target phát triển như callcenter và Grafana. Chưa có app held-out nào cho jar mới.

## 11. Tìm app held-out cho jar `NR-3c087e58` (ghi 09:10 09-30, trước khi mở repo nào)

Luật S1–S8 như §1 và §5; S1 loại thêm callcenter và truthy. Mỗi truy vấn chạy một lần, lưu JSON thô vào
`heldout-small-apps/raw/`, xét theo thứ tự truy vấn rồi thứ tự API trả, bỏ trùng với §3 và §8:
8. `topic:rbac topic:express stars:30..2000`
9. `topic:rbac topic:django stars:30..2000`
10. `topic:rbac topic:go stars:30..2000`
11. `topic:user-management api stars:30..2000`

Dừng khi 2 app qua, hoặc 13:00 09-30. App qua chạy trên jar `NR-3c087e58`, không sửa code trên log của nó; lỗi builder
thì ghi lại và dừng app đó.

Kết quả 09:10–09:25. q8 9 kết quả, q9 10, q10 35, q11 13; 59 repo mới sau bỏ trùng. Luật S7 và S2 (thư viện, công cụ,
operator) xét trên metadata cho 49 repo; 10 repo mở mã:

| # | Repo | Sao | Luật trượt đầu tiên | Lý do |
|---|---|---|---|---|
| 74 | Shaisolaris/node-multitenant-api | 30 | S1 | loại: nạp và thực thi mã từ xa lúc khởi động |
| 75 | qingwave/weave | 604 | S6 | vai trò gỡ bằng `DELETE /api/v1/users/{id}/roles/{rid}`, không có body JSON (như #65) |
| 76 | hequan2017/go-admin | 422 | S8 | casbin từ chối trả HTTP 401, mã 403 nằm trong body (`middleware/permission/permissions.go`) |
| 77 | deatil/lakego-admin | 405 | S2 | không có Dockerfile/compose |
| 78 | mss-boot-io/mss-boot-admin | 72 | S3 | không có file spec; monorepo, 182 route |
| 79 | RohanNagar/thunder | 31 | S6 | không có vai trò |
| 80 | djaodjin/djaoapp | 143 | S4 | `schema.yml` 202 operation |
| 81 | tenxyte/tenxyte | 42 | S2 | package xác thực Django, không có Dockerfile |
| 82 | anditv21/panel | 54 | S2 | PHP, không có Dockerfile/compose |
| 83 | odboy-tianjun/cutego | 44 | S3 | không có spec, không dùng swag; 91 route Gin |

Thêm 09:22 09-30, trước khi chạy: q8–q11 hết, 0 app qua. Truy vấn tiếp, cùng cách xét, cùng luật dừng:
12. `fastapi rbac stars:30..2000 pushed:>2024-09-30`
13. `nestjs swagger rbac stars:30..2000 pushed:>2024-09-30`
14. `springdoc role admin stars:30..2000 pushed:>2024-09-30`
15. `topic:fastapi topic:jwt stars:30..2000 pushed:>2024-09-30`

Thêm S9 sau #74: đọc điểm khởi động và script cài đặt (`postinstall`, `prepare`, entrypoint) trước khi cài hay chạy;
có tải và thực thi mã từ xa thì loại.

## 12. bamf, giao thức (ghi 09:30 09-30, trước khi dựng)

App `mattrobinsonsre/bamf`, commit `394513bd`, MPL-2.0. Trượt S5 (đăng nhập hai bước PKCE). User chọn chạy với hai lệch luật:
1. Shim đăng nhập `infra/bamf-target/login_shim.py`: nhận `POST /login {email,password}`, gọi `/api/v1/auth/local/authorize`
   rồi `/api/v1/auth/token`, trả `{"token": session_token}`. EvoMaster gọi shim qua `externalEndpointURL`; mọi request
   khác đi thẳng tới API.
2. API chạy trên host (Python 3.14, venv), postgres:16-alpine và redis:7-alpine trong Docker. Dockerfile cần apt trong
   Docker, trên máy này đã hỏng một lần (§9).
Cấu hình khai báo: `BAMF_RATE_LIMIT__ENABLED=false` (mặc định giới hạn `/auth/*` theo IP; EvoMaster đăng nhập mỗi test).

Tài khoản: `admin` (bootstrap, vai trò `admin`), `victim` (vai trò `admin`), `viewer` (không vai trò platform), tạo bằng
`POST /api/v1/users` của admin. Spec: `/api/openapi.json` của app, lưu một lần, sha ghi lại.
Trước EvoMaster: kiểm tay một bộ ba (source có guard, `PATCH /users/victim` bỏ vai trò, follow-up bằng token cũ, đăng nhập lại).
Kiểm tay chỉ xác nhận target chạy được; không đổi cấu hình theo kết quả của nó.

Jar `LP-3cc44770` (không sửa code trên log bamf). Seed 1, `--maxTime` theo số endpoint × tài khoản (§2 CLAUDE.md), rate 600.
Dừng: EvoMaster exit khác 0; tài khoản nào không đăng nhập được trong traffic; 0 bộ ba sau seed 1 thì đọc log tìm nguyên nhân
trước seed 2. Lỗi builder thì ghi, không sửa trên bamf.

Bổ sung 09:35. Dựng: `infra/bamf-target/` (`src/` = `git archive` của `394513bd`, script dựng, tắt, `login_shim.py`).
Trên host, lock của bamf không cài `greenlet` cho macOS arm64 (marker nền tảng của SQLAlchemy); cài bù `greenlet==3.3.1`
theo lock (`install.log`). Shim cần thêm trường `state` (`LocalAuthorizeRequest`). Spec 82 operation, sha `bb641d2ca26e4b08`.
Kiểm tay (`infra/bamf-target/handcheck-20260930-0935.txt`): source `PATCH /roles/handcheck-role` victim 200, viewer 403;
admin `PATCH /users/victim@example.com {"roles":[]}` 200, vai trò còn `[]`; token cũ 200; đăng nhập lại, token mới 403.
Harness trong `em-results/bamf-heldout-20260930/`: target mới mỗi seed, proxy ghi traffic ở 8212, shim đi qua proxy để
đếm đăng nhập theo tài khoản; `--maxTime 600s`, rate 600, cần ≥ 246 test (82 × 3).

Lượt a (`em-results/bamf-heldout-20260930/`), self-test jar `LP-3cc44770` 33/33 trước đó. Seed 1, 10:29–10:43: exit 0,
3687 test, đăng nhập victim 1715, admin 1625, viewer 1581; 0 lần thử bộ ba, dừng sớm. Builder chọn transition
`PATCH /api/v1/users/{email}`, giá trị `[user, viewer, guest, member, basic]`; 11 source có guard, đều POST, đều không có
nạn nhân. Nguyên nhân (traffic): search gửi `PUT /api/v1/role-assignments {"provider_name":"local","email":"admin","roles":[]}`
200 lúc 10:31:26 và cùng body cho `victim@example.com` lúc 10:32:31. Sau đó token mới của `admin` và `victim` mang
`roles: []`; 505 lần `POST /users` trả 403 `Admin access required`, gồm 162 của `admin` và 156 của `victim`.
Không phải lỗi builder: search tự hạ quyền hai tài khoản cấu hình, như `PUT /auth/profile` trên truthy (§9).

Sửa, ghi 10:50 trước lượt b: bỏ riêng operation `PUT /api/v1/role-assignments` khỏi spec (lệch luật thứ ba, cùng cách
truthy `nokill`). `PATCH /users/{email}` giữ lại vì là transition; lượt a không có lần nào trả 2xx. Lượt b ghi vào
`em-results/bamf-heldout-20260930b/`, cùng luật dừng.

Lượt b, seed 1, 10:46–10:59: exit 0, 3745 test, 0 lần thử bộ ba, dừng sớm. Hai nguyên nhân:
1. Search gửi `DELETE /api/v1/users/admin` 204 lúc 10:51:57; sau đó 933 lần đăng nhập `admin` trả 401.
2. Source `POST /api/v1/certificates/service` và `POST /api/v1/certificates/revoke` có nạn nhân `victim`, nhưng 20 lần
   `could not target victim 'victim' on PATCH:/api/v1/users/{email}`, `identifiers []`. Builder gán tên nạn nhân (tên trong
   file auth) vào tham số user; API định danh user bằng email, và không body nào có trường tên bằng `victim`.

Sửa, ghi 11:05 trước lượt c, không đổi code: bỏ thêm `DELETE /api/v1/users/{email}` khỏi spec (lệch luật thứ tư; luật 09-17
đã loại xoá subject khỏi transition vì nó giết đăng nhập). Tên tài khoản trong `bamf-auth.yaml` đặt bằng định danh của API:
`victim@example.com`, `admin`, `viewer@example.com`. Builder giả định tên trong file auth là tên tài khoản
(`evomaster-ext/wip/role-value-20260929.md` §Giới hạn); lượt b đặt sai giả định đó. Lượt c ghi vào `…c/`.

Lượt c, seed 1, 11:01–11:14: exit 0, 3922 test, 0 lần thử bộ ba, dừng sớm.
1. Lỗi builder: 20 lần `could not target victim 'victim@example.com' on PATCH:/api/v1/users/{email}`. Tham số user được
   nhận theo tên trong `transitionUserParamSignals` (`RestSecurityBuilder.kt:401`); danh sách không có `email`.
2. Search gửi `PATCH /api/v1/users/admin {"password":"1dfPUCivJ48fi5gR","roles":["admin"]}` 200 lúc 11:03:11; sau đó
   `admin` đăng nhập hỏng (1486 lần hỏng trong lượt).

**Kết quả held-out của bamf trên jar `LP-3cc44770`: 0 bộ ba, không ô nào.** EvoMaster không dựng được bộ ba vì builder
không nhận `{email}` là tham số user. Ghi FN lúc 11:17 là sai, sửa 22:25: kiểm tay 09:35 cho thấy hành vi MR-A1, nhưng bamf
ghi trong mã và tài liệu rằng vai trò của phiên là vai trò lúc đăng nhập (`infra/bamf-target/contract-20260930.md`). bamf
không có lỗi theo hợp đồng của chính nó.

User chọn 11:17: ghi FN, sửa builder; từ đây bamf là target phát triển. Sửa: `email` thành nhóm tham số user thứ hai,
xét sau các tên hiện có và trước `id` (`evomaster-ext/wip/email-param-20260930.md`). Lệch luật thứ năm, ghi trước lượt d:
spec bỏ trường `password` của `UserUpdate` (body của `PATCH /users/{email}`), vì search dùng chính transition để đổi mật
khẩu tài khoản cấu hình.

Self-test lần 1 của jar `EP-9007f79a` (11:20–11:33, bamf seed 1): vẫn 20 lần `could not target`. Nguyên nhân: EvoMaster tạo gene
chuỗi của path param với `invalidChars = ['/', '.']` (`RestActionBuilderV3.kt:2247`, upstream), nên `victim@example.com`
không gán được vào `{email}`. Search gửi được `/users/admin` vì `admin` không có dấu chấm. Lệch luật thứ sáu, ghi 11:40
trước lần 2: `victim` và `viewer` tạo bằng CLI bootstrap của bamf (như `admin`) với định danh không dấu chấm; `viewer` bị
admin gỡ vai trò `admin` bằng `PATCH /users/viewer {"roles":[]}` (script dựng, chế độ `dotless`; `bamf-auth-dotless.yaml`).
Giới hạn cần ghi: path param chứa `.` (email, tên miền) không nhận được giá trị nạn nhân trong EvoMaster v6.1.1.

Self-test lần 2 (`em-results/emailparam-selftest-20260930-114430/`, 11:44–12:08): 4/6. `bamf-email-param-targeted` qua
nhưng không có ý nghĩa: builder không tới bước chọn nạn nhân. 11 source, đều `victims []`, 0 lần thử bộ ba. Search gỡ quyền
hai tài khoản bằng `DELETE /api/v1/role-assignments/local/admin/admin` (11:46:21) và `…/local/victim/admin` (11:52:07);
sau đó đăng nhập `admin` 1454 lần và `victim` 751 lần mang `roles: []`. Lệch luật thứ bảy, ghi 12:12 trước lần 3: bỏ thêm
`DELETE /api/v1/role-assignments/{provider_name}/{email}/{role_name}` khỏi spec (thao tác gỡ vai trò không có body, builder
không dùng làm transition).

Self-test lần 3 (`em-results/emailparam-selftest-20260930-120947/`): 6/6; 11 lần thử bộ ba, 10 lần transition 400
(`Role 'user' not found`), VOID. Jar `ER-06b48c30` thêm giá trị hạ `[]` cho mảng vai trò (`evomaster-ext/wip/empty-roles-20260930.md`).
Self-test `empty-roles.sh` (`em-results/emptyroles-selftest-20260930-123733/`): 10/10, bamf seed 1 có 970. Traffic 12:49:08–09:
`POST /api/v1/certificates/revoke` của `victim` (token có `admin`) 200; `PATCH /api/v1/users/victim {"roles":[]}` của `viewer`
(vừa được khôi phục `admin`) 200; follow-up bằng token cũ của `victim` 200; token mới của `victim` (`roles: []`) 403.
Bamf là target phát triển từ 11:17; bảy lệch luật khai báo ở trên. Seeds 1–10: `em-results/bamf-dev-20260930d/`.
Các lần nổ 970 trên bamf bắt đúng hành vi bamf đã ghi trong hợp đồng; xếp chúng vào ô nào chưa quyết.

## 13. Tìm app có lỗi theo hợp đồng, qua issue và commit (ghi 22:25 09-30, trước truy vấn nào)

Lý do đổi hướng: bamf qua lọc S1–S9 nhưng không có hợp đồng (§12). Từ nay tìm ngược từ chỗ vendor đã nhận lỗi: một commit
hoặc PR sửa, hoặc một issue maintainer xác nhận là lỗi. Commit sửa cho luôn hai bản: bản dính (commit cha) và bản đã sửa.
Mục tiêu: app công khai, ít người dùng, ít người đóng góp.

Luật, xét theo thứ tự, dừng ở luật trượt đầu tiên. S1–S6, S8, S9 như §1, §5, §11; đổi S2, S7; thêm S10 đứng đầu:

| Mã | Luật |
|---|---|
| S10 | Hợp đồng: commit/PR sửa đã merge, hoặc issue có maintainer xác nhận là lỗi, mô tả đúng lớp: admin thu hẹp vai trò, quyền hoặc nhóm của một user khác, phiên hoặc token có từ trước vẫn giữ quyền cũ. Loại: đăng xuất, đổi mật khẩu, xoá hoặc vô hiệu hoá user (đăng nhập lại hỏng nên không có chứng chỉ mới), lỗi chéo tài khoản |
| S7 | Dưới 2000 sao. Bỏ điều kiện commit trong 24 tháng |
| S2 | Như §1, hoặc chạy trên host bằng công cụ chuẩn của stack (pip, npm, mvn, go) không cần dịch vụ trả phí; áp cho cả bản dính và bản sửa |

Truy vấn GitHub REST không đăng nhập, mỗi truy vấn chạy một lần, trang đầu (30 kết quả), thứ tự API trả, JSON thô vào
`heldout-small-apps/raw/`. Commit (`search/commits`): q16 `invalidate sessions role change`, q17 `revoke sessions role changed`,
q18 `logout user when role changes`, q19 `invalidate tokens role change`, q20 `permissions stale session role`.
Issue và PR (`search/issues`): q21 `role change take effect in:title`, q22 `permissions not updated after role change in:title`,
q23 `removed admin still access in:title`, q24 `revoked permission still in:title`, q25 `jwt old role in:title`.

Xét theo thứ tự truy vấn rồi thứ tự API trả, bỏ trùng repo. S10 xét trên tiêu đề, thân, diff; S7 trên metadata; phần còn
lại trên bản clone nông, chỉ đọc, không cài. Dừng khi 2 app qua, hoặc hết q16–q25, hoặc 12:00 10-01. App qua: kiểm tay bộ ba
trên bản dính và bản sửa trước khi viết cấu hình EvoMaster.

### Kết quả truy vấn (22:22–22:26)

Tổng: q16 24906, q17 15440, q18 24774, q19 41073, q20 53329, q21 28, q22 0, q23 5, q24 19, q25 4. q19 và q20 lần gọi đầu
trả 403 (giới hạn tốc độ, không có JSON), gọi lại 22:25. 196 repo sau bỏ trùng, đánh số #101–#296 theo thứ tự xét;
metadata (sao, fork, license) trong `raw/q16-25-meta.json`. Cách đọc S1: license GitHub trả `None` thì trượt S1;
`NOASSERTION` thì mở file license. Commit cùng sha ở một fork thì xếp trùng với repo gốc.

### #101 wagoebv/wagoe (xét 22:30–22:55)

Framework web Clojure, 6 sao, EPL-2.0; repo có app chạy được (`Dockerfile` dựng uberjar từ `src/` và `libs/`).
- S10 qua. Commit `180fbc5629` (07-21, BOU-191): *"a role change let a live session retain its old privileges"*, sửa để
  *"a demotion cannot retain elevated access"*. Sửa chỉ huỷ phiên phía server.
- Bản cha `14166422df`: Bearer JWT đi vào `jwt-authentication-middleware`, vai trò lấy từ claim; token phiên đi vào
  `session-authentication-middleware`, đọc user từ DB. Commit `88033e04` (08-25) ghi rằng trước nó nhánh JWT cho
  `{:id nil :email nil :role nil}` với mọi token, nên ở bản cha nhánh JWT không mang vai trò admin nào.
- Bản hiện tại `d2ceb362a0` (09-28): `POST /api/v1/auth/login` trả JWT không lưu DB (`shell/auth.clj:321–332`), claim
  `role` (`:119`); `validate-jwt-token` chỉ kiểm chữ ký và hạn (`:134–139`); `require-admin` đọc `:user` của request
  (`http_interceptors.clj:163–176`), tức claim. Huỷ phiên của BOU-191 không chạm JWT. Nếu kiểm tay khớp, JWT cũ của
  user bị hạ vẫn qua `require-admin` trên bản mới nhất: vi phạm hợp đồng BOU-191, chưa có bản sửa.
- S7 qua. S3 qua: `/swagger.json` bật mặc định (`reitit_router.clj:741`), Swagger 2.0. S5 qua: JSON `email`/`password`,
  token trong body. S6 qua: `PUT /api/v1/users/:id`, `role ∈ {admin, user, viewer}`, chỉ admin. S8 qua: `require-admin`
  trả 403. S4 chưa chắc: khoảng 78 khai báo method trong các module bật mặc định, cần đếm trên spec thật.
- S2 chưa xong: Docker build cần `apt-get` trong stage runtime (từng hỏng trên máy này, §9); host có Java 17, chưa có
  Clojure CLI, image dựng dùng JDK 21. S9: `Dockerfile` và `src/wagoe/main.clj` không tải hay chạy mã từ xa.
- Chưa kiểm tay. Chưa có bản sửa cho nhánh JWT, nên chưa có cặp bản dính/bản sửa.

## 14. wagoe: dựng, chạy, kiểm tay (ghi 10-01, sau khi kiểm)

Dựng: uberjar host đã xong 09-30 22:54 (`infra/wagoe-target/`, `build exit 0`), commit `d2ceb362a0`, jar 172 MB. Không cần
đường Docker `apt-get` mà §13 lo; rào S2 gỡ.

Chạy: Postgres 16 trong Docker + profile `dev` cổng 3000. Boot sạch ("Wagoe HTTP server started successfully"), schema
tạo 4 bảng `auth_users, users, user_sessions, user_audit_log`. `GET /swagger.json` 200, 50 path. Ba endpoint MR-A1 sống:
`POST /api/v1/auth/login`, `GET,POST /api/v1/users`, `DELETE,GET,PUT /api/v1/users/{id}`.

Tạo tài khoản: `POST /api/v1/users` runtime đòi auth (401) dù swagger ghi security None; `/test/reset` 404 trong dev
(flag không bật). Dùng CLI `java -jar <jar> cli user create --email .. --name .. --role .. --password ..` (qua
`register-user`, ghi thẳng Postgres). Ba user: `op1@acme.test` admin, `vic1@acme.test` admin, `target1@acme.test` user,
mật khẩu test `Test-Pass-1234!`.

Login trả `jwtToken` (JWT `eyJ…`, claim `role`) và `sessionToken` (opaque). Hai nhánh auth tách biệt như §13.

Kiểm tay — **970/MR-A1 KHỚP** (credential = JWT):
- A. victim login trước transition → OLD JWT, claim `role=admin`.
- B. transition: hạ role victim admin→user (làm bằng `UPDATE users SET role='user'` trong DB, vì PUT REST vướng, xem
  dưới). C. API xác nhận victim role=user.
- D. REPLAY: OLD JWT (claim admin) gọi `POST /api/v1/users` (admin-only) → **HTTP 201**, vẫn tạo được user.
- E. D1: victim login mới → JWT claim `role=user` → cùng write → **HTTP 403** "Admin role required".
- F. sanity: operator admin → cùng write → 201. Endpoint đúng là admin-only.
Chuỗi: source ALLOWED(201) trước, transition hạ quyền, follow-up token cũ ALLOWED(201) = vi phạm; credential mới
DENIED(403) = đúng chiều D1. Nguyên nhân: `require-admin` đọc role từ claim JWT; `validate-jwt-token` chỉ kiểm chữ ký +
hạn, không tra DB. BOU-191 chỉ huỷ session phía server.

Vướng cho bước chạy máy:
- Transition qua REST (`PUT /api/v1/users/{id}`) là **full-object**: từ chối body một phần; key **camelCase**
  (`notificationsSms`, `timeFormat`…); các trường nullable (timezone, avatar-url, time-format enum, mfa-enabled…) phải có
  giá trị hợp lệ. Hạ role bằng PUT cần builder gửi body đầy đủ — đây là chỗ EvoMaster dễ gãy (như bamf/Vikunja). Source
  admin-write (`POST /api/v1/users`) thì body đơn giản.
- Jar là bản **chưa vá nhánh JWT** → chưa có cặp dính/vá cho nhánh JWT (mặt 0-FP). Cặp chỉ có ở nhánh session: cha
  `14166422df` vs vá `180fbc5629`.

Smoke EvoMaster (jar ER-06b48c30, seed 1, spec cắt còn login + users GET/POST + users/{id} GET/PUT, dev profile):
`infra/em-results/wagoe-smoke-20261001/`. Kết quả: **0 bộ ba, 0 VOID, 0 970**. Chẩn đoán từ trace
`RestSecurityBuilder` mức DEBUG:
- Builder **nhận đúng** `{id}` là userParam và **chọn đúng transition** `PUT /api/v1/users/{id}` (không phải lỗi
  lớp bamf). `guarded source candidates: 1 [POST /api/v1/users]`.
- `source POST:/api/v1/users victims []` → `sources exhausted after 0 triple attempts`. Theo mã (RestSecurityBuilder.kt
  :580–586) victim = test đã gọi source với user auth và nhận 2xx; danh sách rỗng ⇒ **trong cả lượt không lần nào create
  (có auth) trả 2xx**.
- Nguyên nhân: `POST /api/v1/users` bắt buộc ngữ nghĩa **không có trong OpenAPI**: `password` runtime bắt buộc nhưng
  schema chỉ required [email,name,role]; `name` phải khớp regex chỉ chữ cái (số/ký hiệu → `invalid-characters`);
  `role=viewer` trong enum nhưng dev từ chối (allowed {user,admin,manager}). Body ngẫu nhiên gần như luôn 400. Create
  hợp lệ tay (`{email,name:"Eve",password,role:"user"}`) → 201.
- Operator-auth từng hỏng (fuzzer đổi email/active qua PUT) đã khử bằng reseed sạch trước mỗi lượt; khử xong **vẫn**
  `victims []` ⇒ blocker cốt lõi là source create không 2xx, không phải auth.
- Đây là **ranh giới độ trung thực của spec**: oracle chọn đúng transition, lỗi có thật, nhưng black-box không dựng nổi
  write-source vì ràng buộc input không được OpenAPI mô tả. Khác với ranh giới hình dạng lỗi (Airflow transition không
  REST; Vikunja không cấp chứng chỉ mới).

Làm spec trung thực (chỉ sửa spec đưa EvoMaster, app nguyên vẹn; lệch luật đã khai) — Path B, user chọn 10-01: ép
`consumes:[application/json]` (wagoe khai body là edn/transit/msgpack, EvoMaster gửi TEXT → server không parse); create
khai `password` required + `name` pattern chỉ-chữ-cái + `role` enum [admin,user] + enum hoá `timeFormat/dateFormat/theme`
(server validate ngữ nghĩa không có trong OpenAPI). Sau đó **create 2xx được** (DB 3→24 user). Nhưng builder **vẫn
`victims []`**, tầng chặn sâu hơn lộ ra:
- `Minimizer - Different status code 409 returned from original 201 for POST:/api/v1/users`. **POST create không
  idempotent**: lần đầu 201, replay cùng email → 409. Minimization replay y nguyên → 409, EvoMaster không giữ được cá thể
  create-2xx ổn định → source không ALLOWED → `victims []` → 0 triple. wagoe không có reset endpoint (dev `/test/reset` 404).
- Ngay cả nếu ổn định được: follow-up của oracle cũng replay source → create trùng email → 409 (INCONCLUSIVE) thay vì 201
  ALLOWED → không nổ 970. **Source phải lặp lại được (idempotent)**; wagoe chỉ lộ một admin-write black-box (create,
  non-idempotent); write idempotent duy nhất `PUT /users/{id}` đã là transition (builder loại transition khỏi source).
- Ranh giới cuối cùng của wagoe: **oracle replay cần một write-source lặp-lại-được và ALLOWED; create non-idempotent +
  SUT không reset làm follow-up không cho tín hiệu sạch.** Mới, khác cả ranh giới hình-dạng-lỗi lẫn độ-trung-thực-spec.
  Harness: `infra/em-results/wagoe-smoke-20261001/` (smoke.sh, smoke-debug.sh, smoke-faithful.sh, reseed.sh); jar
  ER-06b48c30; toàn bộ là smoke cô lập biến, không phải số báo cáo.

## 15. Tiếp §13 từ #102 (ghi 08:56 10-01, trước khi mở commit/issue/diff nào)

wagoe (#101) qua S10 nhưng tắc ở một ranh giới mới (§14): source `POST create` không idempotent, không có reset, nên
EvoMaster không ổn định được source 2xx. Tiếp danh sách `raw/q16-25-meta.json` "order" từ #102 để tìm ứng viên kế.

Luật giữ nguyên S1–S10 (§13). Sàng sơ `order[#102..#296]` bằng S1 (có license, không `None`/`NOASSERTION`) và S7
(<2000 sao) để lại 33 repo; xét theo thứ tự "order", mỗi repo đọc S10 trên commit/diff hoặc issue (core API, không
dùng search), rồi S2–S9.

Thêm một ưu tiên tiebreak ghi trước, rút từ §14, không phải một gate loại bỏ: khi hai ứng viên cùng qua S10, chọn
ứng viên mà thao tác bị gác có một **write-source idempotent hoặc lặp-lại-được và ALLOWED** (PUT upsert, hoặc có
đường reset) để oracle ổn định được source 2xx. Ứng viên chỉ có create non-idempotent vẫn được xét, chỉ xếp sau.

Luật dừng: dừng khi **1 app qua trọn S1–S10 và dựng được với cặp bản dính/bản sửa** (đủ để chạy máy), hoặc hết 33
repo. Kết quả mong đợi không ghi ở đây.

### Kết quả §15 (ghi 09:05 10-01, sau khi xét S1–S10 trên #102+)

Sàng S1+S7 để lại 33 repo trong `order[#102..#296]`. Xét theo thứ tự.

Đính chính một kết luận vội lúc 08:58: ba lô curl đầu trả 404 cho mọi URL làm tôi ghi commit/issue "đã bị rebase, repo
tổng hợp". Direct curl lại từng URL trả 200: 404 là lỗi transient của loop, không phải commit/issue biến mất. Các commit
#117, #127 tồn tại và có nội dung thật.

Ba hit từ truy vấn issue trên org thật, mỗi cái trượt một luật:
- #294 `ansible/django-ansible-base` PR 1082 (merged 08-04): tiêu đề nhắc "JWT claims old Role sync" nhưng thân là **sửa
  hiệu năng** (bọc `_sync_old_rbac` trong `disable_rbac_sync`, 8.8x), không phải lỗi phân quyền tồn dư. S10 trượt.
- #280 `verana-labs/verre` issue 107 (closed 06-16): đúng lớp khái niệm ("revoked permission still resolves authorized")
  nhưng là **DID/verifiable-credential trên testnet/indexer** (`src/resolver/didValidator.ts`), chứng chỉ cũ không do
  endpoint login cấp. S5/S3 trượt.
- #284 `wso2/product-is` issue 25308 (Severity/Major, Type/Bug, closed 09-03-2025): lỗi thật nhưng là **trạng thái
  request duyệt đang chờ** còn sót sau khi gỡ quyền approver, không phải credential mang role cũ; và build WSO2 IS 7.2 là
  cực nặng. S10 lớp biên + S2 trượt.

Hai hit từ truy vấn commit qua S10 với cặp bản dính/bản sửa sạch:
- **#117 `orkestra-cc/orkestra`** (Apache-2.0, 3★, Go, tạo 2025-12-20, 73MB, backend định danh dùng `huma/v2`). Commit
  `5330755dbb` (fix) / parent `2e9a2dcb38` (dính). Message: *"A role change flushed no authz cache and ended no session,
  so a demoted administrator kept administrator verdicts for ... a whole access-token lifetime of stale `srole`."*
  Patch sửa `core/user/handlers/user_handler.go` (+105/-10): thêm terminate-session + invalidate-cache cho nhánh đổi
  system-role (D27). Bản dính: nhánh role không làm hai việc đó. Phần `srole` trong access-token không phụ thuộc cache
  60s, nên oracle khai thác được không cần lệch luật TTL.
- #127 `octarq-org/octarq` (MIT, 2★, Go multi-tenant). Commit `6ccaaaa4d3` / parent `f6cbc4396b`: "invalidate same-org
  sessions on member role change". Cùng lớp, để làm dự phòng.

Screen orkestra: S1 Apache-2.0 ✓; S7 3★ ✓; S10 cặp sạch ✓; S2 `docker/docker-compose.infra.yml`+`backend/Dockerfile`
+`go.mod` (MongoDB qua compose) ✓; S3 `huma/v2` tự sinh OpenAPI + `backend/openapi/enterprise.json` + `scripts/openapi-dump.sh`
✓; S5 login→access-token mang `srole` ✓; S6 route đổi role trong `user_handler.go`, admin-gated ✓; S8/S9 chưa đọc chi tiết.

Caveat độ tin cậy (ghi để thầy tự cân): orkestra là repo "superpowers" phát triển có AI (`docs/superpowers/specs/`,
`CLAUDE.md` rải trong module), 3★, chưa rõ có người dùng thật. Một bản vá maintainer đã merge đúng lớp là một hợp đồng
thật — mạnh hơn lỗi tự gieo, yếu hơn một CVE. Rủi ro còn mở, giải ở bước dựng: cần một admin-write **idempotent và
ALLOWED** làm source (ranh giới §14 wagoe); orkestra có nhiều endpoint admin CRUD nên khả năng cao hơn wagoe, chưa chắc.

Theo luật dừng §15 (1 app qua trọn screen + có cặp dính/sửa dựng được): **dừng hunt. Ứng viên kế = orkestra**, dự phòng
octarq.

## 16. orkestra: dựng, bootstrap, kiểm tay, vì sao oracle không với tới (ghi 10:05 10-01, sau khi kiểm)

Kết luận: lỗi THẬT (vendor đã vá, kiểm tay khớp cả bản dính lẫn bản vá), có cặp vuln/fixed sạch, nhưng oracle MR-A1
không nổ trên cả hai bản — vì hai lý do độc lập. Ranh giới thứ ba, khác wagoe (§14).

### Dựng (target `infra/orkestra-target/`)
- Clone `orkestra-cc/orkestra`; bản dính `2e9a2dcb38` ("fix(authz): route a role edit past the gate"), bản vá
  `5330755dbb` (lịch sử tuyến tính, chỉ chạm `user_handler.go`+`interfaces.go`+test, không chạm docker/).
- Dev stack: `docker-compose.dev.yml` dùng `Dockerfile.dev-backend` (`golang:1.26.8-alpine`+AIR, **public, không cần
  dhi.io**), source mount `../backend:/app` + AIR hot-reload → đổi bản dính↔vá chỉ cần `git checkout` (AIR rebuild ~2s).
  Infra: mongo 8.0.29 (replica set rs0) + redis 8.2.10 + rustfs. `make init --yes` sinh .env+RS256 keys. `/openapi.json`
  bật sẵn (dev). Port 3000/27017/6379.

### Bootstrap (ba tài khoản, qua REST, không chọc DB)
- User đầu đăng ký → super_admin (`main.go:138` "first user becomes super_admin"): `op@orkestra.test`.
- Self-register operator mặc định tắt (403 `auth.registration_disabled`). SA bật qua `PATCH /v1/admin/modules/auth`
  `{"config":{"registrationEnabledAdmin":"true"}}` (needsRestart=false) — thao tác cấu hình, không sửa code.
- Đăng ký `vic@`/`tgt@` (mặc định role `guest`), SA promote `vic@`→`administrator` qua `PUT /v1/users/{id}`.
- Auth: `POST /v1/auth/operator/login` → `accessToken` (JWT RS256, claim `srole`,`sid`,`sub`, exp 15m). Config
  `infra/em-config/orkestra-auth.yaml`, reseed `em-results/orkestra-handcheck-20261001/reseed.sh`.

### Transition đòi step-up (lý do oracle #1)
`PUT /v1/users/{id}` (đổi system-role) mang `RequireStepUp(5m)` (`user/routes.go:85–95`). Bằng chứng: token login tươi
của SA gọi PUT trả **401 `password_confirm_required`**; phải `POST /v1/auth/operator/me/password-confirm` lấy token
elevated trước. `POST /v1/users` (source/follow-up, `system.users.admin`) **không** step-up (`routes.go:69`). EvoMaster
cấu hình auth một-bước (một login/tài khoản) không password-confirm được → builder gọi transition sẽ nhận 401, transition
không 2xx → bộ ba VOID.

### Kiểm tay MR-A1 (lý do oracle #2: lớp ZITADEL, không phải credential-persistence)
`em-results/orkestra-handcheck-20261001/handcheck-cacheaware.{sh,log}`. source=POST /v1/users; transition=PUT role.

Bản dính `2e9a2dcb38`, sau khi hạ victim administrator→guest, poll token-cũ (srole=administrator) vs token-mới (login
lại, guest):
```
t=0s  fresh(guest)=200  old(administrator)=200
...   (giữ 200 suốt)
t=62s fresh(guest)=403  old(administrator)=403   <- cả hai lật cùng lúc
```
Quyền lấy từ tra cứu user→DB cache 60s (`RequireSystemPermission`, `middleware/auth.go:953`), KHÔNG từ claim `srole`
trong token. Tồn dư là **độ trễ cache 60s dùng chung cho mọi credential**: token mới cũng 200 trong cửa sổ, cả hai 403
sau đó. MR-A1 cần old=2xx VÀ fresh=403 — ở đây fresh=old luôn → oracle hai-credential (D1) không tách được, không nổ.
Giống lớp ZITADEL (`cve-survey/coverage.md` §2): credential mới cũng được chấp nhận.

Bản vá `5330755dbb`, ngay t=0s: `fresh(guest)=403` (flush cache tức thì) và `old(administrator)=401` (session bị thu hồi
— `terminateSessions`). → nếu oracle có chạy tới follow-up: old=401 INCONCLUSIVE → 0 FP.

### Hệ quả cho chọn ứng viên
Chủ đề commit §13 q16–q20 ("invalidate sessions/tokens on role change") chính là các app mà authz dựa trên DB/session
(lớp ZITADEL) hoặc có step-up — sai hình dạng cho MR-A1. MR-A1 nổ khi authz **mang theo trong credential** (claim role
được tin mà không tra DB, hoặc quyền gắn API-key): pyLoad, và nhánh JWT của wagoe (đúng hình dạng nhưng kẹt source
non-idempotent §14). Ứng viên kế nên ưu tiên authz-từ-claim, source idempotent, transition không step-up.

Caveat độ tin cậy giữ như §15. orkestra stack còn chạy nền; git tree đang ở bản vá.

## 17. Tiếp §15 theo tiêu chí tinh (ghi 10:08 10-01, trước khi mở diff nào)

Rút từ ba near-miss (wagoe §14, orkestra §16): oracle MR-A1 chỉ nổ khi authz **mang theo trong credential** — role/quyền
nằm trong JWT claim (hoặc gắn API-key) và được tin mà KHÔNG tra lại DB/session mỗi request. Fix kiểu "invalidate
sessions / flush cache" = authz dựa DB/session (lớp ZITADEL, không nổ). Fix kiểu "revoke/invalidate TOKENS/JWTs" = bản
dính tin token → đúng hình dạng.

Sàng lại shortlist §15 bằng ba điều kiện, xét theo thứ tự order, dừng ở 1 app qua:
- C-JWT: bản dính ủy quyền từ claim trong token, không tra DB/session mỗi request (đọc trên diff + code authz).
- C-SRC: có một admin-write **idempotent** gọi được làm source (PUT upsert / PATCH / thao tác lặp được), không phải chỉ
  create non-idempotent (ranh giới wagoe §14).
- C-STEP: transition (đổi role/quyền) KHÔNG đòi step-up/MFA re-proof (ranh giới orkestra §16 lý do #1).

Ứng viên JWT-theme trong order: #137 tibba, #194 open-kanban, #201 supply-chain, #205 artifact-keeper, #223 snaplink.
Kết quả mong đợi không ghi ở đây.

### Chọn §17: #205 artifact-keeper/artifact-keeper (ghi 10:12 10-01)

Xét #137 tibba và #205 artifact-keeper (cùng Rust, cùng C-JWT). Chọn artifact-keeper: 1097★ ("drop-in Artifactory",
app thật, không throwaway — đáng tin hơn tibba 1★), và mô tả MR-A1 rõ nhất:
- Commit `e64cc5c6` / parent `e56d3aa7e2` (dính). `#1821`: *"is_admin is baked into JWT claims at mint time with no DB
  recheck, so a demoted admin keeps admin authority until the token expires (default 30 min)."*
- Transition = `PATCH /users/{id}` `is_admin:false` (handler `update_user`, `backend/src/api/handlers/users.rs:455`).
- C-JWT ✓✓: bản dính đọc `is_admin` từ claim, không tra DB. Watermark credential-change (`auth_service.rs:310
  fetch_credential_change_watermark`) chỉ gồm password/totp, KHÔNG gồm privilege → token cũ (is_admin=true, iat sau
  watermark) vẫn hợp lệ → giữ admin. Bản vá thêm cột `privileges_changed_at` fold vào GREATEST → token cũ bị từ chối.
- Khác orkestra (§16): token MỚI sau demotion mint với is_admin=FALSE → bị từ chối. Tồn dư là credential-specific (nằm
  trong JWT cũ), KHÔNG phải cache dùng chung → token-cũ=2xx, token-mới=403 → đúng tín hiệu 970. C-STEP: patch update_user
  không có step-up (chờ xác nhận). C-SRC: cần admin-write idempotent khác PATCH /users (chờ xác nhận ở bước dựng).

## 18. artifact-keeper: dựng + kiểm tay MR-A1 XÁC NHẬN (ghi 11:40 10-01, sau khi kiểm)

Kết luận: lỗi MR-A1 THẬT, **credential-specific**, kiểm tay khớp trên bản dính. Đây là ứng viên công khai đầu tiên
ngoài pyLoad có hình dạng token-cũ=ALLOWED / token-mới=DENIED ổn định (hình dạng để 970 nổ). Khác orkestra (§16, cache
dùng chung) và wagoe (§14, source non-idempotent).

### Dựng (`infra/artifact-keeper-target/`)
- Clone `artifact-keeper/artifact-keeper`; bản dính `e56d3aa7e2`, bản vá `e64cc5c608` (#1821). Lịch sử tuyến tính.
- Dev stack: `docker-compose.local-dev.yml` + override `docker-compose.thesis.yml` (backend chỉ phụ thuộc postgres;
  bỏ expose 9090 vì host chiếm; `user: "0:0"` vì volume /data/storage root-owned; tắt opensearch/dtrack). Infra tối thiểu:
  postgres:18 + backend (rust:1.96 + cargo-watch, port 8080). OpenSearch/Dependency-Track optional, không dựng.
- Lệch luật build (ghi): dev image thiếu proto well-known types → thêm protoc chính thức v29.3 vào `Dockerfile.backend.dev`
  (dòng mốc THESIS), giống `Dockerfile.backend` production.

### Bootstrap (REST, không chọc DB)
- User admin mặc định `admin`/`admin` (`ADMIN_PASSWORD=admin`), `must_change_password` → setup middleware khoá mutation.
  Đổi qua `POST /api/v1/users/{id}/password` (được miễn khỏi khoá). Mật khẩu policy đòi ký tự đặc biệt → dùng
  `Thesis-Pass-1234`. Đổi mật khẩu bump watermark credential-change (giây) → chờ 2s trước khi re-login (tránh iat==watermark).
- SA tạo `victim` (is_admin=true) + `viewer` (is_admin=false) qua `POST /api/v1/users`. Login `POST /api/v1/auth/login`
  → `access_token` (JWT, claim `is_admin`, exp 30'). Config `infra/em-config/artifactkeeper-auth.yaml`.

### Kiểm tay MR-A1 (`em-results/artifactkeeper-20261001/handcheck-clean.sh`, log `handcheck-vuln-final2.log`)
source=follow-up=`POST /api/v1/users` (require_admin, non-idempotent); transition=`PATCH /api/v1/users/{id} {is_admin:false}`.
Bản dính `e56d3aa7`:
```
[A] victim login -> token cũ, claim is_admin=True
[B] token cũ: POST /users                -> 200  (ALLOWED quan sát được)
[C] viewer(is_admin=false): POST /users  -> 403  (guard = require_admin)
[D] admin PATCH /users/{victim} is_admin=false -> 200  (transition, KHÔNG step-up)
[E] login lại victim: claim is_admin=False ; POST /users -> 403  (chứng chỉ mới BỊ TỪ CHỐI)
[F] REPLAY token cũ: POST /users         -> 200  (LỖI MR-A1: token cũ vẫn admin)
poll +8/16/24/32s: old=200 fresh=403 ỔN ĐỊNH
```
Cơ chế (khớp mô tả vendor #1821 + code `middleware/auth.rs:153` `is_admin=claims.is_admin`): is_admin nằm trong JWT lúc
mint, không tra DB; watermark credential-change bản dính chỉ gồm password/totp, không gồm privilege → token cũ hợp lệ +
claim admin → vẫn admin tới khi hết hạn (30'). Token mới mint sau demotion mang is_admin=false → 403. Tồn dư
credential-specific (không phải cache 60s như orkestra: old giữ 200 ổn định, fresh 403 ngay).

### Ba điều kiện cho chạy máy
- C-JWT ✓ (xác nhận code + kiểm tay). C-STEP ✓ (transition PATCH is_admin không step-up, [D]=200).
- C-SRC còn mở: hand-check dùng POST /users (non-idempotent); oracle replay cùng request sẽ 409 (ranh giới wagoe). Có
  write require_admin idempotent (`update_permission`, `assign_role`) — builder có tự chọn được không thì phải chạy mới biết.

Còn lại: (a) kiểm bản vá `e64cc5c608` (token cũ phải bị từ chối → 0 FP); (b) chạy máy EvoMaster.

### Bản vá `e64cc5c608` (ghi 11:50 10-01, log `handcheck-fixed.log`)
Cùng bootstrap + chuỗi. [A]–[E] như bản dính (source 200, viewer 403, transition 200, fresh victim is_admin=False
→ 403). [F] REPLAY token cũ sau demotion -> **401** (token bị vô hiệu: iat < watermark mới gồm `privileges_changed_at`).
poll old=401/fresh=403 ổn định. → oracle follow-up token cũ = 401 INCONCLUSIVE → 0 FP trên bản vá.

Cặp vuln/fixed hoàn chỉnh, giống pyLoad: bản dính token-cũ=200 (970 kỳ vọng nổ), bản vá token-cũ=401 (không nổ).
Còn lại: chạy máy EvoMaster trên bản dính (rủi ro C-SRC: builder tự chọn source idempotent require_admin được không).

### Chạy máy EvoMaster trên bản dính `e56d3aa7` (protocol, ghi trước lượt chạy — 2026-10-01)
Mục tiêu: 970 có **tự** dựng được bộ ba và nổ trên bản dính không (C-SRC là câu hỏi mở).

Thiết lập. jar `ER-06b48c30` (sha `06b48c30...`). Bản dính phải wipe volume DB trước khi lên (bản vá đã migrate DB
lên version 131 `privileges_changed_at`; code bản dính thiếu 131 → sqlx `Migration(VersionMissing(131))` exit 1 →
`reseed.sh full` để migrate lại từ đầu). Backend qua proxy bắt traffic `capture_proxy.py 8212 -> localhost:8080`;
EvoMaster `--bbTargetUrl http://localhost:8212`, auth config trỏ login qua 8212 (đếm login mỗi tài khoản).
`--bbSwaggerUrl file://` openapi đã bỏ `DELETE /users/{id}` (chống xoá nhầm tài khoản). Oracle gốc (default
`statefulAuthzTwoCredentialJudgment=false`, như pyLoad/bamf), `--useExperimentalOracles true`,
`--extraPhaseBudgetPercentage 0.6`, `--ratePerMinute 600`, logback builder-debug.

Probe seed 1, `--maxTime 1200s` (search) + pha security ≤ 720s.

Luật dừng sớm (đọc log khi rơi xuống):
1. Nếu login victim/admin/viewer không đủ cả 3 trong traffic → dừng, sai thiết lập auth.
2. Nếu `Evaluated tests` < 390 (số operation) → ngân sách chưa phủ hết endpoint cho victim → tăng maxTime, không kết luận.
3. Nếu victim đã bị exercise mà pha security dựng **0 bộ ba** (0 dòng `Assembled`/`Discarded ... VOID`/
   `Discarded ... UNCONFIRMED`) → dừng, đọc builder-debug tìm source/transition builder xét, trước khi chạy loạt.
4. Nếu dựng được bộ ba nhưng 0 nổ 970 → đọc builder-debug xem source builder chọn; nếu là write non-idempotent
   (replay 409/4xx) thì đây là C-SRC/ranh giới wagoe, không phải oracle sai.

### Kết quả chạy máy — FN trên held-out (probe seed 1, `machine-probe/`, ghi 15:25 10-01)
jar ER-06b48c30, maxTime 1200s+pha security, 389 op, 1568 test, login victim 1027/admin 751/viewer 767, 0 máy ngủ.
**det970=0, assembled=0, VOID=8, unconfirmed=0.** Báo lỗi tìm được là code 100 (500 nội bộ), không phải 970.

Chẩn đoán (builder-debug `logs/seed1-1200s.log`):
- Source: builder nhận 44 endpoint `require_admin`. Chọn `POST /admin/analytics/snapshot`. Mọi attempt
  `codes 200/xxx/200` — source 2xx **và follow-up replay token-cũ 2xx**: tín hiệu vuln có mặt, máy quan sát được.
  C-SRC/wagoe KHÔNG cắn (source idempotent, replay 200 không 409).
- Transition: 8 ứng viên, builder chọn `POST /users/{id}/roles` (score 0.3, reducedRoleValues 5 — duy nhất có giá
  trị vai trò giảm được). Transition **chưa từng 2xx**: 5×422 (EvoMaster không dựng nổi body role/uuid), 2×403
  (operator=viewer), 1×400. → mọi bộ ba VOID vì transition ≠ 2xx.
- `PATCH /users/{id} {is_admin:false}` (transition kiểm-tay = 200) **không xuất hiện trong ứng viên transition**
  (grep = 0). Từ vựng builder nhận "giá trị vai trò" (enum/mảng, reducedRoleValues>0) nhưng không nhận boolean
  `is_admin` flip. Và roles ⟂ is_admin trong app này: đổi roles không hạ cờ is_admin chặn source.

→ FN trên app held-out công khai (lỗi MR-A1 thật, kiểm tay xác nhận §18). Cơ chế: **từ vựng transition thiếu
boolean admin-flip**. Cùng lớp FN với bamf ({email} param). Giữ nguyên held-out (chưa có thay đổi mã builder nào
viết theo app này).

### Thay đổi builder: nhận boolean admin-flip transition (ghi 16:00 10-01)
Neo corpus: `is_admin` boolean trong S108/S109, `admin:false` trong S210 — lỗ hổng rút lexicon, không overfit.
`RestSecurityBuilder.kt`: hằng `ADMIN_FLAG_FIELD_SIGNALS=[is_admin,isadmin,is_superuser,is_superadmin,is_staff]`;
`transitionScore=max(pathScore, 0.6 nếu hay chứa admin-flag)` thay `transitionPathScore` ở looksLike+rank+log;
harvest thêm nhánh BooleanGene→"false"; setter+keepOnlyTargetFields thêm ADMIN_FLAG. Chỉ cộng thêm, không bỏ nhánh cũ.
jar `AF-422f912b` (EMConfig options không đổi). artifact-keeper → nay thành target phát triển (mất held-out).

Self-test `infra/evomaster-ext/selftest/admin-flag-transition.sh` (8/8 PASS, exit 0): ARM1 jar mới trên vuln —
score-boost 0.6, reducedRoleValues=1, transition chosen PATCH:/users/{id}, bộ ba `statuses 200/200/200` nổ 970;
ARM2 jar ER cùng cấu hình KHÔNG nổ + KHÔNG boost (falsifiability). Đây là 970 **máy tự phát hiện** đầu tiên trên
artifact-keeper (focused). Còn lại: cổng hồi quy (reports-api/vampi/pyLoad) + chạy đầy đủ (vuln auto-970, fixed 0 FP).

### Chạy đầy đủ (dev target, jar AF, `artifactkeeper-machine-20261001/`, protocol ghi trước — 16:05 10-01)
389 op (bỏ DELETE /users/{id}), proxy 8212 đếm login, reseed full mỗi seed, oracle gốc (D1=false), extraPhase 0.6,
maxTime 600s. vuln seeds 1-5 (auto-970), rồi fixed seeds 1-3 (0 FP). Luật dừng sớm: seed 1 thiếu login một tài khoản
→ dừng; máy ngủ bất kỳ → dừng. Transition kỳ vọng builder tự chọn: PATCH:/users/{id} is_admin (score 0.6).

### KẾT QUẢ: 970 máy tự phát hiện trên artifact-keeper (vuln seed 1, 17:18 10-01)
jar AF, 389 op, maxTime 1200s, oracle gốc (D1=false). **det970=1, assembled=1, void=7, evaluated=1571,
login v:882/a:610/w:656, sleep=0.** Builder tự: transition chosen PATCH:/api/v1/users/{id} (is_admin, score 0.6),
45 guarded source (viewer 403), bộ ba `POST:/admin/analytics/snapshot victim 'victim' operator 'operator'
transition PATCH:/users/{id} statuses 200/200/200`. 7 VOID = viewer-làm-operator 403 (không tín hiệu, đúng).
Đây là 970 máy phát hiện trên app công khai vendor-confirmed, không tự gieo. Còn: seeds 2-5 (recall), fixed (0 FP), gate.

### Fix setter (reliability) + jar AF2 (ghi 19:35 10-01)
Recall AF 1/4 vì `is_admin` kiểu `["boolean","null"]` → wrapper NullableGene serialize null bất định (PATCH 200 nhưng
no-op → UNCONFIRMED, re-login probe chống FP đúng). Fix `setAdminFlagActive`: ép inner BooleanGene=false + activate
wrapper (walk-parent như clearRoleArrays, xử lý OptionalGene lồng NullableGene). jar AF2-6b5606d4. Self-test 9/9 PASS
(thêm `demote-body-false`: PATCH 200 có is_admin=false, 0 null). Chạy lại AF2 seeds 1-5 (AF cũ lưu runs-vuln-AF.csv).

### KẾT QUẢ CHỐT vuln (AF2, 21:40 10-01): recall 5/5
seeds 1-5 maxTime 1200s, mọi seed det970=1, assembled=1, void=7, unconfirmed=0, sleep=0, login cả 3 tài khoản.
Bộ ba mỗi seed: source POST:/admin/* (require_admin) / transition PATCH:/users/{id} is_admin=false (200) /
follow-up replay token cũ (200). 970 máy tự phát hiện 5/5 trên artifact-keeper vuln (389 op). jar AF2-6b5606d4.
Tiếp: fixed (0 FP) + cổng hồi quy.

### KẾT QUẢ CHỐT fixed (AF2, 00:00 10-02): 0/3 FP — cặp hoàn chỉnh
fixed seeds 1-3 (bản vá e64cc5c6), det970=0/assembled=0/void=8 toàn bộ. Attempt then chốt
(victim 'victim', operator 'operator'): `codes 200/200/401` — source 200, transition 200 (hạ quyền vẫn thành công như
vuln), follow-up token-cũ **401** (watermark privileges_changed_at vô hiệu) → VOID → không nổ. Cơ chế 0-FP đúng (do
watermark, không phải transition hỏng).

BẢNG CHỐT artifact-keeper (jar AF2-6b5606d4, 389 op, maxTime 1200s, oracle gốc D1=false):
| bản | 970 nổ | FP |
|---|---|---|
| vuln e56d3aa7 | 5/5 | — |
| fixed e64cc5c6 | — | 0/3 |
Máy tự phát hiện trên app công khai vendor-confirmed (artifact-keeper 1097★, #1821), ngoài lỗi tự gieo. Giống pyLoad.
Còn: cổng hồi quy reports-api/vampi trên AF2 (bắt buộc vì đổi cách dựng bộ ba) trước khi trích số vào luận văn.
