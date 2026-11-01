# EvoMaster upstream master trên Tier-1, 20 seed — 2026-10-18

Viết trước lượt chạy. Yêu cầu của user (2026-10-18): lấy EvoMaster mới nhất, build, chạy đủ 20 seed trên Tier-1,
kiểm xem bản hiện tại có dựng và tìm ra lỗi lớp MR-A1 không, rồi soát lại.

## Câu hỏi

Trên bản lỗi Tier-1 `reports-api` (:8080), EvoMaster upstream không có mã của ta:
1. **Tìm ra:** có báo lỗi nào mà test của nó là chuỗi hạ quyền rồi dùng lại token cũ không.
2. **Dựng:** trong toàn bộ traffic (search, pha security, minimization), có lần nào một token cấp lúc tài khoản còn
   ADMIN được dùng cho thao tác chỉ-ADMIN sau khi tài khoản đó bị hạ xuống VIEWER, mà không có reset hay nâng quyền
   xen giữa không; nếu có, mã trạng thái là gì, và có source 2xx bằng cùng token trước lúc hạ không.

## Jar

- Upstream `WebFuzzing/EvoMaster` master `ab983ba3380c2c1a4891440c7799880f2f81882a` (2026-10-16 15:37 +0200), 169
  commit sau `d8658d97` (lần đọc mã 2026-10-02), 1382 commit sau `v6.1.1`. Release mới nhất vẫn là `v6.2.0`.
- Clone `/Users/minhnguyen/IdeaProjects/EvoMaster-upstream` (`--filter=blob:none`), không đụng repo của ta.
- Build: `JAVA_HOME=$(/usr/libexec/java_home -v 17) mvn -pl core -am package -DskipTests`. Lệnh của skill
  `evomaster-build` (`-Dmaven.test.skip=true`) hỏng ở đây: `evomaster-client-java-sql` cần test-jar
  `evomaster-ci-utils:tests:6.2.1-SNAPSHOT`, mà `maven.test.skip` không dựng test-jar.
- Bản giữ: `EvoMaster-upstream/evomaster-upstream-master-d898c1ce.jar`, sha256
  `d898c1ceedc82459b245fe581cd037aa64318fce6c1e0f7f9052dfeaec6a5558`; harness dừng nếu sha khác.
- `report.json` ghi `EvoMaster 6.2.1-SNAPSHOT`. `EMConfig.class` không chứa chuỗi `statefulAuthz` nào.
- Mã an toàn đổi từ `d8658d97`: `RestSecurityOracle.kt` 14 dòng, `RestSecurityBuilder.kt` 6 dòng, đều là đổi tên
  hằng (`SECURITY_WRONG_AUTHORIZATION` thành `SECURITY_INCONSISTENT_WRITE_AUTHORIZATION`, `SECURITY_XSS` thành
  `SECURITY_XSS_INJECTION`, commit `c40d79c746` "updated to WFC 0.10.0").

## Lệnh

Hàm `t1` của `upstream_t1.sh`. So với hàng `tier1 vuln` không reset của `p2f-full-20261015/p2f_full.sh`, diff 25 token
của dòng lệnh khác đúng hai chỗ: jar, và `--bbTargetUrl http://localhost:8280` (proxy) thay `:8080`. Spec vẫn đọc thẳng
từ `:8080`. Seed 1–20, `POST /reset` trước mỗi seed và sau batch.

## Proxy ghi traffic

`capture_proxy.py`, chép nguyên từ `gg-overnight-20260926/` (`cmp` trùng). Mỗi request một dòng JSON: method, path,
12 ký tự cuối header `Authorization`, body request, mã trạng thái, 2000 ký tự đầu body phản hồi. Mỗi seed một file
`traffic/t1-upstream-seed<N>.jsonl`.

`audit_traffic.py` đọc traffic: gán token cho tài khoản qua `POST /auth/login` 200 (claim `role` trong JWT), theo dõi
vai trò hiện tại (seed: alice ADMIN, superadmin ADMIN, bob VIEWER; `POST /reset` 2xx đưa về seed; `PUT
/users/{u}/role` 2xx đổi vai trò). Thao tác chỉ-ADMIN: POST/PUT/DELETE/PATCH trên `/reports*` và `/users/{u}/role`.
Lời gọi "token cũ" là thao tác chỉ-ADMIN bằng token claim ADMIN của tài khoản đang là VIEWER. Đếm theo mã: 2xx, 403,
khác; `full_triples_2xx` là lời gọi token cũ 2xx có source 2xx bằng cùng token trước lần hạ.

**Đối chứng dương của thiết bị đo** (`control/`, chạy trước batch): phát tay chuỗi README qua proxy.
Bản lỗi :8080: source 204, transition 200, follow-up token cũ 204, follow-up token mới 403; script ra `stale_2xx=1`,
`full_triples_2xx=1`. Bản vá :8081: follow-up token cũ 403; script ra `stale_403=1`, `stale_2xx=0`. Lời gọi bằng token
đăng nhập lại không bị đếm (`control/audit.out`).

**Lượt thử** (`smoke/`, 30s, seed 99, không thuộc dữ liệu): exit 0, `report.json` cùng định dạng, 287 request qua proxy,
không lỗi proxy, đăng nhập 45/32/32 lần (alice/superadmin/bob).

## Mỗi hàng ghi

`runs.csv`: `tier,arm,seed,exit,faults,fault_count,requests,proxy_errors,login_alice,login_superadmin,login_bob,
demotions,stale_2xx,stale_403,stale_other,full_triples_2xx`. `faults` là tập mã lỗi trong `report.json`.

## Luật dừng (kiểm sau mỗi hàng, `check`)

- 2 hàng liên tiếp `faults = ERR` (không đọc được `report.json`).
- Bất kỳ lỗi chuyển tiếp nào của proxy.
- Một trong ba tài khoản không có lần đăng nhập 200 nào trong traffic của hàng.
- Có `Entering Sleep` mới trong `pmset -g log`.

Luật "3 seed đầu cùng một mẫu và 0 bộ ba hợp lệ" (CLAUDE.md §2) không áp dụng: upstream không có bộ dựng bộ ba, và
user yêu cầu đủ 20 seed để đo đúng điều đó. Ghi là lệch luật.

## Sau batch

1. `audit-traffic.out` (harness tự chạy).
2. Soát test sinh ra: mọi lỗi trong `report.json`, đọc tay mọi test thuộc nhóm security và mọi test có gọi
   `PUT /users/{u}/role`.
3. Snapshot sang `~/thesis-backups/`.

## Thay đổi sau khi chốt

- 2026-10-18 khoảng 22:55, lúc batch ở seed 6: thêm `audit_tests.py` cho bước 2 "Sau batch". Nó đọc mọi test sinh ra,
  tìm `PUT /users/{u}/role` với `VIEWER` trả 2xx rồi một thao tác chỉ-ADMIN bằng `auth_<u>` trong cùng test, ghi mã trạng
  thái, có source 2xx trước đó không, và mã lỗi chú thích trên lời gọi đó. Đối chứng trước khi dùng
  (`control/audit-tests-control.out`): test 970 của `p2f-full-20261015` seed 8 bản lỗi ra 2 lời gọi 2xx có source, lời
  gọi đầu mang `970`; bản vá cùng seed ra 3 lời gọi 403; thư mục `smoke/out` ra 0. Bản đầu gán chú thích lỗi vào khối
  trước nên đọc `970` thành rỗng; đã sửa trước khi chạy trên dữ liệu batch.

## Lệch luật đã khai

1. Proxy nằm giữa EvoMaster và target, khác hàng `tier1 vuln` của ta; arm này không ghép đôi với số của ta.
2. Build bằng `-DskipTests` thay lệnh của skill (lý do ở mục Jar).
3. Luật dừng sớm theo mẫu bộ ba bỏ, theo yêu cầu 20 seed của user.
