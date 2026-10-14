import json, os
from math import comb
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("de", os.path.join(HERE, "derive_eval.py"))
src = open(os.path.join(HERE, "derive_eval.py")).read().replace("\nmain()\n", "\n")
ns = {"__file__": os.path.join(HERE, "derive_eval.py"), "__name__": "de"}
exec(compile(src, "derive_eval.py", "exec"), ns)


def exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(comb(n, i) for i in range(0, k + 1)) / 2.0 ** n
    return min(1.0, 2 * p)


def main():
    fields = ns["build"]()
    train = [f for f in fields if f["split"] == "train"]
    test = [f for f in fields if f["split"] == "test"]
    out = {}
    for name in ("A-role", "A-admin", "C", "B-low", "B-high"):
        words, _, _ = ns["derive"](ns["docs"](train, name))
        dd = ns["docs"](test, name)
        hard = ns["HARD"][name]
        b = c = both = neither = 0
        for d in dd:
            hc = ns["classify"](name, hard, d[0]) == d[1]
            dc = ns["classify"](name, words, d[0]) == d[1]
            if hc and dc:
                both += 1
            elif hc:
                b += 1
            elif dc:
                c += 1
            else:
                neither += 1
        out[name] = {"docs": len(dd), "both_correct": both, "only_hard_correct": b, "only_derived_correct": c,
                     "both_wrong": neither, "p_exact": round(exact(b, c), 6)}
    json.dump(out, open(os.path.join(HERE, "mcnemar.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


main()
