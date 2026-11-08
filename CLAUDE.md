# CLAUDE.md — Luận văn: oracle phân quyền có trạng thái cho EvoMaster

Nghiên cứu an toàn phần mềm cho luận văn tốt nghiệp: thêm một bộ phát hiện lỗi phân quyền vào EvoMaster, công cụ sinh
test API mã nguồn mở. Mọi target chạy cục bộ trên máy tác giả hoặc là mã nguồn mở tải về để đo. Không tác động hệ thống
của ai khác.

Ảnh chụp hiện trạng. Sửa tại chỗ, xoá phần đã bị thay thế, không bao giờ nối thêm lịch sử.
Mỗi sự kiện nằm ở một file: file này giữ luật và trỏ tới phần còn lại (§7).

## 1. Dự án

- Oracle **970 `SECURITY_STATEFUL_AUTHORIZATION`**: một tài khoản vẫn vào được sau khi bị thu hẹp quyền, phát hiện bằng
  cách dùng lại thông tin đăng nhập cấp trước lúc đó.
- Giai đoạn: viết luận văn. Số đo cuối: jar M2, chạy lại mọi target ngày 2026-11-08 (§4). Hạn: **cuối tháng 11 năm
  2026**. Bản nháp: `writing/KLTN_NguyenLeMinh.pdf`.
- Luận văn viết bằng **tiếng Việt**. Trả lời theo ngôn ngữ của user.
- Tác giả: kỹ sư phần mềm, ~2 năm fintech, Java/Spring Boot. Đọc được Kotlin, viết Kotlin chưa thoải mái.
- Mã nguồn: `/Users/minhnguyen/IdeaProjects/EvoMaster`, nhánh `stateful-authz-oracle`, 15 commit trên `v6.1.1`, HEAD
  `9c4be5b1dc` (đã push). Không reset, không transition khai báo, không D1; phán quyết chỉ còn probe C4.
  `f73010103b` là jar P2f (dự phòng). Chi tiết: `infra/evomaster-ext/README.md`.
- Thư mục luận văn là một git repo (nhánh `main`, 10 commit).
- Đã dựng: quan hệ MR-A1, cách dựng bộ ba, phán quyết 970, và bốn target: hai lỗi gieo (`reports-api`,
  `vampi-seeded`) và hai lỗi thật (pyLoad CVE-2026-41133, artifact-keeper lỗi vendor #1821). Trong CSV của các lượt
  chạy, `tier1`, `tier2`, `tier2b` là reports-api, vampi-seeded, pyLoad.

## 2. Luật làm việc

### Phạm vi và mã nguồn

- Chỉ làm đúng việc được giao. Việc tuỳ chọn: hỏi trước. Bước nhỏ, lời lẽ đơn giản.
- Thay đổi EvoMaster chỉ nằm trong repo gốc. **Đưa mã ra xem và chờ OK trước khi viết hoặc dựng.**
  Trước một thay đổi có thể làm xê dịch một con số đã có, diễn tập rollback (skill `evomaster-build`).
- **Biên dịch được chưa phải là xong.** Mỗi thay đổi mã đi kèm một self-test chạy nó và kiểm một kết quả quan sát được,
  không phải kiểm cú pháp: `infra/evomaster-ext/selftest/<change>.sh`, exit 0 khi đạt, mỗi kiểm tra một dòng in ra, và
  mỗi kiểm tra phải có khả năng trượt. Test nêu tên những dòng mã mới mà nó chạy qua. Test nằm trong repo luận văn:
  không bao giờ nằm trong cây mã EvoMaster, không bao giờ nằm trong bản vá.
- **Mã ta thêm vào không mang comment**, ở mọi ngôn ngữ: không `//`, `/* */`, `#`, KDoc, Javadoc, docstring.
  Giải thích nằm ở chat, commit message hoặc `docs/`. Comment của upstream giữ nguyên. Không để lại debug print.
- Viết theo mã upstream xung quanh. Không bao giờ chạy formatter (ktlint, google-java-format, black) lên file upstream.
- Xử lý lỗi tường minh: một lượt chạy hỏng phải hiện ra thành một hàng hỏng, không bao giờ thành im lặng.
- Khi một kiểm tra trượt, sửa phần cài đặt. Chỉ đổi kỳ vọng khi có bằng chứng rằng kỳ vọng đó sai.
- Chỉ commit và push khi user yêu cầu. Message `<type>: <description>`, không có dòng attribution.
- Không khởi chạy agent trừ khi user yêu cầu. Không bao giờ dùng `--dangerously-skip-permissions`.
- Không để secret thật trong file. Thông tin đăng nhập của target tự gieo là dữ liệu test có chủ đích.

### Bằng chứng

- Mọi khẳng định truy được về một file trong `infra/em-results/` hoặc về một nguồn gốc. Chỗ nào không truy được thì nói
  ra ngay trong câu đó.
- Kiểm bài báo trên tài liệu sống, không kiểm theo trí nhớ.
- Một câu trích chỉ vào được bản giao nộp sau khi mở nguồn gốc và khớp đúng từng chữ (PDF: `pdftotext`). Bản tóm tắt do
  web-fetch trả về không tính là đã kiểm. Diễn giải lại thì ghi rõ là diễn giải.
- Mục tiêu là một luận văn bảo vệ được. Công sức dồn vào chỗ hội đồng sẽ hỏi; phạm vi phải làm xong được.
- Đánh giá giữ trung lập: nêu cả lập luận chống lại khuyến nghị của chính mình; sửa lỗi cũ công khai.
- Đào sâu nền móng dưới các kết quả đã có trước khi mở thêm phạm vi. Thành thật về độ khó và rủi ro.

### Đo đạc

- Im lặng không phải bằng chứng: phải cho thấy thiết bị đo có khả năng tạo ra tín hiệu (EvoMaster log mức `warn`; chẩn
  đoán của builder mức `debug`).
- Không bao giờ viết kết quả mong đợi vào harness hay vào doc trước lượt chạy.
- Mỗi arm một biến, kiểm bằng cách diff toàn bộ dòng lệnh.
- Một chênh lệch ghép đôi chỉ thành phát hiện khi có kiểm định và p-value đi kèm.
- Mỗi con số trích ra đều nêu jar của nó; một bảng không bao giờ trộn jar.
- Mỗi lúc một việc nặng (lượt EvoMaster, `mvn`, `docker build`, pytest replay): `--maxTime` là đồng hồ treo tường.
- Không lượt chạy nào kéo dài vô ích. Trước một batch, viết luật dừng sớm vào protocol, ví dụ 3 seed
  đầu của mọi arm cho cùng một mẫu và 0 bộ ba hợp lệ. Đọc từng hàng ngay khi nó rơi xuống; luật nổ thì dừng batch, ghi
  lần dừng đó thành một lệch luật, và tìm nguyên nhân trong log trước khi chạy tiếp. Sửa lãng phí đồng hồ trước lượt
  chạy: minimization chạy lại mọi test giữ lại, mà `--security` đòi `--minimize`, nên nâng rate lên thay vì bỏ
  minimize.
- Định cỡ ngân sách tìm kiếm theo API. EvoMaster chạy trước một test cho mỗi endpoint mỗi tài khoản, tài khoản cuối
  trong file auth đi trước (`RestSampler.kt:322–346`, `:46`); ngân sách dưới mức endpoint × tài khoản thì không bao giờ
  chạy tới tài khoản đầu tiên. Kiểm số lần đăng nhập của từng tài khoản trong traffic.
- Máy ngủ làm hỏng mọi hàng nó chạm vào: `--maxTime` vẫn đếm tiếp. Bọc batch trong `caffeinate -dims`, để mở nắp máy,
  cắm sạc (pin 1% thì máy vẫn ngủ), và cho harness dừng khi thấy bất kỳ `Entering Sleep` nào trong `pmset -g log` trong
  lúc một hàng đang chạy.
- Mỗi batch ghi vào một thư mục mới; xong thì snapshot sang `~/thesis-backups/`. Quy trình: skill `em-batch`,
  `regression-gate`.

### Viết — chat, docs, luận văn

- Viết ngắn. Nêu sự thật, không bình luận. Kết luận trước, bằng chứng sau. Mọi khẳng định có ví dụ.
- Giải thích cơ chế: nó làm gì, ai gọi, lúc nào, rồi một ví dụ với giá trị thật. Tên hàm, số dòng chỉ để tra.
- Artifact hoặc doc giải thích code phải có chạy tay: số dòng thật, giá trị vào thật, giá trị ra thật, mỗi dòng mã một hàng.
- Soát từng câu mình vừa viết. Cắt ngay khi gặp:
  - câu tương phản `X, không phải Y`: giữ X, bỏ vế Y;
  - mệnh đề đuôi `…, và đó là lý do…`, `…, nên có thể…`, `…, điều này cho thấy…`;
  - câu mở đoạn tổng kết `Nhìn chung…`, `Điều đáng nói nhất là…`;
  - tính từ đánh giá `mạnh nhất`, `đáng chú ý nhất`, `hoàn hảo`, `rất khác`;
  - ngoặc kép quanh cụm trừu tượng: viết thẳng bằng số hoặc sự kiện, hoặc xoá;
  - WHY không làm người đọc đổi hành động; cross-reference kể lể;
  - note lặp lại bảng hoặc hình ngay trên nó: xoá hẳn;
  - `⇒` `→` trong văn xuôi (trong hình chạy tay thì được), emoji, IN HOA nhấn mạnh rải rác;
  - ô bảng có câu thứ hai.
- Sửa bản cũ: xoá bản dài, không để bản ngắn nằm cạnh.
- Luận văn chỉ ghi kết quả cuối và cách đo. Sự cố lúc chạy (máy ngủ, chạy song song, seed chạy lại) và đời các jar
  không vào luận văn.
- Đã ghi vào file thì chỉ báo ngắn file và mục; không in lại nội dung ra chat.

### Thiết lập ngữ cảnh

Mỗi loại nội dung nằm đúng một chỗ; phần còn lại theo bảng §7.

| Nội dung | Chỗ |
|---|---|
| Luật, hiện trạng, con trỏ | file này; không ghi ngày sự kiện, đời jar hay phương pháp đã thay |
| Sự cố lúc chạy | `PROTOCOL.md` của thư mục chạy |
| Đời jar và commit | `infra/evomaster-ext/jars.md` |
| Phương pháp đã thay (lexicon) | `docs/lexicon.md` |
| App và dữ liệu đã bỏ khỏi luận văn | `~/thesis-archive/`, ngoài repo, giữ nguyên đường dẫn repo; không trích |
| Tài liệu học mã | `docs/code-walkthrough/` (kiểu EvoMaster: `part0-base-evomaster.md`; Kotlin: `kotlin-co-ban.md`), `docs/evomaster-study/` |
| Cách làm việc riêng với user | memory; không chép luật hay sự thật dự án, vì subagent không đọc memory |
| Doc hết hiệu lực | `docs/archive/`; không trích số hay luật từ đó |

- `~/.claude/rules/` bị loại khỏi dự án này (`claudeMdExcludes`, `.claude/settings.local.json`). Luật trong file này là
  tập con áp dụng được.
- Agent toàn cục trong `~/.claude/agents/` mang chỉ dẫn xung đột (TDD, coverage 80%, reviewer bắt buộc). Việc luận văn
  dùng `.claude/agents/thesis-{coder,runner,analyst,verifier}.md`.
- Agent Explore và Plan dựng sẵn không nạp file này: nhắc lại luật cần thiết khi giao việc cho chúng.
- `.claude/hooks/guard.py` chặn: việc nặng khi một batch đang chạy; xoá hoặc ghi đè dữ liệu đã ghi nhận và bản sao lưu;
  dòng comment mới trong mã (dòng chứa mốc `THESIS` được miễn).
- Sau khi đổi file ngữ cảnh, chạy `infra/context-eval/questions.md`.

## 3. Oracle — đặc tả đầy đủ `docs/metamorphic-authz-relations.md`

- **MR-A1.** Một thao tác ghi đòi hỏi đúng quyền bị gỡ, đã quan sát thấy ALLOWED, phải thành DENIED sau khi quyền đó bị
  gỡ, với cùng thông tin đăng nhập trước lúc gỡ. Quan hệ không phải là tính đơn điệu: quyền truy cập của tài khoản vừa
  bị hạ không bao giờ lớn lên.
- ALLOWED = 2xx. DENIED = 403. 401 = INCONCLUSIVE. 404 không phải từ chối; các target kiểm phân quyền trước khi kiểm tồn tại.
- **Guard.** Nguồn là một thao tác ghi bị chặn bởi quyền đã gỡ, và lời gọi xen giữa qua được
  `looksLikePermissionReducingTransition`. Không có guard thì `GET /reports` (viewer cũng được phép) đọc thành lỗi.
- **Bộ ba** `source, transition, follow-up`. Follow-up dùng lại token trước lúc chuyển; đăng nhập mới sau lúc chuyển trả
  token đã bị thu hẹp và che mất lỗi.
- **VOID** trừ khi source 2xx, transition 2xx và follow-up kết luận được. Một bộ ba VOID không là bằng chứng cho chiều nào.
- BSR INCITS 359 Draft 4/4/2003 §6.1.1 để ngỏ phiên đang mở sau `DeassignUser` cho phía cài đặt
  (*"could wait for such a session to terminate normally"*). Trích bản draft, không bao giờ trích bản đã xuất bản
  ANSI INCITS 359-2004: bản đó trả phí và ta không có (`infra/analysis/lexicon-rules/sources.md` §B).
  Một phát hiện dựa trên hợp đồng của chính ứng dụng (bản vá của vendor, biến thể đã sửa).
- Phạm vi: A1, hạ vai trò. A2 (chuyển quyền sở hữu) và A3 (hết hạn quyền) đã định nghĩa, chưa chứng minh.
  Lỗi chéo tài khoản (BOLA/BFLA) thuộc về baseline, Şahin et al. arXiv:2604.00702 (`docs/related-work.md`).

## 4. Số hiện tại — jar M2, chạy 2026-11-08; chi tiết, nguồn và dè dặt trong `docs/results.md`

| Target | Lỗi | 970 nổ, bản lỗi | FP, bản vá |
|---|---|---|---|
| `reports-api` | gieo | 19/20 | 0/20 |
| `vampi-seeded` | gieo | 7/20 | 0/20 |
| pyLoad | CVE-2026-41133 | 5/5 | 0/5 |
| artifact-keeper | lỗi vendor #1821 | 5/5 | 0/3, bản vá của vendor |

- 98 hàng, một jar: `m2-wave1-20261108/runs.csv` (90 hàng) và `m2-wave2-20261108/` (8 hàng artifact-keeper); đếm
  bằng `m2-wave1-20261108/m2_counts.py` (`m2-counts-cp.out`). Trên ba target đầu, M2 trùng P2f ở 90/90 ô 970.
- 0 FP trong 48 lượt bản đã vá, trên 30 bộ ba dựng được trên mã đã vá. TP 36, FN 14, FP 0, TN 30; mọi FN là lượt không
  dựng được bộ ba (`docs/results.md` §1a).
- Bản vá của artifact-keeper trả 401 cho token cũ, mà 401 là INCONCLUSIVE: 3 lượt không báo nhầm và cũng không dựng
  được bộ ba nào, nên không có TN.
- Ghi recall black-box của vampi-seeded là **30–35%**.
- Soát cấu trúc và replay chưa chạy trên M2. Soát cấu trúc: reports-api 39/39, vampi-seeded 20/20 (AF2, P2f),
  artifact-keeper 5/5 (P2f); pyLoad (auth bằng cookie) xác nhận bằng `verify_ground_truth.sh`. Replay từ trạng thái
  sạch, jar AF2: 55/59 (reports-api 38/39, vampi-seeded 17/20); pyLoad 28/38, 10 trượt ở assertion thân phản hồi, không
  ở mã trạng thái. Viết "replay được 55/59", không bao giờ viết "tái lập được".
- "Phát hiện khi đã có một bộ ba hợp lệ" gần như là định nghĩa. Không bao giờ trích nó như độ chính xác.
- Trên reports-api, mã 403 của probe C4 đến từ `POST /reports`. Không viết rằng C4 thử lại guard ở đó.
- Transition của pyLoad buộc `permission=1` và một giá trị `role` tìm sang trái; C4 xác nhận từng lần hạ quyền.
- Transition của artifact-keeper là `PATCH /api/v1/users/{id}` với `{"is_admin": false}`, builder tự chọn từ spec.
- Endpoint reseed của reports-api và pyLoad là của ta; của vampi-seeded là của VAmPI.

## 5. Jar — sổ đầy đủ `infra/evomaster-ext/jars.md`

- Mọi con số hiện tại: `EvoMaster/evomaster-M2-917c57dd.jar` = HEAD `9c4be5b1dc` với `stateful-authz-model.csv` thay
  bằng mô hình M2 (sha256 `b2deef150bf8…`). Cây mã còn M1: M2 chưa nằm trong commit nào. Không reset, không transition
  khai báo, không D1; `EMConfig.kt` trùng v6.1.1. M2 không chạy cổng: nó đo lại đầy đủ mọi arm trên mọi target.
- Dự phòng: `EvoMaster/evomaster-P2f-64ee8ffc.jar` = commit `f73010103b`, bộ số `p2f-full-20261015/` (180 hàng). Jar
  này còn reset, transition khai báo và D1, sau cờ mặc định tắt.
- Jar cũ còn được trích ở bảng riêng, ghi tên jar: AF2 (replay, `docs/results.md` §3).
- Một jar mới chỉ trích lại số sau khi qua cổng 12 hàng (skill `regression-gate`) hoặc sau một lượt đo lại đầy đủ; khi
  cách dựng bộ ba đổi thì phải đo lại các arm bị ảnh hưởng.

## 6. Hiện trạng

Giai đoạn viết. Yêu cầu của thầy hướng dẫn: báo cáo TP/TN/FP/FN theo từng target (§4); đưa bằng chứng ngoài các lỗi
tự gieo: pyLoad (CVE, bản vá do ta viết) và artifact-keeper (lỗi vendor, bản vá của vendor), hai bằng chứng ngang nhau.

**Mô hình chọn transition.** Naive Bayes trên token path, trường và verb của mỗi op ghi; chấm op, trường vai trò, trường
nạn nhân và giá trị quyền (`docs/naive-bayes.md`). M2 học từ corpus gán nhãn lại (`nop-hoi-dong/nhan-hoc-cuoi.csv`,
209 op T trên 10.381 op ghi; quy trình `infra/analysis/lexicon-rules/relabel-20261101/PROTOCOL.md`). Trên nửa thi
(237 spec, 8.674 op ghi, 153 op T): 117 op T có điểm dương (76,5%, Clopper–Pearson 68,9–82,9%), 763 trong 880 op điểm
dương mang nhãn N. Kiểm chéo trên 47 spec của M1 là số thăm dò, vì 47 spec đó đã bị nhìn nhiều lần. Còn viết tay:
`1, 0, 2` cho trường số, token `id`. Cổng posterior > 0,5 cũng chặn phán quyết (`RestSecurityOracle.kt:577`, `:596`).
Đổi cách chấm (viết tay, lexicon, M1, M2) không mất phát hiện nào (`docs/results.md` §6).

**Lexicon** (jar `L` tới `AF2`) chỉ còn là phép so sánh trong chương mô hình. Số và cách trích: `docs/lexicon.md`.

**Chỉ bốn target.** Luận văn chỉ dùng bốn target ở §4. App khác đã thử không vào luận văn.

**Target phát triển.** pyLoad và artifact-keeper là target phát triển: các bản sửa builder được viết trong lúc chạy
chính chúng. Nhãn này chỉ chặn khẳng định về recall trên app lạ. Một lỗi thật tool bắt được, không có chuỗi riêng của
app trong mã, vẫn báo cáo được, kèm lịch sử sửa. artifact-keeper: mã builder, oracle và mô hình không chứa chuỗi nào
của app; spec của app bị loại khỏi corpus học; lịch sử sửa theo jar ở `docs/results.md` §5.

**Nhịp làm việc.** Một phiên tương tác làm việc; không có phiên chạy không người trông.
Batch rút gọn, chọn trước lượt chạy: không đổi cách dựng hay cách phán quyết thì chỉ chạy cổng; thay đổi nhỏ thì chạy
seeds 1–10 trên mọi arm và target; thay đổi lớn hoặc một arm mới thì chờ một lượt đầy đủ. Số của luận văn chỉ lấy từ bộ
đầy đủ.

**Chưa làm.** RESTler trong related work (`docs/related-work.md` §4); phát lệnh khôi phục của
operator vào test sinh ra (replay reports-api seed 16); ablation theo từng thành phần; arm so sánh dùng LLM phân loại
transition; dựng chủ động (D2). Còn mở: `docs/argument.md`, `docs/lexicon.md`.

**Hạn chế phải viết.** A2/A3 chưa chứng minh; mã từ chối chưa cấu hình được (bản vá của artifact-keeper trả 401);
pyLoad và artifact-keeper là target phát triển; không khẳng định recall trên app lạ.

## 7. Tra ở đâu

| Cần | File |
|---|---|
| Định nghĩa oracle | `docs/metamorphic-authz-relations.md` |
| Số, soát tay, hạn chế, cách viết | `docs/results.md` |
| Luận điểm, bằng chứng, giới hạn từng luận điểm | `docs/argument.md` |
| Related work, tính mới, trích dẫn đã kiểm | `docs/related-work.md` |
| Thay đổi mã, điểm tích hợp, mã fault | `infra/evomaster-ext/README.md` |
| Sổ jar đầy đủ | `infra/evomaster-ext/jars.md` |
| Self-test cho mỗi thay đổi mã | `infra/evomaster-ext/selftest/` |
| Vướng safety classifier: triệu chứng, cách làm | `infra/evomaster-ext/safety-classifier-notes.md` |
| Mô hình Naive Bayes (M2, M1): cách tính, kiểm chéo, file mô hình | `docs/naive-bayes.md` |
| Gán nhãn lại, mô hình M2, bản nộp hội đồng | `infra/analysis/lexicon-rules/relabel-20261101/PROTOCOL.md`, `relabel-20261101/nop-hoi-dong/`, `lexicon-rules/m2-model-20261107/` |
| Bộ từ vựng của jar `L` tới `AF2`: luật, nhãn, ba lần rút, thứ hạng | `docs/lexicon.md`, `infra/analysis/lexicon-rules/` |
| Corpus gán nhãn: 36 spec WFD, danh sách apis.guru | `infra/analysis/corpus/` |
| Mã từ chối trên ba target | `infra/analysis/denial-codes-2026-09-17.md` |
| Probe C4 re-login | `docs/metamorphic-authz-relations.md` §5.6 |
| Ghi chú từng hàm của builder, jar SR: làm gì, ai gọi, ví dụ chạy tay | `docs/evomaster-study/03-ham-stateful-authz.md` |
| Target reports-api | `infra/reports-api/README.md` |
| Target vampi-seeded | `infra/vampi-seeded/THESIS-SEED.md` |
| Target pyLoad và các lệch luật đã khai | `docs/tier2b-pyload-target.md` §3 |
| Target artifact-keeper: dựng, phần của ta, kiểm tay | `docs/artifact-keeper-target.md` |
| Cách soát tay | skill `em-batch` (After a batch), `docs/results.md` §3 |
| Sổ chạy và kho đề bài của squad (đã tắt) | `infra/squad/SQUAD.md` |
| Dựng, jar, rollback, git | skill `evomaster-build` |
| Chạy EvoMaster, batch, soát, replay | skill `em-batch` |
| Cổng hồi quy | skill `regression-gate` |
| HTML sang PDF | skill `render-pdf` |
| Đề cương | `Thesis_Proposal_EvoMaster.html`, `.pdf` |
| Bản nháp khoá luận, quy định của bộ môn | `writing/KLTN_NguyenLeMinh.pdf`, `writing/QuyDinh_KhoaLuanTotNghiep_BoMonCNPM_2026-01.pdf` |
| Kiểm ngữ cảnh | `infra/context-eval/questions.md`; file đã nạp: `.claude/logs/instructions-loaded.jsonl` |
| Quy trình viết | ARS plugin: `/ars-plan`, `/ars-outline`, `/ars-reviewer` |
