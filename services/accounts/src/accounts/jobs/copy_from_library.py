"""Copies users' email settings, their consent log and accepted terms from library's database,
which held them before this service, into this one. A one-off, run once where library has such
rows (locally; production had none before launch), before library stops using its tables. Safe
to repeat: a row already here (by its key) is left as it is, so nothing changed here since is
overwritten.

Reads library's database as library's own user (LIBRARY_DATABASE_URL) and writes this
service's (DATABASE_URL):

    LIBRARY_DATABASE_URL=postgresql://library:...@postgres:5432/library \\
        uv run --no-sync python -m accounts.jobs.copy_from_library
"""

import os

import psycopg
from psycopg import sql

from accounts.constants.library_copy import COPY_BATCH, LIBRARY_TABLES


def copy_table(source, target, table: str, columns: tuple, key: tuple) -> int:
    """Every row of `table`, COPY_BATCH at a time, each batch its own transaction; how many
    were new here."""
    names = sql.SQL(", ").join(map(sql.Identifier, columns))
    select = sql.SQL("SELECT {} FROM {} ORDER BY {}").format(
        names, sql.Identifier(table), sql.SQL(", ").join(map(sql.Identifier, key))
    )
    insert = sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT ({}) DO NOTHING").format(
        sql.Identifier(table),
        names,
        sql.SQL(", ").join(sql.Placeholder() * len(columns)),
        sql.SQL(", ").join(map(sql.Identifier, key)),
    )
    added = 0

    with source.cursor(name=f"copy_{table}") as rows:
        rows.execute(select)

        while batch := rows.fetchmany(COPY_BATCH):
            with target.transaction(), target.cursor() as cursor:
                for row in batch:
                    cursor.execute(insert, row)
                    added += cursor.rowcount

    return added


def main() -> None:
    with (
        psycopg.connect(os.environ["LIBRARY_DATABASE_URL"]) as source,
        psycopg.connect(os.environ["DATABASE_URL"], autocommit=True) as target,
    ):
        for table, (columns, key) in LIBRARY_TABLES.items():
            added = copy_table(source, target, table, columns, key)
            print(f"{table}: {added} rows copied")


if __name__ == "__main__":
    main()
