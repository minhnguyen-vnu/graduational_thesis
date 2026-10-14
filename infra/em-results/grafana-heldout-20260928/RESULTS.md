# Grafana OSS 12.1.1, held-out, jar `TT` — 2026-09-28

Giao thức: `infra/analysis/cve-survey/heldout-20260928.md` §3. Harness `run.sh`, dòng từng lượt `runs.csv`,
log `logs/`, request `traffic/`.

## Kết quả

| Nhánh | Seeds | 970 | Bộ ba hợp lệ | VOID | UNCONFIRMED | Mã bộ ba |
|---|---|---|---|---|---|---|
| `auto` | 1–6 | 0 | 0 | 36 | 0 | tất cả `200/404/200` |
| `declared` | 1–6 | 0 | 0 | 0 | 6 | tất cả `200/200/200` |

FP 0, TN 0: không bộ ba hợp lệ nào để phán. 12/12 lượt exit 0.

## Sai lệch

Giao thức ghi seeds 1–10. Dừng sau seed 6 hai nhánh, 14:51, quyết định của user: 11 lượt đầu cùng một mẫu mỗi
nhánh. `logs/auto-seed7-600s-up.txt` là container của lượt 7 bị dừng giữa chừng, không có lượt chạy.

## Nguyên nhân, đọc từ log và request

1. `auto`: builder chọn `PUT /api/access-control/roles/{roleUID}` ở cả 6 seed. Route không tồn tại trên bản OSS
   này: 197 request tới `/api/access-control/roles*` trong 12 lượt, cả GET, POST, PUT, DELETE, đều
   `404 {"message":"Not found"}`. Có thể là tính năng chỉ bản Enterprise có; chưa kiểm với tài liệu Grafana.
2. Nạn nhân luôn là `admin`: trong 12 lượt, mọi nguồn có nạn nhân đều ghi `victims [admin]`, dù `victim` cũng là
   Admin của org. Cơ chế, kiểm 09-29: search không gửi request nào bằng `victim`. EvoMaster khởi đầu bằng một test
   mỗi endpoint cho từng tài khoản, lấy từ cuối danh sách (`RestSampler.kt:322–346`, `:46`): `viewer`, rồi `admin`,
   rồi `victim`. Seed 1 có 309 endpoint và 592 test: `viewer` 309, `admin` 283 (`traffic/auto-seed1-600s.jsonl`).
   `victim` chỉ đăng nhập từ phút 18, trong pha security.
3. `declared`: transition khai `user_id=2` hạ `victim`, còn follow-up phát lại token của `admin`; `admin` vẫn là
   Admin nên 200, C4 đăng nhập lại `admin` cũng 200, bộ ba bị loại UNCONFIRMED.
4. Dù chọn đúng `PATCH /api/org/users/{user_id}`, builder ghi tên tài khoản (`victim`) vào `user_id` kiểu số
   (`setUserTargetToVictim`, `:999`) và không thành. Id `2` có trong response `GET /api/org/users` của chính lượt
   chạy (`"userId":2,"login":"victim"`).

Grafana thành target phát triển cho jar sau `TT` (CLAUDE.md §5).

## Thời gian mỗi lượt

24 phút cho `--maxTime 600s`: search 10 phút, minimization 8,5 phút (chạy lại 493 test ở `--ratePerMinute 60`),
security 6 phút, trong đó phần 970 khoảng 15 giây (`logs/auto-seed5-600s.log`).
