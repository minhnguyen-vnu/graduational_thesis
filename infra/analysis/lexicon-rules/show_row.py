import csv, io, os, sys

D = "labelling-r2/"
HEAD = ["row_id", "spec_id", "method", "path", "summary", "description",
        "param_names", "body_field_names", "enum_values",
        "annotator", "label", "rule_id", "doubt_token", "note", "final_label"]


def worklist():
    return [l.split()[0] for l in io.open(D + "worklist.txt", encoding="utf-8") if l.strip()]


def done_ids():
    out = {}
    for f in os.listdir(D):
        if f.endswith(".human.csv"):
            for r in csv.DictReader(io.open(D + f, encoding="utf-8")):
                out[r["row_id"]] = r["label"]
    return out


def row_of(rid):
    spec = rid.split("-")[0]
    for r in csv.DictReader(io.open(D + spec + ".csv", encoding="utf-8")):
        if r["row_id"] == rid:
            return r
    raise SystemExit("khong thay " + rid)


def main():
    wl, done = worklist(), done_ids()
    todo = [r for r in wl if r not in done]
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    print("Da gan %d/%d, con %d" % (len(wl) - len(todo), len(wl), len(todo)))
    for rid in todo[:n]:
        r = row_of(rid)
        print("")
        print("row_id           : " + r["row_id"])
        print("method + path    : %s %s" % (r["method"], r["path"]))
        print("summary          : " + (r["summary"] or "(trong)"))
        d = r["description"] or "(trong)"
        print("description      : " + (d[:300] + (" …" if len(d) > 300 else "")))
        print("param_names      : " + (r["param_names"] or "(trong)"))
        print("body_field_names : " + (r["body_field_names"] or "(trong)"))
        print("enum_values      : " + (r["enum_values"] or "(trong)"))


main()
