import os
import re
import sys

OUT = sys.argv[1]
MODES = sys.argv[2:]
RESULTS = []

CAND = re.compile(r"transition candidate (\S+) score (-?[0-9.]+) roleField (\S+) victimField (\S+) reducedRoleValues")
REDUCED = re.compile(r"reduced role values (\[[^\]]*\])")
ANON = re.compile(r"anonymous control: \S+=(\S+)")
FIRED = "Constructed a stateful-authorization (MR-A1) test revealing privilege persistence"


def check(name, ok, detail):
    RESULTS.append(ok)
    print("%s  %-34s %s" % ("PASS" if ok else "FAIL", name, detail))


def logtext(mode, tag):
    p = os.path.join(OUT, "%s-%s.log" % (mode, tag))
    return open(p, errors="replace").read() if os.path.exists(p) else ""


def candidates(text):
    out = {}
    for m in CAND.finditer(text):
        name, score, role, victim = m.group(1), float(m.group(2)), m.group(3), m.group(4)
        out[name] = (score, role, victim)
    return out


def scores(mode):
    p = os.path.join(OUT, "%s-scores.txt" % mode)
    out = {}
    if not os.path.exists(p):
        return out
    for line in open(p):
        m = re.match(r"SCORE (\S+) (\S+) (-?[0-9.]+) gate=(\S+) role=(\S+) victim=(\S+)", line)
        if m:
            out["%s:%s" % (m.group(1), m.group(2))] = (float(m.group(3)), m.group(4) == "True", m.group(5), m.group(6))
    return out


def leaf(colon):
    return colon.split(":")[-1] if colon not in ("null", "-", "") else "-"


def reduced_lists(text):
    return [m.group(1) for m in REDUCED.finditer(text)]


def anon_code(text):
    m = ANON.search(text)
    return m.group(1) if m else None


def parity(mode):
    text = logtext(mode, "new")
    cand = candidates(text)
    sc = scores(mode)
    if not sc:
        check("%s-parity" % mode, False, "python scores missing")
        return
    bad = []
    seen = 0
    for name, (jscore, jrole, jvictim) in cand.items():
        if name not in sc:
            continue
        seen += 1
        pscore, pgate, prole, pvictim = sc[name]
        if round(jscore, 2) != round(pscore, 2):
            bad.append("%s score jar %.4f py %.4f" % (name, jscore, pscore))
        if leaf(jrole) != prole:
            bad.append("%s role jar %s py %s" % (name, leaf(jrole), prole))
        if leaf(jvictim) != pvictim:
            bad.append("%s victim jar %s py %s" % (name, leaf(jvictim), pvictim))
    check("%s-parity" % mode, seen > 0 and not bad,
          "%d candidate(s) matched python; mismatches %s" % (seen, bad[:4]))


def fired(mode, tag="new"):
    return FIRED in logtext(mode, tag)


MODE_CHECKS = {}


def define(mode, fn):
    MODE_CHECKS[mode] = fn


def first_reduced(t):
    rl = reduced_lists(t)
    firsts = [x.strip("[]").split(",")[0].strip().strip("'") for x in rl if x.strip("[]")]
    return firsts, rl


def enum_role(mode):
    t = logtext(mode, "new")
    check("%s-fires" % mode, fired(mode), "970 constructed = %s" % fired(mode))
    firsts, rl = first_reduced(t)
    check("%s-reduced-low-first" % mode, "VIEWER" in firsts, "reduced role value lists %s (low value first)" % rl)
    code = anon_code(t)
    check("%s-anon-not-403" % mode, code is not None and code != "403",
          "anonymous control code %s (401 source -> 970 still fires)" % code)


def bool_restricted(mode):
    t = logtext(mode, "new")
    cand = candidates(t)
    rf = next((v[1] for k, v in cand.items() if k == "PATCH:/users/{username}"), None)
    check("%s-rolefield-restricted" % mode, rf is not None and leaf(rf) == "restricted",
          "roleField %s (bool flip direction is validated on real artifact-keeper is_admin)" % rf)


def num_two(mode):
    t = logtext(mode, "new")
    cand = candidates(t)
    rf = next((v[1] for k, v in cand.items() if k == "POST:/api/set_user_permission"), None)
    check("%s-rolefield-permission" % mode, rf is not None and leaf(rf) == "permission", "roleField %s" % rf)
    firsts, rl = first_reduced(t)
    check("%s-reduced-first-1" % mode, "1" in firsts, "reduced role value lists %s" % rl)
    check("%s-fires" % mode, fired(mode), "970 constructed = %s" % fired(mode))


def path_id_username(mode):
    t = logtext(mode, "new")
    cand = candidates(t)
    vf = next((v[2] for k, v in cand.items() if k == "PATCH:/users/{id}"), None)
    check("%s-victim-body-username" % mode, vf is not None and vf == "body:username", "victimField %s" % vf)
    check("%s-fires" % mode, fired(mode),
          "970 constructed = %s (fires only if the path patch put the victim id into {id})" % fired(mode))


def access_level(mode):
    t = logtext(mode, "new")
    cand = candidates(t)
    rf = next((v[1] for k, v in cand.items() if k == "PUT:/groups/{id}/members/{username}"), None)
    check("%s-rolefield-access_level" % mode, rf is not None and leaf(rf) == "access_level",
          "roleField %s (enabled bool is rejected)" % rf)
    check("%s-fires" % mode, fired(mode), "970 constructed = %s" % fired(mode))


def anon_deny(mode):
    for tag in ("new", "d1"):
        t = logtext(mode, tag)
        code = anon_code(t)
        inc = "INCONCLUSIVE" in t
        check("%s-%s-anon-403-inconclusive" % (mode, tag), code == "403" and inc and not fired(mode, tag),
              "anonymous control code %s, INCONCLUSIVE %s, fired %s" % (code, inc, fired(mode, tag)))


def gate_low(mode):
    t = logtext(mode, "new")
    cand = candidates(t)
    sc = scores(mode)
    logs_gate = sc.get("POST:/logs", (0, True, "-", "-"))[1]
    true_in = "PUT:/users/{username}/role" in cand
    check("%s-logs-gated-out" % mode, "POST:/logs" not in cand and logs_gate is False and true_in,
          "candidates %s; python gate for /logs %s (low-score op excluded, true transition kept)" % (list(cand.keys()), logs_gate))


def put_id_source(mode):
    t = logtext(mode, "new")
    cand = candidates(t)
    sc = scores(mode)
    src_gate = sc.get("PUT:/docs/{id}", (0, True, "-", "-"))[1]
    check("%s-source-not-excluded" % mode, src_gate is False,
          "python gate for source PUT:/docs/{id} %s (score>0 gate keeps resource-write source)" % src_gate)
    check("%s-fires" % mode, fired(mode),
          "970 constructed = %s (PUT /{noun}/{id} source must not be excluded as a transition)" % fired(mode))


define("put-id-source", put_id_source)
define("enum-role", enum_role)
define("bool-restricted", bool_restricted)
define("num-two", num_two)
define("path-id-username", path_id_username)
define("access-level", access_level)
define("anon-deny", anon_deny)
define("gate-low", gate_low)

for mode in MODES:
    parity(mode)
    MODE_CHECKS.get(mode, lambda m: None)(mode)

old = logtext("enum-role", "old")
check("p1-has-no-nb-debug", old != "" and "roleField" not in old,
      "P1 jar emits no NB candidate debug (mechanism is new); log present %s" % (old != ""))

print("summary %d/%d checks passed" % (sum(RESULTS), len(RESULTS)))
sys.exit(1 if not all(RESULTS) else 0)
