"""Migration 0028 deletes the AI usage rows ck_ai_usage_service refuses (a test's 'e2e' calls)
and validates the check."""

import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from tests.integration.test_rules_migration import ROW, upgrade


def test_the_refused_rows_go_and_the_check_is_validated():
    url = make_url(os.environ["DATABASE_URL"]).set(database="billing_check_cleanup_test")
    admin = create_engine(
        url.set(drivername="postgresql+psycopg", database="postgres"), isolation_level="AUTOCOMMIT"
    )
    plain = url.render_as_string(hide_password=False).replace("+psycopg", "")

    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))
        connection.execute(text(f'CREATE DATABASE "{url.database}"'))

    try:
        upgrade(plain, "0023")
        engine = create_engine(url.set(drivername="postgresql+psycopg"))

        with engine.begin() as connection:
            connection.execute(text(ROW))
            connection.execute(
                text(ROW.replace("'a-test'", "'rounds'").replace("old-test-row", "kept"))
            )

        upgrade(plain, "head")

        with engine.connect() as connection:
            left = list(connection.scalars(text("SELECT event_id FROM ai_usage")))
            valid = connection.scalar(
                text("SELECT convalidated FROM pg_constraint WHERE conname = 'ck_ai_usage_service'")
            )

        engine.dispose()

        assert (left, valid) == (["kept"], True)
    finally:
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))

        admin.dispose()
