# Kết quả — P2d trên các hàng AF2 nổ

Jar `evomaster-P2d-2e0dbd4d.jar`, 11:33–13:40, 16 hàng, không luật dừng nào nổ. Không trích số.

16/16 hàng trùng AF2 cùng arm, cùng seed, trên 8 cột det970, assembled, void, resets, restores_ok, restores_no,
statuses, faults (`compare-af2.txt`, so bằng `awk` với `af2-full-remeasure-20261003/runs.csv`).

| Arm | Hàng | Nổ | Restore trên AF2 |
|---|---|---|---|
| vampi vuln có reset | 13 | 13/13 | 0 lượt ở cả 13 hàng |
| pyLoad vuln không reset, seeds 1–3 | 3 | 3/3 | 1 lượt thành công mỗi hàng |

Không thấy lỗi nào khác ngoài lỗi restore `EVOMASTER` (`p2d-night-20261012/STOPPED.md`).

pyLoad: P2d nâng operator bằng giá trị `0,0` (hai trường; log mức `warn` không ghi tên trường), AF2 bằng `0`;
cả hai nhận 200 và dựng cùng bộ ba `POST /json/status` 200/200/200 (`logs/t2b-vuln-seed1-r0.log`).
