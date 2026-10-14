"""Thanh phan cua F1 trung binh tren dev (select.json): danh sach nao quyet dinh R4 thang, va moi danh sach
co bao nhieu truong duong / nha cung cap tren dev."""
import json, os
from lib import *

s = json.load(open(os.path.join(R2, "select.json")))
LISTS = ("A-role", "A-admin", "C", "B-low", "B-high")
print("%-8s %s" % ("", "  ".join("%-6s" % r for r in ("R0", "R1", "R2", "R3", "R4"))), " | duong dev / nha_cc")
for n in LISTS:
    d = s["per_rule"]["R4"][n]["dev"]
    print("%-8s %s | %d / %d" % (n, "  ".join("%.3f " % s["per_rule"][r][n]["dev"]["f1"] for r in ("R0", "R1", "R2", "R3", "R4")),
                                 d["pos"], d["pos_providers"]))
print("mean    ", "  ".join("%.3f " % s["per_rule"][r]["mean_f1"] for r in ("R0", "R1", "R2", "R3", "R4")))
print("\nR4 words:", {n: s["per_rule"]["R4"][n]["words"] for n in LISTS})
print("R1 words:", {n: s["per_rule"]["R1"][n]["words"] for n in LISTS})
# chi tinh 2 danh sach co nhieu duong nhat
for r in ("R0", "R1", "R2", "R3", "R4"):
    print(r, "TB F1 chi A-role + C: %.3f" % ((s["per_rule"][r]["A-role"]["dev"]["f1"] + s["per_rule"][r]["C"]["dev"]["f1"]) / 2))
