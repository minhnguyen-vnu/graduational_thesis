# Đo lại jar SL+M2 (shorten-logic + model M2), 2026-11-12

Chạy lại cả bốn target với jar SL+M2 để kiểm refactor "shorten-logic" không đổi số trên target thật và trích lại số
trên mã đã gộp. Thư mục: wave 1 ở đây, wave 2 ở `../slm2-wave2-20261112/`.

## Jar

`EvoMaster/evomaster-SLM2-b8b5cf1a.jar` = HEAD `9c4be5b1dc` + thay đổi shorten-logic (chưa commit, giữ comment
`THESIS`) + `stateful-authz-model.csv` thay bằng M2 (sha256 `b2deef150bf8…`). Dựng 2026-11-12; M1 khôi phục về cây mã
ngay sau khi dựng. sha16 jar `b8b5cf1adb560c87`.
Khác jar M2 (`917c57dd`) đúng ở phần mã: M2 = cùng model nhưng mã HEAD chưa gộp (jar DC); SLM2 = cùng model, mã đã gộp.
Self-test tĩnh/động của chính thay đổi shorten-logic: `selftest/shorten-logic-20261112.sh` (đạt trước đợt này).
Mỗi harness chặn nếu sha16 khác `b8b5cf1adb560c87`.

## Mục đích

Refactor shorten-logic gộp 9 chỗ mã lặp (`wip/shorten-logic-20261112.md`), tuyên bố không đổi logic. Self-test trên
stub đã cho 135/135 so với jar DC. Đợt này là bằng chứng end-to-end trên target thật: nếu SLM2 tái lập đúng số của M2
thì refactor không đổi hành vi, và số luận văn trích được từ mã đã gộp. Không qua cổng 12/21 hàng: jar không reset, đo
thẳng mọi arm không reset, so số với bộ M2 đã lưu (`../m2-wave1-20261108/`, `../m2-wave2-20261108/`).

## Cờ

Như `docs/results.md` §0, giống hệt đợt M2 (bỏ `--statefulAuthzTwoCredentialJudgment`; phán quyết chỉ C4).
`--useExperimentalOracles true`; `--extraPhaseBudgetPercentage` 0,6 (reports/vampi/pyLoad) hoặc 0,25 (artifact-keeper).
Tier-1/2 `--maxTime 150s`; pyLoad `10m`; artifact-keeper `1200s`. Mỗi JVM `-Xmx2g`. Reseed SUT trước mỗi lượt. Mỗi
làn `cd` một thư mục làm việc riêng.

## Thứ tự

- Wave 1 (`slm2_wave1.sh`): 6 làn **song song**, mỗi target một cổng — reports lỗi :8080 / vá :8081, vampi :5002 /
  :5003, pyLoad :8090 / :8091. 20 seed mỗi làn reports/vampi, 5 mỗi làn pyLoad. Gộp `runs.csv` (90 hàng).
  Trước khi phóng: dừng container `reports-api` đang giữ :8080? Không — Wave 1 dùng chính reports-api :8080.
- Wave 2 (`../slm2-wave2-20261112/`): **nối tiếp** (guard "mỗi lúc một việc nặng"). Dừng container `reports-api`
  (:8080) để nhường artifact-keeper. `ak_vuln.sh` 5 seed (commit lỗi `e56d3aa7`), rồi checkout commit vá `e64cc5c608`
  + `.sqlx` → rebuild → `ak_fixed.sh` 3 seed. Sau đo: trả repo về `e56d3aa7` sạch.

## Luật dừng (viết trước lượt chạy)

Như đợt M2, nằm trong harness. Mỗi làn tự kiểm sau mỗi hàng; luật nổ thì dừng làn (ghi `STOPPED`/`DUNG`):
bản vá có det970=1 (FP); arm lỗi 3 hàng đầu assembled=0; 2 hàng ERR liên tiếp; có `Entering Sleep` mới; artifact-keeper
seed đầu thiếu đăng nhập một tài khoản hoặc evaluated < 389. Không luật nào nổ trong đợt này.

## Kết quả — trùng khít M2

| Target | SL+M2 lỗi | SL+M2 vá | M2 (08/11) |
|---|---|---|---|
| reports-api | 19/20 | 0/20 | 19/20, 0/20 |
| vampi-seeded | 7/20 | 0/20 | 7/20, 0/20 |
| pyLoad | 5/5 | 0/5 | 5/5, 0/5 |
| artifact-keeper | 5/5 | 0/3 | 5/5, 0/3 |

98 hàng. Integrity: 0 hàng det970 thiếu triple, 0 FP, 0 ERR. Audit (`audit970.out`): reports+vampi 26 PASS / 0 FAIL /
0 UNPARSED; artifact-keeper 5 PASS / 0 FAIL. artifact-keeper mọi seed triple `PATCH:/api/v1/users/{id}` 200/200/200;
bản vá mọi seed assembled=0 (token cũ sau hạ quyền trả 401 = INCONCLUSIVE, không dựng được bộ ba).

Bản vá xác nhận sống bằng tay trước khi đo FP (`logs/../fixed-manual-reseed.txt` ở wave 2): token cũ của victim tạo
user được (200) → admin hạ quyền victim (200) → dùng lại token cũ trả **401**.

## Lệch luật đã khai

1. **Chạy song song** 6 làn wave 1, theo yêu cầu user. Wave 2 nối tiếp.
2. **Bỏ cờ D1** `--statefulAuthzTwoCredentialJudgment` (jar không có cờ này). Phán quyết chỉ C4.
3. **Không qua cổng 21 hàng**: jar không reset, đo arm không reset thẳng, so bộ M2 đã lưu.
4. Luật §6 "không chạy không người trông" đã bị xoá khỏi `CLAUDE.md` trong phiên này theo yêu cầu user.

## Sự cố

Không. Máy không ngủ (0 `Entering Sleep` kể từ 14:38), cắm sạc suốt, không Docker treo. Monitor log reseed bản vá một
lần hết hạn không bắt được dòng "backend up" (timing của `tail -F`); reseed thực tế thành công (kiểm tay ngay sau).

## Tái lập

Jar dựng lại từ cây shorten-logic (chưa commit) + model M2 bằng
`scratchpad/build_slm2.sh`-tương đương: `cp m2-model .../stateful-authz-model.csv`, build core, `git checkout` trả M1.
Harness và log từng làn ở thư mục này và `../slm2-wave2-20261112/`. Chưa commit, chưa promote.
