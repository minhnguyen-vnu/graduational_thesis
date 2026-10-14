import json, os, subprocess, sys, urllib.parse
from extract_fields import CORPUS, old_rows, new_rows, spec_file

HERE = os.path.dirname(os.path.abspath(__file__))
CHUNK = 60


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
    sample = json.load(open(os.path.join(CORPUS, "sample-field.json")))
    reserve = json.load(open(os.path.join(CORPUS, "sample-field-reserve.json")))
    rows, bad = new_rows(sample)
    repl = []
    nxt = {"enriched": 0, "random": 0}
    for i, (sid, why) in enumerate(bad):
        orig = next(a for a in sample if a["spec_id"] == sid)
        pool = reserve[orig["pool"]]
        a = dict(pool[nxt[orig["pool"]]], split=orig["split"], spec_id="S%03d" % (400 + i), replaces=sid)
        nxt[orig["pool"]] += 1
        fetch(a)
        r2, b2 = new_rows([a])
        repl.append(dict(a, ok=not b2, reason_replaced=why, reason_dropped=(b2[0][1] if b2 else "")))
        rows += r2
    json.dump(repl, open(os.path.join(CORPUS, "sample-field-replacements.json"), "w"), indent=1)
    old, miss = old_rows()
    allr = old + rows
    with open(os.path.join(HERE, "rows.jsonl"), "w") as f:
        for r in allr:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    d = os.path.join(HERE, "rows")
    os.makedirs(d, exist_ok=True)
    specs = sorted({r["spec_id"] for r in allr})
    chunks, cur = [], []
    for s in specs:
        cur += [r for r in allr if r["spec_id"] == s]
        if len(cur) >= CHUNK:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    for i, c in enumerate(chunks, 1):
        open(os.path.join(d, "chunk-%03d.txt" % i), "w").write("\n\n".join(render(r) for r in c) + "\n")
    print("spec moi hong: %s" % bad)
    print("thay: %s" % [(a["replaces"], a["spec_id"], a["provider"], a["ok"], a["reason_dropped"]) for a in repl])
    print("dong cu khong tim thay op: %d %s" % (len(miss), miss[:10]))
    print("dong cu %d, dong moi %d, truong %d, khoi %d"
          % (len(old), len(rows), sum(len(r["fields"]) for r in allr), len(chunks)))
    print("op bi cat truong: %d" % sum(1 for r in allr if r["fields_cut"]))
    for sp in ("train", "test"):
        ss = {r["spec_id"] for r in rows if r["split"] == sp}
        print("moi %s: %d spec, %d dong" % (sp, len(ss), sum(1 for r in rows if r["split"] == sp)))


main()
