# M2 model rerun — wave 2 (bamf, artifact-keeper), 2026-11-08

Protocol đầy đủ của cả đợt M2: `../m2-wave1-20261108/PROTOCOL.md`. Kết quả: `docs/results.md` §1, §5, §7.

Wave 2 chạy nối tiếp (guard "mỗi lúc một việc nặng"): bamf (`bamf.sh`, 10 seed, proxy 8213) → artifact-keeper lỗi
(`ak_vuln.sh`, 5 seed) → bản vá vendor (`ak_fixed.sh`, 3 seed). Jar `evomaster-M2-917c57dd.jar`, bỏ cờ D1.
bamf 0/10; artifact-keeper lỗi 5/5, bản vá `e64cc5c608` 0/3 (xác nhận vá sống bằng tay, mã trả về `e56d3aa7e2`).
Lệch luật và sự cố (ngủ cạn pin 07:05, Docker treo + restart, redo seed 2, checkout `.sqlx`): protocol wave 1 §Lệch.
