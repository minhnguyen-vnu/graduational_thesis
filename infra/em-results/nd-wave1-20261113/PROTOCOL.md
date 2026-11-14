# Đo lại jar ND (shorten-logic committed + nodup-tokens, model m2-nodup), 2026-11-13

Chạy lại cả bốn target với jar ND để đo lại đầy đủ sau khi đổi mô hình chọn transition và viết lại `tokens()`.
Thư mục: wave 1 ở đây, wave 2 ở `../nd-wave2-20261113/`. Phiên `graduational-thesis-37` chuyển lời user (user đang
ngủ), chạy theo đúng PROTOCOL đợt SLM2 (`../slm2-wave1-20261112/`).

## Jar

`EvoMaster/evomaster-ND-07ebf19f.jar` = HEAD `2c3f281f13` (shorten-logic đã commit, chỉ phần mã) + bản vá chưa commit
`infra/evomaster-ext/wip/nodup-tokens-20261113.patch` + `stateful-authz-model.csv` thay bằng m2-nodup
(`infra/analysis/lexicon-rules/m2-nodup-20261112/stateful-authz-model.csv`, sha256 `dcc77b59ed0f…`).
sha256 jar `07ebf19f9682497e8a9a637e99d66e63e15bf72db4c6f985f92bb656af143897`, sha16 `07ebf19f9682497e`.
Kiểm trước đợt: sha256 jar khớp file `.sha256` cạnh jar; model trong jar `dcc77b59ed0f94ee` khớp model trên đĩa;
`EMConfig` không in cờ `statefulAuthz*` (bằng SLM2/M2). Mỗi harness chặn nếu sha16 khác `07ebf19f9682497e`.

Hai thay đổi so với SLM2 (`infra/evomaster-ext/wip/nodup-tokens-20261113.md`):
1. `opFeatures` bỏ đặc trưng `f:` lấy từ tham số path; mô hình học lại tương ứng, chỉ bảng op đổi.
2. `tokens()` viết lại không dùng regex, đã chứng minh tương đương.
Self-test: `infra/em-results/nodup-tokens-selftest-20261113-002956/selftest.out` (90 PASS, 0 FAIL, exit 0).

## Mục đích

Mô hình chọn transition đổi (m2-nodup) nên cách dựng bộ ba có thể đổi. Jar mới chỉ trích được số sau một lượt đo đầy
đủ (CLAUDE.md §5). Đợt này đo thẳng mọi arm không reset, so từng target với bộ SLM2 đã lưu
(`../slm2-wave1-20261112/`, `../slm2-wave2-20261112/`): số 970 và hàng nào đổi transition/bộ ba. Không qua cổng 12/21
hàng.

## Cờ

Giống hệt đợt SLM2 (bỏ `--statefulAuthzTwoCredentialJudgment`; phán quyết chỉ C4). `--useExperimentalOracles true`;
`--extraPhaseBudgetPercentage` 0,6 (reports/vampi/pyLoad) hoặc 0,25 (artifact-keeper). Tier-1/2 `--maxTime 150s`;
pyLoad `10m`; artifact-keeper `1200s`. Mỗi JVM `-Xmx2g`. Reseed SUT trước mỗi lượt. Mỗi làn `cd` một thư mục riêng.

## Thứ tự

- Wave 1 (`nd_wave1.sh`): 6 làn **song song** — reports lỗi :8080 / vá :8081, vampi :5002 / :5003, pyLoad :8090 /
  :8091. 20 seed mỗi làn reports/vampi, 5 mỗi làn pyLoad. Gộp `runs.csv` (90 hàng).
- Wave 2 (`../nd-wave2-20261113/`): **nối tiếp** (guard "mỗi lúc một việc nặng"). Dừng container `reports-api` (:8080)
  nhường artifact-keeper. `ak_vuln.sh` 5 seed (commit lỗi `e56d3aa7`), rồi checkout commit vá `e64cc5c608` + `.sqlx` →
  rebuild → kiểm tay bản vá còn sống → `ak_fixed.sh` 3 seed. Sau đo: trả repo về `e56d3aa7` sạch.

## Harness: diff với SLM2 (chỉ JAR/WANT/BASE + nhãn log)

`nd_wave1.sh` vs `slm2_wave1.sh`: dòng 6–8 (JAR, WANT, BASE), dòng 14 và 127 (nhãn `M2`→`ND`).
`ak_vuln.sh`, `ak_fixed.sh` vs SLM2: dòng 5–7 (JAR, WANT, BASE), dòng 79 (nhãn `SLM2-b8b5cf1a`→`ND-07ebf19f`).
Companion `openapi-trimmed.json`, `artifactkeeper-auth-proxied.yaml`: giống hệt (cmp). Không đổi dòng lệnh EvoMaster,
cờ, seed, luật dừng.

## Luật dừng (viết trước lượt chạy, nằm trong harness)

Như đợt SLM2. Mỗi làn tự kiểm sau mỗi hàng; luật nổ thì dừng làn (`STOPPED`/`DUNG`): bản vá có det970=1 (FP); arm lỗi
3 hàng đầu assembled=0; 2 hàng ERR liên tiếp; có `Entering Sleep` mới trong lúc một hàng chạy; artifact-keeper seed đầu
thiếu đăng nhập một tài khoản hoặc evaluated < 389.

## Lệch luật đã khai

1. **Chạy song song** 6 làn wave 1, theo pattern user đã cho ở đợt SLM2. Wave 2 nối tiếp.
2. **Bỏ cờ D1** `--statefulAuthzTwoCredentialJudgment` (jar không có cờ này). Phán quyết chỉ C4.
3. **Không qua cổng 12/21 hàng**: jar không reset, đo arm không reset thẳng, so bộ SLM2 đã lưu.

## Kết quả

| Target | ND lỗi | ND vá | SLM2 (12/11) |
|---|---|---|---|
| reports-api | 19/20 | 0/20 | 19/20, 0/20 |
| vampi-seeded | 6/20 | 0/20 | 7/20, 0/20 |
| pyLoad | 5/5 | 0/5 | 5/5, 0/5 |
| artifact-keeper | 4/5 | 0/3 | 5/5, 0/3 |

98 hàng (90 wave 1 + 8 wave 2). Integrity: 0 hàng det970 thiếu bộ ba, 0 FP bản vá, 0 ERR, không máy ngủ, không luật
dừng nổ. Audit (`audit970.out`, phạm vi như SLM2 = arm vuln reports+vampi): **25 PASS / 0 FAIL / 0 UNPARSED** (SLM2 26;
ND 25 vì vampi 6 thay vì 7). Wave 2 audit (`../nd-wave2-20261113/audit970.out`): **4 PASS / 0 FAIL** (SLM2 5). pyLoad
không parse được (cookie phiên); CSV + log builder xác nhận bộ ba 200/200/200 ở 5 seed vuln, 403 ở bản vá.

## Khác SLM2 — đúng 2 seed, cùng cơ chế

Mô hình m2-nodup đổi điểm chọn transition → quỹ đạo search đổi → hai seed biên không dựng được bộ ba trong ngân sách.
Cả hai là FN do không có bộ ba, không phải phán quyết sai; detector (VOID/assemble/phán quyết) không đổi; 0 FP.

1. **vampi vuln seed 15**: SLM2 dựng bộ ba trên `PUT:/books/v1/{book_title}/secret` (victim `name1`,
   transition `PUT:/users/v1/{username}/role`, 200/200/200 → nổ). ND cùng source nhưng mọi attempt source victim trả
   **401** (INCONCLUSIVE) → 6 attempt VOID, không dựng được bộ ba. 19 seed còn lại giống hệt SLM2.
2. **artifact-keeper vuln seed 3**: SLM2 dựng bộ ba trên `POST:/api/v1/admin/analytics/snapshot` (victim `victim`,
   transition `PATCH:/api/v1/users/{id}`, 200/200/200). ND search bám source khác `PUT:/api/v1/admin/sso/ldap/{id}`
   (victim `operator`); các attempt 200/200/200 ở đó bị VOID đúng (transition không hạ quyền thật liên quan source,
   guard loại). 4 seed còn lại (1,2,4,5) dựng bộ ba `PATCH:/api/v1/users/{id}` 200/200/200 như SLM2.

Bản vá artifact-keeper xác nhận sống bằng tay trước khi đo FP (`../nd-wave2-20261113/logs/fixed-manual-reseed.txt` +
probe 401): token victim cũ tạo user 200 → admin hạ quyền victim 200 → dùng lại token cũ trả **401**.

## Sự cố

Không. Máy không ngủ (0 `Entering Sleep` kể từ 02:50), AC suốt. Reseed bản vá rebuild backend ~141s (cargo biên dịch lại
`auth_service.rs`+`users.rs`), các reseed khác ~57–60s. Sau đo trả repo artifact-keeper về `e56d3aa7` sạch
(backend/.sqlx 0 dòng dirty), hạ container artifact-keeper, bật lại reports-api :8080 (reset 200). Chưa commit, chưa
promote. Jar ND chỉ trích số sau lượt đầy đủ này; phiên `graduational-thesis-37` cập nhật docs.
