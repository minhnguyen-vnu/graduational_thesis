import glob
import os
import re
import sys

REF = sys.argv[1]
NEW = sys.argv[2]

KEEP = re.compile(r"RestSecurityBuilder|[Ss]tateful-authorization|Privilege-restore")
STAMP = re.compile(r"^\d\d:\d\d:\d\d\.\d+ \[[^\]]*\] ")


def builder_lines(path):
    out = []
    for line in open(path, errors="replace"):
        if not KEEP.search(line):
            continue
        out.append(STAMP.sub("", line.rstrip("\n")))
    return out


failed = False
modes = sorted(os.path.basename(p)[:-len("-lf.log")] for p in glob.glob(os.path.join(REF, "*-lf.log")))
for mode in modes:
    new_path = os.path.join(NEW, mode + "-lf.log")
    if not os.path.exists(new_path):
        print("FAIL  compare-%-22s new run has no %s-lf.log" % (mode, mode))
        failed = True
        continue
    ref = builder_lines(os.path.join(REF, mode + "-lf.log"))
    new = builder_lines(new_path)
    if ref == new:
        print("PASS  compare-%-22s %d builder lines identical to the jar LF run" % (mode, len(ref)))
        continue
    failed = True
    first = next((i for i, (a, b) in enumerate(zip(ref, new)) if a != b), min(len(ref), len(new)))
    print("FAIL  compare-%-22s ref %d lines, new %d lines, first difference at line %d" % (
        mode, len(ref), len(new), first + 1))
    print("        ref: %s" % (ref[first] if first < len(ref) else "<end>"))
    print("        new: %s" % (new[first] if first < len(new) else "<end>"))
sys.exit(1 if failed else 0)
