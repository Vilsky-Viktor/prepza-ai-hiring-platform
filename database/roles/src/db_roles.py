"""Gives each service its own Postgres user, owning only its own database.

Run by the deploy pipeline before migrations, as a Cloud Run job with the admin's URL
(ADMIN_DATABASE_URL, the instance's admin user, on the `postgres` database) and every service's
URL (DATABASE_URL_<NAME>: that service's user, password and database). Safe to repeat: users are
created or get their password again, ownership moves only if it hasn't yet.

Users are made here, by SQL, not through Cloud SQL's API, which makes every user it creates a
member of cloudsqlsuperuser; these get nothing but their own database. Docker Compose runs it
too (`db-roles`), before every migration, with the local admin `prepza`. Its own small image
(database/roles/Dockerfile), as it belongs to no service.

    python -m db_roles
"""

import os
from urllib.parse import unquote, urlparse

import psycopg
from psycopg import sql

ADMIN_URL = "ADMIN_DATABASE_URL"
SERVICE_PREFIX = "DATABASE_URL_"


def service_logins(environ) -> list[tuple[str, str, str]]:
    """(database, user, password) of every service, from its DATABASE_URL_<NAME>."""
    logins = []

    for key, url in sorted(environ.items()):
        if not key.startswith(SERVICE_PREFIX):
            continue

        parsed = urlparse(url)
        database = parsed.path.lstrip("/")
        user = unquote(parsed.username or "")
        logins.append((database, user, unquote(parsed.password or "")))

    return logins


def ensure_user(admin, user: str, password: str) -> None:
    """Creates the user, or sets its password again; the admin may then act for it."""
    exists = admin.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", [user]).fetchone()
    statement = (
        "ALTER ROLE {} WITH LOGIN PASSWORD {}" if exists else "CREATE ROLE {} LOGIN PASSWORD {}"
    )
    admin.execute(sql.SQL(statement).format(sql.Identifier(user), sql.Literal(password)))
    admin.execute(sql.SQL("GRANT {} TO CURRENT_USER").format(sql.Identifier(user)))


def give_database(admin, database: str, user: str) -> None:
    """The user owns its database, and only it may connect."""
    name, role = sql.Identifier(database), sql.Identifier(user)
    admin.execute(sql.SQL("ALTER DATABASE {} OWNER TO {}").format(name, role))
    admin.execute(sql.SQL("REVOKE ALL ON DATABASE {} FROM PUBLIC").format(name))
    admin.execute(sql.SQL("GRANT CONNECT, TEMPORARY ON DATABASE {} TO {}").format(name, role))


# The relations in `public` the admin owns, but not a sequence that moves with its table's column
# (serial, identity), which can't change owner on its own.
OWN_RELATIONS = """
SELECT c.oid::regclass::text FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p', 'v', 'S')
  AND c.relowner = (SELECT oid FROM pg_roles WHERE rolname = CURRENT_USER)
  AND NOT EXISTS (
    SELECT 1 FROM pg_depend d WHERE d.objid = c.oid AND d.deptype IN ('a', 'i')
  )
"""
# The functions in `public` the admin owns (the migrations' triggers'), but not an extension's.
OWN_FUNCTIONS = """
SELECT p.oid::regprocedure::text FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public'
  AND p.proowner = (SELECT oid FROM pg_roles WHERE rolname = CURRENT_USER)
  AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.objid = p.oid AND d.deptype = 'e')
"""
# Postgres's bootstrap superuser: the local container's admin (POSTGRES_USER), never Cloud SQL's.
BOOTSTRAP_USER = "SELECT oid = 10 FROM pg_roles WHERE rolname = CURRENT_USER"


def give_objects(admin_url: str, database: str, user: str) -> None:
    """What the admin created in the database (tables, sequences, the vector extension) moves to
    the user. The admin owns no database any more by now, so nothing outside it moves. Postgres
    refuses to reassign everything the bootstrap superuser owns (the local admin), so then only
    its tables, views, sequences and functions move, one at a time."""
    url = urlparse(admin_url)._replace(path=f"/{database}").geturl()
    role = sql.Identifier(user)

    with psycopg.connect(url, autocommit=True) as conn:
        if not conn.execute(BOOTSTRAP_USER).fetchone()[0]:
            conn.execute(sql.SQL("REASSIGN OWNED BY CURRENT_USER TO {}").format(role))

            return

        for (name,) in conn.execute(OWN_RELATIONS).fetchall():
            conn.execute(sql.SQL("ALTER TABLE {} OWNER TO {}").format(sql.SQL(name), role))

        for (name,) in conn.execute(OWN_FUNCTIONS).fetchall():
            conn.execute(sql.SQL("ALTER FUNCTION {} OWNER TO {}").format(sql.SQL(name), role))


def main() -> None:
    admin_url = os.environ[ADMIN_URL]
    admin_user = unquote(urlparse(admin_url).username or "")
    logins = service_logins(os.environ)

    if not logins or any(not user or user == admin_user for _, user, _ in logins):
        raise SystemExit("Each service needs its own user, other than the admin.")

    with psycopg.connect(admin_url, autocommit=True) as admin:
        for _, user, password in logins:
            ensure_user(admin, user, password)

        # Every database changes owner before any objects move: moving objects also moves the
        # databases the admin still owns.
        for database, user, _ in logins:
            give_database(admin, database, user)

    for database, user, _ in logins:
        give_objects(admin_url, database, user)

    print(f"Database users set for {len(logins)} services")


if __name__ == "__main__":
    main()
