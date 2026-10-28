import uuid
from datetime import UTC, date, datetime

from prepza_common.db.db import one_of
from prepza_common.events.audit_actions import MAX_TARGET_LABEL, AuditAction, AuditGroup, TargetKind
from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from companies.constants.audit import VIA_API, VIA_ATS, VIAS
from companies.models.base import Base


class AuditEvent(Base):
    """A member's action in a company, for its action log: who took it, what (its group, for the
    log's filter), on what, when, and through what (via). Deleted with the company."""

    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_company_id_created_at", "company_id", "created_at"),
        Index(
            "ix_audit_events_company_id_user_id_created_at", "company_id", "user_id", "created_at"
        ),
        Index("ix_audit_events_company_id_group_created_at", "company_id", "group", "created_at"),
        # A person's entries (their account's export and deletion).
        Index("ix_audit_events_user_id", "user_id"),
        # A member's views of a candidate's results: one row a day (UTC), the latest view's.
        Index(
            "uq_audit_events_results_viewed_day",
            "company_id",
            "user_id",
            "target_id",
            "day",
            unique=True,
            postgresql_where=text("action = 'results_viewed'"),
        ),
        CheckConstraint(one_of("action", AuditAction), name="ck_audit_events_action"),
        CheckConstraint(one_of('"group"', AuditGroup), name="ck_audit_events_group"),
        CheckConstraint(one_of("target_kind", TargetKind), name="ck_audit_events_target_kind"),
        CheckConstraint(one_of("via", (*VIAS, VIA_API, VIA_ATS)), name="ck_audit_events_via"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(64))
    # The action's group (AuditGroup), what the log's action filter looks up; always set, though
    # nullable so code rolled back to before it still records.
    group: Mapped[str | None] = mapped_column(String(32))
    # What it was about (TargetKind) and its id: a candidate's invite, an interview, a member, the
    # company, an API key, a web hook or an integration.
    target_kind: Mapped[str | None] = mapped_column(String(32))
    target_id: Mapped[uuid.UUID | None]
    # What isn't a person, as it was named then (an interview's title, an ATS's name, a web
    # hook's host), so it still reads once it's gone. People are looked up when the log is read.
    target_label: Mapped[str | None] = mapped_column(String(MAX_TARGET_LABEL))
    # What the action took away: an API key's narrowed permissions. None otherwise.
    removed: Mapped[list[str] | None] = mapped_column(ARRAY(String(64)))
    # What it was recorded through when not a person in the app: "assistant" (VIA_ASSISTANT)
    # when the in-app assistant read for the user, "mcp" (VIA_MCP) when an AI app they connected
    # did. None otherwise.
    via: Mapped[str | None] = mapped_column(String(32))
    # Through an AI agent signed in with an API key: the key (the api service's). None otherwise.
    key_id: Mapped[uuid.UUID | None]
    # The event another service sent it in (prepza_common.events.audit), so a redelivery stores it once;
    # None for companies' own.
    event_id: Mapped[str | None] = mapped_column(String(128), unique=True)
    # The UTC day of a results view (only), fixed at its first view that day: what keeps it to
    # one row a member, candidate and day while created_at moves to the latest view.
    day: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
