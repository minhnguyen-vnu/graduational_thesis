import json
import sys
import urllib.request

lexicon_csv, spec_url, mode = sys.argv[1], sys.argv[2], sys.argv[3]

words = []
for line in open(lexicon_csv):
    parts = line.strip().split(",")
    if len(parts) == 3 and parts[0] == "path":
        try:
            words.append((parts[1].lower(), float(parts[2])))
        except ValueError:
            pass

ADMIN = ["is_admin", "isadmin", "is_superuser", "is_superadmin", "is_staff"]
VERBS = ["PUT", "PATCH", "POST", "DELETE"]

spec = json.load(urllib.request.urlopen(spec_url))
rows = []
for path, ops in spec["paths"].items():
    for verb, op in ops.items():
        fields = []
        body = op.get("requestBody")
        if body:
            fields = list(body["content"]["application/json"]["schema"].get("properties", {}).keys())
        hay = (path + " " + verb.upper() + ":" + path + " " + " ".join(fields)).lower()
        score = max([s for w, s in words if w in hay] or [0.0])
        if any(a in hay for a in ADMIN):
            score = max(score, 0.6)
        rows.append((verb.upper(), path, round(score, 4)))

ranked = sorted([r for r in rows if r[0] in VERBS and r[2] > 0], key=lambda r: (-r[2], VERBS.index(r[0])))
sources = [r for r in rows if r[0] == "PUT" and r[1].endswith("/{id}")]
true_op = [r for r in ranked if r[1] in ("/users/{username}/role", "/users/{username}")]

problems = []
if [s for s in sources if s[2] > 0]:
    problems.append("a source scores above 0: %s" % [s for s in sources if s[2] > 0])
if not true_op:
    problems.append("the true transition has no score")
else:
    rank = ranked.index(true_op[0]) + 1
    if mode in ("noop-decoy", "reject-decoy", "restore-budget"):
        decoy = [r for r in ranked if r[1] == "/permissions/{username}"]
        if not decoy or ranked.index(decoy[0]) + 1 >= rank:
            problems.append("the decoy does not rank above the true transition")
    if mode == "alpha" and rank <= 8:
        problems.append("the true transition ranks %d, inside the first 8" % rank)

print("ranked %s" % ["%s %s %.4f" % r for r in ranked])
print("problems %s" % (problems or "none"))
sys.exit(1 if problems else 0)
