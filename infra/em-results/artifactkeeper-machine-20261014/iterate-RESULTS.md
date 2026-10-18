# artifact-keeper — vá setField wrapper-activation, xác nhận 970 nổ (2026-10-15)

Chuỗi: chạy P2e (`evomaster-P2e-6ae8277b.jar`) trên artifact-keeper vuln (`e56d3aa7`) ra FN; truy nguyên tới mã; vá;
dựng lại; chạy lại tới khi 970 nổ. Lặp đúng 1 vòng là nổ.

## FN gốc (jar P2e, seeds 1–2)

`runs-vuln.csv`: `vuln,1,…,det970=0,assembled=0,void=17,unconfirmed=3` và `vuln,2,…,det970=0`.

Builder duyệt 7 transition (lọc `reducedRoleValues≥1`), gồm cả transition thật `PATCH /api/v1/users/{id}` (ứng viên 4,
score 3.70). Transition thật bị loại KHÔNG phải do luật chuyển-ứng-viên mà do hết victim:

- Lượt admin PATCH victim: body lên dây là `{"is_admin":null}` (traffic seed 1 req 4574, seed 2 req 5173) → server 200
  nhưng không hạ quyền. `RestSecurityBuilder.kt:1001-1003` đánh dấu victim vào `privilegeReducedInPhase` trên MỌI 2xx,
  trước cả bước xác nhận. C4 sau đó báo "re-login did not show the privilege removed" → UNCONFIRMED, nhưng dấu vẫn còn.
- `:782`/`:788` loại victim đã đánh dấu khỏi phần còn lại của pha (kể cả vai trò operator). Victim `operator` chỉ còn
  operator `viewer` (không admin) → 403. Hết victim → sang ứng viên 5.

## Lỗi mã (P2e, commit a544c996ac)

`setField` (`RestSecurityBuilder.kt:1359-1363`) ghi giá trị qua `f.gene` rồi `activateAncestors(f.gene)` — chỉ bật các
wrapper TRÊN `f.gene`. `NullableGene` nằm giữa `f.gene` và lá không được bật: `NullableGene.unsafeSetFromStringValue`
(`NullableGene.kt:130-135`) chỉ chạm `isActive` ở nhánh `"null"`, nhánh giá trị thật để nguyên. Lần khởi tạo ngẫu nhiên
để nó tắt → `getValueAsPrintableString` (`NullableGene.kt:85-88`) in `nullLabel` → body `{"is_admin":null}`.

Trường `is_admin` trong spec là `{"type":["boolean","null"]}` → có `NullableGene` trong chuỗi. AF2 dùng hàm riêng
`setAdminFlagActive` đặt `bool.value` thẳng ở lá rồi bật wrapper từ lá đi lên → body `{"is_admin":false}` (AF2 traffic
seed 1 req 4852, 10002). P2 thay bằng `setField` chung và làm trượt điểm bật wrapper.

## Vá (tổng quát, không chắp vá)

`RestSecurityBuilder.kt:1360-1361`: `f.gene` → `f.value` (lá). Neo cả bước ghi và bật-wrapper vào lá; `activateAncestors`
bật mọi wrapper từ lá tới gốc, đúng cho mọi kiểu trường nullable/optional. Trùng khuôn `clearArray` (`:1379-1384`) đã có.
Không chuỗi/path/tên trường/giá trị nào của artifact-keeper vào mã. Patch: `wip/setfield-leaf-activate-20261015.patch`.
Rollback đã diễn tập (checkout + reapply khớp byte).

## Kết quả vòng 1 (jar vá `evomaster-P2f-64ee8ffc.jar`, cùng cấu hình held-out)

`iterate.log`: `fix1-seed1 exit=0 det970=1 assembled=2 patch_chosen=1 unconfirmed=2 patch200_false=1 patch200_null=0`.

Bộ ba (`fix1-seed1.log`): `Assembled … on POST:/api/v1/admin/analytics/snapshot (victim 'victim', operator 'operator',
transition PATCH:/api/v1/users/{id}, statuses 200/200/200)`; `transition PATCH … proven by an attempt with statuses
200/200/200`. PATCH quyết định: `/api/v1/users/5b85e9d4-… -> {"is_admin":false}` → 200 (hạ quyền thật). report.json có
fault 970. Hình dạng bộ ba trùng lần nổ AF2.

Chỉ đổi jar giữa FN và TP; spec, auth, cấu hình, target đều giữ nguyên.

## Dè dặt

- Jar `P2f-64ee8ffc` CHƯA qua cổng hồi quy. Chưa có số luận văn nào đổi theo nó. Cổng + đo lại là bước sau.
- `:1001-1003` (đánh dấu "đã hạ" trên mọi 2xx, không chỉ khi C4 xác nhận) vẫn là một điểm yếu riêng; không cần cho lần
  nổ này vì body giờ hạ quyền thật, nhưng là một thay đổi tách riêng nếu muốn làm chặt.
- Hệ quả tài liệu cần soát: `docs/argument.md` K3 ("thay hardcode bằng mô hình không mất phát hiện nào") và K4 — FN này
  do refactor P2 (`setField`), một thay đổi P2e, gây ra trên target phát triển artifact-keeper.

## Chạy đủ seed (jar vá `evomaster-P2f-64ee8ffc.jar`, arm vuln, 2026-10-15)

`runs-fixjar-vuln.csv` / `progress-fixjar-vuln.log`: 5/5 seed nổ 970. Mỗi seed det970=1, assembled=2, PATCH:/users/{id}
chosen=1, PATCH-200 body `is_admin=false` (false=1, null=0, other=0), slept=0, exit=0. Không dừng sớm, không máy ngủ.

| seed | det970 | assembled | patch200_false | patch200_null | slept |
|---|---|---|---|---|---|
| 1 | 1 | 2 | 1 | 0 | 0 |
| 2 | 1 | 2 | 1 | 0 | 0 |
| 3 | 1 | 2 | 1 | 0 | 0 |
| 4 | 1 | 2 | 1 | 0 | 0 |
| 5 | 1 | 2 | 1 | 0 | 0 |

Soát cấu trúc `audit970-fixjar-vuln.out`: 5/5 PASS (A cùng credential, B không re-login giữa source↔follow-up, C operator
khác, D ba trạng thái 2xx), 0 FAIL, 0 UNPARSED, 0 silent triple. Không seed nào có 970 mà thiếu bộ ba.

Cấu hình `run-fix-vuln.sh`: reseed full trước mỗi seed, maxTime 1200s, rate 600, extraPhase 0.25, D1 tắt, proxy :8212.
So với FN gốc của P2e chỉ đổi jar; spec, auth, target giữ nguyên.

Dè dặt: jar P2f chưa qua cổng hồi quy; đây là arm vuln của target phát triển, không phải số luận văn. Arm fixed (0 FP)
cần checkout + build lại backend, chưa chạy.
