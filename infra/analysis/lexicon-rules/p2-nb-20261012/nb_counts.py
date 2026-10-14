import sys, math
from collections import defaultdict
sys.argv = ["x", "RF"]
exec(open("nbcheck_all.py").read().split("flt = sys.argv[1]")[0])
pos = [o for o in ops if lab[o["row_id"]]["T"]]
neg = [o for o in ops if not lab[o["row_id"]]["T"]]
print("N_T", len(pos), "N_N", len(neg), "prior log(%d/%d)=%.3f" % (len(pos), len(neg), math.log(len(pos) / len(neg))))
for t in ("f:permission", "p:user", "f:password", "v:POST", "f:name"):
    dr = sum(1 for o in pos if t in fe(o)); dn = sum(1 for o in neg if t in fe(o))
    pv = len({o["provider"] for o in pos if t in fe(o)})
    pr = (dr + 1) / (len(pos) + 2); qn = (dn + 1) / (len(neg) + 2)
    print("%-13s df_T=%d df_N=%d prov=%d  P(t|T)=%.4f P(t|N)=%.4f  w=%.2f" % (t, dr, dn, pv, pr, qn, math.log(pr / qn)))
