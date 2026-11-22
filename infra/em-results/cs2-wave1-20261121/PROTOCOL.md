# Đo lại jar CS2 (C4 chỉ kết luận trên mã của source), 2026-11-21

Chạy lại cả bốn target với jar CS2 để đo lại đầy đủ 98 hàng sau khi đổi probe C4. Thư mục: wave 1 ở đây,
wave 2 ở `../cs2-wave2-20261121/`. Phiên `graduational-thesis-4a` chuyển lời user (Minh); phiên này (Opus 4.8)
đo, phiên 4a cập nhật docs khi có số. Chạy theo đúng PROTOCOL/harness đợt LF (`../lf-wave1-20261118/PROTOCOL.md`,
`lf_wave1.sh`), chỉ đổi jar và nhãn.

## Jar

`EvoMaster/evomaster-CS2-f3412dc8.jar`. sha256 `f3412dc87f1083a369763fd14c4b4029d424e60b3d68140777a61526c77cc9c0`,
sha16 WANT `f3412dc87f1083a3`; khớp file `.sha256` cạnh jar. Model trong jar = m2-nodup (`dcc77b59ed0f…`), trùng LF.
Mỗi harness chặn nếu sha16 khác WANT.

Thay đổi so với cây LF: chỉ `RestSecurityBuilder.kt` (bản vá P1 + P3, chưa commit). Chi tiết
`infra/evomaster-ext/wip/c4-source-status-20261121.md`, sổ jar mục "Jar ứng viên, chưa trích số".
Self-test `selftest/c4-source-status-20261121.sh`: 57 PASS / 0 FAIL, exit 0
(`../c4-source-status-selftest-20261121-170956.out`). Không sửa cây mã EvoMaster, không dựng jar.

## Mục đích

P1 đổi cách probe C4 kết luận: C4 chỉ đọc mã của **source** của lát chép lại (không đọc `lastVictimStatus`); mỗi call
trước source phải cùng nhóm mã (`code/100`) như chính nó trong bộ ba, nếu không → INCONCLUSIVE, bỏ bộ ba với nhãn
UNCONFIRMED. Đối chứng ẩn danh chỉ bỏ credential ở source. P3 dọn mã, không đổi hành vi. Vì cách phán quyết C4 đổi,
số LF không còn trích được cho CS2; đo thẳng mọi arm trên cả 4 target, so từng target với bộ LF đã lưu
(`../lf-wave1-20261118/`, `../lf-wave2-20261118/`): số 970, hàng nào đổi theo từng seed, McNemar chính xác.

## Cờ

Giống hệt đợt LF: bỏ cờ D1 `--statefulAuthzTwoCredentialJudgment` (jar không có cờ này; phán quyết chỉ C4).
`--useExperimentalOracles true`; `--extraPhaseBudgetPercentage` 0,6 (reports/vampi/pyLoad) hoặc 0,25 (artifact-keeper).
reports/vampi `--maxTime 150s`; pyLoad `10m`; artifact-keeper `1200s`. Mỗi JVM `-Xmx2g`. Reseed SUT trước mỗi lượt.
Mỗi làn `cd` một thư mục riêng.

## Thứ tự

- Wave 1 (`cs2_wave1.sh`): 6 làn **song song** — reports lỗi :8080 / vá :8081, vampi :5002 / :5003, pyLoad :8090 /
  :8091. 20 seed mỗi làn reports/vampi, 5 mỗi làn pyLoad. Gộp `runs.csv` (90 hàng kỳ vọng).
- Wave 2 (`../cs2-wave2-20261121/`): **nối tiếp** (guard "mỗi lúc một việc nặng"). Dừng container `reports-api` (:8080)
  nhường artifact-keeper. `ak_vuln.sh` 5 seed (commit lỗi `e56d3aa7`), rồi checkout commit vá `e64cc5c608` + `.sqlx`
  → rebuild → kiểm tay bản vá còn sống → `ak_fixed.sh` 3 seed. Sau đo: trả repo về `e56d3aa7` sạch.

## Dựng target (phiên này, trước khi phóng)

Máy đã khởi động lại sau đợt LF (container target Exited 2–3 ngày). Dựng lại theo `docs/targets-bringup.md` §4:
`docker rm -f` 6 container cũ → `docker run` lại từ image. Image khớp ID bảng bringup (reports `7c98b63bbfc4`,
vampi `7ba9a98ac50e`, pyload-vuln `25451c1a1bd6`, pyload-fixed `5e2451ab380d`). Kiểm: 6 spec/health 200, 6 reseed 200
(đã xác nhận). Image trùng ID bộ LF/ND đã kiểm ground-truth; đợt này kiểm health+reseed thay vì diễn lại bug-demo,
luật dừng 3-hàng-đầu assembled=0 bắt target hỏng câm.

## Harness: diff với LF (chỉ JAR/WANT/BASE + nhãn log)

`cs2_wave1.sh` vs `lf_wave1.sh`: dòng 6–8 (JAR, WANT, BASE), dòng 14 và 127 (nhãn `LF`→`CS2`). Không đổi dòng lệnh
EvoMaster, cờ, seed, luật dừng. Diff đầy đủ đã chạy: đúng 5 dòng, không gì khác.

## Nguồn điện

AC Power, 90%, cắm sạc (xác nhận `pmset -g batt`). `Entering Sleep` gần nhất 2026-11-21 07:03:38 (trước đợt chạy).
Harness chụp mốc này lúc phóng và dừng nếu có `Entering Sleep` mới lúc một hàng đang chạy. Để mở nắp máy.

## Luật dừng (viết trước lượt chạy, nằm trong harness)

Như đợt LF. Mỗi làn tự kiểm sau mỗi hàng; luật nổ thì dừng làn (`STOPPED`): bản vá có det970=1 (FP); arm lỗi 3 hàng
đầu assembled=0; 2 hàng ERR liên tiếp; có `Entering Sleep` mới trong lúc một hàng chạy; artifact-keeper seed đầu
thiếu đăng nhập một tài khoản hoặc evaluated < 389. Luật nổ: dừng làn/batch, ghi thành lệch luật ở đây, tìm nguyên
nhân trong log trước khi chạy tiếp, báo phiên 4a.

## Lệch luật đã khai

1. **Chạy song song** 6 làn wave 1 (pattern user đã cho ở đợt SLM2/ND/LF). Wave 2 nối tiếp.
2. **Bỏ cờ D1** `--statefulAuthzTwoCredentialJudgment` (jar không có cờ này). Phán quyết chỉ C4.
3. **Không qua cổng 12/21 hàng**: C4 đổi cách phán quyết nên cổng không đủ; đo thẳng mọi arm, so bộ LF đã lưu.

## Cách đếm (ghi trước, quyết lúc đếm)

Đếm bằng `cs2_counts.py` (bản sao `lf_counts.py`, `WAVE2` trỏ `../cs2-wave2-20261121`). Số bộ ba đếm theo
`* Assembled a stateful` (chuẩn), không theo cột `assembled` CSV. Báo: 970 nổ bản lỗi, FP bản vá, TP/FN/FP/TN theo
target. TN báo cả hai cách như LF (TN_old = mọi bộ ba Assembled bản vá; TN_403 = chỉ follow-up 403), kèm số bộ ba
bản vá có follow-up khác 2xx/403/401. Không trộn hai cách trong một cột.

## Báo phiên 4a (SendMessage, khi xong hoặc luật dừng nổ)

- Bảng theo target: 970 nổ bản lỗi, FP bản vá, TP/FN/FP/TN (đếm như `lf_counts.py`).
- So với LF theo từng seed: hàng nào thêm, hàng nào mất, McNemar chính xác.
- Đếm dòng log C4 theo target: "Discarded an UNCONFIRMED", "re-login probe INCONCLUSIVE" (tách theo lý do),
  "anonymous control", "already reduced in this phase".
- Mọi lệch luật và sự cố lúc chạy.

## Không làm

Không commit/push; không sửa cây mã EvoMaster, không dựng jar; không sửa `docs/results.md`, `CLAUDE.md`,
`infra/evomaster-ext/jars.md` hay chương luận văn. Phiên 4a cập nhật docs sau khi có số.
