# Kế hoạch đo tháng 10 — nháp 2026-09-27

Nháp để người dùng duyệt ngày 09-30. Chưa có con số kỳ vọng nào trong file này. Giờ máy tính từ thời gian chạy
đã đo; mỗi lúc một job nặng, nên giờ máy là giờ đồng hồ.

## 1. Thời gian một lượt, đo được

| Target | Một lượt | Nguồn |
|---|---|---|
| Tier-1, Tier-2 | ~5 phút | `em-results/transitiontrim-chain-20260927c/progress.log`, 4m50s giữa hai dòng |
| pyLoad | ~19 phút | `postfallback-chain-20260925/rerun-progress.log`, 8 lượt trong 149 phút |
| Airflow | ~24 phút | `gg-overnight-20260926/progress.log`, 22:59–23:23 |
| Vikunja | ~23 phút | `vikunja-postfallback-20260925/progress.log`, 11:07–11:30 |

Một bộ đầy đủ, không reset, 20 seeds, bản lỗi và bản đã vá của ba target: 40×5 + 40×5 + 40×19 phút ≈ 19 giờ.
Thêm nhánh reset: gấp đôi.

## 2. Jar

Jar đóng băng ngày 09-30. Ứng viên: `TT-129a7a56` nếu seeds 11–20 sạch (`em-results/transitiontrim-chain-20260927c/`).
Mọi con số tháng 10 ghi tên jar; bảng không trộn jar.

Cập nhật 2026-10-04: jar trích số đã chốt là `AF2-6b5606d4` (commit `8d6cf8431f`), tái lập jar `R` từng seed
(`af2-full-remeasure-20261003/`). Bảng §3 giữ nhãn jar của bản nháp 09-27.

## 3. Các nhánh

| # | Nhánh | Đo gì | Lượt | Giờ | Dữ liệu đã có |
|---|---|---|---|---|---|
| A1 | jar `R`, cờ D1 tắt | điểm xuất phát | — | 0 | `docs/results.md` §1, pyLoad chỉ 5 seeds |
| A2 | jar `R`, pyLoad seeds 6–20 | cho đủ 20 seeds như Tier-1/2 | 30 | 9,5 | không |
| B1 | jar đóng băng, cờ D1 tắt | từ vựng + các sửa builder | 20 còn thiếu | 6,5 | seeds 1–20 Tier-1/2 và pyLoad bản lỗi (đang chạy); thiếu pyLoad bản đã vá |
| B2 | jar đóng băng, cờ D1 bật | phán quyết hai chứng chỉ | 100 | 19 | không |
| B3 | B1 và B2, nhánh reset | ablation reset | 200 | 38 | không |
| C1 | Airflow, `cache_ttl=0`, seeds 1–10 | app thật, bộ ba hợp lệ | 10 | 4 | seeds 1–3 chạy tối 09-27 |
| C2 | Vikunja, spec có example, seeds 1–10 | app thật, mặt âm tính | 20 | 8 | seeds 1–2 chạy tối 09-27 |
| D | tắt từng thành phần: từ vựng, cổng trường thân, thu giá trị cục bộ, POST fallback, transition trim | đóng góp từng phần | 5 × (Airflow 5 + Tier-1/2 10) | ~25 | không |
| F | Vikunja CVE-2026-35594, thu hồi link share, chạy máy | TP trên CVE thật thứ hai; chuẩn bị từ 09-27 | 10 | 4 | không |
| E | LLM phân loại transition | so với từ vựng trên nửa test | offline | 0 | không |

B1 so với A1 trả lời "thay bộ từ và sửa builder có mất phát hiện nào không". B2 so với B1 trả lời "D1 đổi gì".
Bảng bốn ô theo tier (`infra/analysis/confusion/four_cells.py`) chạy trên mọi nhánh.

D cần cờ tắt cho từng thành phần, tức một thay đổi mã kèm self-test. E chạy trên corpus đã gán nhãn, không cần
EvoMaster.

Tổng A2 + B1–B3 + C + D: khoảng 110 giờ máy, chừng 5–6 ngày đêm chạy liền.

## 4. Thay đổi mã còn lại

| Việc | Vì sao | Đo lại |
|---|---|---|
| Xuất bước khôi phục quyền vào test sinh ra | replay Tier-1 no-reset seed 16 hỏng vì thiếu bước này | replay 58 lượt |
| Cờ tắt từng thành phần | nhánh D | gate |
| Gán giá trị vào mảng object (`roles: [{"name": ...}]`) | Airflow hiện chỉ gửi `roles: []`; khôi phục quyền không làm được | self-test Airflow |
| Chủ động dựng nguồn (D2) | Vikunja: nguồn thiếu nạn nhân | ngoài phạm vi nếu hết giờ |

## 5. Thứ tự đề xuất

1. B1 cho đủ (pyLoad bản đã vá), rồi B2: hai nhánh trả lời câu hỏi chính.
2. C1, C2: bằng chứng ngoài lỗi tự cài.
3. A2, B3.
4. D, E nếu còn giờ.

Lý lẽ ngược lại: D cho biết thành phần nào đáng giá, người chấm có thể hỏi trước B3. Đổi chỗ 3 và 4 là hợp lý nếu
thời gian viết chương cần D sớm.

## 6. Luật dừng, viết trước khi chạy

- Gate hỏng ở một dòng bản đã vá: dừng chuỗi, không đo tiếp jar đó.
- Một lượt ERR vì target treo: giữ dòng ERR, chạy lại lượt đó cùng jar và cùng lệnh sau khi dựng lại target.
- Không đổi luật đếm sau khi thấy số.
