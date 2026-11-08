# Bản đồ lập luận

Mỗi khẳng định của luận văn một mục: con số, đối chứng, trường hợp không do ta viết, giới hạn. Số trích từ file
nguồn ghi bên cạnh; con số nào không có nguồn thì không vào luận văn.

Jar chính: `M2` (`evomaster-M2-917c57dd.jar`, mọi số ở `docs/results.md`, chạy 2026-11-08). Hàng nào mang số của jar
khác thì ghi tên jar ở đầu hàng.

## K1. Khi dựng được bộ ba hợp lệ, oracle phán đúng

| | |
|---|---|
| Con số, jar `M2` | Mọi bộ ba dựng được trên bản lỗi đều ra 970 (19/19, 7/7, 5/5, 5/5); 0 FP trong 48 lượt bản đã vá, trên 30 bộ ba thực hiện trên mã đã vá (`docs/results.md` §1, §1a) |
| Đối chứng | Mỗi target có bản đã vá chỉ khác đúng chỗ lỗi; bộ ba trên bản đã vá đọc `200/200/403`. Bản vá của artifact-keeper là của vendor |
| Giới hạn | Bản vá của artifact-keeper trả 401 cho token cũ, nên 3 lượt không dựng được bộ ba: không báo nhầm, cũng không có TN. "Phát hiện khi có bộ ba hợp lệ" gần như định nghĩa, không trích làm độ chính xác (`docs/results.md` §2) |

## K2. Oracle bắt được lỗi thật

| | |
|---|---|
| Con số, jar `M2` | pyLoad CVE-2026-41133: bản lỗi 5/5, bản vá 0/5, Fisher một phía p = 0,004. artifact-keeper, lỗi vendor #1821: bản lỗi 5/5, bản vá của vendor 0/3, p = 0,018 (`docs/results.md` §1) |
| Đối chứng | pyLoad: bản vá do ta viết. artifact-keeper: bản vá của vendor `e64cc5c608` |
| Không do ta viết | pyLoad: lỗi của pyLoad, upstream chưa vá; bản đối chứng, endpoint reseed và spec `/json/*` là của ta (`docs/tier2b-pyload-target.md` §3). artifact-keeper: lỗi, bản vá, mã app và spec là của vendor; ta chỉ bỏ `DELETE /users/{id}` khỏi spec và chỉnh cách dựng container (`docs/artifact-keeper-target.md` §2) |
| Giới hạn | Một CVE và một lỗi vendor. Cả hai là target phát triển: năm bản sửa builder được viết khi chạy pyLoad (`docs/tier2b-pyload-target.md` §5), ba khi chạy artifact-keeper, mã và mô hình không chứa chuỗi nào của app (`docs/results.md` §5); số của hai target không nói gì về recall trên app lạ. |

## K3. Tool tự tìm transition, không cần người khai

| | |
|---|---|
| Con số, mô hình `M2` | Trên nửa thi của corpus gán nhãn lại (237 spec, 8.674 op ghi, 153 op T): 117 op T có điểm dương (76,5%, Clopper–Pearson 68,9–82,9%); 763 trong 880 op điểm dương mang nhãn N (`docs/results.md` §7). Trên target, xếp từ spec tĩnh: op T hạng 1 ở reports-api, vampi-seeded, pyLoad; hạng 4 trong 5 op khả dụng ở artifact-keeper (`lexicon-rules/m2-model-20261107/compare_targets.out`) |
| Con số, mô hình `M1` (jar `P2e`, `P2f`) | Kiểm chéo theo nhà cung cấp 5 phần × 4 lần lặp: op T đứng đầu ở 16–18, trong 4 đầu ở 21–25 của 47 spec test (`infra/evomaster-ext/wip/p2-design-20261012.md` §1) |
| Con số, bộ từ vựng (jar `L` tới `AF2`) | Endpoint `R` hạng 1 ở 4 trong 6 spec test, top-8 ở 6 (`docs/lexicon.md` §7). Bộ từ viết tay trước jar `L` (8 từ path + 9 từ param, `firstOrNull`): 0 trong 6 |
| Đối chứng | Đổi cách chấm không mất phát hiện nào: từ vựng (AF2) sang M1 (P2f) trùng từng seed ở mọi ô 970; M1 sang M2 trùng 90/90 hàng; artifact-keeper 5/5 trên AF2, P2f và M2 (`docs/results.md` §6) |
| Không do ta viết | pyLoad và artifact-keeper: builder tự chọn transition từ spec, không khai báo. |
| Giới hạn | 47 spec test của M1 đã bị nhìn nhiều lần: số là thăm dò. Điểm dương chỉ chọn ứng viên. Đường dẫn `/role` của vampi-seeded do ta đặt. |

## K4. Recall thấp có nguyên nhân đo được

| | |
|---|---|
| Con số, jar `M2` | Mọi FN là lượt không dựng được bộ ba; 0 FN có bộ ba (`docs/results.md` §1a). vampi-seeded 7/20 |
| Giới hạn | Giới hạn nằm ở bước search dựng bộ ba. Search phá điều kiện tiền đề: hạ quyền làm source 403, xoá tài khoản nạn nhân (`docs/results.md` §7) |

## Ranh giới phải viết

1. Transition phải gọi được bằng HTTP.
2. Sau transition phải cấp được chứng chỉ mới để so. Lỗi dạng xoá chủ thể không có chứng chỉ mới.
3. Lỗi mà đăng nhập mới cũng không bị từ chối thì C4 loại, đúng thiết kế (`docs/metamorphic-authz-relations.md` §5.6).
4. Từ chối phải là 403. Bản vá trả 401 (artifact-keeper) cho ra bộ ba VOID (`docs/results.md` §1).

## Câu hỏi người chấm dễ hỏi, trả lời ở đâu

| Câu hỏi | Trả lời |
|---|---|
| Chỉ một CVE, có phải may? | K2: thêm một lỗi vendor có bản vá của vendor |
| Sao chỉ bốn app? | Hai lỗi gieo đo trên mã ta kiểm soát; hai lỗi thật có bản vá để đếm FP. Không khẳng định recall trên app lạ (K2 giới hạn) |
| artifact-keeper có phải cài cắm? | Mã app, lỗi, bản vá là của vendor; mã công cụ không chứa chuỗi nào của app; nhưng là target phát triển (K2 giới hạn) |
| Mô hình có quá khớp? | M2 đo trên nửa thi chưa dùng để học (K3); số kiểm chéo của M1 là thăm dò |
| Vì sao vampi-seeded thấp? | K4 |
| 0 FP có ý nghĩa không? | 48 lượt, trên 30 bộ ba thực hiện trên mã đã vá (K1) |
