"""What `.claude/rules/database.md` asks of every table, checked on a migrated database. Each
service's tests/integration/test_migrations.py asserts that `problems` finds nothing, so a table
that breaks a rule fails the tests instead of reaching production."""

import importlib
import pkgutil
import re
from types import ModuleType

from prepza_common.db import sqlalchemy_url
from sqlalchemy import CheckConstraint, create_engine, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

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

# Every constraint and index of the database, by table.
NAMES = """
    SELECT conrelid::regclass::text, conname FROM pg_constraint
    WHERE connamespace = 'public'::regnamespace AND contype IN ('p', 'u', 'f', 'c')
    UNION SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public'
"""


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


def _model_names(models: ModuleType) -> set[tuple[str, str]]:
    """The constraints and indexes the models in the package `models` (every module of it, and
    its Base in models.base) would create, by table."""
    for module in pkgutil.iter_modules(models.__path__):
        importlib.import_module(f"{models.__name__}.{module.name}")

    metadata = importlib.import_module(f"{models.__name__}.base").Base.metadata
    dialect = postgresql.dialect()
    names = set()

    for table in metadata.tables.values():
        ddl = str(CreateTable(table).compile(dialect=dialect))
        names |= {(table.name, name) for name in re.findall(r"CONSTRAINT (\w+)", ddl)}
        names |= {
            (
                table.name,
                re.search(r"INDEX (\w+) ON", str(CreateIndex(index).compile(dialect=dialect)))[1],
            )
            for index in table.indexes
        }

    return names


def misnamed(database_url: str, models: ModuleType) -> list[str]:
    """The constraints and indexes whose names differ between the models (app.models, with the
    naming convention) and the database: a migration dropping one by its model's name would
    miss it. Tables outside the models are left out."""
    named = _model_names(models)
    tables = {table for table, _ in named}
    engine = create_engine(sqlalchemy_url(database_url))

    try:
        with engine.connect() as connection:
            found = {
                (table, name)
                for table, name in connection.execute(text(NAMES)).all()
                if table in tables
            }
    finally:
        engine.dispose()

    return sorted(
        [f"only in the models: {t}.{n}" for t, n in named - found]
        + [f"only in the database: {t}.{n}" for t, n in found - named]
    )


def _literals(condition: str) -> set[str]:
    """The quoted values and the numbers in a CHECK's condition, however Postgres rewrote it."""
    quoted = set(re.findall(r"'((?:[^']|'')*)'", condition))
    numbers = set(
        re.findall(r"(?<![\w'.])-?\d+(?![\w'])", re.sub(r"'(?:[^']|'')*'", "", condition))
    )

    return quoted | numbers


def stale_checks(database_url: str, models: ModuleType) -> list[str]:
    """The models' CHECKs (by name) missing from the database or allowing other values there: a
    value added to a closed set in the code needs a migration that changes its CHECK, or the
    database refuses it."""
    _model_names(models)
    metadata = importlib.import_module(f"{models.__name__}.base").Base.metadata
    wanted = {
        constraint.name: str(constraint.sqltext)
        for table in metadata.tables.values()
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }
    engine = create_engine(sqlalchemy_url(database_url))

    try:
        with engine.connect() as connection:
            found = dict(
                connection.execute(
                    text(
                        "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint"
                        " WHERE contype = 'c' AND connamespace = 'public'::regnamespace"
                    )
                ).all()
            )
    finally:
        engine.dispose()

    return sorted(
        f"{name}: " + ("missing" if name not in found else "allows other values")
        for name, condition in wanted.items()
        if name not in found or _literals(condition) != _literals(found[name])
    )
