# Mattermost 11.11.1, held-out, jar `VI-d2325da7` — lượt 1, 2026-09-28

Giao thức: `infra/analysis/cve-survey/heldout-20260928.md` §3. Harness `run.sh`, dòng từng lượt `runs.csv`, log
`logs/`, request `traffic/`.

## Kết quả

| Nhánh | Seeds | 970 | Bộ ba hợp lệ | VOID | UNCONFIRMED | Lần thử bộ ba |
|---|---|---|---|---|---|---|
| `auto` | 1–3 | 0 | 0 | 0 | 0 | 0 |

FP 0, TN 0. 3/3 lượt exit 0.

## Sai lệch

Giao thức ghi seeds 1–10. Luật dừng sớm kích hoạt sau seed 3, 17:08:46: 3 seed cùng mẫu, 0 bộ ba hợp lệ.

## Nguyên nhân, đọc từ log, request và mã EvoMaster

Builder chọn `PUT /api/v4/roles/{role_id}/patch` ở cả 3 seed; 59–62 nguồn có guard, nguồn nào cũng `victims []`,
`sources exhausted after 0 triple attempts` (`logs/auto-seed1-300s-evomaster-VI-d2325da7.log`, 16:38:45).

Không nguồn nào có nạn nhân vì search không gửi request nào bằng `victim`:

| Seed | Đăng nhập trong 300 s search | Cả lượt |
|---|---|---|
| 1 | viewer 623, admin 35, victim 0 | viewer 1538, admin 44, victim 0 |
| 2 | viewer 623, admin 37, victim 0 | viewer 1531, admin 52, victim 0 |
| 3 | viewer 623, admin 36, victim 0 | viewer 1537, admin 54, victim 0 |

Mỗi test đăng nhập một lần: seed 1 có 1582 token khác nhau cho 1582 lần đăng nhập. Test sinh ra ở seed 1 đăng nhập
`viewer` 620 lần, `admin` 9, `victim` 0.

Cơ chế, `RestSampler.kt:322–346` và `:46` (upstream): lúc khởi đầu EvoMaster tạo một test cho mỗi endpoint, lần lượt
cho không-auth rồi từng tài khoản theo thứ tự trong file auth, và lấy test từ cuối danh sách. Thứ tự chạy là `viewer`,
`admin`, `victim`, không-auth, mỗi khối 623 test. Search 300 s ở `--ratePerMinute 300` đánh giá 658–659 test
(`Evaluated tests`), hết khối `viewer` và 35–37 test đầu khối `admin`.

Cùng cơ chế giải thích nguyên nhân 2 của Grafana (`em-results/grafana-heldout-20260928/RESULTS.md`): 309 endpoint,
592 test, `viewer` 309 rồi `admin` 283, `victim` chưa tới. Vikunja (153 endpoint, 593 test) và Airflow (140 endpoint,
574 test) chạy hết ba khối tài khoản.

Lượt 2 đổi ngân sách search, không đổi builder: giao thức ghi trước lượt 2 ở `heldout-20260928.md` §3.
