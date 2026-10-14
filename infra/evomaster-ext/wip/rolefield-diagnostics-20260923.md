# Patch role-field + log chẩn đoán — 2026-09-23

Patch tăng dần: `rolefield-diagnostics-20260923.patch` (trên cây `7f85c6af`).
Cả cây: `d1-lexicon-field-harvest-rolefield-20260923.patch`, sha diff `d5a9b00de2af8811`.
Jar `7f9d977e4849080a`, giữ ở `EvoMaster/evomaster-RF-7f9d977e.jar`. Rollback tập 23:25, sha trước và sau `d5a9b00d`.
Duyệt: người dùng cho viết và build không cần xem mã đêm 09-23, với điều kiện self-test đầy đủ.

## Thay đổi

**A. `harvestReducedRoleCandidates`.** Hai dòng đổi hành vi:
- ứng viên không có gene nào tên khớp `roleFieldSignals` trả `[]`, nên vòng ứng viên bỏ qua nó;
- gene `contentTypeGene` của `BodyParam` không vào `enumVocab`.

| Endpoint (Tier-1) | Trước | Sau |
|---|---|---|
| `POST /auth/login`, không có trường role | 1 giá trị (content type) | 0, bị bỏ qua |
| `PUT /users/{username}/role` | 4 giá trị | 3: `[VIEWER, ADMIN, EVOMASTER]` |

**B. Log `debug`**, không đổi hành vi: giá trị role đã chọn, danh sách nguồn được canh, nạn nhân của mỗi nguồn,
operator của mỗi nạn nhân, hết giờ, chạm trần số lần thử, nạn nhân đã bị hạ trong pha, tổng số lần thử cuối pha.

## Self-test `selftest/rolefield-diagnostics.sh`

12/12 đạt trên jar `7f9d977e` (`infra/em-results/rolefield-chain-20260924/selftest-rolefield.txt`).
Các check hỏng được trên jar cũ `2ec4b921`: `field-harvest-chain-20260923/selftest-harvest/bodytype.log` ghi
`POST:/auth/login ... reducedRoleValues 1`, nên `no-role-field-skipped` hỏng; jar cũ không in năm dòng log mới,
nên bốn check `*-logged` hỏng.

## Self-test cũ bị ảnh hưởng

- `local-harvest.sh` `content-type-is-a-value` ghi lại đúng lỗi patch A sửa; trên jar mới nó hỏng. Chuỗi
  `rolefield-chain-20260924/chain.sh` đòi đúng check đó hỏng và sáu check còn lại đạt.
- `field-gate.sh` `body-word-passes-gate` đọc dòng `transition chosen`. `PUT /reports/{id}` không có trường role,
  nên sau patch A nó qua cổng nhưng không được chọn. Check đổi sang đọc ứng viên đầu tiên, tức đầu ra của cổng.
  Trên log jar cũ ứng viên đầu tiên cũng là `PUT:/reports/{id}`, nên check vẫn đạt ở đó.
