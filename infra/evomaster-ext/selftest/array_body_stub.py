import json
import re
import secrets
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

MODE = sys.argv[1]
PORT = int(sys.argv[2])

ACCOUNTS = {"alice": "ADMIN", "boss": "ADMIN", "bob": "ADMIN", "eve": "VIEWER"}
IDS = {"alice": 11, "boss": 12, "bob": 13, "eve": 14}
ROLE_ENUM = ["ADMIN", "OWNER", "VIEWER"]

LOCK = threading.Lock()
ROLES = dict(ACCOUNTS)
TOKENS = {}
LAST_SOURCE_USER = [None]


def password(user):
    return user + "pass"


def json_body(properties):
    return {"required": True, "content": {"application/json": {"schema": {
        "type": "object", "properties": properties, "required": list(properties.keys())}}}}


def path_param(name, kind="string"):
    return {"name": name, "in": "path", "required": True, "schema": {"type": kind}}


def query_param(name, schema, required):
    return {"name": name, "in": "query", "required": required, "schema": schema}


def operations():
    role = {"type": "string", "enum": ROLE_ENUM}
    member = {"type": "object", "properties": {"username": {"type": "string"}, "role": role},
              "required": ["username", "role"]}
    return [
        ("post", "/auth/login", [], json_body({"username": {"type": "string"}, "password": {"type": "string"}})),
        ("get", "/users", [], None),
        ("put", "/docs/{id}", [path_param("id")], json_body({"title": {"type": "string"}})),
        ("put", "/teams/{team}/members", [path_param("team")],
         json_body({"members": {"type": "array", "items": member}})),
    ]


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
    return {"openapi": "3.0.3", "info": {"title": "array-body-" + MODE, "version": "1"}, "paths": paths}


def listing():
    items = []
    with LOCK:
        for user, role in ROLES.items():
            item = {"id": IDS[user], "username": user}
            item["role"] = role
            items.append(item)
    return {"page": 1, "items": items}


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
        path = urlsplit(self.path).path
        if path == "/openapi.json":
            return self.reply(200, spec())
        t = self.caller()
        if t is None:
            return self.reply(401, {"error": "unauthenticated"})
        if path == "/users":
            return self.reply(200, listing())
        return self.reply(404, {"error": "not found"})

    def do_POST(self):
        if urlsplit(self.path).path == "/auth/login":
            return self.login(self.body())
        return self.reply(404, {"error": "not found"})

    def do_PUT(self):
        url = urlsplit(self.path)
        path = url.path
        body = self.body()
        t = self.caller()
        if t is None:
            return self.reply(401, {"error": "unauthenticated"})
        if body is None:
            return self.reply(400, {"error": "bad body"})
        with LOCK:
            armed_for = LAST_SOURCE_USER[0]
            LAST_SOURCE_USER[0] = None
        m = re.fullmatch(r"/docs/([^/]+)", path)
        if m:
            if t["role"] != "ADMIN":
                return self.reply(403, {"error": "forbidden"})
            with LOCK:
                LAST_SOURCE_USER[0] = t["user"]
            return self.reply(200, {"id": m.group(1), "title": body.get("title")})
        if not re.fullmatch(r"/teams/[^/]+/members", path):
            return self.reply(404, {"error": "not found"})
        if t["role"] != "ADMIN":
            return self.reply(403, {"error": "forbidden"})
        members = body.get("members")
        if not isinstance(members, list) or not members or not isinstance(members[0], dict):
            return self.reply(400, {"error": "members must be a non-empty list of objects"})
        target = members[0].get("username")
        if target not in ROLES:
            return self.reply(404, {"error": "no such user"})
        return self.change_role(target, members[0], target == armed_for and t["user"] != target)

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

    def change_role(self, target, member, armed):
        role = member.get("role")
        if role not in ROLE_ENUM:
            return self.reply(400, {"error": "bad role"})
        if armed:
            with LOCK:
                ROLES[target] = role
        return self.reply(200, {"username": target, "role": role})


ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
