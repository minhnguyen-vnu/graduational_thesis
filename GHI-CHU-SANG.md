# Đêm 2026-09-21 — làm gì, cần bạn quyết gì

## Số quan trọng nhất

Trên nửa test, cách chọn transition **hôm nay** (`RestSecurityBuilder.kt:809`, `firstOrNull` sau khi
sắp theo verb) chọn đúng endpoint `R` ở **0 trong 6 spec**. Số này sạch: 8 từ path và 9 từ tham số
cứng trong code chưa bao giờ được chỉnh theo corpus này.

| Cách chọn transition | top-1 | top-3 | top-8 |
|---|---|---|---|
| hôm nay, `firstOrNull` | 0.000 | — | — |
| xếp hạng, bộ từ rút từ train cũ (26 `R`, 5 nhà cung cấp) | 0.167 | 0.500 | 0.833 |
| xếp hạng, bộ từ rút từ train mở rộng (39 `R`, 11 nhà cung cấp) | **0.667** | **1.000** | **1.000** |

Ba hàng trên xếp hạng trên các dòng đã giữ của mỗi spec, tối đa 36. Lúc chạy thật EvoMaster xếp trên
mọi endpoint ghi: S210 có 451, S116 có 161. Sau khi gán bù 41 dòng xếp trên (`sampling-plan.md` §1h),
hạng trên toàn bộ là **chính xác**, không còn là khoảng:

| Nửa test, trên mọi endpoint | top-1 | top-3 | top-8 |
|---|---|---|---|
| bộ từ mới | **0.500** | **0.833** | **1.000** |

Mọi spec test có endpoint `R` trong 8 ứng viên đầu, không phải trong 3. Đó là lý do giữ
`MAX_TRANSITION_CANDIDATES = 8` trong patch — quyết định số 2 dưới đây đã có câu trả lời.

Luật tính điểm viết lúc 00:02 và không sửa một chữ nào sau đó. Chỉ dữ liệu train đổi.

Đo trên cùng bộ nhãn test, cải thiện chia gần đôi: sửa lỗi trích xuất envelope JSON:API góp
`0.167 → 0.333`, thêm 15 spec vào nửa train góp `0.333 → 0.667`.

Từ cứu được hai spec mà lần trước không từ nào bắt được là `collaborators`, học từ 2 dòng `R` của
`github.com` ở nửa train, dùng được ở `flat.io` và `gitea.io` của nửa test. Đây là chỗ duy nhất có
một từ học ở nhà cung cấp này áp được sang nhà cung cấp khác.

Chi tiết: `infra/analysis/lexicon-rules/lexicon-20260921/RESULTS.md`.

## Bốn quyết định đang chờ bạn

1. **Duyệt patch nháp** `infra/evomaster-ext/wip/lexicon-rank-20260921.patch` (+56/−21,
   `git apply --check` đã qua). Mô tả và hai chỗ cần soi ở file `.md` cùng tên. Chưa áp, chưa build.
2. ~~Giới hạn ứng viên~~ — đã trả lời: giữ 8. Hạ xuống 3 mất một trong sáu spec test.
3. **Lượt người trên phần mở rộng.** 253 dòng mới chỉ có nhãn hai máy đồng thuận, không ai soát.
   Có muốn tự soát một tầng mẫu như lần trước không.
4. **Cột `op giữ` trong `corpus/sampling-plan.md` §2 ghi 15 nhưng file `S*.csv` giữ tới 36 dòng.**
   Cần đối chiếu lại. Không ảnh hưởng con số nào đã báo.

## Đã làm đêm qua

| Việc | Ở đâu |
|---|---|
| §12 công thức điểm, viết 00:02 trước khi có script | `rules-draft.md` §12 |
| Luật xử lý phần mở rộng, viết 00:28 trước khi thấy lượt L1 | `corpus/sampling-plan.md` §1g |
| Sửa `extract_ops.py` bóc envelope JSON:API; 17 dòng S131 đổi | `corpus/sampling-plan.md` §1f |
| Bốc thêm 15 spec vào nửa train, seed `20260921` | `corpus/sampling-plan.md` §1e |
| Hai lượt máy mù trên 266 dòng, kappa 0.742, giữ 253 loại 13 | `lexicon-rules/labelling-r3/` |
| Rút lại bộ từ vựng, đo lại | `lexicon-20260921/RESULTS.md` |
| Patch nháp + self-test 6 kiểm tra | `evomaster-ext/wip/`, `selftest/lexicon-rank.sh` |

## Chưa làm, và vì sao

- Chưa build, chưa chạy self-test, chưa qua cổng hồi quy. Luật là phải có OK của bạn trước.
- Không có lượt người nào trên 253 dòng mới. Không ai phân xử 13 dòng bị loại: `sampling-plan.md` §1g
  chọn loại thay vì để mô hình gán, vì `rules-changelog.md` đã ghi một lần mô hình phân xử thay người rồi.
- Nửa test đã bị dùng để phát triển từ 09-20 (`rules-draft.md` §12.5). Con số mục trên sạch hơn con số
  hôm qua vì luật đã đóng băng trước khi corpus mở rộng, nhưng vẫn không phải ước lượng trên dữ liệu
  chưa ai nhìn.
- Một hạn chế cũ nay sai: "hai lượt máy dùng kiến thức ngoài spec, chứng cứ S131-0097 và S131-0100".
  Sau khi bóc envelope, hai dòng đó ra `N` và `R`. Đó là lỗi trích xuất của ta, không phải lỗi người gán.
