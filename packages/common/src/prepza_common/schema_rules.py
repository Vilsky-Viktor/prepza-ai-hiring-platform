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
