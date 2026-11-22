import json
import re
import secrets
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

MODE = sys.argv[1]
PORT = int(sys.argv[2])
REQLOG = sys.argv[3]

if MODE == "num":
    HIGH, LOW = 0, 1
elif MODE == "num1":
    HIGH, LOW = 1, 0
elif MODE == "bool":
    HIGH, LOW = True, False
elif MODE == "noplan":
    HIGH, LOW = "EDITOR", "VIEWER"
else:
    HIGH, LOW = "ADMIN", "VIEWER"
ENUM = ["EDITOR", "VIEWER"] if MODE == "noplan" else ["ADMIN", "VIEWER"]
NUMERIC = MODE in ("num", "num1")

LOCK = threading.Lock()
ROLES = {"alice": HIGH, "bob": LOW, "carol": LOW}
TOKENS = {}
LAST_SOURCE_USER = [None]


def json_body(properties):
    return {"required": True, "content": {"application/json": {"schema": {
        "type": "object", "properties": properties, "required": list(properties.keys())}}}}


def path_param(name):
    return {"name": name, "in": "path", "required": True, "schema": {"type": "string"}}


def operations():
    ops = [
        ("post", "/auth/login", [], json_body({"username": {"type": "string"}, "password": {"type": "string"}})),
        ("get", "/users", [], None),
        ("put", "/docs/{id}", [path_param("id")], json_body({"title": {"type": "string"}})),
    ]
    if NUMERIC:
        ops.append(("put", "/users/{username}/permission", [path_param("username")],
                    json_body({"permission": {"type": "integer"}, "role": {"type": "integer"}})))
    elif MODE == "bool":
        ops.append(("patch", "/users/{username}", [path_param("username")],
                    json_body({"is_admin": {"type": "boolean"}})))
    else:
        ops.append(("put", "/users/{username}/role", [path_param("username")],
                    json_body({"role": {"type": "string", "enum": ENUM}})))
    if MODE == "novictim":
        ops.append(("put", "/settings/role", [], json_body({"role": {"type": "string", "enum": ENUM}})))
    return ops


def spec():
    paths = {}
    for verb, path, params, body in operations():
        op = {"operationId": verb + re.sub(r"[^A-Za-z0-9]", "_", path), "responses": {"200": {
            "description": "ok", "content": {"application/json": {"schema": {"type": "object"}}}}}}
        if params:
            op["parameters"] = params
        if body:
            op["requestBody"] = body
        paths.setdefault(path, {})[verb] = op
    return {"openapi": "3.0.3", "info": {"title": "trim-" + MODE, "version": "1"}, "paths": paths}


def listing():
    key = "is_admin" if MODE == "bool" else "role"
    with LOCK:
        items = []
        for u, r in ROLES.items():
            item = {"username": u, key: r}
            if NUMERIC:
                item["permission"] = r
            items.append(item)
    return {"items": items}


class Handler(BaseHTTPRequestHandler):

    def log_message(self, *args):
        pass

    def reply(self, code, payload, record=None):
        if record is not None:
            record["code"] = code
            with LOCK:
                with open(REQLOG, "a") as fh:
                    fh.write(json.dumps(record) + "\n")
        data = json.dumps(payload).encode()
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
        with LOCK:
            return TOKENS.get(h[7:] if h.startswith("Bearer ") else "")

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == "/openapi.json":
            return self.reply(200, spec())
        with LOCK:
            LAST_SOURCE_USER[0] = None
        if self.caller() is None:
            return self.reply(401, {"error": "unauthenticated"})
        if url.path == "/users":
            return self.reply(200, listing())
        return self.reply(404, {"error": "not found"})

    def do_POST(self):
        url = urlsplit(self.path)
        if url.path != "/auth/login":
            return self.reply(404, {"error": "not found"})
        body = self.body() or {}
        u = body.get("username")
        if u not in ROLES or body.get("password") != str(u) + "pass":
            return self.reply(401, {"error": "bad credentials"})
        token = secrets.token_hex(16)
        with LOCK:
            TOKENS[token] = {"user": u, "role": ROLES[u]}
        return self.reply(200, {"token": token})

    def do_PUT(self):
        return self.write("PUT", urlsplit(self.path).path)

    def do_PATCH(self):
        return self.write("PATCH", urlsplit(self.path).path)

    def write(self, method, path):
        body = self.body()
        t = self.caller()
        rec = {"m": method, "path": path, "caller": t["user"] if t else None, "body": body, "applied": False}
        with LOCK:
            armed_for = LAST_SOURCE_USER[0]
            LAST_SOURCE_USER[0] = None
        if t is None:
            return self.reply(401, {"error": "unauthenticated"}, rec)
        if body is None:
            return self.reply(400, {"error": "bad body"}, rec)
        if method == "PUT" and re.fullmatch(r"/docs/[^/]+", path):
            if t["role"] != HIGH:
                return self.reply(403, {"error": "privileged role required"}, rec)
            with LOCK:
                LAST_SOURCE_USER[0] = t["user"]
            return self.reply(200, {"id": path.split("/")[-1], "title": body.get("title")}, rec)
        with LOCK:
            changer = ROLES[t["user"]]
        if MODE == "novictim" and method == "PUT" and path == "/settings/role":
            if changer != HIGH:
                return self.reply(403, {"error": "privileged role required"}, rec)
            return self.reply(200, {"role": body.get("role")}, rec)
        if NUMERIC:
            m = re.fullmatch(r"/users/([^/]+)/permission", path) if method == "PUT" else None
            value = body.get("role")
            valid = isinstance(value, int) and not isinstance(value, bool)
        elif MODE == "bool":
            m = re.fullmatch(r"/users/([^/]+)", path) if method == "PATCH" else None
            value = body.get("is_admin")
            valid = isinstance(value, bool)
        else:
            m = re.fullmatch(r"/users/([^/]+)/role", path) if method == "PUT" else None
            value = body.get("role")
            valid = value in ENUM
        if not m:
            return self.reply(404, {"error": "not found"}, rec)
        if changer != HIGH:
            return self.reply(403, {"error": "privileged role required"}, rec)
        target = m.group(1)
        if target not in ROLES:
            return self.reply(404, {"error": "no such user"}, rec)
        if not valid:
            return self.reply(400, {"error": "invalid role"}, rec)
        raising = value == HIGH and type(value) is type(HIGH)
        caller = t["user"]
        apply = caller != target and ((raising and caller == armed_for) or (not raising and target == armed_for))
        if apply:
            rec["applied"] = True
            with LOCK:
                ROLES[target] = value
        return self.reply(200, {"username": target, "role": value}, rec)


ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
