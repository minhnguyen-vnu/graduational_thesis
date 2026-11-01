import csv
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
THESIS = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
LR = os.path.join(THESIS, "infra", "analysis", "lexicon-rules")
MODEL = "/Users/minhnguyen/IdeaProjects/EvoMaster/core/src/main/resources/stateful-authz-model.csv"
SPEC = os.path.join(HERE, "reports-api-docs-8081.json")
sys.path.insert(0, os.path.join(LR, "p2-model-20261012"))
sys.argv = [sys.argv[0]]
import derive_model as D


def tokens(text):
    out = set()
    for piece in re.split(r"[^A-Za-z0-9]+", text):
        if not piece:
            continue
        for t in re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+", piece):
            t = t.lower()
            if len(t) >= 4 and not t.isdigit():
                out.add(t)
    return out


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


W = {}
for r in csv.DictReader(open(MODEL)):
    W.setdefault(r["table"], {})[r["feature"]] = float(r["weight"])

lab, ops = D.load()
docs = D.op_docs(ops, lab)
npos = sum(1 for _, _, p in docs if p)
nneg = len(docs) - npos
print(f"ops {len(docs)}  T=1 {npos}  T=0 {nneg}  providers with T=1 {len({pr for _, pr, p in docs if p})}")
print(f"prior ln({npos}/{nneg}) = {math.log(npos / nneg):.3f}")
for t in ["p:role", "p:username", "p:users", "f:role", "f:username", "v:PUT", "v:POST"]:
    dp = sum(1 for fs, _, p in docs if p and t in fs)
    dn = sum(1 for fs, _, p in docs if not p and t in fs)
    pv = len({pr for fs, pr, p in docs if p and t in fs})
    w = math.log((dp + 1) / (npos + 2)) - math.log((dn + 1) / (nneg + 2))
    print(f"{t:12s} d_T {dp:3d}  d_N {dn:5d}  providers {pv:2d}  w = ln({dp + 1}/{npos + 2}) - ln({dn + 1}/{nneg + 2}) = {w:+.3f}  model {W['op'].get(t, float('nan')):+.3f}")

spec = json.load(open(SPEC))


def leaves(schema, acc):
    if "$ref" in schema:
        schema = spec["components"]["schemas"][schema["$ref"].split("/")[-1]]
    for k, v in (schema.get("properties") or {}).items():
        acc.append(k)
        leaves(v, acc)
    return acc


print("reports-api write ops, table op")
for path, methods in spec["paths"].items():
    for m, op in methods.items():
        if m.upper() not in ("POST", "PUT", "PATCH", "DELETE"):
            continue
        fs = {"v:" + m.upper()} | {"p:" + t for t in tokens(path)}
        for p in op.get("parameters", []):
            if p["in"] in ("path", "query"):
                fs |= {"f:" + t for t in tokens(p["name"])}
        for c in op.get("requestBody", {}).get("content", {}).values():
            for leaf in leaves(c.get("schema", {}), []):
                fs |= {"f:" + t for t in tokens(leaf)}
        parts = [(f, W["op"][f]) for f in sorted(fs) if f in W["op"]]
        score = W["op"]["__prior__"] + sum(w for _, w in parts)
        print(f"  {m.upper():6s} {path:24s} score {score:+.3f}  posterior {sigmoid(score):.4f}  " + " ".join(f"{f}{w:+.3f}" for f, w in parts))

for table, feats in [("role", ["k:enum", "l:body", "w:role", "n:role"]), ("victim", ["k:str", "l:path", "w:username", "n:username"])]:
    s = W[table]["__prior__"] + sum(W[table][f] for f in feats)
    print(f"{table} field: prior {W[table]['__prior__']:+.3f} " + " ".join(f"{f}{W[table][f]:+.3f}" for f in feats) + f" = {s:+.3f}  posterior {sigmoid(s):.4f}")

for v in ["VIEWER", "ADMIN"]:
    lo = max((w for k, w in W["low"].items() if k in v.lower()), default=0.0)
    hi = max((w for k, w in W["high"].items() if k in v.lower()), default=0.0)
    print(f"value {v}: low {lo:.3f} high {hi:.3f} k = low - high = {lo - hi:+.3f}")

final = {r["row_id"]: r for r in csv.DictReader(open(os.path.join(LR, "field-labelling-r4-20261006", "final-all.csv")))}
rows = {}
for line in open(os.path.join(LR, "field-labelling-r4-20261006", "rows-all.jsonl")):
    o = json.loads(line)
    rows[o["row_id"]] = o
for rid in ["S101-0104", "S101-0063", "S313-0010"]:
    o, l = rows[rid], final[rid]
    print(f"label {rid} {o['method']} {o['path']} fields {[f['loc'] + ':' + f['name'] for f in o['fields']]} T={l['T']} victim={l['victim']} role={l['role']} order={l['order']}")
