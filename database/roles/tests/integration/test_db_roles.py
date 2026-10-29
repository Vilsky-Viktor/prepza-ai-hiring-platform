"""The db-roles job gives a service's database and what's in it to the service's own user, who
alone may connect, also when the admin is Postgres's bootstrap user (the local container's).
Its own throwaway database and users, dropped after."""

import os
import uuid
from urllib.parse import urlparse

import psycopg
import pytest
from psycopg import sql

import db_roles

OBJECTS = """
CREATE TABLE things (id serial PRIMARY KEY, name text);
CREATE VIEW thing_names AS SELECT name FROM things;
CREATE SEQUENCE loose_numbers;
CREATE FUNCTION touch() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END $$;
"""
OWNERS = """
SELECT c.relname, pg_get_userbyid(c.relowner) FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind IN ('r', 'v', 'S')
UNION ALL
SELECT p.proname, pg_get_userbyid(p.proowner) FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public' AND p.proname = 'touch'
"""


def at(url: str, database: str, user: str | None = None, password: str | None = None) -> str:
    parsed = urlparse(url)
    netloc = parsed.netloc

    if user:
        netloc = f"{user}:{password}@{parsed.hostname}:{parsed.port or 5432}"

    return parsed._replace(scheme="postgresql", netloc=netloc, path=f"/{database}").geturl()


@pytest.fixture
def service():
    """A database the admin made and filled, and the service user and another one, all new."""
    admin_url = at(os.environ["DATABASE_URL"].replace("+psycopg", ""), "postgres")
    suffix = uuid.uuid4().hex[:8]
    database, user, other = f"roles_{suffix}", f"svc_{suffix}", f"other_{suffix}"

    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
        admin.execute(
            sql.SQL("CREATE ROLE {} LOGIN PASSWORD 'other'").format(sql.Identifier(other))
        )

    with psycopg.connect(at(admin_url, database), autocommit=True) as conn:
        conn.execute(OBJECTS)

    yield admin_url, database, user, other

    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute(
            sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(database))
        )

        for role in (user, other):
            admin.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(role)))


def test_the_service_user_owns_its_database_and_everything_in_it_and_alone_connects(service):
    admin_url, database, user, other = service

    # Twice, as every deploy (and every local start) runs it.
    for _ in range(2):
        with psycopg.connect(admin_url, autocommit=True) as admin:
            db_roles.ensure_user(admin, user, "secret")
            db_roles.give_database(admin, database, user)

        db_roles.give_objects(admin_url, database, user)

    with psycopg.connect(at(admin_url, database, user, "secret")) as conn:
        owners = dict(conn.execute(OWNERS).fetchall())
        # The owner changes its own tables, as its migrations do.
        conn.execute("ALTER TABLE things ADD COLUMN note text")

    assert owners == {
        "things": user,
        "things_id_seq": user,
        "thing_names": user,
        "loose_numbers": user,
        "touch": user,
    }

    with pytest.raises(psycopg.OperationalError, match="permission denied"):
        psycopg.connect(at(admin_url, database, other, "other")).close()
