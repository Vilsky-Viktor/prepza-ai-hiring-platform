"""ai_usage takes the code_tags action: generation's job that tags the notation of questions'
examples is recorded and priced like every other AI call. The action CHECK is replaced by one
with the new value, added NOT VALID and validated in its own transaction (every row holds)

Revision ID: 0029
Revises: 0028
Create Date: 2026-10-22
"""

from alembic import op

revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None

NAME = "ck_ai_usage_action"
ACTIONS = (
    "assistant_message",
    "assistant_title",
    "campaign_translation",
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
NEW = ("code_tags",)


def condition(actions: tuple[str, ...]) -> str:
    return "action IN (" + ", ".join(f"'{action}'" for action in sorted(actions)) + ")"


def replace(actions: tuple[str, ...]) -> None:
    op.execute(f"ALTER TABLE ai_usage DROP CONSTRAINT {NAME}")
    op.execute(f"ALTER TABLE ai_usage ADD CONSTRAINT {NAME} CHECK ({condition(actions)}) NOT VALID")

    with op.get_context().autocommit_block():
        op.execute(f"ALTER TABLE ai_usage VALIDATE CONSTRAINT {NAME}")


def upgrade() -> None:
    replace(ACTIONS + NEW)


def downgrade() -> None:
    op.execute("DELETE FROM ai_usage WHERE action IN ('code_tags')")
    replace(ACTIONS)
