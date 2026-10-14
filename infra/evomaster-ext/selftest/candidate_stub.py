import json
import re
import secrets
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODE = sys.argv[1]
PORT = int(sys.argv[2])

ACCOUNTS = {
    "alice": ("alicepass", "ADMIN"),
    "boss": ("bosspass", "ADMIN"),
    "bob": ("bobpass", "VIEWER"),
}
if MODE in ("restore-budget", "bool-flag"):
    ACCOUNTS["boss"] = ("bosspass", "VIEWER")
if MODE == "proven-404":
    ACCOUNTS["carol"] = ("carolpass", "ADMIN")

SOURCES = ["docs", "notes", "files"]
if MODE == "cap20":
    SOURCES = ["docs", "notes", "files", "sheets", "slides", "boards", "pages", "links", "tasks", "memos", "wikis", "forms"]

ALPHA_DECOYS = ["audit", "export", "import", "refresh", "report", "rebuild", "archive", "purge"]

DECOY_MODES = ("noop-decoy", "reject-decoy", "restore-budget")

LOCK = threading.Lock()
STATE = {}


def reset_state():
    with LOCK:
        STATE["roles"] = {u: r for u, (_, r) in ACCOUNTS.items() if not (MODE == "proven-404" and u == "carol")}
        STATE["tokens"] = {}


reset_state()


def source_allowed(source, user, role):
    if MODE == "proven-404":
        if source == "notes":
            return user == "carol"
        if user == "carol":
            return False
    return role == "ADMIN"


def operations():
    ops = [("post", "/auth/login", {"username": {"type": "string"}, "password": {"type": "string"}}, [])]
    for s in SOURCES:
        ops.append(("put", "/%s/{id}" % s, {"title": {"type": "string"}}, ["id"]))
    if MODE == "bool-flag":
        ops.append(("patch", "/users/{username}", {"is_admin": {"type": "boolean"}}, ["username"]))
    else:
        ops.append(("put", "/users/{username}/role", {"role": {"type": "string", "enum": ["ADMIN", "VIEWER"]}}, ["username"]))
    if MODE in DECOY_MODES:
        ops.append(("put", "/permissions/{username}", {"permission": {"type": "string"}}, ["username"]))
    if MODE == "alpha":
        for d in ALPHA_DECOYS:
            ops.append(("post", "/permissions/%s" % d, None, []))
    if MODE == "cap20":
        ops.append(("post", "/reset", None, []))
    return ops


def spec():
    paths = {}
    for verb, path, body, params in operations():
        op = {"operationId": verb + re.sub(r"[^A-Za-z0-9]", "_", path),
              "responses": {"200": {"description": "ok", "content": {"application/json": {"schema": {"type": "object"}}}}}}
        if params:
            op["parameters"] = [{"name": p, "in": "path", "required": True, "schema": {"type": "string"}} for p in params]
        if body is not None:
            op["requestBody"] = {"required": True, "content": {"application/json": {"schema": {
                "type": "object", "properties": body, "required": list(body.keys())}}}}
        paths.setdefault(path, {})[verb] = op
    return {"openapi": "3.0.3", "info": {"title": "candidate-stub-" + MODE, "version": "1"}, "paths": paths}


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
            t = STATE["tokens"].get(token)
        if t is None or t["revoked"]:
            return None
        return t

    def do_GET(self):
        if self.path == "/openapi.json":
            return self.reply(200, spec())
        return self.reply(404, {"error": "not found"})

    def do_POST(self):
        self.dispatch("post")

    def do_PUT(self):
        self.dispatch("put")

    def do_PATCH(self):
        self.dispatch("patch")

    def dispatch(self, verb):
        path = self.path.split("?")[0]
        body = self.body()
        if verb == "post" and path == "/auth/login":
            return self.login(body)
        if verb == "post" and path == "/reset" and MODE == "cap20":
            reset_state()
            return self.reply(200, {"reset": True})
        t = self.caller()
        if t is None:
            return self.reply(401, {"error": "unauthenticated"})
        if body is None:
            return self.reply(400, {"error": "bad body"})
        m = re.fullmatch(r"/([a-z]+)/([^/]+)", path)
        if verb == "put" and m and m.group(1) in SOURCES:
            if not source_allowed(m.group(1), t["user"], t["role"]):
                return self.reply(403, {"error": "forbidden"})
            return self.reply(200, {"id": m.group(2), "title": body.get("title")})
        m = re.fullmatch(r"/users/([^/]+)/role", path)
        if verb == "put" and m and MODE != "bool-flag":
            return self.set_role(t, m.group(1), body.get("role"))
        m = re.fullmatch(r"/users/([^/]+)", path)
        if verb == "patch" and m and MODE == "bool-flag":
            flag = body.get("is_admin")
            if not isinstance(flag, bool):
                return self.reply(400, {"error": "is_admin must be boolean"})
            return self.set_role(t, m.group(1), "ADMIN" if flag else "VIEWER")
        m = re.fullmatch(r"/permissions/([^/]+)", path)
        if verb == "put" and m and MODE in DECOY_MODES:
            if MODE == "noop-decoy":
                return self.reply(200, {"username": m.group(1), "permission": body.get("permission")})
            if t["role"] != "ADMIN":
                return self.reply(403, {"error": "forbidden"})
            return self.reply(422, {"error": "unknown permission"})
        if verb == "post" and MODE == "alpha" and m and m.group(1) in ALPHA_DECOYS:
            return self.reply(200, {"done": m.group(1)})
        return self.reply(404, {"error": "not found"})

    def login(self, body):
        if body is None:
            return self.reply(400, {"error": "bad body"})
        u = body.get("username")
        acc = ACCOUNTS.get(u) if isinstance(u, str) else None
        if acc is None or body.get("password") != acc[0]:
            return self.reply(401, {"error": "bad credentials"})
        token = secrets.token_hex(16)
        with LOCK:
            role = STATE["roles"].get(u, acc[1])
            STATE["tokens"][token] = {"user": u, "role": role, "revoked": False}
        return self.reply(200, {"token": token})

    def set_role(self, t, target, role):
        if t["role"] != "ADMIN":
            return self.reply(403, {"error": "forbidden"})
        if MODE == "protected-victim" and target == "boss":
            return self.reply(403, {"error": "protected account"})
        with LOCK:
            known = target in STATE["roles"]
        if not known:
            return self.reply(404, {"error": "no such user"})
        if role not in ("ADMIN", "VIEWER"):
            return self.reply(400, {"error": "bad role"})
        if MODE == "cap20":
            return self.reply(200, {"username": target, "role": role})
        with LOCK:
            STATE["roles"][target] = role
            if MODE == "revoke":
                for tok in STATE["tokens"].values():
                    if tok["user"] == target:
                        tok["revoked"] = True
        return self.reply(200, {"username": target, "role": role})


ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
