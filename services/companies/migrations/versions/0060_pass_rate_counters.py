"""Pass rates read from counters kept per interview (interview_results) instead of counting every
finished invite on each page: finished (candidates finished with a grade), passed (of them, at or
above the pass mark) and grade_total (their grades added up, for the average). A trigger keeps
them in the same transaction as an invite's change of status, grade or interview, and another
recounts `passed` when the pass mark changes. A table of their own, so the counts don't touch
interviews.updated_at, which the public API syncs by. Filled once here, a batch of interviews at
a time

Revision ID: 0060
Revises: 0059
Create Date: 2026-10-22
"""

import sqlalchemy as sa
from alembic import op

revision = "0060"
down_revision = "0059"
branch_labels = None
depends_on = None

# An invite counts once finished with a grade; each change takes its old row off and adds its new.
INVITE_COUNTS = """
CREATE FUNCTION count_invite() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP <> 'INSERT' AND OLD.status = 'finished' AND OLD.grade IS NOT NULL THEN
        UPDATE interview_results r SET finished = finished - 1,
            passed = passed - (OLD.grade >= i.pass_mark)::int,
            grade_total = grade_total - OLD.grade
        FROM interviews i WHERE i.id = OLD.interview_id AND r.interview_id = i.id;
    END IF;

    IF TG_OP <> 'DELETE' AND NEW.status = 'finished' AND NEW.grade IS NOT NULL THEN
        INSERT INTO interview_results AS r (interview_id, company_id, finished, passed, grade_total)
        SELECT i.id, i.company_id, 1, (NEW.grade >= i.pass_mark)::int, NEW.grade
        FROM interviews i WHERE i.id = NEW.interview_id
        ON CONFLICT (interview_id) DO UPDATE SET finished = r.finished + 1,
            passed = r.passed + excluded.passed, grade_total = r.grade_total + excluded.grade_total;
    END IF;

    RETURN NULL;
END $$
"""
PASS_MARK = """
CREATE FUNCTION recount_passed() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    UPDATE interview_results SET passed = (
        SELECT count(*) FROM candidate_invites
        WHERE interview_id = NEW.id AND status = 'finished' AND grade >= NEW.pass_mark
    ) WHERE interview_id = NEW.id;
    RETURN NULL;
END $$
"""
FILL = """
INSERT INTO interview_results (interview_id, company_id, finished, passed, grade_total)
SELECT n.id, n.company_id, count(*), count(*) FILTER (WHERE v.grade >= n.pass_mark), sum(v.grade)
FROM interviews n JOIN candidate_invites v ON v.interview_id = n.id
WHERE v.status = 'finished' AND v.grade IS NOT NULL
    AND n.id IN (SELECT id FROM interviews WHERE id > %(after)s ORDER BY id LIMIT 500)
GROUP BY n.id
ON CONFLICT (interview_id) DO NOTHING
"""
NEXT = (
    "SELECT id FROM (SELECT id FROM interviews WHERE id > %(after)s ORDER BY id LIMIT 500) p "
    "ORDER BY id DESC LIMIT 1"
)


def upgrade() -> None:
    op.create_table(
        "interview_results",
        sa.Column(
            "interview_id",
            sa.Uuid(),
            sa.ForeignKey("interviews.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "company_id",
            sa.Uuid(),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("finished", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("passed", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("grade_total", sa.BigInteger(), nullable=False, server_default="0"),
        sa.CheckConstraint(
            "passed >= 0 AND passed <= finished AND grade_total >= 0",
            name="ck_interview_results_counts",
        ),
        sa.Index("ix_interview_results_finished", sa.text("finished DESC"), "interview_id"),
    )
    op.execute(INVITE_COUNTS)
    op.execute(PASS_MARK)
    op.execute(
        "CREATE TRIGGER count_invite "
        "AFTER INSERT OR DELETE OR UPDATE OF status, grade, interview_id ON candidate_invites "
        "FOR EACH ROW EXECUTE FUNCTION count_invite()"
    )
    op.execute(
        "CREATE TRIGGER recount_passed AFTER UPDATE OF pass_mark ON interviews "
        "FOR EACH ROW WHEN (OLD.pass_mark IS DISTINCT FROM NEW.pass_mark) "
        "EXECUTE FUNCTION recount_passed()"
    )

    with op.get_context().autocommit_block():
        bind = op.get_bind()
        after = "00000000-0000-0000-0000-000000000000"

        # A batch of interviews at a time, each its own transaction.
        while after is not None:
            bind.exec_driver_sql(FILL, {"after": after})
            after = bind.exec_driver_sql(NEXT, {"after": after}).scalar()


def downgrade() -> None:
    op.execute("DROP TRIGGER recount_passed ON interviews")
    op.execute("DROP TRIGGER count_invite ON candidate_invites")
    op.execute("DROP FUNCTION recount_passed()")
    op.execute("DROP FUNCTION count_invite()")
    op.drop_table("interview_results")
