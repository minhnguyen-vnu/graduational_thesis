# Chạy lại các dòng máy ngủ làm hỏng, jar `VI-d2325da7` — 2026-09-29

Lý do: `victimid-chain-20260928/` chạy trong lúc máy ngủ từ 21:46 (pmset `Clamshell Sleep`); Tier-2 bản đã sửa
seeds 4–10 và pyLoad seeds 1–10 bị hỏng. Script `rerun.sh` (seeds pyLoad 1–3, 09:2x–10:04), `rerun-cont.sh`
(phần còn lại, 16:19–19:09), cả hai bọc `caffeinate -dims`, ghi `sleep_events` mỗi dòng.

## Kết quả

| Target | Seeds | 970 | Bộ ba hợp lệ | sleep_events |
|---|---|---|---|---|
| pyLoad bản lỗi | 1–10 | 10/10 | 10, đều `200/200/200` | 0 |
| Tier-2 bản đã sửa | 4–10 | 0/7 | 2, đều `200/200/403` | 0 |

So với jar `TT` (`transitiontrim-chain-20260927c/runs.csv`) trên cột 970, bộ ba, VOID, mã và tập lỗi: 17/17 dòng
giống. 37 dòng trước 21:46 của `victimid-chain-20260928/` cũng giống jar `TT` (CLAUDE.md §5).

## Sai lệch

Dừng chủ động 10:04:54 sau pyLoad seed 3 để nhường máy cho app held-out nhỏ (user, 09-29); chạy tiếp 16:19.
Sao lưu `~/thesis-backups/thesis-full-20260929-1909.tar.gz`.
