# Đo lại jar TR2 — wave 2 (artifact-keeper), 2026-11-21

Protocol đầy đủ: `../tr2-wave1-20261121/PROTOCOL.md`. Jar `evomaster-TR2-3beccb00.jar` (sha16 `3beccb0086b6983a`),
bỏ cờ D1 (phán quyết chỉ C4). Model `dcc77b59ed0f…`, giống LF/CS2. Cây = CS2 + `trim-restore`.

Wave 2 **nối tiếp** sau wave 1 (guard "mỗi lúc một việc nặng"). Trình tự (theo `../cs2-wave2-20261121/PROTOCOL.md` +
`docs/targets-bringup.md` §5–6):
1. `docker stop reports-api` để nhả cổng 8080 (sau khi wave 1 xong).
2. Repo artifact-keeper ở `infra/artifact-keeper-target/src`, HEAD `e56d3aa7` (bản lỗi), `git status --short` đúng 2 dòng
   (`M docker/Dockerfile.backend.dev`, `?? docker-compose.thesis.yml`) — kiểm trước khi chạy. Dựng backend (reseed full).
3. `ak_vuln.sh` 5 seed — tự `reseed.sh full` trước mỗi seed; proxy `capture_proxy.py 8212→8080`;
   `--extraPhaseBudgetPercentage 0.25 --ratePerMinute 600 --maxTime 1200s`, swagger `openapi-trimmed.json`, target :8212.
4. `git checkout e64cc5c608 -- backend .sqlx` → reseed rebuild (~141s) → KIỂM TAY bản vá còn sống
   (token victim cũ 200 → admin hạ quyền 200 → token cũ trả 401) → `ak_fixed.sh` 5 seed (user nâng từ 3, xem Lệch).
5. Sau đo: trả repo về `e56d3aa7` sạch (gỡ 3 file bản vá thêm theo targets-bringup §5), backend/.sqlx 0 dòng dirty;
   hạ container artifact-keeper; `docker start reports-api` + reset 200.

## Thay đổi so với CS2 (trim-restore)

Chỉ S2 đổi hành vi trên artifact-keeper: `POST /api/v1/admin/sso/oidc` không còn là ứng viên transition (thiếu
`victimField`). Transition của bộ ba ak là `PATCH /api/v1/users/{id}` (có victimField), không bị S2 loại. Đo thẳng;
**không ghi số mong đợi** (CLAUDE.md §2). So từng seed với CS2 (chỉ có vuln seed 1–3) và với LF (`../lf-wave2-20261118/`).

## Harness: diff với CS2 (chỉ JAR/WANT/BASE + nhãn log)

`ak_vuln.sh`, `ak_fixed.sh` vs CS2: dòng 5–7 (JAR, WANT, BASE), dòng 79 (nhãn `CS2-f3412dc8`→`TR2-3beccb00`) — đúng 4
dòng mỗi file, diff đã chạy. `ak_vuln` vs `ak_fixed`: chỉ dòng 12 `ARM=`. Companion `openapi-trimmed.json`,
`artifactkeeper-auth-proxied.yaml`: trùng byte CS2 (cmp). Không đổi dòng lệnh EvoMaster, cờ, luật dừng.
Thư mục con `logs/traffic/tests/wd-ak` đã tạo sẵn (tránh sự cố reseed hỏng câm như CS2 lượt phóng đầu).

## Lệch so với khuôn (do user chỉ định)

ak_fixed **5 seed** (nâng từ 3) "cho đủ để báo cáo", như CS2. Bản vá ak trả 401 (INCONCLUSIVE) cho token cũ → arm fixed
không dựng được bộ ba, không cho TN; 5 seed chỉ để kiểm không-báo-nhầm. Tổng TR2 = 90 (wave1) + 5 (vuln) + 5 (fixed)
= **100 hàng**. Cặp so với CS2 ở ak chỉ có ở vuln seed 1–3 (CS2 wave2 chưa xong: không có vuln seed 4–5, không có fixed);
arm fixed so với LF (0/3). Khai với phiên 54.

## Luật dừng

Trong harness ak (như CS2/LF): `Entering Sleep` mới → dừng; seed đầu thiếu đăng nhập một tài khoản → dừng;
evaluated < 389 ở seed đầu → cảnh báo. Harness ak **không** tự dừng khi arm vá có det970=1 (khác harness wave 1):
luật "FP → dừng" ở đây được bảo đảm bằng (a) kiểm tay bản vá trước lượt ([F] replay token cũ = 401, đã xác nhận
04:06, `logs/patched-handcheck.txt`) và (b) watcher nền bắt mọi `fixed,…,det970=1` trong `runs-ak-fixed.csv` để báo
và dừng tay. Luật nổ: dừng, ghi lệch luật ở đây, tìm nguyên nhân log, báo phiên 54.

## Cách đếm

Như CS2/LF: báo cả TN_old (mọi bộ ba Assembled trên bản vá) và TN_403 (follow-up 403), kèm số bộ ba follow-up khác
2xx/403/401. Bản vá ak trả 401 cho token cũ (INCONCLUSIVE) nên thường assembled=0; ghi rõ. Số bộ ba đếm theo log
`transition PATCH:... statuses`, UNCONFIRMED theo "Discarded an UNCONFIRMED", VOID theo "Discarded a VOID".

## Sự cố lúc chạy

(ghi khi xảy ra)

## Không làm

Không commit/push; không sửa cây mã EvoMaster, không dựng jar; không sửa docs/results.md, CLAUDE.md, jars.md hay
chương luận văn. Phiên 54 cập nhật docs sau khi có số.
