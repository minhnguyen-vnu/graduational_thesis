# CLAUDE.md — Luận văn: oracle phân quyền có trạng thái cho EvoMaster

Nghiên cứu an toàn phần mềm cho luận văn tốt nghiệp: thêm một bộ phát hiện lỗi phân quyền vào EvoMaster, công cụ sinh
test API mã nguồn mở. Mọi target chạy cục bộ trên máy tác giả hoặc là mã nguồn mở tải về để đo. Không tác động hệ thống
của ai khác.

Ảnh chụp hiện trạng. Sửa tại chỗ, xoá phần đã bị thay thế, không bao giờ nối thêm lịch sử.
Mỗi sự kiện nằm ở một file: file này giữ luật và trỏ tới phần còn lại (§7).

## 1. Dự án

- Oracle **970 `SECURITY_STATEFUL_AUTHORIZATION`**: một tài khoản vẫn vào được sau khi bị thu hẹp quyền, phát hiện bằng
  cách dùng lại thông tin đăng nhập cấp trước lúc đó.
- Giai đoạn: phát triển tới **2026-09-30** (§6). Tháng 10: tinh chỉnh, đánh giá, viết. Hạn: **cuối tháng 11 năm 2026**.
- Luận văn viết bằng **tiếng Việt**. Trả lời theo ngôn ngữ của user.
- Tác giả: kỹ sư phần mềm, ~2 năm fintech, Java/Spring Boot. Đọc được Kotlin, viết Kotlin chưa thoải mái.
- Mã nguồn: `/Users/minhnguyen/IdeaProjects/EvoMaster`, nhánh `stateful-authz-oracle`, 12 commit trên `v6.1.1`, HEAD
  `a544c996ac` (jar P2e, chưa push); commit ngay trước `8d6cf8431f` là jar AF2. Chi tiết: `infra/evomaster-ext/README.md`.
- Thư mục luận văn là một git repo (nhánh `main`, 2 commit).
- Đã dựng: quan hệ MR-A1, cách dựng bộ ba, phán quyết 970, và ba target — Tier-1 `reports-api`, Tier-2 `vampi-seeded`,
  Tier-2b pyLoad CVE-2026-41133.

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
- Không lượt chạy nào kéo dài vô ích (user, 2026-09-28). Trước một batch, viết luật dừng sớm vào protocol, ví dụ 3 seed
  đầu của mọi arm cho cùng một mẫu và 0 bộ ba hợp lệ. Đọc từng hàng ngay khi nó rơi xuống; luật nổ thì dừng batch, ghi
  lần dừng đó thành một lệch luật, và tìm nguyên nhân trong log trước khi chạy tiếp. Sửa lãng phí đồng hồ trước lượt
  chạy: trên Grafana, minimization chạy lại 493 test mất 8,5 trên 24 phút ở `--ratePerMinute 60`; `--security` đòi
  `--minimize`, nên nâng rate lên thay vì bỏ minimize.
- Định cỡ ngân sách tìm kiếm theo API. EvoMaster chạy trước một test cho mỗi endpoint mỗi tài khoản, tài khoản cuối
  trong file auth đi trước (`RestSampler.kt:322–346`, `:46`); ngân sách dưới mức endpoint × tài khoản thì không bao giờ
  chạy tới tài khoản đầu tiên. Grafana (309 endpoint) và Mattermost (623) mất `victim` theo đúng cách này. Kiểm số lần
  đăng nhập của từng tài khoản trong traffic.
- Máy ngủ làm hỏng mọi hàng nó chạm vào: `--maxTime` vẫn đếm tiếp. Bọc batch trong `caffeinate -dims`, để mở nắp máy, và
  cho harness dừng khi thấy bất kỳ `Entering Sleep` nào trong `pmset -g log` trong lúc một hàng đang chạy.
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
- Đã ghi vào file thì chỉ báo ngắn file và mục; không in lại nội dung ra chat.

### Thiết lập ngữ cảnh

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

## 4. Số hiện tại — jar P2e (`6ae8277b`, bộ gộp có lệch luật); chi tiết, nguồn và dè dặt trong `docs/results.md`

| Target | 970 nổ, không reset | 970 nổ, có reset | FP trên bản đã sửa |
|---|---|---|---|
| Tier-1 `reports-api` | 19/20 | 20/20 | 0/40 |
| Tier-2 `vampi-seeded` | 7/20 | 13/20 | 0/40 |
| Tier-2b pyLoad | 5/5 | 5/5 | 0/10 |

- Bộ gộp 180 hàng `p2e-continue-20261013/merged.csv`: 71 hàng P2e, 109 hàng P2d. Lệch luật đã khai (user,
  2026-10-14): bảng trộn jar, và cổng chạy trên P2d (21/21, `p2d-night-20261012/gate/`), chưa chạy trên P2e. 109
  hàng P2d không chạy qua đoạn mã P2e đổi. Mọi ô trùng AF2 (`af2-full-remeasure-20261003/`) và jar R từng seed. Lượt đầy đủ trên riêng P2e để sau
  (`p2e-full-20261014/`).
- 0 FP trong 90 lượt chạy target đã sửa, trên 116 bộ ba dựng được trên mã đã vá (AF2: 99).
- Soát cấu trúc: 59/59 lần nổ reports+vampi qua kiểm tra (P2e và AF2); pyLoad (auth bằng cookie) xác nhận bằng
  `verify_ground_truth.sh`. Replay từ trạng thái sạch, jar AF2, chưa chạy lại trên P2e: 55/59 (reports 38/39,
  vampi 17/20); pyLoad 28/38, 10 trượt ở assertion thân phản hồi, không ở mã trạng thái.
- Ghi recall black-box của Tier-2 là **30–35%**.
- Ablation reset **không có ý nghĩa thống kê**: Tier-2 McNemar chính xác p = 0,070. Không bao giờ viết "nhân quả".
- Viết "replay được 55/59", không bao giờ viết "tái lập được".
- "Phát hiện khi đã có một bộ ba hợp lệ" gần như là định nghĩa. Không bao giờ trích nó như độ chính xác.
- Không reset là con số chính. Endpoint reset của Tier-1 và Tier-2b là của ta.
- Trên Tier-1, mã 403 của probe C4 đến từ `POST /reports`. Không viết rằng C4 thử lại guard ở đó.
- Transition của pyLoad buộc `permission=1` và một giá trị `role` tìm sang trái; C4 xác nhận từng lần hạ quyền.

## 5. Jar — sổ đầy đủ `infra/evomaster-ext/jars.md`

- Mọi con số hiện tại: `EvoMaster/evomaster-P2e-6ae8277b.jar` = commit `a544c996ac` (nhánh `stateful-authz-oracle`):
  AF2 + P1 duyệt nhiều op, 20 lần thử thay vì 8 + P2 Naive Bayes thay các danh sách viết tay (thiết kế
  `infra/evomaster-ext/wip/p2-design-20261012.md`). Số lấy từ bộ gộp có lệch luật (§4).
- AF2 (`evomaster-AF2-6b5606d4.jar`, commit `8d6cf8431f`) và jar R (`5bce137f`, `007e5e09f9`) giữ làm nguồn gốc;
  replay trong `docs/results.md` §3 còn trên AF2.
- Một jar mới chỉ trích lại một con số sau khi qua cổng hồi quy, và khi cách dựng bộ ba đổi thì phải đo lại các arm bị
  ảnh hưởng. AF2 đã qua cổng (2026-10-02) và đo lại đầy đủ (`af2-full-remeasure-20261003/`). P2d qua cổng 21/21
  (2026-10-13, `p2d-night-20261012/gate/`); trong đó chỉ 2 hàng vampi seed 3 chạy qua đoạn mã P2e đổi, và 2 hàng này
  chạy lại trên P2e vẫn khớp kỳ vọng của cổng (`p2e-continue-20261013/gate-predict.out`). P2e chưa chạy cổng.

## 6. Hiện trạng cuối giai đoạn phát triển

Yêu cầu của thầy hướng dẫn: báo cáo TP/TN/FP/FN theo từng tier; đưa bằng chứng ngoài các lỗi tự gieo (pyLoad là một lỗi
của một lớp).

**Từ vựng.** AF2 chấm transition bằng lexicon (53 path + 45 param) và nhận diện trường bằng danh sách viết tay. P2e
thay cả hai bằng Naive Bayes rút từ nhãn vòng 4 (10.381 op ghi, 230 API): bảng `op`, `role`, `victim`, `low`/`high`
trong `stateful-authz-model.csv` (`infra/evomaster-ext/wip/p2-design-20261012.md`). Còn viết tay: `1, 0, 2` cho trường
số, token `id`. Số kiểm chéo đo trên 47 spec test đã bị nhìn nhiều lần, nên chỉ là thăm dò. Khi tắt D1, cổng
posterior > 0,5 cũng chặn phán quyết (`RestSecurityOracle.kt:583`, `:602`).

**Lexicon.** Rút từ các spec thật đã gán nhãn, đo trên spec held-out. Toàn bộ luật, nhãn, ba lần rút và thứ hạng:
`docs/lexicon.md`, `infra/analysis/lexicon-rules/`, `infra/analysis/corpus/sampling-plan.md`. Những con số không được
trích sai:
- Lexicon trong jar AF2 (P2e không còn đọc nó) là lần rút thứ ba, có audit: **53 từ path, 45 từ param**
  (`lexicon-rules/lexicon-20260921-audited/`).
- Thứ hạng trên nửa held-out, trên mọi endpoint ghi, bộ chấm điểm có tên trường thân (jar `RF` tới `AF2`):
  **top-1 0,667, top-3 0,833, top-8 1,000** theo thứ tự spec, khoảng tốt nhất–xấu nhất 0,500–0,833 / 0,667–0,833 /
  0,833–1,000. Bộ path-only trước đó (jar `L`): 0,500 / 0,667 / 1,000 (khoảng 0,333–0,667 / 0,500–0,667 / 0,833–1,000).
  Khoảng không phải sai số lấy mẫu: nhiều endpoint trùng điểm, trùng verb, trùng trạng thái userParam, nên hạng của
  endpoint `R` trong nhóm trùng do một tie-break chưa khai báo quyết định (`docs/lexicon.md` §7).
- `firstOrNull`, cách chọn trước jar `L`, chọn trúng một endpoint `R` trong **0 trên 6** spec test.
- L1–L2 kappa đo độ nhất quán của một nhà cung cấp, không đo tính đúng: viết điều đó thành một hạn chế.
- Bộ 56 từ viết tay trước bộ từ vựng (trong đó 8 từ path và 9 từ param chọn transition;
  `lexicon-rules/lexicon-20260920/RESULTS.md`) là của ta và tuỳ tiện: nó không phải baseline trong luận văn, và không có bảng nào so hai bộ. Nó ở lại như một
  phép kiểm khi phát triển và như chính điểm yếu mà chương này sửa.
- Thay bộ hardcode bằng lexicon rút được không làm mất phát hiện nào trên target của ta: jar `L` 0 trên 30 hàng ghép
  đôi (`docs/results.md` §5b); jar `TT` trùng jar `R` ở 80 cặp seed Tier-1/2 (`transitiontrim-chain-20260927c/RESULTS.md`).

**D1, phán quyết bằng hai credential.** Sau bộ ba, một test riêng đăng nhập nạn nhân mới tinh và gửi đúng lời gọi
follow-up. 970 cần source 2xx, transition 2xx, follow-up cũ 2xx, follow-up mới bị từ chối. Mỗi test đăng nhập một lần,
nên lời gọi bằng token cũ chạy trước. "Bị từ chối" theo §3 cho mọi method: 403 là từ chối, 2xx không phải, mã khác thì
ghi INCONCLUSIVE và không nổ gì (`infra/analysis/denial-codes-2026-09-17.md`). D1 lấy vị từ transition (bộ từ vựng trên
AF2, cổng Naive Bayes trên P2e) và phần replay lát cắt ra khỏi phán quyết.

**Target held-out.** Chỉ một app chưa hề bị đụng vào bởi một thay đổi mã mới là held-out. Airflow (từ 09-23), Grafana,
callcenter, truthy, bamf (từ 09-30 11:17) và artifact-keeper (từ 10-01) đều đã thành target phát triển, vì các bản sửa
builder được viết trong lúc chạy chính chúng. Diễn biến từng app: `infra/analysis/heldout-small-apps.md`,
`infra/analysis/cve-survey/`.
- Airflow với `AIRFLOW__FAB__CACHE_TTL=0` (lệch luật đã khai): hai bộ ba hợp lệ, follow-up 403, không có 970. Đây là
  **2 TN trên mã của bên thứ ba** (`em-results/airflow-ttl-20260927/RESULTS.md`).
- bamf trên jar `LP`: 0 bộ ba, builder không nhận `{email}` là tham số user. bamf không có lỗi theo hợp đồng của chính
  nó: vai trò của phiên là vai trò lúc đăng nhập (`infra/bamf-target/contract-20260930.md`).
- bamf trên jar `ER`: 5/10 seed nổ 970, trên một target đã thành target phát triển, với bảy lệch luật đã khai. Các lần
  nổ bắt đúng hành vi bamf ghi trong hợp đồng; xếp vào ô nào chưa quyết.
- Vikunja: 0 bộ ba trên mọi jar; điểm nghẽn là source không có nạn nhân.
- artifact-keeper (target phát triển cho nhận-diện cờ admin boolean của AF2): bản lỗi 5/5 tự nổ 970 (bộ ba
  `PATCH /api/v1/users/{id}` 200/200/200), bản vá 0 FP trên 3 lượt (`em-results/artifactkeeper-machine-20261001/`).

**Nhịp làm việc.** Một phiên tương tác làm việc; không có phiên chạy không người trông. Squad tắt từ 2026-09-17;
`infra/squad/` ở lại làm sổ chạy và kho đề bài. Mỗi lúc một việc nặng.
Batch rút gọn, chọn trước lượt chạy: không đổi cách dựng hay cách phán quyết thì chỉ chạy cổng; thay đổi nhỏ thì chạy
seeds 1–10 trên mọi arm và target; thay đổi lớn hoặc một arm mới thì chờ một lượt đầy đủ. Số của luận văn chỉ lấy từ bộ
đầy đủ.

**Còn mở.** `infra/analysis/cve-survey/coverage.md`, `docs/argument.md`, `docs/lexicon.md`.

**Tháng 10.** Cũ và D1 và D1 + lexicon trên cùng bộ seed, TP/TN/FP/FN theo tier; phát lệnh khôi phục của operator vào
test sinh ra (sửa replay Tier-1, seed 16 không reset); ablation theo từng thành phần; RESTler trong related work
(`docs/related-work.md` §4); một arm so sánh dùng LLM phân loại transition; dựng chủ động (D2). Đã xong: P1–P2e, duyệt
nhiều op và Naive Bayes thay bộ từ vựng cùng các danh sách viết tay (`docs/naive-bayes.md`, `infra/evomaster-ext/jars.md`).

**Hạn chế phải viết.** A2/A3 chưa chứng minh; mã từ chối chưa cấu hình được; path param chứa dấu chấm (email, tên miền)
không nhận được giá trị nạn nhân trong EvoMaster v6.1.1.

## 7. Tra ở đâu

| Cần | File |
|---|---|
| Định nghĩa oracle | `docs/metamorphic-authz-relations.md` |
| Số, soát tay, ablation, hạn chế, cách viết | `docs/results.md` |
| Luận điểm, bằng chứng, giới hạn từng luận điểm | `docs/argument.md` |
| Độ phủ CVE của oracle | `infra/analysis/cve-survey/coverage.md` |
| Kế hoạch đo tháng 10 (nháp) | `docs/plan-october.md` |
| Related work, tính mới, trích dẫn đã kiểm | `docs/related-work.md` |
| Thay đổi mã, điểm tích hợp, mã fault | `infra/evomaster-ext/README.md` |
| Sổ jar đầy đủ | `infra/evomaster-ext/jars.md` |
| Self-test cho mỗi thay đổi mã | `infra/evomaster-ext/selftest/` |
| Vướng safety classifier: triệu chứng, cách làm | `infra/evomaster-ext/safety-classifier-notes.md` |
| Mô hình Naive Bayes của P2e: cách tính, kiểm chéo, file mô hình | `docs/naive-bayes.md` |
| Bộ từ vựng của jar `L` tới `AF2`: luật, nhãn, ba lần rút, thứ hạng | `docs/lexicon.md`, `infra/analysis/lexicon-rules/` |
| Corpus gán nhãn: 36 spec WFD, danh sách apis.guru | `infra/analysis/corpus/` |
| Tìm app held-out, giao thức từng app | `infra/analysis/heldout-small-apps.md` |
| Khảo sát CVE: truy vấn, dữ liệu thô, ứng viên | `infra/analysis/cve-survey/` |
| Mã từ chối trên ba target | `infra/analysis/denial-codes-2026-09-17.md` |
| Thiết kế probe C4 re-login | `docs/design-relogin-probe.md` |
| Target Tier-1 | `infra/reports-api/README.md` |
| Target Tier-2 | `docs/tier2-seeded-benchmark-plan.md` §4 |
| Target Tier-2b và các lệch luật đã khai | `docs/tier2b-pyload-target.md` §3 |
| Airflow CVE-2026-82310: chỉ kiểm tay, chưa chạy máy | `infra/airflow-target/README.md` |
| Cách soát tay | `infra/em-results/audit-batch/AUDIT.md` |
| Sổ chạy và kho đề bài (squad tắt 09-17) | `infra/squad/SQUAD.md` |
| Dựng, jar, rollback, git | skill `evomaster-build` |
| Chạy EvoMaster, batch, soát, replay | skill `em-batch` |
| Cổng hồi quy | skill `regression-gate` |
| HTML sang PDF | skill `render-pdf` |
| Báo cáo tiến độ cho thầy | `docs/bao-cao-tien-do-2026-08-23.md`, `Bao_cao_tien_do_2026-08-23.pdf` |
| Đề cương | `Thesis_Proposal_EvoMaster.html`, `.pdf` |
| Kiểm ngữ cảnh | `infra/context-eval/questions.md`; file đã nạp: `.claude/logs/instructions-loaded.jsonl` |
| Quy trình viết | ARS plugin: `/ars-plan`, `/ars-outline`, `/ars-reviewer` |
