"""scripts/check_migrations.py: what it finds in a migration's upgrade, and what it lets pass."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "check_migrations", Path(__file__).resolve().parent.parent / "check_migrations.py"
)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)

NO_CONCURRENTLY = "an index built without CONCURRENTLY"
VALIDATED = "a foreign key or CHECK added without NOT VALID"
TYPE = "a column's type changed in place"
NOT_NULL = "SET NOT NULL without a validated CHECK (col IS NOT NULL)"
RENAME = "a rename (expand, then contract)"


def upgrade(*statements: str) -> str:
    body = "\n".join(f"    {statement}" for statement in statements)

    return f"from alembic import op\n\n\ndef upgrade() -> None:\n{body}\n"


@pytest.mark.parametrize(
    ("statement", "found"),
    [
        ('op.create_index("ix_t_a", "t", ["a"])', NO_CONCURRENTLY),
        ('op.execute("CREATE INDEX ix_t_a ON t (a)")', NO_CONCURRENTLY),
        ('op.execute("CREATE UNIQUE INDEX ix_t_a ON t (a)")', NO_CONCURRENTLY),
        ('op.create_foreign_key("fk", "t", "p", ["p_id"], ["id"])', VALIDATED),
        ('op.create_check_constraint("ck_t_a", "t", "a > 0")', VALIDATED),
        ('op.execute("ALTER TABLE t ADD CONSTRAINT ck_t_a CHECK (a > 0)")', VALIDATED),
        ('op.alter_column("t", "a", type_=sa.Text())', TYPE),
        ('op.execute("ALTER TABLE t ALTER COLUMN a TYPE text")', TYPE),
        ('op.alter_column("t", "a", nullable=False)', NOT_NULL),
        ('op.execute("ALTER TABLE t ALTER COLUMN a SET NOT NULL")', NOT_NULL),
        ('op.alter_column("t", "a", new_column_name="b")', RENAME),
        ('op.rename_table("t", "u")', RENAME),
        ('op.execute(f"ALTER TABLE {table} RENAME TO u")', RENAME),
    ],
)
def test_an_unsafe_operation_on_an_existing_table_is_found(statement, found):
    assert check.problems(upgrade(statement)) == [(5, found)]


@pytest.mark.parametrize(
    "statement",
    [
        'op.create_index("ix_t_a", "t", ["a"], postgresql_concurrently=True)',
        'op.execute("CREATE INDEX CONCURRENTLY ix_t_a ON t (a)")',
        'op.create_check_constraint("ck_t_a", "t", "a > 0", postgresql_not_valid=True)',
        'op.execute("ALTER TABLE t ADD CONSTRAINT ck_t_a CHECK (a > 0) NOT VALID")',
        'op.execute("ALTER TABLE t VALIDATE CONSTRAINT ck_t_a")',
        'op.add_column("t", sa.Column("a", sa.Text(), server_default="x"))',
        'op.execute("ALTER TABLE t ALTER COLUMN created_at SET DEFAULT now()")',
    ],
)
def test_a_safe_operation_passes(statement):
    assert check.problems(upgrade(statement)) == []


def test_anything_goes_on_a_table_made_in_the_same_migration():
    source = upgrade(
        'op.create_table("t", sa.Column("a", sa.Text()))',
        'op.create_index("ix_t_a", "t", ["a"])',
        "op.execute(\"ALTER TABLE t ADD CONSTRAINT ck_t_a CHECK (a <> '')\")",
    )

    assert check.problems(source) == []


def test_set_not_null_passes_after_a_check_that_the_column_is_not_null():
    source = upgrade(
        'op.execute("ALTER TABLE t ADD CONSTRAINT ck_t_a CHECK (a IS NOT NULL) NOT VALID")',
        'op.execute("ALTER TABLE t VALIDATE CONSTRAINT ck_t_a")',
        'op.execute("ALTER TABLE t ALTER COLUMN a SET NOT NULL")',
    )

    assert check.problems(source) == []


def test_a_statement_marked_as_allowed_passes_and_a_downgrade_is_not_checked():
    source = (
        upgrade(
            "# migration-check: a row per wallet at most",
            'op.execute("ALTER TABLE t ADD CONSTRAINT ck_t_a CHECK (a > 0)")',
        )
        + '\n\ndef downgrade() -> None:\n    op.create_index("ix_t_a", "t", ["a"])\n'
    )

    assert check.problems(source) == []


def test_a_helper_the_upgrade_calls_is_checked():
    source = (
        "from alembic import op\n\n\ndef add():\n"
        '    op.execute("ALTER TABLE t ADD CONSTRAINT ck_t_a CHECK (a > 0)")\n'
    )

    assert check.problems(source) == [(5, VALIDATED)]


def test_the_migrations_in_the_repository_pass():
    assert check.main() == 0
