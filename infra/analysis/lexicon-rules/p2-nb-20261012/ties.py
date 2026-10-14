import sys
from collections import defaultdict
exec(open("b3check.py").read().rsplit("for rep, fl in", 1)[0])
for rep, fl in enumerate(M.folds(ops)):
    tie_specs = 0; specs = 0; tie_ops = 0; via_ops = 0
    for held in fl:
        tr = [o for o in ops if o["provider"] not in held]
        te = [o for o in ops if o["provider"] in held and o["spec"] not in old29 and o["method"] in sim.VERB_ORDER]
        wA, pA = nb_train(tr); nbA = nb_scorer(wA, pA); wF, pF = ftrain(tr)
        by = defaultdict(list)
        for o in te:
            by[o["spec"]].append(o)
        for s, ol in by.items():
            via = [o for o in ol if nbA(o) > pA and nbf_pick(o, wF, pF)]
            if not any(lab[o["row_id"]]["T"] for o in via):
                continue
            specs += 1
            sc = [round(nbA(o), 9) for o in via]
            via_ops += len(via)
            tie_ops += sum(1 for x in sc if sc.count(x) > 1)
            tpos = [i for i, o in enumerate(via) if lab[o["row_id"]]["T"]]
            tscores = {sc[i] for i in tpos}
            if any(sc.count(x) > 1 and any(not lab[via[j]["row_id"]]["T"] for j in range(len(via)) if sc[j] == x) for x in tscores):
                tie_specs += 1
    print("repeat %d: specs with T viable %d, specs where a T op ties with a non-T op %d; viable ops %d, ops in a tie %d" % (rep + 1, specs, tie_specs, via_ops, tie_ops))
