# Cẩm nang CLI

Các lệnh và cờ dùng trong hệ thống luận văn: gọi API bằng `curl`, đọc JSON bằng `jq`, quản lý container bằng `docker`,
chạy EvoMaster và replay test nó sinh ra. Mọi output chạy thật ngày 2026-10-19 trên máy tác giả, shell zsh; lệnh chạy
được cả trong bash.

Tái hiện lỗi trên từng hệ thống:

| Hệ thống | File | Cổng bản lỗi / bản vá |
|---|---|---|
| Tier-1 `reports-api` | `tier1-reports-api.md` | 8080 / 8081 |
| Tier-2 `vampi-seeded` | `tier2-vampi-seeded.md` | 5002 / 5003 |
| Tier-2b pyLoad CVE-2026-41133 | `tier2b-pyload.md` | 8090 / 8091 |

## 1. Công cụ

| Công cụ | Ở đâu | Dùng cho |
|---|---|---|
| `curl` | có sẵn trên macOS | gọi API |
| `jq` 1.7.1 | `/usr/bin/jq`, có sẵn trên macOS | lấy token, giải JWT, đọc `report.json` |
| `docker` | Docker Desktop | bật, xem log, vào trong container target |
| Java 17 | `/usr/libexec/java_home -v 17` | chạy jar EvoMaster |
| Python có `pytest` | `infra/em-results/tier1-clean-remeasure/.replay-venv/` | replay test EvoMaster sinh ra |

## 2. curl

### 2.1 Cờ

| Cờ | Làm gì | Ví dụ |
|---|---|---|
| `-X <METHOD>` | đặt method | `-XDELETE`, `-XPUT`, `-XPOST` |
| `-H '<Tên>: <giá trị>'` | thêm header | `-H "Authorization: Bearer $OLD"` |
| `-d '<thân>'` | gửi thân request | `-d '{"role":"VIEWER"}'` |
| `-s` | tắt thanh tiến trình và thông báo lỗi | luôn dùng khi lấy giá trị vào biến |
| `-o /dev/null` | bỏ thân phản hồi | khi chỉ cần mã trạng thái |
| `-w '<mẫu>'` | in thêm sau khi xong | `-w '%{http_code}\n'` |
| `-c <file>` | lưu cookie phản hồi vào file | đăng nhập pyLoad |
| `-b <file>` | gửi cookie đọc từ file | gọi pyLoad bằng phiên đã lưu |
| `-i` | in header phản hồi | xem `Set-Cookie`, `Location` |
| `-v` | in cả request lẫn phản hồi | soát header đã gửi |
| `--max-time <giây>` | dừng nếu quá lâu | `--max-time 3` khi kiểm app sống |

Biến trong `-w`:

| Biến | Ra |
|---|---|
| `%{http_code}` | mã trạng thái, `000` nếu không kết nối được |
| `%{redirect_url}` | địa chỉ `Location` của phản hồi 302 |

### 2.2 Mẫu lệnh

In mã trạng thái:

```
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8080/v3/api-docs
```

```
200
```

In thân rồi mã trạng thái trên dòng riêng:

```
curl -s -w '\n%{http_code}\n' -XDELETE http://localhost:8081/reports/99
```

```
{"error":"missing or malformed token"}
401
```

Gửi JSON thì phải kèm `Content-Type`:

```
curl -s -XPOST http://localhost:8080/auth/login -H 'Content-Type: application/json' -d '{"username":"alice","password":"alicepass"}'
```

Gửi form thì không cần header, `-d` tự đặt `application/x-www-form-urlencoded`:

```
curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' -c alice.txt -XPOST http://localhost:8090/login -d 'username=alice&password=alicepass'
```

```
302 http://localhost:8090/dashboard
```

### 2.3 Hai cách mang thông tin đăng nhập

| Cách | Target | Lấy | Gửi |
|---|---|---|---|
| Bearer JWT | Tier-1, Tier-2 | đọc field token trong thân phản hồi đăng nhập | `-H "Authorization: Bearer $TOKEN"` |
| Cookie phiên | pyLoad | `-c file` lúc đăng nhập | `-b file` |

Tái hiện MR-A1 cần giữ thông tin đăng nhập cấp trước lúc hạ quyền. Với Bearer, giữ biến `OLD` và không gán lại. Với
cookie, giữ file cookie cũ và đăng nhập lại vào một file khác.

## 3. jq

| Lệnh | Làm gì |
|---|---|
| `jq -r .token` | lấy field `token`, bỏ ngoặc kép |
| `jq -c .` | in JSON trên một dòng |
| `jq -c '[.users[] \| {username, admin}]'` | chỉ giữ hai field của mỗi phần tử |
| `jq -R 'split(".")[1] \| @base64d \| fromjson'` | giải phần giữa của JWT |

Lưu token vào biến:

```
OLD=$(curl -s -XPOST http://localhost:8080/auth/login -H 'Content-Type: application/json' -d '{"username":"alice","password":"alicepass"}' | jq -r .token)
```

Giải JWT để xem vai trò được ghi lúc đăng nhập:

```
jq -R 'split(".")[1] | @base64d | fromjson' <<< "$OLD"
```

```
{
  "sub": "alice",
  "role": "ADMIN",
  "iat": 1792422244,
  "exp": 1792425844
}
```

`-R` đọc đầu vào là chuỗi thô. `split(".")[1]` lấy phần payload. `@base64d` giải base64. `fromjson` đổi chuỗi thành JSON.

## 4. Biến và hàm shell

```
H=http://localhost:8080
J='Content-Type: application/json'
curl -s -XPOST $H/reset
```

- `$(...)` lấy output của lệnh làm giá trị.
- Header có biến thì dùng ngoặc kép (`"Authorization: Bearer $OLD"`). Thân JSON không có biến thì dùng ngoặc đơn.
- Mỗi file tái hiện có một hàm `a1…` chạy cả chuỗi. Dán hàm vào terminal một lần rồi gọi theo tên; hàm mất khi đóng
  terminal.
- Trong zsh, chữ `=` đứng đầu một từ bị hiểu là tìm lệnh: `echo =====` báo `not found`. Đặt nó trong ngoặc đơn.

## 5. docker

| Lệnh | Làm gì |
|---|---|
| `docker ps --format '{{.Names}}\t{{.Ports}}\t{{.Status}}'` | liệt kê container đang chạy |
| `docker start <tên>...` | bật lại container đã dừng |
| `docker logs --tail 20 <tên>` | 20 dòng log cuối |
| `docker exec <tên> <lệnh>` | chạy lệnh trong container |
| `docker inspect <tên> --format '{{.Config.Env}}'` | xem biến môi trường, để biết đâu là bản vá |

Container của ba target:

| Container | Cổng | Bản | Khác bản lỗi ở |
|---|---|---|---|
| `reports-api` | 8080 | Tier-1 lỗi | |
| `reports-api-fixed` | 8081 | Tier-1 vá | `APP_SECURITY_STATEFUL_ROLE_CHECK=true` |
| `vampi-seeded` | 5002 | Tier-2 lỗi | |
| `vampi-seeded-fixed` | 5003 | Tier-2 vá | `statefulrolecheck=1` |
| `pyload-vuln` | 8090 | Tier-2b lỗi | |
| `pyload-fixed` | 8091 | Tier-2b vá | image dựng với `--build-arg STATEFUL_ROLE_CHECK=1`; env ghi `PYLOAD_STATEFUL_ROLE_CHECK=1` |

Kiểm sáu cổng còn sống:

```
for p in 8080 8081 5002 5003 8090 8091; do curl -s -o /dev/null --max-time 3 -w "$p %{http_code}\n" http://localhost:$p/; done
```

```
8080 401
8081 401
5002 200
5003 200
8090 302
8091 302
```

`000` nghĩa là container đã dừng. Mã khác `000` là app đang trả lời: `/` của Tier-1 đòi token nên ra `401`, của pyLoad
chuyển về trang đăng nhập nên ra `302`.

## 6. Đọc mã trạng thái theo oracle

Theo `CLAUDE.md` §3:

| Mã | Oracle đọc là |
|---|---|
| 2xx | ALLOWED |
| 403 | DENIED |
| 401 | INCONCLUSIVE |
| 404, 400, 302, mã khác | không phải từ chối |

Một bộ ba chỉ kết luận được khi source 2xx và transition 2xx. Mỗi file tái hiện có bảng mã trạng thái riêng của app đó.

## 7. EvoMaster

### 7.1 Một lượt chạy

Lệnh của một hàng Tier-1 bản lỗi, không reset, jar P2f, giống hàm `t1` trong
`infra/em-results/p2f-full-20261015/p2f_full.sh`:

```
curl -s -o /dev/null -XPOST http://localhost:8080/reset
JAVA_HOME=$(/usr/libexec/java_home -v 17) java -jar /Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-P2f-64ee8ffc.jar \
  --blackBox true \
  --bbSwaggerUrl http://localhost:8080/v3/api-docs --bbTargetUrl http://localhost:8080 \
  --configPath infra/em-config/reports-auth.yaml \
  --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
  --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed 1 \
  --outputFolder infra/em-results/<thư-mục-mới>/t1-vuln-seed1
```

Lệnh cho Tier-2 và pyLoad nằm cuối file tái hiện của từng target.

### 7.2 Cờ upstream

| Cờ | Giá trị ta dùng | Làm gì |
|---|---|---|
| `--blackBox` | `true` | chạy không cần driver; EvoMaster chỉ thấy HTTP |
| `--bbSwaggerUrl` | URL spec, hoặc `file://…` | spec OpenAPI để sinh request |
| `--bbTargetUrl` | `http://localhost:<cổng>` | địa chỉ gửi request |
| `--configPath` | `infra/em-config/<target>-auth.yaml` | danh sách tài khoản và cách đăng nhập |
| `--useExperimentalOracles` | `true` | bật oracle thử nghiệm, trong đó có 970 |
| `--extraPhaseBudgetPercentage` | `0.6` | mỗi pha sau tìm kiếm (security, minimization) được tối đa 60% `--maxTime` |
| `--outputFormat` | `PYTHON_UNITTEST` | test sinh ra bằng Python |
| `--ratePerMinute` | `120`; pyLoad `200` | giới hạn số request mỗi phút |
| `--maxTime` | `150s`; pyLoad `10m` | thời gian tìm kiếm, tính theo đồng hồ treo tường |
| `--seed` | `1`–`20` | hạt giống ngẫu nhiên |
| `--outputFolder` | thư mục mới | nơi ghi test và `report.json` |
| `--endpointExclude` | `"/api/kill,/api/restart"` (pyLoad) | bỏ endpoint, ở đây là hai endpoint tắt app |

### 7.3 Cờ luận văn thêm

Chỉ có trong P2f và các jar trước (`EMConfig.kt:3044–3077` ở commit `f73010103b`), không có trong EvoMaster upstream.
Jar SR và HEAD `1cd0d091f4` đã gỡ cả ba cờ và báo `is not a recognized option`.

| Cờ | Mặc định | Làm gì |
|---|---|---|
| `--statefulAuthzResetEndpoint "<VERB> <URL>"` | rỗng | gọi endpoint reset trước mỗi lần dựng bộ ba; arm "có reset" của bảng số |
| `--statefulAuthzTransition "<VERB> <PATH> k=v ..."` | rỗng | khai báo tay lời gọi hạ quyền; arm dùng cờ này không đo recall |
| `--statefulAuthzTwoCredentialJudgment` | `false` | phán quyết D1 bằng token cũ và token mới |

Endpoint reset của ba target: `POST http://localhost:8080/reset`, `GET http://localhost:5002/createdb`,
`POST http://localhost:8090/thesis/reset`.

### 7.4 Đọc kết quả

Thư mục output có `EvoMaster_faults_Test.py`, `EvoMaster_others_Test.py`, `EvoMaster_successes_Test.py`, `report.json`,
`index.html`.

Đếm lỗi theo mã:

```
jq -c '[.faults.foundFaults[]? | .faultCategories[]?.code] | group_by(.) | map({(.[0]|tostring): length}) | add' <thư-mục>/report.json
```

Trên `infra/em-results/p2f-full-20261015/tests/t1-vuln-seed1-r0`:

```
{"205":1,"970":1}
```

Tìm test mang lỗi 970:

```
grep -n "Fault970\|def test_.*stillAllowed" <thư-mục>/EvoMaster_faults_Test.py
```

```
57:    def test_0_put_on_report_stillAllowedAfterPermissionRevoked(self):
140:        # Fault970. Stateful Authorization: privilege persists after a permission-reducing transition.
```

### 7.5 Replay một test

Reset target trước, rồi chạy đúng một test. `PYTHONDONTWRITEBYTECODE=1` và `-p no:cacheprovider` giữ thư mục kết quả
không bị ghi thêm `__pycache__` hay `.pytest_cache`.

```
V=/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/em-results/tier1-clean-remeasure/.replay-venv
cd infra/em-results/p2f-full-20261015/tests/t1-vuln-seed1-r0
curl -s -o /dev/null -XPOST http://localhost:8080/reset
PYTHONDONTWRITEBYTECODE=1 $V/bin/python -m pytest -q -p no:cacheprovider "EvoMaster_faults_Test.py::EvoMaster_faults_Test::test_0_put_on_report_stillAllowedAfterPermissionRevoked"
```

```
1 passed in 0.10s
```

Địa chỉ target nằm cứng trong test (`baseUrlOfSut = "http://localhost:8080"`). Chạy cả file một lần thì test sau chạy
trên trạng thái test trước để lại, nên có thể trượt; replay từng test, reset trước mỗi test.

### 7.6 Luật khi chạy

- Mỗi lúc một việc nặng: một lượt EvoMaster, `mvn`, `docker build` hoặc `pytest`. Hook `.claude/hooks/guard.py` chặn
  việc thứ hai khi một batch đang chạy.
- Reset target trước mỗi lượt.
- Mỗi batch một thư mục mới trong `infra/em-results/`; xong thì snapshot sang `~/thesis-backups/`.
- Batch dài chạy dưới `caffeinate -dims` và để mở nắp máy: máy ngủ làm hỏng hàng đang chạy vì `--maxTime` vẫn đếm.
- Quy trình batch đầy đủ: skill `em-batch`.
