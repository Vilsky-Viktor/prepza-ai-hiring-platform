"""The database refuses what the code never writes: a value outside its closed set (statuses,
kinds, roles), and numbers out of range (percentages, votes, counters). Each CHECK is added NOT
VALID, which takes its table's lock only for a moment, then validated in its own transaction,
which reads the rows without blocking writes; ck_notifications_kind stays NOT VALID (it guards
every new row) while rows of kinds no longer sent age out of the 90-day retention

Revision ID: 0015
Revises: 0014
Create Date: 2026-10-21
"""

from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None

# (table, name, condition), as the models build them on 2026-10-21.
CHECKS = (
    (
        "bulk_recipients",
        "ck_bulk_recipients_status",
        "status IN ('pending', 'sent', 'skipped', 'failed')",
    ),
    (
        "bulk_sends",
        "ck_bulk_sends_kind",
        "kind IN ('legal_terms', 'legal_privacy', 'legal_dpa', 'updates', 'promotions')",
    ),
    ("campaigns", "ck_campaigns_kind", "kind IN ('updates', 'promotions')"),
    (
        "notifications",
        "ck_notifications_kind",
        "kind IN ('question_flagged', 'question_fixed', 'referral_rewarded', 'auto_top_up_charged', 'auto_top_up_failed', 'candidate_finished', 'invite_undelivered', 'interview_ready', 'interview_cancelled', 'ats_not_invited', 'ats_cannot_write', 'connection_broken', 'webhook_stopped', 'member_joined', 'ownership_received', 'verification_approved', 'verification_declined', 'news', 'legal_terms', 'legal_privacy', 'legal_dpa')",
    ),
    ("notifications", "ck_notifications_recipient", "recipient IN ('user', 'company', 'all')"),
    (
        "sent_emails",
        "ck_sent_emails_kind",
        "kind IN ('digest', 'low_credits', 'no_candidates', 'review_waiting')",
    ),
    ("slack_connections", "ck_slack_connections_status", "status IN ('connected', 'broken')"),
    (
        "suppressed_addresses",
        "ck_suppressed_addresses_reason",
        "reason IN ('bounced', 'complained')",
    ),
)
# Validated once older rows are gone (see above).
NOT_YET = ("ck_notifications_kind",)


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
