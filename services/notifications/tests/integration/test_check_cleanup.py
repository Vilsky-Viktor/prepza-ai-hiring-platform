"""Migration 0021 deletes the notifications ck_notifications_kind refuses (a kind no longer sent)
and validates the check."""

import os
import subprocess
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ROW = (
    "INSERT INTO notifications (id, event_id, recipient, recipient_id, kind, link, data) "
    "VALUES (gen_random_uuid(), '{event}', 'user', 'u1', '{kind}', '/x', '{{}}')"
)


def upgrade(url: str, revision: str) -> None:
    done = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", revision],
        env={**os.environ, "DATABASE_URL": url},
        capture_output=True,
        text=True,
        check=False,
    )

    assert done.returncode == 0, done.stderr[-2000:]


def test_the_refused_rows_go_and_the_check_is_validated():
    url = make_url(os.environ["DATABASE_URL"]).set(database="notifications_check_cleanup_test")
    admin = create_engine(
        url.set(drivername="postgresql+psycopg", database="postgres"), isolation_level="AUTOCOMMIT"
    )
    plain = url.render_as_string(hide_password=False).replace("+psycopg", "")

    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))
        connection.execute(text(f'CREATE DATABASE "{url.database}"'))

    try:
        # Before the kinds were checked.
        upgrade(plain, "0014")
        engine = create_engine(url.set(drivername="postgresql+psycopg"))

        with engine.begin() as connection:
            connection.execute(text(ROW.format(event="old", kind="kit_ready")))
            connection.execute(text(ROW.format(event="kept", kind="news")))

        upgrade(plain, "head")

        with engine.connect() as connection:
            left = list(connection.scalars(text("SELECT event_id FROM notifications")))
            valid = connection.scalar(
                text(
                    "SELECT convalidated FROM pg_constraint WHERE conname = 'ck_notifications_kind'"
                )
            )

        engine.dispose()

        assert (left, valid) == (["kept"], True)
    finally:
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))

        admin.dispose()
