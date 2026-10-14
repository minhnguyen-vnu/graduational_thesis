import json, random, sys
from collections import defaultdict

SEED = 20260918
SEED_EXT = 20260921
ENRICHED_CATS = {"security", "collaboration", "developer_tools", "enterprise"}
N_EXT = 15
OUR_TARGETS = ("vampi", "pyload", "reports-api")

data = json.load(open("apis-guru-list.json"))
used = {a["provider"] for a in json.load(open("sample-picked.json"))}
used |= {a["provider"] for a in json.load(open("sample-replacements.json"))}

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
        "enriched": bool(cats & ENRICHED_CATS),
        "swaggerUrl": v["swaggerUrl"], "openapiVer": v.get("openapiVer", ""),
    })

rng = random.Random(SEED)
one_per_provider = {}
for provider in sorted(by_provider):
    one_per_provider[provider] = rng.choice(sorted(by_provider[provider], key=lambda a: a["key"]))

pool = sorted(p for p, a in one_per_provider.items() if a["enriched"] and p not in used)
pick = sorted(random.Random(SEED_EXT).sample(pool, N_EXT))
out = []
for i, p in enumerate(pick):
    a = dict(one_per_provider[p])
    a["spec_id"] = "S%03d" % (200 + i)
    a["pool"] = "enriched"
    a["split"] = "train"
    out.append(a)

json.dump(out, open("sample-ext.json", "w"), indent=1, ensure_ascii=False)
print("pool giau con lai %d nha cung cap, da dung %d" % (len(pool), len(used)))
for a in out:
    print("| %s | %s | `%s` | enriched | train |" % (a["spec_id"], a["provider"], a["key"]))
