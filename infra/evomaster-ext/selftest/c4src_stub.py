import json
import re
import secrets
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

MODE = sys.argv[1]
PORT = int(sys.argv[2])
REQLOG = sys.argv[3]

ENUM = ["ADMIN", "VIEWER"]
ACCOUNTS = {"alice": "ADMIN", "boss": "ADMIN", "bob": "ADMIN", "eve": "VIEWER"}
SOURCE_ROLE = "ADMIN"
CHANGER_ROLES = {"ADMIN"}
UNARMED_CODE = 409 if MODE == "op-refused" else 200
if MODE == "op-refused":
    ENUM = ["OWNER", "ADMIN", "VIEWER"]
    ACCOUNTS = {"alice": "OWNER", "boss": "VIEWER", "bob": "ADMIN", "eve": "VIEWER"}
    SOURCE_ROLE = "OWNER"
    CHANGER_ROLES = {"OWNER", "ADMIN"}
if MODE == "value-reject":
    ENUM = ["ADMIN", "VIEWER", "GUEST"]

LOCK = threading.Lock()
ROLES = dict(ACCOUNTS)
TOKENS = {}
DOCS = set()
DRAFTS = set()
CHECKED_OUT = set()
WARMED = set()
REJECTED_ONCE = [False]
LAST_SOURCE_USER = [None]
COUNT = [0]


def json_body(properties):
    return {"required": True, "content": {"application/json": {"schema": {
        "type": "object", "properties": properties, "required": list(properties.keys())}}}}


def path_param(name):
    return {"name": name, "in": "path", "required": True, "schema": {"type": "string"}}


def operations():
    ops = [
        ("post", "/auth/login", [], json_body({"username": {"type": "string"}, "password": {"type": "string"}})),
        ("get", "/users", [], None),
        ("put", "/users/{username}/role", [path_param("username")],
         json_body({"role": {"type": "string", "enum": ENUM}})),
    ]
    if MODE in ("len1", "source-200", "op-refused", "value-reject", "prior-harmless"):
        ops.append(("put", "/docs/{id}", [path_param("id")], json_body({"title": {"type": "string"}})))
    if MODE == "prior-harmless":
        ops.append(("delete", "/docs/{id}", [path_param("id")], None))
    if MODE == "source-200":
        ops.append(("put", "/notes/{id}", [path_param("id")], json_body({"text": {"type": "string"}})))
    if MODE == "chain":
        ops.append(("post", "/docs", [], json_body({"title": {"type": "string"}})))
        ops.append(("put", "/docs/{id}", [path_param("id")], json_body({"title": {"type": "string"}})))
    if MODE == "prior-noncreate":
        ops.append(("post", "/checkout", [], json_body({"note": {"type": "string"}})))
        ops.append(("put", "/files/{id}", [path_param("id")], json_body({"name": {"type": "string"}})))
    if MODE == "anon-prefix":
        ops.append(("post", "/drafts", [], json_body({"title": {"type": "string"}})))
        ops.append(("put", "/drafts/{id}", [path_param("id")], json_body({"title": {"type": "string"}})))
    return ops


def spec():
    paths = {}
    for verb, path, params, body in operations():
        responses = {"200": {"description": "ok", "content": {"application/json": {"schema": {"type": "object"}}}}}
        if verb == "post" and path != "/auth/login":
            responses = {"201": {"description": "created", "content": {"application/json": {"schema": {
                "type": "object", "properties": {"id": {"type": "string"}}}}}}}
        op = {"operationId": verb + re.sub(r"[^A-Za-z0-9]", "_", path), "responses": responses}
        if params:
            op["parameters"] = params
        if body:
            op["requestBody"] = body
        paths.setdefault(path, {})[verb] = op
    return {"openapi": "3.0.3", "info": {"title": "c4src-" + MODE, "version": "1"}, "paths": paths}


def listing():
    with LOCK:
        return {"items": [{"username": u, "role": r} for u, r in ROLES.items()]}


class Handler(BaseHTTPRequestHandler):

    def log_message(self, *args):
        pass

    def reply(self, code, payload=None, record=None, location=None):
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
        if location is not None:
            self.send_header("Location", location)
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

    def token(self):
        h = self.headers.get("Authorization") or ""
        return h[7:] if h.startswith("Bearer ") else ""

    def caller(self):
        with LOCK:
            return TOKENS.get(self.token())

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == "/openapi.json":
            return self.reply(200, spec())
        t = self.caller()
        rec = {"m": "GET", "path": url.path, "caller": t["user"] if t else None, "armed": False}
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
        return self.write("POST", url.path)

    def do_DELETE(self):
        url = urlsplit(self.path)
        t = self.caller()
        rec = {"m": "DELETE", "path": url.path, "caller": t["user"] if t else None, "armed": False}
        with LOCK:
            LAST_SOURCE_USER[0] = None
        if t is None:
            return self.reply(401, {"error": "unauthenticated"}, rec)
        if MODE == "prior-harmless" and re.fullmatch(r"/docs/[^/]+", url.path):
            with LOCK:
                WARMED.add(self.token())
            return self.reply(404, {"error": "no such doc"}, rec)
        return self.reply(404, {"error": "not found"}, rec)

    def do_PUT(self):
        return self.write("PUT", urlsplit(self.path).path)

    def write(self, method, path):
        body = self.body()
        t = self.caller()
        rec = {"m": method, "path": path, "caller": t["user"] if t else None, "armed": False}
        with LOCK:
            armed_for = LAST_SOURCE_USER[0]
            LAST_SOURCE_USER[0] = None
        if method == "POST" and path == "/drafts" and t is None:
            return self.reply(400, {"error": "login required"}, rec)
        if t is None:
            return self.reply(401, {"error": "unauthenticated"}, rec)
        if body is None:
            return self.reply(400, {"error": "bad body"}, rec)
        if method == "POST" and path == "/docs":
            if t["role"] != "ADMIN":
                return self.reply(403, {"error": "admin role required"}, rec)
            new_id = "d" + secrets.token_hex(4)
            with LOCK:
                DOCS.add(new_id)
                LAST_SOURCE_USER[0] = t["user"]
            return self.reply(201, {"id": new_id}, rec, "/docs/" + new_id)
        if method == "PUT" and re.fullmatch(r"/docs/[^/]+", path):
            if t["role"] != SOURCE_ROLE:
                return self.reply(403, {"error": "admin role required"}, rec)
            doc = path.split("/")[-1]
            with LOCK:
                warmed = self.token() in WARMED
            if MODE == "prior-harmless" and not warmed:
                return self.reply(409, {"error": "send DELETE /docs/{id} first"}, rec)
            if MODE == "chain" and doc not in DOCS:
                return self.reply(404, {"error": "no such doc"}, rec)
            with LOCK:
                LAST_SOURCE_USER[0] = t["user"]
            return self.reply(200, {"id": doc, "title": body.get("title")}, rec)
        if method == "PUT" and re.fullmatch(r"/notes/[^/]+", path):
            if t["role"] != SOURCE_ROLE:
                return self.reply(403, {"error": "admin role required"}, rec)
            with LOCK:
                LAST_SOURCE_USER[0] = t["user"]
            return self.reply(200, {"id": path.split("/")[-1], "text": body.get("text")}, rec)
        if method == "POST" and path == "/checkout":
            if t["role"] != "ADMIN":
                return self.reply(403, {"error": "admin role required"}, rec)
            with LOCK:
                CHECKED_OUT.add(self.token())
            return self.reply(200, {"checked_out": True}, rec)
        if method == "PUT" and re.fullmatch(r"/files/[^/]+", path):
            with LOCK:
                ok = self.token() in CHECKED_OUT
            if not ok:
                return self.reply(403, {"error": "check out first"}, rec)
            with LOCK:
                LAST_SOURCE_USER[0] = t["user"]
            return self.reply(200, {"id": path.split("/")[-1], "name": body.get("name")}, rec)
        if method == "POST" and path == "/drafts":
            new_id = "r" + secrets.token_hex(4)
            with LOCK:
                DRAFTS.add(new_id)
            return self.reply(201, {"id": new_id}, rec, "/drafts/" + new_id)
        if method == "PUT" and re.fullmatch(r"/drafts/[^/]+", path):
            if t["role"] != "ADMIN":
                return self.reply(403, {"error": "admin role required"}, rec)
            draft = path.split("/")[-1]
            if draft not in DRAFTS:
                return self.reply(404, {"error": "no such draft"}, rec)
            with LOCK:
                LAST_SOURCE_USER[0] = t["user"]
            return self.reply(200, {"id": draft, "title": body.get("title")}, rec)
        m = re.fullmatch(r"/users/([^/]+)/role", path)
        if method != "PUT" or not m:
            return self.reply(404, {"error": "not found"}, rec)
        target = m.group(1)
        with LOCK:
            changer = ROLES[t["user"]]
        if changer not in CHANGER_ROLES:
            return self.reply(403, {"error": "admin role required"}, rec)
        if target not in ROLES:
            return self.reply(404, {"error": "no such user"}, rec)
        role = body.get("role")
        if role not in ENUM:
            return self.reply(400, {"error": "invalid role"}, rec)
        armed = target == armed_for and t["user"] != target
        rec["armed"] = armed
        if armed and MODE == "value-reject" and not REJECTED_ONCE[0]:
            REJECTED_ONCE[0] = True
            return self.reply(400, {"error": "invalid role"}, rec)
        if not armed and UNARMED_CODE != 200:
            return self.reply(UNARMED_CODE, {"error": "role change needs a fresh source call by the target"}, rec)
        if armed and MODE != "source-200":
            with LOCK:
                ROLES[target] = role
        return self.reply(200, {"username": target, "role": role}, rec)

    def login(self, body):
        if body is None:
            return self.reply(400, {"error": "bad body"})
        u = body.get("username")
        if not isinstance(u, str) or u not in ACCOUNTS or body.get("password") != u + "pass":
            return self.reply(401, {"error": "bad credentials"})
        token = secrets.token_hex(16)
        with LOCK:
            TOKENS[token] = {"user": u, "role": ROLES[u]}
        return self.reply(200, {"token": token})


ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
