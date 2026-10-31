import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from testee_common.db.db import one_of

from companies.constants.brand import Theme
from companies.constants.invites import MAX_CANDIDATE_NAME_LENGTH, InviteStatus
from companies.models.base import Base


class CandidateInvite(Base):
    __tablename__ = "candidate_invites"
    __table_args__ = (
        UniqueConstraint("interview_id", "email"),
        # An interview's invites by last change, for the public API's updated_since (migration
        # 0045).
        Index("ix_candidate_invites_interview_updated", "interview_id", "updated_at", "id"),
        # An interview's candidates, newest first.
        Index("ix_candidate_invites_interview_created", "interview_id", "created_at", "id"),
        # A person's invites (their account's deletion and export), and the invites sent before
        # a time (expiry, reminders, retention).
        Index("ix_candidate_invites_email", "email"),
        Index("ix_candidate_invites_sent_at", "sent_at"),
        CheckConstraint(one_of("status", InviteStatus), name="ck_candidate_invites_status"),
        CheckConstraint(one_of("theme", Theme), name="ck_candidate_invites_theme"),
        CheckConstraint("grade BETWEEN 0 AND 100", name="ck_candidate_invites_grade"),
        CheckConstraint("extra_time >= 0", name="ck_candidate_invites_extra_time"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    interview_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interviews.id", ondelete="CASCADE"))
    # The interview's company, kept on the row too (every tenant's row carries it).
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    email: Mapped[str] = mapped_column(String(320))
    # The candidate's name from their verified sign-in, filled once when they start; None until
    # then, or when their sign-in has none.
    name: Mapped[str | None] = mapped_column(String(MAX_CANDIDATE_NAME_LENGTH))
    token: Mapped[str] = mapped_column(String(64), unique=True)
    user_id: Mapped[str | None] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), default=InviteStatus.INVITED)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
    # When the row last changed: a trigger sets it on every update (migration 0045), so the
    # public API's lists can be synced with updated_since.
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # When the invite email was last sent; an invite never started expires INVITE_EXPIRY_DAYS
    # after it.
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    # When the one reminder went out; sending the invite again clears it.
    reminded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Extra time for a candidate who needs it (an accommodation), in percent of each question's
    # time; set before they start.
    extra_time: Mapped[int] = mapped_column(default=0, server_default="0")
    # This candidate's own interview mode, set before they start: True by voice, False by click;
    # None follows the interview's (interviews.voice). Only one apart from the interview's is
    # kept (helpers/candidates.py voice_override).
    voice: Mapped[bool | None]
    # When the candidate's latest start began making their sessions with the extra time and mode
    # above (services/candidate_start.py): from then on neither changes, so their sessions never
    # miss a change saved meanwhile. Cleared when rounds refused that start; None before.
    starting_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # The candidate's final grade, in percent, and whether any integrity signal was recorded:
    # stored when they finish (interview.finished), so the list sorts and filters by them in SQL.
    # None until then.
    grade: Mapped[int | None]
    flagged: Mapped[bool] = mapped_column(default=False, server_default="false")
    # The key of the credits billing set aside for this invite, without the candidate's email:
    # its own, so an email invited again after its invite was removed is held and charged anew.
    hold_key: Mapped[str] = mapped_column(Text(), index=True)
    # Where the company's own platform takes the candidate back once they've finished (the
    # public API's return_url: https, or http on localhost); None for everyone else.
    return_url: Mapped[str | None] = mapped_column(String(2048))
    # Sent by the company's own platform, which knows who the candidate is: the link signs them
    # in as this invite's guest, and testee sends no emails.
    guest: Mapped[bool] = mapped_column(default=False, server_default="false")
    # The theme its pages show (constants/brand.py's Theme), as the API asked; None: the
    # candidate's own.
    theme: Mapped[str | None] = mapped_column(String(8))
    # When the candidate first started, and when they finished; None before (and for candidates
    # from before these were kept).
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # When the candidate confirmed they'd answer on their own, without AI tools or other people:
    # starting requires it. None before they start (and for candidates from before it was asked).
    pledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # When the invite email last bounced or was marked as spam; None when it never did.
    undelivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
