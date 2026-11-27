import base64
import http.client
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LISTEN = int(sys.argv[1])
TARGET = int(sys.argv[2])
LOG = open(sys.argv[3], "w", buffering=1)
LOCK = threading.Lock()
SEQ = [0]
T0 = time.time()
HOP = {"transfer-encoding", "connection", "content-length", "server", "date", "keep-alive"}


def claims(auth):
    if not auth or not auth.startswith("Bearer "):
        return "-"
    tok = auth[7:]
    try:
        p = tok.split(".")[1]
        p += "=" * (-len(p) % 4)
        c = json.loads(base64.urlsafe_b64decode(p))
        return "%s[%s]..%s" % (c.get("sub"), c.get("role"), tok[-6:])
    except Exception:
        return "?.." + tok[-6:]


def short(b, n=160):
    s = b.decode("utf-8", "replace").replace("\n", " ")
    return s if len(s) <= n else s[:n] + "..."


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def read_body(self):
        n = self.headers.get("Content-Length")
        if n:
            return self.rfile.read(int(n))
        if self.headers.get("Transfer-Encoding", "").lower() == "chunked":
            out = b""
            while True:
                size = int(self.rfile.readline().strip(), 16)
                if size == 0:
                    self.rfile.readline()
                    return out
                out += self.rfile.read(size)
                self.rfile.readline()
        return b""

    def handle_any(self):
        body = self.read_body()
        if self.path.startswith("/__mark/"):
            with LOCK:
                LOG.write("=== MARK %s t=%.1fs\n" % (self.path[8:], time.time() - T0))
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP}
        c = http.client.HTTPConnection("localhost", TARGET, timeout=60)
        c.request(self.command, self.path, body=body if body else None, headers=headers)
        r = c.getresponse()
        data = r.read()
        rh = r.getheaders()
        c.close()
        who = claims(self.headers.get("Authorization"))
        if self.path == "/auth/login" and r.status == 200:
            try:
                who = "LOGIN->" + claims("Bearer " + json.loads(data)["token"])
            except Exception:
                pass
        with LOCK:
            SEQ[0] += 1
            LOG.write("%05d t=%6.1fs %-6s %-28s %-28s req=%s -> %d %s\n" % (
                SEQ[0], time.time() - T0, self.command, self.path, who,
                short(body), r.status, "" if self.path.startswith("/v3/api-docs") else short(data)))
        self.send_response(r.status)
        for k, v in rh:
            if k.lower() not in HOP:
                self.send_header(k, v)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = do_HEAD = do_OPTIONS = do_TRACE = handle_any


ThreadingHTTPServer(("localhost", LISTEN), H).serve_forever()
