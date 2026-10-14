# Sổ jar — oracle 970

Sổ này giữ toàn bộ dòng đời các jar. `CLAUDE.md` §5 chỉ giữ jar đang trích số, jar đang phát triển nếu có, và jar giữ làm nguồn gốc.
Luật: một jar mới chỉ được trích lại một con số sau khi qua cổng hồi quy, và khi construction đổi thì phải đo lại các arm bị ảnh hưởng.

## Jar đang trích số

`EvoMaster/evomaster-P2e-6ae8277b.jar` = commit `a544c996ac`, trích số từ 2026-10-14 trên bộ gộp
`em-results/p2e-continue-20261013/merged.csv` (71 hàng P2e, 109 hàng P2d). Lệch luật đã khai: bảng trộn jar, cổng chạy
trên P2d (21/21, `p2d-night-20261012/gate/`); 2 hàng cổng chạy qua đoạn mã P2e đổi (vampi seed 3 không reset) chạy lại
trên P2e vẫn khớp (`gate-predict.out`). Replay
(`docs/results.md` §3) còn trên AF2. Dựng, self-test và bộ gộp: mục P2e bên dưới.

## Jar trích số tới 2026-10-14, giữ làm nguồn gốc

`EvoMaster/evomaster-AF2-6b5606d4.jar` = commit `8d6cf8431f` (nhánh `stateful-authz-oracle`) = jar `ER` + nhận
transition lật cờ admin kiểu boolean (`is_admin`, `is_superuser`, `is_staff`...). `transitionScore` cộng điểm cho
trường cờ admin, `harvestReducedRoleCandidates` lấy `false`, và `setAdminFlagActive` ép wrapper nullable của
`is_admin` về present+false. Jar `AF-422f912b` chỉ có phần nhận-diện; setter chưa ép wrapper nên `is_admin` serialize
`null` ngẫu nhiên, recall 1/4. AF2 sửa setter, recall 5/5. Chỉ sửa `RestSecurityBuilder.kt`; EMConfig y nguyên jar
`ER` (ba option statefulAuthz). Tree `bf615f36`, baseline rollback `wip/admin-flag-baseline-20261001.patch`. Self-test
`admin-flag-transition.sh` 9/9, có kiểm falsifiability bằng jar `ER` cùng cấu hình không nổ. Cổng 21/21 ngày
2026-10-02 (1h48, máy không ngủ; `em-results/regression-check/archive-20261002-AF2-6b5606d4/`, backup
`~/thesis-backups/regression-gate-20261002-AF2-6b5606d4/`). artifact-keeper thành target phát triển: vuln 5/5 auto-970
(bộ ba `PATCH /api/v1/users/{id}` 200/200/200), fixed 0/3 FP (`em-results/artifactkeeper-machine-20261001/`).

Đo lại §4 đầy đủ seeds 1–20 (Tier-2b 1–5) ngày 2026-10-03/04, `em-results/af2-full-remeasure-20261003/`: trùng khít
jar R từng seed (detection, four-cells, ablation gains {3,7,8,9,12,16,19} / lost {15}), 0 FP/90, soát cấu trúc 59/59
reports+vampi (pyLoad auth cookie, xác nhận bằng `verify_ground_truth.sh`), replay 55/59. AF2 thay jar R làm jar
trích số từ 2026-10-04 tới 2026-10-14.

## Chuỗi P1–P2e, mới nhất trước

`EvoMaster/evomaster-P2e-6ae8277b.jar` (sha256 `6ae8277b…`, `.sha256` cạnh jar) = commit `a544c996ac` (2026-10-14,
chưa push; `git diff 8d6cf8431f a544c996ac -- core/src/main/kotlin` trùng từng byte bản vá cả cây) = jar P2d + 4 dòng trong
`RestSecurityBuilder.kt:1265–1269` (`wip/p2e-increment-over-p2d-20261013.diff`; cả cây
`wip/p2e-restore-high-20261013.patch`, diễn tập rollback 2026-10-13 trùng từng byte; model CSV `9a7a7749…`, trùng bản
trong jar). Giá trị nâng quyền của trường enum chỉ gồm các giá trị mô hình chấm `high > low`. AF2 chỉ nâng bằng giá trị
trong danh sách viết tay (`admin` trên vampi). Self-test `p2e-restore-high-20261013.sh` 7/7, bốn kiểm tra trượt trên
log P2d (`em-results/p2e-selftest-20261013-134225/`). `em-results/p2e-continue-20261013/`: 71 hàng P2e gộp với 109
hàng P2d mà sửa C không đổi (lập luận và 11 hàng kiểm lại trong `PROTOCOL.md`, `RESULTS.md`); 180 hàng, số nổ và FP
trùng AF2 ở cả 12 arm. Trích số từ 2026-10-14 (mục đầu).

`EvoMaster/evomaster-P2d-2e0dbd4d.jar` (sha256 `2e0dbd4d…`, `.sha256` cạnh jar) = jar P2c + hai thay đổi trong
`RestSecurityBuilder.kt` (`wip/p2d-increment-over-p2c-20261012.diff`; cả cây `wip/p2d-lowkeep-elevate-20261012.patch`,
diễn tập rollback 2026-10-12 trùng từng byte; model CSV không đổi, sha256 `9a7a7749…`). A `:1248–1249`: vai hiện tại
mà bảng `low`/`high` chấm là thấp không còn loại giá trị hạ. B `:1261`: snapshot của operator chấm là thấp không còn làm
giá trị khôi phục, thay bằng enum xếp theo `high − low`. AF2 làm hai việc này bằng danh sách viết tay (`isLowPrivRole`,
`harvestElevatedRoleCandidates`); P2 bỏ danh sách và mất cả hai. Self-test `p2d-reduce-elevate-20261012.sh` 6/6, hai kiểm
tra trượt trên log P2c (`em-results/p2d-selftest-20261012-223150/`). Chuỗi `em-results/p2d-night-20261012/`: probe
reports seeds 10/13/16 9/9, FP 0/6, cổng 21/21 MATCH (2026-10-13 01:44); đo lại dừng sau 114 hàng
(`STOPPED.md`): reports 80/80 trùng AF2, vampi vuln không reset 6/20 (AF2 7/20), restore tiêu một lượt vào giá trị
`EVOMASTER` mà EvoMaster tự chèn vào enum. 16 hàng AF2 nổ còn lại trùng AF2
(`em-results/p2d-af2fired-probe-20261013/`). Thay bằng P2e. Không dùng.

`EvoMaster/evomaster-P2c-b2ade764.jar` (sha256 `b2ade764…`) = jar P2b + một dòng `RestSecurityBuilder.kt:858`: gọi
khôi phục với restorer = nạn nhân, target = operator, như AF2 (`wip/p2-nb-restoreswap-20261012.patch`). P2b tráo hai tham
số: reports seeds 4/8 AF2 6/6, P2b 0/6 (`em-results/p2b-confirm-20261012/`). Self-test `restore-swap-20261012.sh` 4/4,
FP 0/6 (`em-results/fp-check-p2c-20261012/`), cổng rút gọn (`regression-check/NOTE-20261012-P2c.md`). Đo lại dừng sau
arm reports vuln không reset, 16/20, trượt seeds 10/13/16/17; AF2 19/20 trượt 17
(`em-results/p2c-full-remeasure-20261012/STOPPED.md`). Interleave seeds 10/13/16: AF2 9/9, P2c 0/9. Thay bằng P2d.
Không dùng.

`EvoMaster/evomaster-P2b-93db089f.jar` (sha256 `93db089f…`, `.sha256` cạnh jar) = commit `8d6cf8431f` + bản vá chưa
commit `wip/p2-nb-20261012.patch` (gồm P1, chỉ `RestSecurityBuilder.kt`) + tài nguyên mới
`core/src/main/resources/stateful-authz-model.csv`. P2: thay max-lexicon + cờ admin + mọi danh sách viết tay bằng Naive
Bayes mức op (nhóm A) và mức trường (B1 vai trò, B3 nạn nhân), giá trị theo kiểu (B2), đọc phản hồi theo khoá danh tính
(B4), đối chứng ẩn danh trong cả hai phép xác nhận D1 và C4, cổng = posterior > 0,5 (`transitionScore > 0`, dùng y hệt
một vị từ ở builder và oracle), phá hoà theo thứ tự spec. Mô hình sinh bằng
`infra/analysis/lexicon-rules/p2-model-20261012/derive_model.py`; `check_model.py` 8/8 (sinh lại trùng byte, trọng số
bằng hệt script đo `nb_train`/`ftrain`/`vtrain`, `low`/`high` khớp `RK.csv`, tiên nghiệm −3,94/−1,94, điểm pyLoad
5,61/2,84/1,69). Diễn tập rollback 2026-10-12: patch áp lại trùng từng byte. Self-test `p2-stateful-authz.sh`
2026-10-12: 25/25 trên 8 mode stub (`em-results/p2-selftest-20261012-095033/`) — điểm và trường chọn của Kotlin bằng
hệt Python trên mọi mode; enum/num/access/path-id nổ 970; đối chứng ẩn danh 403 → INCONCLUSIVE (cả C4 và D1), 401 → vẫn
nổ; op điểm thấp bị loại khỏi danh sách transition; mode `put-id-source` (source ghi `PUT /docs/{id}` điểm đầy đủ < 0
không bị loại khỏi vai source, 970 nổ) bắt đúng lỗi loại-source; jar P1 không in dấu hiệu NB. Qua cổng hồi quy 21/21
MATCH 2026-10-12, 1h47 (`regression-check/archive-20261012-P2b-93db089f-PASS/`). Tráo restorer/target ở `:858`, sửa ở
P2c. Không dùng.

`EvoMaster/evomaster-P2-205d923d.jar` (sha256 `205d923d…`): bản P2 đầu, cổng Σw > 0. Cổng hồi quy 2026-10-12 bắt lỗi
loại-source: 2/2 hàng Tier-1 vuln ra 970=0 (oracle loại oan source thật `PUT /reports/{id}` vì Σw +0,43 > 0). Sửa
bằng Design 1 — gộp vị từ về posterior > 0,5 (điểm đầy đủ > 0), tách sạch source −3,51 khỏi transition +8,50
(`wip/p2-design-20261012.md §7`, `regression-check/NOTE-20261012-P2b.md`). Harness `regression_check.sh` cũng sửa:
cột `statuses` đếm bộ ba hai lần vì dòng log "proven by an attempt" của P1/P2, bỏ dòng này trước khi trích. Giữ làm
mốc lỗi, không dùng.

`EvoMaster/evomaster-P1-80024675.jar` (sha256 `80024675…`, `.sha256` cạnh jar) = commit `8d6cf8431f` + bản vá chưa
commit `wip/candidate-iteration-20261011.patch` (P1, chỉ `RestSecurityBuilder.kt`): duyệt mọi op khả dụng thay vì dừng
ở op đầu; bỏ giới hạn 8 op đầu (α); trần tổng 20; trần 5 cho op chưa chứng minh, trừ op cuối; dấu nạn nhân của op chưa
chứng minh bị xoá khi sang op kế; cặp (op, nạn nhân) bị từ chối thì bỏ qua ở các source sau; ngân sách khôi phục 3 lần
mỗi op; bước 2 trả 404 trên op đã chứng minh không chuyển op; log REVOKED, khôi phục không chạy được, probe C4 không kết
luận. Thiết kế chốt 2026-10-11 qua tranh luận với hai agent. Diễn tập rollback 2026-10-11: patch áp lại trùng từng byte.
Self-test `candidate-iteration.sh` 2026-10-11: 9 kịch bản trên target giả, mọi kiểm tra PASS, 13 kiểm tra về mã mới
trượt khi tráo log jar AF2 vào (`em-results/candidate-iteration-selftest-20261011/`). Ba nhánh chưa chạy qua: không có
mã trạng thái (`-/-/-`), probe C4 không kết luận, khôi phục bị bỏ qua. Chưa qua cổng hồi quy; user quyết không đo lại
đầy đủ trước P2. Lượt reports-api seeds 1–10, bốn arm, 40 hàng (`em-results/p1-reports-20261011/`, 2026-10-11): trùng
AF2 từng hàng ở mọi cột chung và ở bảng soát cấu trúc; luật mới không chạm vào lượt nào vì reports-api có một op khả dụng.
Không trích số từ jar này.

## Chuỗi trước đó, mới nhất trước

`evomaster-R-5bce137f.jar` = commit `007e5e09f9`. Jar trích số cũ tới 2026-10-04; AF2 tái lập toàn bộ §4 từng seed.
Giữ làm nguồn gốc.

`evomaster-ER-06b48c30.jar` = jar `LP` + tham số path `email` của user thành nhóm thứ hai
(`wip/email-param-20260930.md`, jar `EP-9007f79a`) + giá trị hạ `[]` cho mảng vai trò (`wip/empty-roles-20260930.md`).
Tree `fe0dca8a`, rollback diễn tập 2026-09-30 13:05. Self-test `empty-roles.sh` 10/10, lần đầu có 970 trên bamf.
Chuỗi `em-results/emptyroles-chain-20260930/`.

`evomaster-LP-3cc44770.jar` = jar `NR-3c087e58` + không bao giờ lấy giá trị vai trò quyền thấp làm vai trò hiện tại
(tree `46f937b4`). Self-test 33/33. Bamf held-out trên jar này: FN.

`evomaster-NR-3c087e58.jar` = jar `NR-aeeb485c` với vai trò hiện tại chỉ đọc từ body GET (tree `9643fa8f`).
Self-test 9/9 ×3, cổng 21/21; seeds 1–10 41/43 hàng bằng jar `VI`; Tier-1 seed 10 mất 970 và mất bộ ba: một GET trong
archive cho `superadmin` là `VIEWER` (`em-results/t1seed10-debug-20260930/RESULTS.md`).
Chuỗi dừng 09:05 tại pyLoad seed 4 (`numrole-chain-20260930/`).

`evomaster-NR-aeeb485c.jar` = jar `RV` + giá trị vai trò dạng số cho mọi `NumberGene`, vai trò hiện tại đọc từ `id`/`name`
của object vai trò, giá trị vai trò kế tiếp khi transition từ chối giá trị (4xx/5xx khác 401/403/404), và object nạn nhân
tên theo `login`/`username` xếp trước khớp `name` (tree `94b6a068`, `wip/num-role-20260929.md`; jar `NR-04c73346` trượt
self-test, không đo). Viết trên truthy. Self-test 9/9, rollback diễn tập 09-29. Cổng 20/21: Tier-2 ours-fixed-reset seed 3
mất một bộ ba vì vai trò hiện tại đọc từ echo của một write (`em-results/gate-mismatch-20260930/`).

`evomaster-RV-44254256.jar` = jar `VI` + bỏ giá trị vai trò bằng vai trò hiện tại của nạn nhân (đọc từ body archive), và
trường body `login`/`username`/`user_name` mang tên nạn nhân (tree `ef3690d3`, `wip/role-value-20260929.md`).
Viết trên callcenter. Self-test 9/9, rollback diễn tập 09-29. Cổng dừng ở hàng 3 khi jar `NR` thay thế.

`evomaster-VI-d2325da7.jar` = `core/target/evomaster.jar` dựng 2026-09-28: jar `TT` + bỏ qua route thiếu, id nạn nhân lấy
từ body archive, và hàng đợi transition khi 404 (tree `cc178c8d`, `wip/victim-id-route-missing-20260928.md`; bốn jar VI
trung gian không đo). Self-test 9/9, cổng 21/21, rollback diễn tập 09-29. Seeds 1–10
(`em-results/victimid-chain-20260928/`): 37 hàng chạy trước 21:46 khớp jar `TT` về 970, số VOID và tập fault; 17 hàng bị
máy ngủ làm hỏng, chạy lại 09-29, cũng khớp (`em-results/victimid-rerun-20260929/RESULTS.md`).

`evomaster-TT-129a7a56.jar` = `core/target/evomaster.jar` dựng 2026-09-27 01:33: jar `GG` + transition trim
(tree `4d2beb47`, `wip/transition-trim-20260926.md`, lần thứ tư; jar `TT-0b6f3c31`, `TT-3072fec2`, `TT-88f8e7a1` trượt
self-test, không đo). Self-test 8/8, cổng 21/21, seeds 1–10: 0 trên 50 hàng ghép đôi đổi so với jar `PF`
(`em-results/transitiontrim-chain-20260927c/RESULTS.md`). Seeds 1–20 mọi arm, không reset: Tier-1 19/20, Tier-2 7/20,
pyLoad 20/20, FP 0/60; Tier-1/2 giống jar `R` từng seed (80 cặp).
Đóng băng 09:31–14:50 ngày 2026-09-28 cho lượt Grafana held-out (`infra/analysis/cve-survey/heldout-20260928.md`).
User mở băng 14:50: bản sửa cho hai nguyên nhân Grafana đi sang jar mới, đo trên một app held-out thứ hai chưa chạy bao
giờ; Grafana thành target phát triển của jar đó.

`evomaster-GG-a6839ada.jar` = jar `PF` + gene-set guard (tree `66bffda6`, `wip/gene-set-guard-20260925.md`).
Self-test 6/6 và post-fallback 6/6, cổng 21/21, Airflow exit 0 (`em-results/genesetguard-chain-20260925/RESULTS.md`).

`evomaster-PF-0607485b.jar` = jar `RF` + POST fallback (tree `00f98d29`, `wip/post-fallback-20260924.md`).
Self-test 5/6: trên Airflow EvoMaster exit 1 trong `setAllRoleFieldsTo`. Cổng 21/21; seeds 1–10 trong
`em-results/postfallback-chain-20260925/` (pyLoad seeds 3–10 chạy lại sau một lần target treo).

`evomaster-RF-7f9d977e.jar` = jar dựng 2026-09-23 23:28: jar `L` + field-gate, local-harvest, role-field và chẩn đoán
debug (tree diff `d5a9b00d`, `wip/d1-lexicon-field-harvest-rolefield-20260923.patch`). Self-test 12/12 mới, field-gate 7/7,
local-harvest 6/7 với `content-type-is-a-value` trượt theo thiết kế; cổng 21/21; seeds 1–10 trên ba target và 20 lượt arm
fixed: 0 trên 50 hàng ghép đôi đổi về 970 so với jar `L` và so với `evomaster-FH-2ec4b921.jar` (field-gate + local-harvest,
cũng 0/50: `em-results/field-harvest-chain-20260923/`). `em-results/rolefield-chain-20260924/RESULTS.md`.

`evomaster-L-5b3d5442.jar` = `core/target/evomaster.jar` dựng 2026-09-21 22:20: commit `634850be3a` + bản sửa mã từ chối
chưa commit + bản vá xếp hạng chưa commit + `core/src/main/resources/stateful-authz-lexicon.csv`. Self-test 14/14,
cổng 21/21, seeds 1–10 trên ba target và 20 lượt arm fixed, 0 phát hiện mất so với các hàng D1
(`em-results/lexicon-chain-20260921/`, `docs/results.md` §5b).

`evomaster-prelexicon-2c343573.jar` (sha256 `2c343573…`) = commit `634850be3a` + bản sửa mã từ chối chưa commit
(`wip/d1-denial-codes-20260917.patch`): D1 sau một cờ mặc định tắt, và trong nhánh hai credential thì 403 một mình là
từ chối với mọi verb. Cổng 21/21 (2026-09-18, 23:27–01:14, `em-results/regression-check/observed.csv`); self-test 14/14
(`em-results/d1-selftest-20260917-231617/`). Seeds 1–10 trên ba target, cả hai arm (`em-results/d1-seeds1-10/`,
`em-results/d1-pyload-seeds1-10/`): cờ không đổi phát hiện nào (Tier-1 10/10, Tier-2 3/10, pyLoad 10/10 ở cả hai arm,
ghép đôi từng seed) và mỗi phát hiện trong 23 phát hiện mang một dòng probe, tất cả `=403`.

`evomaster-D1-634850be.jar` (sha256 `0c4205ce…`, commit `634850be3a`), cổng 21/21 (2026-09-17). Vẫn tính mọi PUT khác 2xx
là từ chối.

`evomaster-0e-bf26b653.jar` (sha256 `7974e803…`, nguồn `bf26b65322`), cổng 21/21 (2026-09-13).
