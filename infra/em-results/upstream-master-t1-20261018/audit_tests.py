import glob
import os
import re
import sys

ADMIN_ONLY = re.compile(r"^/(reports(/.*)?|users/[^/]+/role)$")
TEST = re.compile(r"\n    def (test_\w+)\(self\):")


def calls_of(body):
    out = []
    blocks = re.split(r"\n        headers = \{\}\n", body)
    for i, b in enumerate(blocks[1:], start=1):
        prev = blocks[i - 1]
        last_assert = prev.rfind("assert ")
        tail = prev[prev.find("\n", last_assert) if last_assert >= 0 else 0:]
        m = re.search(r"requests\s*\\?\s*\.(get|post|put|delete|patch)\(", b)
        if not m:
            continue
        u = re.search(r'self\.baseUrlOfSut \+ (?:str\()?"([^"]*)"', b)
        path = u.group(1) if u else "?"
        if path.startswith("/auth/login"):
            continue
        a = re.search(r'headers\["Authorization"\] = auth_(\w+)', b)
        role = re.search(r'\\"role\\" : \\"(\w+)\\"', b)
        st = re.search(r"assert res_\d+\.status_code == (\d+)", b)
        fault = re.findall(r"# Fault(\d+)\.", tail)
        out.append({"method": m.group(1).upper(), "path": path, "user": a.group(1) if a else None,
                    "role": role.group(1) if role else None, "status": int(st.group(1)) if st else None,
                    "faults": fault})
    return out


def audit_file(f):
    src = open(f, encoding="utf-8", errors="replace").read()
    heads = list(TEST.finditer(src))
    res = []
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(src)
        cs = calls_of(src[h.start():end])
        role_calls = [k for k, c in enumerate(cs) if c["method"] == "PUT" and re.match(r"^/users/[^/]+/role$", c["path"])]
        hits = []
        for d in role_calls:
            c = cs[d]
            if c["role"] != "VIEWER" or c["status"] is None or not 200 <= c["status"] < 300:
                continue
            victim = c["path"].split("/")[2]
            for k in range(d + 1, len(cs)):
                f2 = cs[k]
                if f2["user"] == victim and f2["method"] in ("POST", "PUT", "DELETE", "PATCH") and ADMIN_ONLY.match(f2["path"]):
                    src_ok = any(cs[j]["user"] == victim and cs[j]["method"] in ("POST", "PUT", "DELETE", "PATCH")
                                 and ADMIN_ONLY.match(cs[j]["path"]) and cs[j]["status"] and 200 <= cs[j]["status"] < 300
                                 for j in range(d))
                    hits.append({"demotion_call": d + 1, "victim": victim, "followup_call": k + 1,
                                 "followup": f"{f2['method']} {f2['path']}", "status": f2["status"],
                                 "source_2xx_before": src_ok, "faults_on_followup": f2["faults"]})
        res.append({"test": h.group(1), "calls": len(cs), "role_calls": len(role_calls), "hits": hits,
                    "faults": sorted({x for c in cs for x in c["faults"]})})
    return res


def main(dirs):
    print("run\ttests\ttests_with_role_call\tdemote_then_reuse\treuse_2xx\treuse_2xx_with_source\tfault_codes_on_reuse")
    for d in dirs:
        files = sorted(glob.glob(os.path.join(d, "EvoMaster_*_Test.py")))
        tests = [t for f in files for t in audit_file(f)]
        hits = [(t["test"], h) for t in tests for h in t["hits"]]
        ok = [x for x in hits if x[1]["status"] and 200 <= x[1]["status"] < 300]
        print("\t".join(str(v) for v in [os.path.basename(d.rstrip("/")), len(tests), sum(1 for t in tests if t["role_calls"]),
                                          len(hits), len(ok), sum(1 for x in ok if x[1]["source_2xx_before"]),
                                          "|".join(sorted({c for _, h in hits for c in h["faults_on_followup"]})) or "-"]))
        for name, h in hits:
            print(f"#  {os.path.basename(d.rstrip('/'))} {name} {h}")


if __name__ == "__main__":
    main(sys.argv[1:])
