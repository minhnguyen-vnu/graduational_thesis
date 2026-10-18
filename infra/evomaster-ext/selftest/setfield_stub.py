import json
import re
import secrets
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(sys.argv[1])
RECORD = sys.argv[2]

ACCOUNTS = {"alice": "alicepass", "boss": "bosspass", "bob": "bobpass"}
ADMINS = {"alice", "boss"}
SOURCES = ["docs", "notes", "files"]
NULLABLE = {"display_name": "string", "email": "string", "is_active": "boolean", "is_admin": "boolean"}

LOCK = threading.Lock()
STATE = {"seq": 0}


def reset_state():
    with LOCK:
        STATE["users"] = {u: {"display_name": u, "email": u + "@example.org", "is_active": True,
                              "is_admin": u in ADMINS} for u in ACCOUNTS}
        STATE["tokens"] = {}


reset_state()


def record(entry):
    with LOCK:
        STATE["seq"] += 1
        entry["seq"] = STATE["seq"]
        with open(RECORD, "a") as f:
            f.write(json.dumps(entry) + "\n")


def ok(schema):
    return {"200": {"description": "ok", "content": {"application/json": {"schema": schema}}}}


def json_body(schema):
    return {"required": True, "content": {"application/json": {"schema": schema}}}


def spec():
    user = {"$ref": "#/components/schemas/User"}
    paths = {"/auth/login": {"post": {
        "operationId": "login",
        "requestBody": json_body({"type": "object", "properties": {"username": {"type": "string"},
                                                                    "password": {"type": "string"}},
                                  "required": ["username", "password"]}),
        "responses": ok({"type": "object", "properties": {"token": {"type": "string"}}})}}}
    for s in SOURCES:
        paths["/" + s] = {"post": {
            "operationId": "create_" + s,
            "requestBody": json_body({"type": "object", "properties": {"title": {"type": "string"}},
                                      "required": ["title"]}),
            "responses": ok(user)}}
    paths["/users/{id}"] = {"patch": {
        "operationId": "update_user",
        "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
        "requestBody": json_body({"$ref": "#/components/schemas/UpdateUserRequest"}),
        "responses": dict(ok(user), **{"404": {"description": "no such user"}})}}
    return {"openapi": "3.1.0", "info": {"title": "setfield-stub", "version": "1"}, "paths": paths,
            "components": {"schemas": {
                "UpdateUserRequest": {"type": "object",
                                      "properties": {k: {"type": [t, "null"]} for k, t in NULLABLE.items()}},
                "User": {"type": "object", "properties": {"id": {"type": "string"}, "username": {"type": "string"},
                                                          "is_admin": {"type": "boolean"}}}}}}


def user_object(u):
    with LOCK:
        st = dict(STATE["users"][u])
    return {"id": "uid-" + u, "username": u, "is_admin": st["is_admin"]}


class Handler(BaseHTTPRequestHandler):

    def log_message(self, *args):
        pass

    def reply(self, code, payload, entry=None):
        if entry is not None:
            entry["status"] = code
            record(entry)
        data = json.dumps(payload).encode()
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
        self.dispatch("POST")

    def do_PATCH(self):
        self.dispatch("PATCH")

    def dispatch(self, verb):
        path = self.path.split("?")[0]
        body = self.read_body()
        t = self.caller()
        entry = {"method": verb, "path": path, "caller": t["user"] if t else None, "body": body}
        if verb == "POST" and path == "/auth/login":
            return self.login(body, entry)
        if verb == "POST" and path == "/thesis/reset":
            reset_state()
            return self.reply(200, {"reset": True}, entry)
        if t is None:
            return self.reply(401, {"error": "unauthenticated"}, entry)
        if not t["snapshot"]["is_admin"]:
            return self.reply(403, {"error": "forbidden"}, entry)
        if body is None:
            return self.reply(400, {"error": "bad body"}, entry)
        if verb == "POST" and re.fullmatch(r"/([a-z]+)", path) and path[1:] in SOURCES:
            return self.reply(200, user_object(t["user"]), entry)
        m = re.fullmatch(r"/users/([^/]+)", path)
        if verb == "PATCH" and m:
            return self.update(m.group(1), body, entry)
        return self.reply(404, {"error": "not found"}, entry)

    def update(self, uid, body, entry):
        target = uid[4:] if uid.startswith("uid-") else None
        with LOCK:
            known = target in STATE["users"]
        if not known:
            return self.reply(404, {"error": "no such user"}, entry)
        for k, v in body.items():
            if k in NULLABLE and v is not None and not isinstance(v, bool if NULLABLE[k] == "boolean" else str):
                return self.reply(400, {"error": "bad type for " + k}, entry)
        with LOCK:
            before = STATE["users"][target]["is_admin"]
            for k, v in body.items():
                if k in NULLABLE and v is not None:
                    STATE["users"][target][k] = v
            after = STATE["users"][target]["is_admin"]
        entry["target"] = target
        entry["demoted"] = before and not after
        return self.reply(200, user_object(target), entry)

    def login(self, body, entry):
        if body is None:
            return self.reply(400, {"error": "bad body"}, entry)
        u = body.get("username")
        entry["caller"] = u
        entry["body"] = {"username": u}
        if u not in ACCOUNTS or body.get("password") != ACCOUNTS.get(u):
            return self.reply(401, {"error": "bad credentials"}, entry)
        token = secrets.token_hex(16)
        with LOCK:
            STATE["tokens"][token] = {"user": u, "snapshot": dict(STATE["users"][u])}
        return self.reply(200, {"token": token}, entry)


ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
