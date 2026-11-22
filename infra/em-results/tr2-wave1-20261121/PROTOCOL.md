# Đo lại jar TR2 — wave 1 (reports-api, vampi-seeded, pyLoad), 2026-11-21

Đo lại đầy đủ cả bốn target với jar TR2 sau đợt CS2. Wave 1 ở đây (90 hàng); wave 2 artifact-keeper ở
`../tr2-wave2-20261121/`. Phiên `graduational-thesis-54` chuyển lời user; phiên này (Opus 4.8) đo, phiên 54 cập nhật
docs khi có số. Chạy theo đúng PROTOCOL/harness đợt CS2 (`../cs2-wave1-20261121/`, `cs2_wave1.sh`), chỉ đổi jar.

## Jar

`EvoMaster/evomaster-TR2-3beccb00.jar`. sha256 `3beccb0086b6983a6676eaf8df5c2b09cf90fc6ab72d22da7115ca0a5b4edb9f`,
sha16 WANT `3beccb0086b6983a`; khớp file `.sha256` cạnh jar. Model trong jar (`stateful-authz-model.csv`) sha256
`dcc77b59ed0f94ee…`, trùng m2-nodup (LF/CS2) — đã kiểm `unzip -p … | shasum`. Harness chặn nếu sha16 jar khác WANT.

Cây = HEAD `2c3f281f13` + `infra/evomaster-ext/wip/trim-restore-20261121-tree.patch` = cây CS2 +
`wip/trim-restore-20261121.patch` (sổ jar mục "Jar ứng viên"). Self-test
`../trim-restore-selftest-20261121-222605.out`: 63 PASS / 0 FAIL. Phiên e7 đã soát mã. Không sửa cây mã EvoMaster,
không dựng jar.

## Thay đổi so với cây CS2 (trim-restore)

- gỡ mã thừa ở lượt 2 (nâng quyền operator) và ở bước chọn source;
- lượt 2 chỉ còn một lời nâng cho mỗi operator: enum lấy giá trị cao nhất, bool `true`, số `0`;
- S2: bỏ ứng viên transition không có `victimField`.

Trên 4 target chỉ S2 đổi cách chọn ứng viên transition, chạm artifact-keeper (`POST /api/v1/admin/sso/oidc` không còn
là ứng viên) và pyLoad. Đo thẳng mọi arm; **không ghi số mong đợi** vào protocol trước lượt chạy (CLAUDE.md §2). So
từng target với bộ CS2 đã lưu (`../cs2-wave1-20261121/`) và bộ LF (`../lf-wave1-20261118/`): số 970, hàng đổi theo
seed, McNemar chính xác.

## Cờ

Giống hệt CS2/LF: bỏ cờ D1 `--statefulAuthzTwoCredentialJudgment` (jar không có cờ này; phán quyết chỉ C4).
`--useExperimentalOracles true`; `--extraPhaseBudgetPercentage 0.6`. reports/vampi `--maxTime 150s --ratePerMinute 120`;
pyLoad `--maxTime 10m --ratePerMinute 200 --endpointExclude "/api/kill,/api/restart"`. Mỗi JVM `-Xmx2g`. Reseed SUT
trước mỗi lượt. Mỗi làn `cd` một thư mục riêng. Config: `infra/em-config/{reports-auth,vampi-seeded-auth,pyload-auth}.yaml`.

## Thứ tự

Wave 1 (`tr2_wave1.sh`): 6 làn **song song** — reports lỗi :8080 / vá :8081, vampi :5002 / :5003, pyLoad :8090 / :8091.
20 seed mỗi làn reports/vampi, 5 mỗi làn pyLoad. Gộp `runs.csv` (90 hàng kỳ vọng về số lượng hàng, không về kết quả).
Wave 2 nối tiếp ở `../tr2-wave2-20261121/` (guard "mỗi lúc một việc nặng").

## Harness: diff với CS2 (chỉ JAR/WANT/BASE + nhãn log)

`tr2_wave1.sh` vs `cs2_wave1.sh`: dòng 6–8 (JAR, WANT, BASE), dòng 14 và 127 (nhãn `CS2`→`TR2`) — đúng 5 dòng, diff đã
chạy. Chỉ dòng JAR đổi dòng lệnh EvoMaster; WANT/BASE/nhãn là ghi sổ. Không đổi cờ, seed, luật dừng.

## Dựng target (phiên này, trước khi phóng)

Container đang chạy từ đợt CS2 (up 6h). Dựng lại sạch theo `docs/targets-bringup.md` §4 thay vì tái dùng, vì pyLoad giữ
trạng thái fuzzer ở lớp ghi của container (`/thesis/reset` chỉ ghi bảng users); tái dùng thì TR2 khởi đầu bẩn hơn CS2,
hỏng so sánh một-biến. Đã: `docker stop artifact-keeper-dev-backend` (nhả :8080) → `docker rm -f` 6 container cũ →
`docker run` 6 container mới từ image (ID trong bảng bringup). Kiểm: 6 spec/health 200, 6 reseed 200 (đã xác nhận).
Luật dừng 3-hàng-đầu assembled=0 bắt target hỏng câm.

## Nguồn điện

AC Power, 90%, cắm sạc (`pmset -g batt`). Harness chụp mốc `Entering Sleep` gần nhất lúc phóng, dừng nếu có mốc mới
trong lúc một hàng chạy. Để mở nắp máy.

## Luật dừng (viết trước lượt chạy, trong harness)

Như CS2/LF. Mỗi làn tự kiểm sau mỗi hàng; luật nổ thì dừng làn (`STOPPED`): bản vá có det970=1 (FP); arm lỗi 3 hàng đầu
assembled=0; 2 hàng ERR liên tiếp; có `Entering Sleep` mới trong lúc một hàng chạy. Luật nổ: dừng làn, ghi lệch luật ở
đây, tìm nguyên nhân log trước khi chạy tiếp, báo phiên 54.

## Lệch luật đã khai

1. **Chạy song song** 6 làn wave 1 (pattern user đã cho ở các đợt trước). Wave 2 nối tiếp.
2. **Bỏ cờ D1** `--statefulAuthzTwoCredentialJudgment` (jar không có cờ này). Phán quyết chỉ C4.
3. **Không qua cổng 12 hàng**: cách dựng bộ ba đổi (trim-restore chạm S2) nên cổng không đủ; đo thẳng mọi arm, so bộ
   CS2/LF đã lưu.

## Cách đếm (ghi trước, quyết lúc đếm)

Đếm bằng script đếm của CS2/LF (`lf_counts.py`, `WAVE2` trỏ `../tr2-wave2-20261121`). Số bộ ba đếm theo
`* Assembled a stateful` (chuẩn), không theo cột `assembled` CSV. Báo: 970 nổ bản lỗi, FP bản vá, TP/FN/FP/TN theo
target. TN báo cả hai cách như LF (TN_old = mọi bộ ba Assembled bản vá; TN_403 = chỉ follow-up 403). So ghép đôi với
CS2 kèm McNemar p, và với LF.

## Lưu ý về bộ nền CS2 (so ghép đôi)

CS2 wave 1 đủ 90 hàng (bộ nền đầy đủ cho reports/vampi/pyLoad). CS2 wave 2 (artifact-keeper) **chưa xong**: chỉ có
ak-vuln seed 1–3 (3 TP), không có seed 4–5, không có arm fixed — do user đã dừng đợt CS2. So ghép đôi TR2 vs CS2 ở
artifact-keeper vì thế chỉ có ở 3 seed vuln; wave-1 target có bộ nền CS2 đầy đủ. Đã khai với phiên 54.

## Đính chính (sau khi phiên 54 soát)

Nguyên nhân hàng vampi seed 15 (7→6) trong `tr2-analysis.out` ghi SAI (quy cho lượt-2 trim-restore). Đúng: dao động
run-to-run do ngân sách time-based — lượt 2 không chạy ở cả hai lượt (0 Privilege-restore); pha search lệch trước
builder (Covered targets 12 vs 24 tại cùng mốc ngân sách). Bằng chứng đầy đủ: `CORRECTION-vampi-seed15.md`. McNemar
TR2 vs CS2 p=1.0 không đổi.

## Không làm

Không commit/push; không sửa cây mã EvoMaster, không dựng jar; không sửa `docs/results.md`, `CLAUDE.md`,
`infra/evomaster-ext/jars.md` hay chương luận văn. Phiên 54 cập nhật docs sau khi có số.
