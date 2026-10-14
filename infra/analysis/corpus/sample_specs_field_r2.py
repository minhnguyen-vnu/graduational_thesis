import json, random
from collections import defaultdict

SEED = 20260918
SEED_R2 = 20261006
ENRICHED_CATS = {"security", "collaboration", "developer_tools", "enterprise"}
N_RANDOM = 63
EXCLUDE = ("airflow", "vampi", "pyload", "reports-api", "grafana", "mattermost", "vikunja",
           "callcenter", "truthy", "bamf", "artifact-keeper")

data = json.load(open("apis-guru-list.json"))
used = set()
for f in ("sample-picked.json", "sample-replacements.json", "sample-ext.json",
          "sample-field.json", "sample-field-replacements.json"):
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

enriched = sorted(p for p, a in one_per_provider.items() if a["enriched"] and p not in used)
rand_pool = sorted(p for p, a in one_per_provider.items() if not a["enriched"] and p not in used)
pick_r = random.Random(SEED_R2).sample(rand_pool, N_RANDOM)
rest = sorted(set(rand_pool) - set(pick_r))
reserve = random.Random(SEED_R2 + 1).sample(rest, min(len(rest), 60))

out = []
for p in enriched:
    out.append(dict(one_per_provider[p], pool="enriched", split="test"))
for p in sorted(pick_r):
    out.append(dict(one_per_provider[p], pool="random", split="test"))
for i, a in enumerate(out):
    a["spec_id"] = "S%03d" % (500 + i)

json.dump(out, open("sample-field-r2.json", "w"), indent=1, ensure_ascii=False)
json.dump([dict(one_per_provider[p], pool="random", split="test") for p in reserve],
          open("sample-field-r2-reserve.json", "w"), indent=1, ensure_ascii=False)
print("giau %d, ngau nhien %d, du phong %d" % (len(enriched), len(pick_r), len(reserve)))
for a in out:
    print("| %s | %s | `%s` | %s |" % (a["spec_id"], a["provider"], a["key"], a["pool"]))
