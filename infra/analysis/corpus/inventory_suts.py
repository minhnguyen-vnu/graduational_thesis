import json, os, glob, sys

import subprocess


def load_yaml(path):
    r = subprocess.run(["ruby", "-ryaml", "-rjson", "-e",
                        "print JSON.dump(YAML.safe_load(File.read(ARGV[0]), aliases: true))", path],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise ValueError(r.stderr.strip()[:80])
    return json.loads(r.stdout)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "wfd", "openapi-swagger")
WRITE = ("post", "put", "patch", "delete")

rows, bad = [], []
for p in sorted(glob.glob(os.path.join(SRC, "*"))):
    name = os.path.basename(p)
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            d = json.load(f) if name.endswith(".json") else load_yaml(p)
    except Exception as e:
        bad.append((name, type(e).__name__ + ": " + str(e)[:60]))
        continue
    if not isinstance(d, dict):
        bad.append((name, "not a mapping"))
        continue
    ver = d.get("openapi") or d.get("swagger") or "?"
    paths = d.get("paths") or {}
    nw = sum(1 for it in paths.values() if isinstance(it, dict)
             for m in it if m.lower() in WRITE)
    rows.append((name, str(ver), len(paths), nw, os.path.getsize(p)))

rows.sort(key=lambda r: -r[3])
out = os.path.join(HERE, "wfd-suts.md")
with open(out, "w") as f:
    f.write("# WFD — 36 spec, một spec một SUT\n\n")
    f.write("Nguồn: `infra/analysis/corpus/wfd/openapi-swagger/`, thư mục WFD tự gom một file một SUT.\n")
    f.write("Thay cho `wfd-inventory.md`, vốn quét cả cây nguồn nên lẫn 63 fixture test của microcks.\nFile YAML đọc bằng `ruby -ryaml` vì máy không có PyYAML.\n\n")
    f.write("Cột `ghi` đếm số operation POST, PUT, PATCH, DELETE. `CLAUDE.md` §6 chỉ gán nhãn operation ghi.\n\n")
    f.write("| # | Spec | Phiên bản | Đường dẫn | Ghi | Bytes |\n|---|---|---|---|---|---|\n")
    for i, r in enumerate(rows, 1):
        f.write("| %d | `%s` | %s | %d | %d | %d |\n" % (i, r[0], r[1], r[2], r[3], r[4]))
    if bad:
        f.write("\n## Không đọc được\n\n")
        for n, e in bad:
            f.write("- `%s` — %s\n" % (n, e))
    tot_p = sum(r[2] for r in rows)
    tot_w = sum(r[3] for r in rows)
    f.write("\n## Tổng\n\n")
    f.write("%d spec đọc được, %d không đọc được. %d đường dẫn, %d operation ghi.\n"
            % (len(rows), len(bad), tot_p, tot_w))
    z = [r[0] for r in rows if r[3] == 0]
    f.write("\nSpec không có operation ghi nào (%d): %s\n"
            % (len(z), ", ".join("`%s`" % x for x in z) if z else "không có"))
print("ok %d rows, %d bad, writes=%d" % (len(rows), len(bad), sum(r[3] for r in rows)))
