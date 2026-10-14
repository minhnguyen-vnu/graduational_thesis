#!/usr/bin/env python3
"""
Patch an INSTALLED pyload-ng tree for the Tier-2b experiment (pyLoad CVE-2026-41133).

Two independent edits, selected by argv:

  patch_pyload.py <site-packages> csrf         -> always applied, BOTH variants
  patch_pyload.py <site-packages> rolecheck    -> applied to the FIXED variant only

Edit 1 (csrf) -- webui/app/config.py
    Adds WTF_CSRF_METHODS = [] to BaseConfig.

    Why: pyLoad calls flask_wtf's csrf.protect() MANUALLY (helpers.py, apikey_auth) and
    also relies on CSRFProtect's default before_request hook for /json/*. protect() does
    NOT honour WTF_CSRF_ENABLED -- that flag is only read inside the before_request hook
    (flask_wtf/csrf.py:233) -- but it DOES return early when the request method is absent
    from WTF_CSRF_METHODS (flask_wtf/csrf.py:282). CSRFProtect.init_app reads that key via
    config.get() (csrf.py:216-217), so a value loaded earlier by app.config.from_object()
    wins. An empty list therefore neutralises CSRF for every method.

    This touches the CSRF extension's configuration ONLY. It changes nothing about who is
    authorized: it removes an anti-forgery control that is orthogonal to the access-control
    bug under test, so that a non-browser client (the fuzzer) can reach the session-auth
    path at all. Applied identically to both variants, so it cannot affect the differential.

Edit 2 (rolecheck) -- webui/app/helpers.py, parse_permissions()
    Makes authorization re-read role/permission from the database instead of trusting the
    copy cached into the Flask session at login time.

    This is the CONTROL for the experiment, not a discovered upstream fix: upstream never
    fixed this (is_authenticated is byte-identical from 0.5.0b3.dev97 through dev101 and on
    develop, despite the advisory claiming a fix in dev98). The patch is not invented for
    the occasion either -- it applies to the session branch exactly the fresh-database read
    that the X-API-Key branch of apikey_auth() in this very file already performs.

Every edit asserts its anchor text is present exactly once and fails the build otherwise,
so a pyload version bump can never silently turn a patch into a no-op.
"""
import pathlib
import sys

CSRF_ANCHOR = """class BaseConfig:
    DEBUG = False
"""

CSRF_PATCHED = """class BaseConfig:
    # THESIS (Tier-2b): neutralise Flask-WTF CSRF so a non-browser client can reach the
    # session-authenticated paths. Orthogonal to authorization; applied to BOTH variants.
    WTF_CSRF_METHODS = []
    DEBUG = False
"""

ROLE_ANCHOR = """    perms["ANY"] = True
    if session.get("role") == Role.ADMIN:
        for key in perms.keys():
            perms[key] = True

    elif session.get("perms"):
        p = session.get("perms")
        perms.update(get_permission(p))
"""

ROLE_PATCHED = """    perms["ANY"] = True
    # THESIS CONTROL (fixed variant): re-read role/permission from the database rather than
    # trusting the copy cached in the session at login time. This mirrors what the X-API-Key
    # branch of apikey_auth() in this same file already does.
    _fresh_api = flask.current_app.config["PYLOAD_API"]
    _fresh = _fresh_api.pyload.db.get_all_user_data().get(session.get("id"))
    _fresh_role = _fresh["role"] if _fresh else None
    _fresh_perm = _fresh["permission"] if _fresh else 0
    if _fresh_role == Role.ADMIN:
        for key in perms.keys():
            perms[key] = True

    elif _fresh_perm:
        perms.update(get_permission(_fresh_perm))
"""

API_ANCHOR = """        s = flask.session
        if is_authenticated(s):
            user_info = {
                "id": s["id"],
                "name": s["name"],
                "role": s["role"],
                "permission": s["perms"],
            }
"""

API_PATCHED = """        s = flask.session
        if is_authenticated(s):
            # THESIS CONTROL (fixed variant): same fresh-database read as parse_permissions(), so
            # the control holds on EVERY authorization path rather than only the /json one. Without
            # this, /api/* would remain vulnerable in the "fixed" image and the differential would
            # depend on which surface a request happened to use.
            _fresh = api.pyload.db.get_all_user_data().get(s["id"])
            if not _fresh:
                return flask.json.jsonify({"error": "Invalid API credentials"}), 401
            user_info = {
                "id": s["id"],
                "name": _fresh["name"],
                "role": _fresh["role"],
                "permission": _fresh["permission"],
            }
"""

RESET_ANCHOR = '''bp = flask.Blueprint("json", __name__)
'''

RESET_PATCHED = '''bp = flask.Blueprint("json", __name__)


@bp.route("/thesis/reset", methods=["GET", "POST"], endpoint="thesis_reset")
def thesis_reset():
    """
    THESIS TEST FIXTURE -- present in BOTH variants, so it cancels out of the differential.

    Restores the account state the MR-A1 triple needs: the seeded administrators are put back to
    role ADMIN and the accounts the fuzzer created are removed. This is the analogue of
    reports-api's POST /reset and VAmPI's GET /createdb, which the two seeded targets expose and
    stock pyLoad does not -- without it the state-reset ablation cannot be run on this target at
    all, because --statefulAuthzResetEndpoint needs an HTTP endpoint.

    It writes only to the users table. It contains no authorization logic, and it is deliberately
    unauthenticated, exactly like the reset endpoints of the other two targets: a reset that
    required an admin session would be unusable precisely when it is needed, i.e. after the search
    has demoted every administrator.
    """
    import sqlite3

    from pyload.core.database.user_database import _gensalt, _salted_password

    api = flask.current_app.config["PYLOAD_API"]
    db_path = os.path.join(api.pyload.userdir, "data", "pyload.db")

    keep = {"pyload": None, "alice": "alicepass", "superadmin": "superpass"}

    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "DELETE FROM users WHERE name NOT IN (?, ?, ?)", tuple(keep)
    )
    for name, password in keep.items():
        if password is None:
            cur.execute("UPDATE users SET role=0, permission=0 WHERE name=?", (name,))
        else:
            cur.execute(
                "UPDATE users SET password=?, role=0, permission=0 WHERE name=?",
                (_salted_password(password, _gensalt()), name),
            )
    con.commit()
    con.close()
    return jsonify(True)
'''

EDITS = {
    "csrf": ("pyload/webui/app/config.py", CSRF_ANCHOR, CSRF_PATCHED),
    "reset": ("pyload/webui/app/blueprints/json_blueprint.py", RESET_ANCHOR, RESET_PATCHED),
    "rolecheck": ("pyload/webui/app/helpers.py", ROLE_ANCHOR, ROLE_PATCHED),
    "rolecheck_api": ("pyload/webui/app/helpers.py", API_ANCHOR, API_PATCHED),
}


def apply(root: pathlib.Path, name: str) -> None:
    rel, anchor, patched = EDITS[name]
    path = root / rel
    text = path.read_text(encoding="utf-8")

    found = text.count(anchor)
    if found != 1:
        raise SystemExit(
            f"REFUSING TO PATCH: anchor for '{name}' occurs {found} times in {rel}, expected 1. "
            "The installed pyload version differs from the one this patch was written against."
        )

    path.write_text(text.replace(anchor, patched), encoding="utf-8")
    print(f"[patch] applied '{name}' to {rel}")


if __name__ == "__main__":
    site_packages = pathlib.Path(sys.argv[1])
    for edit in sys.argv[2:]:
        if edit not in EDITS:
            raise SystemExit(f"unknown edit '{edit}'; known: {', '.join(EDITS)}")
        apply(site_packages, edit)
