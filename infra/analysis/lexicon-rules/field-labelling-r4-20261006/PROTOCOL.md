# Gán nhãn mức operation, vòng 4 — protocol

Chốt 2026-10-06 khoảng 23:35, trước khi gán dòng nào của vòng này. Hướng: `../field-identification-direction-20261006.md`.
Không sửa mã EvoMaster. Thay đổi sau khi chốt ghi ở §9.

## 1. Dữ liệu

- 230 API của vòng 3 có 10.381 operation ghi. Vòng 3 đã gán 3.972 (`../field-labelling-r3-20261006/final.csv`). Vòng
  4 gán 6.409 op còn lại, thuộc 74 API có hơn 36 op ghi (`build_rows.py`, `rows-new.jsonl`, `rows/`, 86 khối 75 op).
- Mã dòng mới `Sxxx-Nnnnn`, `nnnn` là vị trí op trong spec (thứ tự path rồi method, `extract_fields.ops_of`).
- Trích trường giống hệt vòng 1–3 (`extract_fields.fields_of`); có `schema:` như vòng 3.
- Thứ tự khối: các API xáo theo seed `20261006`, op của một API nằm liền nhau. Ba lượt gán đi cùng thứ tự.

## 2. Nhãn

`GUIDE.md`, chép nguyên từ vòng 3. Mỗi op một dòng `row_id,T,victim,role,order,sub`.

## 3. Lượt gán

| Lượt | Ai | Thấy gì |
|---|---|---|
| LA | `claude -p --safe-mode --model claude-sonnet-5-5 --effort high`, mỗi phiên 5 khối | chỉ `GUIDE.md`, `rows/` trong thư mục riêng |
| LB | `claude -p --safe-mode --model claude-opus-5-5 --effort medium`, mỗi phiên 5 khối | như LA |
| LM | phiên chính (Opus 5.5, effort xhigh) | đã thấy nhãn, kết quả vòng 1–3 và tranh luận về chúng |

LA, LB ghi mọi dòng. LM ghi dòng khác mặc định vào `LM/raw/`, `expand.py` điền `T = 0` cho phần còn lại và từ chối mã
dòng lạ (như L1 vòng 3).

## 4. Gộp nhãn

- `T` cuối: đa số trong ba lượt. Op chỉ có hai lượt mà hai lượt lệch nhau: phân xử. Op có dưới hai lượt: xem §7.
- Với op `T` cuối = 1, từng cột `victim`, `role`, `order`: đa số trong các lượt gán `T = 1` (so sau khi tách `|`,
  bỏ khoảng trắng, sắp xếp). Không có đa số: phân xử.
- Phân xử: một phiên `claude -p --safe-mode` Opus 5.5 mới, thấy op và các phương án đặt tên X/Y/Z theo thứ tự xáo
  (seed `20261006`), không biết phương án của ai; chọn một phương án và ghi một câu lý do.
- Kappa: Fleiss trên `T` cho ba lượt; Cohen từng cặp.

## 5. Luật dừng sớm

Khi cả ba lượt xong khối 001–005: Fleiss kappa `T` dưới 0,6 thì dừng gán, ghi lệch luật, và dùng danh sách vòng 3.

## 6. Rút và đo

Tài liệu rút: nhãn cuối của 3.972 op vòng 3 cộng op vòng 4 (§7).

Luật rút: `../field-labelling-r3-20261006/PROTOCOL.md` §5, nguyên văn, trừ một điểm: ứng viên là token tách từ tên lá
dương (camelCase, rồi ký tự không chữ-số, hạ chữ thường, bỏ đuôi `s` khi dài hơn 4, giữ token ≥ 4 ký tự), cộng
nguyên tên lá dương, cộng thuật ngữ chuẩn dưới đây qua cùng phép tách; **không cộng từ viết tay**.

- SCIM RFC 7643 §4.1 (User): userName, name, displayName, nickName, profileUrl, title, userType, preferredLanguage,
  locale, timezone, active, password, emails, phoneNumbers, ims, photos, addresses, groups, entitlements, roles,
  x509Certificates; §4.2 (Group): displayName, members.
- BSR INCITS 359 Draft §6.1: user, role, permission, session, operation, object.

Cờ admin (`:104`) và trường vai trò (`:417`) cùng luật, tách theo kiểu boolean như vòng 3. Thấp/cao (`:418`, `:419`)
chỉ rút khi có ≥ 15 enum có thứ tự từ ≥ 10 nhà cung cấp; không đủ thì báo "corpus không đủ", danh sách viết tay giữ
nguyên và được ghi là phần viết tay còn lại, kèm độ phủ trên corpus.

Báo thêm, không dùng để chọn: biến thể cộng từ viết tay vào ứng viên (như vòng 3).

Đo: `sim.py` vòng 3, với một thay đổi: thứ tự op trong một API là vị trí op trong spec (`pos`). Chỉ số M1–M5, kiểm
chéo nhóm theo nhà cung cấp 5 phần × 4 lần lặp (seed `20261006`, lần 1 là số chính), McNemar chính xác hai phía ghép
đôi, KTC 95% bootstrap theo nhà cung cấp 2.000 lần. So: danh sách rút vòng 4, bộ viết tay, danh sách vòng 3. Neo trên
6 target như vòng 3.

**Dùng:** danh sách rút trên toàn bộ dữ liệu là kết quả của vòng này, dù số đo thế nào. Không đổi luật sau khi thấy số.

## 7. Hạn chót

Gán dừng lúc 2026-10-07 09:00. API nào còn op có dưới hai lượt gán thì cả API đó quay về tập op vòng 3 (bỏ op vòng 4
của nó). Ghi số API bị quay về.

Hết quota giữa chừng: các lượt `claude -p` tự thử lại mỗi 10 phút; phiên chính được đánh thức lại bằng lịch định kỳ.

## 8. Đầu ra

`LA/`, `LB/`, `LM/`, `kappa.json`, `disagreements.csv`, `adjudication.csv`, `final-r4.csv`, `final-all.csv`,
`lists/`, `cv.json`, `RESULTS.md`.

## 9. Thay đổi sau khi chốt
- Luật dừng §5 (`kappa.py 001,...,005`, `kappa-early.json`): 375 op, Fleiss kappa T 0,921; Cohen LA–LB 1,0, LA–LM 0,886, LB–LM 0,886. Không dừng.
- 2026-10-06 23:42: tài khoản hết quota (LA 21 khối, LB 24 khối, LM 25 khối). Dừng tới 03:02 theo yêu cầu user; runner `run2.sh` coi khối là xong khi đủ số dòng.
- 2026-10-06 23:55: user đổi ý, cho chạy tiếp ngay trên tài khoản mới; runner `run3.sh` (bỏ cổng chờ).
- Từ khối 034, LM chỉ ghi dòng `T = 1`; cột `sub` của LM để trống từ đó. `sub` không dùng trong gộp, rút hay đo.
- 2026-10-07 00:07: user dừng mọi lượt để chuyển về tài khoản cũ (LA 66 file, LB 69 file, LM xong 001–074). LA, LB
  chạy lại bằng `run2.sh` từ 03:02; khối dở lúc dừng được gán lại từ đầu.
- 2026-10-07 03:02–03:15: LA, LB xong 86/86 khối trên tài khoản cũ; LM xong 075–086. Đủ 6.409 dòng ở cả ba lượt. Phân xử 3 op (`adjudication-prompt.txt`). Thêm `extra_tests.py` (kiểm định M5, R4 so R3) ngoài protocol.
