import json
import sys

DROP = {
    ("post", "/auth/logout"),
    ("post", "/users/{userId}/password"),
    ("post", "/webhook-subscriptions"),
    ("put", "/webhook-subscriptions/{subscriptionId}"),
    ("delete", "/webhook-subscriptions/{subscriptionId}"),
}

src, dst = sys.argv[1], sys.argv[2]
spec = json.load(open(src, encoding="utf-8"))
dropped = []
for path, item in spec["paths"].items():
    for verb in list(item):
        if (verb, path) in DROP:
            del item[verb]
            dropped.append(f"{verb.upper()} {path}")
spec["paths"] = {"/api/v1" + k: v for k, v in spec["paths"].items()}
spec["servers"] = [{"url": "/"}]
json.dump(spec, open(dst, "w", encoding="utf-8"), indent=1)
print(len(dropped), "dropped:", "; ".join(dropped))
