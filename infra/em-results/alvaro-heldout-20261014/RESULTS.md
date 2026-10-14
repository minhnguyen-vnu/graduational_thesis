# alvaro held-out — kết quả (jar P2e-6ae8277b, 2026-10-14)

Giao thức: `PROTOCOL.md`. MR-A1 kiểm tay XÁC NHẬN live (`handcheck.sh`, token-cũ ADMIN=200 sau hạ / token-mới USER=403 / neg=403).

## Kết quả: KHÔNG chạy máy được (lượt này) — Prisma query-engine panic dưới fuzzing

Dựng lại stack (node:18 container + postgres:16 `alvaro-pg` + network, node_modules build sẵn), setup+handcheck PASS,
spec 3.0.0 parse OK (không như fastschema). EvoMaster vào search, nhưng **login sập**:

- Traffic lượt auto seed 1: `/login` → **200×20, 500×988, 400×3**. Sau ~20 login thành công, engine panic rồi 500 hàng loạt.
- App log: `PANIC: called Option::unwrap() on a None value in query-engine/core/src/query_document/parser.rs:250` trên
  `this.prisma.user.findUnique()` (login). Prisma Client **3.14.0**, Query Engine **linux-arm64**, Node 18. Prisma gọi đây
  là "non-recoverable error". Sau panic, login tuần tự ngay sau đó vẫn 500 (3/3) → engine chết hẳn tới khi restart app.

Cơ chế: EvoMaster gửi input fuzz vào các endpoint chạm Prisma; một input kích hoạt panic của query-engine Prisma 3.14
(bug cũ trên arm64), engine thành non-recoverable → mọi login sau đó 500 → EvoMaster hầu như không auth được → không bộ ba.
Dừng lượt sau khi xác nhận (login 500 cả khi gọi tuần tự).

Đây là blocker **môi trường/công cụ, trên cả oracle** — và một phần là **artifact của môi trường test** (arm64 Mac + Prisma
3.14 cũ): trên x86 hoặc Prisma mới có thể không panic. Không phải giới hạn của oracle 970. Lỗi MR-A1 của alvaro là THẬT
(kiểm tay tuần tự xác nhận); chỉ là không fuzz máy được với stack này.

## Dè dặt

- Chưa thử: restart app + chạy rate rất thấp (60/phút) xem có tránh được trigger panic không. Panic là "unwrap on None" ở
  parser Prisma — nhiều khả năng do INPUT cụ thể, không phải tải, nên rate thấp có thể vẫn chết. Quyết định của user.
- Không nâng Prisma (sửa deps = đổi target, deviation nặng, mã 2022 có thể vỡ).
- Builder decisions không đọc được vì search chạy trên auth chết (assembled không đáng tin); không xếp FN/TP.
