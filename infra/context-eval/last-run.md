# Context eval — last run

2026-10-14, lượt 5, fresh `general-purpose` agent, đọc `CLAUDE.md` từ đĩa, soát từng số của `docs/naive-bayes.md`
với file nguồn (mọi số khớp; `check_model.py` chạy lại 8/8). Chạy sau khi viết `docs/naive-bayes.md`, đánh dấu
`docs/lexicon.md` là lịch sử, sửa ghi chú tên jar, thêm P2 vào "Tháng 10", giải thích AF2 41/38. Agent bị cấm đọc
`infra/context-eval/`. **22/22 khớp `expected.md`.**

Mâu thuẫn lượt 5 báo:
- Đã sửa sau lượt này: `docs/results.md` §5 "AF2 wrote `role` only" sai (AF2 `setAllRoleFieldsTo` ghi cả hai trường;
  log AF2 in một giá trị); "180 hàng trùng AF2" ở `docs/naive-bayes.md`, `docs/argument.md` đổi thành "số nổ 970 và FP
  trùng"; `docs/naive-bayes.md` §4 thiếu VOID vampi seed 19, §3 trộn "viết tay" với luật RF; `docs/argument.md` K2
  ghi bản vá pyLoad là của pyLoad (bản vá là của ta); `CLAUDE.md` §6 "D1 lấy bộ từ vựng ra khỏi phán quyết".
- Có từ trước, chờ user: `CLAUDE.md` §6 gọi nửa test của lexicon là "held-out" dù nửa đó đã dùng khi phát triển;
  `docs/results.md` §6 "34 of 39" và "424 of 428 runs" không nêu jar.

1. Không. Đưa mã ra xem và chờ OK trước khi viết hoặc dựng. [CLAUDE.md §2; evomaster-build]
2. Không. Mã thêm không mang comment; `guard.py` chặn. [CLAUDE.md §2; guard.py]
3. `evomaster-P2e-6ae8277b.jar`, commit `a544c996ac`, bộ gộp có lệch luật; AF2 giữ làm nguồn gốc. [CLAUDE.md §4/§5; docs/results.md §0; jars.md]
4. 30–35% (P2e và AF2 7/20 không reset). [CLAUDE.md §4; docs/results.md §1a/§8]
5. Không. McNemar chính xác p = 0,070. [CLAUDE.md §4; docs/results.md §4/§8]
6. Không. "replay được 55/59", jar AF2, chưa chạy lại trên P2e. [CLAUDE.md §4; docs/results.md §3/§8]
7. 0 FP trên 90 lượt, 116 bộ ba trên mã đã vá (AF2: 99). [CLAUDE.md §4; docs/results.md §1a]
8. INCONCLUSIVE; bộ ba VOID. [CLAUDE.md §3; metamorphic-authz-relations §5.1]
9. Không. Kiểm phân quyền trước tồn tại. [CLAUDE.md §3]
10. VOID trừ khi source 2xx, transition 2xx, follow-up kết luận được. [CLAUDE.md §3]
11. Không có guard thì `GET /reports` (viewer cũng được) đọc thành lỗi. [CLAUDE.md §3; metamorphic-authz-relations §2.3]
12. `nohup caffeinate -dims zsh <harness> > <folder>/nohup.out 2>&1 & disown`; không `run_in_background`; harness dừng khi máy ngủ. [em-batch]
13. Không. Một việc nặng một lúc; `guard.py` chặn. [CLAUDE.md §2; em-batch; evomaster-build]
14. Không. Chỉ cho thấy 21 hàng không hỏng. [regression-gate]
15. Không tự nó; chạy lặp xen kẽ với jar tham chiếu. [regression-gate]
16. Thư mục mới dưới `infra/em-results/` (harness `rm -rf` output), rồi snapshot. [em-batch; CLAUDE.md §2]
17. Mở nguồn gốc, khớp từng chữ, `pdftotext`; web-fetch không tính. [CLAUDE.md §2]
18. Không cái nào; `~/.claude/rules/` bị loại trừ. [CLAUDE.md §2]
19. Chỉ khi user yêu cầu; `origin` = `github.com/minhnguyen-vnu/evomaster-stateful-authz`. [evomaster-build]
20. `docs/tier2b-pyload-target.md` §3. [CLAUDE.md §7]
21. Không; 403 đến từ `POST /reports`. [docs/results.md §6; CLAUDE.md §4]
22. Không cái nào; dùng `.claude/agents/thesis-*` và self-test. [CLAUDE.md §2]
