import json, os, re, sys

RUNS = sys.argv[1]
MODES = sys.argv[2].split()
CAND = re.compile(r"Stateful-authorization transition candidate (\S+) score (\S+) roleField")
SKIP = re.compile(r"Stateful-authorization transition candidate (\S+) skipped")
TOL = 1e-9
failed = False


def check(name, ok, detail):
    global failed
    print("%s  %s  %s" % ("PASS" if ok else "FAIL", name, detail))
    if not ok:
        failed = True


def log_candidates(mode, tag):
    p = os.path.join(RUNS, "%s-%s.log" % (mode, tag))
    text = open(p, errors="replace").read() if os.path.exists(p) else ""
    scored = {}
    for m in CAND.finditer(text):
        scored[m.group(1)] = float(m.group(2))
    skipped = set()
    for m in SKIP.finditer(text):
        skipped.add(m.group(1))
    return scored, skipped


def py_scores(mode, which):
    p = os.path.join(RUNS, "%s-scores-%s.txt" % (mode, which))
    out = {}
    if os.path.exists(p):
        for line in open(p):
            m = re.match(r"SCORE (\S+) (\S+)$", line.strip())
            if m:
                out[m.group(1)] = float(m.group(2))
    return out


def det970(mode, tag):
    try:
        faults = json.load(open(os.path.join(RUNS, "%s-%s" % (mode, tag), "report.json")))["faults"]["foundFaults"]
        return 970 in [c["code"] for f in faults for c in f["faultCategories"]]
    except (OSError, ValueError, KeyError):
        return None


def mismatches(scored, skipped, py):
    bad = []
    for name, s in scored.items():
        if name not in py or abs(py[name] - s) > TOL:
            bad.append("%s jar %r python %r" % (name, s, py.get(name)))
    want = {k for k, v in py.items() if v > 0}
    got = set(scored) | skipped
    if got != want:
        bad.append("guard set jar-only %s python-only %s" % (sorted(got - want), sorted(want - got)))
    return bad


changed = []
wrong_model_bad = 0
pathf_bad = 0
for mode in MODES:
    nd, nd_skip = log_candidates(mode, "nd")
    ref, ref_skip = log_candidates(mode, "ref")
    py_nd = py_scores(mode, "nodup")
    py_m2 = py_scores(mode, "m2")
    check("%s-reached" % mode, len(nd) > 0 and len(ref) > 0 and len(py_nd) > 0,
          "candidate lines: ND %d, SLM2 %d; python write ops %d" % (len(nd), len(ref), len(py_nd)))
    bad = mismatches(nd, nd_skip, py_nd)
    check("%s-nd-equals-python-nodup" % mode, not bad and len(nd) > 0,
          "%d candidates, every score within %g of op_feats_nodup + nodup model; guard set equal" % (len(nd), TOL)
          if not bad else "; ".join(bad[:3]))
    bad = mismatches(ref, ref_skip, py_m2)
    check("%s-slm2-equals-python-m2" % mode, not bad and len(ref) > 0,
          "%d candidates, every score within %g of op_feats + M2 model; guard set equal" % (len(ref), TOL)
          if not bad else "; ".join(bad[:3]))
    wrong_model_bad += len(mismatches(nd, nd_skip, py_m2))
    pathf_bad += len(mismatches(nd, nd_skip, py_scores(mode, "nodup-pathf")))
    for name, s in nd.items():
        if name in py_m2 and abs(py_m2[name] - s) > 1e-6:
            changed.append("%s %s: ND %.4f, M2 %.4f" % (mode, name, s, py_m2[name]))
    same_guard = {k for k, v in py_nd.items() if v > 0} == {k for k, v in py_m2.items() if v > 0}
    a, b = det970(mode, "nd"), det970(mode, "ref")
    if same_guard:
        check("%s-970-same" % mode, a is not None and a == b,
              "970 ND %s, SLM2 %s (python guard sets equal under both models)" % (a, b))
    else:
        print("INFO  %s-970  970 ND %s, SLM2 %s (python guard sets differ between models, so 970 may differ)" % (mode, a, b))

check("change-exercised", len(changed) > 0,
      "%d candidate scores differ from M2 and match the nodup model, e.g. %s" % (len(changed), "; ".join(changed[:3])))
check("compare-can-fail", wrong_model_bad > 0,
      "ND logs checked against the M2 python scores give %d mismatches" % wrong_model_bad)
check("forgot-path-caught", pathf_bad > 0,
      "ND logs checked against the nodup model scored with path fields still in f: give %d mismatches" % pathf_bad)
sys.exit(1 if failed else 0)
