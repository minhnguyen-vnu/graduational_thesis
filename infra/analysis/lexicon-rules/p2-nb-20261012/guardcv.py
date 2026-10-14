import sys
sys.argv = ["x", "RF"]
exec(open("nbcheck_all.py").read().split("flt = sys.argv[1]")[0])
cur = X.read_lexicon(X.JAR_LEX)[0]
for rep, fl in enumerate(M.folds(ops)):
    c = {"T": 0, "N": 0, "T_lex": 0, "N_lex": 0, "T_post": 0, "N_post": 0, "T_lr": 0, "N_lr": 0}
    for held in fl:
        tr = [o for o in ops if o["provider"] not in held]
        te = [o for o in ops if o["provider"] in held and o["spec"] not in old29 and o["method"] in sim.VERB_ORDER]
        w, prior = nb_train(tr); nb = nb_scorer(w, prior)
        pw, qw = X.as_lex(*X.derive_new([x for x in rows if provider[x["spec_id"]] not in held], provider, False))
        for o in te:
            k = "T" if lab[o["row_id"]]["T"] else "N"
            c[k] += 1
            h = sim.hay(o)
            c[k + "_lex"] += any(x in h for x, s in pw)
            s = nb(o)
            c[k + "_post"] += s > 0
            c[k + "_lr"] += s > prior
    print("repeat %d: T ops %d -> lexicon>0 %d, NB post>0.5 %d, NB LR>1 %d | other ops %d -> lexicon>0 %d, post>0.5 %d, LR>1 %d" % (
        rep + 1, c["T"], c["T_lex"], c["T_post"], c["T_lr"], c["N"], c["N_lex"], c["N_post"], c["N_lr"]))
