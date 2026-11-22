# Đo lại jar CS2 — wave 2 (artifact-keeper), 2026-11-21

Protocol đầy đủ: `../cs2-wave1-20261121/PROTOCOL.md`. Jar `evomaster-CS2-f3412dc8.jar` (sha16 `f3412dc87f1083a3`),
bỏ cờ D1 (phán quyết chỉ C4). Model m2-nodup (`dcc77b59ed0f`), giống LF. Thay đổi CS2 so với LF: chỉ probe C4
(`RestSecurityBuilder.kt`) chỉ kết luận trên mã của source.

Wave 2 nối tiếp (guard "mỗi lúc một việc nặng"). Trình tự (theo `../lf-wave2-20261118/PROTOCOL.md` +
`docs/targets-bringup.md` §5–6):
1. `docker stop reports-api` để nhả cổng 8080 (sau khi wave 1 xong).
2. Repo artifact-keeper ở `infra/artifact-keeper-target/src`, HEAD `e56d3aa7` (bản lỗi), status đúng 2 dòng
   (`M docker/Dockerfile.backend.dev`, `?? docker-compose.thesis.yml`) — đã xác nhận.
3. `ak_vuln.sh` 5 seed — tự `reseed.sh full` trước mỗi seed; proxy `capture_proxy.py 8212→8080`;
   `--extraPhaseBudgetPercentage 0.25 --ratePerMinute 600 --maxTime 1200s`, swagger `openapi-trimmed.json`, target :8212.
4. `git checkout e64cc5c608 -- backend .sqlx` → reseed rebuild (~141s) → KIỂM TAY bản vá còn sống
   (token victim cũ 200 → admin hạ quyền 200 → token cũ trả 401) → `ak_fixed.sh` 5 seed (user nâng từ 3, xem Lệch).
5. Sau đo: trả repo về `e56d3aa7` sạch (gỡ 3 file bản vá thêm theo targets-bringup §5), backend/.sqlx 0 dòng dirty;
   hạ container artifact-keeper; `docker start reports-api` + reset 200.

## Harness: diff với LF (chỉ JAR/WANT/BASE + nhãn log)

`ak_vuln.sh` vs LF: dòng 5–7 (JAR, WANT, BASE), dòng 79 (nhãn `LF-d559dc73`→`CS2-f3412dc8`) — 4 dòng.
`ak_fixed.sh` vs LF: 4 dòng trên + dòng 13 `SEEDS=(1 2 3)`→`(1 2 3 4 5)` — 5 dòng (lệch do user, xem dưới).
Companion `openapi-trimmed.json`, `artifactkeeper-auth-proxied.yaml`: trùng byte LF (cmp). Không đổi dòng lệnh
EvoMaster, cờ, luật dừng.

## Lệch so với khuôn LF (do user chỉ định 2026-11-21)

ak_fixed nâng **3 → 5 seed** "cho đủ để báo cáo". LF/ND dùng 3 seed cho arm fixed vì bản vá trả 401
(INCONCLUSIVE) cho token cũ → arm fixed không dựng được bộ ba, không cho TN; 3 seed chỉ để kiểm không-báo-nhầm.
Hệ quả: tổng hàng CS2 = 90 (wave1) + 5 (ak_vuln) + 5 (ak_fixed) = **100 hàng** (LF 98). Cặp so với LF chỉ có ở
seed 1–3 của ak_fixed; seed 4–5 không có đối chứng LF (arm fixed det970=0 nên không ảnh hưởng McNemar). Khai với peer 4a.

## Luật dừng (trong harness, như LF)

bản vá det970=1 (FP) → dừng; 2 hàng ERR liên tiếp; `Entering Sleep` mới; artifact-keeper seed đầu thiếu đăng nhập
một tài khoản hoặc evaluated < 389. Luật nổ: dừng, ghi lệch luật ở đây, tìm nguyên nhân trong log, báo phiên 4a.

## Sự cố lúc chạy

1. Lượt phóng đầu (19:13) hỏng câm: folder cs2-wave2 mới chỉ có `wd-ak` (harness `mkdir -p $WD`), thiếu `logs/`,
   `traffic/`, `tests/`. Redirect reseed `> $BASE/logs/<name>-reseed.txt` fail → `bash $RESEED` không chạy →
   5 hàng ERR tức thì, không có marker `victim login is_admin=True`. Nguyên nhân là chuẩn bị folder (chép 4 file
   nhưng chưa tạo thư mục con), không phải harness/jar. Khắc phục: `mkdir -p logs traffic tests`, chuyển 3 file void
   (`runs-ak-vuln.csv`, `progress-ak.log`, `nohup-ak-vuln.out`) sang `void-reseedfail-20261121/`, phóng lại 19:16.
   Lượt lại: reseed chạy thật (`=== reset DB ===`, DB healthy, backend biên dịch). 5 hàng ERR không tính vào số.

## Cách đếm

Như wave 1: báo cả TN_old (mọi bộ ba Assembled trên bản vá) và TN_403 (follow-up 403), kèm số bộ ba follow-up khác
2xx/403/401. Bản vá artifact-keeper trả 401 cho token cũ (INCONCLUSIVE) nên thường assembled=0; ghi rõ.

## Không làm

Không commit/push; không sửa cây mã EvoMaster, không dựng jar; không sửa docs/results.md, CLAUDE.md, jars.md hay
chương luận văn. Phiên 4a cập nhật docs sau khi có số.
