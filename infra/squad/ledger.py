import json
import sys

try:
    with open(sys.argv[1], encoding="utf-8", errors="replace") as handle:
        data = json.load(handle)
except Exception:
    print("unparsed log,,,")
    sys.exit(0)

if not isinstance(data, dict):
    print("unexpected log shape,,,")
    sys.exit(0)

subtype = str(data.get("subtype", ""))
reason = "ok"
if data.get("is_error"):
    reason = "error"
if subtype and subtype != "success":
    reason = subtype.replace(",", " ")

fields = [reason, data.get("total_cost_usd", ""), data.get("num_turns", ""), data.get("session_id", "")]
print(",".join(str(value) for value in fields))
