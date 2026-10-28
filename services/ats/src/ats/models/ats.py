import uuid
from datetime import UTC, datetime

from prepza_common.db.db import one_of
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ats.constants.ats import AtsProvider, CandidateStatus, ConnectionStatus, FailReason
from ats.models.base import Base


class AtsConnection(Base):
    """A company's connection to its applicant tracking system: one per company and ATS."""

    __tablename__ = "ats_connections"
    __table_args__ = (
        UniqueConstraint("company_id", "provider"),
        CheckConstraint(one_of("provider", AtsProvider), name="ck_ats_connections_provider"),
        CheckConstraint(one_of("status", ConnectionStatus), name="ck_ats_connections_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # The company, in the companies service.
    # Indexed by the unique (company_id, provider).
    company_id: Mapped[uuid.UUID] = mapped_column()
    provider: Mapped[str] = mapped_column(String(32))
    # What the company sees it connected as (Workable's subdomain).
    account: Mapped[str] = mapped_column(Text())
    # The ATS key, encrypted (helpers/encryption.py); never returned to the browser.
    credentials: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default=ConnectionStatus.CONNECTED)
    # The Workable member results are written back as (comments need an author).
    member_id: Mapped[str | None] = mapped_column(Text())
    # Who connected it: their invites and limits apply to candidates the ATS sends.
    created_by: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
    # When the ATS first refused the results written back while the key still read: the company
    # was told once. Cleared by a reconnect or a write that goes through.
    write_refused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # The interface language of the member who connected it: results go back to the ATS in it.
    language: Mapped[str | None] = mapped_column(String(8))


class AtsJobLink(Base):
    """An ATS job linked to a prepza interview: candidates who reach `stage_id` in that job get
    the interview."""

    __tablename__ = "ats_job_links"
    # Its connection's links are found by this unique constraint's first column.
    __table_args__ = (UniqueConstraint("connection_id", "job_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    connection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ats_connections.id", ondelete="CASCADE")
    )
    # The connection's company, kept on the row too (every tenant's row carries it).
    company_id: Mapped[uuid.UUID] = mapped_column(index=True)
    # The interview, in the companies service: its interview.deleted event removes this row.
    interview_id: Mapped[uuid.UUID] = mapped_column(index=True)
    # The ATS's own ids, and their names as they were when linked.
    job_id: Mapped[str] = mapped_column(String(100))
    job_name: Mapped[str] = mapped_column(Text())
    stage_id: Mapped[str] = mapped_column(String(100))
    stage_name: Mapped[str] = mapped_column(Text())
    # The ATS's notification for this job and stage, cancelled when the link goes.
    subscription_id: Mapped[str | None] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )


class AtsCandidate(Base):
    """A candidate the ATS sent for an interview: one row per candidate and interview, so a
    repeated or simultaneous event invites them once. Kept after an unlink, for writing their
    results back."""

    __tablename__ = "ats_candidates"
    __table_args__ = (
        UniqueConstraint("connection_id", "candidate_id", "interview_id"),
        # A linked job's candidates, oldest first; deleting a job link finds its rows by it too.
        Index("ix_ats_candidates_link_id_created_at", "link_id", "created_at"),
        Index("uq_ats_candidates_invite_id", "invite_id", unique=True),
        # The recovery job's candidates still to invite, its kept results not yet written back,
        # and the companies' candidates who couldn't be invited, each by connection.
        Index(
            "ix_ats_candidates_waiting",
            "connection_id",
            "created_at",
            postgresql_where=text("status IN ('waiting', 'inviting')"),
        ),
        Index(
            "ix_ats_candidates_unreported",
            "connection_id",
            "kept_at",
            postgresql_where=text("result IS NOT NULL AND reported_at IS NULL"),
        ),
        Index(
            "ix_ats_candidates_failed",
            "connection_id",
            "failed_at",
            postgresql_where=text("status = 'failed'"),
        ),
        CheckConstraint(one_of("status", CandidateStatus), name="ck_ats_candidates_status"),
        CheckConstraint(one_of("reason", FailReason), name="ck_ats_candidates_reason"),
        CheckConstraint("attempts >= 0", name="ck_ats_candidates_attempts"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Indexed by the unique (connection_id, candidate_id, interview_id).
    connection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ats_connections.id", ondelete="CASCADE")
    )
    # The connection's company, kept on the row too (every tenant's row carries it).
    company_id: Mapped[uuid.UUID] = mapped_column(index=True)
    # The interview, in the companies service: its interview.deleted event removes this row.
    interview_id: Mapped[uuid.UUID] = mapped_column(index=True)
    link_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ats_job_links.id", ondelete="SET NULL")
    )
    # The ATS's own candidate id, and who they are.
    candidate_id: Mapped[str] = mapped_column(Text())
    email: Mapped[str] = mapped_column(String(320), index=True)
    # Their name as the ATS sent it, passed on with the invite; None when it sent none.
    name: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(16), default=CandidateStatus.WAITING)
    # When an invite was last started (status inviting): one left too long was cut off.
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Why they weren't invited (constants/ats.py FailReason).
    reason: Mapped[str | None] = mapped_column(String(16))
    # When they first couldn't be invited; a retry that fails again keeps it.
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Invites that failed in passing (companies erred or didn't answer), tried again until
    # MAX_INVITE_ATTEMPTS.
    attempts: Mapped[int] = mapped_column(default=0, server_default="0")
    # The candidate's invite, in the companies service.
    # One ATS row per invite (uq_ats_candidates_invite_id): the one whose results go back.
    invite_id: Mapped[uuid.UUID | None] = mapped_column()
    # When their results went back to the ATS: once.
    reported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Their results (companies' candidate.finished event) while the connection is broken or the
    # ATS fails: sent by the recovery job once it works.
    result: Mapped[dict | None] = mapped_column(JSONB)
    # When the results were last kept: the recovery job tries the longest kept first, so results
    # an ATS keeps refusing don't hold up the others.
    kept_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # When writing the results back started: one left this long (STALE_CLAIM_MINUTES) was cut off
    # (the server stopped mid-write), and the recovery job writes them again.
    report_claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        index=True,
    )
