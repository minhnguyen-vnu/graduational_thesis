import sys
D = "/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/analysis/lexicon-rules/lexicon-combine-20261007"
sys.path.insert(0, D)
import measure2 as W
X, M, sim = W.X, W.M, W.sim
lab, ops, rows, provider = X.new_data()
cur = X.read_lexicon(X.JAR_LEX)
new = X.as_lex(*X.derive_new(rows, provider, False))
flag, fs, _ = W.flag_feature(ops, lab)
r4 = sim.derive(ops, lab, "std")[0]
print("R4 lists:", {k: r4[k] for k in ("role", "admin", "low", "high", "spec", "id")})
for LBname, LB in (("HARD", sim.HARD), ("R4", r4)):
    red = M.R.fns(LB)[0]
    for name, path, m, p in M.TARGETS:
        tops = M.R.spec_ops(path)
        scorers = W.arm_scorers(cur, new, flag, fs)
        for a in ("A-cur", "A-new-0"):
            ts, up, _ = scorers[a]
            is_t = lambda op: op["method"] == m and op["path"] == p
            ranked = [op for op in tops if op["method"] in sim.VERB_ORDER and ts(op) > 0]
            ranked.sort(key=lambda op: (-ts(op), not up(op), sim.VERB_ORDER.index(op["method"])))
            v8 = [o for o in ranked[:8] if red(o, LB)]
            va = [o for o in ranked if red(o, LB)]
            pos = lambda L: next((i + 1 for i, o in enumerate(L) if is_t(o)), "-")
            print("%-5s %-16s %-8s top8: %d op, true #%s | alpha: %d op, true #%s  %s" % (LBname, name, a, len(v8), pos(v8), len(va), pos(va), ["%s %s" % (o["method"], o["path"]) for o in va][:6]))
