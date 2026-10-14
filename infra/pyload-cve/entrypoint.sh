#!/bin/sh
# pyLoad has no --host/--port CLI flags: the WebUI binds to whatever webui.host says in the
# generated config (default "localhost", which is unreachable from outside the container).
# So: let a dry run generate the config, rewrite host to 0.0.0.0, seed the test accounts,
# then start for real.
#
# Nothing here changes application logic -- it is bind-address plumbing plus test fixtures.
set -e

USERDIR=/data
CFG="$USERDIR/settings/pyload.cfg"
DB="$USERDIR/data/pyload.db"

mkdir -p "$USERDIR"

if [ ! -f "$CFG" ]; then
    echo "[entrypoint] generating initial config..."
    pyload --userdir "$USERDIR" --storagedir "$USERDIR/downloads" --dry-run || true
fi

if [ -f "$CFG" ]; then
    # Rewrite "ip host" to 0.0.0.0 -- but ONLY inside the [webui] section.
    # The file also has an "ip host" under [proxy] and an "ip syslog_host"
    # under [log], and it is tab-indented, so do it section-aware in Python.
    python - "$CFG" <<'PYEOF'
import re, sys
path = sys.argv[1]
out, section = [], None
for line in open(path, encoding="utf-8").read().splitlines(keepends=True):
    if re.match(r'^\S', line):                       # section header
        section = line.split("-", 1)[0].strip()
    elif section == "webui" and re.match(r'^\s*ip host\s*:', line):
        line = re.sub(r'=.*$', '= 0.0.0.0', line.rstrip("\n")) + "\n"
    out.append(line)
open(path, "w", encoding="utf-8").write("".join(out))
PYEOF
    echo "[entrypoint] host lines now:"
    grep -n "ip host" "$CFG" || true
else
    echo "[entrypoint] WARNING: no config at $CFG"
fi

# Seed the victim/operator admin accounts the MR-A1 triple needs.
python /seed_users.py "$DB"

echo "[entrypoint] variant: version=$PYLOAD_VARIANT_VERSION stateful_role_check=$PYLOAD_STATEFUL_ROLE_CHECK"

exec pyload --userdir "$USERDIR" --storagedir "$USERDIR/downloads" --debug
