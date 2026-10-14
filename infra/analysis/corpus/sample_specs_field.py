import json, random, sys
from collections import defaultdict

SEED = 20260918
SEED_FIELD = 20261004
ENRICHED_CATS = {"security", "collaboration", "developer_tools", "enterprise"}
N_PER_POOL = 50
EXCLUDE = ("airflow", "vampi", "pyload", "reports-api", "grafana", "mattermost", "vikunja",
           "callcenter", "truthy", "bamf", "artifact-keeper")

data = json.load(open("apis-guru-list.json"))
used = set()
for f in ("sample-picked.json", "sample-replacements.json", "sample-ext.json"):
    used |= {a["provider"] for a in json.load(open(f))}

by_provider = defaultdict(list)
for key, entry in data.items():
    v = entry["versions"][entry["preferred"]]
    info = v["info"]
    provider = info.get("x-providerName") or key.split(":")[0]
    if any(t in key.lower() or t in provider.lower() for t in EXCLUDE):
        continue
    cats = set(info.get("x-apisguru-categories") or [])
    by_provider[provider].append({
        "key": key, "provider": provider, "categories": sorted(cats),
        "enriched": bool(cats & ENRICHED_CATS),
        "swaggerUrl": v["swaggerUrl"], "openapiVer": v.get("openapiVer", ""),
    })

rng = random.Random(SEED)
one_per_provider = {}
for provider in sorted(by_provider):
    one_per_provider[provider] = rng.choice(sorted(by_provider[provider], key=lambda a: a["key"]))

out = []
reserve = {}
for pool_name, flag in (("enriched", True), ("random", False)):
    pool = sorted(p for p, a in one_per_provider.items() if a["enriched"] == flag and p not in used)
    pick = random.Random(SEED_FIELD).sample(pool, N_PER_POOL)
    rest = sorted(set(pool) - set(pick))
    reserve[pool_name] = random.Random(SEED_FIELD + 1).sample(rest, min(len(rest), N_PER_POOL))
    order = sorted(pick)
    random.Random(SEED_FIELD).shuffle(order)
    half = {p: ("train" if i < N_PER_POOL // 2 else "test") for i, p in enumerate(order)}
    print("tang %s: con %d nha cung cap, boc %d" % (pool_name, len(pool), len(pick)))
    for p in sorted(pick):
        a = dict(one_per_provider[p], pool=pool_name, split=half[p])
        out.append(a)

for i, a in enumerate(out):
    a["spec_id"] = "S%03d" % (300 + i)

json.dump(out, open("sample-field.json", "w"), indent=1, ensure_ascii=False)
json.dump({k: [dict(one_per_provider[p], pool=k) for p in v] for k, v in reserve.items()},
          open("sample-field-reserve.json", "w"), indent=1, ensure_ascii=False)
for a in out:
    print("| %s | %s | `%s` | %s | %s |" % (a["spec_id"], a["provider"], a["key"], a["pool"], a["split"]))
