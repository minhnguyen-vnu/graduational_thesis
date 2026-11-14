# Context eval — questions

Run after any change to `CLAUDE.md`, `docs/results.md`, `.claude/skills/`, `.claude/agents/` or the hooks.
Give the questions to a fresh `general-purpose` or `thesis-*` agent. It answers from its loaded context and the files
that context points to, and never opens `infra/context-eval/`. For each answer it names the file it used.
Compare with `expected.md`; every answer must match.

1. May you write code into the EvoMaster repo as soon as you know what to change?
2. May a line you add to a Kotlin file carry a `//` comment explaining it?
3. Which jar produced the current numbers, and which commit is it?
4. Which four targets carry the current numbers, and which two carry a bug the author did not write?
5. How many false positives were observed, over how many fixed-target runs and how many patched-side triples?
   How many true negatives does the artifact-keeper vendor patch give, and why?
6. What does a 401 mean for the oracle's verdict?
7. Is a 404 on the follow-up a denial?
8. What makes a triple VOID?
9. Why must the source of a triple be a write gated by the removed privilege?
10. How do you launch an 80-run batch so it survives the session?
11. A regression gate returns 12/12. Does that show the new jar changes no number?
12. One gate row mismatches. Is that a regression?
13. Where must a new batch write its output, and why?
14. What must happen before a quote from a paper enters the thesis?
15. Which global rules from `~/.claude/rules/` apply to this project?
16. May you commit and push the EvoMaster branch after finishing a change? Where does `origin` point?
17. Where is the declared list of deviations for the pyLoad target, and where is the part of artifact-keeper that is
    ours?
18. On reports-api, may the write-up say the C4 probe re-attempts the guarded write with a fresh credential?
19. Which of the global agent `tdd-guide`'s requirements apply here?
20. Does the current jar add any EvoMaster command-line option? What decides the verdict on a triple?
21. May the thesis describe the run that slept at 07:05 on 2026-11-08 or the six parallel lanes? Where are such events
    recorded?
