"""What `.claude/rules/database.md` asks of every table, checked on a migrated database. Each
service's tests/integration/test_migrations.py asserts that `problems` finds nothing, so a table
that breaks a rule fails the tests instead of reaching production."""

from prepza_common.db import sqlalchemy_url
from sqlalchemy import create_engine, text

# Each rule: what breaks it, and a query naming every table or column that does.
RULES = {
    "created_at without a database default": """
        SELECT table_name FROM information_schema.columns
        WHERE table_schema = 'public' AND column_name = 'created_at' AND column_default IS NULL
    """,
    "timestamp without a time zone": """
        SELECT table_name || '.' || column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND data_type = 'timestamp without time zone'
    """,
    "json instead of jsonb, char(n) or money": """
        SELECT table_name || '.' || column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND data_type IN ('json', 'character', 'money')
    """,
    "a serial key instead of an identity column": """
        SELECT table_name || '.' || column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND column_default LIKE 'nextval(%'
    """,
    "a native enum instead of a CHECK": """
        SELECT typname::text FROM pg_type
        WHERE typtype = 'e' AND typnamespace = 'public'::regnamespace
    """,
    "a foreign key without ON DELETE": """
        SELECT conrelid::regclass::text || '.' || conname FROM pg_constraint
        WHERE contype = 'f' AND connamespace = 'public'::regnamespace AND confdeltype = 'a'
    """,
    # Its columns, in any order, lead an index: else a parent's delete reads the whole table.
    "a foreign key without an index": """
        SELECT c.conrelid::regclass::text || '.' || c.conname FROM pg_constraint c
        WHERE c.contype = 'f' AND c.connamespace = 'public'::regnamespace AND NOT EXISTS (
            SELECT FROM pg_index i
            WHERE i.indrelid = c.conrelid
            AND (i.indkey::int2[])[0:cardinality(c.conkey) - 1] @> c.conkey
            AND (i.indkey::int2[])[0:cardinality(c.conkey) - 1] <@ c.conkey
        )
    """,
    # A concurrent build that failed: it slows writes and serves no query.
    "an invalid index": """
        SELECT indexrelid::regclass::text FROM pg_index i JOIN pg_class t ON t.oid = i.indrelid
        WHERE NOT i.indisvalid AND t.relnamespace = 'public'::regnamespace
    """,
}


def problems(database_url: str) -> list[str]:
    """Every rule broken in the database at `database_url`, as "rule: table[.column]"."""
    engine = create_engine(sqlalchemy_url(database_url))

    try:
        with engine.connect() as connection:
            return sorted(
                f"{rule}: {name}"
                for rule, query in RULES.items()
                for name in connection.execute(text(query)).scalars()
            )
    finally:
        engine.dispose()
