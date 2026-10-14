import json
import os
import re
import sys

OUT = sys.argv[1]
T = "PUT:/users/{username}/role"
D = "PUT:/permissions/{username}"
B = "PATCH:/users/{username}"

RESULTS = []

ATTEMPT = re.compile(
    r"^\* (?:Discarded a (?P<void>VOID)|Discarded an (?P<unc>UNCONFIRMED)|Assembled a) stateful-authorization \(MR-A1\)"
    r" (?:attempt|triple) on (?P<src>\S+?):? .*?\(victim '(?P<victim>[^']+)', operator '(?P<op>[^']+)',"
    r"(?: transition (?P<trans>\S+),)? (?:codes|statuses) (?P<codes>[0-9/-]+)\)(?P<tail>.*)$")
CHOSEN = re.compile(r"transition chosen: (\S+)")


def parse(mode, tag):
    path = os.path.join(OUT, "%s-%s.log" % (mode, tag))
    if not os.path.exists(path):
        return None
    text = open(path, errors="replace").read()
    cand = None
    attempts = []
    for line in text.splitlines():
        m = CHOSEN.search(line)
        if m:
            cand = m.group(1)
            continue
        m = ATTEMPT.match(line)
        if m:
            kind = "VOID" if m.group("void") else "UNCONFIRMED" if m.group("unc") else "ASSEMBLED"
            attempts.append(dict(cand=cand, kind=kind, src=m.group("src"), victim=m.group("victim"), op=m.group("op"),
                                 codes=m.group("codes"), trans=m.group("trans"), tail=m.group("tail")))
    rep = os.path.join(OUT, "%s-%s" % (mode, tag), "report.json")
    try:
        cats = [x["code"] for f in json.load(open(rep))["faults"]["foundFaults"] for x in f["faultCategories"]]
        det = 970 in cats
    except Exception:
        det = None
    exitfile = os.path.join(OUT, "%s-%s.exit" % (mode, tag))
    exitcode = open(exitfile).read().strip() if os.path.exists(exitfile) else "missing"

    return dict(text=text, attempts=attempts, det=det, exit=exitcode)


def check(name, ok, detail):
    RESULTS.append(ok)
    print("%s  %-28s %s" % ("PASS" if ok else "FAIL", name, detail))


def survives(mode, r):
    ok = r is not None and r["exit"] == "0" and "at org.evomaster" not in r["text"]
    check(mode + "-survives", ok, "new jar exit %s, stack trace %s" % (
        r and r["exit"], r is not None and "at org.evomaster" in r["text"]))
    return ok


def under(r, cand):
    return [a for a in r["attempts"] if a["cand"] == cand]


def fired_on(r, trans):
    return [a for a in r["attempts"] if a["kind"] == "ASSEMBLED" and a["trans"] == trans and a["codes"].endswith("/200")]


def noop_decoy(new, old):
    if not survives("noop-decoy", new):
        return
    d, t = under(new, D), under(new, T)
    fired = fired_on(new, T)
    check("noop-decoy-next-candidate", new["det"] is True and bool(fired) and bool(d),
          "candidate loop :561 keeps going after the first candidate: 970 %s, attempts under decoy %d, under true %d, %s"
          % (new["det"], len(d), len(t), fired[:1]))
    reused = fired and fired[0]["victim"] in {a["victim"] for a in d if a["codes"].split("/")[1].startswith("2")}
    check("noop-decoy-mark-cleared", bool(reused),
          "retainAll at :573 frees a victim the decoy marked: victim of the 970 %s, decoy 2xx victims %s"
          % (fired[0]["victim"] if fired else None, sorted({a["victim"] for a in d})))
    check("noop-decoy-old-misses", old is not None and old["det"] is False,
          "fixture discriminates: old jar 970 %s, attempts %s" % (old and old["det"], old and len(old["attempts"])))


def reject_decoy(new, old):
    if not survives("reject-decoy", new):
        return
    d = under(new, D)
    line = "transition %s not proven after 5 attempts; trying the next candidate" % D
    check("reject-decoy-cap5", line in new["text"] and len(d) == 5,
          "candidateCapReached :494 and attemptAllowed :497 stop the decoy: attempts under decoy %d, line %s"
          % (len(d), line in new["text"]))
    check("reject-decoy-true-fires", new["det"] is True and bool(fired_on(new, T)),
          "after the cap the true transition runs: 970 %s" % new["det"])
    check("reject-decoy-old-misses", old is not None and old["det"] is False and len(under(old, D)) >= 8,
          "fixture discriminates: old jar 970 %s, attempts under decoy %d" % (old and old["det"], old and len(under(old, D))))


def restore_budget(new, old):
    if not survives("restore-budget", new):
        return
    restores = re.findall(r"^\* Privilege-restore (accepted|refused) for '(\w+)' by '\w+' with role '\w+' on (\S+)", new["text"], re.M)
    on_d = [x for x in restores if x[2] == D]
    acc_t = [x for x in restores if x[2] == T and x[0] == "accepted"]
    spent = ("restore budget of 3 spent on %s" % D) in new["text"]
    check("restore-budget-per-candidate", spent and len(on_d) == 3 and bool(acc_t) and len(restores) >= 4,
          "privilegeRestoreAttempts reset at :572: restores on decoy %d, accepted on true %d, total %d, budget line %s"
          % (len(on_d), len(acc_t), len(restores), spent))
    s2 = ("%s refused or rejected every attempt on victim 'alice'" % D) in new["text"]
    check("restore-budget-refused-pair", s2,
          "refusedTransitionVictims write at :780 after the restore pass: line %s" % s2)
    check("restore-budget-true-fires", new["det"] is True and bool(fired_on(new, T)), "970 %s" % new["det"])
    check("restore-budget-old-misses", old is not None and old["det"] is False,
          "fixture discriminates: old jar 970 %s" % (old and old["det"]))


def protected_victim(new, old):
    if not survives("protected-victim", new):
        return
    s2 = ("%s refused or rejected every attempt on victim 'boss'" % T) in new["text"]
    nsrc = {a["src"] for a in new["attempts"] if a["victim"] == "boss"}
    osrc = {a["src"] for a in old["attempts"] if a["victim"] == "boss"} if old else set()
    check("protected-victim-skip", s2 and len(nsrc) == 1 and len(osrc) >= 2,
          "skip at :670 after the write at :780: sources tried on boss new %d %s, old %d, line %s"
          % (len(nsrc), sorted(nsrc), len(osrc), s2))
    check("protected-victim-alice-fires", new["det"] is True and any(a["victim"] == "alice" for a in fired_on(new, T)),
          "the refused pair does not block the other victim: 970 %s" % new["det"])


def revoke(new, old):
    if not survives("revoke", new):
        return
    nrev = [a for a in new["attempts"] if a["codes"] == "200/200/401" and "REVOKED:" in a["tail"]]
    orev = [a for a in old["attempts"] if a["codes"] == "200/200/401"] if old else []
    check("revoke-label", bool(nrev) and bool(orev) and not any("REVOKED" in a["tail"] for a in orev),
          "VOID line at :914 carries REVOKED on 200/200/401: new %d, old 200/200/401 lines %d without label"
          % (len(nrev), len(orev)))
    check("revoke-no-970", new["det"] is False, "a revoked token is not a finding: 970 %s" % new["det"])


def proven_404(new, old):
    if not survives("proven-404", new):
        return
    line = "proven transition %s returned 404 for victim 'carol'" % T
    adv = "returned 404 after a 2xx source; trying the next candidate"
    check("proven-404-keeps-candidate", line in new["text"] and adv not in new["text"] and old is not None and adv in old["text"],
          "branch at :886 writes the pair instead of advancing: new line %s, new advance %s, old advance %s"
          % (line in new["text"], adv in new["text"], old is not None and adv in old["text"]))
    check("proven-404-fires", new["det"] is True, "970 %s" % new["det"])


def alpha(new, old):
    if not survives("alpha", new):
        return
    cand = "transition candidate %s score" % T
    check("alpha-no-cut", cand in new["text"] and new["det"] is True and old is not None and cand not in old["text"] and old["det"] is False,
          "ranked list at :532 is no longer cut at 8: new evaluates true %s, 970 %s; old evaluates %s, 970 %s"
          % (cand in new["text"], new["det"], old is not None and cand in old["text"], old and old["det"]))


def cap20(new, old):
    if not survives("cap20", new):
        return
    na, oa = len(new["attempts"]), len(old["attempts"]) if old else -1
    check("cap20-total", na == 20 and oa == 8,
          "MAX_STATEFUL_TRIPLE_ATTEMPTS = 20 at :124: attempts new %d, old %d" % (na, oa))
    srcs = {a["src"] for a in new["attempts"]}
    kinds = {a["kind"] for a in new["attempts"]}
    check("cap20-same-candidate", len(srcs) > 1 and {a["cand"] for a in new["attempts"]} == {T} and "UNCONFIRMED" in kinds,
          "UNCONFIRMED keeps the candidate and moves to the next source: sources %d, kinds %s" % (len(srcs), sorted(kinds)))


def bool_flag(new, old):
    if not survives("bool-flag", new):
        return
    line = "restore unavailable on %s" % B
    check("bool-flag-restore-unavailable", line in new["text"] and old is not None and line not in old["text"],
          "log at :736 when no elevated value exists: new %s, old %s" % (line in new["text"], old is not None and line in old["text"]))


CHECKS = [("noop-decoy", noop_decoy), ("reject-decoy", reject_decoy), ("restore-budget", restore_budget),
          ("protected-victim", protected_victim), ("revoke", revoke), ("proven-404", proven_404),
          ("alpha", alpha), ("cap20", cap20), ("bool-flag", bool_flag)]

WANTED = sys.argv[2:] or [m for m, _ in CHECKS]
for mode, fn in CHECKS:
    if mode in WANTED:
        fn(parse(mode, "new"), parse(mode, "old"))

sys.exit(0 if RESULTS and all(RESULTS) else 1)
