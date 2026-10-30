import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column

from rounds.models.base import Base


class VoiceClip(Base):
    """A text read aloud once by OpenAI's text-to-speech (Ogg Opus) and played to every candidate
    who hears it: a voice interview's question with its options, or one of the interviewer's own
    phrases. Company content or fixed text, never a candidate's voice or words. Deleted with its
    company, and once nobody has played it for CLIP_UNUSED_DAYS (jobs: voice-clips)."""

    __tablename__ = "voice_clips"
    __table_args__ = (Index("ix_voice_clips_used_at", "used_at"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # What was read, by whom and how (helpers/voice_speech.py clip_key): the same text in the same
    # voice is one clip.
    key: Mapped[str] = mapped_column(String(64), unique=True)
    # The company whose question it reads; None for the interviewer's phrases.
    company_id: Mapped[uuid.UUID | None] = mapped_column(index=True)
    audio: Mapped[bytes] = mapped_column(LargeBinary)
    # How long it plays.
    seconds: Mapped[float]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # When a candidate last played it, at most CLIP_TOUCH_HOURS out of date.
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
