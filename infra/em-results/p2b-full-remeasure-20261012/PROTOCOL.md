# P2b full re-measure — §4 numbers on jar P2b (93db089f)

P2b (`wip/p2-nb-20261012.patch`, commit `8d6cf8431f` + patch) thay toàn bộ danh sách viết
tay bằng Naive Bayes mức op và mức trường (B1/B3), giá trị theo kiểu (B2), đọc phản hồi theo
khoá danh tính (B4), đối chứng ẩn danh (D1+C4), cổng = posterior > 0,5. Cách dựng bộ ba đổi
lớn, nên §4 (jar AF2) không mang sang: cần một lượt seeds đầy đủ (CLAUDE.md §6: "thay đổi
lớn … chờ một lượt đầy đủ"). P2b qua cổng hồi quy 21/21 MATCH 2026-10-12.

## Jar under test
`/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-P2b-93db089f.jar`
sha256 `93db089f…`, trùng byte với `core/target/evomaster.jar` lúc dựng và với jar đã qua cổng.

## What is measured
Bảng §4, chạy lại trên P2b. Hai arm chỉ khác một biến (jar giữ cố định, cờ chép byte-for-byte
từ harness AF2 `af2_full_remeasure.sh`). Harness không mã hoá kết quả mong đợi.

| Tier | Target | Arms (seeds) | Runs |
|---|---|---|---|
| 1 | reports-api :8080/:8081 | vuln·noreset, fixed·noreset, vuln·reset, fixed·reset (1–20) | 80 |
| 2 | vampi-seeded :5002/:5003 | ours-vuln·noreset, ours-fixed·noreset, ours-vuln·reset, ours-fixed·reset (1–20) | 80 |
| 2b | pyLoad :8090/:8091 | vuln·noreset, vuln·reset, fixed·noreset, fixed·reset (1–5) | 20 |

Tier-2b là arm SUY RA: không `--statefulAuthzTransition`. Recall ở đây là số black-box hợp lệ
trên CVE bên thứ ba. pyLoad đổi tập loại-source dưới P2b (`/json/generate_apikey` điểm đầy đủ
−1,46 < 0 không còn bị loại), nên phải đo lại, không mang số AF2 sang.

Cờ mỗi tier: reports/vampi `--maxTime 150s --ratePerMinute 120`; pyLoad `--maxTime 10m
--ratePerMinute 200 --endpointExclude "/api/kill,/api/restart"`. Mọi arm: `--useExperimentalOracles
true --extraPhaseBudgetPercentage 0.6`. Arm reset thêm `--statefulAuthzResetEndpoint`.

## Sửa harness so với bản AF2
`collect` trích cột `statuses` bỏ dòng log "proven by an attempt with" trước khi grep — dòng này
do P1/P2 thêm, trùng giá trị với dòng "Assembled", làm đếm bộ ba hai lần. Cột `assembled`
(`grep -c "Assembled .* statuses"`) và `det970` (từ `report.json`) không bị ảnh hưởng. Cùng bản
sửa đã áp cho `regression-check/NOTE-20261012-P2b.md`.

## Early-stop rule (viết trước khi chạy, CLAUDE.md §2)
Đọc từng hàng khi rơi vào progress.log.
- Arm vuln (reports vuln, vampi ours-vuln, pyLoad vuln): 3 seed đầu của một arm đều
  assembled=0 (0 bộ ba) → dừng batch, khai lệch luật, tìm nguyên nhân trong log trước khi chạy
  tiếp. 0 bộ ba nghĩa là builder không dựng trên target đó, không phải app sạch.
- Arm fixed: bất kỳ det970=1 trên target fixed là dương tính giả → dừng, điều tra.
- Hàng nào statuses=NA / faults=ERR (crash, target chết) là hàng hỏng, không phải 0 im lặng:
  dừng nếu hai hàng liên tiếp cùng arm.

## Machine-sleep rule
Chạy dưới `caffeinate -dims`, mở nắp. `pmset -g log` hiện bất kỳ `Entering Sleep` nào sau mốc
bắt đầu trong lúc một hàng đang chạy thì mọi hàng nó chạm là void — dừng, ghi, chạy lại arm đó.

## Runtime
≈ reports 6,7h + vampi 6,7h + pyLoad 3,7h ≈ 17h treo tường. runs.csv ghi nối từng run nên các
hàng đã xong sống sót qua gián đoạn. Thứ tự reports → vampi → pyLoad để hai tier chính xong trước.

## After the batch
audit970_seeded.py trên test sinh ra; toàn vẹn (không 970 nếu không có bộ ba; số log == runs.csv);
replay test 970 trên SUT gieo lại; snapshot sang ~/thesis-backups/; rồi cập nhật docs/results.md
và CLAUDE.md §4/§5, nêu jar P2b.
