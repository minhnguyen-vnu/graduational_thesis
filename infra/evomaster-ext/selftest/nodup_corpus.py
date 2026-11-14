import json, os, sys

LR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "analysis", "lexicon-rules"))
FILES = ["field-labelling-r4-20261006/rows-all.jsonl", "relabel-20261101/nop-hoi-dong/op-hoc.jsonl",
         "relabel-20261101/nop-hoi-dong/op-thi.jsonl"]

out = set()
for name in FILES:
    for line in open(os.path.join(LR, name)):
        if not line.strip():
            continue
        r = json.loads(line)
        out.add(r["path"])
        for f in r["fields"]:
            out.add(f["name"])
            for part in f["name"].split("."):
                out.add(part)
            for v in f.get("enum") or []:
                out.add(str(v))
out = sorted(s for s in out if "\n" not in s and "\r" not in s)
with open(sys.argv[1], "w") as fh:
    fh.write("\n".join(out) + "\n")
print("corpus strings %d from %d files" % (len(out), len(FILES)))
