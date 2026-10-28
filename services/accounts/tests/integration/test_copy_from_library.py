"""The one-off copy of library's email settings, consent log and accepted terms: every row comes
over once, and a second run adds nothing and keeps what changed here since."""

import os
import uuid

import psycopg
import pytest
from sqlalchemy.engine import make_url

from accounts.core.db import Session
from accounts.jobs.copy_from_library import main
from accounts.models.emails import EmailPreferences
from accounts.repositories import emails, legal
from tests.integration.transactions import transaction

LIBRARY_TABLES = """
CREATE TABLE email_preferences (user_id varchar(128) PRIMARY KEY,
  candidate_finished bool NOT NULL, invite_undelivered bool NOT NULL,
  ats_not_invited bool NOT NULL, interview_ready bool NOT NULL, reminders bool NOT NULL,
  updates bool NOT NULL, promotions bool NOT NULL, updated_at timestamptz NOT NULL);
CREATE TABLE email_consents (id uuid PRIMARY KEY, user_id varchar(128) NOT NULL,
  setting varchar(32) NOT NULL, granted bool NOT NULL, source varchar(16) NOT NULL,
  basis varchar(16) NOT NULL, text_version varchar(16) NOT NULL, changed_by varchar(128),
  created_at timestamptz NOT NULL);
CREATE TABLE terms_acceptances (user_id varchar(128), version varchar(10),
  accepted_at timestamptz NOT NULL, PRIMARY KEY (user_id, version));
"""


def plain(url) -> str:
    return url.render_as_string(hide_password=False).replace("+psycopg", "")


@pytest.fixture
def library(monkeypatch):
    """A stand-in for library's database, with its tables and one user's rows, dropped after."""
    url = make_url(os.environ["DATABASE_URL"])
    name = f"library_copy_{uuid.uuid4().hex[:8]}"
    user = f"copied-{uuid.uuid4()}"

    with psycopg.connect(plain(url.set(database="postgres")), autocommit=True) as admin:
        admin.execute(f'CREATE DATABASE "{name}"')

    try:
        with psycopg.connect(plain(url.set(database=name)), autocommit=True) as source:
            source.execute(LIBRARY_TABLES)
            source.execute(
                "INSERT INTO email_preferences VALUES (%s, true, true, true, true, false,"
                " true, false, now())",
                [user],
            )
            source.execute(
                "INSERT INTO email_consents VALUES (%s, %s, 'updates', true, 'sign_in',"
                " 'soft_opt_in', '2026-10-08', NULL, now())",
                [uuid.uuid4(), user],
            )
            source.execute("INSERT INTO terms_acceptances VALUES (%s, '2026-10-10', now())", [user])

        monkeypatch.setenv("LIBRARY_DATABASE_URL", plain(url.set(database=name)))

        yield user
    finally:
        with psycopg.connect(plain(url.set(database="postgres")), autocommit=True) as admin:
            admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


def test_every_row_comes_over_once_and_a_rerun_keeps_what_changed_here(run, library, capsys):
    main()

    async def change_here():
        async with Session.begin() as session:
            row = await session.get(EmailPreferences, library)
            row.reminders = True

    run(change_here())
    main()

    async def found():
        return (
            await transaction(emails.preferences, library),
            await transaction(emails.consents, library),
            await transaction(legal.accepted_terms, library),
        )

    preferences, consents, terms = run(found())
    printed = capsys.readouterr().out

    assert (preferences["updates"], preferences["reminders"]) == (True, True)
    assert [(row["setting"], row["basis"]) for row in consents] == [("updates", "soft_opt_in")]
    assert [row["version"] for row in terms] == ["2026-10-10"]
    assert printed.splitlines()[3:] == [
        "email_preferences: 0 rows copied",
        "email_consents: 0 rows copied",
        "terms_acceptances: 0 rows copied",
    ]
