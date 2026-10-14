import json
import os
import re
import subprocess
import sys
from collections import Counter

THESIS = "/Users/minhnguyen/IdeaProjects/graduational-thesis"
EVOMASTER = "/Users/minhnguyen/IdeaProjects/EvoMaster"
RESULTS = THESIS + "/infra/em-results/"
PROTECTED_FRAGMENTS = ("infra/em-results", "thesis-backups")
DATA_EXTENSIONS = (".csv", ".log", ".out", ".json")
COMMENT_STYLES = {".kt": "slash", ".kts": "slash", ".java": "slash", ".py": "hash", ".sh": "hash"}
PROVENANCE_MARKER = "THESIS"

HEAVY = re.compile(
    r"\bmvn\b(?!\s+(-v|-version|--version)\b)"
    r"|\bdocker\s+(build|compose\s+up)\b"
    r"|-jar\s+\S*evomaster\S*\.jar"
    r"|em-venv/bin/evomaster\b"
    r"|\bpytest\b"
    r"|(em-results|pyload-cve)/\S+\.sh\b"
)
RUNNING = re.compile(r"java\b.*evomaster\S*\.jar|(em-results|pyload-cve)/\S+\.sh\b")
JOB_EXECUTABLES = {"java", "bash", "sh", "zsh"}
TOOL_WRAPPER_MARK = "shell-snapshots"
REMOVE = re.compile(r"(^|\s)(rm|rmdir|unlink|trash)(\s|$)")
SEGMENT_SPLIT = re.compile(r"&&|\|\||;|\||\n")
OVERWRITE_TARGET = re.compile(r"(?<![>&0-9])>(?![>&])\s*([^\s;&|()]+)")


def deny(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def running_jobs():
    listing = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, text=True, check=True).stdout
    own = {os.getpid(), os.getppid()}
    jobs = []
    for line in listing.splitlines():
        pid, _, command = line.strip().partition(" ")
        command = command.strip()
        executable = os.path.basename(command.split(" ", 1)[0]) if command else ""
        if (pid.isdigit() and int(pid) not in own and executable in JOB_EXECUTABLES
                and TOOL_WRAPPER_MARK not in command and RUNNING.search(command)):
            jobs.append(pid + " " + command[:120])
    return jobs


def resolve(path, cwd):
    expanded = os.path.expanduser(path.strip("'\""))
    return os.path.normpath(expanded if os.path.isabs(expanded) else os.path.join(cwd, expanded))


def is_recorded_data(path):
    return path.startswith(RESULTS) and path.endswith(DATA_EXTENSIONS) and os.path.exists(path)


def check_bash(command, cwd):
    if HEAVY.search(command):
        jobs = running_jobs()
        if jobs:
            deny("A measurement batch is running (" + "; ".join(jobs[:2]) + "). mvn, docker build, pytest, "
                 "EvoMaster runs and harness scripts wait until it finishes: --maxTime is wall-clock.")
    for segment in SEGMENT_SPLIT.split(command):
        if REMOVE.search(segment) and any(fragment in segment for fragment in PROTECTED_FRAGMENTS):
            deny("Measurement data and backups are never deleted by the agent (infra/em-results, "
                 "~/thesis-backups). Write new results to a new folder; the user deletes by hand if needed.")
        for target in OVERWRITE_TARGET.findall(segment):
            if is_recorded_data(resolve(target, cwd)):
                deny("Redirect would overwrite recorded data: " + target + ". Write to a new file.")


def comment_lines(text, style):
    found = []
    for line in text.splitlines():
        stripped = line.strip()
        if PROVENANCE_MARKER in stripped:
            continue
        if style == "slash":
            full = stripped.startswith(("//", "/*", "*"))
            trailing = " //" in line and line[:line.index(" //")].count('"') % 2 == 0
        else:
            full = (stripped.startswith("#") and not stripped.startswith("#!")) or stripped.startswith(('"""', "'''"))
            trailing = " # " in line and line[:line.index(" # ")].count('"') % 2 == 0 and line[:line.index(" # ")].count("'") % 2 == 0
        if full or trailing:
            found.append(stripped)
    return Counter(found)


def check_file_tool(tool, tool_input):
    path = tool_input.get("file_path", "")
    if is_recorded_data(path):
        deny("Recorded measurement data is never edited: " + path + ". Write a new file instead.")
    style = COMMENT_STYLES.get(os.path.splitext(path)[1])
    if not style or not path.startswith((THESIS + "/", EVOMASTER + "/")):
        return
    if tool == "Write":
        before = open(path, encoding="utf-8", errors="replace").read() if os.path.exists(path) else ""
        pairs = [(before, tool_input.get("content", ""))]
    elif tool == "Edit":
        pairs = [(tool_input.get("old_string", ""), tool_input.get("new_string", ""))]
    else:
        pairs = [(edit.get("old_string", ""), edit.get("new_string", "")) for edit in tool_input.get("edits", [])]
    added = Counter()
    for old, new in pairs:
        added += comment_lines(new, style) - comment_lines(old, style)
    if added:
        deny("Code we add carries no comments (CLAUDE.md). New comment lines in " + path + ": "
             + " | ".join(list(added)[:3]))


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError as error:
        print("guard.py: unreadable hook input: " + str(error), file=sys.stderr)
        sys.exit(1)
    tool = event.get("tool_name", "")
    tool_input = event.get("tool_input", {}) or {}
    if tool == "Bash":
        check_bash(tool_input.get("command", ""), event.get("cwd", THESIS))
    elif tool in ("Write", "Edit", "MultiEdit"):
        check_file_tool(tool, tool_input)


main()
