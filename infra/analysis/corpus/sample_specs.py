import json, random, sys
from collections import defaultdict

SEED = 20260918
ENRICHED_CATS = {"security", "collaboration", "developer_tools", "enterprise"}
N_ENRICHED = 20
N_RANDOM = 10
TEST_FRACTION = 0.5
OUR_TARGETS = ("vampi", "pyload", "reports-api")

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
        "key": key,
        "provider": provider,
        "categories": sorted(cats),
        "enriched": bool(cats & ENRICHED_CATS),
        "swaggerUrl": v["swaggerUrl"],
        "openapiVer": v.get("openapiVer", ""),
    })

rng = random.Random(SEED)
one_per_provider = {}
for provider in sorted(by_provider):
    apis = sorted(by_provider[provider], key=lambda a: a["key"])
    one_per_provider[provider] = rng.choice(apis)

enriched_pool = sorted([p for p, a in one_per_provider.items() if a["enriched"]])
random_pool = sorted([p for p, a in one_per_provider.items() if not a["enriched"]])

enriched_pick = sorted(rng.sample(enriched_pool, N_ENRICHED))
random_pick = sorted(rng.sample(random_pool, N_RANDOM))
picked = [one_per_provider[p] for p in enriched_pick + random_pick]

for i, a in enumerate(picked):
    a["spec_id"] = "S%03d" % (100 + i)
    a["pool"] = "enriched" if a["provider"] in enriched_pick else "random"

order = list(picked)
rng.shuffle(order)
n_test = round(len(order) * TEST_FRACTION)
test = {a["provider"] for a in order[:n_test]}
for a in picked:
    a["split"] = "test" if a["provider"] in test else "train"

if "--json" in sys.argv:
    print(json.dumps(picked, indent=1, ensure_ascii=False))
else:
    print("pool giau %d nha cung cap, pool ngau nhien %d" % (len(enriched_pool), len(random_pool)))
    print("| spec_id | nha cung cap | API | pool | split | categories |")
    print("|---|---|---|---|---|---|")
    for a in picked:
        print("| %s | %s | `%s` | %s | %s | %s |"
              % (a["spec_id"], a["provider"], a["key"], a["pool"], a["split"], ", ".join(a["categories"]) or "-"))
    print()
    print("train %d, test %d" % (sum(1 for a in picked if a["split"] == "train"),
                                 sum(1 for a in picked if a["split"] == "test")))
