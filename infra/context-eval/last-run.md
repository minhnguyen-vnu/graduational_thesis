# Context eval — last run

2026-10-31, hai lượt, mỗi lượt một `general-purpose` agent mới, đọc `CLAUDE.md` từ đĩa, bị cấm đọc `infra/context-eval/`.
Lượt 1 chạy sau khi sửa artifact-keeper và luật target phát triển. Lượt 2 chạy sau khi sửa HEAD `1cd0d091f4` và mọi chỗ
nói về reset, D1, transition khai báo. **Cả hai lượt 23/23 khớp `expected.md`.**

Lượt 1 báo `CLAUDE.md` ghi sai HEAD; đã kiểm bằng git và sửa trước lượt 2.

Lượt 2 báo, chưa sửa, chờ user:
- `CLAUDE.md` §3 ghi VOID khi follow-up không kết luận được; `RestSecurityBuilder.kt:1101` chỉ loại follow-up null hoặc
  401, nên follow-up 404 hoặc 5xx đi tới log `Assembled`, không nổ 970. P2f không gặp ca này: mọi bộ ba là `200/200/200`
  hoặc `200/200/403` (`p2f-counts.out`).
- `docs/tier2b-pyload-target.md` dòng 73, 248 gọi 0/5 trước mở rộng là recall trung thực; `docs/results.md` §1 ghi 5/5
  trên P2f.
- `infra/analysis/denial-codes-2026-09-17.md` §1 và §3 nói khác nhau về 401; `CLAUDE.md` §3 ghi "các target" kiểm phân
  quyền trước tồn tại, tài liệu gốc chỉ kiểm trên reports-api và vampi.
- Skill `em-batch` bước 1 nêu ba mẫu harness không có kiểm `Entering Sleep`, trong khi bước 4 yêu cầu; kiểm tra đó nằm ở
  `p2e-full-20261014/p2e_full.sh`.
- Skill `regression-gate` dùng lại `regression-check/`, trái luật mỗi batch một thư mục mới của `CLAUDE.md` §2.
- `CLAUDE.md` §2 nêu 4 agent `thesis-*`, `.claude/agents/` có 6.

1. Không. Đưa mã ra xem và chờ OK trước khi viết hoặc dựng. [CLAUDE.md §2; evomaster-build]
2. Không. Mã thêm không mang comment; `guard.py` chặn. [CLAUDE.md §2; guard.py]
3. `evomaster-P2f-64ee8ffc.jar`, commit `f73010103b`, cha của HEAD. [CLAUDE.md §4–5; docs/results.md §0]
4. 30–35%. P2f 7/20, jar R soát lại 6/20. [CLAUDE.md §4; docs/results.md §1a, §8]
5. Không. McNemar chính xác p = 0,070. [CLAUDE.md §4; docs/results.md §4, §8]
6. Không. "replay được 55/59", jar AF2. [CLAUDE.md §4; docs/results.md §3]
7. 0 FP trên 90 lượt, 116 bộ ba trên mã đã vá. [docs/results.md §1a, §2]
8. INCONCLUSIVE; bộ ba VOID. [CLAUDE.md §3; metamorphic-authz-relations §5.1]
9. Không. [CLAUDE.md §3; metamorphic-authz-relations §5.1]
10. VOID khi source hoặc transition không 2xx, hoặc follow-up không kết luận được. [CLAUDE.md §3; docs/results.md §2]
11. Không có guard thì `GET /reports` (viewer cũng được) đọc thành lỗi. [CLAUDE.md §3; metamorphic-authz-relations §2.3]
12. `nohup caffeinate -dims zsh <harness> > <folder>/nohup.out 2>&1 & disown`; không `run_in_background`. [em-batch]
13. Không. Một việc nặng một lúc; `guard.py` chặn. [CLAUDE.md §2; guard.py; evomaster-build]
14. Không. Chỉ cho thấy 21 hàng không hỏng. [regression-gate; CLAUDE.md §5]
15. Chưa kết luận; chạy lại xen kẽ với jar tham chiếu. [regression-gate]
16. Thư mục mới dưới `infra/em-results/` (harness `rm -rf` output), rồi snapshot. [CLAUDE.md §2; em-batch]
17. Mở nguồn gốc, khớp từng chữ, `pdftotext`; web-fetch không tính. [CLAUDE.md §2]
18. Không rule nào; `~/.claude/rules/` bị loại bằng `claudeMdExcludes`. [CLAUDE.md §2]
19. Chỉ khi user yêu cầu; `origin` = `github.com/minhnguyen-vnu/evomaster-stateful-authz`. [CLAUDE.md §2; evomaster-build]
20. `docs/tier2b-pyload-target.md` §3. [CLAUDE.md §7]
21. Không; 403 đến từ `POST /reports`. [CLAUDE.md §4; docs/results.md §6]
22. Không yêu cầu nào; dùng `.claude/agents/thesis-*` và self-test. [CLAUDE.md §2]
23. Không, jar SR báo `is not a recognized option`; số trích từ P2f. [CLAUDE.md §5; jars.md; em-batch]
