# Chuỗi gene-set-guard — 2026-09-25

Jar `a6839ada5b839465` (`EvoMaster/evomaster-GG-a6839ada.jar`) = jar `PF` (`0607485b`) cộng
`infra/evomaster-ext/wip/gene-set-guard-20260925.patch`. Cây làm việc `66bffda62766c472`
(`wip/d1-lexicon-field-harvest-rolefield-postfallback-geneguard-20260925.patch`). `chain.sh` chờ `CHAIN DONE` của
`../postfallback-chain-20260925/`, rồi chạy 08:12–11:33; cờ D1 tắt.

## Kết quả

| Bước | Kết quả |
|---|---|
| Áp patch, tập rollback | sha `66bffda6` trước và sau |
| Self-test mới `gene-set-guard.sh` | 6/6 đạt, `logs/selftest-geneguard.log` |
| Self-test `post-fallback.sh` trên jar mới | 6/6 đạt, `logs/selftest-postfallback.log`; trên jar `PF` là 5/6 |
| Cổng hồi quy | 21 dòng, lệch 0 (`logs/gate-observed.csv`) |
| Vikunja seed 1 (`../vikunja-postfallback-20260925/logs/gg-seed1.log`) | exit 0; 9 nguồn POST, 0 nạn nhân, 0 bộ ba |

Không chạy lại seeds: một lượt chạy chỉ khác jar `PF` khi jar `PF` đã ném lỗi ở một trong 4 chỗ được bọc, và
lượt đó là một lượt crash (`wip/gene-set-guard-20260925.md`).

## Airflow seed 1 (`selftest-geneguard/airflow-seed1.log`)

Hết crash: exit 0, mã lỗi `[100]`. Năm lần thử bộ ba trên nguồn `POST /api/v2/connections/defaults`, cả năm VOID:

| Nạn nhân | Người thao tác | Mã source/transition/follow-up |
|---|---|---|
| admin | victim | 204/403/204 (hai lần) |
| admin | viewer | 204/403/204 |
| victim | admin | 204/**422**/204 |
| victim | viewer | 204/403/204 |

Khôi phục quyền cho `victim` do `admin`: `admin` 422, `administrator` 200, `owner` 422.
`sources exhausted after 5 triple attempts`.

Bộ ba đúng hình (nạn nhân `victim`, người thao tác `admin`) dừng ở transition 422. Curl trên user thử `probe`
2026-09-25 09:45, `PATCH /auth/fab/v1/users/probe`:

| Body | Mã |
|---|---|
| `{"first_name":""}` | 422 `string_too_short` |
| `{"extra":1}` | 422 `extra_forbidden` |
| `{"username":"zzq"}` | 200, user đổi tên thành `zzq` |
| `{"roles":null}` | 200, vai trò không đổi |
| `{"email":"abc"}`, `{"password":"x"}` | 200 |
| `{"roles":[]}` với `?update_mask=abc` | 400 `Unknown update masks` |

Body thật của lần transition 422 không có trong log: bộ ba VOID không được xuất thành test. Chuỗi rỗng trong một
trường tên là một nguyên nhân khớp với 422, chưa kiểm. Lần khôi phục 200 với `administrator` có thể đã gửi
`roles: null` (không đổi gì) hoặc `roles: []` (gỡ hết vai trò); log không phân biệt được.

Sao lưu: `~/thesis-backups/thesis-full-20260925-1130.tar.gz`.
