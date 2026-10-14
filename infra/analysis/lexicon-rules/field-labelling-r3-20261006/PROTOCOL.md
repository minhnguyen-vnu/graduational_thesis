# Gán nhãn mức operation, vòng 3 — protocol

Chốt 2026-10-06 khoảng 02:20, trước khi gán dòng nào của vòng này. Thay đổi sau khi chốt ghi ở §9. Lý do và lựa chọn:
`../council-20261005/DECISION.md`. Không sửa mã EvoMaster.

## 1. Dữ liệu

- Mọi operation ghi của vòng 1 và vòng 2: 3.972 op, 228 nhà cung cấp (`build_rows.py`, `rows.jsonl`, `rows/`, 53 khối
  75 op). Trường giữ nguyên như hai vòng trước; thêm `schema:` là tên `$ref` của body (1.590 op), vì EvoMaster đặt tên
  gene gốc của body theo tên này (`RestActionBuilderV3.kt:779`).
- Không có tập test chưa ai nhìn: phiên chính (L1) đã thấy nhãn và kết quả của mọi spec ở hai vòng trước. Ước lượng
  held-out lấy từ kiểm chéo nhóm theo nhà cung cấp (§6). Ghi đây là hạn chế.

## 2. Nhãn

Theo `GUIDE.md`: mỗi op một dòng `row_id,T,victim,role,order,sub`. Nhãn cũ mức trường không dùng.

## 3. Lượt gán

- L1: phiên chính (Claude Opus 5.5). L2: `claude -p --safe-mode`, model Sonnet 5.5, chỉ thấy `GUIDE.md` và `rows/`,
  mù với L1 và với mọi nhãn cũ.
- Phân xử: `claude -p --safe-mode`, Opus 5.5, phiên mới; mỗi dòng lệch được trình bày với hai nhãn đặt tên X/Y theo thứ
  tự ngẫu nhiên (seed `20261006`), không biết nhãn nào của ai; ghi nhãn chọn và một câu lý do cho từng dòng.
- Kappa trên T và trên cặp (T, victim, role) đúng hoàn toàn; tính trên nhãn gốc.

## 4. Luật dừng sớm

Sau khi cả hai lượt xong khối 001–005: kappa T dưới 0,6 thì dừng, ghi lệch luật, sửa `GUIDE.md`.

## 5. Rút từ

Tài liệu: chỉ trường trong op T = 1 (nhãn cuối), tên lá như hai vòng trước (`leaf`: phần sau dấu chấm cuối, bỏ `[]`).

| Danh sách | Dương | Âm |
|---|---|---|
| A-role (`:417`) | trường trong `role`, kiểu không phải boolean | trường khác của op T, trừ boolean |
| A-admin (`:104`) | trường boolean trong `role` | trường boolean khác của op T |
| C (`:414`, `:415`) | trường trong `victim` | trường khác của op T |
| B-low / B-high (`:418`, `:419`) | giá trị thấp nhất / cao nhất của `order` | giá trị khác cùng enum |

Ứng viên: tách tên lá gốc theo camelCase rồi theo ký tự không chữ-số, hạ chữ thường, bỏ đuôi `s` khi từ dài hơn 4 ký tự,
giữ token ≥ 4 ký tự; cộng nguyên tên lá dương (hạ chữ thường); cộng các từ viết tay của danh sách đó. Khớp như runtime:
tên lá chứa từ.

Đơn vị đếm là nhà cung cấp:
- `pos(w)`: số nhà cung cấp có ít nhất một trường dương chứa `w`.
- `any(w)`: số nhà cung cấp có ít nhất một trường (dương hoặc âm) chứa `w`.
- Giữ `w` khi `pos(w) ≥ 3`, `pos(w)/any(w) ≥ 0,5`, và `w` qua hai điều kiện đó ở ít nhất 70% của 200 lần bootstrap
  nhà cung cấp (seed `20261006`). Bỏ từ chứa một từ ngắn hơn đã giữ.

Cấu trúc giữ nguyên như runtime: C có ba tầng (từ cụ thể, rồi `email`, rồi `id`). `id` là luật cấu trúc, không qua luật
rút; `email` vào tầng 2 chỉ khi qua luật. B chỉ rút khi có ít nhất 15 enum có thứ tự từ ít nhất 10 nhà cung cấp; nếu
không, báo "corpus không đủ" và chỉ đo danh sách viết tay.

Báo thêm biến thể "chỉ corpus": cùng luật, không cộng từ viết tay vào ứng viên.

## 6. Đo

Mô phỏng runtime: `sim.py`, dựng từ `../council-20261005/A/work/w07_runtime_sim.py`. Giả định của mô phỏng ghi đầu file.
Chỉ số, khai trước:

| Mã | Chỉ số | Đơn vị |
|---|---|---|
| M1 | Transition được chọn là op T và danh sách vai trò khớp ít nhất một trường `role` của nó | API có ít nhất một op T có `role` |
| M2 | Báo nhầm: transition khả dụng được chọn nhưng API không có op T | API không có op T |
| M3 | Trường nạn nhân chọn đầu tiên nằm trong `victim` | op T có `victim` khác rỗng và khác `self` |
| M4 | Giá trị hạ quyền đứng đầu là giá trị thấp nhất của `order` | op T có `order` xếp được |
| M5 | Số op T = 0 được điểm transition 0,6 nhờ danh sách admin | op |

Kiểm chéo nhóm theo nhà cung cấp: 5 phần × 4 lần lặp (seed `20261006`). Mỗi phần: rút danh sách trên 4 phần còn lại,
đo M1–M5 trên phần giữ lại; gộp dự đoán giữ lại của một lần lặp. Lần lặp 1 là số chính; ba lần còn lại báo độ ổn định.
So viết tay với danh sách rút: McNemar chính xác hai phía, ghép đôi theo API (M1, M2) hoặc op (M3, M4); KTC 95%
bootstrap theo nhà cung cấp (2.000 lần) cho hiệu tỉ lệ.

Danh sách cuối: rút trên cả 228 nhà cung cấp bằng cùng luật. Nó không có số held-out riêng; kiểm chéo ước lượng cho
quy trình rút.

Neo trên target như vòng 2 (`../field-labelling-r2-20261004/PROTOCOL.md` §6), không phải held-out.

## 8. Đầu ra

`L1/`, `L2/`, `kappa.json`, `disagreements.csv`, `adjudication.csv`, `final.csv`, `lists/`, `cv.json`, `RESULTS.md`.

## 9. Thay đổi sau khi chốt

- Cách ghi của L1: L1 đọc trọn từng khối bằng Read, ghi các dòng khác mặc định vào `L1/raw/chunk-NNN.txt`; `expand.py`
  điền các op còn lại thành `T = 0` theo danh sách mã dòng của khối và từ chối mã dòng lạ. L2 ghi mọi dòng trực tiếp.
- L2 chạy theo lô 5 khối, mỗi lô một phiên `claude -p` mới (`scratchpad/r3L2/run.sh`); phiên không có Bash nên không tự
  đếm số dòng; `kappa.py` đếm dòng thiếu.
- Luật dừng §4 (`kappa.py 001,002,003,004,005`, chỉ in số tổng): 375 op, kappa T 0,749 (L1 16 T = 1, L2 26). Không dừng.
- Sau khi chốt, lúc chạy: số nhà cung cấp thật là 230 (không phải 228); L2 dừng ở khối 038 vì hết quota và chạy tiếp
  khối 039–053 lúc 06:52; người phân xử chỉ chọn X hoặc Y; giả định mô phỏng ghi ở `RESULTS.md` §8 vì luật không
  comment; thêm M1 phụ và thăm dò hậu kiểm, ghi rõ trong `RESULTS.md` §3, §5.
