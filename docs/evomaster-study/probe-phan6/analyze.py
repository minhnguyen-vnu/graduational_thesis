import collections
import json
import re
import sys

LINE = re.compile(r"^(\d{5}) t=\s*([\d.]+)s (\S+)\s+(\S+)\s+(\S+)\s+req=(.*?) -> (\d{3}) ?(.*)$")
MARK = re.compile(r"^=== MARK (\w+) t=([\d.]+)s")

SEED = {"alice": "ADMIN", "superadmin": "ADMIN", "bob": "VIEWER"}
stored = dict(SEED)
phase = "INIT"
calls = []
for raw in open(sys.argv[1]):
    raw = raw.rstrip("\n")
    m = MARK.match(raw)
    if m:
        phase = m.group(1)
        calls.append({"mark": phase, "t": float(m.group(2))})
        continue
    m = LINE.match(raw)
    if not m:
        continue
    seq, t, verb, path, who, req, st, resp = m.groups()
    st = int(st)
    login = who.startswith("LOGIN->")
    w = who[7:] if login else who
    mw = re.match(r"(\w+)\[(\w+)\]\.\.(\S+)", w)
    user, claim, tail = (mw.group(1), mw.group(2), mw.group(3)) if mw else (None, None, None)
    before = dict(stored)
    stale = (not login) and user is not None and claim != stored.get(user)
    if verb == "POST" and path == "/reset" and st == 200:
        stored = dict(SEED)
    if verb == "PUT" and path.startswith("/users/") and path.endswith("/role") and st == 200:
        try:
            body = json.loads(resp)
            stored[body["username"]] = body["role"]
        except Exception:
            pass
    calls.append({"seq": seq, "t": float(t), "phase": phase, "verb": verb, "path": path, "login": login,
                  "user": user, "claim": claim, "tail": tail, "status": st, "req": req, "resp": resp,
                  "stale": stale, "stored_before": before, "stored_after": dict(stored)})

real = [c for c in calls if "seq" in c and not c["path"].startswith("/v3/")]
print("requests", len(real), "logins", sum(c["login"] for c in real))
for c in calls:
    if "mark" in c:
        print("MARK", c["mark"], "t=%.1f" % c["t"])
by_phase = collections.OrderedDict()
for c in real:
    p = by_phase.setdefault(c["phase"], collections.Counter())
    p["requests"] += 1
    p["logins"] += c["login"]
    p["anon"] += (not c["login"]) and c["user"] is None
    p["stale"] += c["stale"]
    p["stale_2xx"] += c["stale"] and 200 <= c["status"] < 300
    p["reset_200"] += c["verb"] == "POST" and c["path"] == "/reset" and c["status"] == 200
    if c["verb"] == "PUT" and c["path"].endswith("/role") and c["status"] == 200:
        p["role_200"] += 1
        if '"VIEWER"' in c["req"]:
            p["demote_200"] += 1
for k, v in by_phase.items():
    print("phase %-20s %s" % (k, dict(v)))

print("\nresets with 200:", " ".join(c["seq"] + ":" + c["phase"][:3] for c in real if c["verb"] == "POST" and c["path"] == "/reset" and c["status"] == 200))
print("\nrole changes with 200 (seq phase operator[claim] path body -> stored after)")
for c in real:
    if c["verb"] == "PUT" and c["path"].endswith("/role") and c["status"] == 200:
        print("  %s %-12s %s[%s] %s %s -> %s" % (c["seq"], c["phase"], c["user"], c["claim"], c["path"], c["req"],
                                                   ",".join("%s=%s" % kv for kv in sorted(c["stored_after"].items()))))

print("\nstale-token calls (claim differs from stored role at send time)")
for c in real:
    if c["stale"]:
        print("  %s %-12s %-6s %-22s %s token[%s] stored[%s] -> %d %s" % (
            c["seq"], c["phase"], c["verb"], c["path"], c["user"], c["claim"], c["stored_before"][c["user"]],
            c["status"], c["resp"][:60]))

print("\nlast stored roles", stored)

a1 = [c for c in real if c["stale"] and c["claim"] == "ADMIN" and c["stored_before"][c["user"]] == "VIEWER"]
print("\nA1-direction stale calls (token ADMIN, stored VIEWER):", len(a1), "with 2xx:", sum(200 <= c["status"] < 300 for c in a1))
for c in a1:
    print("  %s %-12s %-6s %-22s %s ..%s -> %d" % (c["seq"], c["phase"], c["verb"], c["path"], c["user"], c["tail"], c["status"]))
