import json
import sys

DROP = [
    ("delete", "/admin/users/{user_id}"),
    ("post", "/admin/users/{user_id}/disable"),
    ("put", "/admin/users/{user_id}/password"),
    ("post", "/admin/users/{user_id}/logout"),
    ("post", "/admin/users/{user_id}/revoke-auth-token"),
    ("put", "/user"),
    ("put", "/user/password"),
    ("post", "/user/revoke-auth-token"),
    ("delete", "/org/users/{user_id}"),
    ("delete", "/orgs/{org_id}/users/{user_id}"),
    ("delete", "/orgs/{org_id}"),
]

src, dst = sys.argv[1], sys.argv[2]
spec = json.load(open(src))
for verb, path in DROP:
    ops = spec["paths"][path]
    del ops[verb]
    print(f"dropped {verb.upper()} {path}")
    if not any(k in ops for k in ("get", "put", "post", "patch", "delete", "head", "options")):
        del spec["paths"][path]
json.dump(spec, open(dst, "w"), indent=1)
