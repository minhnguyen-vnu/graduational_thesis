import json
import re
import secrets
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODE = sys.argv[1]
PORT = int(sys.argv[2])

ACCOUNTS = {"alice": "alicepass", "boss": "bosspass", "bob": "bobpass"}
ADMINS = {"alice", "boss"}
SOURCES = ["docs", "notes", "files"]

LOCK = threading.Lock()
STATE = {}


def default_state():
    if MODE == "num-two":
        return {u: {"permission": 2 if u in ADMINS else 1, "role": 2 if u in ADMINS else 1} for u in ACCOUNTS}
    if MODE == "bool-restricted":
        return {u: {"restricted": u not in ADMINS} for u in ACCOUNTS}
    if MODE == "access-level":
        return {u: {"access_level": 50 if u in ADMINS else 10, "enabled": True} for u in ACCOUNTS}
    return {u: {"role": "ADMIN" if u in ADMINS else "VIEWER"} for u in ACCOUNTS}


def admin_by_state(st):
    if MODE == "num-two":
        return st.get("permission", 0) >= 2
    if MODE == "bool-restricted":
        return not st.get("restricted", True)
    if MODE == "access-level":
        return st.get("access_level", 0) >= 50
    return st.get("role") == "ADMIN"


def live_state(u):
    with LOCK:
        return dict(STATE["roles"].get(u, {}))


def reset_state():
    with LOCK:
        STATE["roles"] = default_state()
        STATE["tokens"] = {}


reset_state()


def transition_op():
    if MODE == "num-two":
        return ("post", "/api/set_user_permission",
                {"user": {"type": "string"}, "permission": {"type": "integer"}, "role": {"type": "integer"}}, [])
    if MODE == "bool-restricted":
        return ("patch", "/users/{username}", {"restricted": {"type": "boolean"}}, ["username"])
    if MODE == "access-level":
        return ("put", "/groups/{id}/members/{username}",
                {"access_level": {"type": "integer"}, "enabled": {"type": "boolean"}}, ["id", "username"])
    if MODE == "path-id-username":
        return ("patch", "/users/{id}",
                {"username": {"type": "string"}, "role": {"type": "string", "enum": ["ADMIN", "VIEWER"]}}, ["id"])
    return ("put", "/users/{username}/role", {"role": {"type": "string", "enum": ["ADMIN", "VIEWER"]}}, ["username"])


def operations():
    ops = [("post", "/auth/login", {"username": {"type": "string"}, "password": {"type": "string"}}, [])]
    for s in SOURCES:
        if MODE == "put-id-source":
            ops.append(("put", "/%s/{id}" % s, {"title": {"type": "string"}}, ["id"]))
        else:
            ops.append(("post", "/%s" % s, {"title": {"type": "string"}}, []))
    if MODE == "gate-low":
        ops.append(("post", "/logs", {"message": {"type": "string"}}, []))
    ops.append(transition_op())
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
    return {"openapi": "3.0.3", "info": {"title": "p2-stub-" + MODE, "version": "1"}, "paths": paths}


def victim_object(u):
    st = live_state(u)
    if MODE == "num-two":
        return {"user": u, "id": "uid-" + u, "permission": st.get("permission"), "role": st.get("role")}
    if MODE == "bool-restricted":
        return {"username": u, "id": "uid-" + u, "restricted": st.get("restricted")}
    if MODE == "access-level":
        return {"username": u, "id": "uid-" + u, "access_level": st.get("access_level")}
    if MODE == "path-id-username":
        return {"username": u, "id": "uid-" + u, "role": "ADMIN" if admin_by_state(st) else "VIEWER"}
    return {"username": u, "id": "uid-" + u, "role": "ADMIN" if admin_by_state(st) else "VIEWER"}


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

    def read_body(self):
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
            return STATE["tokens"].get(token)

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
        body = self.read_body()
        if verb == "post" and path == "/auth/login":
            return self.login(body)
        if verb == "post" and path == "/thesis/reset":
            reset_state()
            return self.reply(200, {"reset": True})
        t = self.caller()
        sm = re.fullmatch(r"/([a-z]+)", path)
        pm = re.fullmatch(r"/([a-z]+)/([^/]+)", path)
        is_post_source = verb == "post" and sm and sm.group(1) in SOURCES
        is_put_source = verb == "put" and MODE == "put-id-source" and pm and pm.group(1) in SOURCES
        if is_post_source or is_put_source:
            if t is None:
                return self.reply(403 if MODE == "anon-deny" else 401, {"error": "no"})
            if not admin_by_state(t["snapshot"]):
                return self.reply(403, {"error": "forbidden"})
            if body is None:
                return self.reply(400, {"error": "bad body"})
            return self.reply(200, victim_object(t["user"]))
        if t is None:
            return self.reply(401, {"error": "unauthenticated"})
        if verb == "post" and path == "/logs" and MODE == "gate-low":
            return self.reply(403, {"error": "forbidden"})
        return self.transition(verb, path, t, body)

    def transition(self, verb, path, t, body):
        if not admin_by_state(t["snapshot"]):
            return self.reply(403, {"error": "forbidden"})
        if body is None:
            return self.reply(400, {"error": "bad body"})
        target, fields = self.target_and_fields(verb, path, body)
        if target is None:
            return self.reply(404, {"error": "not found"})
        with LOCK:
            if target not in STATE["roles"]:
                return self.reply(404, {"error": "no such user"})
            for k, v in fields.items():
                STATE["roles"][target][k] = v
        return self.reply(200, dict({"user": target}, **fields))

    def target_and_fields(self, verb, path, body):
        if MODE == "num-two" and verb == "post" and path == "/api/set_user_permission":
            f = {}
            if "permission" in body:
                f["permission"] = body["permission"]
            if "role" in body:
                f["role"] = body["role"]
            return body.get("user"), f
        if MODE == "bool-restricted":
            m = re.fullmatch(r"/users/([^/]+)", path)
            if verb == "patch" and m and isinstance(body.get("restricted"), bool):
                return m.group(1), {"restricted": body["restricted"]}
        if MODE == "access-level":
            m = re.fullmatch(r"/groups/([^/]+)/members/([^/]+)", path)
            if verb == "put" and m:
                return m.group(2), {"access_level": body.get("access_level")}
        if MODE == "path-id-username":
            m = re.fullmatch(r"/users/([^/]+)", path)
            if verb == "patch" and m:
                return m.group(1).replace("uid-", ""), {"role": body.get("role")}
        m = re.fullmatch(r"/users/([^/]+)/role", path)
        if verb == "put" and m:
            return m.group(1), {"role": body.get("role")}
        return None, {}

    def login(self, body):
        if body is None:
            return self.reply(400, {"error": "bad body"})
        u = body.get("username")
        if u not in ACCOUNTS or body.get("password") != ACCOUNTS.get(u):
            return self.reply(401, {"error": "bad credentials"})
        token = secrets.token_hex(16)
        with LOCK:
            STATE["tokens"][token] = {"user": u, "snapshot": dict(STATE["roles"].get(u, {}))}
        return self.reply(200, {"token": token})


ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
