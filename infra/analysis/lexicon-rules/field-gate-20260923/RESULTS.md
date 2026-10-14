# Cổng chặn đọc thêm tên trường thân yêu cầu — đo 2026-09-23

Luật `../rules-draft.md` §13, viết lúc 12:42 trước khi `rank_field.py` tồn tại.
Chạy: `python3 ../rank_field.py rank-field.txt` và `python3 ../rank_targets.py <thu-muc-spec>`.
Bộ từ vựng không đổi: `../lexicon-20260921-audited/stateful-authz-lexicon.csv`.

## 1. Chọn biến thể trên nửa train

| Biến thể | top-1 thứ tự spec | top-3 | top-8 |
|---|---|---|---|
| V0 (đang chạy trong jar `L`) | 0.500 | 0.800 | 1.000 |
| **V1** (một bộ từ vựng, path + trường thân) | **0.500** | **0.900** | 1.000 |
| V2 (hai bộ từ vựng, lấy max) | 0.500 | 0.800 | 1.000 |

Ba biến thể hoà ở top-1. §13.4 khai trước: hoà thì lấy V1, vì nó không thêm dữ liệu vào file từ vựng.
**Chọn V1.** Biến thể được chọn bằng luật phá hoà đã khai, không bằng con số nửa test.

## 2. Ba điều kiện nhận của §13.5

| | Điều kiện | Kết quả |
|---|---|---|
| 1 | top-1 nửa train của V1 không thấp hơn V0 | `0.500` = `0.500` ✔ |
| 2 | `PATCH /auth/fab/v1/users/{username}` của Airflow qua cổng | điểm `0.3000` ✔ |
| 3 | ba target của luận văn giữ hạng 1 | Tier-1, Tier-2, pyLoad đều hạng 1 ✔ |

## 3. Airflow

| Bộ chọn | Ứng viên / 68 endpoint ghi | Hạng của `PATCH /auth/fab/v1/users/{username}` | Điểm |
|---|---|---|---|
| 8 từ cứng (trước patch) | 3 | **không qua cổng** | 0.0000 |
| V0, bộ từ vựng đang chạy | 17 | 4–13 | 0.2000 |
| V1 | 37 | **1–5** | 0.3000 |

Hai chỗ đáng ghi.

**Bộ từ vựng đã đóng vào jar `L` tự nó đã mở được cổng Airflow.** Tám từ cứng
(`role permission member subscription plan owner grant access`) không từ nào trúng
`/auth/fab/v1/users/{username}`; bộ rút từ corpus trúng `user` (`0.2000`). `CLAUDE.md` §6 viết
"builder không tìm thấy transition nào" — câu đó nói về jar trước, không còn đúng với jar `L`.
Chưa có lần chạy EvoMaster nào trên Airflow với jar `L` xác nhận.

**V1 nâng nó lên nhóm hạng nhất** vì trường thân `roles` trúng từ `roles` (`0.3000`), cao hơn `user`.
Sáu trường thân của endpoint đó: `email, first_name, last_name, password, roles, username`.

## 4. Nửa test, báo một lần

| Biến thể | top-1 | top-3 | top-8 |
|---|---|---|---|
| V0 | 0.500 | 0.667 | 1.000 |
| **V1** | **0.667** | **0.833** | 1.000 |
| V2 | 0.333 | 0.500 | 0.833 |

Chênh lệch V0→V1 nằm ở đúng một spec: S108 từ hạng 6 lên hạng 1, đúng spec mà lượt soát nhãn đã làm
tụt (`../lexicon-20260921-audited/RESULTS.md` §6). Endpoint `R` của S108 là
`DELETE /repos/{owner}/{repo}/collaborators/{collaborator}`; nó lên hạng vì trường thân của các endpoint
đứng trên không kéo chúng lên, còn nó thì có.

V2 xấu hơn hẳn: S116 tụt từ hạng 1 xuống 24–27. Bộ từ vựng `field` riêng chứa những từ chung chung
(`description`, `enabled`, `public`) với điểm đủ cao để kéo endpoint không liên quan lên trước. Đây là lý do
không nhân hệ số cho vế trường mà cũng không tách bộ.

## 5. Giá phải trả

Số ứng viên qua cổng tăng: Tier-1 từ 1 lên 2, pyLoad từ 8 lên 17, Airflow từ 17 lên 37.
Hôm nay không tốn gì vì `MAX_TRANSITION_CANDIDATES = 8` chưa có tác dụng lúc chạy
(`../lexicon-20260921-audited/RESULTS.md` §9). Nếu sửa chỗ thu giá trị quyền thành cục bộ thì mỗi ứng viên
thêm là một lần dựng bộ ba, và con số này thành chi phí thật.

## 6. Chưa chứng minh

- Chưa có dòng Kotlin nào. Chưa build, chưa self-test, chưa qua cổng hồi quy.
- Nửa test đã bị dùng để phát triển từ 09-20 (`../rules-draft.md` §12.5); mục 4 là số báo cáo, không phải
  ước lượng trên dữ liệu giữ riêng.
- Ba target và Airflow xếp hạng từ spec tĩnh, không phải từ `actionDefinitions` của EvoMaster.
  EvoMaster có thể loại bớt endpoint trước khi xếp; con số 68 và 62 là số endpoint ghi trong spec.
