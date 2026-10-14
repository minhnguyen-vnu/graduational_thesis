# Thiết kế: Đầu dò đăng nhập lại (re-login probe)

> **Trạng thái: BẢN THIẾT KẾ ĐỂ DUYỆT — chưa viết một dòng code nào.**
> Ngày 23/08/2026. Cần duyệt trước khi hiện thực.

---

## 1. Vấn đề: ba chỗ hiện đang ĐOÁN thay vì ĐO

Công cụ hiện tại dựa vào ba suy đoán từ đặc tả OpenAPI. Cả ba đều đã lộ điểm yếu:

| # | Hiện tại đoán bằng gì | Hỏng ở đâu (đã có bằng chứng) |
|---|---|---|
| **Đ1** | Giá trị "vai trò thấp" lấy từ **enum chuỗi** trong đặc tả (`harvestReducedRoleValue`) | pyLoad khai `role: integer` → không có enum → **thoát toàn bộ tính năng**. Xác nhận bằng lần chạy chẩn đoán 23/08: đúng 1 dòng log, `no reduced role value in the schema vocabulary` |
| **Đ2** | Phép chuyển đổi có thật sự **giảm** quyền hay không → đoán từ **tên endpoint** (`looksLikePermissionReducingTransition`) | Seed 15 của Tier-2: quá trình tìm kiếm **THĂNG** quyền `name1` lên admin qua đúng endpoint đó. Tên đúng, ngữ nghĩa ngược |
| **Đ3** | Hành động canh gác có bị chặn theo **vai trò** hay không → đoán từ "đã từng có ai bị 403 ở đây" + "phải là lệnh ghi" | Không phân biệt được **chặn theo vai trò** và **chặn theo chủ sở hữu**. Hệ quả kéo theo: phải loại bỏ mọi `GET`, kể cả `GET` chỉ-admin hợp lệ |

Ba suy đoán này độc lập nhau nhưng **cùng một bản chất**: ta hỏi *đặc tả* một câu mà chỉ có *hệ thống đang chạy* mới trả lời được.

## 2. Ý tưởng

Thay vì đoán, **hỏi thẳng hệ thống** bằng một lần đăng nhập lại:

> Sau khi áp dụng phép chuyển đổi, cho nạn nhân **đăng nhập lại để lấy credential MỚI**, rồi thử lại
> đúng hành động canh gác đó.
>
> - Credential **mới** bị **403** ⇒ quyền **thật sự** đã bị gỡ, **và** hành động này **thật sự** bị
>   chặn bởi quyền đó. Tiền đề được xác lập bằng quan sát.
> - Credential **mới** vẫn **2xx** ⇒ hoặc phép chuyển đổi chẳng giảm gì, hoặc hành động này không bị
>   chặn bởi thứ vừa bị gỡ. **VÔ HIỆU** — không kết luận gì.

## 3. Vì sao KHÔNG vòng quanh

Đây là điểm phải bảo vệ được trước phản biện.

| | Câu hỏi | Credential dùng |
|---|---|---|
| **Đầu dò** | Quyền có thật sự bị gỡ không? | **MỚI** (cấp sau khi hạ quyền) |
| **Oracle** | Credential **CŨ** có bị bỏ qua kiểm tra không? | **CŨ** (cấp trước khi hạ quyền) |

Hai câu hỏi khác nhau, trên hai credential khác nhau. Đầu dò xác lập **tiền đề**; oracle kiểm **lỗi**.

**Và nó vẫn hoạt động trên ứng dụng ĐANG DÍNH LỖI** — đây là chỗ mấu chốt. Lớp lỗi ta nhắm tới
(CWE-613) có bản chất là *credential chụp ảnh quyền tại thời điểm cấp phát*. Nên một lần đăng nhập
**mới** luôn phản ánh quyền **hiện tại**. Đã kiểm chứng cơ chế này đúng trên cả ba hệ thống:

- `reports-api`: role nằm trong JWT, cấp lúc đăng nhập → token mới mang VIEWER → 403 ✅
- `vampi-seeded`: login chụp `admin` claim vào JWT → token mới mang `admin=False` → 403 ✅
- `pyLoad`: `set_session()` chép role/permission vào session lúc đăng nhập → session mới mang role mới → 403 ✅

## 4. Bảng phán quyết

Một lần chuyển đổi cho **cả hai** câu trả lời, không cần chuyển đổi thêm lần nữa:

| Thử lại bằng credential **CŨ** | Đầu dò bằng credential **MỚI** | Phán quyết |
|---|---|---|
| 403 | 403 | 🟢 **ĐẠT** — thực thi đúng |
| **2xx** | **403** | 🔴 **LỖI (970)** — credential cũ vượt rào, credential mới thì không |
| 2xx | 2xx | ⚪ **VÔ HIỆU** — hành động không bị chặn bởi thứ vừa gỡ, hoặc chuyển đổi không giảm gì |
| 403 | 2xx | ⚪ **VÔ HIỆU** — bất thường, không kết luận |
| bất kỳ | **401** | ⚪ **VÔ HIỆU** — nạn nhân không đăng nhập lại được (đã bị xoá) |

Hàng thứ ba chính là **đường báo động giả** mà ba suy đoán ở §1 đang cố chặn bằng cảm tính. Từ nay nó
bị chặn bằng **phép đo**.

## 5. Thứ tự thực hiện — quan trọng và không hiển nhiên

```
1. reset (nếu có)
2. nạn nhân đăng nhập  → credential CŨ
3. hành động canh gác bằng credential CŨ        → kỳ vọng 2xx
4. người thao tác áp dụng phép chuyển đổi
5. hành động canh gác bằng credential CŨ lần nữa → ⬅ LÀM TRƯỚC
6. nạn nhân ĐĂNG NHẬP LẠI → credential MỚI
7. hành động canh gác bằng credential MỚI        → ⬅ ĐẦU DÒ, làm SAU
```

**Bước 5 phải đứng trước bước 6.** Lý do: một số hệ thống chỉ cho phép một phiên đăng nhập tại một
thời điểm, nên việc đăng nhập lại có thể **huỷ credential cũ**. Nếu đầu dò chạy trước, credential cũ
có thể chết và bước thử lại đọc ra 401 = KHÔNG KẾT LUẬN ĐƯỢC — tức là **tự tay phá huỷ phép thử của
chính mình**, đúng loại lỗi §6 của CLAUDE.md đang mô tả. Đặt đầu dò sau thì rủi ro này bằng 0.

## 6. Cơ chế kỹ thuật — đầu dò là một individual RIÊNG

Không thể nhét "đăng nhập lại" vào giữa một individual, vì EvoMaster đăng nhập **một lần, ngay đầu
mỗi test**, rồi mọi hành động dùng chung map `tên người dùng → token` (CLAUDE.md §7.8).

Nhưng chính đặc tính đó lại cho ta lời giải **miễn phí**: chạy đầu dò như một **individual thứ hai**.

Đã kiểm chứng trong mã nguồn (23/08):
- `BlackBoxRestFitness` dòng 52–54 gọi `AuthUtils.getCookies` / `getTokens` ở **mỗi lần** chạy một individual
- `getTokens` dựng một map **mới** và thực hiện **lời gọi đăng nhập thật** cho từng người dùng có mặt trong individual đó
- kết quả `putAll` đè lên map đang giữ → credential của nạn nhân được **làm mới**

⇒ Chỉ cần dựng một individual thứ hai chỉ chứa `[hành động canh gác, auth = nạn nhân]` và chạy nó qua
`fitness.computeWholeAchievedCoverageForPostProcessing(...)` ngay sau bộ ba. Credential mới đến tự
động, **không phải đụng một dòng nào vào tầng xác thực**.

> Đây chính là đặc tính "EvoMaster đăng nhập lại ở mỗi test" mà luận văn đang dùng để giải thích **vì
> sao đối chuẩn không dựng nổi A1**. Ở đây nó đổi vai từ trở ngại thành công cụ — một chi tiết đáng
> viết vào luận văn.

## 7. Ba thay đổi kéo theo

### 7.1 `harvestReducedRoleValue` → trả về DANH SÁCH ứng viên, không phải một giá trị

Hiện tại: chỉ đọc `EnumGene`, trả một giá trị, `null` thì thoát.

Đề xuất: sinh danh sách giá trị ứng viên theo thứ tự ưu tiên, và **để đầu dò chọn cái đúng**:

1. enum chuỗi khớp từ vựng quyền thấp (giữ nguyên hành vi cũ → **không phá số liệu cũ**)
2. các giá trị enum còn lại
3. với tham số **kiểu số**: các giá trị nhỏ trong miền (0, 1, 2) — **không đoán chiều nào là thấp**,
   thử lần lượt và để đầu dò xác nhận
4. với tham số **kiểu chuỗi không enum**: từ vựng quyền thấp mặc định (`user`, `viewer`, `guest`, `member`)

Đây là chỗ gỡ **Đ1** — và cũng là chỗ gỡ được pyLoad.

### 7.2 Cho phép `POST` làm hành động nguồn khi **không** khai báo

Hiện `POST` chỉ được nhận ở chế độ khai báo. Lập luận biện minh **đã có sẵn trong comment của code**:
một `POST` thật sự "tiêu thụ" sẽ tự làm hỏng bước thử lại của chính nó và bị loại thành VÔ HIỆU, nên
không làm yếu độ chính xác. Có đầu dò rồi thì lập luận này còn chắc hơn nữa.

Đây là rào cản thứ hai của pyLoad (`/json/*` chỉ có `POST`/`GET`).

### 7.3 Nhận lại `GET` làm hành động canh gác

Khi đã có đầu dò thì quy tắc "chỉ nhận lệnh ghi" trở nên **thừa và có hại**: nó chỉ là cách gián tiếp
để né chuyện chặn-theo-chủ-sở-hữu, mà đầu dò xử lý chuyện đó **trực tiếp và chính xác hơn**.

- `GET` chỉ-admin → credential mới bị 403 → **nhận** (hiện đang bỏ sót)
- `PUT` chặn theo chủ sở hữu → credential mới vẫn 2xx (vẫn là đồ của mình) → **loại** (hiện đang nhận nhầm)

Nên thay đổi này **vừa tăng recall vừa tăng precision** — đúng chỗ trả lời câu hỏi về `GET` chỉ-admin.

## 8. Chi phí và ràng buộc

| Khoản | Đánh giá |
|---|---|
| **Số request thêm** | 1 đăng nhập + 1 hành động cho mỗi lần thử. Nhỏ so với ngân sách pha bảo mật |
| **Trần số lần thử** | Phải giữ. Mỗi lần thử **tiêu mất một nạn nhân** (chuyển đổi đã áp dụng rồi) |
| ⚠️ **Không có endpoint reset thì gần như chỉ được thử MỘT lần** | Sau lần chuyển đổi đầu tiên, nạn nhân đã bị hạ quyền vĩnh viễn. Thử giá trị ứng viên thứ hai đòi hỏi trạng thái sạch. **Đây là ràng buộc nghiêm trọng nhất của thiết kế này** |
| **Hệ quả** | Danh sách ứng viên ở §7.1 phải **xếp thứ tự tốt**, vì thường chỉ bắn được một phát. Với hệ thống có endpoint reset thì lặp thoải mái |

## 9. Giới hạn còn lại (phải ghi vào luận văn)

1. **Đầu dò giả định đăng nhập lại thì nhận quyền hiện tại.** Nếu một hệ thống hỏng tới mức
   **cả credential mới cũng giữ quyền cũ**, đầu dò sẽ nói "chưa giảm" và ta **bỏ sót** (FN, không phải FP).
   Đó là một lớp lỗi khác, và quan hệ MR-A1 cũng không áp dụng sạch sẽ ở đó.
2. **Không tự sinh ra được người thao tác còn quyền.** Nếu pha tìm kiếm đã hạ quyền toàn bộ tài khoản
   thì vẫn bó tay — đúng hạn chế ① của mục 8 báo cáo, thiết kế này không đụng tới.
3. **Ràng buộc "chỉ thử được một lần" ở §8** khi hệ thống không có endpoint reset.

## 10. Kế hoạch đo lại (bắt buộc, vì code đổi thì mọi số cũ hết hiệu lực)

1. **Trước tiên** chạy `regression_check.sh` (21 dòng) — thay đổi §7.1 giữ nguyên nhánh enum nên
   **kỳ vọng 21/21 tái lập**; nếu lệch là thiết kế đã vô tình nới điều kiện tiền đề.
2. Chạy lại 4 nhánh Tier-1 / Tier-2 (80 lần chạy, ~7 tiếng, chạy qua đêm bằng `nohup`).
3. Chạy Tier-2b **suy luận tự động + đặc tả đầy đủ, KHÔNG khai báo** — đây là phép đo mới quan trọng
   nhất: nó trả lời *"công cụ có tự bắt được một CVE thật không?"*
4. So sánh từng cặp với số cũ, báo cáo cả chỗ tăng lẫn chỗ giảm.

**Điểm quay lui:** jar đóng băng `evomaster-frozen-769c16d.jar` — khôi phục bằng một lệnh `cp` nếu
kết quả xấu đi.
