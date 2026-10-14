import json
import sys

import yaml

DROP = {
    ("post", "/api/v4/users/logout"),
    ("delete", "/api/v4/users"),
    ("delete", "/api/v4/users/{user_id}"),
    ("put", "/api/v4/users/{user_id}"),
    ("put", "/api/v4/users/{user_id}/patch"),
    ("put", "/api/v4/users/{user_id}/active"),
    ("put", "/api/v4/users/{user_id}/password"),
    ("post", "/api/v4/users/password/reset"),
    ("put", "/api/v4/users/{user_id}/mfa"),
    ("post", "/api/v4/users/{user_id}/convert_to_bot"),
    ("post", "/api/v4/users/{user_id}/sessions/revoke"),
    ("post", "/api/v4/users/{user_id}/sessions/revoke/all"),
    ("post", "/api/v4/users/sessions/revoke/all"),
    ("put", "/api/v4/users/{user_id}/auth"),
    ("post", "/api/v4/users/migrate_auth/ldap"),
    ("post", "/api/v4/users/migrate_auth/saml"),
    ("put", "/api/v4/config"),
    ("put", "/api/v4/config/patch"),
    ("post", "/api/v4/config/reload"),
    ("post", "/api/v4/config/migrate"),
    ("post", "/api/v4/restart"),
    ("post", "/api/v4/database/recycle"),
    ("post", "/api/v4/license"),
    ("delete", "/api/v4/license"),
    ("post", "/api/v4/saml/reset_auth_data"),
}

src, dst = sys.argv[1], sys.argv[2]
spec = yaml.safe_load(open(src, encoding="utf-8"))
dropped = []
for path, item in spec["paths"].items():
    for verb in list(item):
        if (verb, path) in DROP:
            del item[verb]
            dropped.append(f"{verb.upper()} {path}")
missing = sorted(f"{v.upper()} {p}" for v, p in DROP if f"{v.upper()} {p}" not in dropped)
spec["servers"] = [{"url": "/"}]
json.dump(spec, open(dst, "w", encoding="utf-8"), default=str)
print(f"dropped {len(dropped)} of {len(DROP)}")
for m in missing:
    print(f"missing {m}")
