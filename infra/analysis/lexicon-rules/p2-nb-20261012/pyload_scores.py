import sys
D = "/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/analysis/lexicon-rules/lexicon-combine-20261007"
sys.path.insert(0, D)
import measure2 as W
X, M, sim = W.X, W.M, W.sim
lab, ops, rows, provider = X.new_data()
pw, qw = X.as_lex(*X.derive_new(rows, provider, False))
for name, path, m, p in M.TARGETS:
    if name not in sys.argv[1:]:
        continue
    tops = M.R.spec_ops(path)
    out = []
    for op in tops:
        if op["method"] not in sim.VERB_ORDER:
            continue
        h = sim.hay(op)
        hits = sorted([(s, w) for w, s in pw if w in h], reverse=True)
        if hits:
            out.append((hits[0][0], op["method"], op["path"], hits[:5]))
    out.sort(key=lambda x: -x[0])
    print(name, "write ops scored>0:", len(out), "of", sum(1 for o in tops if o["method"] in sim.VERB_ORDER))
    for s, mm, pp, h in out[:12]:
        print("  %.4f %-6s %-45s %s %s" % (s, mm, pp, " ".join("%s=%.3f" % (w, x) for x, w in h), "<== TRUE" if (mm, pp) == (m, p) else ""))
