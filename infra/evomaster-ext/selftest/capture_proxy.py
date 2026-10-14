import gzip
import http.client
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LISTEN = int(sys.argv[1])
TARGET_HOST = sys.argv[2]
TARGET_PORT = int(sys.argv[3])
OUT = sys.argv[4]
LOCK = threading.Lock()
HOP = {"connection", "keep-alive", "transfer-encoding", "te", "trailer", "upgrade", "proxy-connection", "content-length", "host"}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def _forward(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n) if n else b""
        headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP}
        headers["Host"] = "%s:%d" % (TARGET_HOST, TARGET_PORT)
        conn = http.client.HTTPConnection(TARGET_HOST, TARGET_PORT, timeout=60)
        try:
            conn.request(self.command, self.path, body=body, headers=headers)
            resp = conn.getresponse()
            rbody = resp.read()
            status, rheaders = resp.status, resp.getheaders()
        except Exception as e:
            status, rheaders, rbody = 502, [], ("proxy error: %s" % e).encode()
        finally:
            conn.close()
        auth = self.headers.get("Authorization") or ""
        logged = rbody
        if any(k.lower() == "content-encoding" and "gzip" in v.lower() for k, v in rheaders):
            try:
                logged = gzip.decompress(rbody)
            except Exception:
                pass
        rec = {
            "t": time.strftime("%H:%M:%S"),
            "ts": time.time(),
            "method": self.command,
            "path": self.path,
            "auth_tail": auth[-12:],
            "req_body": body.decode("utf-8", "replace"),
            "status": status,
            "resp_body": logged[:2000].decode("utf-8", "replace"),
        }
        with LOCK:
            with open(OUT, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
        self.send_response(status)
        for k, v in rheaders:
            if k.lower() not in HOP:
                self.send_header(k, v)
        self.send_header("Content-Length", str(len(rbody)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(rbody)

    do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = do_HEAD = do_OPTIONS = _forward


ThreadingHTTPServer(("127.0.0.1", LISTEN), Handler).serve_forever()
