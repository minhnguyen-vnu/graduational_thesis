import sys
sys.path.insert(0, "/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/analysis/lexicon-rules/lexicon-r4-20261007")
import measure as M
X, sim = M.X, M.sim
lab, ops, rows, provider = X.new_data()
sp = "S517"
pv = {o["provider"] for o in ops if o["spec"] == sp}
tr_rows = [x for x in rows if provider[x["spec_id"]] not in pv]
pw, qw = X.as_lex(*X.derive_new(tr_rows, provider, False))
ol = [o for o in ops if o["spec"] == sp and o["method"] in sim.VERB_ORDER]
def hits(o):
    h = sim.hay(o)
    return sorted([(s, w) for w, s in pw if w in h], reverse=True)
sc = sorted(ol, key=lambda o: -(hits(o)[0][0] if hits(o) else 0))
print(sp, pv, len(ol), "write ops")
for i, o in enumerate(sc[:6]):
    print(i, o["method"], o["path"], ["%s=%.3f" % (w, s) for s, w in hits(o)[:4]], "T" if lab[o["row_id"]]["T"] else "")
for i, o in enumerate(sc):
    if lab[o["row_id"]]["T"]:
        print("T at", i, o["method"], o["path"], ["%s=%.3f" % (w, s) for s, w in hits(o)[:4]], "fields:", [f["name"] for f in o["fields"]][:12])
