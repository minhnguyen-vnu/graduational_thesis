#!/usr/bin/env python3
import re, sys, glob, os, json

LOGIN_PATHS = ("/auth/login", "/users/v1/login")

CALL = re.compile(r'res_(\d+)\s*=\s*requests\s*\\?\s*\.\s*(get|post|put|patch|delete)\s*\(', re.S)
AUTH = re.compile(r'headers\["Authorization"\]\s*=\s*(auth_\w+)')
STAT = re.compile(r'assert\s+res_(\d+)\.status_code\s*==\s*(\d+)')
URLLIT = re.compile(r'"(/[^"]*)"')
DIGITS = re.compile(r'/\d+')


def norm(path):
    return DIGITS.sub("/{id}", path.split("?")[0].rstrip("/") or "/")


def parse_calls(body):
    marks = [(m.start(), m.group(1), m.group(2).upper()) for m in CALL.finditer(body)]
    codes = {m.group(1): m.group(2) for m in STAT.finditer(body)}
    calls = []
    for k, (pos, idx, verb) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(body)
        expr = body[pos:end]
        lits = URLLIT.findall(expr)
        path = lits[0] if lits else None
        head = body[marks[k - 1][0] if k else 0:pos]
        a = AUTH.findall(head)
        calls.append({
            "i": idx, "verb": verb, "pos": pos,
            "path": path, "npath": norm(path) if path else None,
            "auth": a[-1] if a else None,
            "code": codes.get(idx, "?"),
            "is_login": bool(path) and any(path.startswith(p) for p in LOGIN_PATHS),
        })
    return calls


def split_tests(src):
    fns = list(re.finditer(r'\n    def (test_\w+)\(', src))
    for i, m in enumerate(fns):
        end = fns[i + 1].start() if i + 1 < len(fns) else len(src)
        yield m.group(1), src[m.start():end]


def audit_fault(name, body):
    calls = [c for c in parse_calls(body) if not c["is_login"]]
    logins = [c for c in parse_calls(body) if c["is_login"]]
    mk = body.find("# Fault970")
    if mk < 0 or len(calls) < 3:
        return name, "UNPARSED", {}
    follow = next((c for c in calls if c["pos"] > mk), None)
    before = [c for c in calls if c["pos"] < mk]
    if follow is None or len(before) < 2:
        return name, "UNPARSED", {}
    trans = before[-1]
    source = next((c for c in reversed(before[:-1])
                   if c["auth"] == follow["auth"] and c["npath"] == follow["npath"]
                   and c["verb"] == follow["verb"]), None)
    if source is None:
        return name, "UNPARSED", {}
    between = (source["pos"], follow["pos"])
    chk = {
        "A_same_cred": follow["auth"] is not None and source["auth"] == follow["auth"],
        "B_no_relogin": not any(between[0] < l["pos"] < between[1] for l in logins),
        "C_other_op": trans["auth"] is not None and trans["auth"] != follow["auth"],
        "D_statuses": (source["code"], trans["code"], follow["code"]),
        "endpoint": f'{follow["verb"]} {follow["npath"]}',
        "transition": f'{trans["verb"]} {trans["npath"]}',
        "cred": f'{source["auth"]} / op {trans["auth"]}',
    }
    ok = (chk["A_same_cred"] and chk["B_no_relogin"] and chk["C_other_op"]
          and all(s.startswith("2") for s in chk["D_statuses"]))
    return name, ("PASS" if ok else "FAIL"), chk


def find_silent_triples(body):
    calls = [c for c in parse_calls(body) if not c["is_login"]]
    logins = [c for c in parse_calls(body) if c["is_login"]]
    found = []
    for k in range(len(calls) - 2):
        src = calls[k]
        if src["auth"] is None or not src["code"].startswith("2"):
            continue
        if src["verb"] not in ("PUT", "PATCH", "POST", "DELETE"):
            continue
        for j in range(k + 1, len(calls)):
            fu = calls[j]
            if fu["auth"] != src["auth"] or fu["npath"] != src["npath"] or fu["verb"] != src["verb"]:
                continue
            mid = [c for c in calls[k + 1:j]
                   if c["auth"] is not None and c["auth"] != src["auth"]
                   and c["code"].startswith("2")]
            if not mid:
                continue
            if any(src["pos"] < l["pos"] < fu["pos"] for l in logins):
                continue
            found.append({
                "endpoint": f'{src["verb"]} {src["npath"]}',
                "statuses": f'{src["code"]}/{mid[-1]["code"]}/{fu["code"]}',
                "cred": src["auth"], "op": mid[-1]["auth"],
                "transition": f'{mid[-1]["verb"]} {mid[-1]["npath"]}',
            })
            break
    return found


def run(folder):
    files = sorted(glob.glob(os.path.join(folder, "*Test.py")))
    faults, silent, unparsed = [], [], []
    for f in files:
        src = open(f, encoding="utf-8", errors="replace").read()
        for name, body in split_tests(src):
            if "Fault970" in body:
                n, verdict, chk = audit_fault(name, body)
                if verdict == "UNPARSED":
                    unparsed.append((os.path.basename(f), n))
                else:
                    faults.append((os.path.basename(f), n, verdict, chk))
            else:
                for t in find_silent_triples(body):
                    silent.append((os.path.basename(f), name, t))
    return {"folder": folder, "faults": faults, "silent": silent, "unparsed": unparsed}


def main():
    targets = sys.argv[1:]
    if not targets:
        print("usage: audit970_seeded.py <run-folder> [...]", file=sys.stderr)
        sys.exit(2)
    tot_p = tot_f = tot_u = tot_s = 0
    rows = []
    for t in targets:
        r = run(t)
        p = sum(1 for x in r["faults"] if x[2] == "PASS")
        f = sum(1 for x in r["faults"] if x[2] == "FAIL")
        u, s = len(r["unparsed"]), len(r["silent"])
        tot_p, tot_f, tot_u, tot_s = tot_p + p, tot_f + f, tot_u + u, tot_s + s
        rows.append((os.path.basename(t.rstrip("/")), p, f, u, s))
        for fn, name, verdict, chk in r["faults"]:
            if verdict == "FAIL":
                print(f'  FAIL {os.path.basename(t.rstrip("/"))} {fn}::{name} {json.dumps(chk)}')
        for fn, name in r["unparsed"]:
            print(f'  UNPARSED {os.path.basename(t.rstrip("/"))} {fn}::{name}')
    print(f'{"run":<28}{"970 PASS":>9}{"970 FAIL":>9}{"UNPARSED":>9}{"silent triples":>15}')
    for name, p, f, u, s in rows:
        print(f'{name:<28}{p:>9}{f:>9}{u:>9}{s:>15}')
    print(f'{"TOTAL":<28}{tot_p:>9}{tot_f:>9}{tot_u:>9}{tot_s:>15}')
    sys.exit(1 if (tot_f or tot_u) else 0)


if __name__ == "__main__":
    main()
