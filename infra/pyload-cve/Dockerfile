# Tier-2b target: pyLoad CVE-2026-41133 (CWE-613, stale session privilege after role change).
#
# The vulnerability is REAL and THIRD-PARTY -- not seeded by us. Login caches role/permission
# into the Flask session; authorization later reads that cache; set_user_permission() never
# invalidates any session. A demoted admin therefore keeps admin power for the life of the
# session cookie.
#
# BOTH variants are built from the SAME upstream release (0.5.0b3.dev97). Upstream never
# actually fixed this -- is_authenticated is byte-identical dev97..dev101 and on develop,
# despite the advisory claiming a fix in dev98 -- so the fixed variant is a CONTROL WE WRITE,
# applying to the session branch the fresh-database read the X-API-Key branch already does.
# Using one upstream version for both arms makes the differential as tight as possible: the
# ONLY difference between the two images is that one edit.
#
#   STATEFUL_ROLE_CHECK=0  -> VULNERABLE (default)
#   STATEFUL_ROLE_CHECK=1  -> FIXED (control)
#
# Both variants additionally get the CSRF edit, so it cancels out of the differential.
# See patch_pyload.py for why each edit is needed and what it does not touch.
FROM python:3.11-slim

ARG PYLOAD_VERSION=0.5.0b3.dev97
ARG STATEFUL_ROLE_CHECK=0

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "pyload-ng==${PYLOAD_VERSION}"

COPY patch_pyload.py /patch_pyload.py

# The CSRF edit goes to both variants; the role-check edit only to the fixed one.
# patch_pyload.py aborts the build if an anchor does not match exactly once.
RUN SP=$(python -c "import site; print(site.getsitepackages()[0])") \
 && python /patch_pyload.py "$SP" csrf reset \
 && if [ "${STATEFUL_ROLE_CHECK}" = "1" ]; then python /patch_pyload.py "$SP" rolecheck rolecheck_api; fi

# Record which variant this image is, so a running container is self-identifying.
ENV PYLOAD_VARIANT_VERSION=${PYLOAD_VERSION}
ENV PYLOAD_STATEFUL_ROLE_CHECK=${STATEFUL_ROLE_CHECK}

COPY seed_users.py /seed_users.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

CMD ["/entrypoint.sh"]