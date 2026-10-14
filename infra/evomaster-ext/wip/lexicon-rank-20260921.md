# Patch nháp: xếp hạng transition thay cho `firstOrNull`

Chưa áp, chưa build. Cần OK trước khi chạy `git apply`.

- Patch: `lexicon-rank-20260921.patch`, `git apply --check -p1` đã qua trên cây làm việc sạch.
- File từ vựng: `infra/analysis/lexicon-rules/lexicon-20260921/stateful-authz-lexicon.csv`
  (63 từ path, 50 từ param, rút từ nửa train đã mở rộng), phải copy vào `core/src/main/resources/` trước khi build.
- Self-test: `infra/evomaster-ext/selftest/lexicon-rank.sh`, 6 kiểm tra.

## Sửa gì

| Chỗ | Trước | Sau |
|---|---|---|
| `RestSecurityBuilder.kt:67` | `TRANSITION_PATH_SIGNALS`, 8 từ cứng | `loadLexicon`, đọc `/stateful-authz-lexicon.csv` |
| `:87` | `TRANSITION_PATH_SIGNALS.any { hay.contains(it) }` | `transitionPathScore(hay) > 0.0` |
| `:363` | `transitionUserParamSignals`, 9 từ cứng | `TRANSITION_USER_PARAM_LEXICON` |
| `:809` `findPermissionReducingTransition` | lọc theo `pathSignal && hasUserParam`, `firstOrNull` theo thứ tự verb | `rankPermissionReducingTransitions`, sắp theo điểm giảm dần |
| `:458` | một transition; `harvestReducedRoleCandidates` rỗng là bỏ cuộc | thử tối đa 8 ứng viên theo thứ tự hạng |

## Hai quyết định cần bạn soi

**Điều kiện tham số không còn là bộ lọc, chỉ là trọng tài khi bằng điểm.** Đo ở
`lexicon-20260920/RESULTS.md` §10: biến thể lọc cứng theo tham số loại luôn endpoint `R` ở 4 trong 6
spec test, mẫu số tụt từ 6 xuống 2. Bản cũ lọc cứng (`:821` `pathSignal && hasUserParam`).

**Giới hạn 8 ứng viên** dùng lại hằng số `MAX_STATEFUL_TRIPLE_ATTEMPTS`. Chưa có bằng chứng 8 là số đúng.
`lexicon-20260921/RESULTS.md` §8 đo trên toàn bộ endpoint của mỗi spec, sau khi gán bù cho hạng thành
chính xác: top-1 `0.500`, top-3 `0.833`, **top-8 `1.000`**. Mọi spec test đều có endpoint `R` trong 8 ứng
viên đầu, không phải trong 3. Con số 8 là con số đo được. Hạ xuống 3 mất một trong sáu spec.

## Chưa chứng minh

- Chưa build, chưa chạy self-test.
- Chưa qua cổng hồi quy, chưa chạy seeds 1–10. Mọi số ở `docs/results.md` vẫn thuộc jar R.
- File từ vựng sinh từ 39 dòng `R` trên 11 nhà cung cấp của nửa train đã mở rộng
  (`lexicon-20260921/RESULTS.md`). Chưa có lượt người nào trên 253 dòng mới.
- Trên cả ba target, xếp hạng đưa transition thật lên hạng 1 khi chạy trên toàn bộ endpoint
  (`lexicon-20260921/RESULTS.md` §6). Trên vampi `role` được 0.273, `email` 0.222, `password` 0.214.
  Chưa lần chạy EvoMaster nào xác nhận.
