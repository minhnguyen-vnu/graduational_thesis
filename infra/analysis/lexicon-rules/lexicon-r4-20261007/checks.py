import csv, glob, hashlib, io, json, os, re, shutil, sys, tempfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lexlib as X
import measure as M

sim = X.sim
RESULTS = []


def report(code, ok, msg):
    RESULTS.append(ok)
    print("%s %s %s" % (code, "PASS" if ok else "FAIL", msg))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def c1():
    rows, provider = X.old_train()
    p, q = X.derive_old_rule(rows, provider)
    out = os.path.join(HERE, "c1-lexicon-from-old-labels.csv")
    X.write_lexicon(out, X.lexicon_rows(p, q))
    report("C1", sha(out) == sha(X.JAR_LEX),
           "old labels -> %d path, %d param; sha %s vs jar %s" % (len(p), len(q), sha(out)[:12], sha(X.JAR_LEX)[:12]))


def old_rank_text():
    sp = {s: half for s, (_, half) in X.old_split_map().items()}
    lab = {}
    for r in csv.DictReader(io.open(os.path.join(X.LR, "labelling-r2", "final.csv"), encoding="utf-8")):
        if r["final_label"] in ("R", "N"):
            lab[r["row_id"]] = r["final_label"]
    for f in ("labelling-r3/final.v2.csv", "labelling-r4/final.v2.csv"):
        for r in csv.DictReader(io.open(os.path.join(X.LR, f), encoding="utf-8")):
            if r["final_label"] in ("R", "N"):
                lab[r["row_id"]] = r["final_label"]
            else:
                lab.pop(r["row_id"], None)

    def ops(spec):
        for d in ("ops-full", "ops-ext"):
            p = os.path.join(X.CORPUS, d, spec + ".csv")
            if os.path.exists(p):
                return [r for r in csv.DictReader(io.open(p, encoding="utf-8")) if r["method"].upper() in X.VERBS]
        return []
    pw, qw = X.read_lexicon(X.JAR_LEX)

    def best(h):
        hit = [s for w, s in pw if w in h]
        return max(hit) if hit else 0.0

    def fh(r):
        return (r.get("body_field_names") or "").replace(";", " ").replace(",", " ").lower()
    sc = {"V0": lambda r: best(X.path_hay(r)), "V1": lambda r: best(X.path_hay(r) + " " + fh(r))}

    def userparam(r):
        n = (r["param_names"] or "").lower()
        return any(w in n for w, _ in qw)
    lines = []
    for v in ("V0", "V1"):
        for half in ("train", "test"):
            specs = sorted({s for s in sp if sp[s] == half})
            rows, tot = [], 0
            hb, hw, hs = ({k: 0 for k in M.KS} for _ in range(3))
            for s in specs:
                o = ops(s)
                if not o or not any(lab.get(r["row_id"]) == "R" for r in o):
                    continue
                tot += 1
                key = lambda r: (-sc[v](r), not userparam(r), X.VERBS.index(r["method"].upper()))
                groups = {}
                for r in o:
                    groups.setdefault(key(r), []).append(r)
                idx = {r["row_id"]: i for i, r in enumerate(o)}
                oseq = sorted(o, key=lambda r: key(r) + (idx[r["row_id"]],))
                rseq = min(i + 1 for i, r in enumerate(oseq) if lab.get(r["row_id"]) == "R")
                before, bst, wst, unres = 0, None, None, 0
                for k2 in sorted(groups):
                    g = groups[k2]
                    nr = sum(1 for r in g if lab.get(r["row_id"]) == "R")
                    if nr:
                        bst, wst = before + 1, before + (len(g) - nr) + 1
                        break
                    before += len(g)
                    unres += sum(1 for r in g if r["row_id"] not in lab)
                for k in M.KS:
                    hb[k] += bst <= k
                    hw[k] += wst <= k
                    hs[k] += rseq <= k
                rows.append("     %s hang %s/%d  thu-tu-spec %d%s" % (s, bst if bst == wst else "%d-%d" % (bst, wst), len(o), rseq,
                                                                      "  (%d dong chua ro xep tren)" % unres if unres else ""))
            lines.append("%s %s: %d spec co endpoint R" % (v, half, tot))
            lines.append("   " + " | ".join(
                "top-%d %d/%d = %.3f" % (k, hb[k], tot, hb[k] / float(tot)) if hb[k] == hw[k]
                else "top-%d %d-%d/%d = %.3f-%.3f" % (k, hw[k], hb[k], tot, hw[k] / float(tot), hb[k] / float(tot)) for k in M.KS))
            lines.append("   thu tu spec: " + " | ".join("top-%d %d/%d = %.3f" % (k, hs[k], tot, hs[k] / float(tot)) for k in M.KS))
            lines += rows
        lines.append("")
    return "\n".join(lines)


def c2():
    got = old_rank_text()
    ref = io.open(os.path.join(X.LR, "field-gate-20260923", "rank-field.txt"), encoding="utf-8").read()
    v1test = [l for l in got.splitlines() if l.startswith("V1 test")]
    idx = got.splitlines().index(v1test[0]) if v1test else -1
    report("C2", ref.startswith(got), "V0+V1 train/test blocks (%d lines) identical to rank-field.txt; V1 test: %s"
           % (len(got.splitlines()), got.splitlines()[idx + 2].strip() if idx >= 0 else "?"))


def c3():
    lab, ops, rows, provider = X.new_data()
    ref = json.load(open(os.path.join(X.R4DIR, "cv.json")))["repeats"][0]["rates"]
    pw, qw = X.read_lexicon(X.JAR_LEX)
    got = {"hard": defaultdict(dict), "derived": defaultdict(dict)}
    fl = next(M.folds(ops))
    for held in fl:
        tr = [op for op in ops if op["provider"] not in held]
        te = [op for op in ops if op["provider"] in held]
        r4 = sim.derive(tr, lab, "std")[0]
        for tag, LB in (("hard", sim.HARD), ("derived", r4)):
            ts, up, ao = M.scorer(pw, qw, LB["admin"])
            for m, d in M.sim_outcomes(te, lab, lambda s: True, LB, ts, up, ao).items():
                got[tag][m].update(d)
    pairs = [(t, m, sum(got[t][m].values()), ref[t][m]["yes"], len(got[t][m]), ref[t][m]["n"]) for t in ("hard", "derived") for m in ("M1", "M1any", "M2", "M5")]
    report("C3", all(a == b and c == d for _, _, a, b, c, d in pairs),
           "repeat 1 with jar lexicon: " + ", ".join("%s %s %d/%d (ref %d/%d)" % (t, m, a, c, b, d) for t, m, a, b, c, d in pairs))


def c4():
    p = os.path.join(X.R4DIR, "final-all.csv")
    ids = [r["row_id"] for r in csv.DictReader(open(p))]
    lab, ops, rows, provider = X.new_data()
    t1 = sum(1 for l in lab.values() if l["T"])
    tprov = len({op["provider"] for op in ops if lab[op["row_id"]]["T"]})
    ok = len(ids) == 10381 and len(set(ids)) == len(ids) and t1 == 199 and tprov == 56 and len(ops) == len(lab)
    report("C4", ok, "rows %d unique %d T=1 %d providers-with-T %d ops-with-row %d" % (len(ids), len(set(ids)), t1, tprov, len(ops)))


def c5():
    lab, ops, rows, provider = X.new_data()
    new = defaultdict(set)
    for op in ops:
        new[op["spec"]].add((op["method"].upper(), op["path"]))
    old = X.old_corpus()
    miss, tot, specs = [], 0, set()
    for r in old.values():
        tot += 1
        specs.add(r["spec_id"])
        if (r["method"].upper(), r["path"]) not in new.get(r["spec_id"], set()):
            miss.append((r["spec_id"], r["method"], r["path"]))
    report("C5", not miss and len(specs) > 0, "old rows %d in %d specs; not found in round-4 spec of same id: %d %s" % (tot, len(specs), len(miss), miss[:3]))


def c6(outdir):
    lab, ops, rows, provider = X.new_data()
    cands = {}
    for name in ("candidates-newV1-path.csv", "candidates-new-path.csv"):
        cands[name] = {r["tu"]: r for r in csv.DictReader(open(os.path.join(outdir, name)))}
    msgs, ok = [], True
    for w in ("permission", "admin", "user"):
        for name, hayf in (("candidates-newV1-path.csv", sim.hay), ("candidates-new-path.csv", lambda op: (op["path"] + " " + op["method"] + ":" + op["path"]).lower())):
            dr = dn = 0
            pv = set()
            for op in ops:
                if w in hayf(op).lower():
                    if lab[op["row_id"]]["T"]:
                        dr += 1
                        pv.add(op["provider"])
                    else:
                        dn += 1
            c = cands[name].get(w)
            if c is None:
                msgs.append("%s %s absent (independent dr=%d)" % (name.split("-")[1], w, dr))
                ok = ok and dr == 0
                continue
            same = (int(c["df_r"]), int(c["df_n"]), int(c["nha_cung_cap"])) == (dr, dn, len(pv))
            ok = ok and same
            msgs.append("%s %s %d/%d/%d vs %s/%s/%s" % (name.split("-")[1], w, dr, dn, len(pv), c["df_r"], c["df_n"], c["nha_cung_cap"]))
    report("C6", ok, "; ".join(msgs))


def c7(outdir):
    res = json.load(open(os.path.join(outdir, "cv.json")))
    leaks = [l for r in res["repeats"] for l in r["leak"]]
    lab, ops, rows, provider = X.new_data()
    present = set(res["old29"]) & {op["spec"] for op in ops}
    rows, _ = X.old_train()
    trained = {r["spec_id"] for r in rows}
    ok = (all(l["train_test_providers"] == 0 and l["test_specs_in_old29"] == 0 for l in leaks)
          and set(res["old29"]) == trained and len(trained) == 29 and len(present) == 29)
    report("C7", ok, "%d folds checked; excluded %d = specs with old training rows %d, present in round-4 corpus %d"
           % (len(leaks), len(res["old29"]), len(trained), len(present)))


def c8(outdir):
    res = json.load(open(os.path.join(outdir, "cv.json")))
    nc = res["negative_control"]
    a0 = res["repeats"][0]["rates_V"]["A-newV1-0"]["top1"]["yes"]
    ok = nc["top1_permuted"] < nc["top1_real"] and nc["top1_real"] == a0
    report("C8", ok, "top-1 real %d, permuted %d, random expected %.2f, of %d specs; real == A-newV1-0 repeat 1 (%d)"
           % (nc["top1_real"], nc["top1_permuted"], nc["top1_random_expected"], nc["specs"], a0))


def c9(outdir):
    tmp = tempfile.mkdtemp(dir=os.environ.get("TMPDIR", "/tmp"))
    M.main(tmp)
    names = ["cv.json", "targets.json", "lexicon-new.csv", "lexicon-newV1.csv"]
    diff = [n for n in names if sha(os.path.join(tmp, n)) != sha(os.path.join(outdir, n))]
    shutil.rmtree(tmp)
    report("C9", not diff, "second full run, differing files: %s" % (diff or "none"))


def c10(outdir):
    msgs, ok = [], True
    for n in ("lexicon-new.csv", "lexicon-newV1.csv"):
        rows = list(csv.reader(open(os.path.join(outdir, n), newline="")))
        head = rows[0] == ["kind", "word", "score"]
        body = rows[1:]
        kinds = {r[0] for r in body} <= {"path", "param"}
        uniq = len({(r[0], r[1]) for r in body}) == len(body)
        rng = all(0.0 < float(r[2]) < 1.0 for r in body)
        good = head and kinds and uniq and rng and len(body) > 0
        ok = ok and good
        msgs.append("%s %d path %d param ok=%s" % (n, sum(1 for r in body if r[0] == "path"), sum(1 for r in body if r[0] == "param"), good))
    report("C10", ok, "; ".join(msgs))


def rt_deref(doc, node, depth=0):
    while isinstance(node, dict) and "$ref" in node and depth < 20:
        ref = node["$ref"]
        if not ref.startswith("#/"):
            return {}
        cur = doc
        for part in ref[2:].split("/"):
            cur = cur.get(part, {}) if isinstance(cur, dict) else {}
        node, depth = cur, depth + 1
    return node if isinstance(node, dict) else {}


def rt_body(doc, op):
    rb = rt_deref(doc, op.get("requestBody") or {})
    out = []
    for ct in (rb.get("content") or {}).values():
        sch = rt_deref(doc, ct.get("schema") or {})
        if sch.get("type") == "array":
            sch = rt_deref(doc, sch.get("items") or {})
        out += list((sch.get("properties") or {}).keys())
        for comb in ("allOf", "oneOf", "anyOf"):
            for sub in sch.get(comb) or []:
                out += list((rt_deref(doc, sub).get("properties") or {}).keys())
    return sorted(set(out))


def c11():
    ref = io.open(os.path.join(X.LR, "field-gate-20260923", "rank-targets.txt"), encoding="utf-8").read().splitlines()
    pw, _ = X.read_lexicon(X.JAR_LEX)
    names = {"tier1": "reports-api", "tier2": "vampi-seeded", "tier2b": "pyLoad", "airflow": "Airflow"}
    spec = {t[0]: t for t in M.TARGETS}
    ok, msgs = True, []
    for tier, tname in names.items():
        _, path, tv, tp = spec[tname]
        doc = json.load(open(path))
        rows = []
        for p, item in (doc.get("paths") or {}).items():
            item = rt_deref(doc, item)
            for verb, op in item.items():
                if verb.upper() in X.VERBS and isinstance(op, dict):
                    rows.append({"method": verb.upper(), "path": p, "body": rt_body(doc, op)})
        sc = lambda r: max([s for w, s in pw if w in (r["path"] + " " + r["method"] + ":" + r["path"]).lower() + " " + " ".join(r["body"]).lower()] or [0.0])
        cand = [r for r in rows if sc(r) > 0.0]
        ranked = sorted(cand, key=lambda r: (-sc(r), X.VERBS.index(r["method"])))
        t = next(r for r in rows if r["method"] == tv and r["path"] == tp)
        s0 = sc(t)
        lo = sum(1 for r in ranked if sc(r) > s0) + 1
        hi = sum(1 for r in ranked if sc(r) >= s0)
        line = "%-8s %-10s ung vien %3d / %3d ghi | transition %s  diem %.4f" % (tier, "V1", len(cand), len(rows),
                                                                                "hang %s" % ("%d" % lo if lo == hi else "%d-%d" % (lo, hi)), s0)
        hit = line in ref
        ok = ok and hit
        msgs.append("%s %s" % (tier, "match" if hit else "MISMATCH: " + line))
    logs = glob.glob(os.path.join(X.LR, "..", "..", "em-results", "artifactkeeper-machine-20261001", "logs", "*"))
    pat = re.compile(r"transition candidate (\w+):(\S+) score ([0-9.]+) userParam \w+ reducedRoleValues (\d+)")
    seen = set()
    for f in logs:
        for l in io.open(f, encoding="utf-8", errors="replace"):
            m = pat.search(l)
            if m:
                seen.add((m.group(1), m.group(2), round(float(m.group(3)), 4), int(m.group(4)) > 0))
    _, path, tv, tp = spec["artifact-keeper"]
    tops = M.R.spec_ops(path)
    ts, up, _ = M.scorer(pw, X.read_lexicon(X.JAR_LEX)[1], sim.HARD["admin"])
    ranked = [op for op in tops if op["method"] in sim.VERB_ORDER and ts(op) > 0]
    ranked.sort(key=lambda op: (-ts(op), not up(op), sim.VERB_ORDER.index(op["method"])))
    red = M.R.fns(sim.HARD)[0]
    mine = {(op["method"], op["path"], round(ts(op), 4), bool(red(op, sim.HARD))) for op in ranked[:8]}
    hit = mine == seen and len(seen) == 8
    ok = ok and hit
    msgs.append("artifact-keeper top-8 vs AF2 log: %s (log %d, mine %d, only-log %s, only-mine %s)"
                % ("match" if hit else "MISMATCH", len(seen), len(mine), sorted(seen - mine)[:2], sorted(mine - seen)[:2]))
    report("C11", ok, "; ".join(msgs))


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else "all"
    outdir = HERE
    if stage in ("pre", "all"):
        c1()
        c2()
        c3()
        c4()
        c5()
        c11()
    if stage in ("post", "all"):
        c6(outdir)
        c7(outdir)
        c8(outdir)
        c10(outdir)
        c9(outdir)
    print("ALL PASS" if all(RESULTS) else "SOME FAIL")
    sys.exit(0 if all(RESULTS) else 1)


if __name__ == "__main__":
    main()
