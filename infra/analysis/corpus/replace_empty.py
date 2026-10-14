import json, random, subprocess, sys
from collections import defaultdict

SEED = 20260918
ENRICHED_CATS = {"security", "collaboration", "developer_tools", "enterprise"}
OUR_TARGETS = ("vampi", "pyload", "reports-api")
EMPTY = json.load(open("empty-specs.json"))

picked = json.load(open("sample-picked.json"))
data = json.load(open("apis-guru-list.json"))

by_provider = defaultdict(list)
for key, entry in data.items():
    v = entry["versions"][entry["preferred"]]
    info = v["info"]
    provider = info.get("x-providerName") or key.split(":")[0]
    if any(t in key.lower() or t in provider.lower() for t in OUR_TARGETS):
        continue
    cats = set(info.get("x-apisguru-categories") or [])
    by_provider[provider].append({
        "key": key, "provider": provider, "categories": sorted(cats),
        "enriched": bool(cats & ENRICHED_CATS), "swaggerUrl": v["swaggerUrl"],
    })

rng = random.Random(SEED)
one_per_provider = {}
for provider in sorted(by_provider):
    one_per_provider[provider] = rng.choice(sorted(by_provider[provider], key=lambda a: a["key"]))

used = {a["provider"] for a in picked}
rng2 = random.Random(SEED + 1)
out = []
next_id = 130
for spec_id in EMPTY:
    old = next(a for a in picked if a["spec_id"] == spec_id)
    pool = sorted(p for p, a in one_per_provider.items()
                  if a["enriched"] == (old["pool"] == "enriched") and p not in used)
    prov = rng2.choice(pool)
    used.add(prov)
    new = dict(one_per_provider[prov])
    new.update({"spec_id": "S%03d" % next_id, "pool": old["pool"], "split": old["split"],
                "replaces": spec_id})
    next_id += 1
    out.append(new)

json.dump(out, open("sample-replacements.json", "w"), indent=1, ensure_ascii=False)
for a in out:
    print("%s thay %s | %s | %s | %s" % (a["spec_id"], a["replaces"], a["provider"], a["pool"], a["split"]))
