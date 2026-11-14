# Context eval — last run

2026-11-14, một `general-purpose` agent mới, đọc `CLAUDE.md` từ đĩa, không đọc `infra/context-eval/`. Chạy sau khi bỏ
nhãn "target phát triển" khỏi `CLAUDE.md` §6 và khỏi khóa luận (`docs/results.md` §9 ghi bỏ khi viết).
**21/21 khớp `expected.md`.**

Agent báo, để nguyên:
- `docs/results.md` §5 và `docs/tier2b-pyload-target.md` §5 vẫn ghi lịch sử sửa builder trên pyLoad và artifact-keeper.
  Đó là sự thật về quá trình làm, giữ để trả lời hội đồng; §9 quyết định cách viết.
- `CLAUDE.md` §6 trích `RestSecurityOracle.kt:577`, `:594` theo HEAD `2c3f281f13`; trên cây ND có comment `THESIS` là
  `:583`, `:602`.
