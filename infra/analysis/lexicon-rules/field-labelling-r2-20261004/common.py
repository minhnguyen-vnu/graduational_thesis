import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
R1 = os.path.join(HERE, "..", "field-labelling-20261004")

_src = open(os.path.join(R1, "derive_eval.py")).read().replace("\nmain()\n", "\n")
R1NS = {"__file__": os.path.join(R1, "derive_eval.py"), "__name__": "r1"}
exec(compile(_src, "derive_eval.py", "exec"), R1NS)

HARD = R1NS["HARD"]
docs = R1NS["docs"]
tokens = R1NS["tokens"]
classify = R1NS["classify"]
prf = R1NS["prf"]
LISTS = ("A-role", "A-admin", "C", "B-low", "B-high")
RULES = ("R0", "R1", "R2", "R3", "R4")
TIE_ORDER = ("R2", "R3", "R1", "R4", "R0")


def r1_fields():
    return R1NS["build"]()


def candidates(dd):
    pos = [d for d in dd if d[1]]
    neg = [d for d in dd if not d[1]]
    if not pos:
        return [], 0.0
    base = len(pos) / float(len(dd))
    cand = set()
    for d in pos:
        cand |= tokens(d[0])
    stats = []
    for w in sorted(cand):
        hp = [d for d in pos if w in d[0]]
        hn = [d for d in neg if w in d[0]]
        ncc = len({d[2] for d in hp})
        prec = len(hp) / float(len(hp) + len(hn))
        score = (len(hp) + 1) / float(len(hp) + len(hn) + 2) * ncc / float(ncc + 1)
        stats.append({"word": w, "df_pos": len(hp), "df_neg": len(hn), "providers": ncc,
                      "precision": round(prec, 4), "score": round(score, 4)})
    return stats, base


def select(stats, base, rule):
    ok = [s for s in stats if s["providers"] >= 2]
    if rule == "R0":
        kept = [s["word"] for s in ok if s["precision"] >= 2 * base]
    elif rule == "R1":
        kept = [s["word"] for s in ok if s["precision"] >= 0.3]
    elif rule == "R2":
        kept = [s["word"] for s in ok if s["precision"] >= 0.5]
    elif rule == "R3":
        kept = [s["word"] for s in ok if s["score"] >= 0.3]
    elif rule == "R4":
        kept = [s["word"] for s in sorted(ok, key=lambda s: (-s["score"], s["word"]))[:5]]
    else:
        raise ValueError(rule)
    kept = sorted(kept)
    dropped = {b for a in kept for b in kept if a != b and a in b}
    return [w for w in kept if w not in dropped]


def derive(dd, rule):
    stats, base = candidates(dd)
    if not stats:
        return [], stats, base
    return select(stats, base, rule), stats, base
