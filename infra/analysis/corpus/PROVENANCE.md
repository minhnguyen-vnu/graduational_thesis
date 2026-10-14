# Corpus provenance

Tải nguyên văn, chưa lọc, chưa chọn mẫu.

## 1. apis.guru list.json

Lệnh tải (chạy từ `/Users/minhnguyen/IdeaProjects/graduational-thesis`):

```
curl -sSL https://api.apis.guru/v2/list.json -o infra/analysis/corpus/apis-guru-list.json
```

| Mục | Giá trị |
|---|---|
| File | `infra/analysis/corpus/apis-guru-list.json` |
| sha256 | `dfac835d2d1f13dfdb82723d72be1acf567df53c1b710bf6d68e28b795696e66` |
| Kích thước | 8855894 bytes |
| Giờ tải (mtime file) | 2026-09-16 22:25:31 +07 (UTC+0700, Asia/Ho_Chi_Minh) |

Lệnh sinh ba giá trị trên:

```
shasum -a 256 infra/analysis/corpus/apis-guru-list.json
stat -f '%z bytes' infra/analysis/corpus/apis-guru-list.json
stat -f 'mtime=%Sm' -t '%Y-%m-%d %H:%M:%S %Z (%z)' infra/analysis/corpus/apis-guru-list.json
```

Output nguyên văn:

```
dfac835d2d1f13dfdb82723d72be1acf567df53c1b710bf6d68e28b795696e66  infra/analysis/corpus/apis-guru-list.json
8855894 bytes
mtime=2026-09-16 22:25:31 +07 (+0700)
```

## 2. Đếm API và provider

Định nghĩa dùng để đếm:

- **API** = một khoá cấp một trong `list.json`; một khoá có thể chứa nhiều version.
- **Provider (định nghĩa chính)** = phần đứng trước dấu `:` đầu tiên của khoá; khoá không có `:` thì lấy cả khoá.
- **Provider (định nghĩa đối chiếu)** = `versions[preferred].info["x-providerName"]`.

Script: `infra/analysis/corpus/count_corpus.py`. Nội dung nguyên văn:

```python
import json

with open("infra/analysis/corpus/apis-guru-list.json") as f:
    data = json.load(f)

n_apis = len(data)
providers_by_key = {k.split(":")[0] for k in data}
provider_names = set()
missing_xprovider = 0
for k, v in data.items():
    pref = v.get("preferred")
    versions = v.get("versions", {})
    entry = versions.get(pref) or (list(versions.values())[0] if versions else {})
    name = entry.get("info", {}).get("x-providerName")
    if name is None:
        missing_xprovider += 1
    else:
        provider_names.add(name)

print("n_apis", n_apis)
print("n_providers_key_prefix", len(providers_by_key))
print("n_providers_x_providerName", len(provider_names))
print("entries_missing_x_providerName", missing_xprovider)
print("key_prefix_equals_x_providerName", providers_by_key == provider_names)
```

Lệnh chạy:

```
python3 infra/analysis/corpus/count_corpus.py
```

Output nguyên văn:

```
n_apis 2529
n_providers_key_prefix 677
n_providers_x_providerName 676
entries_missing_x_providerName 0
key_prefix_equals_x_providerName False
```

Hai tập provider lệch nhau đúng một phần tử. Lệnh:

```
python3 -c "
import json
d=json.load(open('infra/analysis/corpus/apis-guru-list.json'))
pk={k.split(':')[0] for k in d}
pn=set()
for k,v in d.items():
    p=v.get('preferred'); e=v.get('versions',{}).get(p,{})
    pn.add(e.get('info',{}).get('x-providerName'))
print('only_in_key_prefix', sorted(pk-pn))
print('only_in_x_providerName', sorted(pn-pk))
"
```

Output nguyên văn:

```
only_in_key_prefix ['api.ebay.com']
only_in_x_providerName []
```

## 3. WFD Dataset clone

Lệnh (chạy từ `/Users/minhnguyen/IdeaProjects/graduational-thesis`, timeout 900000 ms):

```
git clone --depth 1 https://github.com/WebFuzzing/Dataset infra/analysis/corpus/wfd
```

Kết quả: clone xong, `exit=0`, kết thúc lúc 2026-09-16 22:27:26 +07 (+0700), khoảng 1 phút 55 giây sau lệnh tải
list.json. Dòng cuối của git: `Updating files: 100% (18538/18538), done.`

Lệnh ghi lại commit HEAD của bản clone bị harness chặn quyền. Thông báo nguyên văn:

```
This command changes directory before running a version-control command, which can pick up untrusted hooks or repository configuration from the target directory. Approve only if you trust it.
```

Bước đó bỏ qua theo ràng buộc; PROVENANCE không có commit hash của bản clone WFD.

## 4. Kiểm kê OpenAPI trong WFD

Script quét: `infra/analysis/corpus/scan_wfd_openapi.py`. Bảng 145 dòng mà nó sinh ra đã bị xoá ngày 2026-09-17:
quét cả cây nguồn nên 63 dòng là fixture test của microcks, không phải API được kiểm thử. Bảng dùng cho lấy mẫu
là `infra/analysis/corpus/wfd-suts.md`, sinh bởi `inventory_suts.py` từ `wfd/openapi-swagger/`, 36 spec, một SUT một spec.

Lệnh:

```
python3 infra/analysis/corpus/scan_wfd_openapi.py
```

Output nguyên văn:

```
scanned 968
matched 145
unreadable 0
out /Users/minhnguyen/IdeaProjects/graduational-thesis/infra/analysis/corpus/wfd-inventory.md
```
