"""Every tenant's row carries its company: sets get company_id from owner_id (a company's own;
NULL for a platform template, CHECKed), and topics, questions and the questions' stats,
revisions, ratings, reports and reporters from their parent, each filled in batches and
indexed. A trigger fills it on every insert, from the parent, so no insert path can miss it.
And one topic per place in its set, one question per place in its topic, deferred so a reorder
swaps places in one transaction (unique indexes built concurrently, then attached)

Revision ID: 0035
Revises: 0034
Create Date: 2026-10-22
"""

from alembic import op
from prepza_common.db.tenant_columns import add_company_id, drop_company_id

revision = "0035"
down_revision = "0034"
branch_labels = None
depends_on = None

# (table, its parent, the column that points at it), parents first.
CHILDREN = (
    ("topics", "sets", "set_id"),
    ("questions", "topics", "topic_id"),
    ("question_stats", "questions", "question_id"),
    ("question_revisions", "questions", "question_id"),
    ("question_ratings", "questions", "question_id"),
    ("question_reports", "questions", "question_id"),
    ("question_reporters", "questions", "question_id"),
)
SETS_FILL = (
    "UPDATE sets SET company_id = owner_id::uuid WHERE id IN (SELECT id FROM sets "
    "WHERE company_id IS NULL AND owner_type = 'company' LIMIT 1000)"
)
OWNED = "ck_sets_company_id"
# A child's company, from its parent (TG_ARGV: the parent table, the column pointing at it).
FROM_PARENT = """
CREATE FUNCTION company_from_parent() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.company_id IS NULL THEN
        EXECUTE format('SELECT company_id FROM %I WHERE id = $1.%I', TG_ARGV[0], TG_ARGV[1])
            INTO NEW.company_id USING NEW;
    END IF;
    RETURN NEW;
END $$
"""
FROM_OWNER = """
CREATE FUNCTION company_from_owner() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.owner_type = 'company' THEN
        NEW.company_id := NEW.owner_id::uuid;
    END IF;
    RETURN NEW;
END $$
"""
# (constraint, table, columns)
POSITIONS = (
    ("uq_topics_set_position", "topics", "set_id, position"),
    ("uq_questions_topic_position", "questions", "topic_id, position"),
)


def fill(table: str, parent: str, column: str) -> str:
    return (
        f"UPDATE {table} t SET company_id = p.company_id FROM {parent} p "
        f"WHERE p.id = t.{column} AND t.ctid IN (SELECT c.ctid FROM {table} c "
        f"JOIN {parent} q ON q.id = c.{column} "
        "WHERE c.company_id IS NULL AND q.company_id IS NOT NULL LIMIT 1000)"
    )


def upgrade() -> None:
    op.execute(FROM_PARENT)
    op.execute(FROM_OWNER)
    op.execute(
        "CREATE TRIGGER company_from_owner BEFORE INSERT OR UPDATE OF owner_type, owner_id "
        "ON sets FOR EACH ROW EXECUTE FUNCTION company_from_owner()"
    )

    for table, parent, column in CHILDREN:
        op.execute(
            f"CREATE TRIGGER company_from_parent BEFORE INSERT ON {table} FOR EACH ROW "
            f"EXECUTE FUNCTION company_from_parent('{parent}', '{column}')"
        )

    add_company_id(op, "sets", SETS_FILL, required=False)
    op.execute(
        f"ALTER TABLE sets ADD CONSTRAINT {OWNED} "
        "CHECK ((owner_type = 'company') = (company_id IS NOT NULL)) NOT VALID"
    )

    with op.get_context().autocommit_block():
        op.execute(f"ALTER TABLE sets VALIDATE CONSTRAINT {OWNED}")

    for table, parent, column in CHILDREN:
        add_company_id(op, table, fill(table, parent, column), required=False)

    with op.get_context().autocommit_block():
        for name, table, columns in POSITIONS:
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {name}")
            op.execute(f"CREATE UNIQUE INDEX CONCURRENTLY {name} ON {table} ({columns})")
            op.execute(
                f"ALTER TABLE {table} ADD CONSTRAINT {name} UNIQUE USING INDEX {name} "
                "DEFERRABLE INITIALLY DEFERRED"
            )


def downgrade() -> None:
    for name, table, _ in POSITIONS:
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT {name}")

    for table, _, _ in reversed(CHILDREN):
        op.execute(f"DROP TRIGGER company_from_parent ON {table}")
        drop_company_id(op, table)

    op.execute(f"ALTER TABLE sets DROP CONSTRAINT {OWNED}")
    op.execute("DROP TRIGGER company_from_owner ON sets")
    drop_company_id(op, "sets")
    op.execute("DROP FUNCTION company_from_parent()")
    op.execute("DROP FUNCTION company_from_owner()")
