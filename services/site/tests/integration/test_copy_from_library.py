"""The one-off copy of library's news posts and their translations: over once, and a second run
adds nothing and keeps what changed here since."""

import os
import uuid

import psycopg
import pytest
from sqlalchemy.engine import make_url

from site_content.core.db import Session
from site_content.jobs.copy_from_library import main
from site_content.models.news import News
from site_content.repositories import news

LIBRARY_TABLES = """
CREATE TABLE news (id uuid PRIMARY KEY, title varchar(120) NOT NULL, text text NOT NULL,
  published_on date NOT NULL, created_at timestamptz NOT NULL, updated_at timestamptz NOT NULL);
CREATE TABLE news_translations (news_id uuid REFERENCES news ON DELETE CASCADE,
  language varchar(8), title varchar(120) NOT NULL, text text NOT NULL,
  PRIMARY KEY (news_id, language));
"""


def plain(url) -> str:
    return url.render_as_string(hide_password=False).replace("+psycopg", "")


@pytest.fixture
def library(monkeypatch):
    """A stand-in for library's database, with its tables and one post translated into German,
    dropped after."""
    url = make_url(os.environ["DATABASE_URL"])
    name = f"library_copy_{uuid.uuid4().hex[:8]}"
    post = uuid.uuid4()

    with psycopg.connect(plain(url.set(database="postgres")), autocommit=True) as admin:
        admin.execute(f'CREATE DATABASE "{name}"')

    try:
        with psycopg.connect(plain(url.set(database=name)), autocommit=True) as source:
            source.execute(LIBRARY_TABLES)
            source.execute(
                "INSERT INTO news VALUES (%s, 'Hello', 'Our first post', '2026-10-20', now(),"
                " now())",
                [post],
            )
            source.execute(
                "INSERT INTO news_translations VALUES (%s, 'de', 'Hallo', 'Unser erster Beitrag')",
                [post],
            )

        monkeypatch.setenv("LIBRARY_DATABASE_URL", plain(url.set(database=name)))

        yield post
    finally:
        with psycopg.connect(plain(url.set(database="postgres")), autocommit=True) as admin:
            admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


def test_every_row_comes_over_once_and_a_rerun_keeps_what_changed_here(run, library, capsys):
    main()

    async def change_here():
        async with Session.begin() as session:
            row = await session.get(News, library)
            row.title = "Hello again"

    run(change_here())
    main()

    async def found():
        async with Session() as session:
            return (
                (await session.get(News, library)).title,
                await news.titles(session, [library], "de"),
            )

    title, german = run(found())
    printed = capsys.readouterr().out

    assert (title, german) == ("Hello again", {str(library): "Hallo"})
    assert "news: 1 rows copied" in printed
    assert "news: 0 rows copied" in printed
    assert "news_translations: 0 rows copied" in printed
