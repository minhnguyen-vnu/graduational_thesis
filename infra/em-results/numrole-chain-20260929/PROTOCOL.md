# Chuỗi jar `NR-aeeb485c` (ghi 23:01 09-29, trước khi chạy)

Jar `EvoMaster/evomaster-NR-aeeb485c.jar` (`wip/num-role-20260929.md`), self-test num-role 9/9. Bọc `caffeinate -dims`;
mỗi dòng ghi `sleep_events`, có dòng `Entering Sleep` thì dừng chuỗi.

1. Self-test cũ trên jar mới: `role-value.sh` (callcenter, Tier-1), `victim-id.sh` (Grafana, Tier-1). Ghi số PASS/FAIL, không dừng chuỗi.
2. Gate 21 dòng (`core/target/evomaster.jar` = jar trên). Dừng chuỗi nếu có dòng bản đã sửa lệch.
3. Seeds 1–10: Tier-1 bản lỗi, Tier-2 bản lỗi, Tier-1 và Tier-2 bản đã sửa, pyLoad bản lỗi; cờ như `victimid-chain-20260928`.
   Dừng sớm: Tier-1 bản lỗi seeds 1–3 đều không có 970.
4. Truthy seeds 1–10 (target phát triển), harness `truthy-heldout-20260929d/run.sh`, thư mục `truthy-dev-20260930/`, luật dừng như §9.
5. Sao lưu sau bước 3 và 4.

So sánh sau chạy: từng dòng seeds 1–10 với jar `VI`/`TT` trên 970, số bộ ba, VOID, mã, tập lỗi.
