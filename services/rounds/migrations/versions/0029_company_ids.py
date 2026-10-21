"""Every tenant's row carries its company: sessions get company_id from companies' request (an
interview's; practice has none), and answers and signals from their section, filled by a
trigger on every insert. Sections saved before keep none: their company lives in the companies
service, which a migration can't read

Revision ID: 0029
Revises: 0028
Create Date: 2026-10-22
"""

from alembic import op
from prepza_common.tenant_columns import add_company_id, drop_company_id

revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None

CHILDREN = ("answers", "signals")
FROM_SESSION = """
CREATE FUNCTION company_from_session() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.company_id IS NULL THEN
        SELECT company_id INTO NEW.company_id FROM sessions WHERE id = NEW.session_id;
    END IF;
    RETURN NEW;
END $$
"""
# Nothing to fill: no section has its company yet.
NOTHING = "UPDATE {table} SET company_id = NULL WHERE false"


def upgrade() -> None:
    add_company_id(op, "sessions", NOTHING.format(table="sessions"), required=False)
    op.execute(FROM_SESSION)

    for table in CHILDREN:
        add_company_id(op, table, NOTHING.format(table=table), required=False)
        op.execute(
            f"CREATE TRIGGER company_from_session BEFORE INSERT ON {table} FOR EACH ROW "
            "EXECUTE FUNCTION company_from_session()"
        )


def downgrade() -> None:
    for table in CHILDREN:
        op.execute(f"DROP TRIGGER company_from_session ON {table}")
        drop_company_id(op, table)

    op.execute("DROP FUNCTION company_from_session()")
    drop_company_id(op, "sessions")
