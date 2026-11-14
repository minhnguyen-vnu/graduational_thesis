# Hồ sơ gán nhãn

Mỗi op ghi (POST, PUT, PATCH, DELETE) trong spec OpenAPI được gán một nhãn: T hoặc N. T là op hạ quyền, tức op đổi
vai trò hoặc thu hồi quyền của một tài khoản đã có. N là mọi op còn lại. Nhãn phần học dùng để học mô hình M2, nhãn
phần thi dùng để chấm M2.

## Kết quả

| | Học | Thi |
|---|---|---|
| API | 230 | 237 |
| Op ghi | 10.381 | 8.674 |
| Op người gán xem | 602 | 544 |
| Op T theo nhãn cuối | 209 | 153 |

M2 trên phần thi:

- M2 bắt được 117 trong 153 op T (76,5%, khoảng tin cậy 95%: 68,9–82,9%).
- M2 chọn 880 op, trong đó 763 op mang nhãn N.

Nhãn AI so với nhãn cuối, phần thi:

- Người gán xem hết 176 op có ít nhất một AI gọi T; 153 op trong số đó là T. Cả 132 op hai AI cùng gọi T đều là T.
  Trong 44 op một AI gọi T, AI kia gọi N, có 21 op là T.
- Trong 368 op hai AI cùng gọi N, bốc ngẫu nhiên cho người gán xem, không op nào là T. Từ mẫu này, số op T còn sót trong
  8.014 op chưa xem nằm trong khoảng 0–80 (khoảng tin cậy 95%).

`kiem-tra.py` tính lại mọi số trên từ hai bảng nhãn và ghi ra `ket-qua.txt`.

## Cách làm

1. Chia dữ liệu. Phần học gồm 230 API của bộ gán nhãn trước. Phần thi lấy mỗi công ty trên apis.guru chưa có trong phần
   học một API, chọn theo tên công ty trước khi mở spec: 365 API, trong đó 237 API có op ghi.
2. Hai AI gán cả 19.055 op theo cùng một phiếu (`phieu/phieu-cho-AI.md`): Claude Sonnet 5.5 và Claude Opus 5.5. Mỗi AI
   chạy một lượt riêng, không dùng tool, không thấy nhãn của AI kia.
3. Người gán xem 1.146 op theo `phieu/huong-dan-nguoi-gan.html`, không thấy nhãn AI.
   - Học: 66 op hai AI gán lệch nhau, 165 op hai AI cùng gọi T, 371 op hai AI cùng gọi N bốc ngẫu nhiên.
   - Thi: 176 op có ít nhất một AI gọi T, 368 op hai AI cùng gọi N bốc ngẫu nhiên.
4. Chốt nhãn cuối (cột `lay_theo`):
   - op người gán chưa xem: lấy nhãn hai AI, vì ở mọi op này hai AI gán giống nhau;
   - op người gán xem và khớp ít nhất một AI: lấy nhãn người gán;
   - op người gán khác cả hai AI (66 op học, 53 op thi): xem lại, chọn nhãn người gán, nhãn hai AI, nhãn Opus hoặc nhãn
     Sonnet.
5. Học M2 trên nhãn cuối phần học, rồi chấm M2 trên nhãn cuối phần thi. Điểm M2 của một op là tiên nghiệm cộng trọng số
   các dấu hiệu của op (từ trong path, tên trường, method) lấy từ `mo-hinh-M2.csv`. M2 chọn op khi điểm lớn hơn 0.

Ngoài T/N, nhãn T còn ghi trường vai trò và trường chỉ tài khoản bị hạ quyền. Hai nhãn cùng là T mà chọn khác trường
cũng tính là khác, nên có op ba nhãn đều là T vẫn phải xem lại.

### Ngoại lệ trong bảng

- Sau khi chấm M2, 44 op phần thi mà một AI gọi T, AI kia gọi N được xem lại lần nữa. 4 op đổi từ N sang T (`lay_theo`
  bắt đầu bằng "soát lại sau khi chấm M2"). Trước lần này phần thi có 149 op T và M2 bắt được 116.
- 8 op phần học hai AI cùng gọi T mà người gán chưa xem là ví dụ có lời giải trong hướng dẫn.
- 116 op phần thi có `ghi_chu` được để riêng trước khi bốc mẫu ngẫu nhiên, vì là các ứng viên đứng đầu của mô hình cũ
  P2f. Phép suy 0–80 op sót tính trên 8.014 op còn lại.

## File

| File | Nội dung |
|---|---|
| `nhan-hoc.csv` | 10.381 op phần học: nhãn hai AI, nhãn người gán, nhãn cuối |
| `nhan-thi.csv` | 8.674 op phần thi: như trên, thêm điểm M2 |
| `ket-qua.txt` | Các số ở mục Kết quả |
| `kiem-tra.py` | Tính lại `ket-qua.txt` từ hai bảng nhãn: `python3 kiem-tra.py` |
| `mo-hinh-M2.csv` | Mô hình M2, học từ nhãn cuối phần học |
| `phieu/` | Phiếu cho AI, hướng dẫn cho người gán |
| `goc/` | File gốc, chỉ cần khi đối chiếu: nội dung từng op, nhãn đầy đủ của AI và người gán, nhãn cuối kèm trường, phiếu xem lại |

## Cột của `nhan-hoc.csv` và `nhan-thi.csv`

| Cột | Nghĩa |
|---|---|
| `id`, `api` | Mã op, mã API |
| `method`, `path`, `mo_ta` | Op lấy từ spec |
| `AI_Sonnet`, `AI_Opus` | Nhãn của từng AI |
| `nguoi_gan` | Nhãn người gán; để trống khi người gán chưa xem |
| `nhan_cuoi` | Nhãn dùng để học hoặc chấm |
| `lay_theo` | Nhãn cuối lấy theo đâu (bước 4) |
| `diem_M2`, `M2_chon` | Chỉ có ở phần thi: điểm M2; "có" khi điểm lớn hơn 0 |
| `ghi_chu` | Chỉ có ở phần thi: đánh dấu 116 op để riêng |

Hai bảng nhãn dựng bằng `../build_ho_so.py` từ `../nop-hoi-dong/`.
