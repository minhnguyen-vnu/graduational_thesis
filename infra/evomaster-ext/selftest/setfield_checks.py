import json
import re
import sys

OUT = sys.argv[1]
FAILED = []


def check(name, ok, good, bad):
    print(("PASS  %-15s %s" % (name, good)) if ok else ("FAIL  %s  --  %s" % (name, bad)))
    if not ok:
        FAILED.append(name)


def records(tag):
    try:
        return [json.loads(l) for l in open("%s/%s-stub.jsonl" % (OUT, tag))]
    except (OSError, ValueError):
        return []


def triples(rs):
    out = []
    seq = [r for r in rs if r["path"] != "/auth/login"]
    for i in range(1, len(seq) - 1):
        s, t, f = seq[i - 1], seq[i], seq[i + 1]
        if (s["method"] == "POST" and s["path"] != "/thesis/reset" and s["status"] == 200
                and t["method"] == "PATCH" and t["path"] == "/users/uid-%s" % s["caller"]
                and t["caller"] not in (None, s["caller"])
                and f["method"] == s["method"] and f["path"] == s["path"] and f["caller"] == s["caller"]):
            out.append(t)
    return out


def det970(tag):
    try:
        faults = json.load(open("%s/%s/report.json" % (OUT, tag)))["faults"]["foundFaults"]
        return 1 if 970 in [c["code"] for f in faults for c in f["faultCategories"]] else 0
    except (OSError, ValueError, KeyError):
        return "ERR"


def log(tag):
    try:
        return open("%s/%s.log" % (OUT, tag), errors="ignore").read()
    except OSError:
        return ""


def admin_value(t):
    return (t["body"] or {}).get("is_admin", "absent")


exits = {tag: open("%s/%s.exit" % (OUT, tag)).read().strip() for tag in ("new", "old")}
check("S-ran", exits["new"] == "0" and exits["old"] == "0",
      "both runs exited 0", "exit codes new=%s old=%s" % (exits["new"], exits["old"]))

field = re.search(r"transition candidate PATCH:/users/\{id\} score \S+ roleField body:is_admin", log("new"))
check("S-field", field is not None,
      "builder scored PATCH:/users/{id} with roleField body:is_admin (type [boolean, null])",
      "no 'transition candidate PATCH:/users/{id} ... roleField body:is_admin' line in new.log")

new_t = triples(records("new"))
check("S-reached", len(new_t) > 0,
      "%d triple transitions PATCH /users/uid-<victim> on the stub" % len(new_t),
      "no source -> PATCH /users/uid-<victim> -> follow-up sequence in new-stub.jsonl")

values = [admin_value(t) for t in new_t]
check("S-false", len(new_t) > 0 and all(v is False for v in values),
      "every triple transition body has is_admin false: %s" % sorted({json.dumps(t["body"]) for t in new_t}),
      "is_admin values in triple transitions: %s" % [json.dumps(v) for v in values])

demoted = [t for t in new_t if t["status"] == 200 and t.get("demoted")]
check("S-demoted", len(demoted) > 0,
      "%d triple transitions returned 200 and turned is_admin true -> false" % len(demoted),
      "no triple transition demoted the victim: statuses %s" % [t["status"] for t in new_t])

d = det970("new")
check("S-det970", d == 1, "new report.json has fault 970", "new det970=%s" % d)

old_t = triples(records("old"))
old_values = [admin_value(t) for t in old_t]
nulls = sum(1 for v in old_values if v is None)
check("checks-can-fail", nulls > 0,
      "old jar: %d of %d triple transition bodies carry is_admin null -> S-false FAILS on it; old det970=%s"
      % (nulls, len(old_t), det970("old")),
      "old jar sent no is_admin null in %d triple transitions (%s); the checks do not separate the jars"
      % (len(old_t), [json.dumps(v) for v in old_values]))

sys.exit(1 if FAILED else 0)
