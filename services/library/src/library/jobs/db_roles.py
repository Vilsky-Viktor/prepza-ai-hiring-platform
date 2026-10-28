"""Gives each service its own Postgres user, owning only its own database.

Run by the deploy pipeline before migrations, as a Cloud Run job with the admin's URL
(ADMIN_DATABASE_URL, the instance's admin user, on the `postgres` database) and every service's
URL (DATABASE_URL_<NAME>: that service's user, password and database). Safe to repeat: users are
created or get their password again, ownership moves only if it hasn't yet.

Users are made here, by SQL, not through Cloud SQL's API, which makes every user it creates a
member of cloudsqlsuperuser; these get nothing but their own database.

    uv run --no-sync python -m library.jobs.db_roles
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


def give_objects(admin_url: str, database: str, user: str) -> None:
    """What the admin created in the database (tables, sequences, the vector extension) moves to
    the user. The admin owns no database any more by now, so nothing outside it moves."""
    url = urlparse(admin_url)._replace(path=f"/{database}").geturl()

    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(sql.SQL("REASSIGN OWNED BY CURRENT_USER TO {}").format(sql.Identifier(user)))


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
