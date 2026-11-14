# Đo lại jar ND — wave 2 (artifact-keeper), 2026-11-13

Protocol đầy đủ: `../nd-wave1-20261113/PROTOCOL.md`. Jar `evomaster-ND-07ebf19f.jar`, bỏ cờ D1.

Wave 2 nối tiếp (guard "mỗi lúc một việc nặng"). Dừng container `reports-api` để nhường :8080.
`ak_vuln.sh` 5 seed (commit lỗi `e56d3aa7`). Rồi `git checkout e64cc5c608 -- backend .sqlx` → reseed rebuild →
kiểm tay bản vá còn sống (token cũ sau hạ quyền trả 401) → `ak_fixed.sh` 3 seed.
Sau đo trả repo về `e56d3aa7` sạch (backend/.sqlx 0 dòng dirty).

## Kết quả

`ak_vuln.sh` 5 seed → **4/5** det970 (seed 1,2,4,5 bộ ba `PATCH:/api/v1/users/{id}` 200/200/200; seed 3 không dựng
được bộ ba, FN — xem `../nd-wave1-20261113/PROTOCOL.md`). `ak_fixed.sh` 3 seed → **0/3**, mọi seed assembled=0
(token cũ trả 401 = INCONCLUSIVE). SLM2 là 5/5 và 0/3. Audit `audit970.out`: **4 PASS / 0 FAIL / 0 UNPARSED**.
3 tài khoản đăng nhập đủ mỗi seed, evaluated 1518–1607 (≥ 389).

Bản vá kiểm tay còn sống trước khi đo FP (`logs/fixed-manual-reseed.txt`, backend up ~141s + probe): token victim cũ
200 → admin hạ quyền 200 → token cũ **401**. Sau đo trả repo về `e56d3aa7` sạch (backend/.sqlx 0 dòng dirty).
Không sự cố, máy không ngủ.
