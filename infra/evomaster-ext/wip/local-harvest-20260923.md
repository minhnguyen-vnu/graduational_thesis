# Patch: thu giá trị quyền theo từng endpoint

Chưa áp, chưa build. Cần OK trước khi `git apply`.

- Patch: `local-harvest-20260923.patch`, một dòng. `git apply --check -p1` đã qua.
- Self-test: `infra/evomaster-ext/selftest/local-harvest.sh`.
- Áp được độc lập với `field-gate-20260923.patch`, và áp được cả hai cùng lúc.

## Sửa gì

```
-        val enumVocab = (allGenes(transition) + actionDefinitions.flatMap { allGenes(it) })
+        val enumVocab = allGenes(transition)
```

Chỉ trong `harvestReducedRoleCandidates` (`:871`). `harvestElevatedRoleCandidates` không đổi: nó phục vụ
khôi phục quyền, không quyết định chọn endpoint nào.

## Vì sao

`harvestReducedRoleCandidates` gom giá trị `enum` từ **toàn bộ API**. Ứng viên hạng 1 vì thế hầu như luôn có
giá trị quyền để đề xuất, nên vòng lặp 8 ứng viên của `lexicon-rank-20260921.patch` không bao giờ chạy sang
ứng viên thứ hai. Self-test hiện tại ghi đúng hành vi đó: `harvest-is-global` thấy 6 giá trị quyền thu được
trên `POST /auth/login`, một endpoint không có trường quyền nào.

Hệ quả: `MAX_TRANSITION_CANDIDATES = 8` không có tác dụng lúc chạy, và con số `top-8 = 1.000` đo trên corpus
không chuyển được sang runtime. Chỉ `top-1` là con số có nghĩa.

## Ba target có sống không

Đọc từ spec, chưa chạy:

| Target | Transition | Nguồn giá trị quyền của chính nó |
|---|---|---|
| Tier-1 | `PUT /users/{username}/role` | `RoleUpdateRequest.role` enum `ADMIN, VIEWER` |
| Tier-2 | `PUT /users/v1/{username}/role` | `role` enum `admin, user` |
| pyLoad | `POST /api/set_user_permission` | **không có enum nào**; `permission` và `role` là query param số, nên `numericRoleCandidates` lo |

Không target nào lấy giá trị quyền từ endpoint khác. Đây là lý do tin patch này không mất phát hiện.
Chứng cứ là 10 seed mỗi target, không phải bảng này.

## Đo được gì trước khi build chuỗi (2026-09-23, jar `2ec4b921`)

Hai lần chạy dò trên Tier-1, đọc dòng `transition candidate` ở mức `debug`:

| Endpoint đứng đầu (từ vựng mồi) | `reducedRoleValues` | Vòng lặp |
|---|---|---|
| `POST /reset` — không có thân yêu cầu | **0** | nhảy sang `PUT /users/{username}/role`, chọn endpoint đó |
| `POST /auth/login` — có thân, không có trường quyền | **1** | dừng, chọn login |

Dưới jar `L` (thu toàn API) `POST /auth/login` cho **6** giá trị. Xuống 1 là bằng chứng patch có tác dụng.

**Giá trị còn lại là kiểu nội dung, không phải quyền.** `BodyParam` giữ `contentTypeGene: EnumGene<String>`
(`BodyParam.kt:38`), nên mọi endpoint có thân yêu cầu thu được ít nhất `application/json` và không bao giờ
trả về danh sách rỗng. Vòng lặp 8 ứng viên vì thế chỉ nhảy khi ứng viên hạng trên **không có thân yêu cầu**.

Đây là điểm yếu sẵn có của `harvestReducedRoleCandidates`, không phải do patch này sinh ra: nó coi
`application/json` là một giá trị quyền hợp lệ. Patch này không sửa chỗ đó. Cách sửa tiếp theo — đòi ứng viên
phải có một gene tên trúng `roleFieldSignals` — là một thay đổi khác, chưa khai, chưa đo.

## Chỗ phải soi

Đây là thay đổi **có thể làm tụt số**. Nếu một target thật sự sống nhờ giá trị `enum` vay từ endpoint khác
thì nó mất phát hiện. Theo `CLAUDE.md` §6 nhịp chạy: sửa nhỏ thì chạy seeds 1–10 mọi nhánh, mọi target.

Nếu 10 seed cho kết quả y như jar `L` thì patch này không đổi số, mà chỉ làm `MAX_TRANSITION_CANDIDATES`
có nghĩa lần đầu. Đó là điều cần cho luận văn: hôm nay không viết được câu nào về top-3 hay top-8.

## Chưa chứng minh

- Chưa build, chưa self-test, chưa chạy seed nào.
- Chưa đo vòng lặp thật sự chạy sang ứng viên thứ hai trên target nào.
