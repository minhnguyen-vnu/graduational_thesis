# Tái hiện lỗi trên Tier-1 `reports-api`

Cờ và cú pháp lệnh: `cli.md`. Output chạy thật ngày 2026-10-19.

## 1. Lỗi

alice là ADMIN và đăng nhập lấy token. superadmin hạ alice xuống VIEWER. Trên bản lỗi, token alice lấy trước lúc bị hạ
vẫn xoá được báo cáo. Bản vá trả 403.

`infra/reports-api/src/main/java/com/thesis/reportsapi/security/AuthFilter.java:85–93`:

- Bản lỗi lấy vai trò từ claim `role` trong JWT (dòng 92). Claim được ghi lúc đăng nhập và không đổi khi vai trò đổi.
- Bản vá đọc vai trò hiện tại trong kho user ở mỗi request (dòng 86–90).

Hai container chạy cùng một image. Bản vá thêm biến môi trường `APP_SECURITY_STATEFUL_ROLE_CHECK=true`. Token sống 3600
giây (`app.jwt.ttl-seconds`).

## 2. Target

| | Bản lỗi | Bản vá |
|---|---|---|
| Container | `reports-api` | `reports-api-fixed` |
| Cổng | 8080 | 8081 |
| Spec | `http://localhost:8080/v3/api-docs` | `http://localhost:8081/v3/api-docs` |
| Reset | `POST /reset` | `POST /reset` |

| Tài khoản | Mật khẩu | Vai trò | Dùng làm |
|---|---|---|---|
| `alice` | `alicepass` | ADMIN | nạn nhân bị hạ |
| `superadmin` | `superpass` | ADMIN | người hạ |
| `bob` | `bobpass` | VIEWER | đối chứng âm |

Sau `POST /reset` app có báo cáo id 1–5; id mới tiếp theo là 6.

| Method | Path | Ai được gọi |
|---|---|---|
| `POST` | `/auth/login` | ai cũng được; token ở field `token` |
| `GET` | `/reports`, `/reports/{id}`, `/users/me` | mọi tài khoản đã đăng nhập |
| `POST`, `PUT`, `DELETE` | `/reports`, `/reports/{id}` | ADMIN |
| `PUT` | `/users/{username}/role` | ADMIN; thân `{"role":"ADMIN"}` hoặc `{"role":"VIEWER"}` |
| `POST` | `/reset` | ai cũng được |

## 3. Từng bước

Đổi `8080` thành `8081` để chạy bản vá.

```
H=http://localhost:8080
J='Content-Type: application/json'
```

**Bước 1. Reset.**

```
curl -s -XPOST $H/reset
```

```
{"status":"reset"}
```

**Bước 2. alice và superadmin đăng nhập, giữ token.**

```
OLD=$(curl -s -XPOST $H/auth/login -H "$J" -d '{"username":"alice","password":"alicepass"}' | jq -r .token)
ADM=$(curl -s -XPOST $H/auth/login -H "$J" -d '{"username":"superadmin","password":"superpass"}' | jq -r .token)
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

**Bước 3. Source: alice xoá báo cáo 1 bằng token cũ.**

```
curl -s -o /dev/null -w '%{http_code}\n' -XDELETE $H/reports/1 -H "Authorization: Bearer $OLD"
```

Ra `204` trên cả hai bản.

**Bước 4. Transition: superadmin hạ alice xuống VIEWER.**

```
curl -s -w '\n%{http_code}\n' -XPUT $H/users/alice/role -H "Authorization: Bearer $ADM" -H "$J" -d '{"role":"VIEWER"}'
```

```
{"username":"alice","role":"VIEWER"}
200
```

**Bước 5. Follow-up: token cũ của alice xoá báo cáo 2.**

```
curl -s -o /dev/null -w '%{http_code}\n' -XDELETE $H/reports/2 -H "Authorization: Bearer $OLD"
```

| 8080 bản lỗi | 8081 bản vá |
|---|---|
| `204` (lỗi) | `403` |

**Bước 6. Đối chứng: alice đăng nhập lại, gửi đúng lời gọi ở bước 5.**

```
NEW=$(curl -s -XPOST $H/auth/login -H "$J" -d '{"username":"alice","password":"alicepass"}' | jq -r .token)
jq -R 'split(".")[1] | @base64d | fromjson' <<< "$NEW"
curl -s -w '\n%{http_code}\n' -XDELETE $H/reports/2 -H "Authorization: Bearer $NEW"
```

Token mới mang `"role": "VIEWER"`. Cả hai bản trả:

```
{"error":"admin role required"}
403
```

**Bước 7. Reset.**

```
curl -s -XPOST $H/reset
```

Trên 8080, bước 3–6 khớp đủ bốn điều kiện nổ 970 của jar P2f: source 2xx, transition 2xx, follow-up bằng token cũ 2xx,
follow-up bằng token mới 403. Ở bước 6, đăng nhập lại cấp token VIEWER và lỗi không còn hiện ra.

## 4. Lời gọi phụ

Chạy sau bước 4, trước bước 7.

```
curl -s $H/users/me -H "Authorization: Bearer $OLD"
curl -s -w '\n%{http_code}\n' -XPOST $H/reports -H "Authorization: Bearer $OLD" -H "$J" -d '{"title":"t","classification":"PUBLIC"}'
BOB=$(curl -s -XPOST $H/auth/login -H "$J" -d '{"username":"bob","password":"bobpass"}' | jq -r .token)
curl -s -w '\n%{http_code}\n' -XDELETE $H/reports/3 -H "Authorization: Bearer $BOB"
curl -s -w '\n%{http_code}\n' -XDELETE $H/reports/3
```

| Lời gọi | 8080 bản lỗi | 8081 bản vá |
|---|---|---|
| `GET /users/me`, token cũ alice | `{"username":"alice","role":"ADMIN"}` | `{"username":"alice","role":"VIEWER"}` |
| `POST /reports`, token cũ alice | `201`, báo cáo id 6, `owner` là `alice` | `403` |
| `DELETE /reports/3`, token bob | `403` | `403` |
| `DELETE /reports/3`, không token | `401` | `401` |

## 5. Một lệnh

Dán vào terminal một lần, rồi gọi `a1 8080` hoặc `a1 8081`. Hàm tự reset trước và sau.

```
a1() {
  local H=http://localhost:${1:-8080}
  local J='Content-Type: application/json'
  curl -s -o /dev/null -XPOST $H/reset
  local OLD=$(curl -s -XPOST $H/auth/login -H "$J" -d '{"username":"alice","password":"alicepass"}' | jq -r .token)
  local ADM=$(curl -s -XPOST $H/auth/login -H "$J" -d '{"username":"superadmin","password":"superpass"}' | jq -r .token)
  local s=$(curl -s -o /dev/null -w '%{http_code}' -XDELETE $H/reports/1 -H "Authorization: Bearer $OLD")
  local t=$(curl -s -o /dev/null -w '%{http_code}' -XPUT $H/users/alice/role -H "Authorization: Bearer $ADM" -H "$J" -d '{"role":"VIEWER"}')
  local o=$(curl -s -o /dev/null -w '%{http_code}' -XDELETE $H/reports/2 -H "Authorization: Bearer $OLD")
  local NEW=$(curl -s -XPOST $H/auth/login -H "$J" -d '{"username":"alice","password":"alicepass"}' | jq -r .token)
  local n=$(curl -s -o /dev/null -w '%{http_code}' -XDELETE $H/reports/2 -H "Authorization: Bearer $NEW")
  curl -s -o /dev/null -XPOST $H/reset
  echo "source      alice token cũ   DELETE /reports/1            $s"
  echo "transition  superadmin       PUT /users/alice/role VIEWER $t"
  echo "follow-up   alice token cũ   DELETE /reports/2            $o"
  echo "đối chứng   alice token mới  DELETE /reports/2            $n"
  if [[ $s == 2* && $t == 2* && $o == 2* && $n == 403 ]]; then
    echo "MR-A1 bị vi phạm: token cũ vẫn xoá được sau khi alice bị hạ"
  else
    echo "MR-A1 giữ: token cũ không còn quyền ghi"
  fi
}
```

`a1 8080`:

```
source      alice token cũ   DELETE /reports/1            204
transition  superadmin       PUT /users/alice/role VIEWER 200
follow-up   alice token cũ   DELETE /reports/2            204
đối chứng   alice token mới  DELETE /reports/2            403
MR-A1 bị vi phạm: token cũ vẫn xoá được sau khi alice bị hạ
```

`a1 8081`:

```
source      alice token cũ   DELETE /reports/1            204
transition  superadmin       PUT /users/alice/role VIEWER 200
follow-up   alice token cũ   DELETE /reports/2            403
đối chứng   alice token mới  DELETE /reports/2            403
MR-A1 giữ: token cũ không còn quyền ghi
```

## 6. Mã trạng thái của app

App kiểm theo thứ tự: token (401), thân request (400), quyền (403), tồn tại (404).

| Mã | Nghĩa | Ví dụ thật trên 8081 |
|---|---|---|
| `401` | thiếu token, token hỏng hoặc hết hạn | `Bearer ` rỗng: `{"error":"missing or malformed token"}` |
| `400` | thân sai, chưa tới bước kiểm quyền | bob `POST /reports` với `{}`: `{"error":"classification must not be null"}` |
| `400` | vai trò viết thường | `{"role":"viewer"}`: `{"error":"invalid role"}` |
| `403` | bị chặn ở quyền | bob `DELETE /reports/99`: `{"error":"admin role required"}` |
| `404` | đã qua kiểm quyền, id không tồn tại | superadmin `DELETE /reports/99`: `{"error":"report not found"}` |

Follow-up có thân sai trả 400 với mọi token, nên không cho biết gì về quyền.

## 7. Sự cố

| Triệu chứng | Nguyên nhân | Cách xử lý |
|---|---|---|
| `000`, `curl` thoát mã 7 | container dừng | `docker start reports-api reports-api-fixed` |
| bước 3 ra `401` | đăng nhập hỏng, `OLD` rỗng | `echo $OLD`, chạy lại bước 2 |
| bước 3 ra `403` | lần trước chưa reset, alice vẫn là VIEWER nên token mới mang VIEWER | chạy lại bước 1 và 2 |
| bước 5 trên 8080 ra `403` | `OLD` bị gán lại sau bước 4 | lấy token ở bước 2, trước bước 4 |

## 8. Chạy EvoMaster

Lệnh một lượt: `cli.md` §7.1. Arm có reset, chỉ chạy được trên P2f và các jar trước, thêm
`--statefulAuthzResetEndpoint "POST http://localhost:8080/reset"`.
Auth: `infra/em-config/reports-auth.yaml`.
