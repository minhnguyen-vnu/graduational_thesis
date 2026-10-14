#!/usr/bin/env python3
"""
Seed the pyLoad user database with the accounts the MR-A1 triple needs.

pyLoad creates exactly one account on first start ("pyload"/"pyload", role 0 = ADMIN),
which is not enough: the triple needs a VICTIM admin (demoted mid-triple) and a separate
OPERATOR admin (still privileged enough to perform the demotion).

  alice      / alicepass  role 0 (ADMIN)  -- victim, demoted by the transition
  superadmin / superpass  role 0 (ADMIN)  -- operator, performs the transition

Passwords are hashed with pyLoad's own helpers, and rows are written with the same columns
as UserDatabase.add_user, so these accounts are indistinguishable from ones created through
the application. Seeding users is not a change to application behaviour -- it is the test
fixture, the same role infra/reports-api's /reset and VAmPI's /createdb play.

Idempotent: re-running resets the seeded accounts to their initial role, which is what makes
it usable to restore state between runs.
"""
import pathlib
import sqlite3
import sys

from pyload.core.database.user_database import _gensalt, _salted_password

ROLE_ADMIN = 0

USERS = [
    ("alice", "alicepass", ROLE_ADMIN),
    ("superadmin", "superpass", ROLE_ADMIN),
]


def seed(db_path: pathlib.Path) -> None:
    if not db_path.is_file():
        raise SystemExit(f"no pyload database at {db_path}")

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    for name, password, role in USERS:
        salted = _salted_password(password, _gensalt())
        cur.execute("SELECT name FROM users WHERE name=?", (name,))
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO users (name, password, role, permission) VALUES (?, ?, ?, ?)",
                (name, salted, role, 0),
            )
            action = "created"
        else:
            # Reset an existing account: this is what restores role state between runs.
            cur.execute(
                "UPDATE users SET password=?, role=?, permission=? WHERE name=?",
                (salted, role, 0, name),
            )
            action = "reset"
        print(f"[seed] {action} {name} (role={role})")

    con.commit()
    con.close()


if __name__ == "__main__":
    seed(pathlib.Path(sys.argv[1]))
