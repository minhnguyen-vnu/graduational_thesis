#!/usr/bin/env python3
"""Structural hand-audit of every generated test that carries fault 970.

Reads the emitted Python tests, not the status strings, and checks the four things
CLAUDE.md 5.2 says a valid MR-A1 triple must show:
  A  source and follow-up carry the SAME credential variable
  B  no /login call happens BETWEEN them  (the stale-token replay is the whole point)
  C  the transition is performed by a DIFFERENT credential
  D  source 2xx, transition 2xx, follow-up 2xx   (a fault, not a pass or a VOID)
Anything it cannot parse is reported as UNPARSED, never silently skipped.
"""
import re, sys, glob, os, collections

CALL = re.compile(r'res_(\d+)\s*=\s*requests\s*\\?\s*\.\s*(get|post|put|patch|delete)\('
                  r'\s*self\.baseUrlOfSut\s*\+\s*"([^"]+)"', re.S)
COOK = re.compile(r'cookies\s*=\s*(cookies_\w+)')
STAT = re.compile(r'assert\s+res_(\d+)\.status_code\s*==\s*(\d+)')
LOGIN = re.compile(r'\.post\(self\.baseUrlOfSut\s*\+\s*"/login"')

def audit(path):
    src = open(path, encoding="utf-8", errors="replace").read()
    fns = list(re.finditer(r'\n    def (test_\w+)\(', src))
    out = []
    for i, m in enumerate(fns):
        body = src[m.start(): fns[i+1].start() if i+1 < len(fns) else len(src)]
        if "Fault970" not in body:
            continue
        name = m.group(1)
        # order of appearance of the real (non-login) calls
        calls = []
        for c in CALL.finditer(body):
            seg = body[c.start(): c.start()+900]
            ck = COOK.search(seg)
            calls.append({"i": c.group(1), "verb": c.group(2).upper(),
                          "path": c.group(3).split("?")[0], "cook": ck.group(1) if ck else None,
                          "pos": c.start()})
        codes = {g(1): g(2) for g in (m2.groups for m2 in STAT.finditer(body)) for g in [lambda k, gg=g(): gg[k-1]]} if False else \
                {mm.group(1): mm.group(2) for mm in STAT.finditer(body)}
        # the 970 marker sits immediately before the FOLLOW-UP
        mk = body.find("# Fault970")
        if mk < 0 or len(calls) < 3:
            out.append((name, "UNPARSED", {})); continue
        follow = next((c for c in calls if c["pos"] > mk), None)
        before = [c for c in calls if c["pos"] < mk]
        if follow is None or len(before) < 2:
            out.append((name, "UNPARSED", {})); continue
        trans = before[-1]
        source = next((c for c in reversed(before[:-1])
                       if c["cook"] == follow["cook"] and c["path"] == follow["path"]), None)
        if source is None:
            out.append((name, "UNPARSED", {})); continue
        seg = body[source["pos"]: follow["pos"]]
        chk = {
            "A_same_cred":  source["cook"] == follow["cook"] and follow["cook"] is not None,
            "B_no_relogin": not LOGIN.search(seg),
            "C_other_op":   trans["cook"] is not None and trans["cook"] != follow["cook"],
            "D_statuses":   (codes.get(source["i"], "?"), codes.get(trans["i"], "?"), codes.get(follow["i"], "?")),
        }
        ok = chk["A_same_cred"] and chk["B_no_relogin"] and chk["C_other_op"] and \
             all(s.startswith("2") for s in chk["D_statuses"])
        out.append((name, "PASS" if ok else "FAIL", {
            "guard": f'{follow["verb"]} {follow["path"]}', "victim": follow["cook"],
            "operator": trans["cook"], "transition": f'{trans["verb"]} {trans["path"]}',
            "statuses": "/".join(chk["D_statuses"]),
            "A": chk["A_same_cred"], "B": chk["B_no_relogin"], "C": chk["C_other_op"]}))
    return out

tot = collections.Counter(); guards = collections.Counter(); pairs = collections.Counter()
for d in sorted(glob.glob(sys.argv[1])):
    f = os.path.join(d, "EvoMaster_faults_Test.py")
    if not os.path.exists(f):
        print(f"{os.path.basename(d):24s} NO FAULT FILE"); continue
    r = audit(f)
    c = collections.Counter(v for _, v, _ in r)
    tot.update(c)
    print(f"{os.path.basename(d):24s} 970-tests={len(r):2d}  " +
          "  ".join(f"{k}={v}" for k, v in sorted(c.items())))
    for n, v, info in r:
        if v != "PASS":
            print(f"    !! {v} {n} {info}")
        else:
            guards[info["guard"]] += 1
            pairs[(info["victim"], info["operator"])] += 1
print()
print("TOTAL", dict(tot))
print("guards :", dict(guards))
print("pairs  :", {f"{a}->{b}": n for (a, b), n in pairs.items()})
