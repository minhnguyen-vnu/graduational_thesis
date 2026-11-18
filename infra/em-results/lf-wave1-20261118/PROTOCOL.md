# Đo lại jar LF (logic-fix của builder+oracle, model m2-nodup), 2026-11-18

Chạy lại cả bốn target với jar LF để đo lại đầy đủ sau khi sửa logic thiếu/sai/thừa của mã 970.
Thư mục: wave 1 ở đây, wave 2 ở `../lf-wave2-20261118/`. Phiên `graduational-thesis-e4` chuyển lời user
(user đang ngủ); phiên này (Opus 4.8) đo, phiên e4 cập nhật docs khi có số. Chạy theo đúng PROTOCOL đợt ND
(`../nd-wave1-20261113/PROTOCOL.md`), vì ND là khuôn gần nhất.

## Jar

`EvoMaster/evomaster-LF-d559dc73.jar` = HEAD `2c3f281f13` + bản vá chưa commit
`infra/evomaster-ext/wip/logic-fix-20261118-tree.patch` (4 file: RestSecurityBuilder.kt, RestSecurityOracle.kt,
ExperimentalFaultCategory.kt, stateful-authz-model.csv). Model trong jar = m2-nodup (sha16 `dcc77b59ed0f94ee`,
giống ND). sha256 jar `d559dc730701745eebe5233e24733299b6fd8d50d62715caacfa3b8d5603ffc1`, sha16 WANT `d559dc730701745e`.
Mỗi harness chặn nếu sha16 khác WANT.

Kiểm trước đợt (phiên này): sha256 jar khớp file `.sha256` cạnh jar; model trong jar `dcc77b59ed0f94ee` khớp
`infra/analysis/lexicon-rules/m2-nodup-20261112/stateful-authz-model.csv`; cây mã EvoMaster = HEAD `2c3f281f13` +
4 file sửa (uncommitted) trùng `logic-fix-20261118-tree.patch`. Self-test `selftest/logic-fix-20261118.sh`:
48 PASS / 0 FAIL exit 0 (`../logic-fix-selftest-20261118-014908.out`). Review độc lập agent Opus 5.5 (xhigh):
không có lỗi mã mức chặn (không crash/vòng lặp/đường FP mới cho 970) — `logic-fix-20261118.md` mục "Review của agent".

Không sửa cây mã EvoMaster, không dựng jar. Cây mã hiện mang đúng mã của jar LF.

## Mục đích

Logic-fix đổi cách dựng bộ ba (thêm source POST, đổi danh tính nạn nhân sang loginName, khoá cặp 404, v.v.), nên số
ND không còn trích được cho jar LF. Jar mới chỉ trích được số sau một lượt đo đầy đủ (CLAUDE.md §5), và cổng 12 hàng
không đủ khi cách dựng bộ ba đổi. Đợt này đo thẳng mọi arm trên cả 4 target, so từng target với bộ ND đã lưu
(`../nd-wave1-20261113/`, `../nd-wave2-20261113/`): số 970, và hàng nào đổi transition/bộ ba.

## Cờ

Giống hệt đợt ND (= SLM2): bỏ cờ D1 `--statefulAuthzTwoCredentialJudgment` (jar không có cờ này; phán quyết chỉ C4).
`--useExperimentalOracles true`; `--extraPhaseBudgetPercentage` 0,6 (reports/vampi/pyLoad) hoặc 0,25
(artifact-keeper). reports/vampi `--maxTime 150s`; pyLoad `10m`; artifact-keeper `1200s`. Mỗi JVM `-Xmx2g`.
Reseed SUT trước mỗi lượt. Mỗi làn `cd` một thư mục riêng.

## Thứ tự

- Wave 1 (`lf_wave1.sh`): 6 làn **song song** — reports lỗi :8080 / vá :8081, vampi :5002 / :5003, pyLoad :8090 /
  :8091. 20 seed mỗi làn reports/vampi, 5 mỗi làn pyLoad. Gộp `runs.csv` (90 hàng kỳ vọng).
- Wave 2 (`../lf-wave2-20261118/`): **nối tiếp** (guard "mỗi lúc một việc nặng"). Dừng container `reports-api` (:8080)
  nhường artifact-keeper. `ak_vuln.sh` 5 seed (commit lỗi `e56d3aa7`), rồi checkout commit vá `e64cc5c608` + `.sqlx`
  → rebuild → kiểm tay bản vá còn sống → `ak_fixed.sh` 3 seed. Sau đo: trả repo về `e56d3aa7` sạch.

## Dựng target (phiên này, trước khi phóng)

Máy đã khởi động lại sau đợt ND (Docker daemon tắt, container target Exited 3 ngày). Dựng lại theo
`docs/targets-bringup.md` §4: `docker rm -f` 6 container cũ → `docker run` lại từ image. Image khớp ID bảng bringup
(reports `7c98b63bbfc4`, vampi `7ba9a98ac50e`, pyload-vuln `25451c1a1bd6`, pyload-fixed `5e2451ab380d`,
ak backend `024212a16242`, postgres:16-alpine `721873c34ceb`). Kiểm: 6 spec/health 200, 6 reseed 200. Vì image
trùng ID bộ ND đã kiểm ground-truth, đợt này kiểm health+reseed thay vì diễn lại bug-demo; luật dừng 3-hàng-đầu
assembled=0 bắt target hỏng câm.

## Harness: diff với ND (chỉ JAR/WANT/BASE + nhãn log)

`lf_wave1.sh` vs `nd_wave1.sh`: dòng 6–8 (JAR, WANT, BASE), dòng 14 và 127 (nhãn `ND`→`LF`). Không đổi dòng lệnh
EvoMaster, cờ, seed, luật dừng. (diff đầy đủ đã chạy, đúng 5 dòng.)

## Luật dừng (viết trước lượt chạy, nằm trong harness)

Như đợt ND/SLM2. Mỗi làn tự kiểm sau mỗi hàng; luật nổ thì dừng làn (`STOPPED`/`DUNG`): bản vá có det970=1 (FP);
arm lỗi 3 hàng đầu assembled=0; 2 hàng ERR liên tiếp; có `Entering Sleep` mới trong lúc một hàng chạy;
artifact-keeper seed đầu thiếu đăng nhập một tài khoản hoặc evaluated < 389.

## Lệch luật đã khai

1. **Chạy song song** 6 làn wave 1, theo pattern user đã cho ở đợt SLM2/ND. Wave 2 nối tiếp.
2. **Bỏ cờ D1** `--statefulAuthzTwoCredentialJudgment` (jar không có cờ này). Phán quyết chỉ C4.
3. **Không qua cổng 12/21 hàng**: cách dựng bộ ba đổi nên cổng không đủ; đo thẳng mọi arm, so bộ ND đã lưu.

## Cách đếm (ghi trước, quyết lúc đếm)

`nd-wave1-20261113/nd_counts.py:107` tính TN cho MỌI bộ ba `Assembled` trên bản vá, kể cả follow-up 404/409/400.
Logic-fix thêm source POST (reports-api và nơi khác), nên follow-up POST có thể là 201/409 — không phải 403.
Lúc đếm, báo CẢ HAI số để user chọn số đưa vào luận văn (user quyết):
- TN_old = mọi bộ ba Assembled trên bản vá (đúng luật nd_counts.py đã dùng cho ND; để so thẳng với ND);
- TN_403 = chỉ bộ ba có follow-up 403 trên bản vá.
Kèm: số bộ ba trên bản vá có follow-up KHÁC 2xx/403/401 (vd 409/404/400), tách riêng.
Bảng so ND/LF ghi rõ mỗi ô dùng cách đếm nào, KHÔNG trộn hai cách trong một cột.
Không coi chênh số bộ ba / số lần nâng quyền của reports-api (do thêm source POST /reports) là lỗi harness — đó là
hệ quả dự kiến của logic-fix.

## Kết quả

Chạy 2026-11-18, jar LF-d559dc73. Wave 1 sạch: 0 FP, 0 ERR, 0 STOPPED, không `Entering Sleep`.
`runs.csv` 90 hàng; đếm bằng `lf_counts.py` (bản sao `nd_counts.py`, `WAVE2` trỏ `../lf-wave2-20261118`;
out `lf_counts.out` ở scratchpad phiên). Số bộ ba đếm theo `* Assembled a stateful` (chuẩn), không theo cột
`assembled` của CSV (CSV grep `transition PATCH.* statuses` nên cộng thêm dòng `proven by an attempt`).

970 nổ (bản lỗi) / FP (bản vá), kèm số của jar ND 2026-11-13 để so:

| Target | LF vuln | ND vuln | LF fixed (FP) | ND fixed | LF bộ ba (vuln/fixed) | Fisher p (LF) |
|---|---|---|---|---|---|---|
| reports-api | 20/20 | 19/20 | 0/20 | 0/20 | 38/38 | <1e-6 |
| vampi-seeded | 7/20 | 6/20 | 0/20 | 0/20 | 7/6 | 0,004158 |
| pyLoad | 5/5 | 5/5 | 0/5 | 0/5 | 5/5 | 0,003968 |

Bốn ô (LF, cả 4 target gồm artifact-keeper ở wave 2): TP 37, FN 13 (đều là lượt không dựng được bộ ba, toàn bộ ở
vampi), FP 0, TN 31. ND: TP 34, FN 16, FP 0, TN 30.

Mỗi target vuln LF tăng 1 so ND (reports 19→20, vampi 6→7, artifact-keeper 4→5); bản vá giữ 0 FP. Đúng dự đoán
`logic-fix-20261118.md`: reports thêm source POST (bộ ba 201/200/403 trên bản vá, seed trước bị trượt nay thành TP),
vampi bỏ gửi EVOMASTER + source 401 dừng sớm, artifact-keeper thêm source POST (bộ ba thứ 2).

### Đếm TN (cả hai cách, như đã hẹn với e4)

Statuses bộ ba trên bản vá (từ `lf_counts.out`): reports `{200/200/403, 201/200/403}`, vampi `{200/200/403}`,
pyLoad `{200/200/403}`. Mọi follow-up trên bản vá đều 403. Nên:
- TN_old (mọi lượt bản vá có bộ ba, luật `lf_counts.py:107`) = reports 20 + vampi 6 + pyLoad 5 + ak 0 = 31.
- TN_403 (chỉ follow-up 403) = 31 (trùng, vì không có follow-up nào khác 403).
- Bộ ba bản vá có follow-up KHÁC 2xx/403/401: 0.

Hai cách cho cùng 31; đợt này không có chênh. (Dự đoán follow-up POST 201/409 trên bản vá không xảy ra: re-attempt
POST sau khi hạ quyền trả 403, không phải 409.)

### audit970 (`audit970.out`)

Chạy `audit970_seeded.py` trên `tests/*`. reports vuln 38 PASS / fixed 37 silent; vampi vuln 7 PASS / fixed 6 silent;
artifact-keeper vuln 10 PASS / fixed 0 (wave 2). 0 PASS trên mọi arm bản vá (0 FP). pyLoad (t2b) 5 FAIL với
`cred: "None"`: ca cookie phiên không parse được (CLAUDE.md §4), không phải báo sai; det970 pyLoad 5/5 vuln, 0/5 fixed
lấy từ `report.json`/CSV và xác nhận bằng C4 trong lượt. ND cũng bỏ pyLoad khỏi audit vì lý do này.

### Integrity

Kiểm toàn bộ log wave 1+2 bằng mẫu chuẩn: không det970=1 nào thiếu bộ ba; không FP trên arm bản vá; số bộ ba chuẩn
khớp `lf_counts.py`. 0 vấn đề.
