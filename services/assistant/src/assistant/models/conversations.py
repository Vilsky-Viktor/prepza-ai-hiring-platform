import uuid
from datetime import UTC, datetime

from prepza_common.db.db import one_of
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from assistant.constants.chat import Role, Source, Status, ToolState
from assistant.models.base import Base


def now() -> datetime:
    return datetime.now(UTC)


class Conversation(Base):
    """A user's chat with the assistant, about one company (or none)."""

    __tablename__ = "conversations"
    # A user's conversations, the latest first.
    __table_args__ = (
        Index("ix_conversations_user_latest", "user_id", text("updated_at DESC"), "id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(128))
    company_id: Mapped[uuid.UUID | None] = mapped_column(index=True)
    # The first 80 characters of the first message.
    title: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
    )
    # The last message's time: conversations idle longer than the retention are deleted.
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)


class Message(Base):
    """One message: the user's (typed or spoken) or the assistant's answer with its blocks."""

    __tablename__ = "messages"
    # A conversation's messages in order (and its foreign key's index).
    __table_args__ = (
        Index("ix_messages_conversation_order", "conversation_id", "created_at", "id"),
        CheckConstraint(one_of("role", Role), name="ck_messages_role"),
        CheckConstraint(one_of("source", Source), name="ck_messages_source"),
        CheckConstraint(one_of("status", Status), name="ck_messages_status"),
        CheckConstraint("vote IN (-1, 1)", name="ck_messages_vote"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE")
    )
    # "user" or "assistant".
    role: Mapped[str] = mapped_column(String(16))
    # "text" or "voice" (transcribed; the audio itself is never kept).
    source: Mapped[str] = mapped_column(String(8), default="text")
    content: Mapped[str] = mapped_column(Text)
    # What the panel shows under an answer, as references: each block's kind, its items' ids and
    # its links; the items are fetched again when the conversation is opened.
    blocks: Mapped[list] = mapped_column(JSONB, default=list)
    # The page a user's message was asked on: its key, path and the ids it's about; None for an
    # answer, or a message sent from no known page.
    page: Mapped[dict | None] = mapped_column(JSONB)
    # "complete", "cancelled" (stopped, with its partial text) or "failed".
    status: Mapped[str] = mapped_column(String(16), default="complete")
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    # An answer's Langfuse trace, its model calls'; None when Langfuse wasn't set up.
    trace_id: Mapped[str | None] = mapped_column(String(32))
    # The user's thumbs up (1) or down (-1) on an answer; None when there's none.
    vote: Mapped[int | None] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
    )


class ToolCall(Base):
    """A tool an answer used: which, how long it took and how it ended; never its data."""

    __tablename__ = "tool_calls"
    __table_args__ = (CheckConstraint(one_of("state", ToolState), name="ck_tool_calls_state"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), index=True
    )
    tool: Mapped[str] = mapped_column(String(64))
    # The names of the arguments it was called with, never their values.
    arguments: Mapped[list] = mapped_column(JSONB)
    # The service's answer; None when it didn't answer.
    status_code: Mapped[int | None] = mapped_column(Integer)
    duration_ms: Mapped[int] = mapped_column(Integer)
    # No longer kept (other people's data): always None.
    result: Mapped[dict | None] = mapped_column(JSONB)
    # "done" or "failed".
    state: Mapped[str] = mapped_column(String(32), default="done")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
    )
