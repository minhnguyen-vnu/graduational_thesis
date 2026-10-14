import json, os

src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "evaluate.py")).read().replace("\nmain()\n", "\n")
ns = {"__file__": os.path.abspath("evaluate.py"), "__name__": "ev"}
exec(compile(src, "evaluate.py", "exec"), ns)


def main():
    allf = ns["r1_fields"]() + ns["r2_fields"]()
    out = {"note": "R4 tren train + dev + test (228 nha cung cap); khong co tap do held-out", "lists": {}}
    for n in ns["EVAL"]:
        w, stats, base = ns["derive"](ns["docs"](allf, n), "R4")
        top = sorted([s for s in stats if s["providers"] >= 2], key=lambda s: (-s["score"], s["word"]))[:8]
        out["lists"][n] = {"words": w, "top8": top}
        print(n, w)
    out["counts"] = ns["counts"](allf)
    json.dump(out, open(os.path.join(ns["HERE"], "merged-lists.json"), "w"), indent=1)


main()
