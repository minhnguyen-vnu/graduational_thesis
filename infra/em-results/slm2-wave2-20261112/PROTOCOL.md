# Đo lại jar SL+M2 — wave 2 (artifact-keeper), 2026-11-12

Protocol đầy đủ: `../slm2-wave1-20261112/PROTOCOL.md`. Kết quả cả đợt khớp khít M2.

Wave 2 nối tiếp (guard "mỗi lúc một việc nặng"). Dừng container `reports-api` để nhường :8080.
`ak_vuln.sh` 5 seed (commit lỗi `e56d3aa7`) → **5/5** det970, mọi seed triple `PATCH:/api/v1/users/{id}` 200/200/200.
Rồi `git checkout e64cc5c608 -- backend .sqlx` → reseed rebuild (backend up ~54s) → `ak_fixed.sh` 3 seed → **0/3**,
assembled=0 (token cũ trả 401 = INCONCLUSIVE). Jar `evomaster-SLM2-b8b5cf1a.jar`, bỏ cờ D1.

Bản vá xác nhận sống bằng tay trước khi đo (`logs/fixed-manual-reseed.txt` + kiểm 401): token cũ sau hạ quyền trả 401.
Sau đo trả repo về `e56d3aa7` sạch (backend/.sqlx 0 dòng dirty). Audit `audit970.out`: 5 PASS / 0 FAIL / 0 UNPARSED.
Không sự cố, máy không ngủ.
