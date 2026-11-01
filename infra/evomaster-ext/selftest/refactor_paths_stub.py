import json
import re
import secrets
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODE = sys.argv[1]
PORT = int(sys.argv[2])

ACCOUNTS = {"alice": "ADMIN", "boss": "ADMIN", "bob": "ADMIN", "eve": "VIEWER"}
if MODE in ("unavailable", "budget"):
    ACCOUNTS = {"alice": "ADMIN", "boss": "VIEWER", "bob": "VIEWER"}
if MODE == "cap20":
    ACCOUNTS = {"u%02d" % i: "ADMIN" for i in range(1, 23)}
    ACCOUNTS["eve"] = "VIEWER"

ROLE_ENUM = ["ADMIN", "VIEWER"]
if MODE == "budget":
    ROLE_ENUM = ["ADMIN", "OWNER", "SUPERUSER", "VIEWER", "GUEST"]
ELEVATED = ("ADMIN", "OWNER", "SUPERUSER")

SOURCES = ["docs", "notes", "files"]
LOCK = threading.Lock()
ROLES = dict(ACCOUNTS)
TOKENS = {}


def password(user):
    return user + "pass"


def operations():
    ops = [("post", "/auth/login", {"username": {"type": "string"}, "password": {"type": "string"}}, [])]
    for s in SOURCES:
        ops.append(("put", "/%s/{id}" % s, {"title": {"type": "string"}}, ["id"]))
    if MODE == "unavailable":
        ops.append(("put", "/users/{username}/roles",
                    {"roles": {"type": "array", "items": {"type": "string"}}}, ["username"]))
    else:
        ops.append(("put", "/users/{username}/role", {"role": {"type": "string", "enum": ROLE_ENUM}}, ["username"]))
    if MODE == "cap5":
        ops.append(("put", "/permissions/{username}", {"permission": {"type": "string"}}, ["username"]))
    return ops


def spec():
    paths = {}
    for verb, path, body, params in operations():
        op = {"operationId": verb + re.sub(r"[^A-Za-z0-9]", "_", path),
              "responses": {"200": {"description": "ok", "content": {"application/json": {"schema": {"type": "object"}}}}}}
        if params:
            op["parameters"] = [{"name": p, "in": "path", "required": True, "schema": {"type": "string"}} for p in params]
        op["requestBody"] = {"required": True, "content": {"application/json": {"schema": {
            "type": "object", "properties": body, "required": list(body.keys())}}}}
        paths.setdefault(path, {})[verb] = op
    return {"openapi": "3.0.3", "info": {"title": "refactor-paths-" + MODE, "version": "1"}, "paths": paths}


class Handler(BaseHTTPRequestHandler):

    def log_message(self, *args):
        pass

    def reply(self, code, payload=None):
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

    def do_GET(self):
        if self.path == "/openapi.json":
            return self.reply(200, spec())
        return self.reply(404, {"error": "not found"})

    def do_POST(self):
        self.dispatch("post")

    def do_PUT(self):
        self.dispatch("put")

    def dispatch(self, verb):
        path = self.path.split("?")[0]
        body = self.body()
        if verb == "post" and path == "/auth/login":
            return self.login(body)
        t = self.caller()
        if t is None:
            return self.reply(401, {"error": "unauthenticated"})
        if body is None:
            return self.reply(400, {"error": "bad body"})
        m = re.fullmatch(r"/([a-z]+)/([^/]+)", path)
        if verb == "put" and m and m.group(1) in SOURCES:
            if t["role"] != "ADMIN":
                return self.reply(403, {"error": "forbidden"})
            return self.reply(200, {"id": m.group(2), "title": body.get("title")})
        m = re.fullmatch(r"/users/([^/]+)/roles?", path)
        if verb == "put" and m:
            return self.set_role(t, m.group(1), body)
        m = re.fullmatch(r"/permissions/([^/]+)", path)
        if verb == "put" and m and MODE == "cap5":
            if t["role"] != "ADMIN":
                return self.reply(403, {"error": "forbidden"})
            return self.apply(m.group(1), "VIEWER")
        return self.reply(404, {"error": "not found"})

    def login(self, body):
        if body is None:
            return self.reply(400, {"error": "bad body"})
        u = body.get("username")
        if not isinstance(u, str) or u not in ACCOUNTS or body.get("password") != password(u):
            return self.reply(401, {"error": "bad credentials"})
        token = secrets.token_hex(16)
        with LOCK:
            TOKENS[token] = {"user": u, "role": ROLES[u]}
        return self.reply(200, {"token": token})

    def apply(self, target, role):
        with LOCK:
            if target not in ROLES:
                return self.reply(404, {"error": "no such user"})
            ROLES[target] = role
        return self.reply(200, {"username": target, "role": role})

    def set_role(self, t, target, body):
        if t["role"] != "ADMIN":
            return self.reply(403, {"error": "forbidden"})
        with LOCK:
            known = target in ROLES
        if not known:
            return self.reply(404, {"error": "no such user"})
        if MODE == "cap5":
            return self.reply(422, {"error": "role changes are disabled"})
        if MODE == "unavailable":
            roles = body.get("roles")
            if not isinstance(roles, list):
                return self.reply(400, {"error": "roles must be a list"})
            return self.apply(target, "ADMIN" if "ADMIN" in roles else "VIEWER")
        role = body.get("role")
        if role not in ROLE_ENUM:
            return self.reply(400, {"error": "bad role"})
        if MODE == "cap20":
            return self.reply(200, {"username": target, "role": role})
        if MODE == "budget" and role in ELEVATED:
            return self.reply(422, {"error": "elevation needs a second approver"})
        return self.apply(target, role)


ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
