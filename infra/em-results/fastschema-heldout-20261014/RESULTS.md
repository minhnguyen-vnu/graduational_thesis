# fastschema held-out — kết quả (jar P2e-6ae8277b, 2026-10-14)

Giao thức: `PROTOCOL.md`. MR-A1 kiểm tay XÁC NHẬN live (`../../fastschema-target/handcheck.sh`, token-cũ Admin=200 / token-mới User=403 / neg=403).

## Kết quả: KHÔNG chạy máy được — blocker tầng parser

EvoMaster v6.1.1 **crash lúc parse spec**, trước khi search bắt đầu (`logs/auto-seed1-600s.log`):

```
[ERROR] EvoMaster process terminated abruptly.
java.lang.reflect.InvocationTargetException: ... AbstractRestFitness.initBean()
Caused by: java.lang.StackOverflowError: null
  at io.swagger.v3.parser.util.ResolverFully.resolveSchema(ResolverFully.java:459)
  at io.swagger.v3.parser.util.ResolverFully.resolveSchemaProperty(ResolverFully.java:648)
  ... (lặp vô hạn)
```

Nguyên nhân: spec OpenAPI 3.1.0 của fastschema có **6 vòng tròn $ref 2-cạnh** giữa các component schema:
`User↔Role`, `Role↔Permission`, `User↔File`, và bản `Schema.User↔Schema.Role`, `Schema.Role↔Schema.Permission`,
`Schema.User↔Schema.File`. swagger-parser mà EvoMaster dùng bật `resolveFully` (inline toàn bộ $ref) nên đệ quy vô hạn
trên quan hệ m2m vòng tròn → StackOverflow. `-Xss` không cứu (vòng lặp vô hạn, không phải sâu-hữu-hạn).

Đây là blocker **ở tầng công cụ, trên cả oracle** — oracle 970 chưa bao giờ chạy. Cùng loại "oracle chưa với tới" như
Airflow (transition không có trong REST) / Vikunja (không cấp được chứng chỉ mới) trong `cve-survey/coverage.md`, nhưng
nguyên nhân khác: EvoMaster không nạp được spec.

Lỗi MR-A1 của fastschema là THẬT (kiểm tay xác nhận); chỉ là EvoMaster v6.1.1 không ingest được spec của nó.

## Dè dặt / ghi chú

- Harness ghi hụt hàng CSV cho lượt crash (bug: EvoMaster crash pre-search → không có file traffic → đếm login lỗi →
  `set -u` thoát ở dòng 44). Đã sửa (`run-full.sh`: login-count rỗng default 0). Không chạy lại vì EvoMaster vẫn crash ở parser.
- Chưa thử de-cycle spec (phá 6 back-ref để parser kết thúc). Nếu de-cycle, auto vẫn nhiều khả năng FN (body m2m + UUID động) — quyết định của user.
- Rủi ro lan: bcms (headless CMS, TS) có thể cùng kiểu spec quan hệ vòng tròn; sẽ kiểm spec trước khi chạy.
