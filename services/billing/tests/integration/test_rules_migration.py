"""Migration 0024 on a database that already holds a row its NOT VALID check refuses (an
ai_usage row a test once stored): it still runs, as it backfills before adding the checks."""

import os
import subprocess
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ROW = (
    "INSERT INTO ai_usage (id, event_id, occurred_at, action, service, model, input_tokens, "
    "cached_input_tokens, output_tokens, audio_seconds, cost_usd, outcome, category) VALUES "
    "(gen_random_uuid(), 'old-test-row', now(), 'help_chat', 'a-test', 'm', 0, 0, 0, 0, 0.5, "
    "'ok', 'paid')"
)


def upgrade(url: str, revision: str) -> None:
    env = {**os.environ, "DATABASE_URL": url}
    done = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", revision],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert done.returncode == 0, done.stderr[-2000:]


def test_the_rules_migration_runs_over_a_row_its_service_check_refuses():
    url = make_url(os.environ["DATABASE_URL"]).set(database="billing_rules_migration_test")
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

        upgrade(plain, "0024")

        with engine.connect() as connection:
            cost = connection.scalar(text("SELECT cost FROM ai_usage"))

        engine.dispose()

        assert float(cost) == 0.5
    finally:
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))

        admin.dispose()
