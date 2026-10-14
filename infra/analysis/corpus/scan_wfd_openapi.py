import os
import re
import sys

ROOT = "/Users/minhnguyen/IdeaProjects/graduational-thesis"
WFD = os.path.join(ROOT, "infra/analysis/corpus/wfd")
EXTS = (".json", ".yaml", ".yml")

json_key = re.compile(r'"(openapi|swagger)"\s*:', re.IGNORECASE)
yaml_key = re.compile(r'^(openapi|swagger)\s*:', re.IGNORECASE | re.MULTILINE)

rows = []
scanned = 0
unreadable = []

for dirpath, dirnames, filenames in os.walk(WFD):
    if ".git" in dirnames:
        dirnames.remove(".git")
    for fn in filenames:
        if not fn.lower().endswith(EXTS):
            continue
        path = os.path.join(dirpath, fn)
        scanned += 1
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                head = f.read(65536)
        except OSError as e:
            unreadable.append((path, str(e)))
            continue
        hit = None
        if json_key.search(head):
            hit = "json-key"
        elif yaml_key.search(head):
            hit = "yaml-key"
        if hit:
            rows.append((os.path.relpath(path, ROOT), os.path.getsize(path), hit))

rows.sort()

out = os.path.join(ROOT, "infra/analysis/corpus/wfd-inventory.md")
with open(out, "w", encoding="utf-8") as f:
    f.write("# WFD Dataset - OpenAPI file inventory\n\n")
    f.write("Clone: `git clone --depth 1 https://github.com/WebFuzzing/Dataset "
            "infra/analysis/corpus/wfd` (xong, exit=0, 2026-09-16 22:27:26 +07).\n\n")
    f.write("## Tieu chi nhan dien\n\n")
    f.write("File co duoi `.json`, `.yaml`, `.yml` (khong phan biet hoa thuong), "
            "bo qua thu muc `.git`, va trong 65536 byte dau co khoa cap dau:\n\n")
    f.write("- `json-key`: khop regex `\"(openapi|swagger)\"\\s*:` (case-insensitive)\n")
    f.write("- `yaml-key`: khop regex `^(openapi|swagger)\\s*:` (multiline, case-insensitive)\n\n")
    f.write("Script: `infra/analysis/corpus/scan_wfd_openapi.py`. "
            "Lenh: `python3 infra/analysis/corpus/scan_wfd_openapi.py`\n\n")
    f.write("Duong dan tuong doi tu `%s`.\n\n" % ROOT)
    f.write("| # | Path | Bytes | Match |\n|---|---|---|---|\n")
    for i, (p, s, h) in enumerate(rows, 1):
        f.write("| %d | `%s` | %d | %s |\n" % (i, p, s, h))
    f.write("\n")
    f.write("| Metric | Value |\n|---|---|\n")
    f.write("| File .json/.yaml/.yml da quet | %d |\n" % scanned)
    f.write("| File khop tieu chi | %d |\n" % len(rows))
    f.write("| File khong doc duoc | %d |\n" % len(unreadable))
    if unreadable:
        f.write("\n## Khong doc duoc\n\n")
        for p, e in unreadable:
            f.write("- `%s`: %s\n" % (os.path.relpath(p, ROOT), e))

print("scanned", scanned)
print("matched", len(rows))
print("unreadable", len(unreadable))
print("out", out)
