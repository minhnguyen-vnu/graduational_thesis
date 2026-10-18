# P2f full §4 re-measure — kết quả (ghi 2026-10-16 14:10, sau FULL DONE 13:56)

Jar `evomaster-P2f-64ee8ffc.jar` (sha256 first-16 `64ee8ffc78a9aad7`), commit `a544c996ac` + fix
setField leaf-activate (`infra/evomaster-ext/wip/setfield-leaf-activate-20261015.patch`). Một jar duy nhất,
không trộn jar. 180 hàng = 21 hàng cổng (PHASE1) + §4 arms (PHASE2).

Cấu hình như §4: Tier-1/Tier-2 rate 120, maxTime 150s, extraPhase 0.6; pyLoad rate 200, maxTime 10m,
`--endpointExclude /api/kill,/api/restart`. Reset endpoint theo từng target. reseed sạch mỗi hàng.

## Bảng P2f so AF2 (`af2-full-remeasure-20261003/runs.csv`)

| Target | arm | reset | AF2 970 | P2f 970 | seeds P2f-only | seeds AF2-only | McNemar exact p |
|---|---|---|---|---|---|---|---|
| Tier-1 reports | vuln | 0 | 19/20 | 19/20 | — | — | 1.000 |
| Tier-1 reports | vuln | 1 | 20/20 | 20/20 | — | — | 1.000 |
| Tier-1 reports | fixed | 0 | 0/20 | 0/20 | — | — | 1.000 |
| Tier-1 reports | fixed | 1 | 0/20 | 0/20 | — | — | 1.000 |
| Tier-2 vampi | ours-vuln | 0 | 7/20 | 7/20 | — | — | 1.000 |
| Tier-2 vampi | ours-vuln | 1 | 13/20 | 13/20 | — | — | 1.000 |
| Tier-2 vampi | ours-fixed | 0 | 0/20 | 0/20 | — | — | 1.000 |
| Tier-2 vampi | ours-fixed | 1 | 0/20 | 0/20 | — | — | 1.000 |
| Tier-2b pyLoad | vuln | 0 | 5/5 | 5/5 | — | — | 1.000 |
| Tier-2b pyLoad | vuln | 1 | 5/5 | 5/5 | — | — | 1.000 |
| Tier-2b pyLoad | fixed | 0 | 0/5 | 0/5 | — | — | 1.000 |
| Tier-2b pyLoad | fixed | 1 | 0/5 | 0/5 | — | — | 1.000 |

Bộ ba dựng được (assembled): pyLoad vuln reset AF2 36 → P2f 75; pyLoad fixed reset AF2 35 → P2f 52.
Các arm khác bằng nhau. Số bộ ba tăng, phán quyết 970 không đổi.

## Toàn vẹn

- Cổng 21/21 MATCH (PHASE1, dừng nếu lệch; không lệch).
- `compare.out`: 180/180 hàng, missing 0, ERR 0, 970-không-bộ-ba 0, FP trên bản vá 0.
- `audit970.out` trên test Tier-1/Tier-2: TOTAL 59 PASS, 0 FAIL, 0 UNPARSED, 56 bộ-ba-im-lặng
  (bộ ba dựng được trên bản vá, đúng là không nổ). pyLoad (auth cookie) kiểm riêng, không qua audit này.
- Không có `Entering Sleep` trong lúc hàng chạy; không STOPPED/ERR.

## Đọc kết quả

- Phán quyết P2f trùng AF2 từng seed từng arm trên §4: `seeds_af2_only` và `seeds_p2f_only` rỗng, p = 1.000.
  Fix setField không làm mất hay thêm lần nổ nào trên ba target §4.
- Tác động của fix nằm ở hình dạng trường role/cờ nullable (artifact-keeper, `is_admin` kiểu
  `["boolean","null"]`). Ba target §4 không có transition dạng cờ boolean nullable, nên phán quyết không đổi;
  pyLoad chỉ tăng số bộ ba dựng được.
- Đây là lượt đầy đủ trên một jar duy nhất, đã qua cổng. Nó gỡ lệch luật "bộ gộp trộn jar" của bảng §4 hiện tại
  (`p2e-continue-20261013/merged.csv`, 71 P2e + 109 P2d). Giá trị các ô không đổi so với bảng hiện tại.
- Chưa promote P2f thành jar luận văn; chờ user quyết. Chưa sửa `docs/results.md`/`CLAUDE.md`.
