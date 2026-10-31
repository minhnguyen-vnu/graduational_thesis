import fcntl, json, os, re, sys, time

STATE = os.environ["FAKE_STATE"]
SYSTEM_ENV = "CLAUDE_CODE_SESSION_ID" in os.environ


def bump():
    with open(os.path.join(STATE, "counter"), "a+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.seek(0)
        n = int(fh.read() or 0) + 1
        fh.seek(0)
        fh.truncate()
        fh.write(str(n))
    return n


def emit(obj):
    print(json.dumps(obj))


def allowed():
    emit({"type": "rate_limit_event", "rate_limit_info": {"status": "allowed", "resetsAt": int(time.time()) + 900,
          "unifiedWindows": {"five_hour": {"utilization": 0.3, "status": "allowed"},
                             "seven_day": {"utilization": 0.1, "status": "allowed"}}}})


def good_csv(ids, drop=0):
    keep = ids[:-drop] if drop else ids
    lines = ["row_id,A,B,C,U,victim,role,order"]
    lines += ["%s,none,other,unclear,0,,," % i for i in keep]
    return "\n".join(lines)


def main():
    text = sys.stdin.read()
    ids = re.findall(r"^## (\S+)", text, re.M)
    n = bump()
    model = sys.argv[sys.argv.index("--model") + 1]
    with open(os.path.join(STATE, "calls.log"), "a") as fh:
        fh.write("%.3f %d %s %s %s %s %s %s\n" % (time.time(), n, model, ids[0], int("--safe-mode" in sys.argv),
                                                  sys.argv[sys.argv.index("--tools") + 1] == "", int(SYSTEM_ENV),
                                                  os.environ.get("DISABLE_PROMPT_CACHING", "0")))
    time.sleep(0.15)
    if n == 5:
        reset = time.time() + 4
        with open(os.path.join(STATE, "limit-window"), "w") as fh:
            fh.write("%.3f %.3f" % (time.time(), reset))
        emit({"type": "rate_limit_event", "rate_limit_info": {"status": "rejected", "resetsAt": int(reset) + 1,
              "rateLimitType": "five_hour", "unifiedWindows": {"five_hour": {"utilization": 1.0, "status": "rejected",
              "resetsAt": int(reset) + 1}, "seven_day": {"utilization": 0.1, "status": "allowed"}}}})
        emit({"type": "result", "subtype": "error", "is_error": True,
              "result": "You've hit your session limit · resets 3am (Asia/Saigon)"})
        return 1
    if n == 11:
        return 1
    if n == 14:
        allowed()
        emit({"type": "result", "subtype": "success", "is_error": False, "result": good_csv(ids, drop=1),
              "usage": {"input_tokens": 1, "output_tokens": 1}, "total_cost_usd": 0})
        return 0
    if n == 17:
        emit({"type": "assistant", "message": {"content": [{"type": "text", "text": "You've hit your session limit"}]}})
        emit({"type": "result", "subtype": "error", "is_error": True, "result": ""})
        return 1
    if "BADBLOCK" in text:
        allowed()
        emit({"type": "result", "subtype": "success", "is_error": False, "result": "khong phai csv",
              "usage": {}, "total_cost_usd": 0})
        return 0
    allowed()
    emit({"type": "result", "subtype": "success", "is_error": False, "result": good_csv(ids),
          "usage": {"input_tokens": 1, "output_tokens": 1}, "total_cost_usd": 0})
    return 0


sys.exit(main())
