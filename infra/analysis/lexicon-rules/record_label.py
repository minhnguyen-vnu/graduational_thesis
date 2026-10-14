import csv, io, os, sys

D = "labelling-r2/"
RULES = {"R2","R3","R4","R5","R6","N1","N2","N3","N4","N5","N6","N7","N8","N9","U1","U2","U3"}
HEAD = ["row_id", "spec_id", "method", "path", "summary", "description",
        "param_names", "body_field_names", "enum_values",
        "annotator", "label", "rule_id", "doubt_token", "note", "final_label"]


def main():
    rid, label, rule = sys.argv[1], sys.argv[2].upper(), sys.argv[3].upper()
    doubt = sys.argv[4] if len(sys.argv) > 4 else ""
    note = sys.argv[5] if len(sys.argv) > 5 else ""
    if label not in ("R", "N", "U"):
        raise SystemExit("label phai la R, N hoac U")
    if rule not in RULES or rule[0] != label:
        raise SystemExit("rule_id khong hop le cho nhan " + label)
    if label == "U" and not doubt:
        raise SystemExit("nhan U bat buoc co doubt_token")
    spec = rid.split("-")[0]
    src = {r["row_id"]: r for r in csv.DictReader(io.open(D + spec + ".csv", encoding="utf-8"))}
    if rid not in src:
        raise SystemExit("khong thay " + rid)
    out = D + spec + ".human.csv"
    rows = list(csv.DictReader(io.open(out, encoding="utf-8"))) if os.path.exists(out) else []
    rows = [r for r in rows if r["row_id"] != rid]
    r = dict(src[rid])
    r.update({"annotator": "human", "label": label, "rule_id": rule,
              "doubt_token": doubt, "note": note, "final_label": ""})
    rows.append(r)
    rows.sort(key=lambda x: x["row_id"])
    with io.open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, HEAD, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)
    print("%s -> %s %s (%s, %d dong)" % (rid, label, rule, os.path.basename(out), len(rows)))


main()
