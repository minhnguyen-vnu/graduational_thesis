import re

SUBJECT = {
    "user", "account", "member", "membership", "principal", "subject", "identity",
    "serviceaccount", "collaborator", "participant", "assignee", "invite", "invitation",
    "guest", "employee", "staff", "person", "people", "group", "team", "org",
    "organization", "tenant", "login", "profile", "actor",
}

PERMISSION = {
    "role", "permission", "privilege", "grant", "scope", "entitlement", "acl",
    "policy", "right", "admin", "administrator", "owner", "ownership", "access",
    "active", "enabled", "disabled", "locked", "suspended", "blocked", "banned",
    "revoke", "deassign", "unassign", "deactivate", "disable", "suspend", "lock",
    "ban", "status", "authorization", "authority", "capability", "claim",
}

FIELDS = (2, 3, 4, 5, 6, 7, 8)

_split = re.compile(r"[^a-z0-9]+")


def tokens(row):
    out = set()
    for i in FIELDS:
        if i >= len(row):
            continue
        for w in _split.split(row[i].lower()):
            if not w:
                continue
            out.add(w)
            for suf in ("ies", "es", "s"):
                if len(w) > 3 and w.endswith(suf):
                    out.add(w[: -len(suf)] + ("y" if suf == "ies" else ""))
    return out


def classes(row):
    t = tokens(row)
    return bool(t & SUBJECT), bool(t & PERMISSION)
