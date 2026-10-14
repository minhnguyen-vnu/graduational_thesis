import json
import sys

SRC = sys.argv[1]
DST = sys.argv[2]

KILL = {
    ("post", "/logout"),
    ("post", "/logoutAll"),
    ("delete", "/user"),
    ("patch", "/user"),
}

doc = json.load(open(SRC, encoding="utf-8"))
removed = []
for path in list(doc.get("paths", {}).keys()):
    item = doc["paths"][path]
    for method in list(item.keys()):
        if (method.lower(), path) in KILL:
            removed.append(method.upper() + " " + path)
            del item[method]
    if not any(m.lower() in {"get", "post", "put", "patch", "delete"} for m in item):
        del doc["paths"][path]

json.dump(doc, open(DST, "w", encoding="utf-8"))
kept = sum(1 for p, it in doc["paths"].items() for m in it if m.lower() in {"get", "post", "put", "patch", "delete"})
print("stripped " + str(len(removed)) + " ops; kept " + str(kept) + " ops")
for r in removed:
    print("  - " + r)
missing = KILL - {(r.split(" ", 1)[0].lower(), r.split(" ", 1)[1]) for r in removed}
if missing:
    print("WARN not found: " + str(sorted(missing)))
    sys.exit(1)
