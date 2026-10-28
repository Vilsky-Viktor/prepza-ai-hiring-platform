import uuid
from datetime import date, datetime

from prepza_common.config.constants import MAX_NEWS_TITLE_LENGTH
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from site_content.models.base import Base


class News(Base):
    """A post on the news page, written in English by a superadmin."""

    __tablename__ = "news"
    # The page lists posts newest first (repositories/news.py).
    __table_args__ = (Index("ix_news_published_on_created_at", "published_on", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(MAX_NEWS_TITLE_LENGTH))
    text: Mapped[str] = mapped_column(Text)
    published_on: Mapped[date]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class NewsTranslation(Base):
    """A post in one other language, from generation. A language without one shows the English
    post; changing the post's title or text deletes its translations."""

    __tablename__ = "news_translations"

    news_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("news.id", ondelete="CASCADE"), primary_key=True
    )
    language: Mapped[str] = mapped_column(String(8), primary_key=True)
    title: Mapped[str] = mapped_column(String(MAX_NEWS_TITLE_LENGTH))
    text: Mapped[str] = mapped_column(Text)
