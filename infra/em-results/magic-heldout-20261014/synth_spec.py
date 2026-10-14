import json
import sys

SRC = sys.argv[1]
DST = sys.argv[2]

TYPEMAP = {
    "string": "string", "long": "integer", "int": "integer", "integer": "integer",
    "bool": "boolean", "boolean": "boolean", "decimal": "number", "double": "number",
    "date": "string", "guid": "string",
}

eps = json.load(open(SRC, encoding="utf-8"))
paths = {}
for e in eps:
    raw = e.get("path", "")
    verb = e.get("verb", "").lower()
    if not raw or verb not in {"get", "post", "put", "patch", "delete"}:
        continue
    url = "/" + raw.lstrip("/")
    if "/auth/" in url:
        continue
    args = e.get("input") or []
    consumes_json = e.get("consumes") == "application/json"
    op = {"responses": {"200": {"description": "ok"}}, "operationId": verb + "_" + raw.replace("/", "_")}
    if consumes_json and verb in {"post", "put", "patch"}:
        props = {a["name"]: {"type": TYPEMAP.get(str(a.get("type", "string")).lower(), "string")} for a in args if a.get("name")}
        op["requestBody"] = {"content": {"application/json": {"schema": {"type": "object", "properties": props}}}}
    else:
        op["parameters"] = [
            {"name": a["name"], "in": "query", "required": False,
             "schema": {"type": TYPEMAP.get(str(a.get("type", "string")).lower(), "string")}}
            for a in args if a.get("name")
        ]
    paths.setdefault(url, {})[verb] = op

doc = {
    "openapi": "3.0.0",
    "info": {"title": "magic synthesized", "version": "v24.0.3"},
    "servers": [{"url": "/"}],
    "paths": paths,
}
json.dump(doc, open(DST, "w", encoding="utf-8"))
ops = sum(1 for p, it in paths.items() for m in it)
print("synthesized " + str(ops) + " ops across " + str(len(paths)) + " paths")
for key in ["/magic/system/magic/roles", "/magic/system/magic/users_roles", "/magic/system/auth/authenticate"]:
    print("  " + key + ": " + (",".join(sorted(paths.get(key, {}).keys())) or "MISSING"))
