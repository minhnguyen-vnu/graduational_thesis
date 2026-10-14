import json, os, subprocess, sys, urllib.parse
R1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "field-labelling-20261004")
sys.path.insert(0, R1)
import extract_fields as ef
from extract_fields import CORPUS, new_rows

HERE = os.path.dirname(os.path.abspath(__file__))
CHUNK = 60
ef.SEED = 20261006


def fetch(a):
    dest = os.path.join(CORPUS, "specs", "%s.json" % a["spec_id"])
    if not os.path.exists(dest):
        subprocess.run(["curl", "-sSfL", "--max-time", "60", "-o", dest,
                        urllib.parse.quote(a["swaggerUrl"], safe=":/")])


def render(r):
    lines = ["## %s  %s %s" % (r["row_id"], r["method"], r["path"])]
    if r["summary"]:
        lines.append("summary: " + r["summary"])
    if r["description"]:
        lines.append("desc: " + r["description"])
    for f in r["fields"]:
        e = " enum[%s]" % "|".join(f["enum"]) if f["enum"] else ""
        lines.append("- %s:%s %s%s" % (f["loc"], f["name"], f["type"], e))
    if r["fields_cut"]:
        lines.append("- (%d truong bi cat)" % r["fields_cut"])
    return "\n".join(lines)


def main():
    sample = json.load(open(os.path.join(CORPUS, "sample-field-r2.json")))
    reserve = json.load(open(os.path.join(CORPUS, "sample-field-r2-reserve.json")))
    rows, bad = new_rows(sample)
    repl = []
    for i, (sid, why) in enumerate(bad):
        a = dict(reserve[i], spec_id="S%03d" % (600 + i), replaces=sid)
        fetch(a)
        r2, b2 = new_rows([a])
        repl.append(dict(a, ok=not b2, reason_replaced=why, reason_dropped=(b2[0][1] if b2 else "")))
        rows += r2
    json.dump(repl, open(os.path.join(CORPUS, "sample-field-r2-replacements.json"), "w"), indent=1)
    with open(os.path.join(HERE, "rows.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    d = os.path.join(HERE, "rows")
    os.makedirs(d, exist_ok=True)
    chunks, cur = [], []
    for s in sorted({r["spec_id"] for r in rows}):
        cur += [r for r in rows if r["spec_id"] == s]
        if len(cur) >= CHUNK:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    for i, c in enumerate(chunks, 1):
        open(os.path.join(d, "chunk-%03d.txt" % i), "w").write("\n\n".join(render(r) for r in c) + "\n")
    print("hong %d: %s" % (len(bad), [b[0] for b in bad]))
    print("thay ok %d, bo %d" % (sum(1 for a in repl if a["ok"]), sum(1 for a in repl if not a["ok"])))
    print("spec %d, dong %d, truong %d, khoi %d, cat %d" % (len({r["spec_id"] for r in rows}), len(rows),
          sum(len(r["fields"]) for r in rows), len(chunks), sum(1 for r in rows if r["fields_cut"])))


main()
