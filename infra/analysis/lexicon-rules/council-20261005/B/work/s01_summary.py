"""In tom tat results.json, mcnemar.json va lists/ cua hai vong (chi doc)."""
import json, os, glob

B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lexicon-rules")
for rnd in ("field-labelling-20261004", "field-labelling-r2-20261004"):
    d = os.path.join(B, rnd)
    print("#####", rnd)
    r = json.load(open(os.path.join(d, "results.json")))
    for k, v in r.items():
        if k != "lists":
            print(k, json.dumps(v))
    for k, v in r.get("lists", {}).items():
        print("==", k, {kk: vv for kk, vv in v.items() if not isinstance(vv, (dict, list)) or kk in ("derived", "final", "words")})
        for kk, vv in v.items():
            if isinstance(vv, dict) or (isinstance(vv, list) and kk not in ("derived", "final", "words")):
                print("   ", kk, json.dumps(vv)[:600])
    m = os.path.join(d, "mcnemar.json")
    if os.path.exists(m):
        print("mcnemar", json.dumps(json.load(open(m))))
    for f in sorted(glob.glob(os.path.join(d, "lists", "list-*.txt"))):
        print(os.path.basename(f), open(f).read().split())
