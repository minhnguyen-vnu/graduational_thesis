#!/usr/bin/env python3
"""Baseline-blindness analysis for the Tier-2 head-to-head.

WHY THIS EXISTS. The baseline arms run without --useExperimentalOracles, so fault 970 is
disabled by configuration. Reporting "baseline detected 0/20" on its own is therefore circular:
of course it scores zero, we turned the oracle off. The defensible claim is the same two-axis
argument used for Tier-1 (CLAUDE.md §6):

  AXIS 1 -- cannot JUDGE it. The Sahin oracles (F204-F208) are single-instant/cross-user; none
           models "permission reduced => must now be denied", so a post-downgrade 200 reads as
           success. This is a property of the published oracles, argued structurally.

  AXIS 2 -- cannot CONSTRUCT it. Measured here: in the baseline's own generated tests, does any
           single test ever assemble the triple -- write the guarded resource, downgrade the
           writer, then write AGAIN with the token captured before the downgrade?

A test only counts as a constructed triple if all four hold:
  (a) it calls the transition endpoint (PUT .../role),
  (b) it calls the guarded write (PUT .../secret) BOTH before and after that transition,
  (c) the two guarded writes use the SAME Authorization variable (a replayed token), and
  (d) that token was captured BEFORE the transition (EvoMaster hoists all logins to the top of
      the test, so any token in scope is pre-transition -- condition (c) effectively implies it,
      but we assert the ordering rather than assume it).

Usage:  baseline_blindness.py <results-dir> [<results-dir> ...]
"""
import re
import sys
import glob
import os

ROLE = "/role"
GUARD = "/secret"


def split_tests(src):
    parts = re.split(r"\n    def (test_\w+)\s*\(self\):", src)
    return [(parts[i], parts[i + 1]) for i in range(1, len(parts) - 1, 2)]


def calls(body):
    """Ordered (line_index, verb, url, auth_var) for each HTTP call in a test body."""
    lines = body.splitlines()
    out = []
    cur_auth = None
    for i, ln in enumerate(lines):
        m = re.search(r'headers\["Authorization"\]\s*=\s*(\w+)', ln)
        if m:
            cur_auth = m.group(1)
        m = re.search(r"\.(get|post|put|patch|delete)\(self\.baseUrlOfSut \+ \"([^\"]+)\"", ln)
        if m:
            out.append((i, m.group(1).upper(), m.group(2), cur_auth))
    return out


def analyse(d):
    src = "".join(open(f).read() for f in sorted(glob.glob(os.path.join(d, "EvoMaster_*_Test.py"))))
    if not src:
        return None
    tests = split_tests(src)
    n_role = n_guard = n_both = n_triple = 0
    triples = []
    for name, body in tests:
        cs = calls(body)
        role_at = [i for i, (_, v, u, _) in enumerate(cs) if ROLE in u and v in ("PUT", "PATCH")]
        guard_at = [i for i, (_, v, u, _) in enumerate(cs) if GUARD in u and v in ("PUT", "PATCH")]
        if role_at:
            n_role += 1
        if guard_at:
            n_guard += 1
        if not (role_at and guard_at):
            continue
        n_both += 1
        for r in role_at:
            before = [i for i in guard_at if i < r]
            after = [i for i in guard_at if i > r]
            # (c)+(d): same auth variable on a pre- and a post-transition guarded write
            shared = {cs[i][3] for i in before if cs[i][3]} & {cs[i][3] for i in after if cs[i][3]}
            if shared:
                n_triple += 1
                triples.append((name, sorted(shared)))
                break
    return dict(dir=os.path.basename(d), tests=len(tests), role=n_role, guard=n_guard,
                both=n_both, triple=n_triple, examples=triples[:3])


def main():
    rows = [r for r in (analyse(d) for d in sys.argv[1:]) if r]
    if not rows:
        print("no test files found", file=sys.stderr)
        return 1
    print(f"{'run':34s} {'tests':>6s} {'role':>5s} {'guard':>6s} {'both':>5s} {'TRIPLE':>7s}")
    for r in rows:
        print(f"{r['dir']:34s} {r['tests']:6d} {r['role']:5d} {r['guard']:6d} {r['both']:5d} {r['triple']:7d}")
    tot = sum(r["triple"] for r in rows)
    print(f"\nconstructed triples across {len(rows)} run(s): {tot}")
    for r in rows:
        for name, auth in r["examples"]:
            print(f"  {r['dir']}: {name}  (replayed token: {', '.join(auth)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
