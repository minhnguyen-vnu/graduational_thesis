# Đọc `report.json` và `EvoMaster_faults_Test.py`

Ví dụ lấy từ một lượt upstream trên reports-api bản lỗi, seed 1, ngày 2026-11-22:
`infra/em-results/upstream-b6307c2d-20261122/tests-seed1-p06/`. Lệnh chạy: `04-lenh-build-va-chay.md` §4.

## Thư mục output

| File | Nội dung |
|---|---|
| `report.json` | tóm tắt máy đọc được: fault, độ phủ, danh sách test |
| `EvoMaster_faults_Test.py` | 13 test làm lộ fault |
| `EvoMaster_successes_Test.py` | 30 test có response 2xx |
| `EvoMaster_others_Test.py` | 15 test còn lại |
| `em_test_utils.py` | hàm phụ cho test, ví dụ `resolve_location` |
| `index.html` | báo cáo xem bằng trình duyệt |

## `report.json`

Bốn phần.

### 1. Thông tin lượt chạy

```json
"toolVersion": "6.2.1-SNAPSHOT",
"creationTime": "2026-11-22T23:02:05+07:00",
"totalTests": 58,
"executionTimeInSeconds": 320
```

### 2. `faults`

```json
"faults": {
  "totalNumber": 17,
  "foundFaults": [ 13 phần tử ]
}
```

Mỗi phần tử của `foundFaults` là một test làm lộ fault:

```json
{
  "operationId": "GET:/reports",
  "testCaseId": "EvoMaster_faults_Test.py#test_0_get_on_reports_showsFaults_109_202",
  "faultCategories": [
    { "id": "SCHEMA_STATUS_NO_401_IF_NO_AUTH",           "code": 202, "context": null },
    { "id": "HTTP_STATUS_NO_401_IF_NO_WWW_AUTHENTICATE", "code": 109, "context": null }
  ]
}
```

| Trường | Nghĩa |
|---|---|
| `operationId` | endpoint, dạng `VERB:/path` |
| `testCaseId` | `<file>#<tên hàm test>` tái hiện fault |
| `faultCategories[].code` | mã fault |
| `faultCategories[].id` | tên mã |

`totalNumber` = 17 khớp với số cặp (endpoint, mã) khác nhau. `POST:/auth/login` nằm ở 5 test nhưng góp 3 cặp: 109, 202,
305. Số khớp do đếm tay; chưa đọc mã tính `totalNumber`.

Mã trong lượt này, điều kiện lấy từ mã upstream `dd063b4f9f`:

| Mã | Tên | Điều kiện | Ở reports-api |
|---|---|---|---|
| 109 | `HTTP_STATUS_NO_401_IF_NO_WWW_AUTHENTICATE` | 401 không kèm header `WWW-Authenticate` (`HttpStatusOracle.kt:91`) | cả 13 test |
| 202 | `SCHEMA_STATUS_NO_401_IF_NO_AUTH` | 401 khi spec không khai cơ chế xác thực (`HttpStatusOracle.kt:87`) | cả 13 test |
| 305 | `SECURITY_NOT_RECOGNIZED_AUTHENTICATED` | request có `auth` nhận 401 (`RestSecurityOracle.kt:160`), cộng bộ lọc `hasNotRecognizedAuthenticated` chưa đọc | test 2, `POST:/auth/login` |

Đọc nhanh mỗi fault một dòng:

```bash
python3 -c "
import json; r = json.load(open('report.json'))
for f in r['faults']['foundFaults']:
    print(f['operationId'], [c['code'] for c in f['faultCategories']])
"
```

### 3. `problemDetails.rest`

| Trường | Giá trị | Nghĩa |
|---|---|---|
| `evaluatedHttpCalls` | 270 | request gửi trong lúc tìm kiếm; khớp `Evaluated actions: 270` trong log |
| `outputHttpCalls` | 79 | request nằm trong 58 test ghi ra |
| `endpointIds` | 9 endpoint | endpoint đọc từ spec |
| `coveredHttpStatus` | 74 phần tử | mỗi phần tử: endpoint, test, mã HTTP nhận được |

Gộp `coveredHttpStatus` theo endpoint:

```bash
python3 -c "
import json, collections; r = json.load(open('report.json'))
d = collections.defaultdict(set)
for c in r['problemDetails']['rest']['coveredHttpStatus']:
    d[c['endpointId']].update(c['httpStatus'])
for k in r['problemDetails']['rest']['endpointIds']:
    print(k, sorted(d.get(k, [])))
"
```

| Endpoint | Mã đã thấy |
|---|---|
| `PUT /users/{username}/role` | 200, 400, 401, 403, 404 |
| `PUT /reports/{id}` | 200, 400, 401, 403, 404 |
| `DELETE /reports/{id}` | 204, 401, 403, 404 |
| `POST /reports` | 201, 400, 401, 403 |
| `GET /reports/{id}` | 200, 401, 404 |
| `GET /reports` | 200, 401 |
| `GET /users/me` | 200, 401 |
| `POST /reset` | 200 |
| `POST /auth/login` | 401 |

`POST /auth/login` chỉ có 401 vì các request tới đó do EvoMaster sinh với username và mật khẩu ngẫu nhiên. Đăng
nhập của ba tài khoản trong `reports-auth.yaml` không tính vào đây. Đây là endpoint duy nhất trong log
`8 endpoints out of 9` không có 2xx.

`POST /reset` nằm trong spec nên EvoMaster cũng gọi nó khi tìm kiếm.

### 4. `testCases`

Mỗi phần tử trỏ tới vị trí một test:

```json
{ "name": "test_0_get_on_reports_showsFaults_109_202",
  "filePath": "EvoMaster_faults_Test.py", "startLine": 49, "endLine": 66 }
```

## `EvoMaster_faults_Test.py`

542 dòng, 13 test. Mỗi test là một hàm `unittest`, gửi lại đúng các request đã làm lộ fault.

### Đầu file

```python
import requests
import unittest
from em_test_utils import *
...
#  The generated test suite contains 13 tests
#  Covered targets: 65
#  Used time: 0h 5m 20s
class EvoMaster_faults_Test(unittest.TestCase):
    baseUrlOfSut = "http://localhost:8080"
```

`baseUrlOfSut` là địa chỉ app. Đổi thành `http://localhost:8081` thì cùng các test chạy lên bản vá.

### Một test: test 0 (dòng 49–66)

```python
# Calls:
# (401) GET:/reports
# Found 2 potential faults. Type-codes: 109, 202
@timeout_decorator.timeout(60)
def test_0_get_on_reports_showsFaults_109_202(self):

    # Fault109. HTTP Violation: no-401-if-no-authenticate.
    # Fault202. Schema Violation: no-401-if-no-auth.
    headers = {}
    headers['Accept'] = "application/json"
    res_0 = requests \
            .get(self.baseUrlOfSut + "/reports",
                headers=headers, timeout=EM_HTTP_TIMEOUT_S, verify=False)

    assert res_0.status_code == 401
    assert "www-authenticate" not in res_0.headers
    assert "application/json" in res_0.headers["content-type"]
```

| Phần | Nghĩa |
|---|---|
| tên `..._showsFaults_109_202` | test làm lộ mã 109 và 202 |
| `# Calls:` | tóm tắt: request nào, nhận mã gì |
| `# FaultNNN` | đặt ngay trên request làm lộ fault |
| `headers` không có `Authorization` | gọi khi chưa đăng nhập |
| `assert` | response đã nhận lúc sinh test: 401, không có `www-authenticate` |

`assert` ghi hành vi lúc chạy, không ghi hành vi đúng. Nếu app sửa để trả `WWW-Authenticate`, test này trượt.

### Một test nhiều bước: test 2, mang mã 305

| Biến | Tài khoản | Request | Response |
|---|---|---|---|
| `res_bob` | | `POST /auth/login` `bob` / `bobpass` | lấy `token_bob` |
| `res_superadmin` | | `POST /auth/login` `superadmin` / `superpass` | lấy `token_superadmin` |
| `res_0` | bob | `POST /reports` | 403, `"admin role required"` |
| `res_1` | superadmin | `POST /reports` | 201, `owner = superadmin` |
| `res_2` | superadmin | `POST /auth/login` `GL9zM6VO3EtmC` / `Av9aSHv` | 401, `"invalid credentials"` |
| `res_3` | superadmin | `DELETE /reports/{id}` (cleanup) | 204 |

- Hai request đầu là bước đăng nhập theo `reports-auth.yaml`; mỗi test tự đăng nhập lại.
- `# Fault109`, `# Fault202`, `# Fault305` đặt trên `res_2`.
- `res_2` mang token của superadmin và nhận 401, khớp điều kiện của 305. `/auth/login` kiểm username và mật khẩu trong
  body, không đọc token; body là cặp ngẫu nhiên nên 401 là đúng. Mã 305 ở test này là báo nhầm.
- `# Cleanup actions` xoá report do test tạo.

### Chạy lại test

```bash
cd /Users/minhnguyen/IdeaProjects/graduational-thesis
curl -s -X POST http://localhost:8080/reset
infra/em-venv/bin/python -m pytest \
  infra/em-results/upstream-b6307c2d-20261122/tests-seed1-p06/EvoMaster_faults_Test.py -v
```

Chưa chạy; chưa kiểm `infra/em-venv` có `requests` và `timeout_decorator`.
