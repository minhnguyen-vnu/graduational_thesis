# Lịch sử sửa phiếu gán nhãn

`rules-draft.md` §9 bước 7: quy tắc chỉ được sửa giữa hai vòng, sửa thì ghi ở đây, và vòng trước không được
gán lại bằng quy tắc mới trừ khi nói rõ.

## v2 — 2026-09-19

**Sửa bước 2.** Cũ: không có **đồng thời** một từ chỉ chủ thể và một từ chỉ quyền → `N2`, dừng.
Mới: không có **bất kỳ** từ nào thuộc hai nhóm → `N2`, dừng; có một từ của một nhóm là đủ để đi tiếp.

**Vì sao.** Bước 2 cũ chặn chính hai ví dụ của phiếu: `POST /roles` (mã `N4`) không có từ chỉ chủ thể,
`DELETE /users/{id}` (mã `N8`) không có từ chỉ quyền — theo nghĩa đen cả hai phải dừng ở `N2`. Nó còn chặn
`DELETE /roles/{id}`, đúng là ví dụ của mã `R2`. Ba lượt gán vòng 1 xử lý chỗ này khác nhau: có lượt dừng ở
`N2`, có lượt đi tiếp tới mã cụ thể, và một phần trong 13 dòng lệch của vòng 1 sinh ra từ đây
(`infra/squad/reports/2026-09-18-dem.md` §4).

**Sửa kèm.** Dòng `N2` trong bảng mã `N` viết lại cho khớp bước 2 mới.

**Hệ quả.** Nhãn vòng 1 sinh ra dưới phiếu v1. Vòng 2 gán lại **toàn bộ 519 dòng** bằng phiếu v2, hai lượt máy
mù như cũ. Nhãn v1 giữ ở `labelling/*.l1.csv`, `*.l2.csv` để đối chiếu, không nhập vào kết quả.

**Không sửa.** Định nghĩa `R`/`N`/`U`, danh sách trường được nhìn, các mã `R2`–`R6`, `N1`, `N3`–`N9`, `U1`–`U3`,
thứ tự quyết định các bước 1, 3, 4, 5.

## 2026-09-20 — sai lệch giao thức phân xử

`labelling-form.md` §8.2 và `rules-draft.md` §9 ghi: người phân xử, LLM không tham gia. Hai mươi dòng thuộc tầng
`agree-R`, nơi người gán khác cả hai lượt máy, do mô hình phân xử theo yêu cầu của người gán. Sổ:
`labelling-r2/adjudication.csv`, cột `adjudicator` ghi `model`.

Kappa người–máy tính trên cột `label` trước khi phân xử, không đổi: 0,369 có trọng số. Bộ từ vựng rút ra từ
`final_label`, tức từ nhãn đã có mô hình tham gia; hạn chế này phải viết trong `docs/lexicon.md`.

## 2026-09-20 — luật chốt nhãn cho tầng lệch

Quyết sau khi đã thấy số đếm, không phụ thuộc dòng nào ra nhãn gì: ở tầng hai máy lệch nhau, nhãn của người
đứng vững khi có ít nhất một trong hai lượt máy cùng nhãn với người. 35 trên 44 dòng rơi vào diện này. Chín dòng
còn lại, cộng ba dòng tầng `agree-N` người khác máy, do mô hình phân xử.

Tổng cộng mô hình phân xử 32 dòng, sổ `labelling-r2/adjudication.csv`. Trong 12 dòng chốt đợt hai, 7 dòng giữ
nhãn của người và 5 dòng theo nhãn máy.

Hai chỗ form còn thiếu, ghi lại để sửa lên v3: `N3` đòi "mức nâng cố định trong path", nên không phủ endpoint chỉ
thêm role mà client chọn giá trị (`S112-0144`); và không mã nào phủ chính sách cấp tổ chức (`S132-0158`,
`S132-0164`).

## Luật rút bộ từ vựng — 2026-09-20 23:31

`rules-draft.md` §11 viết xong lúc 2026-09-20 23:31, trước khi `derive_lexicon.py` tồn tại.
P1 (một từ phải trúng dòng `R` ở ít nhất hai nhà cung cấp) là điều kiện chặn từ riêng của Keycloak.
P2 là công thức `2 * 26/241 = 0.2158`, không phải số chọn tay.
§11.8 khai bản xem trước đã chạy trước khi luật được viết.
Danh sách 4–9 của `RestSecurityBuilder.kt` không rút được: corpus không có nhãn thứ tự giữa các giá trị quyền.

## Xếp hạng thay cho lọc — 2026-09-21 00:02

`rules-draft.md` §12 viết lúc 00:02, trước khi `rank_lexicon.py` tồn tại.
Điểm một từ là `(df_R+1)/(df_R+df_N+2) × ncc/(ncc+1)`. P1 của §11 đổi từ điều kiện chặn thành hệ số phạt.
Thước đo đổi từ precision/recall nhị phân sang hạng của endpoint `R` đầu tiên trong mỗi spec, vì
`RestSecurityBuilder.kt:809` chọn đúng một endpoint làm transition.
§12.5 khai nửa test đã bị dùng để phát triển: mục 12 thiết kế sau khi thấy kết quả `RESULTS.md` §2 và §8.

## Sửa trích xuất envelope JSON:API — 2026-09-21

`corpus/extract_ops.py` thêm `unwrap_envelope`. 17 dòng S131 đổi `body_field_names` từ `data` sang
tên trường thật. Nhãn cũ giữ nguyên ở `labelling-r2/`; bản trích lại gán lại từ đầu ở `labelling-r3/`.
Hạn chế đã ghi trước đó — hai lượt máy dùng kiến thức ngoài spec ở S131 — vẫn đứng, vì nó nói về
lượt gán cũ trên dữ liệu cũ.

## Mở rộng nửa train — 2026-09-21

15 spec mới S200–S214, seed `20260921`, tất cả vào nửa train. Khai ở `corpus/sampling-plan.md` §1e.
Hai lượt máy mù chạy đêm 09-21 trên 249 dòng mới cộng 17 dòng S131 trích lại.
Lượt người chưa chạy trên phần mở rộng này.

## Rút lần 2 trên train mở rộng — 2026-09-21

Luật §11 và §12 không sửa. Chỉ dữ liệu train đổi: 26 `R` trên 5 nhà cung cấp thành 39 `R` trên 11.
Nửa test: top-1 `0.167` lên `0.667`, top-3 `0.500` lên `1.000` (`lexicon-20260921/RESULTS.md` §2).
Đo trên cùng bộ nhãn test cho thấy sửa trích xuất envelope góp `0.167` đến `0.333`, dữ liệu train góp phần còn lại.

Hạn chế cũ "hai lượt máy dùng kiến thức ngoài spec, chứng cứ S131-0097 và S131-0100" nay chỉ còn đúng
với bản trích xuất cũ. Sau khi bóc envelope, hai dòng đó ra `N` và `R` với cả hai lượt máy mới.
Khi viết luận văn phải nói rõ là lỗi trích xuất, không phải lỗi của người gán nhãn.

## Lỗ hổng phiếu tìm thấy từ 13 dòng hai máy lệch — 2026-09-21

13 dòng bị loại theo `sampling-plan.md` §1g. Đọc hết thì bốn nguyên nhân, không phải mười ba.

**1. Phiếu không nói chủ thể có bắt buộc là người không.** 5 dòng.
`POST /admin.apps.restrict` (app), `PATCH /v1/devices/{id}` (device),
`POST .../resourceGroups/.../writeDelegates` ×2 (delegate), `PATCH .../metadata` (document).
Một máy coi app và device là chủ thể nên gán `R2`, máy kia coi chúng là tài nguyên nên gán `N6`.
§3 bước G2 chỉ viết "quyền của chủ thể" mà không định nghĩa chủ thể.
v3 phải nói thẳng: app, thiết bị, service token, delegate có tính là chủ thể hay không.

**2. Chuyển quyền sở hữu không có mã.** 2 dòng.
`PUT /api/v1/transfers/{id4n}/receiveInfo` và `sendInfo`, có `keepOwnership=false`.
Một máy gán `R2` vì chủ cũ mất quyền, máy kia gán `N6`.
Đây là quan hệ A2 (`docs/metamorphic-authz-relations.md`), ngoài phạm vi công cụ này.
Lần trước cùng chuyện này xảy ra với `POST /repos/{owner}/{repo}/transfer` (S108-0129).
v3 cần một mã `N` nói rõ "chuyển quyền sở hữu, thuộc A2, không tính".

**3. Đổi phạm vi chia sẻ của tài nguyên không có mã.** 2 dòng.
`PUT .../history/.../visibility` có `sharedOrganizationIds`, `PUT /policies/{policyId}`.
Client đặt lại danh sách tổ chức được xem: người ngoài danh sách mất quyền đọc, nhưng đối tượng
bị ghi là tài nguyên chứ không phải chủ thể nào.

**4. Chính sách cấp tổ chức.** 2 dòng, đã ghi ở mục trước.
`PUT /user/interaction-limits`, `DELETE .../branches/{branch}/protection/restrictions`.

Hai dòng còn lại (`DELETE /api/v1/UserSubscriptions`, `S210-0240`) là `U2`/`U1` thật, từ nước đôi.

## Hạng đo trên tập nào — 2026-09-21

Con số top-k báo lần đầu xếp trên các dòng đã giữ của mỗi spec, tối đa 36, trong khi runtime xếp trên
mọi endpoint ghi. Sai lệch: top-1 `0.667` so với `0.500`, top-3 `1.000` so với `0.833`.
Gán bù 41 dòng theo `sampling-plan.md` §1h đóng khoảng đó.

Khi viết luận văn, mọi con số top-k phải nói rõ xếp trên tập nào. Xếp trên mẫu là lạc quan.

## Hạng là khoảng, không phải một giá trị — 2026-09-21

`lexicon-20260921/RESULTS.md` §8 viết "ba con số là chính xác, không phải khoảng". Sai, đã rút lại.

Nhiều endpoint có cùng điểm, cùng verb, cùng trạng thái tham số người dùng. Hạng của endpoint `R`
trong nhóm bằng điểm do một luật phá hoà chưa khai quyết định. S123 nằm trong nhóm 10 endpoint bằng
điểm: hạng của nó là `1–10`.

Thước đo mới, `rank_exact2.py`: khoảng tốt nhất–xấu nhất, cộng một giá trị phá hoà bằng thứ tự endpoint
trong spec, tức thứ tự `actionDefinitions` mà EvoMaster nhận. Giá trị thứ hai là giá trị áp dụng được.
Số ở `lexicon-20260921-audited/RESULTS.md` §4.

## Sửa thứ tự tách từ — 2026-09-21

`rules-draft.md` §11.4 khai: tách theo ký tự không phải chữ-số, rồi tách camelCase, rồi hạ chữ thường.
`derive_lexicon.py` hạ chữ thường trước, `derive2.py` không, nên nửa `param` của `lexicon-20260921/`
giữ `permissiongroupid` và `policyid` — hai token dính liền không có trong spec.

`derive3.py` chạy đúng thứ tự §11.4. Luật không sửa; chỉ bản cài đặt sai được sửa cho khớp luật.
Nửa `path` tái lập trùng từng byte, nên lỗi chỉ ảnh hưởng nửa `param`.

## Lượt soát thứ ba trên phần mở rộng — 2026-09-21

`sampling-plan.md` §1i, khai trước khi chạy. Một lượt riêng, mù, 56 dòng: 28 dòng `R` đồng thuận cộng
28 dòng `N` bốc hạt giống `20260921` làm nhiễu. Đồng thuận thô `0.964`, kappa `0.927` trên cả 56 dòng.

Ba dòng train đổi. Một trong ba, `S210-0137 PUT /orgs/{org}/outside_collaborators/{username}`, hạ điểm
từ `collaborators` từ `0.3750` xuống `0.2500` và đẩy S108 từ hạng 1 xuống hạng 6 trên nửa test:
top-1 theo thứ tự spec từ `0.667` xuống `0.500`.

Luật ngày 09-17 xếp "đưa một chủ thể ra khỏi nhóm" vào diện không tính (`rules-draft.md` §8).
Lượt soát áp đúng luật đó. **Luật không sửa sau khi đã thấy giá của nó.**
