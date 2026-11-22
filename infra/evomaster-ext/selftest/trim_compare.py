import os
import re
import sys

REF_DIR, REF_SUF, NEW_DIR, NEW_SUF, LABEL = sys.argv[1:6]
MODES = sys.argv[6:]

KEEP = re.compile(r"RestSecurityBuilder|[Ss]tateful-authorization|Privilege-restore")
STAMP = re.compile(r"^\d\d:\d\d:\d\d\.\d+ \[[^\]]*\] ")
CANDIDATE = re.compile(r"transition candidate (\S+) score \S+ roleField \S+ victimField null reducedRoleValues \[(.+)\]")
OF_N = re.compile(r"\(candidate \d+ of \d+\)")


def builder_lines(path):
    out = []
    for line in open(path, errors="replace"):
        if KEEP.search(line):
            out.append(STAMP.sub("", line.rstrip("\n")))
    return out


def first_difference(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return min(len(a), len(b))


failed = False
for mode in MODES:
    ref_path = os.path.join(REF_DIR, mode + REF_SUF)
    new_path = os.path.join(NEW_DIR, mode + NEW_SUF)
    name = "%s-%s" % (LABEL, mode)
    if not os.path.exists(ref_path) or not os.path.exists(new_path):
        print("FAIL  %-34s missing log: ref %s new %s" % (name, os.path.exists(ref_path), os.path.exists(new_path)))
        failed = True
        continue
    ref = builder_lines(ref_path)
    new = builder_lines(new_path)
    if not ref:
        print("FAIL  %-34s reference log has no builder lines" % name)
        failed = True
        continue
    dropped = sorted({m.group(1) for line in ref for m in [CANDIDATE.search(line)] if m})
    if not dropped:
        if ref == new:
            print("PASS  %-34s %d builder lines identical" % (name, len(ref)))
            continue
        i = first_difference(ref, new)
        print("FAIL  %-34s ref %d lines, new %d lines, first difference at line %d" % (name, len(ref), len(new), i + 1))
        print("        ref: %s" % (ref[i] if i < len(ref) else "<end>"))
        print("        new: %s" % (new[i] if i < len(new) else "<end>"))
        failed = True
        continue
    chosen_new = [d for d in dropped if any("transition chosen: " + d + " " in line for line in new)]
    chosen_ref = [d for d in dropped if any("transition chosen: " + d + " " in line for line in ref)]
    if chosen_new or not chosen_ref:
        print("FAIL  %-34s candidates with victimField null %s: chosen by ref %s, by new %s" % (
            name, dropped, chosen_ref, chosen_new))
        failed = True
        continue

    def strip(lines):
        out = []
        skipping = False
        for line in lines:
            if "transition chosen: " in line:
                skipping = any("transition chosen: " + d + " " in line for d in dropped)
            if skipping:
                if any(e in line for e in ("exhausted its sources", "not proven after")):
                    skipping = False
                continue
            out.append(OF_N.sub("(candidate)", line))
        return out

    r = strip(ref)
    n = strip(new)
    if r == n:
        print("PASS  %-34s ref chose %s, new did not; other %d builder lines identical" % (name, chosen_ref, len(r)))
        continue
    i = first_difference(r, n)
    print("FAIL  %-34s dropped %s; after removing its lines ref %d, new %d, first difference at line %d" % (
        name, dropped, len(r), len(n), i + 1))
    print("        ref: %s" % (r[i] if i < len(r) else "<end>"))
    print("        new: %s" % (n[i] if i < len(n) else "<end>"))
    failed = True
sys.exit(1 if failed else 0)
