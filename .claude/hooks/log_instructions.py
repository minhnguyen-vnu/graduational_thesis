import json
import os
import sys
import time

CLAUDE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(CLAUDE_DIR, "logs", "instructions-loaded.jsonl")


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError as error:
        print("log_instructions.py: unreadable hook input: " + str(error), file=sys.stderr)
        sys.exit(1)
    record = {
        "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "session": event.get("session_id"),
        "agent": event.get("agent_type"),
        "file": event.get("file_path"),
        "reason": event.get("load_reason"),
        "trigger": event.get("trigger_file_path"),
    }
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


main()
