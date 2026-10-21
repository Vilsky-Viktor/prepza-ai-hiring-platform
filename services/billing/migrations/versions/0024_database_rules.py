"""Billing's schema to the database rules: the database refuses values outside each closed set
(owner types, reasons, statuses, currencies, AI actions) and amounts out of range (reserved
credits below zero, an empty hold or purchase), each CHECK added NOT VALID then validated in its
own transaction; ai_usage keeps each call's cost exactly (`cost`, numeric) next to the float
`cost_usd`, filled in batches; the AI model's name and a limit hit's `what` become text; a
buyer's purchases get an index, and the one the unique constraint covers goes.
ck_ai_usage_service stays NOT VALID (it guards every new row) while rows a test once stored
age out of the 13-month retention

Revision ID: 0024
Revises: 0023
Create Date: 2026-10-22
"""

from alembic import op

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None

# (table, name, condition), as the models build them on 2026-10-22.
CHECKS = (
    (
        "ai_usage",
        "ck_ai_usage_action",
        "action IN ('assistant_message', 'assistant_title', 'campaign_translation', 'embeddings', 'help_chat', 'interview_generation', 'key_check_batch', 'news_translation', 'quality_patterns', 'question_regeneration', 'question_verify', 'sample_key_check', 'template_generation', 'template_question_regeneration', 'transcription')",
    ),
    ("ai_usage", "ck_ai_usage_category", "category IN ('paid', 'unpaid', 'no_company', 'prepza')"),
    ("ai_usage", "ck_ai_usage_outcome", "outcome IN ('ok', 'cut', 'failed')"),
    ("ai_usage", "ck_ai_usage_service", "service IN ('assistant', 'generation', 'rounds')"),
    ("auto_top_ups", "ck_auto_top_ups_owner_type", "owner_type IN ('company')"),
    ("auto_top_ups", "ck_auto_top_ups_threshold", "threshold >= 0"),
    ("currency_choices", "ck_currency_choices_owner_type", "owner_type IN ('company', 'user')"),
    (
        "entries",
        "ck_entries_currency",
        "currency IN ('USD', 'EUR', 'GBP', 'CAD', 'AUD', 'ILS', 'PLN', 'JPY', 'KRW', 'TWD', 'HKD', 'CHF', 'THB', 'SGD', 'INR')",
    ),
    ("entries", "ck_entries_owner_type", "owner_type IN ('company')"),
    (
        "entries",
        "ck_entries_reason",
        "reason IN ('welcome', 'topup', 'candidate', 'refund', 'chargeback', 'chargeback_reversed', 'referral', 'referral_reversed', 'adjustment')",
    ),
    ("holds", "ck_holds_amount", "amount > 0"),
    ("holds", "ck_holds_owner_type", "owner_type IN ('company')"),
    ("holds", "ck_holds_reason", "reason IN ('candidate')"),
    ("holds", "ck_holds_status", "status IN ('open', 'charged', 'released')"),
    (
        "purchases",
        "ck_purchases_currency",
        "currency IN ('USD', 'EUR', 'GBP', 'CAD', 'AUD', 'ILS', 'PLN', 'JPY', 'KRW', 'TWD', 'HKD', 'CHF', 'THB', 'SGD', 'INR')",
    ),
    ("purchases", "ck_purchases_quantity", "quantity > 0"),
    ("referrals", "ck_referrals_owner_type", "owner_type IN ('company')"),
    ("wallets", "ck_wallets_owner_type", "owner_type IN ('company')"),
    ("wallets", "ck_wallets_reserved", "reserved >= 0"),
)
NOT_YET = ("ck_ai_usage_service",)
TEXT_COLUMNS = (("ai_usage", "model", 64), ("limit_hits", "what", 64))
BACKFILL = (
    "UPDATE ai_usage SET cost = cost_usd::numeric WHERE id IN "
    "(SELECT id FROM ai_usage WHERE cost IS NULL LIMIT 1000)"
)


def upgrade() -> None:
    op.execute("ALTER TABLE ai_usage ADD COLUMN cost numeric(20, 12)")

    for table, column, _ in TEXT_COLUMNS:
        # migration-check: varchar to text is binary coercible: no rewrite, no index rebuild
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE text")

    for table, name, condition in CHECKS:
        op.execute(f"ALTER TABLE {table} ADD CONSTRAINT {name} CHECK ({condition}) NOT VALID")

    with op.get_context().autocommit_block():
        for table, name, _ in CHECKS:
            if name not in NOT_YET:
                op.execute(f"ALTER TABLE {table} VALIDATE CONSTRAINT {name}")

        # Each batch its own transaction (autocommit), until none is left.
        while op.get_bind().exec_driver_sql(BACKFILL).rowcount:
            pass

        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_purchases_buyer_id")
        op.execute(
            "CREATE INDEX CONCURRENTLY ix_purchases_buyer_id ON purchases (buyer_id, created_at)"
        )
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_purchases_transaction_id")


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_purchases_transaction_id "
            "ON purchases (transaction_id)"
        )
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_purchases_buyer_id")

    for table, name, _ in CHECKS:
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT {name}")

    for table, column, length in TEXT_COLUMNS:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE varchar({length})")

    op.execute("ALTER TABLE ai_usage DROP COLUMN cost")
