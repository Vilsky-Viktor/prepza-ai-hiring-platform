"""A migration step the services share: a tenant-owned child table gets the company_id its parent
already has (`.claude/rules/database.md`, Tenancy), without a long lock. `op` is the migration's
alembic operations object, passed in so the library needs no alembic of its own."""


def add_company_id(op, table: str, fill_batch: str, required: bool = True) -> None:
    """Adds `table.company_id` (uuid), fills it from the parent with `fill_batch` (an UPDATE of at
    most a batch of rows still empty, each run its own transaction, until one changes none),
    indexes it concurrently and, when `required`, makes it NOT NULL through a validated CHECK,
    so neither step scans the table under an exclusive lock."""
    filled = f"ck_{table}_company_id_filled"
    op.execute(f"ALTER TABLE {table} ADD COLUMN company_id uuid")

    with op.get_context().autocommit_block():
        while op.get_bind().exec_driver_sql(fill_batch).rowcount:
            pass

        op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS ix_{table}_company_id")
        op.execute(f"CREATE INDEX CONCURRENTLY ix_{table}_company_id ON {table} (company_id)")

        if required:
            op.execute(
                f"ALTER TABLE {table} ADD CONSTRAINT {filled} "
                "CHECK (company_id IS NOT NULL) NOT VALID"
            )
            op.execute(f"ALTER TABLE {table} VALIDATE CONSTRAINT {filled}")
            op.execute(f"ALTER TABLE {table} ALTER COLUMN company_id SET NOT NULL")
            op.execute(f"ALTER TABLE {table} DROP CONSTRAINT {filled}")


def drop_company_id(op, table: str) -> None:
    op.execute(f"ALTER TABLE {table} DROP COLUMN company_id")
