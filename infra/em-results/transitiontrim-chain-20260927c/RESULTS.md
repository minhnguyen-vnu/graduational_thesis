# Chuỗi transition-trim lần 4 — 2026-09-27

Jar `129a7a56fce83df8` (`EvoMaster/evomaster-TT-129a7a56.jar`), cây `4d2beb47`
(`wip/d1-lexicon-field-harvest-rolefield-postfallback-geneguard-transtrim-20260927c.patch`; mô tả
`wip/transition-trim-20260926.md`). `chain.sh` chạy từ 00:56; cờ D1 tắt; lệnh EvoMaster giống từng cờ
`../rf-seeds11-20-20260925/chain.sh`, trừ jar.

## Kết quả

| Bước | Kết quả |
|---|---|
| Tập rollback | sha `4d2beb47` trước và sau |
| Self-test `transition-trim.sh` 01:33–02:07 | 8/8 (`logs/selftest-transtrim.log`) |
| Cổng hồi quy 02:07–03:54 | 21 dòng, lệch 0 (`logs/gate-observed.csv`) |
| Tier-1 bản lỗi, seeds 1–10 | 970 nổ 10/10 |
| Tier-2 bản lỗi, seeds 1–10 | 3/10: seed 1, 5, 10 |
| pyLoad bản lỗi, seeds 1–10 | 10/10, 0 `Read timed out` |
| Tier-1 và Tier-2 bản đã vá, 20 lần | 0 báo động giả |

Airflow trong self-test: bộ ba đúng cặp `204/200/204`, bị C4 loại (UNCONFIRMED); 0 dòng `Privilege-restore`.
Nguyên nhân UNCONFIRMED: `../transitiontrim-chain-20260927b/RESULTS.md`, mục kiểm tay.

## Ghép từng seed, seeds 1–10

`pairing-seeds1-10.txt`. So với jar `PF` (`../postfallback-chain-20260925/runs-merged.csv`): 50 cặp, 970 mất 0,
thêm 0, 970 trên bản đã vá 0; số VOID và tập mã lỗi trùng cả 50 dòng. So với jar `RF`: như trên, trừ tập mã lỗi
Tier-2 bản lỗi seed 3 và 4, hai dòng chuỗi `RF` đã biết (`../postfallback-chain-20260925/RESULTS.md`).

Sao lưu: `~/thesis-backups/thesis-full-20260927-1027.tar.gz`.

## Seeds 11–20 và pyLoad bản đã vá

Tier-1, Tier-2 hai bản, seeds 11–20: trong chuỗi này, 10:30–14:00. pyLoad bản lỗi seed 11: 14:19. Chuỗi dừng tay
14:20 để ưu tiên Airflow, Vikunja (`progress.log`); không dòng nào mất. pyLoad bản lỗi seeds 12–20:
`../pyload-vuln-tt-12-20-20260927/`. pyLoad bản đã vá seeds 1–20: `../pyload-fixed-tt-20260927/`. Cùng jar, cờ
EvoMaster giống từng dòng (chỉ khác cổng ở nhánh bản đã vá). Gộp: `runs-merged-20seeds.csv`, 120 dòng.

| Target | TP | FN, không bộ ba | FP | TN | Bản đã vá, không bộ ba |
|---|---|---|---|---|---|
| Tier-1 | 19/20 | 1 (seed 17) | 0 | 19 | 1 |
| Tier-2 | 7/20 | 13 | 0 | 7 | 13 |
| pyLoad | 20/20 | 0 | 0 | 20 | 0 |

Bảng tính bằng `infra/analysis/confusion/four_cells.py`, lưu `jar-TT-four-cells.md`. Ghép với jar `R`, Tier-1 và
Tier-2 không reset: 80 cặp, 970 mất 0, thêm 0. 0 `Read timed out` trên 120 dòng.
