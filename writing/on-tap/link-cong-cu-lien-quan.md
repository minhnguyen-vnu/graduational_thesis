# Link các công cụ liên quan: RESTler, BACScan, GraphQLer

Mỗi công cụ ghi: link chính chủ, phần cần đọc, ý cần nắm. Các câu trích trong file này đã được đối chiếu đúng từng chữ với
bản gốc ngày 2026-11-22.

## 1. RESTler (Microsoft)

| Là gì | Link |
|---|---|
| Repo chính thức | https://github.com/microsoft/restler-fuzzer |
| README, mục "RESTler is described in these peer-reviewed research papers" | https://github.com/microsoft/restler-fuzzer#readme |
| Danh sách checker của bản hiện tại (commit gần nhất `6bf6af653d`, 2023-04-26) | https://github.com/microsoft/restler-fuzzer/blob/main/docs/user-guide/Checkers.md |
| Bài ICSE 2019, bài luận văn trích là [15]; PDF trên trang đồng tác giả Patrice Godefroid, README trỏ tới | https://patricegodefroid.github.io/public_psfiles/icse2019.pdf |
| Bài ICST 2020, mở rộng RESTler bằng các luật bảo mật | https://patricegodefroid.github.io/public_psfiles/icst2020.pdf |
| Trang bài ICSE 2019 trên Microsoft Research | https://www.microsoft.com/en-us/research/publication/restler-stateful-rest-api-fuzzing/ |

Đọc:
- ICSE 2019: Abstract và mục "B. Current Limitations".
- ICST 2020: Abstract và danh sách 4 luật ở trang 1.
- Checkers.md: chỉ lướt tên các checker.

Nắm:
- ICSE 2019 sinh chuỗi request có trạng thái và chỉ báo lỗi 500: *"RESTler reports each bug, currently defined as a
  500 HTTP status code"*. Bài này không có chữ "checker".
- ICST 2020 có 4 luật: use-after-free, resource-leak, resource-hierarchy, user-namespace. Bài gọi RESTler là
  "stateful REST API fuzzing [5]": *"Our work extends stateful REST API fuzzing [5]."*
  - Use-after-free: *"A resource that has been deleted must no longer be accessible."* Cái thay đổi là tài nguyên.
  - User-namespace: *"A resource created in a user namespace must not be accessible from another user namespace."*
    Đây là người khác, cùng một thời điểm.
- `NameSpaceRuleChecker` mặc định tắt: *"Will then attempt to use that resource as a different, unauthorized
  (attacker) user."*
- Không luật và không checker nào hạ quyền rồi dùng lại token cũ của cùng một người.

## 2. BACScan (CCS 2025)

| Là gì | Link |
|---|---|
| Trang bài trên ACM, nơi xuất bản chính thức (cần trả phí) | https://doi.org/10.1145/3719027.3744825 |
| PDF trên trang đồng tác giả Yuan Zhang (Fudan) | https://yuanxzhang.github.io/paper/bacscan-ccs25.pdf |
| Bản sao ở lab CUHK của đồng tác giả Wei Meng | https://seclab.cse.cuhk.edu.hk/papers/ccs25-BACScan.pdf |

Bài không có link tới mã nguồn của BACScan.

Đọc: Abstract; §3 Overview và đoạn đầu §3.1 "MBAC Detection Oracle"; §5.1, đoạn "BACScan Setup".

Nắm:
- Đối tượng là web app, không phải REST API: *"a novel black-box approach to detect BAC vulnerabilities in web
  applications"*.
- Cơ chế: *"replay modification requests using an attacker's session and verify if unauthorized changes to data
  occur"*; sau đó mở trang trạng thái để xem dữ liệu có bị đổi không.
- Các user cố định từ đầu: *"Among the two victim users, one shares the same role as the attacker user (e.g., a
  regular user), while the other has a higher role (e.g., an administrator)."*
- Đây là lỗi giữa hai người ở cùng một thời điểm. Không có bước hạ quyền, không dùng lại token cũ.

## 3. GraphQLer (arXiv:2504.13358v2, ASE 2026)

| Là gì | Link |
|---|---|
| Trang arXiv | https://arxiv.org/abs/2504.13358v2 |
| PDF | https://arxiv.org/pdf/2504.13358v2 |
| Mã nguồn, theo chú thích 1 của bài | https://github.com/omar2535/GraphQLer |

Đọc: Abstract; §1 Introduction; cuối §3, hai đoạn "IDOR Chain Strategy" và "UAF Chain Strategy"; §5.4 nếu cần số
liệu.

Nắm:
- Đối tượng là API GraphQL, không phải REST.
- IDOR chain: *"Qualifying chains are replayed with the CREATE step under the primary credential and all subsequent
  steps under the secondary credential."* Đây là người khác.
- UAF chain: tạo, xoá, rồi đọc. Cái thay đổi là tài nguyên.
- Không chuỗi nào hạ quyền của cùng một người rồi dùng lại token cũ.

## 4. So với MR-A1 trên reports-api

| | Chuỗi | Báo lỗi khi | Cái thay đổi |
|---|---|---|---|
| RESTler use-after-free, GraphQLer UAF | `POST /reports` → `DELETE /reports/1` → `GET /reports/1` | Bước cuối 200 | Tài nguyên |
| RESTler user-namespace, GraphQLer IDOR, BACScan, Şahin | alice tạo `/reports/1` → bob dùng token của bob gọi `/reports/1` | bob nhận 200 | Người gọi |
| MR-A1 (970) | alice `PUT /reports/1` 200 → superadmin hạ alice xuống VIEWER → alice `PUT /reports/1` bằng token cũ | Vẫn 200 | Quyền của chính alice |

Chưa chạy RESTler, BACScan hay GraphQLer. So sánh dựa trên bài báo và tài liệu của chính họ. EvoMaster bản upstream
đã chạy: `infra/em-results/upstream-master-t1-20261018/RESULTS.md` (0/20 lỗi loại A1 trên reports-api bản lỗi).
