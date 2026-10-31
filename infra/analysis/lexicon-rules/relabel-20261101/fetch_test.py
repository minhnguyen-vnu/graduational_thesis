import glob, hashlib, json, os, random, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.normpath(os.path.join(HERE, "..", "..", "corpus"))
SPECS = os.path.join(HERE, "test-specs")
SEED = 20261101
SAME_COMPANY_AS_USED = {"ably.io", "bbc.co.uk"}
MERGE = {"apiz.ebay.com": "ebay.com", "google.home": "google.com", "googleapis.com": "google.com",
         "walletobjects.googleapis.com": "google.com"}


def pool():
    data = json.load(open(os.path.join(CORPUS, "apis-guru-list.json")))
    used = set()
    for f in sorted(glob.glob(os.path.join(CORPUS, "sample*.json"))):
        if "reserve" not in f:
            used |= {a["provider"] for a in json.load(open(f))}
    companies = {}
    for key, entry in data.items():
        v = entry["versions"][entry["preferred"]]
        provider = v["info"].get("x-providerName") or key.split(":")[0]
        if provider in used or provider in SAME_COMPANY_AS_USED:
            continue
        company = MERGE.get(provider, provider)
        companies.setdefault(company, []).append({
            "key": key, "provider": provider, "company": company,
            "categories": sorted(v["info"].get("x-apisguru-categories") or []),
            "swaggerUrl": v["swaggerUrl"]})
    return companies


def fetch(a):
    path = os.path.join(SPECS, a["spec_id"] + ".json")
    err = ""
    for attempt in range(4):
        try:
            url = urllib.parse.quote(a["swaggerUrl"], safe=":/?=&%~")
            req = urllib.request.Request(url, headers={"User-Agent": "curl/8.7.1"})
            with urllib.request.urlopen(req, timeout=90) as r:
                body = r.read()
            with open(path + ".tmp", "wb") as fh:
                fh.write(body)
            os.replace(path + ".tmp", path)
            return dict(a, status="ok", bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        except Exception as e:
            err = type(e).__name__
            time.sleep(3 * (attempt + 1))
    return dict(a, status="fail:" + err, bytes=0, sha256="")


def main():
    companies = pool()
    rng = random.Random(SEED)
    picks = []
    for company in sorted(companies):
        picks.append(rng.choice(sorted(companies[company], key=lambda a: a["key"])))
    for i, a in enumerate(picks, 1):
        a["spec_id"] = "E%03d" % i
    os.makedirs(SPECS, exist_ok=True)
    with ThreadPoolExecutor(8) as ex:
        out = list(ex.map(fetch, picks))
    json.dump(out, open(os.path.join(HERE, "test-specs.json"), "w"), indent=1, ensure_ascii=False)
    ok = [a for a in out if a["status"] == "ok"]
    print("cong ty", len(out), "tai duoc", len(ok), "tong MB", round(sum(a["bytes"] for a in ok) / 1e6, 1))
    print("hong", [(a["spec_id"], a["provider"], a["status"]) for a in out if a["status"] != "ok"])


main()
