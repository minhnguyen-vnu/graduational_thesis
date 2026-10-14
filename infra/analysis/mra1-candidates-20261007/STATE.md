# STATE — phục hồi được. Phiên overnight MR-A1, bắt đầu 2026-10-07 22:26 +07

Luật đầy đủ: `README.md` cùng folder + `infra/analysis/heldout-small-apps.md` §1/§13/§17.

- **Hạn dừng**: giờ local ≥ 2026-10-08 12:00 (+07), HOẶC đủ 10 qualifier.
- **Heartbeat**: `2026-10-08 09:40 +07` — LIVE, user ngồi canh. Cron f4b7a399 + heartbeat cron bedc7700 ĐÃ XOÁ, ScheduleWakeup ĐÃ stop (user: "bỏ cron, sáng nay tôi canh được, cứ chạy"). KHÔNG đặt lại tự-động-hoá.
- **ĐÃ QUÉT dải 100–1500★** qua C#/Go/Java-Spring/NestJS/Laravel-PHP/Express/FastAPI (queries T/K/L/G/J). Kết: 2 qualifier (magic #38, hrm #41); còn lại DB/Redis-backed hoặc boilerplate/lib. Route hợp-đồng free-text (C1–C4) rơi đuôi <100★ (OHDSI/Data2Evidence 44★, orionpay 5★, ggid 0★). Category boilerplate/lib (L1–L4) năng suất thấp. Chờ user chọn hướng: dựng hrm/magic làm target thật, hay săn tiếp.
- **Qualifier**: **6 / 10** — #38 magic (1200★ C#), #41 hrm (464★ Spring Boot), #52 bcms (464★ TS CMS), #56 fastschema (575★ Go BaaS), #63 raouf ecommerce-store-api (55★ NestJS), #64 alvaromrveiga ecommerce-backend (72★ NestJS). Cả 6 Tier B. near-miss: 2 (#28, #30). VEIN NestJS dải nhỏ (RolesGuard đọc role từ token + endpoint @IsAdmin đổi role) đang cho quả đều.
- **Candidate đã xét**: 62 app + 2 ecosystem (live sweep dải 100–1500★: 4 qualifier, 20 loại). VEIN năng suất: API-first (BaaS/headless-CMS/low-code) + app cố ý bỏ DB-lookup (hrm). App self-hosted trưởng thành dùng session/DB-store → loại. Yield ~1 qualifier / 6 app đọc.
- **DỰNG + KIỂM TAY (2026-10-09, phiên tương tác)**: user giao dựng + kiểm tay cả 6 qualifier (chưa chạy EvoMaster). Tiến độ: **magic ✓** (`infra/magic-target/RESULTS.md`, token-cũ=202/token-mới=403/neg=403, HEAD aefa668). **fastschema ✓** (`infra/fastschema-target/RESULTS.md`, token mang role_ids, cũ=[Admin]→200/mới=[User]→403/neg=403, HEAD 8133499, named-volume). **raouf ✓** (`infra/raouf-target/RESULTS.md`, build từ source HEAD 08b0760, token mang role: cũ ADMIN→204/mới CUSTOMER→403/neg=403; npm ci + npm run setup + start:dev). **alvaro ✓** (`infra/alvaro-target/RESULTS.md`, build từ source HEAD dbd0cd1 trong node:18 do Node 25 gỡ util.isObject; token mang userRole: cũ ADMIN→200/mới USER→403/neg=403; bootstrap admin qua DB). **bcms ✓** (`infra/bcms-target/RESULTS.md`, build từ source HEAD d0e643d node:20; token mang rls: cũ ADMIN→200/mới USER→403/neg=403; bộ ba <1s trong token 60s). **hrm ✓ (2026-10-11)** (`infra/hrm-target/RESULTS.md`, build jar maven-JDK17 container chạy Java 21, HEAD 1ef6abc; middleware mysql×2+redis+pgvector+minio bitnamilegacy; .env JWT_SECRET base64). Login captcha từ Redis `validate:code`; reset bcrypt pwd admin→`Admin123!` (plaintext seed không rõ, không phải 123456); victim tạo mới `POST /staff` (pwd mặc định `123`) gán role 1 (có `permission:role:edit`) rồi admin hạ sang role 9; SOURCE `PUT /role`, TRANSITION `POST /staff/set/{id}`. token_cũ(role:edit) sau hạ=ALLOWED, token_mới=DENIED, neg=DENIED. **PHÁT HIỆN QUAN TRỌNG + sửa suy luận cũ**: denial mức `@PreAuthorize` trả **HTTP 200 + body code 1300**, KHÔNG phải 403 → oracle 970 nguyên trạng (DENIED=403) KHÔNG nổ trên hrm (đúng hạn chế §6 "mã từ chối chưa cấu hình được"); map tay ALLOWED=body code 200/DENIED=body code 1300. **Cả 6/6 qualifier đã dựng + kiểm tay xong.** Đã tháo hrm (jar+caffeinate killed, hrm-mysql/redis/postgres/minio rm -f, :8888 down) như 5 target trước.
- **ĐÃ QUÉT ~19 category** dải 100–1500★: rbac, jwt, self-hosted, spring, nestjs, laravel, express, fastapi, flask, helpdesk, ticketing, collaboration, forum, saas, multi-tenant, headless-cms, baas, low-code, internal-tool. App thật còn lại phần lớn framework/lib/scaffold/Chinese-Redis-admin/dưới-dải → xác suất thấp. Veins chính đã cạn.
- **Heartbeat**: `2026-10-08 11:20 +07` LIVE. Đang KIỂM CHỨNG 6 qualifier (user: "verify lại... có thực sự dính 970 ko, làm thật kỹ"). Tự-động-hoá vẫn tắt.
- **KIỂM CHỨNG LẦN 2 (2026-10-08 11:20)**: đọc lại file nguồn thật cả 6 qualifier qua raw, xét 4 điều kiện (C-JWT không-DB / transition hạ role user khác / user bị hạ vẫn login / không revoke token cũ). **Cả 6 đều nổ được 970 trong mã.** Bảng verdict + bằng chứng file:dòng ở FINDINGS.md §"Kiểm chứng mã nguồn lần 2". Cảnh báo: bcms token mặc định 60s (mong manh); hrm login captcha bắt buộc (cần lệch luật). Sửa 2 chỗ: raouf source=PATCH (không PUT); bcms thêm cảnh báo 60s.
- **Bottleneck tới 10**: dải nhỏ NestJS/Express hầu hết C-JWT nhưng THIẾU endpoint đổi role user khác (near-miss: vkondratiuk, Yancey-Blog, nestier). Qualifier cần CẢ C-JWT + endpoint đổi role → thiểu số (raouf/alvaro là ecommerce có role mgmt). Category user-management/rbac dải này loại-dominated (LDAP/AD, IdP/OAuth-server, Laravel-admin session, lib). Filter nhanh: probe tree tìm role dto/controller trước khi đọc sâu.
- **CHUYỂN CHIẾN THUẬT (2026-10-08 ~09:00, user chỉ đạo)**: bỏ cào đáy 5–54★ (ra toàn near-miss vì app nhỏ không có endpoint đổi role). Đổi S7′ → **ưu tiên 100–1500★ app self-hosted thật** (dải artifact-keeper 1097★ đã trúng). Tham chiếu chiến thuật thắng §13→§17 heldout: contract-reverse + lọc C-JWT; app thật > throwaway. Lượt đầu theo dải mới ra magic ngay.
- **Tick cuối**: tick-9 (route hợp-đồng + GHSA). h1/h2 issue 0 hit; h3 commit noise; GHSA CWE-613/863 toàn lib phổ biến (Backstage/Ghost >2000). Route hợp-đồng & advisory CẠN cho in-band. Việc kế: đổi ecosystem/category — §Góc mới tick-9.
- **BÀI HỌC tick-4**: issue mô tả C-JWT đẹp (gittensor#1420) nhưng CODE KHÔNG TỒN TẠI trong repo (AI-slop). Luôn verify tree+code thật trước khi ghi qualifier. Nhiều repo active 0★ hình dạng C-JWT ở commit fix (NaderZico, algenri, lkindo) nhưng dưới sàn 5.

## Cách resume (đọc khi re-enter sau quota/wakeup/cron)

1. `date` xem đã tới hạn chưa; đếm qualifier trong `FINDINGS.md`. Thỏa luật dừng → ScheduleWakeup `stop:true`, xoá cron, tổng kết.
2. Chưa thỏa → cập nhật heartbeat ở trên. Lấy candidate đang dở (nếu có) hoặc query pending kế tiếp trong §Hàng đợi.
3. Hand-check CHI TIẾT 1–2 candidate: ưu tiên sao thấp (10≤sao<2000). Chỉ đọc qua `curl` GitHub API + WebFetch
   github.com/raw; KHÔNG dựng, KHÔNG chạy.
4. Dedup TRƯỚC khi xét: `grep -ri <repo> infra/analysis/heldout-small-apps.md infra/analysis/mra1-candidates-20261007/STATE.md`
   — có rồi thì bỏ qua.
5. Ghi MỌI candidate đã xét vào §Nhật ký (kể cả loại, nêu luật trượt đầu). Chỉ qualifier → `FINDINGS.md`.
6. ScheduleWakeup tick kế (delay ~120s) với cùng prompt loop. Lệch luật → ghi vào §Lệch luật rồi tìm nguyên nhân.

## Loại trùng

Mọi repo xuất hiện trong `infra/analysis/heldout-small-apps.md` (đã xét ở các phiên trước) + mọi target trong
`CLAUDE.md`: pyLoad, Airflow, Vikunja, ZITADEL, NocoDB, FUXA, Grafana, Mattermost, VAmPI, reports-api, wagoe,
artifact-keeper, bamf, orkestra, truthy, callcenter/ai-native-callcenter, tibba, và toàn bộ bảng §3/§13/§15 trong
heldout doc. Kiểm bằng grep ở bước 4.

## Hàng đợi truy vấn (GitHub API, unauth, trang đầu 30, thứ tự API trả)

Hướng chính §13: tìm ngược từ hợp đồng (commit/PR/issue vendor nhận lỗi). `search/commits` và `search/issues`.
Đánh dấu: [ ] pending, [x] done. Query cũ §13 (q16–q25) đã chạy phiên trước — KHÔNG lặp; đây là biến thể mới.

search/commits:
- [x] cA `demoted admin still has access` — 31168 hit, free-text nhiễu; không ra candidate MR-A1 rõ trong 30 đầu.
- [ ] cB `role change does not revoke session`
- [x] cC `jwt claims role not rechecked database` + iX `jwt not revalidated after role change` (0 hit) + iY `admin access after demotion` (2 hit: gittensor#1420 phantom, algenri#77 0★) — ra gittensor/NaderZico/algenri/lkindo, đều loại (#18–21).
- [ ] cD `stale permissions after role update`
- [ ] cE `recheck role from database authorization`
- [ ] cF `invalidate token when role changed`
- [ ] cG `downgraded user retains privileges`
- [ ] cH `authorization cached role stale`

search/issues (in:title, is:closed ưu tiên có fix):
- [x] iA `demoted admin still admin in:title` — 1 hit: chronograf#2505 (xét, loại S10).
- [x] iB `role change not reflected in:title` — 12 hit; MR-A1-shaped đều ngoài sao (lessondeck 0★, agri-fi 1★, RestyaPlatform 2089★).
- [x] iC `old token keeps permissions in:title` — 0 hit.
- [x] iD `permissions not revoked in:title` — 19 hit; lọc sao: chỉ chronograf trong khoảng (loại S10); còn lại >2000 hoặc <10 hoặc lib/archived.
- [x] iE `jwt old role in:title` — 8 hit; rentaxis 0★ (shape khớp), django-ansible-base dedup, còn lại lib/naming.
- [ ] iF `removing role has no effect in:title`
- [x] iG `keeps access after demotion in:title` — 0 hit.

Nếu cạn: thêm biến thể "scope", "group membership", "tenant role", "RBAC", `linked:pr is:closed`, ngôn ngữ khác (java/go/python/php/ruby).
Thêm precision: `... in:title is:issue is:closed linked:pr` (kiểu artifact-keeper#1821).

## CẬP NHẬT LUẬT (user, 22:47): sàn sao 10 → 5

S7′ giờ = `5 ≤ sao < 2000`, chỉ cho app ACTIVE thật. Áp từ tick-3.
- Vẫn RỚT sàn 5: lessondeck 0★, rentaxis 0★, agri-fi 1★, perx 3★, hms-dbmi/hypatio 4★ (các app hình-dạng-khớp nằm ở
  đây — nếu user muốn vớt phải cho ngoại lệ từng ca, CHƯA làm).
- VÀO khoảng nhờ nới: ToogaBooga 8★ (nhưng bot game Discord, nghi S3/S5 — xét khi tới lượt).
- Tier B: user CHƯA phản đối (tôi đã nói opt-out) → vẫn ghi Tier B, nhãn rõ.

## Quyết định tự chủ (tick-2, 22:42) — cần user soát sáng mai

Vấn đề yield quan sát được sau 13 candidate: issue/commit MR-A1 **đã xác nhận** tập trung ở repo **0–8★** (dưới sàn 10)
hoặc **>2000★**. Khoảng 10–2000 thưa (khớp kinh nghiệm §13–§17: 2 qualifier/~200 repo). Giữ nguyên S10 + sàn 10 thì
tới trưa mai gần như chắc < 10 qualifier.

Hai cần hỏi user (KHÔNG tự đổi, chỉ đề xuất):
- **(a) Nới sàn sao** xuống <10 cho app ACTIVE thật (vd lessondeck SEC-006, rentaxis — 0★ nhưng hình dạng C-JWT khớp)?
- **(b) Chấp nhận Tier B** = candidate suy từ ĐỌC CODE (authz đọc claim không tra DB), KHÔNG cần hợp đồng vendor? User
  tối nay nói "app có khả năng dính lỗi" → rộng hơn S10. Nếu OK, yield tăng nhiều.

Trong lúc chờ: loop vẫn chạy Mode A (S10, in-band 10–2000) là chính; THÊM discovery in-band để không phí tick:
- search/repositories `stars:10..2000` + topic (rbac/self-hosted/jwt/admin) → app in-band, rồi đọc issue/commit tìm hợp đồng.
- Candidate in-band mà code khớp C-JWT/C-SRC/C-STEP nhưng CHƯA có hợp đồng → ghi FINDINGS **Tier B** (nhãn rõ "chưa
  có hợp đồng, chỉ suy từ code"), tách khỏi Tier A. Bảng tổng hợp đánh dấu cột Tier.

search/repositories (in-band, ưu tiên sao thấp):
- [x] rA `topic:rbac stars:10..800 pushed:>2025-01-01` — 335 hit; shortlist bên dưới.
- [ ] rB `topic:jwt topic:admin stars:10..800`
- [x] rC `fastapi rbac stars:10..800` — 34 hit; shortlist bên dưới.
- [ ] rD `nestjs rbac jwt stars:10..800`
- [ ] rE `spring boot jwt role admin stars:10..800`
- [ ] rF `self-hosted api rbac stars:10..1500 pushed:>2025-06-01`

search/code (antipattern C-JWT, nếu còn hạn mức): `is_admin claims jwt`, `role from token not database`.

### Shortlist in-band để hand-check CODE (rA 335 hit, rC 34 hit; sắp xếp sao tăng; đọc authz để phân C-JWT)
Bỏ: lib/engine (rbac-engine, rbacx, permit SDK, casbin skeleton), frontend-only (asf-react, NexusStackPro), archived
(openfga-laravel, MiniAdmin, bosichong). App thật cần đọc authz dependency/guard:
- [x] lijianqiao/fastapi-admin-v2 (10★) — LOẠI: authz tra DB+Redis (version-bumped), không C-JWT. Xem nhật ký #14.
- [x] gabrielmaialva33/innkeeper (10★) — LOẠI DB-backed (#15).
- [x] rebort-hub/fastapiReactadmin (12★) — LOẠI DB-backed (#16).
- [x] Shankar-105/finance-system-backend (11★) — LOẠI role không trong token (#17).
- [x] salmanx/rails_iam (10★) — LOẠI S2 engine/gem (#22).
- [x] moeinrezai/FastAPI-Authentication (15★) — LOẠI session-based (#24); tenxyte (42★) — LOẠI S2 package (#23).

### §Pivot tick-5 (00:08): shortlist in-band cạn, hết đều DB-backed
Quan sát: 24 candidate, 0 qualifier. App in-band Python admin/auth đều tra DB/cache (không C-JWT). C-JWT thật dồn vào
repo 0★ hoặc issue giả. ĐỔI stack discovery sang nơi hay bake role vào JWT: NestJS (`@Roles`+RolesGuard đọc
`user.roles` từ payload), Express (`req.user.role` từ jwt decode), Go (jwt claims). Query kế (search/repositories, sort
stars asc, 5..1500):
- [x] pA `topic:nestjs topic:jwt stars:5..1500` — 125 hit; caps-pizza (S6), nestjs-auth (DB), đa phần boilerplate.
- [ ] pB `express jwt role middleware admin stars:5..1500` — 2 hit, chất lượng thấp.
- [x] pC `gin jwt rbac admin stars:5..1500` (Go) — 8 hit; đều Casbin DB-policy (gin-casbin-admin xác nhận DB); lakego/go-admin dedup.
- [ ] pD `topic:nestjs topic:authorization stars:5..1500`
Với mỗi app: đọc guard/middleware thật — RolesGuard/JwtStrategy.validate trả payload (C-JWT) hay tra DB (loại). VERIFY
code tồn tại (bài học gittensor). Nếu C-JWT + có admin-write idempotent + transition không step-up → Tier B.

### §Pivot tick-6 (00:41): phát hiện mẫu — cần user soát
**27 candidate, 0 qualifier.** Mẫu RẤT chắc: mọi app in-band 5–2000★ (NestJS/Go-Casbin/FastAPI/Rails/Adonis) đều
re-resolve role/quyền từ DB mỗi request (JwtStrategy.validate→findById, Casbin→GetUserRoles DB, dep→DB). C-JWT (role
nằm trong token, tin không tra DB) chỉ thấy ở repo 0★ (NaderZico, lessondeck, rentaxis) hoặc issue giả (gittensor).
→ **Đây là phát hiện có giá trị cho luận văn**: MR-A1/C-JWT là lớp lỗi HIẾM ở app duy trì tốt — củng cố vì sao target
xác nhận ít (pyLoad, artifact-keeper, wagoe). Nhưng nó làm mục tiêu "10 app in-band" gần như bất khả.
Hướng còn thử (ecosystem hay nhét role vào claim): **Flask-JWT-Extended** (`additional_claims` role, `get_jwt()["role"]`
không tra DB), **Django SimpleJWT custom claims**, **PHP firebase/php-jwt tự check claim**. Query kế:
- [x] pE/pG/pH `...language:...` — 0 hit (query quá chặt). pE2 `flask jwt admin stars:5..1500` = 8 hit → placement-portal (near-miss #28), cafe-connect (#29 loại), còn lại lib/frontend/spam.
- [x] pF `topic:flask-jwt-extended stars:3..1500` — 19 hit, toàn tutorial API nhỏ; pairs-api (near-miss #30).
- [x] pD `topic:nestjs topic:authorization stars:5..1500` — 33 hit; ringslist(#31), e-commerce(#32) loại; nhiều demo/provider.
- [x] pI `flask rbac stars:8..1500` — 3 hit (template/game), bỏ.
NẾU tới ~tick-9 vẫn 0 qualifier: cân nhắc đề xuất user (sáng) chọn — (i) nhận app 0★ shape-khớp làm Tier C, hay (ii)
chốt output = danh sách near-miss + phát hiện "C-JWT hiếm".

### §Near-miss (gom để user soát sáng — KHÔNG phải qualifier)
C-JWT xác nhận qua đọc code, nhưng thiếu một mảnh của MR-A1:
- **#28 placement-portal (10★, in-band, Flask)** — C-JWT ✓ + admin-write idempotent ✓, nhưng KHÔNG có transition hạ-role
  (chỉ vô hiệu/xoá = lớp loại). Gần nhất; nếu thêm 1 endpoint đổi role thì đủ. App active, buildable.
- **#19 NaderZico/ai-appointment-scheduler (0★)** — commit "token carries only user id" = fix bỏ role khỏi token → bản cha C-JWT. Dưới sàn.
- **#8 lessondeck (0★), #9 rentaxis (0★)** — issue tự mô tả C-JWT (stale JWT role / never re-validate). Dưới sàn.
Phát hiện tick-7: C-JWT CÓ tồn tại in-band (placement-portal) nhưng full-MR-A1 (C-JWT + transition hạ-role-vẫn-login-được)
hiếm hơn nữa.

## §Đề xuất tick-8 (01:38) — cho user soát sáng mai

Sau 33 candidate / 0 qualifier / 2 near-miss, kết luận vững:
1. **MR-A1 đầy đủ = giao điểm ba điều kiện hiếm cùng xảy ra**: (C-JWT: role trong token, không tra DB) × (có endpoint
   admin đổi role user khác qua REST) × (account bị hạ vẫn login lại được — không phải vô hiệu/xoá). App in-band 5–2000★
   thường chỉ có 1–2 trong 3: admin-dashboard thì tra DB; app C-JWT nhỏ (placement-portal, pairs-api) thì KHÔNG cho đổi
   role qua API. Đây là lý do pyLoad/artifact-keeper/wagoe quý — chúng rơi đúng giao điểm.
2. **Hệ quả cho phương pháp tìm**: route code-shape (search/repositories) cho ra near-miss (C-JWT thiếu transition).
   Route HỢP-ĐỒNG (issue/PR ai đó đã gặp+sửa đúng lỗi này) nhắm THẲNG vào giao điểm — vì bug chỉ lộ khi đủ cả ba. Đây
   mới là đường ra qualifier Tier A. Từ tick-9: ưu tiên lại issue/PR contract, lọc in-band.
3. **Lựa chọn cho user** (nếu tới trưa vẫn <10 qualifier — nhiều khả năng):
   - (i) **Nhận Tier C** = app 0★ shape-khớp (lessondeck, rentaxis, NaderZico) — nới sàn cho vài ca cụ thể.
   - (ii) **Chốt output** = (a) danh sách near-miss in-band (placement-portal, pairs-api: C-JWT thật, chỉ thiếu
     endpoint đổi role) + (b) phát hiện "full-MR-A1 hiếm ở app duy trì tốt" — bản thân đây là kết quả khảo sát có giá trị
     cho chương đánh giá (giải thích vì sao target xác nhận ít).
   - (iii) **Giữ nguyên** luật, chấp nhận qualifier ít.
Tôi KHÔNG tự chốt; loop tiếp tục chạy route hợp-đồng cho tới trưa hoặc tới 10 qualifier.

### Queue route hợp-đồng (issue/PR, in:title, lọc in-band 5–2000★)
- [ ] hqA `role change requires re-login in:title`
- [ ] hqB `jwt contains role stale in:title`
- [ ] hqC `is_admin in token not checked in:title`
- [ ] hqD `refetch user role after update in:title`  (fix PR)
- [ ] hqE `demote user still has permission in:title`
- [x] hqC/hqE issue (`is_admin in token not rechecked`, `demoted user still has permission`) — 0 hit.
- [x] hqF commit free-text — 8536 noise, bỏ.
- [x] GHSA CWE-613/CWE-863 (40 adv) — toàn lib phổ biến (Backstage/Ghost/npm), không app in-band standalone stale-authz.

### §Góc mới tick-9 (02:05): đổi ecosystem/category để MỞ RỘNG KHẢO SÁT (không lặp góc đã cạn)
Mục tiêu đôi: (a) may ra gặp giao điểm hiếm; (b) mỗi ecosystem loại được = củng cố "MR-A1 hiếm". Mỗi tick 1 góc:
- [ ] gA Rails devise-jwt: `topic:ruby topic:jwt stars:10..1500` + đọc app có admin role mgmt (role trong JWT? devise-jwt thường revoke DB → nghi loại).
- [ ] gB Laravel: `laravel sanctum role admin stars:20..1500 language:php` (Sanctum token DB → nghi loại; tymon/jwt role-in-token → may C-JWT).
- [ ] gC Self-hosted category: `topic:helpdesk self-hosted stars:50..1500`, `topic:crm self-hosted stars:50..1500` — app có user/role mgmt thật.
- [x] gD Go: `topic:gin topic:jwt` 65 hit = toàn boilerplate/tutorial/casbin; GopherCRM (gC2) đại diện Go → DB.
- [x] gE multi-tenant — rcrdk #34 (DB).
- [x] gC self-hosted helpdesk/CRM — GopherCRM #35 (DB), douban/helpdesk #36 (OIDC), paw #37 (Django DB).
- [x] gA Rails — devise-jwt README: Warden DB + revocation DB → không C-JWT. Search ra toàn gem/starter.
- [x] gB Laravel — chỉ ra package laravel-jwtredis; khung tymon/Sanctum retrieveById DB → không C-JWT.
ĐÃ LÀM: deliverable hợp nhất viết vào FINDINGS.md (tick-12). Loop → noop-heartbeat 3600s tới 12:00.
Ghi kết quả từng ecosystem (ngay cả khi loại cả cụm) để làm bảng khảo sát.
Mỗi cái: nếu authz đọc role/quyền từ JWT claim KHÔNG tra DB → Tier B candidate (ghi rõ chưa có hợp đồng). Nếu tra
DB/cache mỗi request → loại (fix sẽ là flush cache, không nổ 970).

## Nhật ký candidate đã xét

| # | repo | sao | nguồn (query/commit/issue) | verdict | luật trượt đầu / lý do |
|---|---|---|---|---|---|
| 1 | influxdata/chronograf | 1566 | iA/iD #2505 | LOẠI | S10: issue stale, reporter "super minor", không maintainer xác nhận, không fix PR/commit; "get logged out" nghiêng về có vô hiệu phiên. Auth OAuth (nghi S5). |
| 2 | bonrow/perx | 3 | iD #1 | LOẠI | S7′ dưới sàn 10 sao; cũng là permission-gateway (nghi S2 lib). |
| 3 | hms-dbmi/hypatio-app | 4 | iD #568 PR | LOẠI | S7′ dưới sàn 10 sao. GHI CHÚ: app thật (Harvard DBMI), active (push 2026-10-05), có fix PR "participant permissions not revoked" — ứng viên để user cân nhắc nới sàn. |
| 4 | amiv-eth/amivapi | 33 | iD #267 | LOẠI | archived=True; issue là "không revoke được nếu không reset toàn bộ" (sai hình dạng, không phải token cũ giữ quyền). |
| 5 | craftcms/cms | 3611 | iD #12756 | LOẠI | S7′ >2000. |
| 6 | Flagsmith/flagsmith | 6590 | iD #5432+#5438 | LOẠI | S7′ >2000. (Hình dạng tốt: "permissions not revoked when View Project disabled" + fix PR — nếu sau này nới trần thì xét lại.) |
| 7 | usekaneo/kaneo | 9379 | cA #1952 | LOẠI | S7′ >2000. |
| 8 | DevLifeCrisis/lessondeck | 0 | iB #20 | LOẠI | S7′ dưới sàn 10. GHI CHÚ hình dạng rất khớp: "[SEC-006] HIGH: Stale JWT session — role/subscription change" (C-JWT). Repo cá nhân 0★. |
| 9 | kunal-ak23/rentaxis | 0 | iE #216 | LOẠI | S7′ dưới sàn 10. GHI CHÚ: "NextAuth JWT session never re-validates against backend" (C-JWT) — khớp, nhưng 0★ cá nhân, active. |
| 10 | Agri-fund/agri-fi | 1 | iB #170 | LOẠI | S7′ dưới sàn 10; issue là client không refresh (sai lớp, authz phía client). |
| 11 | RestyaPlatform/board | 2089 | iB #841 | LOẠI | S7′ ≥2000 (sát trần). App thật (kanban kiểu Trello, có API). Near-miss trần. |
| 12 | ToogaInc/ToogaBooga | 8 | iB #31 | LOẠI | S7′ dưới sàn 10; Discord bot game (nghi S3/S5). |
| 13 | SmartDude04/color-wars-website | 0 | iB #13 | LOẠI | S7′ dưới sàn 10; website game cá nhân. |
| — | ansible/django-ansible-base | — | iE #1082 | LOẠI | dedup: đã có trong heldout-small-apps.md. |
| 14 | lijianqiao/fastapi-admin-v2 | 10 | rA (in-band, hand-check code) | LOẠI | KHÔNG C-JWT: authz tra DB + cache Redis (`core/permissions.py`: `_load_user_permissions_from_db` qua user_role/role_perm/perm DAO; cache key `rbac:perm:v{version}:u:{user_id}` TTL 1800s; `bump_perm_version()` xoá cache khi đổi quyền). JWT chỉ mang user_id. Lớp ZITADEL/DB-session → token cũ re-resolve quyền mới → không nổ 970. |
| 15 | gabrielmaialva33/innkeeper | 10 | rA (hand-check code) | LOẠI | KHÔNG C-JWT: `app/middleware/acl_middleware.ts` `user.load(roles)` từ DB, check `user.roles.some(slug)` theo DB state mỗi request. |
| 16 | rebort-hub/fastapiReactadmin | 12 | rA (hand-check code) | LOẠI | KHÔNG C-JWT: `backend/app/core/permission.py` đọc `auth.user.roles` (object DB) + query DeptModel DB mỗi request dựng cây phòng ban. |
| 17 | Shankar-105/finance-system-backend | 11 | rC (hand-check code) | LOẠI | KHÔNG C-JWT: JWT payload chỉ `sub/exp/typ/jti` (`app/oauth2.py`), role KHÔNG trong token → resolve từ DB theo sub mỗi request. |
| 18 | entrius/gittensor | 49 | iY #1420 | LOẠI | PHANTOM: issue #1420 mô tả C-JWT đẹp (guard đọc `session.is_admin` từ JWT cookie, DB sau guard) NHƯNG repo là Bittensor subnet Python thuần (~36 nhánh emission/validator/compute), KHÔNG có file web/admin/middleware/JWT-cookie nào. Code mô tả không tồn tại; issue closed-not-planned, không maintainer → AI-slop. Verify tree phủ nhận. |
| 19 | NaderZico/ai-appointment-scheduler | 0 | cC commit | LOẠI | S7′ dưới sàn 5. GHI CHÚ: commit "token carries only the user id" = FIX bỏ role khỏi token → bản cha có thể C-JWT. 0★. |
| 20 | algenri-organization/algenri-web | 0 | iY #77 PR | LOẠI | S7′ dưới sàn 5. GHI CHÚ: PR "clear module access after admin demotion" đúng lớp. 0★ site cá nhân. |
| 21 | lkindo/sr | 0 | cC commit | LOẠI | S7′ dưới sàn 5; "revalidate session claims so deactivation takes effect" — deactivation (lớp bị loại). 0★. |
| 22 | salmanx/rails_iam | 10 | rA (hand-check tree) | LOẠI | S2: là Rails ENGINE/gem (mountable, namespaced `app/.../rails_iam/`), không phải app chạy độc lập. Cũng DB-driven (role/permission models + jwt_decoder). |
| 23 | tenxyte/tenxyte | 42 | rA (hand-check tree) | LOẠI | S2: là package Python (`src/tenxyte/`, Django adapter, agent-token infra), library embed vào app khác, không phải target app. |
| 24 | moeinrezai/FastAPI-Authentication | 15 | rC (hand-check code) | LOẠI | KHÔNG C-JWT (độ tin TB): `core/permissions.py` chỉ ma trận ROLE_PERMISSIONS tĩnh; kiến trúc session store revocable (`models/session.py`, `session_service`, endpoint sessions) → lớp session/DB. Chưa đọc dependency cuối. |
| 25 | radqut/caps-pizza | 5 | pA (hand-check code) | LOẠI | S6: `jwt.strategy.ts` validate trả `{uuid}`, token chỉ định danh, KHÔNG role/permission, không RBAC đa vai. |
| 26 | ryanf10/nestjs-auth | 5 | pA (hand-check code) | LOẠI | KHÔNG C-JWT: `jwt.strategy.ts` validate `userService.findOneById(payload.id)` → tra DB, role tươi; RolesGuard đọc `request.user.roles` (user DB đó). Token chỉ `id`. |
| 27 | wxlbd/gin-casbin-admin | 8 | pC (hand-check code) | LOẠI | KHÔNG C-JWT: `middleware/casbin.go` lấy `user_id` từ JWT rồi `GetUserRoles(userID)` tra DB, Enforce theo role DB. Casbin DB-policy. |
| 28 | VIJAYAPANDIANT/placement-portal-application | 10 | pE2 (hand-check code) | **NEAR-MISS** | **C-JWT ✓** (`utils/decorators.py`: `claims=get_jwt(); claims.get('role')!=role → 403`, KHÔNG tra DB; login nhét `role` vào `additional_claims`). **C-SRC ✓** (admin-write idempotent: `PUT /companies/{id}/approve`, `/students/{id}/blacklist` toggle, guard `@role_required('admin')`). **THIẾU transition** (S6): không endpoint hạ role user khác; chỉ approve/deactivate/blacklist/delete = lớp vô hiệu/xoá (§3 LOẠI, re-login hỏng → D1 không có chứng chỉ mới). Nếu có endpoint đổi role → sẽ là qualifier. (S3 spec cũng chưa kiểm — Flask student, nghi không có OpenAPI.) |
| 29 | ser-arthur/cafe-connect-web-platform | 5 | pE2 (hand-check tree) | LOẠI | 17 file, không có file auth/role/RBAC → nghi S3/S6 (không hệ phân quyền). |
| 30 | ozdemirozcelik/pairs-api | 14 | pF (hand-check code) | **NEAR-MISS** | **C-JWT ✓** (`resources/users.py`: `claims=get_jwt(); if not claims["is_admin"]`→401, không tra DB; dùng ở UserRegister/UserList/User). Admin-write có (DELETE `/users/<username>`). **THIẾU transition**: không endpoint đổi `is_admin` (user tạo bằng password, không cơ chế đổi role). Cùng khuôn #28. |
| 31 | israelias/ringslist | 11 | pD/pI (hand-check code) | LOẠI | S6: không role/admin, chỉ user CRUD, authz còn không enforce trên endpoint. |
| 32 | amrmuhamedd/e-commerce-nestjs | 7 | pD (triage tree) | LOẠI (nhẹ) | Commit cả `dist/`; chỉ thấy `jwtauth.guard` (auth), không roles.guard trong tree → nghi không RBAC role-change. Chưa đọc sâu (deprioritized). |
| 33 | mhshahzad/order-pizza-api | 9 | pF (triage tree) | LOẠI (nhẹ) | 15 file, 1 `auth.py`; app nhỏ, nghi không endpoint đổi role (S6). Chưa đọc sâu (deprioritized). |
| 34 | rcrdk/nextjs-fastify-saas-rbac | 54 | gE (hand-check code) | LOẠI | KHÔNG C-JWT: `middlewares/auth.ts` JWT chỉ `sub`; `getCurrentUserMembership` = `prisma.member.findFirst` tra DB mỗi request. Đại diện multi-tenant SaaS (Rocketseat pattern). |
| 35 | florinel-chis/GopherCRM | 23 | gC2 (hand-check code) | LOẠI | KHÔNG C-JWT: JWT CÓ role claim nhưng `service/auth_service.go ValidateToken` BỎ QUA, `userRepo.GetByID` tra DB lấy role authoritative. Thiết kế chống stale đúng. |
| 36 | douban/helpdesk | 22 | gC1 (hand-check code) | LOẠI | S5/S6: auth OIDC external IdP (`libs/auth.py` role từ `resource_access` token Keycloak, lưu session, quản lý role ở IdP không phải REST app). Lớp external-IdP (như Airflow-FAB). |
| 37 | aottr/paw | 21 | gC1 (triage) | LOẠI (nhẹ) | Django ticket system; Django SimpleJWT/session load user từ DB mỗi request → nghi không C-JWT. Chưa đọc sâu (ecosystem Django DB-backed). |
| 38 | polterguy/magic | 1200 | T-band (100-1500★, hand-check code) | **QUALIFIER (Tier B)** | **C-JWT ✓✓**: `TicketFactory.cs CreateTicket` nhét role vào `ClaimTypes.Role`; `VerifyTicket`→`HttpTicketProvider.InRole`=`HttpContext.User.IsInRole` đọc claim, KHÔNG tra DB. Token mặc định `ValidMinutes`/5y, không denylist. **Transition**: `DELETE /magic/users_roles {role,user}` guard root. **C-SRC**: `PUT /magic/roles` idempotent guard root. **403-on-deny** đúng oracle. S2 docker-compose, S3 openapi.get.hl tự serve. Mở: S4 đếm op, S9 xác nhận khi dựng. Chi tiết+chạy tay A–F: FINDINGS.md Qualifier 1. |
| 39 | qingwave/weave | 604 | T-band (hand-check) | LOẠI | DB-backed: `middleware/authentication.go` GetUserByID; `authorization.go Authorize()` GetUserByID + đọc Roles/group từ DB mỗi request. |
| 40 | tx7do/go-wind-admin | 569 | T-band (triage tree) | LOẠI (nhẹ) | go-kratos gRPC/HTTP gen; permission-service + permission_audit_log + MFA/login_policy → authz server-side + step-up + S4>200. Không C-JWT (kiến trúc). |
| 41 | quuuuj/hrm | 464 | K1 (hand-check code) | **QUALIFIER (Tier B)** | **C-JWT ✓✓**: `JwtAuthenticationFilter` dựng authority từ claim `permissions` (code tự ghi chú bỏ `loadUserByUsername` tra DB). `@PreAuthorize("hasAnyAuthority(...)")` gác theo claim. STATELESS. **Transition**: `POST /staff/set/{id}` roleIds guard `system:staff:set_role` → `StaffRoleService.setRole`. **C-SRC**: `PUT /role` guard `permission:role:edit`. 403-on-deny (accessDeniedHandler). Token 15'. S3 springdoc. Mở: captcha S5, S4 op. Chi tiết+A–F: FINDINGS.md Qualifier 2. Spring Boot — hợp luận văn. |
| 42 | Mininglamp-OSS/octo-server | 1064 | T-band (triage tree) | LOẠI (nhẹ) | `internal/carddispatch/authorizer_db.go` DB-backed; 3599 file (messaging/bot platform), S4>>200, external dep. |
| 43 | Genc/spring-boot-boilerplate | 385 | K1 (hand-check code) | LOẠI | 2 lý do: (1) `JwtAuthenticationFilter` gọi `userDetailsService.loadUserByUsername` → authority từ DB, không C-JWT (dù token có claim `role`); (2) chỉ Hello/Login/Registration controller, KHÔNG endpoint đổi role (S6), role enum cố định lúc đăng ký. Khuôn boilerplate điển hình. |
| 44 | kuangshp/nestjs-mysql-api | 903 | K3 (hand-check code) | LOẠI | 2 lý do: `guard/auth.guard.ts` tra `redisService.get(token)` → token là khoá session Redis, `request.user` từ Redis (revoke được) → session-store không C-JWT; auth-fail trả `HttpStatus.OK`(200)+code body → trượt S8. |
| 45 | deatil/larke-admin | 322 | P-band Laravel (hand-check) | LOẠI | DB-backed: `src/Auth/Admin.php hasAccess`→`AuthPermission::enforce(id,...)`; `getRules()`→`AdminRepository::getRules(groupids)` tra DB theo group mỗi lần. JWT mang admin id. |
| 46 | markrai/scrumboy | 444 | P-band Go (hand-check) | LOẠI | Session-store: cookie `scrumboy_session`=token server-side; `store/authctx.go` mang user id, quyền từ `store/permissions.go`/`system_roles.go` theo id mỗi request; 2FA (C-STEP); 618 file (S4). Không C-JWT. |
| 47 | Nine-Minds/alga-psa | 145 | P-band TS (triage tree) | LOẠI (nhẹ) | PSA doanh nghiệp, 10250 file; `packages/authorization/.../rbac.ts` + API-key + authorization kernel DB-backed; S4 khổng lồ. |
| 48 | byceps/byceps | 114 | P-band Flask (triage tree) | LOẠI | `services/authz/authz_service.py`+`dbmodels.py` → authz service DB-backed; Flask session. 1253 file. Không C-JWT. |
| 49 | ivangfr/springboot-react-jwt-token | 188 | K1 (hand-check code) | LOẠI | 2 lý do: `TokenAuthenticationFilter` gọi `userDetailsService.loadUserByUsername` → authority DB; UserController chỉ /me/GET/DELETE, KHÔNG endpoint đổi role (S6). Sample Spring, cùng bẫy Genc. |
| 50 | hequan2017/go-admin | 422 | G5 (hand-check code) | LOẠI | 2 lý do: `middleware/permission` dùng Casbin `Enforcer.EnforceSafe(username,path,method)` → policy DB, JWT chỉ username → không C-JWT; deny trả HTTP 401 mọi lỗi (code trong body) → trượt S8. |
| 51 | KevinLiss/ApeAdmin | 1156 | Q2 FastAPI (hand-check code) | LOẠI | `core/security.py create_access_token`: token chỉ `sub`+exp+type, role/perm KHÔNG trong token → resolve DB mỗi request. Không C-JWT (lớp FastAPI-admin như #14/#16). |
| 52 | bcms/cms | 464 | R4 headless-CMS (hand-check code) | **QUALIFIER (Tier B)** | **C-JWT ✓✓**: payload `rls:Roles` (role trong token); `JWTManager.get` (manager.ts:154) `jwt.payload.rls.find(...)` kiểm claim, không DB; sai → Forbidden 403. **Transition+C-SRC**: `PUT /api/v4/user/update {_id,role}` guard `['ADMIN']` → `user.roles[0].name=body.role` (hạ role user khác, chặn tự-đổi). PUT idempotent. OpenAPI (khối openApi). Chi tiết+A–F: FINDINGS Qualifier 3. |
| 53 | Southclaws/storyden | 340 | R1 forum Go (hand-check code) | LOẠI | `role_assign/resolve.go ResolveRoleIDs`: role resolve từ cache + DB fallback (`db.AccountRoles.Query()`) theo accountID mỗi request, không từ token. Không C-JWT. |
| 54 | usemarble/marble | 384 | R4 CMS TS (hand-check code) | LOẠI | API `middleware/authorization.ts`: workspace-id read-only + API-key cho write (S5 API-key); CMS app better-auth session. Không JWT-role-demotion. |
| 55 | leancodebox/GooseForum | 144 | R1 forum Go (hand-check code) | LOẠI | `checkPermission.go`: `resolveRoleId(c)` từ session-store (`sessionAuth`/`sessionstore.go`) rồi `permission.CheckRole(roleId)` → role từ session/DB, không claim. Session-based. |
| 56 | fastschema/fastschema | 575 | S3 BaaS Go (hand-check code) | **QUALIFIER (Tier B)** | **C-JWT ✓✓**: `fs/jwt.go UserJwtClaims{User}` (user+RoleIDs trong token); `services/auth/middlewares.go ParseUser` `user.Roles=GetRolesFromIDs(user.RoleIDs)` từ claim, không re-fetch membership DB; `Authorize` `IsRoot()`/`AuthUserCan` theo role token, deny→`errors.Forbidden`(403). **Transition**: `fs/user.go Roles []*Role` m2m → content API `PUT /api/content/user/{id}` đổi roles. PUT idempotent. OpenAPI. Chi tiết+A–F: FINDINGS Qualifier 4. |
| 57 | ConduitPlatform/Conduit | 924 | S3 BaaS TS (triage tree) | LOẠI (nhẹ) | Backend gRPC-module; `modules/authentication` + module `authorization` (authz/ReBAC) riêng → quyền từ relation store DB, không claim; kiến trúc module phức tạp (gRPC), S2/S4 nặng. |
| 58 | Erudika/para | 575 | S3 BaaS Java (hand-check code) | LOẠI (nhẹ) | `JWTAuthenticationProvider` validate JWT theo `app.getSecret()+user.getTokenSecret()` (tokenSecret từ DB → revoke bằng xoay secret) + authz `ProtectedPath`/app-permission DB. Token revocable, không C-JWT thuần. Cũng LDAP/OAuth1/app-auth. |
| 59 | sitepins/sitepins | 185 | R4 CMS TS (hand-check code) | LOẠI | Chính là better-auth session (DB); org role (role demote được) qua `resourceAuth.ts requireOrgAccess` query Organization DB → `member.role` từ DB mỗi request → đổi role có hiệu lực ngay. JWT chỉ userId + global role (admin panel, không per-user đổi). |
| 60 | o2sdev/openselfservice | 185 | S3 vein TS (hand-check code) | LOẠI (nhẹ) | `framework/.../auth/auth.guard.ts`: `RoleGuard`/`PermissionGuard` ABSTRACT (framework NestJS), auth uỷ cho integration external (Contentful/Strapi CMS). Framework, không app standalone (S2); auth external. |
| 61 | RaythaHQ/raytha | 248 | R4 CMS C# (hand-check code, core-limit) | LOẠI (nhẹ) | `LoginWithJwt.cs`: JWT login là SSO EXTERNAL (nhận JWT từ AuthenticationScheme/IdP cấu hình, jti replay-protect via db.JwtLogins) rồi phát cookie session riêng → mô hình SSO+cookie, không self-mint stateless role-token; S5 external IdP. (Current-user per-request chưa đọc do core rate-limit.) |
| 62 | ivanarama/onebase | 113 | T1 low-code Go (hand-check code) | LOẠI | Cookie `onebase_session` = session server-side (`serveWithSession` resolve session/DB), không JWT tự chứa; có 2FA (C-STEP). Session-based, không C-JWT. |
| 63 | raouf-b-dev/ecommerce-store-api | 55 | V3 NestJS 30-100★ (hand-check code) | **QUALIFIER (Tier B)** | **C-JWT ✓✓**: `auth.guard.ts` role từ claim `payload.role`→`request.user.role`; `permissions.guard.ts` `resolveRolePermissionsService.execute(user.role)` resolve quyền theo ROLE-CỦA-TOKEN, không tra assignment DB theo userId. `jwt-verifier` không denylist; `assign-user-role.usecase` không revoke → token cũ còn hiệu lực. **Transition**: `AssignUserRoleUseCase` trong `users.controller` (`@RequirePermissions('manage_users')`). **C-SRC**: `PUT /users/:id`. 403 qua ForbiddenException. RS256 local issuer `ecommerce-api`. Chi tiết+A–F: FINDINGS Qualifier 5. CHỨNG MINH dải 30–100★ có qualifier. |
| 64 | alvaromrveiga/ecommerce-backend | 72 | W1 NestJS 20-95★ (hand-check code) | **QUALIFIER (Tier B)** | **C-JWT ✓✓**: `access-jwt.strategy.ts validate(payload)` trả `{userId, userRole: payload.userRole}` từ token, không DB; `roles.guard.ts` `userRole===Role.ADMIN` từ `request.user` (token). **Transition**: `@IsAdmin() @Patch('role') updateUserRole` (user.controller). **C-SRC**: PATCH role idempotent. 403 qua ForbiddenException. Chi tiết: FINDINGS Qualifier 6. |

### §Góc tick-live-1 (2026-10-08 09:xx): dải 100–1500★ app thật
Chạy `search/repositories sort=stars asc` dải `100..1500` + topic rbac/jwt/self-hosted + language go/rust. Lọc BỎ
lib/middleware/engine/scaffold-Casbin (Casbin=DB-policy→không C-JWT). App thật còn lại để đọc authz:
- [x] magic (1200★ C#) → **QUALIFIER #38**.
- [x] qingwave/weave (604★ Go) → #39 LOẠI: `middleware/authentication.go` parse token rồi `userRepo.GetUserByID`; `authorization/authorization.go Authorize()` lại `store.User().GetUserByID` + đọc `user.Roles`/group roles từ DB mỗi request. DB-backed, không C-JWT.
- [x] tx7do/go-wind-admin (569★ Go kratos) → #40 LOẠI (nhẹ): go-kratos gRPC/HTTP gen, permission-service riêng + permission_audit_log + MFA/login_policy → nghi authz tra store server-side + step-up (C-STEP) + S4>200 gen. Không C-JWT (kiến trúc).
- [x] Mininglamp-OSS/octo-server (1064★ Go) → #42 LOẠI (nhẹ): `internal/carddispatch/authorizer_db.go` DB-backed; 3599 file (messaging/bot platform), S4>>200, nhiều external dep. Không bõ.
- [x] quuuuj/hrm (464★ Spring Boot) → **QUALIFIER #41** (C-JWT `permissions` claim, `POST /staff/set/{id}` transition, `PUT /role` source). Mở: captcha login S5, S4 op count.
- [ ] Erudika/para (575★ Java) — multitenant backend, nghi API-key.
- [ ] djaodjin/djaoapp (143★) — gateway user/billing.

### §Góc tick-live-2: dải 100–1500★ Spring Boot/NestJS (K1/K2/K3 đã liệt kê repo)
Shortlist app THẬT chưa đọc (đã bỏ lib/pac4j/sample/boilerplate/casbin-scaffold):
- [ ] youlaitech/youlai-boot (370★ SpringBoot3) — nghi Redis-permission cache (youlai framework). Đọc filter.
- [ ] yangzongzhuan/RuoYi-Vue-Oracle (339★) — RuoYi: LoginUser lưu Redis theo uuid token, perm từ Redis → nghi LOẠI (token-as-session-key).
- [x] kuangshp/nestjs-mysql-api (903★) → #44 LOẠI (Redis session-store + S8).
- [x] Genc/spring-boot-boilerplate (385★) → #43 LOẠI (loadUserByUsername DB + không endpoint đổi role).
- [ ] hoangtien2k3/ecommerce-microservices (390★) — gateway auth, phức tạp.
Heuristic tinh (sau #41/#43): Spring C-JWT = filter KHÔNG gọi `loadUserByUsername` (authority từ claim) + CÓ endpoint admin
gán lại role user khác. Lọc nhanh: đọc JwtAuthenticationFilter trước; thấy loadUserByUsername → LOẠI ngay (DB).
Nhật ký verdict từng cái. Nguồn query: K1 (topic:jwt language:java 80..1500), K2 (topic:spring-boot topic:jwt 50..1500),
K3 (topic:nestjs topic:rbac 30..1500), T1-T5/G5 (repo search dải). Query chưa chạy: `self-hosted team roles api stars:100..1500`,
route hợp-đồng dải mới (search/issues "still admin after"/"jwt role not updated" rồi lọc 100..1500★).
Query kế (khi reset search limit ~1'): `rbac admin language:go stars:150..1200 pushed:>2026-03-01` (T5 bị 403 chưa chạy);
`topic:self-hosted topic:jwt stars:100..1500`; `self-hosted team roles api stars:100..1500`.
Route hợp-đồng dải mới: `search/issues "still admin after" is:issue` / `jwt role not updated` rồi lọc repo 100..1500★.

### §Góc tick-live-3 (2026-10-09, phiên tương tác mới): săn tiếp 6→10
Heartbeat: `2026-10-09` LIVE, user canh, tự-động-hoá tắt. Mục tiêu 4 qualifier nữa. Vein đã chứng minh:
(a) ecommerce NestJS/TS dải nhỏ CÓ endpoint gán lại role (raouf #63, alvaro #64); (b) BaaS/headless-CMS/low-code
API-first (bcms #52, fastschema #56, magic #38). Vein đã cạn (loại cả cụm, §Khảo sát): FastAPI-admin CN, NestJS
boilerplate, Casbin, session-store, multi-tenant SaaS Prisma, Django DRF, devise-jwt, Laravel Sanctum. Lọc nhanh:
đọc file authz/guard TRƯỚC; thấy findById/loadUserByUsername/GetUserByID/Redis-session → LOẠI ngay (DB). Giữ lại khi
authz đọc role/perm thẳng từ claim + CÓ endpoint admin đổi role user khác. Query chưa chạy (queue §tick-live-2 + cB,cD-cH,iF).

| Ecosystem / lớp | App đại diện đã đọc | Cơ chế authz | C-JWT? | Kết luận |
|---|---|---|---|---|
| FastAPI admin-backend (CN) | fastapi-admin-v2 #14, fastapiReactadmin #16 | DB + Redis cache version-bumped | Không | Loại cả lớp |
| NestJS auth/boilerplate | nestjs-auth #26, caps-pizza #25 | JwtStrategy.validate→findById DB | Không | Loại cả lớp |
| Go + Casbin admin | gin-casbin-admin #27 | Casbin enforce theo DB policy, GetUserRoles DB | Không | Loại cả lớp |
| Rails/engine IAM | rails_iam #22 | engine/gem, DB-driven | Không (lib) | Loại (S2) |
| Session-store auth | FastAPI-Authentication #24 | session revocable DB | Không | Loại cả lớp |
| Multi-tenant SaaS | rcrdk #34, innkeeper #15 | membership-role findFirst DB mỗi request | Không | Loại cả lớp |
| Flask-JWT-Extended app nhỏ | placement-portal #28, pairs-api #30 | role/is_admin trong JWT, KHÔNG tra DB | **CÓ** | **near-miss** (thiếu endpoint đổi role) |
| Go CRM (JWT thủ công) | GopherCRM #35 | JWT có role claim NHƯNG ValidateToken GetByID DB | Không | Loại (chống stale chủ động) |
| Self-hosted helpdesk | douban/helpdesk #36 (OIDC), aottr/paw #37 (Django) | OIDC external IdP / Django DB | Không | Loại (external-IdP / DB) |
| Django (DRF SimpleJWT) | aottr/paw #37 | SimpleJWT get_user → DB | Không | Loại cả lớp (nghi) |
| Rails (devise-jwt) | devise-jwt README (khung, 1292★) | Warden load user DB + revocation JTI/Denylist/Allowlist check DB | Không | Loại cả lớp (bằng chứng khung) |
| Laravel (tymon/Sanctum) | search chỉ ra package | guard retrieveById DB / Sanctum token DB | Không | Loại cả lớp (khung, không app standalone) |

## Lệch luật / sự cố

- **2026-10-09**: mốc giờ dừng gốc (giờ local ≥ 2026-10-08 12:00) đã qua từ hôm trước; phiên overnight dừng ở 6/10 qualifier. User tái giao hôm nay ("tạm thời săn tiếp cho tôi tới 10 qualifier"). Luật dừng hiệu lực từ nay: CHỈ còn "đủ 10 qualifier" (bỏ nhánh giờ). Phiên tương tác, user canh; KHÔNG đặt cron/wakeup. Mọi luật lọc/hình dạng/dedup §README giữ nguyên.
