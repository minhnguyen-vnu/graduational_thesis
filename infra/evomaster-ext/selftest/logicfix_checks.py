import glob
import json
import os
import re
import sys

if sys.argv[1] == "--lock-point":
    out, name = sys.argv[2], sys.argv[3]
    text = open(out + "/" + name + ".log", errors="replace").read()
    ts = re.findall(r"^(\d\d:\d\d:\d\d\.\d{3}) \[main\] DEBUG o\.e\.c\.p\.r\.s\.RestSecurityBuilder", text, re.M)
    before = [json.loads(l)["n"] for l in open(out + "/" + name + "-req.jsonl") if l.strip() and json.loads(l)["t"] < ts[0]]
    print(max(before))
    sys.exit(0)

OUT = sys.argv[1]
FAILED = [0]


def check(name, ok, detail):
    print(("PASS  " if ok else "FAIL  ") + name + "  " + detail)
    if not ok:
        FAILED[0] = 1


def log(mode, tag):
    p = os.path.join(OUT, mode + "-" + tag + ".log")
    return open(p, errors="replace").read() if os.path.exists(p) else ""


def requests(mode, tag):
    p = os.path.join(OUT, mode + "-" + tag + "-req.jsonl")
    if not os.path.exists(p):
        return []
    return [json.loads(l) for l in open(p) if l.strip()]


def faults970(mode, tag):
    n = 0
    names = []
    for f in glob.glob(os.path.join(OUT, mode + "-" + tag, "*.py")):
        for line in open(f, errors="replace"):
            if "Fault970" in line:
                n += 1
                names.append(line.strip()[:120])
    return n, names


def window(mode, tag):
    ts = re.findall(r"^(\d\d:\d\d:\d\d\.\d{3}) \[main\] DEBUG o\.e\.c\.p\.r\.s\.RestSecurityBuilder", log(mode, tag), re.M)
    return (ts[0], ts[-1]) if ts else ("99", "00")


def armed(mode, tag):
    lo, hi = window(mode, tag)
    return [r for r in requests(mode, tag) if r.get("armed") and lo <= r.get("t", "") <= hi]


def ran(mode):
    for tag in ("nd", "lf"):
        e = os.path.join(OUT, mode + "-" + tag + ".exit")
        if not os.path.exists(e) or open(e).read().strip() != "0":
            check(mode + "-ran", False, tag + " exit " + (open(e).read().strip() if os.path.exists(e) else "missing"))
            return False
    check(mode + "-ran", True, "both jars exit 0, requests nd %d lf %d" % (len(requests(mode, "nd")), len(requests(mode, "lf"))))
    return True


def sources_line(text):
    m = re.findall(r"guarded source candidates: \d+ \[[^\]]*\]", text)
    return m


M = "post-source"
if ran(M):
    nd, lf = log(M, "nd"), log(M, "lf")
    snd, slf = sources_line(nd), sources_line(lf)
    check(M + "-sources", any("POST:/notes" in s for s in slf) and not any("POST:/notes" in s for s in snd),
          "lf %s | nd %s" % (slf[:1], snd[:1]))
    fn, fl = faults970(M, "nd"), faults970(M, "lf")
    lf_notes = [r for r in armed(M, "lf") if r["m"] == "PUT"]
    check(M + "-970", fl[0] > 0 and fn[0] == 0,
          "Fault970 lines lf %d nd %d; lf %s" % (fl[0], fn[0], fl[1][:1]))
    check(M + "-c4-ran", "anonymous control: POST:/notes" in lf,
          "lf log has anonymous control on POST:/notes: %s" % ("anonymous control: POST:/notes" in lf))

M = "login-name"
if ran(M):
    a_nd = ["%s %s by %s -> %d" % (r["m"], r["path"], r["caller"], r["code"]) for r in requests(M, "nd")
            if r["path"].startswith("/users/") and r["path"].endswith("/role") and r["caller"] == "boss"]
    a_lf = ["%s %s by %s -> %d" % (r["m"], r["path"], r["caller"], r["code"]) for r in armed(M, "lf")]
    nd_opr = [x for x in a_nd if "/users/opr/" in x]
    lf_bob = [x for x in a_lf if "/users/bob/role" in x and x.endswith("200")]
    check(M + "-target", len(lf_bob) > 0 and len(nd_opr) > 0,
          "lf armed %s | nd calls on /users/opr/role %s" % (lf_bob[:2], nd_opr[:2]))
    fn, fl = faults970(M, "nd"), faults970(M, "lf")
    check(M + "-970", fl[0] > 0 and fn[0] == 0, "Fault970 lines lf %d nd %d" % (fl[0], fn[0]))

M = "enum-lower"
if ran(M):
    v_nd = [r["body"].get("role") for r in armed(M, "nd")]
    v_lf = [r["body"].get("role") for r in armed(M, "lf")]
    check(M + "-values", "EVOMASTER" in v_nd and len(v_lf) > 0 and set(v_lf) <= {"user"},
          "armed role values nd %s lf %s" % (v_nd, v_lf))
    c_nd = re.findall(r"candidate PUT:/users/\{username\}/role .*reducedRoleValues \S+", log(M, "nd"))
    c_lf = re.findall(r"candidate PUT:/users/\{username\}/role .*reducedRoleValues .*", log(M, "lf"))
    check(M + "-no-high", bool(c_nd) and c_nd[0].endswith("reducedRoleValues 3") and bool(c_lf) and c_lf[0].endswith("reducedRoleValues [user]"),
          "nd %s | lf %s" % ([x[-22:] for x in c_nd[:1]], [x[-26:] for x in c_lf[:1]]))
    fn, fl = faults970(M, "nd"), faults970(M, "lf")
    check(M + "-970-kept", fl[0] > 0 and fn[0] > 0, "Fault970 lines lf %d nd %d" % (fl[0], fn[0]))

M = "two-role-fields"
if ran(M):
    q_nd = [(r["query"].get("permission", ["-"])[0], r["query"].get("role", ["-"])[0]) for r in armed(M, "nd")]
    q_lf = [(r["query"].get("permission", ["-"])[0], r["query"].get("role", ["-"])[0]) for r in armed(M, "lf")]
    check(M + "-second-field", len(q_lf) > 0 and all(q[1] == "1" for q in q_lf) and any(q[1] != "1" for q in q_nd),
          "armed (permission, role) nd %s lf %s" % (q_nd, q_lf))

M = "bool-victim"
if ran(M):
    nd, lf = log(M, "nd"), log(M, "lf")
    c_nd = re.findall(r"candidate PUT:/admin/role score \S+ roleField \S+ victimField \S+", nd)
    c_lf = re.findall(r"candidate PUT:/admin/role score \S+ roleField \S+ victimField \S+", lf)
    check(M + "-victim-score", bool(c_nd) and c_nd[0].endswith("body:client_id") and bool(c_lf) and c_lf[0].endswith("null"),
          "nd %s | lf %s" % (c_nd[:1], c_lf[:1]))
    r_nd = re.findall(r"current roles \[false\], reduced role values \[[^\]]*\]", nd)
    r_lf = re.findall(r"current roles \[false\], reduced role values \[[^\]]*\]", lf)
    check(M + "-bool-reduce", bool(r_nd) and r_nd[0].endswith("[true]") and bool(r_lf) and all(x.endswith("[]") for x in r_lf),
          "nd %s | lf %s" % (r_nd[:1], r_lf[:1]))
    s_nd, s_lf = sources_line(nd), sources_line(lf)
    check(M + "-guard-source", any("PUT:/admin/role" in x for x in s_nd) and bool(s_lf) and not any("PUT:/admin/role" in x for x in s_lf),
          "nd %s | lf %s" % (s_nd[:1], s_lf[:1]))
    t_lf = [r for r in armed(M, "lf") if r["m"] == "PATCH" and isinstance(r["body"], dict) and r["body"].get("is_admin") is True]
    t_nd = [r for r in armed(M, "nd") if r["m"] == "PATCH" and isinstance(r["body"], dict) and r["body"].get("is_admin") is True]
    check(M + "-no-elevating-transition", len(t_lf) == 0 and len(t_nd) > 0,
          "armed PATCH with is_admin=true: nd %d lf %d" % (len(t_nd), len(t_lf)))

M = "first-404"
if ran(M):
    nd, lf = log(M, "nd"), log(M, "lf")
    a_nd = ["%s->%d" % (r["path"], r["code"]) for r in armed(M, "nd")]
    a_lf = ["%s->%d" % (r["path"], r["code"]) for r in armed(M, "lf")]
    fn, fl = faults970(M, "nd"), faults970(M, "lf")
    check(M + "-skip-victim", fl[0] > 0 and fn[0] == 0 and "returned 404 for victim" in lf and "returned 404 after a 2xx source" in nd,
          "Fault970 lines lf %d nd %d; armed nd %s lf %s" % (fl[0], fn[0], a_nd, a_lf))

M = "query-username"
if ran(M):
    a_nd = [(r["path"], r["query"].get("username", ["-"])[0], r["code"]) for r in armed(M, "nd")]
    a_lf = [(r["path"], r["query"].get("username", ["-"])[0], r["code"]) for r in armed(M, "lf")]
    ok_lf = len(a_lf) > 0 and all(p == "/users/%s/role" % u for p, u, c in a_lf)
    bad_nd = [x for x in a_nd if x[0] != "/users/%s/role" % x[1]]
    fn, fl = faults970(M, "nd"), faults970(M, "lf")
    check(M + "-login-field", ok_lf and len(bad_nd) > 0 and fl[0] > 0 and fn[0] == 0,
          "armed (path, query username, code) nd %s lf %s; Fault970 lf %d nd %d" % (a_nd[:3], a_lf[:3], fl[0], fn[0]))

M = "nested-role"
if ran(M):
    def roles(tag):
        out = []
        for r in armed(M, tag):
            s = r["body"].get("settings") if isinstance(r["body"], dict) else None
            out.append((s.get("role") if isinstance(s, dict) else None, r["code"]))
        return out
    r_nd, r_lf = roles("nd"), roles("lf")
    fn, fl = faults970(M, "nd"), faults970(M, "lf")
    check(M + "-keep-parent", len(r_lf) > 0 and all(x[0] is not None for x in r_lf) and any(x[0] is None for x in r_nd)
          and fl[0] > 0 and fn[0] == 0,
          "armed (settings.role, code) nd %s lf %s; Fault970 lf %d nd %d" % (r_nd[:3], r_lf[:3], fl[0], fn[0]))

M = "num-enum"
if ran(M):
    nd, lf = log(M, "nd"), log(M, "lf")
    v_lf = [r["body"].get("access_level") for r in armed(M, "lf")]
    fn, fl = faults970(M, "nd"), faults970(M, "lf")
    check(M + "-set", "could not set reduced role '10'" in nd and 10 in v_lf and fl[0] > 0 and fn[0] == 0,
          "nd 'could not set reduced role 10': %s; lf armed access_level %s; Fault970 lf %d nd %d"
          % ("could not set reduced role '10'" in nd, v_lf, fl[0], fn[0]))

M = "c4-intact"
if ran(M):
    nd, lf = log(M, "nd"), log(M, "lf")
    u_nd, u_lf = nd.count("Discarded an UNCONFIRMED"), lf.count("Discarded an UNCONFIRMED")
    k_nd, k_lf = nd.count("already reduced in this phase"), lf.count("already reduced in this phase")
    check(M + "-unlock", u_nd > 0 and u_lf > u_nd and k_nd > 0 and k_lf == 0,
          "UNCONFIRMED nd %d lf %d; 'already reduced in this phase' nd %d lf %d" % (u_nd, u_lf, k_nd, k_lf))

M = "no-path-id"
if ran(M):
    def calls(tag):
        lo, hi = window(M, tag)
        return ["%s->%d" % (r["path"], r["code"]) for r in requests(M, tag)
                if r["m"] == "PUT" and re.fullmatch(r"/users/[^/]+", r["path"]) and lo <= r.get("t", "") <= hi]
    p_nd, p_lf = calls("nd"), calls("lf")
    lf = log(M, "lf")
    check(M + "-skip", len(p_nd) > 0 and len(p_lf) == 0 and "could not target victim" in lf,
          "builder PUT /users/{id} calls nd %s lf %s; lf 'could not target victim': %s" % (p_nd[:3], p_lf[:3], "could not target victim" in lf))

M = "source-401"
if ran(M):
    nd, lf = log(M, "nd"), log(M, "lf")
    b_nd = re.findall(r"victim 'bob', operator '[^']+', codes 401/", nd)
    b_lf = re.findall(r"victim 'bob', operator '[^']+', codes 401/", lf)
    check(M + "-stop", len(b_nd) > 1 and len(b_lf) == 1,
          "VOID attempts with source 401 on victim bob: nd %d lf %d" % (len(b_nd), len(b_lf)))

sys.exit(FAILED[0])
