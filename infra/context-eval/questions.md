# Context eval — questions

Run after any change to `CLAUDE.md`, `docs/results.md`, `.claude/skills/`, `.claude/agents/` or the hooks.
Give the questions to a fresh `general-purpose` or `thesis-*` agent. It answers from its loaded context and the files
that context points to, and never opens `infra/context-eval/`. For each answer it names the file it used.
Compare with `expected.md`; every answer must match.

1. May you write code into the EvoMaster repo as soon as you know what to change?
2. May a line you add to a Kotlin file carry a `//` comment explaining it?
3. Which jar produced the current numbers, and which commit is it?
4. How do you quote Tier-2 black-box recall?
5. May the thesis say the state-reset ablation proves the diagnosis causally? Why?
6. May the thesis call the emitted 970 tests "reproducible"? What is the measured figure?
7. How many false positives were observed, over how many fixed-target runs and how many patched-side triples?
8. What does a 401 mean for the oracle's verdict?
9. Is a 404 on the follow-up a denial?
10. What makes a triple VOID?
11. Why must the source of a triple be a write gated by the removed privilege?
12. How do you launch an 80-run batch so it survives the session?
13. May you run `mvn package` while a batch is running? Why?
14. A regression gate returns 21/21. Does that show the new jar changes no number?
15. One gate row mismatches. Is that a regression?
16. Where must a new batch write its output, and why?
17. What must happen before a quote from a paper enters the thesis?
18. Which global rules from `~/.claude/rules/` apply to this project?
19. May you commit and push the EvoMaster branch after finishing a change? Where does `origin` point?
20. Where is the declared list of deviations for the pyLoad target?
21. On Tier-1, may the write-up say the C4 probe re-attempts the guarded write with a fresh credential?
22. Which of the global agent `tdd-guide`'s requirements apply here?
