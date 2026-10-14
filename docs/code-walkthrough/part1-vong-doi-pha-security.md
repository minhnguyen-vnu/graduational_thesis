# Part 1 — Vòng đời pha SECURITY

File: `core/src/main/kotlin/org/evomaster/core/problem/rest/service/RestSecurityBuilder.kt`
Dòng 191–223. Của EvoMaster gốc, **trừ dòng 200–202 là code ta thêm vào**.
Kiểu dữ liệu dùng ở đây (`Solution`, `EvaluatedIndividual`, `RestIndividual`) giải thích ở `part0-base-evomaster.md`.

## 1. Đoạn code này làm gì

Chạy **sau khi** search kết thúc. Nó lấy các test đã sinh ra trong search, rồi lần lượt gọi 5 bộ
sinh test bảo mật. Không đụng vào thuật toán tiến hoá.

Bằng chứng thứ tự pha, log thật `infra/em-results/tier2b-restore-trials/logs/vuln-noreset-seed1.log`:

```
3401: * Phase SEARCH lasted: 0h 10m 0s
3402: * Starting phase MINIMIZATION
3409: * Phase MINIMIZATION lasted: 0h 2m 24s
3410: * Starting phase SECURITY        <- applySecurityPhase() bắt đầu ở đây
3488: * Phase SECURITY lasted: 0h 6m 10s
3489: * Starting phase WRITE_OUTPUT
```

## 2. Chạy tay — run `vuln-noreset-seed1` (pyLoad :8090)

| Dòng | Code | Quan sát thật trong run này |
|---|---|---|
| 191 | `fun applySecurityPhase(): Solution<RestIndividual> {` | Gọi từ `applyPhase()` (dòng 180), do `Main.kt` kích hoạt khi `config.security = true` |
| 194 | `individualsInSolution = this.archive.extractSolution().individuals` | Kiểu `List<EvaluatedIndividual<RestIndividual>>`. Mỗi phần tử là một test: individual (danh sách `RestCallAction`) cộng `results` (danh sách status code). Hình dạng cụ thể xem `part0-base-evomaster.md`. Run này ghi ra 553 test cuối cùng |
| 196 | `expandWithForbidden()` | Với mỗi endpoint chưa có 403 nhưng đã có 401, nó chạy lại test đó bằng user khác để **ép ra 403** |
| 198 | `individualsInSolution = this.archive.extractSolution().individuals` | Đọc lại cùng kiểu đó, vì dòng 196 vừa thêm test 403 mới vào archive. Biến ở dòng 194 là ảnh chụp cũ, không tự cập nhật |
| 200 | `if(!hasPhaseTimedOut()) {` | Ngân sách pha = `extraPhaseBudgetPercentage × maxTime` = `0.6 × 600s` = **360s**. Lúc này mới hết 0s nên vào trong |
| 201 | `addForStatefulAccessControl()` | **Code của ta.** Sinh ra 4 dòng log ngay sau đó (mục 3 bên dưới), kết thúc bằng 1 fault 970 |
| 206 | `if(!hasPhaseTimedOut()) { addForAccessControl() }` | Chạy. Sinh ra ~70 dòng `WARN AuthUtils - Got 401 although having auth for 'pyload' on endpoint: /api/...` — nó thử từng endpoint một |
| 212 | `if(!hasPhaseTimedOut()) { addForInjections() }` | Chạy. Kết quả: **4 fault code 201 (XSS)** trong `report.json` |
| 218 | `if(!hasPhaseTimedOut()) { addForInfoLeakage() }` | Pha đã báo timeout ở 360s (log dòng 3487). Không có fault 209 nào trong `report.json` |
| 222 | `return archive.extractSolution()` | Trả archive đã có test bảo mật. Ghi ra đĩa: 553 test, 38 fault |

Fault đếm được từ `vuln-noreset-seed1/report.json`:

```
code 100 (HTTP 500)      : 37
code 201 (XSS)           :  4
code 970 (của ta)        :  1
```

## 3. Bốn dòng log mà dòng 201 sinh ra

Log thật, dòng 3411–3415:

```
Discarded a VOID stateful-authorization (MR-A1) attempt on POST:/json/status (victim 'pyload', operator 'alice',      codes 200/401/200)
Discarded a VOID stateful-authorization (MR-A1) attempt on POST:/json/status (victim 'pyload', operator 'superadmin', codes 200/401/200)
Privilege-restore accepted for 'alice' by 'pyload' with role '0' on POST:/api/set_user_permission -> 200
Assembled a stateful-authorization (MR-A1) triple on POST:/json/status (victim 'pyload', operator 'alice', transition POST:/api/set_user_permission, statuses 200/200/200)
```

Chi tiết từng dòng thuộc Part 2 và Part 3.

## 4. Ba điểm phải nhớ ở đoạn này

**a. `expandWithForbidden()` ở dòng 196 là điều kiện tiên quyết của ta.**
Code của ta chỉ nhận một endpoint làm `source` nếu endpoint đó **đã từng trả 403** cho ai đó trong archive
(`guardedCandidatesFor`, Part 2). Bằng chứng 403 đó do dòng 196 tạo ra. Nên vị trí dòng 201 nằm ngay sau
dòng 196–198 là ràng buộc dữ liệu.

Đọc `expandWithForbidden()` (dòng 231–273), điều kiện lọc của nó:

| Dòng | Điều kiện | Ý nghĩa |
|---|---|---|
| 237–246 | đã có test 403 cho `op` | Bỏ qua, có sẵn rồi |
| 248–259 | không có test 401 nào | Bỏ qua, endpoint này không gác auth |
| 261–267 | tìm test 2xx có auth | Đây là ứng viên để đổi user |
| 269–271 | `handleCandidatesFor403(...)` | Cắt test tại chỗ 2xx, đổi sang user khác, chạy lại để lấy 403 |

**b. `hasPhaseTimedOut()` là lý do code ta đặt TRƯỚC các oracle khác.**
Cả 4 oracle chia chung 360s. Nếu `addForAccessControl()` chạy trước và ăn hết ngân sách thì oracle của ta
không bao giờ chạy. Run này là ví dụ ngược lại đang xảy ra thật: `addForInfoLeakage()` ở dòng 218 **đã bị
đói ngân sách** — timeout báo ở giây 360, pha kéo 6m10s, `report.json` không có fault 209 nào.

**c. Đây là toàn bộ phần ta sửa trong hàm này: 4 dòng.**
`git diff v6.1.1..HEAD` trên file này, hunk `@@ -137,6 +197,10 @@`:

```
+        if(!hasPhaseTimedOut()) {
+            addForStatefulAccessControl()
+        }
+
```

Không xoá dòng nào. Thân hàm còn lại y hệt v6.1.1.
