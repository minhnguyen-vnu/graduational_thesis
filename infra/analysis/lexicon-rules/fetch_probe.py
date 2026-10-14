import sys
import urllib.request
import urllib.error

UA = {"User-Agent": "Mozilla/5.0"}


def probe(url, out=None):
    try:
        req = urllib.request.Request(url, headers=UA)
        r = urllib.request.urlopen(req, timeout=40)
        d = r.read()
        print(url, "->", r.status, len(d), d[:8])
        if out:
            open(out, "wb").write(d)
        return d
    except urllib.error.HTTPError as e:
        print(url, "-> HTTPError", e.code, e.reason)
    except Exception as e:
        print(url, "->", type(e).__name__, e)
    return None


if __name__ == "__main__":
    out = sys.argv[2] if len(sys.argv) > 2 else None
    probe(sys.argv[1], out)
