import json
import os
import re
import sys

OUT = sys.argv[1]
FAMILIES = [("p2", sys.argv[2].split()), ("cand", sys.argv[3].split()), ("setfield", sys.argv[4].split()),
            ("paths", sys.argv[5].split() if len(sys.argv) > 5 else [])]
RESULTS = []

TRACE = re.compile(r"Stateful-authorization|MR-A1|Privilege-restore")
SCHEMA = re.compile(r"transition candidate \S+ (score|skipped)|model tables")
DEBUG_PREFIX = re.compile(r"^\d\d:\d\d:\d\d\.\d+ \[[^\]]+\] \w+ +\S+ - ")

REACH = {
    ("p2", "anon-deny"): "re-login probe INCONCLUSIVE",
    ("p2", "enum-role"): "anonymous control",
    ("cand", "noop-decoy"): "(candidate 2 of",
    ("cand", "restore-budget"): "Privilege-restore accepted",
    ("cand", "protected-victim"): "already refused victim",
    ("cand", "revoke"): "REVOKED",
    ("cand", "proven-404"): "returned 404 for victim",
    ("setfield", "setfield"): "Assembled a stateful-authorization",
    ("paths", "cap5"): "not proven after 5 attempts",
    ("paths", "cap20"): "attempt cap 20 reached",
    ("paths", "unavailable"): "restore unavailable",
    ("paths", "budget"): "restore budget of 3 spent",
}


def check(name, ok, detail):
    RESULTS.append(ok)
    print("%s  %-44s %s" % ("PASS" if ok else "FAIL", name, detail))


def base(fam, mode, tag):
    name = tag if fam == "setfield" else "%s-%s" % (mode, tag)
    return os.path.join(OUT, fam, name)


def trace(fam, mode, tag):
    path = base(fam, mode, tag) + ".log"
    if not os.path.exists(path):
        return None
    out = []
    for line in open(path, errors="replace").read().splitlines():
        if not TRACE.search(line):
            continue
        line = DEBUG_PREFIX.sub("", line)
        if line.startswith("* "):
            line = line[2:]
        out.append(line)
    return out


def det970(fam, mode, tag):
    try:
        faults = json.load(open(os.path.join(base(fam, mode, tag), "report.json")))["faults"]["foundFaults"]
        return 970 in [c["code"] for f in faults for c in f["faultCategories"]]
    except (OSError, ValueError, KeyError):
        return None


def command(fam, mode, tag):
    path = base(fam, mode, tag) + ".cmd"
    return open(path).read().strip() if os.path.exists(path) else None


def first_diff(a, b):
    for i in range(max(len(a), len(b))):
        x = a[i] if i < len(a) else "<end>"
        y = b[i] if i < len(b) else "<end>"
        if x != y:
            return "line %d: %r vs %r" % (i + 1, x[:120], y[:120])
    return "none"


for fam, modes in FAMILIES:
    for mode in modes:
        key = "%s-%s" % (fam, mode)
        new, ref_a, ref_b = trace(fam, mode, "new"), trace(fam, mode, "refA"), trace(fam, mode, "refB")
        if new is None or ref_a is None or ref_b is None:
            check(key + "-ran", False, "missing log new %s refA %s refB %s" % (new is None, ref_a is None, ref_b is None))
            continue

        cmd_new, cmd_ref = command(fam, mode, "new"), command(fam, mode, "refA")
        jar_free = lambda c: re.sub(r"[-/](new|refA)$", "/TAG", re.sub(r"-jar \S+", "-jar JAR", c or ""))
        check(key + "-cmdline-only-jar-differs",
              cmd_new is not None and jar_free(cmd_new) == jar_free(cmd_ref) and cmd_new != cmd_ref,
              "full command lines differ only in the jar path")

        schema_new = [l for l in new if SCHEMA.search(l)]
        schema_ref = [l for l in ref_a if SCHEMA.search(l)]
        check(key + "-schema-lines-identical", len(schema_ref) > 0 and schema_new == schema_ref,
              "%d schema-only lines, first diff %s" % (len(schema_ref), first_diff(schema_new, schema_ref)))

        aa = ref_a == ref_b
        print("INFO  %-44s %s" % (key + "-aa", "P2f twice: identical (%d lines)" % len(ref_a) if aa
                                   else "P2f twice: differ, %s" % first_diff(ref_a, ref_b)))
        if aa:
            check(key + "-trace-identical", new == ref_a,
                  "%d stateful lines; first diff %s" % (len(new), first_diff(new, ref_a)))
        else:
            same = new == ref_a or new == ref_b
            check(key + "-trace-identical-to-one-ref", same,
                  "A/A differs, so new must equal one P2f run; vs refA %s; vs refB %s"
                  % (first_diff(new, ref_a), first_diff(new, ref_b)))

        d = (det970(fam, mode, "new"), det970(fam, mode, "refA"), det970(fam, mode, "refB"))
        check(key + "-970-same", d[0] is not None and d[0] in (d[1], d[2]),
              "970 new %s refA %s refB %s" % d)

        marker = REACH.get((fam, mode))
        if marker:
            in_ref = any(marker in l for l in ref_a)
            in_new = any(marker in l for l in new)
            check(key + "-path-reached", in_ref and in_new,
                  "%r in P2f no-reset %s, in new %s" % (marker, in_ref, in_new))

print("summary %d/%d checks passed" % (sum(RESULTS), len(RESULTS)))
sys.exit(0 if all(RESULTS) else 1)
