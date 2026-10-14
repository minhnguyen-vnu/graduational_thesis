"""Uoc luong co mau o muc API: do rong CI 95% cua mot ty le, va so API can boc ngau nhien theo ty le API duong da quan sat."""
import math
from load import *

F = load_all()
O = ops(F)
for sp in ("train", "dev", "test"):
    specs = {op[0]["spec"] for op in O.values() if op[0]["split"] == sp}
    a = {op[0]["spec"] for op in O.values() if op[0]["split"] == sp and any(f["A"] for f in op)}
    ac = {op[0]["spec"] for op in O.values() if op[0]["split"] == sp and any(f["C"] for f in op)
          and any(f["A"] in ("role", "admin") for f in op)}
    print("%s: API=%d, API co A=%d (%.0f%%), API co op A role/admin + C=%d (%.0f%%)" % (
        sp, len(specs), len(a), 100.0 * len(a) / len(specs), len(ac), 100.0 * len(ac) / len(specs)))
for n in (21, 50, 100):
    print("n=%d API duong, p=0.5: nua do rong CI 95%% = %.2f" % (n, 1.96 * math.sqrt(0.25 / n)))
need = math.ceil((1.96 / 0.10) ** 2 * 0.25)
print("can %d API duong cho nua do rong 0.10" % need)
for rate in (0.23, 0.14):
    print("  voi ty le API duong %.0f%%: can boc ~%d API" % (100 * rate, math.ceil(need / rate)))
