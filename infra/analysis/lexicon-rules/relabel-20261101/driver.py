import csv, io, json, os, re, subprocess, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("RELABEL_WORK", HERE)
CLAUDE = os.environ.get("RELABEL_CLAUDE", "claude")
SCALE = float(os.environ.get("RELABEL_SCALE", "1"))
LANES = {"A": ("claude-sonnet-5-5", "high"), "B": ("claude-opus-5-5", "medium")}
A_CODES = {"existing", "self", "new", "group", "nonuser", "none"}
B_CODES = {"role_set", "role_remove", "perm", "admin_flag", "member_role", "member_remove", "disable",
           "delete_account", "role_def", "credential", "resource_acl", "other"}
C_CODES = {"down", "up", "unclear"}
COLUMNS = ["row_id", "A", "B", "C", "U", "victim", "role", "order"]
LIMIT_TEXT = re.compile(r"session limit|usage limit|weekly limit|rate limit|hit your", re.I)
MARGIN = 120 * SCALE
POLL = 300 * SCALE
TIMEOUT = 1200
MAX_CONTENT_ATTEMPTS = 5
PASSES = 2
DROP_ENV = ("CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_MESSAGING_SOCKET", "CLAUDE_CODE_MESSAGING_TOKEN",
            "CLAUDE_CODE_CHILD_SESSION", "CLAUDE_CODE_SESSION_ATTENDED", "CLAUDE_CODE_ENTRYPOINT",
            "CLAUDE_CODE_EXECPATH")

lock = threading.Lock()
pause_until = 0.0
state = {"note": "", "five_hour": "", "seven_day": "", "failed": {}}
started = time.time()


def log(msg):
    with lock:
        with open(os.path.join(WORK, "run.log"), "a") as fh:
            fh.write("%s %s\n" % (time.strftime("%F %T"), msg))


def out_path(lane, stage, name):
    return os.path.join(WORK, lane, stage, name + ".csv")


def validate(text, ids):
    body = "\n".join(l for l in text.strip().splitlines() if not l.startswith("```"))
    at = body.find("row_id,")
    if at < 0:
        raise ValueError("khong co header")
    rows = list(csv.DictReader(io.StringIO(body[at:])))
    if not rows or [c.strip() for c in (rows[0].keys())][:8] != COLUMNS:
        raise ValueError("sai cot")
    got = {}
    for r in rows:
        rid = (r.get("row_id") or "").strip()
        if rid not in ids:
            raise ValueError("ma dong la")
        if rid in got:
            raise ValueError("trung dong")
        clean = {c: (r.get(c) or "").strip() for c in COLUMNS}
        if clean["A"] not in A_CODES or clean["B"] not in B_CODES or clean["C"] not in C_CODES or clean["U"] not in ("0", "1"):
            raise ValueError("ma sai")
        got[rid] = clean
    if len(got) != len(ids):
        raise ValueError("thieu %d dong" % (len(ids) - len(got)))
    return [got[i] for i in sorted(got)]


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", newline="") as fh:
        w = csv.DictWriter(fh, COLUMNS)
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)


def is_done(path, ids):
    if not os.path.exists(path):
        return False
    with open(path, newline="") as fh:
        return {r["row_id"] for r in csv.DictReader(fh)} == set(ids)


def call(lane, text, system, env, cwd):
    model, effort = LANES[lane]
    cmd = [CLAUDE, "-p", "--safe-mode", "--no-session-persistence", "--tools", "", "--system-prompt", system,
           "--model", model, "--effort", effort, "--output-format", "stream-json", "--verbose"]
    try:
        p = subprocess.run(cmd, input=text, capture_output=True, text=True, timeout=TIMEOUT, env=env, cwd=cwd)
    except subprocess.TimeoutExpired:
        return {"kind": "transport", "note": "timeout"}
    info, result, seen = None, None, [p.stderr or ""]
    for line in p.stdout.splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            seen.append(line)
            continue
        if d.get("type") == "rate_limit_event":
            info = d.get("rate_limit_info") or info
        elif d.get("type") == "result":
            result = d
            seen.append(str(d.get("result") or ""))
        elif d.get("type") == "assistant":
            for b in (d.get("message") or {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "text":
                    seen.append(b.get("text") or "")
    out = {"info": info, "result": result}
    rejected = False
    resets = None
    if info:
        windows = info.get("unifiedWindows") or {}
        for name in ("five_hour", "seven_day"):
            if name in windows:
                state[name] = windows[name].get("utilization", "")
        if info.get("status") == "rejected":
            rejected, resets = True, info.get("resetsAt")
        for w in windows.values():
            if w.get("status") == "rejected":
                rejected = True
                resets = max(resets or 0, w.get("resetsAt") or 0)
    if result and not result.get("is_error") and result.get("result"):
        out["kind"] = "ok"
        out["text"] = result["result"]
        return out
    if rejected or LIMIT_TEXT.search("\n".join(seen)):
        out["kind"] = "limit"
        out["resets"] = resets
        return out
    out["kind"] = "transport"
    out["note"] = "exit %s, %s" % (p.returncode, "co result" if result else "khong result")
    return out


def wait_pause():
    while True:
        with lock:
            left = pause_until - time.time()
        if left <= 0:
            return
        time.sleep(min(left, 30 * SCALE))


def set_pause(lane, resets):
    global pause_until
    now = time.time()
    target = resets + MARGIN if resets and resets + MARGIN > now else now + POLL
    with lock:
        pause_until = max(pause_until, target)
        state["note"] = "het han muc, cho toi " + time.strftime("%F %T", time.localtime(pause_until))
    log("%s LIMIT, cho toi %s" % (lane, time.strftime("%F %T", time.localtime(target))))


def record_usage(lane, stage, name, secs, res):
    r = res.get("result") or {}
    u = r.get("usage") or {}
    line = [time.strftime("%F %T"), lane, stage, name, round(secs, 1), u.get("input_tokens", ""),
            u.get("cache_creation_input_tokens", ""), u.get("cache_read_input_tokens", ""), u.get("output_tokens", ""),
            (u.get("output_tokens_details") or {}).get("thinking_tokens", ""), r.get("total_cost_usd", ""),
            state["five_hour"], state["seven_day"]]
    with lock:
        with open(os.path.join(WORK, "usage.csv"), "a") as fh:
            fh.write(",".join(str(x) for x in line) + "\n")


def write_status(queue, manifest):
    rows = []
    for lane in LANES:
        for stage in manifest:
            names = [n for s, n in queue if s == stage]
            done = sum(1 for n in names if os.path.exists(out_path(lane, stage, n)))
            rows.append("| %s | %s | %d/%d |" % (lane, stage, done, len(names)))
    text = ["# Trang thai gan nhan", "", "Cap nhat: " + time.strftime("%F %T"),
            "Quota 5 gio: %s, quota tuan: %s" % (state["five_hour"], state["seven_day"]),
            "Ghi chu: " + state["note"], "", "| Luot | Phan | Xong |", "|---|---|---|"] + rows
    if state["failed"]:
        text += ["", "Khoi hong: " + ", ".join(sorted(state["failed"]))]
    tmp = os.path.join(WORK, "STATUS.md.tmp")
    with lock:
        with open(tmp, "w") as fh:
            fh.write("\n".join(text) + "\n")
        os.replace(tmp, os.path.join(WORK, "STATUS.md"))


def run_block(lane, stage, name, ids, system, env, cwd, queue, manifest):
    path = out_path(lane, stage, name)
    with open(os.path.join(WORK, "blocks", stage, name + ".txt")) as fh:
        text = fh.read()
    bad = 0
    while True:
        wait_pause()
        t0 = time.time()
        res = call(lane, text, system, env, cwd)
        if res["kind"] == "limit":
            set_pause(lane, res.get("resets"))
            continue
        if res["kind"] == "transport":
            log("%s %s/%s loi truyen: %s" % (lane, stage, name, res["note"]))
            time.sleep(POLL)
            continue
        try:
            rows = validate(res["text"], set(ids))
        except ValueError as e:
            bad += 1
            log("%s %s/%s dau ra sai lan %d: %s" % (lane, stage, name, bad, e))
            if bad >= MAX_CONTENT_ATTEMPTS:
                state["failed"]["%s/%s/%s" % (lane, stage, name)] = str(e)
                return False
            continue
        write_csv(path, rows)
        record_usage(lane, stage, name, time.time() - t0, res)
        state["note"] = ""
        state["failed"].pop("%s/%s/%s" % (lane, stage, name), None)
        write_status(queue, manifest)
        return True


def run_lane(lane, queue, manifest, system, env, cwd):
    for n in range(PASSES):
        for stage, name in queue:
            ids = manifest[stage][name]
            if not is_done(out_path(lane, stage, name), ids):
                run_block(lane, stage, name, ids, system, env, cwd, queue, manifest)
    log("%s xong hang doi" % lane)


def build_queue(manifest, only):
    train = [("train", n) for n in sorted(manifest["train"])]
    if only == "smoke":
        return train[:5]
    known = [("known", n) for n in sorted(manifest.get("known", {}))]
    test = [("test", n) for n in sorted(manifest.get("test", {}))]
    return train[:5] + known + test + train[5:]


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else "all"
    manifest = json.load(open(os.path.join(WORK, "manifest.json")))
    guide = open(os.path.join(WORK, "GUIDE.md")).read()
    system = guide + ("\n\nĐầu ra: chỉ in CSV, header `row_id,A,B,C,U,victim,role,order`, một dòng cho mọi operation trong "
                      "khối, không thêm chữ nào khác. Giá trị có dấu phẩy đặt trong ngoặc kép.")
    env = {k: v for k, v in os.environ.items() if k not in DROP_ENV}
    cwd = os.path.join(WORK, "empty-cwd")
    os.makedirs(cwd, exist_ok=True)
    queue = build_queue(manifest, only)
    log("BAT DAU %s, %d khoi moi luot" % (only, len(queue)))
    threads = [threading.Thread(target=run_lane, args=(lane, queue, manifest, system, env, cwd)) for lane in LANES]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    write_status(queue, manifest)
    log("KET THUC %s, khoi hong %d" % (only, len(state["failed"])))


main()
