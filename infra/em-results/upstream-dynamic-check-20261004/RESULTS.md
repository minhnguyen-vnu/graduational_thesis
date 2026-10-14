# EvoMaster upstream v6.2.0 chạy máy trên target của ta — 2026-10-04

Bổ sung chạy máy cho kiểm mã tĩnh `docs/related-work.md` §2a (2026-10-02). Câu hỏi: bản release mới nhất của
tác giả, chạy trên chính các app chứa lỗi của ta, có nổ phát hiện nào thuộc lớp "tài khoản vẫn vào được sau khi
bị thu hẹp quyền" không.

**Kết luận: không.** Trên bản lỗi Tier-1 và Tier-2, v6.2.0 nổ các lớp lỗi riêng của nó (thiếu 401, sai schema,
HTTP 500, và một oracle an toàn một-thời-điểm), không lớp nào dựng chuyển đổi hạ quyền hay dùng lại chứng chỉ
trước lúc hạ.

## Jar

- `evomaster.jar` release `v6.2.0` (2026-09-15), tải từ
  <https://github.com/WebFuzzing/EvoMaster/releases/download/v6.2.0/evomaster.jar>
- sha256 `93f9c4a0de88b01395d2a1009776aa739973e9f64343778d2fd49c212fd17915`, 115219542 byte
- `--version` in `EvoMaster version: 6.2.0`
- Jar để ở scratchpad phiên, không đưa vào repo; tải lại từ URL + sha trên.

## Lệnh (một seed mỗi tier, dừng sớm theo luật user 2026-10-04)

```
java -jar evomaster.jar --blackBox true --bbSwaggerUrl <spec> --bbTargetUrl <sut> \
  --configPath infra/em-config/<tier>-auth.yaml \
  --security true --minimize true --minimizeTimeout 2 --useExperimentalOracles true \
  --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 180s --seed 1 --outputFolder <out>
```

- Tier-1 bản lỗi `:8080` (`/v3/api-docs`, `reports-auth.yaml`); reset `POST /reset` trước lượt.
- Tier-2 bản lỗi `:5002` (`/openapi.json`, `vampi-seeded-auth.yaml`); reset `GET /createdb` trước lượt.
- Config auth dạng WFC v6.1.1 được v6.2.0 nhận không lỗi.
- Không chạy pyLoad và không chạy thêm seed: cả hai tier seed 1 đã cho mặt âm tính của lớp lỗi ta nhắm tới;
  mặt âm tính này mang tính cấu trúc (upstream không có hàm dựng chuyển đổi), thêm seed không đổi kết luận.

## Lỗi v6.2.0 nổ (mã theo commons 0.9.0 của upstream, khác mã của ta)

| Tier | Số lỗi | Mã | Tên (lấy từ chú thích test sinh ra) |
|---|---|---|---|
| Tier-1 bản lỗi | 17 | 109 | HTTP Violation: no-401-if-no-authenticate |
| | | 202 | Schema Violation: no-401-if-no-auth |
| | | 305 | Wrongly Not Recognized as Authenticated (một lần, `POST /auth/login`) |
| Tier-2 bản lỗi | 23 | 100 | HTTP Status 500 |
| | | 109 | HTTP Violation: no-401-if-no-authenticate |
| | | 200 | Schema Violation (body/contentType/status không khớp schema) |
| | | 201 | Schema Violation: Invalid Allow HTTP Header |

Oracle gần nhất là `305 Wrongly Not Recognized as Authenticated` trên Tier-1: nó xét một chứng chỉ hợp lệ bị từ
chối (chiều ngược với ta), một thời điểm, không qua chuyển đổi. Trong test sinh ra, phần an toàn của v6.2.0 có thử
một chuỗi chéo tài khoản một-thời-điểm (`bob` → 403, `superadmin` → 201) nhưng không dựng bước hạ quyền và không
dùng lại token trước lúc hạ. Bằng chứng: `tier1-s1/EvoMaster_faults_Test.py`, `tier1-s1/report.json`,
`tier2-s1/report.json`.

## Giới hạn của kiểm này

- Một seed mỗi tier, ngân sách 180s; đây là kiểm nhẹ, không phải đo recall của upstream.
- Chỉ Tier-1 và Tier-2; không chạy pyLoad.
- Mã lỗi của v6.2.0 là commons 0.9.0 (300–312 cho security), khác commons 0.6.0 của jar `AF2` (970). Không trộn
  bảng mã giữa hai bản.
