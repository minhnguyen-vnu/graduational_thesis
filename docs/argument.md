# Bản đồ lập luận — 2026-09-28, cập nhật 2026-10-14

Mỗi khẳng định của luận văn một mục: con số, đối chứng, trường hợp không do ta viết, giới hạn. Số trích từ file
nguồn ghi bên cạnh; con số nào không có nguồn thì không vào luận văn.

Hai jar chính: `P2e` (`evomaster-P2e-6ae8277b.jar`, mọi số ở `docs/results.md`; bộ gộp P2e/P2d là lệch luật đã khai ở
§0, mọi ô 970 trùng jar `AF2` và jar `R` từng seed) và `TT` (`evomaster-TT-129a7a56.jar`, bộ từ vựng và sáu sửa
builder). Mỗi hàng của bảng chỉ mang số của một jar, ghi ở đầu hàng.

## K1. Khi dựng được bộ ba hợp lệ, oracle phán đúng

| | |
|---|---|
| Con số, jar `P2e` | Không reset: mọi bộ ba dựng được trên bản lỗi đều ra 970 (19/19, 7/7, 5/5); 0 FP trong 90 lượt bản đã vá, trên 116 bộ ba thực hiện trên mã đã vá (`docs/results.md` §1, §1a) |
| Con số, jar `TT` | 20 seeds: TP 19, 7, 20; FP 0 trong 60 lượt bản đã vá; TN 19, 7, 20 (`em-results/transitiontrim-chain-20260927c/RESULTS.md`) |
| Đối chứng | Mỗi target có bản đã vá chỉ khác đúng chỗ lỗi; bộ ba trên bản đã vá đọc `200/200/403` |
| Không do ta viết, jar `TT` | Airflow, `cache_ttl=0`: 2 bộ ba hợp lệ, follow-up 403, không 970 (`em-results/airflow-ttl-20260927/RESULTS.md`). Airflow mặc định: bộ ba `204/200/204` bị C4 loại vì bộ đệm vai trò 30 giây theo user, đúng như kiểm tay 09-20 dự đoán (`analysis/cve-survey/airflow-handcheck-20260920.md` §4) |
| Giới hạn | Airflow là target phát triển từ 09-23. `cache_ttl=0` là cấu hình của ta. "Phát hiện khi có bộ ba hợp lệ" gần như định nghĩa, không trích làm độ chính xác (`docs/results.md` §2) |

## K2. Oracle bắt được lỗi thật

| | |
|---|---|
| Con số, jar `P2e` | pyLoad CVE-2026-41133: bản lỗi 5/5, bản vá 0/5, Fisher một phía p = 0,004 (`docs/results.md` §1) |
| Con số, jar `TT` | pyLoad: bản lỗi 20/20, bản vá 0/20 (`em-results/transitiontrim-chain-20260927c/RESULTS.md`) |
| Con số, jar `P2e` (app công khai) | raouf, nhánh declared: dựng bộ ba, nổ 970; soát tay bản sạch `PATCH /categories` ADMIN 200 / CUSTOMER 403 → TP thật, không phải đọc không-guard (`docs/results.md` §5c). Bốn app held-out (raouf, fastschema, alvaro, magic) đều kiểm tay xác nhận MR-A1 thật |
| Đối chứng | pyLoad bản đã vá |
| Không do ta viết | Lỗi là của pyLoad, upstream chưa vá; bản đối chứng đã vá, endpoint reset và spec ghép là của ta (`docs/tier2b-pyload-target.md` §2, §3) |
| Giới hạn | Một CVE. Trong 11 CVE đã xét, chạy máy bắt được 1; 2 tái hiện được bằng tay nhưng oracle chưa với tới; 3 ngoài lớp; 5 không dựng được hoặc chưa chạy (`analysis/cve-survey/coverage.md` §2). 74 ứng viên còn lại xét 09-28, không cái nào đi tới chạy máy (`analysis/cve-survey/heldout-20260928.md`) |

## K3. Tool tự tìm transition, không cần người khai

| | |
|---|---|
| Con số, jar `P2e` | Naive Bayes trên nhãn vòng 4 (10.381 op ghi, 230 API), kiểm chéo theo nhà cung cấp 5 phần × 4 lần lặp: op T đứng đầu ở 16–18, trong 4 đầu ở 21–25 của 47 spec test (`infra/evomaster-ext/wip/p2-design-20261012.md` §1). Trên target, op T hạng 1 ở reports, vampi, pyLoad, Airflow, bamf, hạng 3 ở artifact-keeper |
| Con số, bộ từ vựng (jar `AF2`, `TT`) | Endpoint `R` hạng 1 ở 4 trong 6 spec test, top-8 ở 6 (`docs/lexicon.md` §7) |
| Con số, bộ từ viết tay (trước jar `L`) | 8 từ path + 9 từ param, `firstOrNull`: 0 trong 6 (`docs/lexicon.md` §1) |
| Đối chứng, jar `P2e` | Thay danh sách viết tay bằng mô hình không đổi phát hiện nào: trên 180 hàng P2e/P2d, số nổ 970 và FP trùng jar `AF2` từng seed ở cả 12 arm (`em-results/p2e-continue-20261013/RESULTS.md`) |
| Đối chứng, jar `L` và `TT` | Thay bộ từ viết tay bằng bộ từ vựng không đổi phát hiện nào: jar `L` 0 trên 30 hàng ghép đôi (`docs/results.md` §5b); jar `TT` Tier-1/2 không reset trùng jar `R` ở 80 cặp seed (`em-results/transitiontrim-chain-20260927c/RESULTS.md`) |
| Không do ta viết, jar `TT` | Airflow: builder tự chọn `PATCH /auth/fab/v1/users/{username}` và hai nguồn, không khai transition (`em-results/airflow-ttl-20260927/`). P2e chưa chạy Airflow |
| Giới hạn | 47 spec test đã bị nhìn nhiều lần khi chọn mô hình: số là thăm dò, không gắn p-value xác nhận; không chênh nào với luật max có p < 0,05. Airflow là target phát triển. Vikunja, jar `TT`: 0 bộ ba, kể cả khi spec có example id (`em-results/vikunja-examples-20260927/RESULTS.md`). Nhãn của bộ từ vựng: kappa người–LLM 0,369; mô hình phân xử 32 dòng (`docs/lexicon.md` §4) |

## K4. Recall thấp có nguyên nhân đo được

| | |
|---|---|
| Con số, jar `P2e` | Mọi FN là lượt không dựng được bộ ba; 0 FN có bộ ba (`docs/results.md` §1a). Tier-2 7/20 |
| Con số, jar `TT` | Mọi FN là lượt không dựng được bộ ba; 0 FN có bộ ba (`infra/analysis/confusion/jar-TT-four-cells.md`) |
| Con số, jar `P2e` (app công khai) | Hai cơ chế FN đo được trên app thật: raouf role field không enum → giá trị hạ quyền lấy từ `lowstr`, sai role thật; magic nguồn `PUT roles` crud-update trả 404 với tên lạ → 0 guarded source candidate (`docs/results.md` §5c). Cùng họ với bamf (`{email}`), artifact-keeper (admin-flip) |
| Đối chứng, jar `P2e` | Nhánh reset: Tier-2 13/20; McNemar p = 0,070, không có ý nghĩa (`docs/results.md` §4) |
| Không do ta viết, jar `TT` | Airflow seed 2: không dựng được bộ ba cặp đúng ở cả hai nhánh (`em-results/airflow-ttl-20260927/RESULTS.md`) |
| Giới hạn | Giới hạn nằm ở search dựng bộ ba, không ở phán quyết. Không viết "nhân quả" cho reset |

## Ranh giới phải viết (`analysis/cve-survey/coverage.md` §4)

1. Transition phải gọi được bằng HTTP.
2. Sau transition phải cấp được chứng chỉ mới để so. Lỗi dạng xoá chủ thể không có chứng chỉ mới.
3. Lỗi "không cưỡng chế với ai cả" (ZITADEL) và bộ đệm theo user (Airflow) bị C4/D1 loại đúng thiết kế; phân biệt
   chỉ bằng so với bản vá.

## Câu hỏi người chấm dễ hỏi, trả lời ở đâu

| Câu hỏi | Trả lời |
|---|---|
| Chỉ một CVE, có phải may? | K2 giới hạn, `coverage.md` |
| Airflow có phải cài cắm? | Image chính thức, không sửa mã; nhưng là target phát triển (K1, K3 giới hạn) |
| Mô hình có quá khớp? | 47 spec test đã bị nhìn nhiều lần (K3 giới hạn); ước lượng sạch cần spec mới |
| Vì sao Tier-2 thấp? | K4 |
| 0 FP có ý nghĩa không? | 116 bộ ba trên mã đã vá, không chỉ 90 lượt (K1) |
