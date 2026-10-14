import json, os, sys
sys.argv = ["x"]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "evaluate.py")).read().replace("\nmain()\n", "\n")
ns = {"__file__": os.path.abspath("evaluate.py"), "__name__": "ev"}
exec(compile(src, "evaluate.py", "exec"), ns)


def main():
    dev_train = ns["r1_fields"]()
    test = ns["r2_fields"]()
    out = {"note": "hau kiem, khong thuoc protocol §5-§6", "rules_on_test": {}, "split_mcnemar": {}}
    for rule in ns["RULES"]:
        per = {}
        for name in ns["LISTS"]:
            words, _, _ = ns["derive"](ns["docs"](dev_train, name), rule)
            per[name] = {"words": words, "test": ns["prf"](name, words, ns["docs"](test, name))}
        per["mean_f1"] = round(sum(per[n]["test"]["f1"] for n in ns["LISTS"]) / len(ns["LISTS"]), 4)
        out["rules_on_test"][rule] = per
    out["hard_mean_f1_test"] = round(sum(ns["prf"](n, ns["HARD"][n], ns["docs"](test, n))["f1"] for n in ns["LISTS"]) / len(ns["LISTS"]), 4)
    for name, hard in (("A-role", "A-role"), ("C", "C"), ("C", "C-noid")):
        words, _, _ = ns["derive"](ns["docs"](dev_train, name), "R4")
        dd = ns["docs"](test, name)
        out["split_mcnemar"]["%s/%s" % (hard, "R4")] = {
            "positives": ns["mcnemar"](name, ns["HARD"][hard], words, [d for d in dd if d[1]]),
            "negatives": ns["mcnemar"](name, ns["HARD"][hard], words, [d for d in dd if not d[1]])}
    json.dump(out, open(os.path.join(ns["HERE"], "exploratory.json"), "w"), indent=1)
    for r in ns["RULES"]:
        print(r, out["rules_on_test"][r]["mean_f1"], {n: (out["rules_on_test"][r][n]["test"]["f1"], out["rules_on_test"][r][n]["words"][:12]) for n in ns["LISTS"]})
    print("hard", out["hard_mean_f1_test"])
    print(json.dumps(out["split_mcnemar"]))


main()
