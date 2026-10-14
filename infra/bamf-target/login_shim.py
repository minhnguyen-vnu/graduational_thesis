import base64
import hashlib
import json
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

API = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8110"


def call(path, data, content_type):
    req = urllib.request.Request(API + path, data=data, headers={"Content-Type": content_type}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        verifier = secrets.token_urlsafe(48)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        status, out = call(
            "/api/v1/auth/local/authorize",
            json.dumps({"email": body.get("email", ""), "password": body.get("password", ""),
                        "code_challenge": challenge, "code_challenge_method": "S256",
                        "state": secrets.token_urlsafe(16)}).encode(),
            "application/json",
        )
        if status == 200:
            form = urllib.parse.urlencode({"grant_type": "authorization_code",
                                           "code": json.loads(out)["code"], "code_verifier": verifier}).encode()
            status, out = call("/api/v1/auth/token", form, "application/x-www-form-urlencoded")
        if status == 200:
            out = json.dumps({"token": json.loads(out)["session_token"]}).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.log_date_time_string(), fmt % args))


ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), Handler).serve_forever()
