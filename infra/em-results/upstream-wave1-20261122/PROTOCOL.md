# Baseline upstream EvoMaster — wave 1 (reports-api vuln, vampi-seeded vuln), 2026-11-22

Đo baseline: jar EvoMaster upstream master trên hai target gieo lỗi bản lỗi, mỗi target 20 seed (40 hàng), **cờ giống
hệt `tr2-wave1-20261121`** (chỉ đổi jar + thư mục output). Mục đích: so cái upstream tự phát hiện trên reports-api và
vampi với oracle 970 của luận văn, trên cùng cờ. Việc user giao qua phiên `graduational-thesis-1c`; phiên này (Opus 4.8,
`graduational-thesis-de`) đo. Theo CLAUDE.md §2 (Đo đạc) và skill `em-batch`. Không sửa cây mã EvoMaster, không dựng
jar, không commit, không sửa `docs/results.md`.

## Jar

`EvoMaster-upstream/evomaster-upstream-master-b6307c2d.jar`. sha256
`b6307c2dd247caaf44a5110d7ed03069bbdb0d0205934a250735cbd09dfaa91e`, sha16 WANT `b6307c2dd247caaf`; `shasum -a 256 -c
…jar.sha256` in **OK** (đã kiểm). Upstream `WebFuzzing/EvoMaster` nhánh master, commit `dd063b4f9f` (2026-11-21),
version `6.2.1-SNAPSHOT`. Dựng 2026-11-22 bằng `mvn -pl core -am package -DskipTests` dưới JDK 17 (do phiên 1c/user,
không phải phiên này). Harness chặn nếu sha16 jar khác WANT.

Jar upstream **không có** oracle 970 `SECURITY_STATEFUL_AUTHORIZATION` và không in dòng `Assembled`/`Discarded VOID`/
`Privilege-restore` của builder luận văn. Hai cờ `--useExperimentalOracles` và `--extraPhaseBudgetPercentage` đều có
trong jar (kiểm qua `--help`: `--useExperimentalOracles <Boolean>`, `--extraPhaseBudgetPercentage <Double>`).

## Cờ

Giống hệt TR2 wave1: `--blackBox true`, `--useExperimentalOracles true`, `--extraPhaseBudgetPercentage 0.6`,
`--outputFormat PYTHON_UNITTEST`, `--ratePerMinute 120`, `--maxTime 150s`, `--seed <s>`, `-Xmx2g`, JDK 17. Reseed SUT
trước mỗi lượt: reports `POST /reset`, vampi `GET /createdb`. Config:
`infra/em-config/{reports-auth,vampi-seeded-auth}.yaml`.

## Harness: diff dòng lệnh với TR2

`upstream_wave1.sh` chép từ `../tr2-wave1-20261121/tr2_wave1.sh`. Thân hàm `t1` và `t2` (lời gọi java) **IDENTICAL**
với TR2 (đã `diff`): chỉ khác giá trị biến `$JAR` (đường dẫn jar) và `$BASE` (đường dẫn output). Các biến đổi:

- `JAR` → `…/EvoMaster-upstream/evomaster-upstream-master-b6307c2d.jar`
- `WANT` → `b6307c2dd247caaf`
- `BASE` → `$E/upstream-wave1-20261122`

Lane rút còn 2 (bỏ t1f/t2f/t2bv/t2bf — không có arm fixed, không đo pyLoad):

- `lane t1v t1 tier1 vuln      8080 20 &`  (reports-api bản lỗi)
- `lane t2v t2 tier2 ours-vuln 5002 20 &`  (vampi-seeded bản lỗi)

Chạy **song song** 2 lane. Hàm `t2b` và biến pyLoad (SPEC2B/EXCLUDE) đã gỡ vì không lane nào gọi.

## Thay đổi hàm check/collect so với TR2 (jar upstream không có log builder)

- **Bỏ** luật "first 3 rows … assembled 0": jar upstream không in `Assembled`, giữ luật này thì harness dừng sau 3 hàng.
- **Bỏ** luật false positive arm fixed: không có arm fixed trong batch này.
- **Giữ**: 2 hàng ERR liên tiếp → dừng lane; `Entering Sleep` mới trong `pmset -g log` lúc một hàng chạy → dừng.
- **Thêm** (trong `collect`): hàng có log **không** chứa `EvoMaster process has completed successfully`, hoặc thiếu
  `report.json`, thì det970 ghi `ERR`.
- Cột CSV giữ nguyên của TR2 (`tier,arm,seed,reset,det970,assembled,void_count,resets,restores_ok,restores_no,statuses,faults`).
  Với jar upstream: `det970` = 0 (không có 970) hoặc `ERR`; `assembled/void/restore` = 0; `statuses` = NA. Cột
  `faults` = toàn bộ mã fault trong `report.json` (`faults.foundFaults[].faultCategories[].code`), nối bằng `|`.

## Luật dừng sớm (viết trước khi chạy)

3 seed đầu của một lane đều ERR → dừng batch, tìm nguyên nhân trong log trước khi chạy tiếp. (Luật "2 ERR liên tiếp"
chặt hơn sẽ nổ trước ở seed 2; cả hai đều bật.) Luật nổ: dừng lane (`STOPPED` trong `logs/<lane>.log`), ghi lệch luật
ở đây, báo phiên 1c.

**Cấu trúc dừng.** `halt` chạy trong lane là background job (`lane … &`) nên `exit 1` chỉ dừng lane đó; lane kia chạy
tiếp. Máy ngủ thì cả hai lane đều bắt được ở hàng kế.

## Thứ tự

Một wave: 2 lane song song, mỗi lane 20 seed tuần tự (seq 1→20). Gộp `runs.csv` (40 hàng kỳ vọng về số lượng hàng,
không về kết quả). Không có wave 2.

## Dựng target (trước khi phóng)

Container `reports-api` (:8080) và `vampi-seeded` (:5002) đang chạy từ trước. Kiểm health: `/v3/api-docs` và
`/openapi.json` đều **200** (đã xác nhận). Reseed nằm trong harness trước mỗi lượt.

## Nguồn điện

Nhắc user: cắm sạc, mở nắp máy. Harness chụp mốc `Entering Sleep` gần nhất lúc phóng, dừng nếu có mốc mới trong lúc một
hàng chạy.

## KHÔNG đụng

`../upstream-b6307c2d-20261122/` là hai lượt thử tay của user (seed 1, reports-api) — không ghi đè, không xoá.

## Lệch luật đã khai

Không có. Batch chạy xong 40/40 hàng (reports 20 + vampi 20), 0 ERR, 0 STOPPED, 0 máy ngủ (23:36→01:30). Toàn vẹn:
40 hàng CSV = 40 log = 40 report.json; 40 log có marker "completed successfully". Kết quả: `upstream-analysis.out`.

## Sau khi chạy

Gộp `runs.csv` (40 hàng); kiểm toàn vẹn (số hàng CSV = số log, mỗi hàng có `report.json`); bảng tóm tắt theo target: mỗi
mã fault → số seed (/20) có mã đó, ghi rõ jar `b6307c2d` cạnh bảng; snapshot `~/thesis-backups/` + `.sha256`; nhắn phiên
`graduational-thesis-1c`.
