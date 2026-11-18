# Đo lại jar LF — wave 2 (artifact-keeper), 2026-11-18

Protocol đầy đủ: `../lf-wave1-20261118/PROTOCOL.md`. Jar `evomaster-LF-d559dc73.jar` (sha16 `d559dc730701745e`),
bỏ cờ D1 (phán quyết chỉ C4). Model m2-nodup (`dcc77b59ed0f`), giống ND.

Wave 2 nối tiếp (guard "mỗi lúc một việc nặng"). Trình tự (theo `../nd-wave2-20261113/PROTOCOL.md` +
`docs/targets-bringup.md` §5–6):
1. `docker stop reports-api` để nhả cổng 8080 (wave 1 đã xong).
2. Repo artifact-keeper ở `infra/artifact-keeper-target/src`, HEAD `e56d3aa7` (bản lỗi), status đúng 2 dòng
   (`M docker/Dockerfile.backend.dev`, `?? docker-compose.thesis.yml`).
3. `ak_vuln.sh` 5 seed — tự `reseed.sh full` trước mỗi seed; proxy `capture_proxy.py 8212→8080`;
   `--extraPhaseBudgetPercentage 0.25 --ratePerMinute 600 --maxTime 1200s`, swagger `openapi-trimmed.json`, target :8212.
4. `git checkout e64cc5c608 -- backend .sqlx` → reseed rebuild (~141s) → KIỂM TAY bản vá còn sống
   (token victim cũ 200 → admin hạ quyền 200 → token cũ trả 401) → `ak_fixed.sh` 3 seed.
5. Sau đo: trả repo về `e56d3aa7` sạch (gỡ 3 file bản vá thêm theo targets-bringup §5), backend/.sqlx 0 dòng dirty;
   hạ container artifact-keeper; `docker start reports-api` + reset 200.

## Harness: diff với ND (chỉ JAR/WANT/BASE + nhãn log)

`ak_vuln.sh`, `ak_fixed.sh` vs ND: dòng 5–7 (JAR, WANT, BASE), dòng 79 (nhãn `ND-07ebf19f`→`LF-d559dc73`).
Companion `openapi-trimmed.json`, `artifactkeeper-auth-proxied.yaml`: trùng ND (cmp). Không đổi dòng lệnh EvoMaster,
cờ, seed, luật dừng.

## Luật dừng (trong harness, như ND)

bản vá det970=1 (FP) → dừng; 2 hàng ERR liên tiếp; `Entering Sleep` mới; artifact-keeper seed đầu thiếu đăng nhập
một tài khoản hoặc evaluated < 389. Luật nổ: dừng, ghi lệch luật, tìm nguyên nhân trong log, báo về.

## Cách đếm

Như wave 1: báo cả TN_old (mọi bộ ba Assembled trên bản vá) và TN_403 (follow-up 403), kèm số bộ ba follow-up
khác 2xx/403/401. Bản vá artifact-keeper trả 401 cho token cũ (INCONCLUSIVE) nên thường assembled=0; ghi rõ.

## Kết quả

Chạy 2026-11-18, jar LF-d559dc73. Trình tự: ak_vuln 5 seed (commit lỗi e56d3aa7) → checkout vá e64cc5c608 →
handcheck-clean.sh (kiểm tay) → ak_fixed 3 seed. 0 FP, 0 ERR, 0 sleep, không halt. evaluated mỗi seed ~1510–1600
(≫ NEED_TESTS 389); cả 3 tài khoản đăng nhập mỗi seed (victim ~885, admin ~610, viewer ~645).

| Arm | det970 | Bộ ba (chuẩn) | void | triple |
|---|---|---|---|---|
| vuln (e56d3aa7) | 5/5 | 10 (2/seed) | 6/seed | PATCH /api/v1/users/{id}, 200/200/200 |
| fixed (e64cc5c608) | 0/5→0/3 | 0 | 10/seed | none |

- vuln 5/5 (ND 4/5): logic-fix thêm source POST nên mỗi seed dựng 2 bộ ba — trên `POST /api/v1/admin/analytics/snapshot`
  và `POST /api/v1/admin/backups` (log `* Assembled`), cùng transition `PATCH /api/v1/users/{id}`. Seed ND trượt
  (không dựng được bộ ba) nay có bộ ba và nổ 970. Fisher 5/5 vs 0/3: p=0,017857 (ND 4/5 vs 0/3: p=0,071429).
- Cột `assembled` CSV = 3/seed vì harness grep `transition PATCH.* statuses` bắt thêm dòng
  `* Stateful-authorization transition … proven by an attempt` (1 dòng/transition). Số chuẩn = 2/seed theo
  `* Assembled a stateful`. ND dùng cùng grep nên nhất quán; số báo cáo lấy từ `lf_counts.py`/audit, không từ cột CSV.
- fixed 0 FP, 0 bộ ba: token victim cũ sau hạ quyền trả 401 (INCONCLUSIVE) nên không ghép được follow-up có mã ≠401.
  Giống ND, artifact-keeper bản vá không cho TN (TN_old = TN_403 = 0).

### Kiểm tay bản vá còn sống (`handcheck-clean.sh`, log ở scratchpad phiên `handcheck-fixed-LF.log`)

Sau checkout e64cc5c608 + dựng lại (~132s): [A] victim login is_admin=True → [B] source tạo user bằng token cũ 200 →
[C] viewer tạo 403 → [D] admin PATCH is_admin=false 200 → [E] victim login mới is_admin=False, tạo 403 →
**[F] replay token victim CŨ sau hạ quyền = 401** (bản lỗi = 200), poll +8/16/24/32s đều old=401/fresh=403.
Vendor patch (migration 131 `users_privileges_changed_at` + users.rs/auth_service.rs) sống.

### audit970 (`audit970.out`)

ak-vuln 10 PASS (2/seed), ak-fixed 0 PASS 0 FAIL. Khớp det970.

### Integrity

Không det970=1 thiếu bộ ba; không bộ ba lạ trên bản vá; số bộ ba chuẩn khớp. 0 vấn đề.
