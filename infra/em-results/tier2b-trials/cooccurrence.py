#!/usr/bin/env python3
"""
Did the fuzzer REACH the two endpoints of the MR-A1 triple, and did it ever COMPOSE them?

The distinction is the whole point of the Tier-2b result. A detector can miss a bug because it
never reached the relevant endpoints (a coverage problem) or because it reached them and never put
them in the right sequence with the right credential (a composition problem). Only the second is a
statement about the generator, and only the second is what this target demonstrates.

This is the same measurement that baseline_blindness.py applies to the Sahin baseline on Tier-2,
turned on our own tool.

Counting is per TEST METHOD, never per file: a generated file holds many independent tests, so
"this file mentions both endpoints" says nothing about whether any single test composes them.

Usage: python3 cooccurrence.py [run-dir ...]     (default: vuln-seed*)
"""
import glob
import os
import re
import sys

GUARD = "json/generate_apikey"
TRANSITION = "json/update_users"


def analyse(d):
    guard = transition = both = seq = 0
    for f in glob.glob(os.path.join(d, "*.py")):
        src = open(f, encoding="utf-8", errors="replace").read()
        parts = re.split(r"\n    def (test_\w+)", src)
        for i in range(1, len(parts), 2):
            body = parts[i + 1]
            g, t = GUARD in body, TRANSITION in body
            guard += g
            transition += t
            if not (g and t):
                continue
            both += 1
            calls = [m.group(1) for m in
                     re.finditer(r"json/(generate_apikey|update_users)", body)]
            if any(calls[k:k + 3] == ["generate_apikey", "update_users", "generate_apikey"]
                   for k in range(len(calls) - 2)):
                seq += 1
    return guard, transition, both, seq


if __name__ == "__main__":
    dirs = sys.argv[1:] or sorted(glob.glob("vuln-seed*"))
    print(f"{'run':<14}{'guard':>7}{'transition':>12}{'both':>7}{'g->t->g':>9}")
    for d in dirs:
        g, t, b, s = analyse(d)
        print(f"{d:<14}{g:>7}{t:>12}{b:>7}{s:>9}")
