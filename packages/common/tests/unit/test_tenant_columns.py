from contextlib import contextmanager

from prepza_common import tenant_columns


class FakeOp:
    """Records the statements; the fill changes rows twice, then none."""

    def __init__(self):
        self.run = []
        self.fills = iter([3, 1, 0])

    def execute(self, statement):
        self.run.append(statement)

    def get_context(self):
        op = self

        class Context:
            @contextmanager
            def autocommit_block(self):
                op.run.append("autocommit")
                yield

        return Context()

    def get_bind(self):
        op = self

        class Bind:
            def exec_driver_sql(self, statement):
                op.run.append("fill")

                class Result:
                    rowcount = next(op.fills)

                return Result()

        return Bind()


def test_the_column_is_filled_until_none_is_left_then_indexed_and_made_required():
    op = FakeOp()

    tenant_columns.add_company_id(op, "child", "UPDATE child ...")

    assert op.run == [
        "ALTER TABLE child ADD COLUMN company_id uuid",
        "autocommit",
        "fill",
        "fill",
        "fill",
        "DROP INDEX CONCURRENTLY IF EXISTS ix_child_company_id",
        "CREATE INDEX CONCURRENTLY ix_child_company_id ON child (company_id)",
        (
            "ALTER TABLE child ADD CONSTRAINT ck_child_company_id_filled "
            "CHECK (company_id IS NOT NULL) NOT VALID"
        ),
        "ALTER TABLE child VALIDATE CONSTRAINT ck_child_company_id_filled",
        "ALTER TABLE child ALTER COLUMN company_id SET NOT NULL",
        "ALTER TABLE child DROP CONSTRAINT ck_child_company_id_filled",
    ]


def test_a_column_some_rows_leave_empty_stays_nullable():
    op = FakeOp()

    tenant_columns.add_company_id(op, "child", "UPDATE child ...", required=False)

    assert not any("NOT NULL" in statement for statement in op.run)
