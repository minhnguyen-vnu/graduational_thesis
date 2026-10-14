import csv, hashlib, json, math, os, random, re, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "..", "..", "corpus")
LEX = os.path.join(HERE, "..", "lexicon-20260921-audited", "stateful-authz-lexicon.csv")
SEED = 20261006
MAX_TRANSITION_CANDIDATES = 8
VERB_ORDER = ["PUT", "PATCH", "POST", "DELETE"]
ADMIN_SCORE = 0.6

HARD = {
    "role": ["role", "plan", "permission", "level", "tier"],
    "admin": ["is_admin", "isadmin", "is_superuser", "is_superadmin", "is_staff"],
    "spec": ["username", "userid", "user_id", "user", "account", "member", "subject", "principal"],
    "email": ["email"],
    "id": ["id"],
    "low": ["view", "read", "guest", "basic", "free", "member", "user", "none", "restrict", "limited"],
    "high": ["admin", "owner", "super", "root", "manage", "write", "edit", "power", "full"],
}

STD = ["userName", "name", "displayName", "nickName", "profileUrl", "title", "userType", "preferredLanguage",
       "locale", "timezone", "active", "password", "emails", "phoneNumbers", "ims", "photos", "addresses", "groups",
       "entitlements", "roles", "x509Certificates", "members", "user", "role", "permission", "session", "operation",
       "object"]
R3 = os.path.join(HERE, "..", "field-labelling-r3-20261006")

PATH_LEX = [(r["word"].lower(), float(r["score"])) for r in csv.DictReader(open(LEX)) if r["kind"] == "path"]
PARAM_LEX = [r["word"].lower() for r in csv.DictReader(open(LEX)) if r["kind"] == "param"]


def providers():
    def meta(files):
        out = {}
        for f in files:
            for a in json.load(open(os.path.join(CORPUS, f))):
                out[a["spec_id"]] = a["provider"]
        return out
    m1 = meta(("sample-picked.json", "sample-replacements.json", "sample-ext.json", "sample-field.json",
               "sample-field-replacements.json"))
    m2 = meta(("sample-field-r2.json", "sample-field-r2-replacements.json"))
    return m1, m2


def leaf(name):
    return name.split(".")[-1].replace("[]", "")


def gene_kind(f):
    t = f["type"]
    if t == "boolean":
        return "bool"
    if f["enum"]:
        return "enum"
    if t in ("integer", "number"):
        return "num"
    if t == "string":
        return "str"
    if t.startswith("array"):
        return "array"
    if t == "object":
        return "object"
    return "other"


def load_ops(keep):
    m1, m2 = providers()
    spec_round = {}
    for line in open(os.path.join(R3, "rows.jsonl")):
        r = json.loads(line)
        spec_round[r["spec_id"]] = r["round"]
    ops = []
    for line in open(os.path.join(HERE, "rows-all.jsonl")):
        r = json.loads(line)
        if r["row_id"] not in keep:
            continue
        prov = (m1 if spec_round[r["spec_id"]] == "r1" else m2)[r["spec_id"]]
        fields = []
        for f in r["fields"]:
            if f["name"] == "(body)":
                continue
            fields.append({"loc": f["loc"], "name": f["name"], "key": "%s:%s" % (f["loc"], f["name"]),
                           "leaf": leaf(f["name"]).lower(), "raw_leaf": leaf(f["name"]), "type": f["type"],
                           "enum": [str(v) for v in f["enum"]], "kind": gene_kind(f)})
        ops.append({"row_id": r["row_id"], "spec": r["spec_id"], "provider": prov, "method": r["method"],
                    "path": r["path"], "schema": r.get("schema", ""), "fields": fields, "pos": r.get("pos") or 0})
    ops.sort(key=lambda o: (o["spec"], o["pos"], o["row_id"]))
    return ops


def load_labels(path):
    lab = {}
    for r in csv.DictReader(open(path)):
        split = lambda s: [x.strip() for x in (s or "").split("|") if x.strip()]
        lab[r["row_id"].strip()] = {"T": (r.get("T") or "0").strip() == "1", "victim": split(r.get("victim")),
                                    "role": split(r.get("role")), "order": (r.get("order") or "").strip()}
    return lab


def genes(op):
    out = [(f["leaf"], f["kind"], f) for f in op["fields"]]
    if op["schema"]:
        out.append((op["schema"].lower(), "object", None))
    return out


def hay(op):
    top = [f["name"] for f in op["fields"] if f["loc"] == "body" and "." not in f["name"] and "[" not in f["name"]]
    return (op["path"] + " " + op["method"] + ":" + op["path"] + " " + " ".join(top)).lower()


def path_score(op):
    h = hay(op)
    return max([s for w, s in PATH_LEX if w in h] or [0.0])


def admin_hit(op, L):
    h = hay(op)
    return any(w in h for w in L["admin"])


def transition_score(op, L):
    return max(path_score(op), ADMIN_SCORE if admin_hit(op, L) else 0.0)


def has_user_param(op):
    return any(any(w in n for w in PARAM_LEX) for n, _, _ in genes(op))


def role_genes(op, L):
    return [(n, k, f) for n, k, f in genes(op) if any(w in n for w in L["role"])]


def admin_genes(op, L):
    return [(n, k, f) for n, k, f in genes(op) if k == "bool" and any(w in n for w in L["admin"])]


def is_low(v, L):
    lv = v.lower()
    return any(w in lv for w in L["low"]) and not any(w in lv for w in L["high"])


def reduced_candidates(op, L):
    rg, ag = role_genes(op, L), admin_genes(op, L)
    if not rg and not ag:
        return []
    vocab = []
    for f in op["fields"]:
        if f["kind"] == "enum":
            for v in f["enum"]:
                if v not in vocab:
                    vocab.append(v)
    low = [v for v in vocab if is_low(v, L)]
    num = ["1", "0", "2"] if any(k == "num" for _, k, _ in rg) else []
    strs = ["user", "viewer", "guest", "member", "basic"] if any(k == "str" for _, k, _ in rg) else []
    empty = ["[]"] if any(f is not None and f["loc"] == "body" and k == "array" for _, k, f in rg) else []
    adm = ["false"] if ag else []
    res = []
    for v in adm + low + empty + num + [v for v in vocab if v not in low] + strs:
        if v not in res:
            res.append(v)
    return res


def matched_role_keys(op, L):
    keys = {f["key"] for _, _, f in role_genes(op, L) if f is not None}
    keys |= {f["key"] for _, _, f in admin_genes(op, L)}
    return keys


def pick_victim(op, L):
    specific = [w for w in L["spec"] if w != "id"]
    tiers = [specific, L["email"], ["id"]]
    for loc in ("path", "body"):
        gs = [(n, k, f) for n, k, f in genes(op) if (f is not None and f["loc"] == loc) or (f is None and loc == "body")]
        for sig in tiers:
            for n, k, f in gs:
                if f is not None and any(w in n for w in sig) and k in ("str", "num"):
                    return f
    qsig = specific + ["id"]
    for f in op["fields"]:
        if f["loc"] == "query" and "." not in f["name"] and any(w in f["leaf"] for w in qsig) and f["kind"] in ("str", "num"):
            return f
    return None


def viable_transitions(oplist, L):
    ranked = [op for op in oplist if op["method"] in VERB_ORDER and transition_score(op, L) > 0]
    ranked.sort(key=lambda op: (-transition_score(op, L), not has_user_param(op), VERB_ORDER.index(op["method"])))
    return [op for op in ranked[:MAX_TRANSITION_CANDIDATES] if reduced_candidates(op, L)]


def tokens(raw):
    parts = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", raw)
    parts = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", parts)
    out = set()
    for t in re.split(r"[^A-Za-z0-9]+", parts):
        t = t.lower()
        if len(t) > 4 and t.endswith("s"):
            t = t[:-1]
        if len(t) >= 4:
            out.add(t)
    return out


def docs(ops, lab, which):
    out = []
    for op in ops:
        l = lab.get(op["row_id"])
        if not l or not l["T"]:
            continue
        for f in op["fields"]:
            if which == "role":
                if f["kind"] == "bool":
                    continue
                out.append((f, f["key"] in l["role"], op["provider"]))
            elif which == "admin":
                if f["kind"] != "bool":
                    continue
                out.append((f, f["key"] in l["role"], op["provider"]))
            elif which == "victim":
                out.append((f, f["key"] in l["victim"], op["provider"]))
    return out


def order_docs(ops, lab):
    enums = []
    for op in ops:
        l = lab.get(op["row_id"])
        if not l or not l["T"] or "<" not in l["order"]:
            continue
        levels = [[x.strip().lower() for x in g.split("=") if x.strip()] for g in l["order"].split("<")]
        if len(levels) < 2:
            continue
        enums.append((levels, op["provider"]))
    return enums


def std_terms():
    out = set()
    for t in STD:
        out |= tokens(t)
        out.add(t.lower())
    return out


def rule(docs_list, hand, use_hand, rng_seed):
    cand = set()
    for f, pos, _ in docs_list:
        if pos:
            cand |= tokens(f["raw_leaf"])
            cand.add(f["leaf"])
    if use_hand == "hand":
        cand |= set(hand)
    elif use_hand == "std":
        cand |= std_terms()
    pos_p, any_p = defaultdict(set), defaultdict(set)
    for w in cand:
        for f, pos, p in docs_list:
            if w in f["leaf"]:
                any_p[w].add(p)
                if pos:
                    pos_p[w].add(p)
    return select(cand, pos_p, any_p, rng_seed)


def select(cand, pos_p, any_p, rng_seed):
    provs = sorted({p for s in any_p.values() for p in s})
    def passes(w, weight):
        pos = sum(weight.get(p, 0) for p in pos_p[w])
        an = sum(weight.get(p, 0) for p in any_p[w])
        return pos >= 3 and an > 0 and pos / an >= 0.5
    ones = {p: 1 for p in provs}
    base = [w for w in cand if passes(w, ones)]
    rng = random.Random(rng_seed)
    hits = Counter()
    for _ in range(200):
        weight = Counter(rng.choice(provs) for _ in provs) if provs else Counter()
        for w in base:
            if passes(w, weight):
                hits[w] += 1
    kept = sorted(w for w in base if hits[w] >= 140)
    kept = [w for w in kept if not any(o != w and len(o) < len(w) and o in w for o in kept)]
    stats = {w: {"pos": len(pos_p[w]), "any": len(any_p[w]), "boot": hits[w] / 200} for w in sorted(cand) if pos_p[w]}
    return sorted(kept), stats


def rule_order(enums, side, hand, use_hand, rng_seed):
    cand = set()
    for levels, _ in enums:
        for v in (levels[0] if side == "low" else levels[-1]):
            cand |= tokens(v)
            cand.add(v)
    if use_hand == "hand":
        cand |= set(hand)
    pos_p, any_p = defaultdict(set), defaultdict(set)
    for levels, p in enums:
        target = levels[0] if side == "low" else levels[-1]
        for w in cand:
            for lv in levels:
                for v in lv:
                    if w in v:
                        any_p[w].add(p)
                        if lv is target:
                            pos_p[w].add(p)
    return select(cand, pos_p, any_p, rng_seed)


def derive(ops, lab, use_hand, seed=SEED):
    role, rs = rule(docs(ops, lab, "role"), HARD["role"], use_hand, seed)
    admin, ad = rule(docs(ops, lab, "admin"), HARD["admin"], use_hand, seed)
    vic, vs = rule(docs(ops, lab, "victim"), HARD["spec"] + HARD["email"], use_hand, seed)
    vic = [w for w in vic if w != "id"]
    enums = order_docs(ops, lab)
    nprov = len({p for _, p in enums})
    L = {"role": role, "admin": admin, "spec": [w for w in vic if w != "email"],
         "email": ["email"] if "email" in vic else [], "id": ["id"]}
    info = {"B_enums": len(enums), "B_providers": nprov, "B_sufficient": len(enums) >= 15 and nprov >= 10,
            "stats": {"role": rs, "admin": ad, "victim": vs}}
    if info["B_sufficient"]:
        low, ls = rule_order(enums, "low", HARD["low"], use_hand, seed)
        high, hs = rule_order(enums, "high", HARD["high"], use_hand, seed)
        L["low"], L["high"] = low, high
        info["stats"]["low"], info["stats"]["high"] = ls, hs
    else:
        L["low"], L["high"] = HARD["low"], HARD["high"]
    return L, info


def outcomes(ops, lab, L):
    by_spec = defaultdict(list)
    for op in ops:
        by_spec[op["spec"]].append(op)
    m1, m1any, m2, m3, m4, m5 = {}, {}, {}, {}, {}, {}
    for s, oplist in by_spec.items():
        tops = [op for op in oplist if lab[op["row_id"]]["T"]]
        tops_role = [op for op in tops if lab[op["row_id"]]["role"]]
        viable = viable_transitions(oplist, L)
        def hit(op):
            l = lab[op["row_id"]]
            return l["T"] and bool(matched_role_keys(op, L) & set(l["role"]))
        if tops_role:
            m1[s] = bool(viable) and hit(viable[0])
            m1any[s] = any(hit(op) for op in viable)
        if not tops:
            m2[s] = bool(viable)
    for op in ops:
        l = lab[op["row_id"]]
        if l["T"] and l["victim"] and l["victim"] != ["self"]:
            v = pick_victim(op, L)
            m3[op["row_id"]] = v is not None and v["key"] in l["victim"]
        if l["T"] and "<" in l["order"]:
            low = [x.strip().lower() for x in l["order"].split("<")[0].split("=") if x.strip()]
            c = reduced_candidates(op, L)
            m4[op["row_id"]] = bool(c) and c[0].lower() in low
        if not l["T"]:
            m5[op["row_id"]] = admin_hit(op, L) and path_score(op) < ADMIN_SCORE
    return {"M1": m1, "M1any": m1any, "M2": m2, "M3": m3, "M4": m4, "M5": m5}


def mcnemar(a, b):
    keys = sorted(set(a) & set(b))
    n01 = sum(1 for k in keys if not a[k] and b[k])
    n10 = sum(1 for k in keys if a[k] and not b[k])
    n = n01 + n10
    if n == 0:
        return {"n": len(keys), "b_only": n01, "a_only": n10, "p": 1.0}
    k = min(n01, n10)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)
    return {"n": len(keys), "b_only": n01, "a_only": n10, "p": round(p, 4)}


def boot_diff(a, b, unit_prov, seed=SEED, reps=2000):
    keys = sorted(set(a) & set(b))
    byp = defaultdict(list)
    for k in keys:
        byp[unit_prov[k]].append(k)
    provs = sorted(byp)
    if not provs:
        return None
    rng = random.Random(seed)
    diffs = []
    for _ in range(reps):
        ks = [k for p in (rng.choice(provs) for _ in provs) for k in byp[p]]
        if ks:
            diffs.append((sum(b[k] for k in ks) - sum(a[k] for k in ks)) / len(ks))
    diffs.sort()
    return [round(diffs[int(0.025 * len(diffs))], 3), round(diffs[int(0.975 * len(diffs)) - 1], 3)]


def rate(d):
    return {"n": len(d), "yes": sum(d.values()), "rate": round(sum(d.values()) / len(d), 3) if d else None}


def cv(ops, lab):
    provs = sorted({op["provider"] for op in ops})
    rng = random.Random(SEED)
    reps = []
    for rep in range(4):
        order = provs[:]
        rng.shuffle(order)
        folds = [set(order[i::5]) for i in range(5)]
        pooled = {"hard": defaultdict(dict), "derived": defaultdict(dict), "hand": defaultdict(dict),
                  "corpus": defaultdict(dict), "r3": defaultdict(dict)}
        lists = []
        for i, held in enumerate(folds):
            train = [op for op in ops if op["provider"] not in held]
            test = [op for op in ops if op["provider"] in held]
            Ld, info_d = derive(train, lab, "std")
            Lh, info_h = derive(train, lab, "hand")
            Lc, info_c = derive(train, lab, "none")
            lists.append({"fold": i, "derived": Ld, "hand": Lh, "corpus": Lc, "B_sufficient": info_d["B_sufficient"],
                          "B_enums": info_d["B_enums"], "B_providers": info_d["B_providers"]})
            for tag, L in (("hard", HARD), ("derived", Ld), ("hand", Lh), ("corpus", Lc), ("r3", R3L)):
                for m, d in outcomes(test, lab, L).items():
                    pooled[tag][m].update(d)
        reps.append({"pooled": pooled, "lists": lists})
    return reps


def anchors(L):
    rows = [
        ("reports-api", "role", ["role"], ["username"]),
        ("vampi-seeded", "role", ["role"], ["username"]),
        ("pyLoad", "role", ["permission", "role"], ["user"]),
        ("artifact-keeper", "admin", ["is_admin"], ["id"]),
        ("Airflow", "role", ["roles"], ["username"]),
        ("bamf", None, [], ["email"]),
    ]
    out = []
    for target, kind, afields, cfields in rows:
        a = {f: (any(w in f for w in L["admin"]) if kind == "admin" else any(w in f for w in L["role"])) for f in afields}
        c = {f: any(w in f for w in L["spec"] + L["email"] + L["id"]) for f in cfields}
        out.append({"target": target, "A": a, "C": c})
    return out


R3L = json.load(open(os.path.join(R3, "lists", "final-lists.json")))["derived"]


def main(label_file, outdir):
    lab = load_labels(label_file)
    ops = load_ops(set(lab))
    missing = [op["row_id"] for op in ops if op["row_id"] not in lab]
    keys = {op["row_id"]: {f["key"] for f in op["fields"]} for op in ops}
    bad = []
    for rid, l in lab.items():
        for k in l["victim"] + l["role"]:
            if k != "self" and k not in keys.get(rid, set()):
                bad.append((rid, k))
    unit_prov = {op["spec"]: op["provider"] for op in ops}
    unit_prov.update({op["row_id"]: op["provider"] for op in ops})
    reps = cv(ops, lab)
    res = {"label_file": os.path.basename(label_file), "lexicon_sha256": hashlib.sha256(open(LEX, "rb").read()).hexdigest(),
           "ops": len(ops), "specs": len({op["spec"] for op in ops}), "providers": len({op["provider"] for op in ops}),
           "T1_ops": sum(1 for op in ops if lab[op["row_id"]]["T"]),
           "T1_providers": len({op["provider"] for op in ops if lab[op["row_id"]]["T"]}),
           "missing_labels": len(missing), "label_keys_not_in_rows": bad, "repeats": []}
    for r, rep in enumerate(reps):
        P = rep["pooled"]
        row = {"repeat": r + 1, "rates": {t: {m: rate(P[t][m]) for m in P[t]} for t in P}, "tests": {}}
        for other in ("derived", "hand", "corpus", "r3"):
            for m in ("M1", "M1any", "M2", "M3", "M4"):
                row["tests"]["%s_vs_hard_%s" % (other, m)] = dict(mcnemar(P["hard"][m], P[other][m]),
                                                                     ci95_diff=boot_diff(P["hard"][m], P[other][m], unit_prov) if r == 0 else None)
        row["fold_lists"] = rep["lists"]
        res["repeats"].append(row)
    Ld, info_d = derive(ops, lab, "std")
    Lh, info_h = derive(ops, lab, "hand")
    Lc, info_c = derive(ops, lab, "none")
    TL = (("hard", HARD), ("derived", Ld), ("hand", Lh), ("corpus", Lc), ("r3", R3L))
    final = {"hard": HARD, "derived": Ld, "hand": Lh, "corpus": Lc, "r3": R3L,
             "B": {k: info_d[k] for k in ("B_enums", "B_providers", "B_sufficient")},
             "anchors": {t: anchors(L) for t, L in TL},
             "full_data_rates": {t: {m: rate(d) for m, d in outcomes(ops, lab, L).items()} for t, L in TL}}
    os.makedirs(os.path.join(outdir, "lists"), exist_ok=True)
    json.dump(res, open(os.path.join(outdir, "cv.json"), "w"), indent=1, default=list)
    json.dump(final, open(os.path.join(outdir, "lists", "final-lists.json"), "w"), indent=1)
    for tag, info in (("derived", info_d), ("hand", info_h), ("corpus", info_c)):
        with open(os.path.join(outdir, "lists", "stats-%s.csv" % tag), "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["list", "word", "pos_providers", "any_providers", "boot_pass_rate", "kept"])
            L = {"derived": Ld, "hand": Lh, "corpus": Lc}[tag]
            keptmap = {"role": L["role"], "admin": L["admin"], "victim": L["spec"] + L["email"],
                       "low": L["low"], "high": L["high"]}
            for lst, st in info["stats"].items():
                for word, s in sorted(st.items(), key=lambda kv: (-kv[1]["pos"], kv[0])):
                    w.writerow([lst, word, s["pos"], s["any"], s["boot"], word in keptmap[lst]])
    print(json.dumps({k: res[k] for k in ("ops", "specs", "providers", "T1_ops", "T1_providers", "missing_labels")}))
    print("bad label keys:", len(bad))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
