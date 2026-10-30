"""ai_usage takes the bank_filter action: generation's daily filter of companies' questions
before they join the shared question bank is recorded and priced like every other AI call. The
action CHECK is replaced by one with the new value, added NOT VALID and validated in its own
transaction (every row holds)

Revision ID: 0033
Revises: 0032
Create Date: 2026-10-30
"""

from alembic import op

revision = "0033"
down_revision = "0032"
branch_labels = None
depends_on = None

NAME = "ck_ai_usage_action"
ACTIONS = (
    "assistant_message",
    "assistant_title",
    "campaign_translation",
    "code_tags",
    "embeddings",
    "help_chat",
    "interview_generation",
    "key_check_batch",
    "news_translation",
    "quality_patterns",
    "question_regeneration",
    "question_verify",
    "sample_key_check",
    "template_generation",
    "template_question_regeneration",
    "transcription",
)
NEW = ("bank_filter",)


def condition(actions: tuple[str, ...]) -> str:
    return "action IN (" + ", ".join(f"'{action}'" for action in sorted(actions)) + ")"


def replace(actions: tuple[str, ...]) -> None:
    op.execute("SET lock_timeout = '5s'")
    op.execute(f"ALTER TABLE ai_usage DROP CONSTRAINT {NAME}")
    op.execute(f"ALTER TABLE ai_usage ADD CONSTRAINT {NAME} CHECK ({condition(actions)}) NOT VALID")

    with op.get_context().autocommit_block():
        op.execute(f"ALTER TABLE ai_usage VALIDATE CONSTRAINT {NAME}")


def upgrade() -> None:
    replace(ACTIONS + NEW)


def downgrade() -> None:
    op.execute("DELETE FROM ai_usage WHERE action IN ('bank_filter')")
    replace(ACTIONS)
