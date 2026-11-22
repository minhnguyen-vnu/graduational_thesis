import json
import os
import re
import sys

OUT = sys.argv[1]
MODES = sys.argv[2:]
FAILED = [False]

INCONCLUSIVE_PRIOR = "re-login probe INCONCLUSIVE: a call before the source of the replayed slice changed status group"
KEEP = re.compile(r"RestSecurityBuilder|[Ss]tateful-authorization|Privilege-restore")
STAMP = re.compile(r"^\d\d:\d\d:\d\d\.\d+ \[[^\]]*\] ")


def same_decisions(mode):
    a = [STAMP.sub("", x) for x in log(mode, "cs").splitlines() if KEEP.search(x)]
    b = [STAMP.sub("", x) for x in log(mode, "lf").splitlines() if KEEP.search(x)]
    if a == b:
        return True, "%d builder lines, identical" % len(a)
    first = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    return False, "cs %d lf %d lines, first difference at line %d" % (len(a), len(b), first + 1)


def check(name, ok, detail):
    print("%s  %-34s %s" % ("PASS" if ok else "FAIL", name, detail))
    if not ok:
        FAILED[0] = True


def log(mode, tag):
    path = os.path.join(OUT, "%s-%s.log" % (mode, tag))
    return open(path).read() if os.path.exists(path) else ""


def exit_code(mode, tag):
    path = os.path.join(OUT, "%s-%s.exit" % (mode, tag))
    return open(path).read().strip() if os.path.exists(path) else "missing"


def requests(mode, tag):
    path = os.path.join(OUT, "%s-%s-req.jsonl" % (mode, tag))
    if not os.path.exists(path):
        return []
    return [json.loads(x) for x in open(path) if x.strip()]


def probe_windows(reqs, source_prefix, stop_at_other_caller):
    out = []
    for i in range(len(reqs) - 1):
        t, f = reqs[i], reqs[i + 1]
        if not (t["path"].startswith("/users/") and t.get("armed") and t["code"] == 200):
            continue
        victim = t["path"].split("/")[2]
        if not (f["caller"] == victim and f["path"].startswith(source_prefix) and 200 <= f["code"] < 300):
            continue
        end = len(reqs)
        for k in range(i + 2, len(reqs)):
            r = reqs[k]
            if r["path"].startswith("/users/") and r.get("armed"):
                end = k
                break
            if stop_at_other_caller and r["caller"] not in (victim, None):
                end = k
                break
        out.append((victim, [r for r in reqs[i + 2:end] if r["caller"] == victim]))
    return out


def count(text, needle):
    return text.count(needle)


def constructed(text, source):
    return count(text, "revealing privilege persistence after a role downgrade on " + source + " ")


def unconfirmed(text, source):
    return count(text, "Discarded an UNCONFIRMED stateful-authorization (MR-A1) attempt on " + source + ":")


def anonymous(text, source):
    return re.findall(r"anonymous control: " + re.escape(source) + r"=(\S+)", text)


for mode in MODES:
    cs, lf = exit_code(mode, "cs"), exit_code(mode, "lf")
    check(mode + "-ran", cs == "0" and lf == "0",
          "exit cs %s lf %s, requests cs %d lf %d" % (cs, lf, len(requests(mode, "cs")), len(requests(mode, "lf"))))

if "len1" in MODES:
    cs, lf = log("len1", "cs"), log("len1", "lf")
    s = "PUT:/docs/{id}"
    check("len1-constructed", constructed(cs, s) > 0 and constructed(lf, s) > 0,
          "Constructed on %s: cs %d lf %d" % (s, constructed(cs, s), constructed(lf, s)))
    check("len1-anonymous-401", anonymous(cs, s)[:1] == ["401"] and anonymous(lf, s)[:1] == ["401"],
          "anonymous control codes cs %s lf %s" % (anonymous(cs, s), anonymous(lf, s)))
    check("len1-no-prior-inconclusive", count(cs, INCONCLUSIVE_PRIOR) == 0,
          "cs lines '%s': %d" % (INCONCLUSIVE_PRIOR[:40], count(cs, INCONCLUSIVE_PRIOR)))

if "chain" in MODES:
    cs, lf = log("chain", "cs"), log("chain", "lf")
    s = "PUT:/docs/{id}"
    check("chain-lf-constructed", constructed(lf, s) > 0,
          "ref jar Constructed on %s: %d (403 read from POST /docs)" % (s, constructed(lf, s)))
    check("chain-cs-not-constructed", constructed(cs, s) == 0,
          "new jar Constructed on %s: %d" % (s, constructed(cs, s)))
    check("chain-cs-inconclusive-prior", count(cs, INCONCLUSIVE_PRIOR) > 0 and unconfirmed(cs, s) > 0,
          "new jar: prior-call INCONCLUSIVE %d, UNCONFIRMED on %s %d" % (
              count(cs, INCONCLUSIVE_PRIOR), s, unconfirmed(cs, s)))
    windows = probe_windows(requests("chain", "cs"), "/docs/", True)
    stopped = [v for v, w in windows if w and w[0]["m"] == "POST" and w[0]["path"] == "/docs" and w[0]["code"] == 403
               and not any(r["m"] == "PUT" and r["path"].startswith("/docs/") for r in w)]
    check("chain-cs-probe-stops-at-post", len(windows) > 0 and len(stopped) == len(windows),
          "after each triple on /docs the re-login sends POST /docs 403 and no PUT /docs: %d of %d (victims %s)" % (
              len(stopped), len(windows), [v for v, _ in windows]))

if "prior-noncreate" in MODES:
    cs, lf = log("prior-noncreate", "cs"), log("prior-noncreate", "lf")
    s = "PUT:/files/{id}"
    check("prior-noncreate-lf-constructed", constructed(lf, s) > 0,
          "ref jar Constructed on %s: %d (403 from missing check-out)" % (s, constructed(lf, s)))
    check("prior-noncreate-cs-not-constructed", constructed(cs, s) == 0,
          "new jar Constructed on %s: %d" % (s, constructed(cs, s)))
    check("prior-noncreate-cs-inconclusive", count(cs, INCONCLUSIVE_PRIOR) > 0 and unconfirmed(cs, s) > 0,
          "new jar: prior-call INCONCLUSIVE %d, UNCONFIRMED on %s %d" % (
              count(cs, INCONCLUSIVE_PRIOR), s, unconfirmed(cs, s)))
    for tag in ("lf", "cs"):
        hole = 0
        for victim, w in probe_windows(requests("prior-noncreate", tag), "/files/", False):
            k = next((i for i, r in enumerate(w) if r["path"] == "/checkout" and r["code"] == 403), None)
            if k is not None and any(r["path"].startswith("/files/") and r["code"] == 403 for r in w[k + 1:]):
                hole += 1
        check("prior-noncreate-%s-hole-b-present" % tag, hole > 0,
              "re-login: POST /checkout 403, then the source PUT /files still sent and 403: %d triples" % hole)

if "anon-prefix" in MODES:
    cs, lf = log("anon-prefix", "cs"), log("anon-prefix", "lf")
    s = "PUT:/drafts/{id}"
    check("anon-prefix-cs-source-anonymous", anonymous(cs, s)[:1] == ["401"] and constructed(cs, s) > 0,
          "new jar anonymous control %s, Constructed %d" % (anonymous(cs, s), constructed(cs, s)))
    check("anon-prefix-lf-all-anonymous", anonymous(lf, s)[:1] == ["400"],
          "ref jar anonymous control %s (400 = anonymous POST /drafts)" % anonymous(lf, s))
    reqs = requests("anon-prefix", "cs")
    pairs = 0
    for a, b in zip(reqs, reqs[1:]):
        if (a["m"] == "POST" and a["path"] == "/drafts" and a["caller"] is not None and a["code"] == 201
                and b["m"] == "PUT" and b["path"].startswith("/drafts/") and b["caller"] is None and b["code"] == 401):
            pairs += 1
    check("anon-prefix-cs-prefix-with-token", pairs > 0,
          "new jar: POST /drafts with a token then PUT /drafts anonymous: %d pairs" % pairs)

if "source-200" in MODES:
    cs, lf = log("source-200", "cs"), log("source-200", "lf")
    s = "PUT:/docs/{id}"
    check("source-200-unconfirmed", unconfirmed(cs, s) > 0 and unconfirmed(lf, s) > 0,
          "UNCONFIRMED on %s: cs %d lf %d" % (s, unconfirmed(cs, s), unconfirmed(lf, s)))
    victims_docs = set(re.findall(r"UNCONFIRMED stateful-authorization \(MR-A1\) attempt on PUT:/docs/\{id\}:.*?victim '([^']+)'", cs))
    victims_notes = set(re.findall(r"UNCONFIRMED stateful-authorization \(MR-A1\) attempt on PUT:/notes/\{id\}:.*?victim '([^']+)'", cs))
    locked = count(cs, "already reduced in this phase")
    check("source-200-victim-unlocked", locked == 0 and len(victims_docs & victims_notes) > 0,
          "new jar: 'already reduced' lines %d; victims UNCONFIRMED on both sources %s" % (
              locked, sorted(victims_docs & victims_notes)))
    check("source-200-false-not-null", count(cs, "re-login probe INCONCLUSIVE") == 0 and constructed(cs, s) == 0,
          "new jar INCONCLUSIVE lines %d, Constructed %d" % (count(cs, "re-login probe INCONCLUSIVE"),
                                                             constructed(cs, s)))

if "op-refused" in MODES:
    cs, lf = log("op-refused", "cs"), log("op-refused", "lf")
    refused = r"codes 200/403/"
    check("op-refused-403-branch", len(re.findall(refused, cs)) > 0 and len(re.findall(refused, lf)) > 0,
          "VOID attempts with transition 403: cs %d lf %d" % (len(re.findall(refused, cs)), len(re.findall(refused, lf))))
    check("op-refused-next-operator", constructed(cs, "PUT:/docs/{id}") > 0 and constructed(lf, "PUT:/docs/{id}") > 0,
          "Constructed after switching operator: cs %d lf %d" % (
              constructed(cs, "PUT:/docs/{id}"), constructed(lf, "PUT:/docs/{id}")))
    ok, detail = same_decisions("op-refused")
    check("op-refused-same-decisions", ok, detail)

if "value-reject" in MODES:
    cs, lf = log("value-reject", "cs"), log("value-reject", "lf")
    rejected = "codes 200/400/"
    check("value-reject-400-branch", count(cs, rejected) > 0 and count(lf, rejected) > 0,
          "VOID attempts with transition 400: cs %d lf %d" % (count(cs, rejected), count(lf, rejected)))
    check("value-reject-next-value", constructed(cs, "PUT:/docs/{id}") > 0 and constructed(lf, "PUT:/docs/{id}") > 0,
          "Constructed after the rejected value: cs %d lf %d" % (
              constructed(cs, "PUT:/docs/{id}"), constructed(lf, "PUT:/docs/{id}")))
    ok, detail = same_decisions("value-reject")
    check("value-reject-same-decisions", ok, detail)

if "prior-harmless" in MODES:
    cs, lf = log("prior-harmless", "cs"), log("prior-harmless", "lf")
    s = "PUT:/docs/{id}"
    windows = probe_windows(requests("prior-harmless", "cs"), "/docs/", False)
    shaped = []
    for v, w in windows:
        k = next((i for i, r in enumerate(w) if r["m"] == "PUT" and r["code"] == 403), None)
        if k is not None and any(r["m"] == "DELETE" and r["code"] == 404 for r in w[:k]):
            shaped.append(v)
    check("prior-harmless-probe-prefix", len(windows) > 0 and len(shaped) > 0,
          "re-login sends DELETE /docs 404 (404 in the triple too), then the source PUT /docs 403: %d of %d" % (
              len(shaped), len(windows)))
    check("prior-harmless-cs-constructed", constructed(cs, s) > 0 and count(cs, INCONCLUSIVE_PRIOR) == 0,
          "new jar Constructed on %s %d, prior-call INCONCLUSIVE %d" % (s, constructed(cs, s), count(cs, INCONCLUSIVE_PRIOR)))
    check("prior-harmless-cs-anonymous-401", anonymous(cs, s)[:1] == ["401"],
          "new jar anonymous control %s" % anonymous(cs, s))

sys.exit(1 if FAILED[0] else 0)
