from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from testee_common.db.db import one_of

from notifications.constants.slack import SlackStatus
from notifications.models.base import Base


class SlackConnection(Base):
    """A company's Slack channel: its notifications of the kinds it chose are posted there."""

    __tablename__ = "slack_connections"
    __table_args__ = (
        CheckConstraint(
            one_of("status", (SlackStatus.CONNECTED, SlackStatus.BROKEN)),
            name="ck_slack_connections_status",
        ),
    )

    company_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    # The workspace and channel, as Slack names them, to show.
    team: Mapped[str] = mapped_column(Text())
    channel: Mapped[str] = mapped_column(Text())
    # The channel's web hook and the app's token (to revoke it), sealed with SLACK_ENCRYPTION_KEY.
    webhook: Mapped[str] = mapped_column(Text)
    token: Mapped[str] = mapped_column(Text)
    # The token's SHA-256, to find the other companies on its workspace without unsealing every
    # token; empty only for a token sealed with a key no longer set.
    token_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    kinds: Mapped[list] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(16))
    created_by: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )


class SlackPost(Base):
    """A notification posted (or being posted) to its company's Slack channel, so a retried
    event posts it once; the bell's own record is Received. Pruned after KEEP_DAYS."""

    __tablename__ = "slack_posts"

    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
