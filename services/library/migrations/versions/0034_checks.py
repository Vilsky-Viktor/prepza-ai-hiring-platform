"""The database refuses what the code never writes: a value outside its closed set (statuses,
kinds, roles), and numbers out of range (percentages, votes, counters). Each CHECK is added NOT
VALID, which takes its table's lock only for a moment, then validated in its own transaction,
which reads the rows without blocking writes

Revision ID: 0034
Revises: 0033
Create Date: 2026-10-21
"""

from alembic import op

revision = "0034"
down_revision = "0033"
branch_labels = None
depends_on = None

# (table, name, condition), as the models build them on 2026-10-21.
CHECKS = (
    ("email_consents", "ck_email_consents_basis", "basis IN ('choice', 'soft_opt_in')"),
    (
        "email_consents",
        "ck_email_consents_setting",
        "setting IN ('candidate_finished', 'invite_undelivered', 'ats_not_invited', 'interview_ready', 'reminders', 'updates', 'promotions')",
    ),
    (
        "email_consents",
        "ck_email_consents_source",
        "source IN ('sign_in', 'settings', 'unsubscribe', 'admin')",
    ),
    ("question_ratings", "ck_question_ratings_value", "value IN (-1, 1)"),
    (
        "question_reports",
        "ck_question_reports_reason",
        "reason IN ('wrong_answer', 'unclear', 'hard_to_read', 'off_topic', 'other')",
    ),
    ("question_reports", "ck_question_reports_status", "status IN ('open')"),
    (
        "question_revisions",
        "ck_question_revisions_flag",
        "flag IN ('wrong_key', 'rewrite', 'weak_options')",
    ),
    (
        "question_stats",
        "ck_question_stats_counts",
        "answers >= 0 AND strong_answers >= 0 AND weak_answers >= 0 AND timeouts >= 0",
    ),
    (
        "question_stats",
        "ck_question_stats_flag",
        "flag IN ('wrong_key', 'rewrite', 'weak_options')",
    ),
    ("questions", "ck_questions_pool", "pool IN ('practice', 'company')"),
    ("sets", "ck_sets_kind", "kind IN ('interview', 'template')"),
    ("sets", "ck_sets_level", "level IN ('basic', 'medium', 'hard')"),
    ("sets", "ck_sets_owner_type", "owner_type IN ('company', 'platform')"),
)
NOT_YET = ()


def upgrade() -> None:
    for table, name, condition in CHECKS:
        op.execute(f"ALTER TABLE {table} ADD CONSTRAINT {name} CHECK ({condition}) NOT VALID")

    with op.get_context().autocommit_block():
        for table, name, _ in CHECKS:
            if name not in NOT_YET:
                op.execute(f"ALTER TABLE {table} VALIDATE CONSTRAINT {name}")


def downgrade() -> None:
    for table, name, _ in CHECKS:
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT {name}")
