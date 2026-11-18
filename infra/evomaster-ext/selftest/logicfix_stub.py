import json
import re
import secrets
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

MODE = sys.argv[1]
PORT = int(sys.argv[2])
REQLOG = sys.argv[3]
LOCK_AFTER = int(sys.argv[4]) if len(sys.argv) > 4 else -1

ENUM = ["ADMIN", "VIEWER"]
SOURCE_ROLES = {"ADMIN"}
CHANGER_ROLES = {"ADMIN"}
ACCOUNTS = {"alice": "ADMIN", "boss": "ADMIN", "bob": "ADMIN", "eve": "VIEWER"}
if MODE == "login-name":
    ENUM = ["ADMIN", "EDITOR", "VIEWER"]
    SOURCE_ROLES = {"EDITOR"}
    ACCOUNTS = {"alice": "VIEWER", "boss": "ADMIN", "bob": "EDITOR", "eve": "VIEWER"}
if MODE == "enum-lower":
    ENUM = ["admin", "user"]
    SOURCE_ROLES = {"admin"}
    CHANGER_ROLES = {"admin"}
    ACCOUNTS = {"alice": "admin", "boss": "admin", "bob": "admin", "eve": "user"}
if MODE == "two-role-fields":
    SOURCE_ROLES = {0}
    CHANGER_ROLES = {0}
    ACCOUNTS = {"alice": 0, "boss": 0, "bob": 0, "eve": 1}
if MODE == "source-401":
    ENUM = ["ADMIN", "EDITOR", "VIEWER"]
    SOURCE_ROLES = {"EDITOR"}
    ACCOUNTS = {"alice": "ADMIN", "boss": "ADMIN", "bob": "EDITOR", "eve": "VIEWER"}
if MODE == "num-enum":
    SOURCE_ROLES = {50}
    CHANGER_ROLES = {50}
    ACCOUNTS = {"alice": 50, "boss": 50, "bob": 50, "eve": 10}
IDS = {"alice": 11, "boss": 12, "bob": 13, "eve": 14}

LOCK = threading.Lock()
ROLES = dict(ACCOUNTS)
TOKENS = {}
LAST_SOURCE_USER = [None]
COUNT = [0]


def json_body(properties, required=None):
    return {"required": True, "content": {"application/json": {"schema": {
        "type": "object", "properties": properties,
        "required": list(properties.keys()) if required is None else required}}}}


def path_param(name, kind="string"):
    return {"name": name, "in": "path", "required": True, "schema": {"type": kind}}


def query_param(name, schema, required=True):
    return {"name": name, "in": "query", "required": required, "schema": schema}


def operations():
    role = {"type": "string", "enum": ENUM}
    user = [path_param("username")]
    ops = [
        ("post", "/auth/login", [], json_body({"username": {"type": "string"}, "password": {"type": "string"}})),
        ("get", "/users", [], None),
        ("put", "/docs/{id}", [path_param("id")], json_body({"title": {"type": "string"}})),
    ]
    if MODE == "post-source":
        ops.append(("post", "/notes", [], json_body({"text": {"type": "string"}})))
    if MODE == "c4-intact":
        ops.append(("put", "/files/{id}", [path_param("id")], json_body({"name": {"type": "string"}})))
    if MODE == "two-role-fields":
        ops.append(("put", "/users/{username}/role",
                    user + [query_param("permission", {"type": "integer"}), query_param("role", {"type": "integer"})], None))
    elif MODE == "bool-victim":
        ops.append(("patch", "/users/{username}", user, json_body({"is_admin": {"type": "boolean"}})))
        ops.append(("put", "/admin/role", [],
                    json_body({"client_id": {"type": "string"}, "role": {"type": "string", "enum": ENUM}})))
    elif MODE == "query-username":
        ops.append(("put", "/users/{username}/role", user + [query_param("username", {"type": "string"})],
                    json_body({"role": role})))
    elif MODE == "no-path-id":
        ops.append(("put", "/users/{id}", [path_param("id", "integer")],
                    json_body({"username": {"type": "string"}, "role": role})))
    elif MODE == "num-enum":
        ops.append(("put", "/users/{username}/role", user,
                    json_body({"access_level": {"type": "integer", "enum": [10, 30, 50]}})))
    elif MODE == "nested-role":
        ops.append(("put", "/users/{username}/role", user,
                    json_body({"settings": {"type": "object", "properties": {"role": role}, "required": ["role"]},
                               "note": {"type": "string"}}, required=[])))
    else:
        ops.append(("put", "/users/{username}/role", user, json_body({"role": role})))
    return ops


def spec():
    paths = {}
    for verb, path, params, body in operations():
        op = {"operationId": verb + re.sub(r"[^A-Za-z0-9]", "_", path),
              "responses": {"200": {"description": "ok", "content": {"application/json": {"schema": {"type": "object"}}}}}}
        if params:
            op["parameters"] = params
        if body:
            op["requestBody"] = body
        paths.setdefault(path, {})[verb] = op
    return {"openapi": "3.0.3", "info": {"title": "logicfix-" + MODE, "version": "1"}, "paths": paths}


def listing():
    items = []
    with LOCK:
        for user, role in ROLES.items():
            item = {"username": user} if MODE == "no-path-id" else {"id": IDS[user], "username": user}
            if MODE == "bool-victim":
                item["is_admin"] = False
            elif MODE == "two-role-fields":
                item["role"] = role
                item["permission"] = role
            elif MODE == "num-enum":
                item["access_level"] = role
            else:
                item["role"] = role
            items.append(item)
    return {"page": 1, "items": items}


class Handler(BaseHTTPRequestHandler):

    def log_message(self, *args):
        pass

    def reply(self, code, payload=None, record=None):
        with LOCK:
            COUNT[0] += 1
            n = COUNT[0]
        if record is not None:
            record["n"] = n
            record["code"] = code
            now = time.time()
            record["t"] = time.strftime("%H:%M:%S", time.localtime(now)) + ".%03d" % int((now % 1) * 1000)
            with LOCK:
                with open(REQLOG, "a") as fh:
                    fh.write(json.dumps(record) + "\n")
        data = json.dumps(payload if payload is not None else {}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        try:
            parsed = json.loads(raw or b"{}")
        except ValueError:
            return None
        return parsed if isinstance(parsed, dict) else None

    def caller(self):
        h = self.headers.get("Authorization") or ""
        token = h[7:] if h.startswith("Bearer ") else ""
        with LOCK:
            return TOKENS.get(token)

    def record(self, method, url, body, t):
        return {"m": method, "path": url.path, "query": parse_qs(url.query), "body": body,
                "caller": t["user"] if t else None, "armed": False}

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == "/openapi.json":
            return self.reply(200, spec())
        t = self.caller()
        rec = self.record("GET", url, None, t)
        with LOCK:
            LAST_SOURCE_USER[0] = None
        if t is None:
            return self.reply(401, {"error": "unauthenticated"}, rec)
        if url.path == "/users":
            return self.reply(200, listing(), rec)
        return self.reply(404, {"error": "not found"}, rec)

    def do_POST(self):
        url = urlsplit(self.path)
        if url.path == "/auth/login":
            return self.login(self.body())
        return self.write("POST", url)

    def do_PUT(self):
        return self.write("PUT", urlsplit(self.path))

    def do_PATCH(self):
        return self.write("PATCH", urlsplit(self.path))

    def write(self, method, url):
        body = self.body()
        t = self.caller()
        rec = self.record(method, url, body, t)
        with LOCK:
            armed_for = LAST_SOURCE_USER[0]
            LAST_SOURCE_USER[0] = None
        if t is None:
            return self.reply(401, {"error": "unauthenticated"}, rec)
        if body is None:
            return self.reply(400, {"error": "bad body"}, rec)
        path = url.path
        if method == "PUT" and re.fullmatch(r"/files/[^/]+", path):
            return self.source(t, True, {"id": path.split("/")[-1], "name": body.get("name")}, rec)
        if method == "PUT" and re.fullmatch(r"/docs/[^/]+", path):
            return self.source(t, MODE != "post-source", {"id": path.split("/")[-1], "title": body.get("title")}, rec)
        if method == "POST" and path == "/notes":
            return self.source(t, True, {"text": body.get("text")}, rec)
        if method == "PUT" and path == "/admin/role":
            if ROLES[t["user"]] not in CHANGER_ROLES:
                return self.reply(403, {"error": "forbidden"}, rec)
            return self.reply(200, {"client_id": body.get("client_id")}, rec)
        m = re.fullmatch(r"/users/([^/]+)(/role)?", path)
        if not m:
            return self.reply(404, {"error": "not found"}, rec)
        target = m.group(1)
        if ROLES[t["user"]] not in CHANGER_ROLES:
            return self.reply(403, {"error": "forbidden"}, rec)
        if target not in ROLES:
            return self.reply(404, {"error": "no such user"}, rec)
        armed = target == armed_for and t["user"] != target
        rec["armed"] = armed
        if not armed and MODE == "source-401":
            return self.reply(409, {"error": "role change needs a fresh source call by the target"}, rec)
        if armed and MODE == "first-404" and target == "bob":
            return self.reply(404, {"error": "no such user in the role service"}, rec)
        return self.change_role(target, body, parse_qs(url.query), armed, rec)

    def source(self, t, stale, payload, rec):
        role = t["role"] if stale else ROLES[t["user"]]
        if role not in SOURCE_ROLES:
            return self.reply(403, {"error": "forbidden"}, rec)
        with LOCK:
            LAST_SOURCE_USER[0] = t["user"]
        return self.reply(200, payload, rec)

    def login(self, body):
        if body is None:
            return self.reply(400, {"error": "bad body"})
        u = body.get("username")
        if not isinstance(u, str) or u not in ACCOUNTS or body.get("password") != u + "pass":
            return self.reply(401, {"error": "bad credentials"})
        with LOCK:
            locked = MODE == "source-401" and u == "bob" and 0 <= LOCK_AFTER <= COUNT[0]
        if locked:
            return self.reply(401, {"error": "account locked"})
        token = secrets.token_hex(16)
        with LOCK:
            TOKENS[token] = {"user": u, "role": ROLES[u]}
        return self.reply(200, {"token": token})

    def change_role(self, target, body, query, armed, rec):
        if MODE == "bool-victim":
            flag = body.get("is_admin")
            if not isinstance(flag, bool):
                return self.reply(400, {"error": "is_admin must be a boolean"}, rec)
            role = "ADMIN" if flag else "VIEWER"
        elif MODE == "two-role-fields":
            try:
                role = int((query.get("role") or [""])[0])
                int((query.get("permission") or [""])[0])
            except ValueError:
                return self.reply(400, {"error": "role and permission must be integers"}, rec)
        elif MODE == "num-enum":
            role = body.get("access_level")
            if role not in (10, 30, 50):
                return self.reply(400, {"error": "bad access_level"}, rec)
        elif MODE == "nested-role":
            settings = body.get("settings")
            role = settings.get("role") if isinstance(settings, dict) else None
        else:
            role = body.get("role")
        if MODE not in ("two-role-fields", "num-enum") and role not in ENUM:
            return self.reply(400, {"error": "bad role"}, rec)
        if MODE == "query-username" and (query.get("username") or [None])[0] != target:
            return self.reply(400, {"error": "username does not match the target"}, rec)
        if armed and MODE != "c4-intact":
            with LOCK:
                ROLES[target] = role
        return self.reply(200, {"username": target, "role": role}, rec)


ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
