# Tái hiện lỗi trên Tier-2 `vampi-seeded`

Cờ và cú pháp lệnh: `cli.md`. Output chạy thật ngày 2026-10-19.

## 1. Lỗi

`admin` là ADMIN và đăng nhập lấy token. `superadmin` hạ `admin` xuống `user`. Trên bản lỗi, token cũ của `admin` vẫn
sửa được secret của sách. Bản vá trả 403.

App là bản fork của VAmPI (`erev0s/VAmPI` @ `f16052dc`) có gieo lỗi; mọi dòng gieo mang mốc `THESIS SEED`
(`infra/vampi-seeded/THESIS-SEED.md`).

- Lúc đăng nhập, JWT được ghi thêm claim `admin` (`infra/vampi-seeded/models/user_model.py:38`).
- `is_caller_admin()` ở `infra/vampi-seeded/api_views/users.py:19–32` là chỗ quyết định duy nhất. Bản lỗi tin claim
  `admin` trong token (dòng 32). Bản vá đọc lại user trong DB ở mỗi request (dòng 29–31).

Hai container chạy cùng một image. Bản vá thêm biến môi trường `statefulrolecheck=1`. Token sống 3600 giây
(`tokentimetolive`; VAmPI gốc để 60).

## 2. Target

| | Bản lỗi | Bản vá |
|---|---|---|
| Container | `vampi-seeded` | `vampi-seeded-fixed` |
| Cổng | 5002 | 5003 |
| Spec | `http://localhost:5002/openapi.json` | `http://localhost:5003/openapi.json` |
| Reset | `GET /createdb` | `GET /createdb` |

| Tài khoản | Mật khẩu | Vai trò | Dùng làm |
|---|---|---|---|
| `admin` | `pass1` | admin | nạn nhân bị hạ |
| `superadmin` | `pass1` | admin | người hạ |
| `name1` | `pass1` | user | đối chứng âm |
| `name2` | `pass2` | user | |

Sau `GET /createdb` có 4 sách: `bookTitle1` của `name1`, `bookTitle2` của `name2`, `bookTitle3` của `admin`,
`bookTitle4` của `superadmin`.

| Method | Path | Ai được gọi |
|---|---|---|
| `POST` | `/users/v1/login` | ai cũng được; token ở field `auth_token` |
| `PUT` | `/books/v1/{book_title}/secret` | admin; thân `{"secret":"..."}` |
| `PUT` | `/users/v1/{username}/role` | admin; thân `{"role":"admin"}` hoặc `{"role":"user"}` |
| `GET` | `/users/v1/_debug` | ai cũng được; endpoint có sẵn của VAmPI, in cả mật khẩu |
| `GET` | `/createdb` | ai cũng được |

## 3. Từng bước

Đổi `5002` thành `5003` để chạy bản vá.

```
H=http://localhost:5002
J='Content-Type: application/json'
```

**Bước 1. Reset.**

```
curl -s $H/createdb
```

```
{ "message": "Database populated." }
```

**Bước 2. `admin` và `superadmin` đăng nhập, giữ token.**

```
OLD=$(curl -s -XPOST $H/users/v1/login -H "$J" -d '{"username":"admin","password":"pass1"}' | jq -r .auth_token)
ADM=$(curl -s -XPOST $H/users/v1/login -H "$J" -d '{"username":"superadmin","password":"pass1"}' | jq -r .auth_token)
jq -R 'split(".")[1] | @base64d | fromjson' <<< "$OLD"
```

```
{
  "exp": 1792426363,
  "iat": 1792422763,
  "sub": "admin",
  "admin": true
}
```

**Bước 3. Source: `admin` sửa secret của `bookTitle3` bằng token cũ.**

```
curl -s -w '\n%{http_code}\n' -XPUT $H/books/v1/bookTitle3/secret -H "Authorization: Bearer $OLD" -H "$J" -d '{"secret":"s1"}'
```

```
{"message": "Book secret updated.", "status": "success"}
200
```

**Bước 4. Transition: `superadmin` hạ `admin` xuống `user`.**

```
curl -s -w '\n%{http_code}\n' -XPUT $H/users/v1/admin/role -H "Authorization: Bearer $ADM" -H "$J" -d '{"role":"user"}'
curl -s $H/users/v1/_debug | jq -c '[.users[] | {username, admin}]'
```

```
{"data": {"role": "user", "username": "admin"}, "status": "success"}
200
[{"username":"name1","admin":false},{"username":"name2","admin":false},{"username":"admin","admin":false},{"username":"superadmin","admin":true}]
```

Lệnh thứ hai xác nhận DB đã ghi `admin: false` cho `admin`.

**Bước 5. Follow-up: token cũ của `admin` sửa secret lần nữa.**

```
curl -s -w '\n%{http_code}\n' -XPUT $H/books/v1/bookTitle3/secret -H "Authorization: Bearer $OLD" -H "$J" -d '{"secret":"s2"}'
```

| 5002 bản lỗi | 5003 bản vá |
|---|---|
| `{"message": "Book secret updated.", "status": "success"}` `200` (lỗi) | `{ "status": "fail", "message": "Only Admins may edit book secrets!"}` `403` |

**Bước 6. Đối chứng: `admin` đăng nhập lại, gửi đúng lời gọi ở bước 5.**

```
NEW=$(curl -s -XPOST $H/users/v1/login -H "$J" -d '{"username":"admin","password":"pass1"}' | jq -r .auth_token)
jq -c -R 'split(".")[1] | @base64d | fromjson' <<< "$NEW"
curl -s -w '\n%{http_code}\n' -XPUT $H/books/v1/bookTitle3/secret -H "Authorization: Bearer $NEW" -H "$J" -d '{"secret":"s3"}'
```

Token mới mang `"admin": false`. Cả hai bản trả:

```
{ "status": "fail", "message": "Only Admins may edit book secrets!"}
403
```

**Bước 7. Reset.**

```
curl -s $H/createdb
```

Trên 5002, bước 3–6 khớp đủ bốn điều kiện nổ 970 của jar P2f.

## 4. Lời gọi phụ

Chạy sau bước 4, trước bước 7.

```
U1=$(curl -s -XPOST $H/users/v1/login -H "$J" -d '{"username":"name1","password":"pass1"}' | jq -r .auth_token)
curl -s -w '\n%{http_code}\n' -XPUT $H/books/v1/bookTitle3/secret -H "Authorization: Bearer $U1" -H "$J" -d '{"secret":"x"}'
curl -s -w '\n%{http_code}\n' -XPUT $H/books/v1/bookTitle3/secret -H "$J" -d '{"secret":"x"}'
```

| Lời gọi | 5002 | 5003 |
|---|---|---|
| sửa secret, token `name1` | `403` | `403` |
| sửa secret, không token | `401` | `401` |

## 5. Một lệnh

Dán vào terminal một lần, rồi gọi `a1v 5002` hoặc `a1v 5003`. Hàm tự reset trước và sau.

```
a1v() {
  local H=http://localhost:${1:-5002}
  local J='Content-Type: application/json'
  curl -s -o /dev/null $H/createdb
  local OLD=$(curl -s -XPOST $H/users/v1/login -H "$J" -d '{"username":"admin","password":"pass1"}' | jq -r .auth_token)
  local ADM=$(curl -s -XPOST $H/users/v1/login -H "$J" -d '{"username":"superadmin","password":"pass1"}' | jq -r .auth_token)
  local s=$(curl -s -o /dev/null -w '%{http_code}' -XPUT $H/books/v1/bookTitle3/secret -H "Authorization: Bearer $OLD" -H "$J" -d '{"secret":"s1"}')
  local t=$(curl -s -o /dev/null -w '%{http_code}' -XPUT $H/users/v1/admin/role -H "Authorization: Bearer $ADM" -H "$J" -d '{"role":"user"}')
  local o=$(curl -s -o /dev/null -w '%{http_code}' -XPUT $H/books/v1/bookTitle3/secret -H "Authorization: Bearer $OLD" -H "$J" -d '{"secret":"s2"}')
  local NEW=$(curl -s -XPOST $H/users/v1/login -H "$J" -d '{"username":"admin","password":"pass1"}' | jq -r .auth_token)
  local n=$(curl -s -o /dev/null -w '%{http_code}' -XPUT $H/books/v1/bookTitle3/secret -H "Authorization: Bearer $NEW" -H "$J" -d '{"secret":"s3"}')
  curl -s -o /dev/null $H/createdb
  echo "source      admin token cũ   PUT /books/v1/bookTitle3/secret  $s"
  echo "transition  superadmin       PUT /users/v1/admin/role user    $t"
  echo "follow-up   admin token cũ   PUT /books/v1/bookTitle3/secret  $o"
  echo "đối chứng   admin token mới  PUT /books/v1/bookTitle3/secret  $n"
  if [[ $s == 2* && $t == 2* && $o == 2* && $n == 403 ]]; then
    echo "MR-A1 bị vi phạm: token cũ vẫn sửa được secret sau khi admin bị hạ"
  else
    echo "MR-A1 giữ: token cũ không còn quyền ghi"
  fi
}
```

`a1v 5002`:

```
source      admin token cũ   PUT /books/v1/bookTitle3/secret  200
transition  superadmin       PUT /users/v1/admin/role user    200
follow-up   admin token cũ   PUT /books/v1/bookTitle3/secret  200
đối chứng   admin token mới  PUT /books/v1/bookTitle3/secret  403
MR-A1 bị vi phạm: token cũ vẫn sửa được secret sau khi admin bị hạ
```

`a1v 5003`:

```
source      admin token cũ   PUT /books/v1/bookTitle3/secret  200
transition  superadmin       PUT /users/v1/admin/role user    200
follow-up   admin token cũ   PUT /books/v1/bookTitle3/secret  403
đối chứng   admin token mới  PUT /books/v1/bookTitle3/secret  403
MR-A1 giữ: token cũ không còn quyền ghi
```

## 6. Mã trạng thái của app

Kiểm quyền chạy trước kiểm tồn tại: user thường sửa sách không tồn tại vẫn nhận 403.

| Mã | Nghĩa | Ví dụ thật trên 5003 |
|---|---|---|
| `401` | thiếu token | không header: `"detail": "No authorization token provided"` |
| `400` | thân sai spec | `{"role":"viewer"}`: `"'viewer' is not one of ['admin', 'user'] - 'role'"`; thân `{}`: `"'secret' is a required property"` |
| `403` | bị chặn ở quyền | `name1` sửa secret `nope`: `"Only Admins may edit book secrets!"` |
| `404` | đã qua kiểm quyền, không có đối tượng | `superadmin` sửa secret `nope`: `"Book not found!"`; đổi vai trò `ghost`: `"User not found!"` |

## 7. Sự cố

| Triệu chứng | Nguyên nhân | Cách xử lý |
|---|---|---|
| `000` | container dừng | `docker start vampi-seeded vampi-seeded-fixed` |
| `jq` báo lỗi khi lấy token | đăng nhập hỏng, phản hồi không có `auth_token` | gọi lại lệnh đăng nhập không qua `jq` để đọc lỗi |
| bước 3 ra `403` | lần trước chưa reset, `admin` vẫn là `user` | chạy lại bước 1 và 2 |
| bước 5 trên 5002 ra `403` | `OLD` bị gán lại sau bước 4 | lấy token ở bước 2, trước bước 4 |

## 8. Chạy EvoMaster

Giống hàm `t2` trong `infra/em-results/p2f-full-20261015/p2f_full.sh`. Cờ: `cli.md` §7.

```
curl -s -o /dev/null http://localhost:5002/createdb
JAVA_HOME=$(/usr/libexec/java_home -v 17) java -jar /Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-P2f-64ee8ffc.jar \
  --blackBox true \
  --bbSwaggerUrl http://localhost:5002/openapi.json --bbTargetUrl http://localhost:5002 \
  --configPath infra/em-config/vampi-seeded-auth.yaml \
  --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
  --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed 1 \
  --outputFolder infra/em-results/<thư-mục-mới>/t2-vuln-seed1
```

Arm có reset, chỉ chạy được trên P2f và các jar trước, thêm
`--statefulAuthzResetEndpoint "GET http://localhost:5002/createdb"`.
