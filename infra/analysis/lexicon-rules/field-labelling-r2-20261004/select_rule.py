import json, os
from common import *


def main():
    fields = r1_fields()
    train = [f for f in fields if f["split"] == "train"]
    dev = [f for f in fields if f["split"] == "test"]
    out = {"per_rule": {}}
    for rule in RULES:
        per = {}
        for name in LISTS:
            words, _, _ = derive(docs(train, name), rule)
            m = prf(name, words, docs(dev, name))
            per[name] = {"words": words, "dev": m}
        per["mean_f1"] = round(sum(per[n]["dev"]["f1"] for n in LISTS) / len(LISTS), 4)
        out["per_rule"][rule] = per
    best = max(out["per_rule"][r]["mean_f1"] for r in RULES)
    chosen = next(r for r in TIE_ORDER if out["per_rule"][r]["mean_f1"] == best)
    out["chosen"] = chosen
    out["mean_f1"] = {r: out["per_rule"][r]["mean_f1"] for r in RULES}
    json.dump(out, open(os.path.join(HERE, "select.json"), "w"), indent=1)
    print(json.dumps(out["mean_f1"]), "chon", chosen)
    for name in LISTS:
        print(name, {r: (out["per_rule"][r][name]["dev"]["f1"], len(out["per_rule"][r][name]["words"])) for r in RULES})


main()
