# Mã từ chối trên ba target — bằng chứng cho việc siết D1 về §3

Ghi 2026-09-17. Lý do: `CLAUDE.md` §6 định nghĩa D1 coi mọi mã không thuộc 2xx của PUT là "bị từ chối", còn §3
định nghĩa chỉ 403 là từ chối, 401 là không kết luận được, 404 không phải từ chối. Hai chỗ mâu thuẫn.

## 1. Ba target từ chối bằng mã nào

| Target | Từ chối quyền | 401 sinh ra từ đâu | 404 |
|---|---|---|---|
| Tier-1 `reports-api` | 403 | xác thực hỏng (`infra/reports-api/src/main/java/com/thesis/reportsapi/security/AuthFilter.java:98`) | — |
| Tier-2 `vampi-seeded` | 403 (`docs/tier2-seeded-benchmark-plan.md:62`) | token hết hạn sau 60 giây, đã ghi là INCONCLUSIVE (`:70`) | đã kiểm: non-admin gọi sách không tồn tại vẫn nhận 403, không che bằng 404 (`:71`) |
| Tier-2b pyLoad | 403 trên `/json/*` (`docs/tier2b-pyload-target.md:106–107`) | `/api/*` trả 401 cho lỗi phân quyền, đã ghi là INCONCLUSIVE (`:107–108`) | — |

Nguồn mã 403 của Tier-1: `infra/reports-api/src/main/java/com/thesis/reportsapi/security/ApiException.java:25`
dùng `HttpStatus.FORBIDDEN`.

## 2. Quan sát thực tế của probe D1

Một dòng duy nhất có trên đĩa, từ self-test 2026-09-17:

```
* Stateful-authorization fresh-credential probe: PUT:/reports/{id}[alice]=403
```

Lệnh: `grep -rho "fresh-credential probe[^\"]*" infra/em-results/`.

## 3. Kết luận

Cả ba target từ chối bằng 403. Còn 401 và 404 đều có nguyên nhân không phải do ứng dụng chặn quyền:

- 401 — đăng nhập mới hỏng, hoặc token vừa cấp đã hết hạn. Hai target đã ghi 401 là INCONCLUSIVE.
- 404 — id mà probe nhét vào path sai. Vampi đã kiểm là không che bằng 404.

Luật "mọi non-2xx là từ chối" đọc cả hai trường hợp đó thành "bị từ chối", tức là hai đường sinh 970 giả.

## 4. Lập luận ngược lại, giữ để viết phần hạn chế

Ép đúng 403 là cắm một hằng số do ta chọn, đúng thứ mà D1 sinh ra để loại bỏ. Ứng dụng khác có thể chặn ghi bằng
400 hoặc 409. `CLAUDE.md` §6 đã ghi "denial code not configurable" trong phần hạn chế.

Người dùng duyệt siết về 403 ngày 2026-09-17.
