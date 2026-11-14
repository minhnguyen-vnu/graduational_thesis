# EvoMaster upstream master mới nhất trên Tier-1, 20 seed — 2026-11-11

Viết trước lượt chạy. Yêu cầu của user (2026-11-11): lấy mã upstream mới nhất, chạy trên Tier-1, xem bản đó có tìm ra lỗi
lớp MR-A1 không. Lặp lại `upstream-master-t1-20261018` với jar mới; câu hỏi, proxy, script soát và luật dừng giữ nguyên
như protocol đó.

## Jar

- Upstream `WebFuzzing/EvoMaster` master `067df22ae2f18fa5231eb91260cea21771f10fd7` (2026-11-10 20:30 +0100), 305
  commit sau `ab983ba338` (jar của lượt 2026-10-18). Release mới nhất vẫn là `v6.2.0`.
- Clone `/Users/minhnguyen/IdeaProjects/EvoMaster-upstream`, fast-forward từ `ab983ba338`.
- Build: `JAVA_HOME=$(/usr/libexec/java_home -v 17) mvn -pl core -am package -DskipTests`, exit 0.
- Bản giữ: `EvoMaster-upstream/evomaster-upstream-master-96365f7a.jar`, sha256
  `96365f7a22f5875a32cac9d8db92641fa96d220380080090866287e1500340e5`; harness dừng nếu sha khác. Manifest
  `6.2.1-SNAPSHOT`.
- Mã an toàn đổi từ `ab983ba338`: `RestSecurityOracle.kt` 1 dòng (`javax.inject.Inject` thành
  `com.google.inject.Inject`, commit `6f2c289cbc`), `RestSecurityBuilder.kt` 3 dòng (`@PostConstruct` thành
  `@StartService([Sampler::class])`). Không mã lỗi mới nào về phân quyền.
- `EMConfig.kt`: bỏ `bbExperiments`, thêm `unboundBudgetForFlakiness` (mặc định `false`). Cờ dòng lệnh của harness
  (`security`, `useExperimentalOracles`, `extraPhaseBudgetPercentage`, `minimize`) không đổi.

## Lệnh

`upstream_t1.sh`, chép từ `upstream-master-t1-20261018/upstream_t1.sh`; `diff` khác đúng ba dòng: đường dẫn jar,
thư mục chạy, sha kỳ vọng. `capture_proxy.py`, `audit_traffic.py`, `audit_tests.py` chép nguyên (`cmp` trùng).
Chạy dưới `caffeinate -dims`, seed 1–20, 150 s mỗi seed.

## Đối chứng trước batch

- `control/`: phát tay chuỗi đối chứng của lượt 2026-10-18 qua proxy, trên :8080 và :8081, rồi chạy `audit_traffic.py`.
- `smoke/`: 30 s, seed 99, jar mới, không thuộc dữ liệu.

## Luật dừng

Như protocol 2026-10-18: 2 hàng liên tiếp `faults = ERR`; bất kỳ lỗi chuyển tiếp nào của proxy; một tài khoản không có
lần đăng nhập 200 nào; `Entering Sleep` mới trong `pmset -g log`.

## Lệch luật đã khai

Giữ ba lệch luật của protocol 2026-10-18 (proxy, `-DskipTests`, bỏ luật dừng sớm theo mẫu bộ ba).

## Sự cố trong lúc chạy

- Seed 5, giữa hàng 851 (21:32:01) và 855 (21:32:02) của `traffic/t1-upstream-seed5.jsonl`: target bị reseed mà không có
  `POST /reset` nào qua proxy. ID report tụt từ 22 về 6; hàng 858 superadmin đăng nhập nhận claim ADMIN trong khi audit
  còn giữ VIEWER từ hàng 701. App chỉ reseed qua `POST /reset` (`ResetController.java:22`), container không khởi động
  lại (`RestartCount=0`), không phiên Claude nào gọi :8080 trong 21:20–21:34. Nguồn chưa xác định.
- Hệ quả: `stale_2xx=23` của seed 5 gồm 1 lời gọi token cũ thật (hàng 702) và 22 lời gọi sau hàng 858, khi superadmin đã
  thật sự là ADMIN. `audit_traffic.py` giữ nguyên trong batch; sau batch chạy thêm một kiểm tra khai báo ở đây trước khi
  xem kết quả: so claim của mỗi lần đăng nhập 200 với vai trò audit đang giữ, mỗi chỗ lệch là một lần đổi trạng thái ngoài
  proxy, và đếm lại lời gọi token cũ khi đồng bộ vai trò theo claim.
- Lượt 2026-10-18 chạy cùng kiểm tra này ra 0 chỗ lệch ở cả 20 seed.

## Sau batch

`audit-traffic.out` (harness), `audit_tests.py` trên `tests/`, đọc tay mọi lỗi trong `report.json`, snapshot sang
`~/thesis-backups/`.
