# Chạy lại wave 1 jar TR2 có log debug của builder (reports-api, vampi-seeded, pyLoad), 2026-11-26

Mục đích: có log chẩn đoán của builder (danh sách ứng viên transition, điểm, trường vai trò, trường nạn nhân, giá trị hạ
quyền, "transition chosen … (candidate k of n)", source và nạn nhân được thử) trên ba target của wave 1. Đợt
`../tr2-wave1-20261121/` chạy không có cấu hình log debug (log có 0 dòng DEBUG); đợt `../tr2-wave2-20261121/`
(artifact-keeper) đã có. Số trong luận văn vẫn lấy từ `../tr2-wave1-20261121/`; đợt này đo cùng jar, cùng cờ.

## Jar

`EvoMaster/evomaster-TR2-3beccb00.jar`, sha256 `3beccb0086b6983a6676eaf8df5c2b09cf90fc6ab72d22da7115ca0a5b4edb9f`, khớp
file `.sha256` cạnh jar. Model trong jar sha256 `dcc77b59ed0f94ee…`. Harness chặn nếu sha16 khác `3beccb0086b6983a`.
Không sửa cây mã EvoMaster, không dựng jar.

## Harness: diff với `../tr2-wave1-20261121/tr2_wave1.sh`

Diff đã chạy:
- dòng 8 `BASE` (thư mục mới); dòng 15 và 131 nhãn `TR2` → `TR2DBG` (ghi sổ);
- dòng 10 thêm `DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"`;
- dòng 68, 82, 95: `java -Xmx2g $DEBUG -jar …`. Đây là thay đổi duy nhất trên dòng lệnh EvoMaster, giống nhau ở cả 6
  làn. Cờ EvoMaster, seed, luật dừng không đổi;
- dòng 18–20: chờ điện AC trước khi chụp mốc ngủ và phóng làn (lúc chuẩn bị máy chạy pin 60%, đang xả). Ghi sổ, không
  đổi dòng lệnh EvoMaster.

Cấu hình log: root `warn`, `info_logger` `INFO`, `RestSecurityBuilder` và `RestSecurityOracle` `DEBUG`. Các dòng DEBUG
không khớp mẫu đếm của harness (`Assembled … statuses`, `Discarded a VOID`, `Privilege-restore`, `SUT state reset via`):
đã kiểm trên `../tr2-wave2-20261121/logs/ak-{vuln,fixed}-seed1.log`, 0 dòng DEBUG khớp.

## Dựng target

Container cũ chạy từ 2026-11-21/22 (đợt TR2). Dựng lại sạch theo `docs/targets-bringup.md` §4, như đợt TR2:
`docker rm -f` 6 container → `docker run` 6 container mới. Image: reports-api `7c98b63bbfc4`, vampi-seeded
`7ba9a98ac50e`, pyload-vuln `25451c1a1bd6`, pyload-fixed `5e2451ab380d` (khớp bảng §1). Env: reports-api-fixed
`APP_SECURITY_STATEFUL_ROLE_CHECK=true`; vampi `statefulrolecheck=0/1`; pyLoad `PYLOAD_STATEFUL_ROLE_CHECK=0/1`.
Kiểm: 6 spec/trang login 200, 6 reseed 200.

Khác đợt TR2: `artifact-keeper-dev-backend` và `-dev-db` đang chạy ở cổng 8082/30432 (không đụng cổng của wave 1,
CPU lúc chuẩn bị 0,37% và 0,05%). Đợt TR2 đã dừng backend này. Không đụng tới container của user.

## Thứ tự

6 làn song song như TR2: reports :8080 / :8081, vampi :5002 / :5003, pyLoad :8090 / :8091. 20 seed mỗi làn
reports/vampi, 5 mỗi làn pyLoad. Gộp `runs.csv` (90 hàng là số hàng, không phải kết quả).

## Luật dừng (viết trước lượt chạy, trong harness, như TR2)

Mỗi làn tự kiểm sau mỗi hàng; luật nổ thì dừng làn (`STOPPED`): bản vá có det970=1; arm lỗi 3 hàng đầu assembled=0;
2 hàng ERR liên tiếp; có `Entering Sleep` mới trong lúc một hàng chạy. Luật nổ: ghi lệch luật ở đây, tìm nguyên nhân
trong log trước khi chạy tiếp.

## Cách đếm

Như TR2: bộ ba đếm theo `* Assembled a stateful`. Báo theo target: 970 nổ bản lỗi, FP bản vá; so ghép đôi từng seed
với `../tr2-wave1-20261121/runs.csv`. Không ghi số mong đợi trước lượt chạy.

## Lệch luật đã khai

1. Chạy song song 6 làn (như TR2).
2. Thêm cấu hình log debug: tăng I/O ghi log. Ngân sách tìm kiếm tính theo thời gian, nên lượt chạy có thể lệch TR2 cả
   khi không có thay đổi nào.

## Kết quả (sau lượt chạy)

Chạy 00:30:50 → 02:21:48, 90 hàng, không làn nào dừng, AC Power suốt đợt. Kiểm toàn vẹn: 90 log đều có dòng DEBUG
và dòng `transition chosen`; số `* Assembled a stateful` khớp cột `assembled`; không có 970 nào thiếu bộ ba; 0 hàng ERR.
`audit970.out`: 21 PASS, 5 FAIL (5 FAIL là 5 test pyLoad, xác thực bằng cookie nên checker không đọc được, như TR2).

So từng seed với TR2: `compare_tr2.py` → `compare-tr2.out`.
- 970 theo arm: reports-api 12/20 và 0/20, pyLoad 5/5 và 0/5, giống TR2. vampi-seeded bản lỗi 7/20 (TR2 6/20), bản vá
  0/20.
- Hàng khác duy nhất ở cột 970: vampi-seeded seed 15 (TR2 0, đợt này 1). Seed này đã lệch giữa CS2 (1) và TR2 (0) do
  ngân sách tính theo thời gian (`../tr2-wave1-20261121/CORRECTION-vampi-seed15.md`).
- Khác ở cột khác: vampi seed 5 có 2 lần khôi phục bị từ chối (TR2 1); vampi seed 15 và 19 khác mã lỗi của oracle khác
  (205, 209). Các cột còn lại trùng.

Log debug cho thấy:
- thứ hạng transition của ba target (khối cuối `compare-tr2.out`);
- 6 lượt vampi-seeded bản lỗi không thử lần nào (seed 2, 4, 6, 13, 14, 18, cùng các seed như TR2): source duy nhất qua
  guard là `PUT /books/v1/{book_title}/secret`, và `victims []`, tức không test nào được giữ sau pha tìm kiếm gọi source
  đó bằng một tài khoản đã đăng nhập và nhận 2xx (`victimSlicesOn`, `RestSecurityBuilder.kt:760`);
- 8 lượt reports-api bản lỗi bỏ sót (seed 1, 3, 4, 7, 13, 14, 16, 19, như TR2): mọi lần thử qua mã trạng thái đều bị
  bước đăng nhập lại hủy với lý do "a call before the source of the replayed slice changed status group". Log debug
  không ghi đó là lời gọi nào.

## Không làm

Không commit/push; không sửa cây mã EvoMaster, không dựng jar; không sửa `docs/results.md`, `CLAUDE.md`, `jars.md` hay
chương luận văn.
