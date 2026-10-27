from prepza_common.events.notifications import EVERYONE, NotificationKind, Recipient, notification

from app.constants.quality import COMPANY_INTERVIEWS_LINK
from app.constants.sets import OwnerType


def question_notification(question_set, topic: str, kind: NotificationKind) -> dict | None:
    """For every member of the company that owns the interview. It names the question's topic,
    as a question can be long. The library doesn't know which interview a set belongs to, so a
    company gets its list. None for a template's question: prepza owns it, and no company's
    members are told."""
    if question_set.owner_type != OwnerType.COMPANY:
        return None

    return notification(
        Recipient.COMPANY,
        question_set.owner_id,
        kind,
        COMPANY_INTERVIEWS_LINK.format(company_id=question_set.owner_id),
        title=question_set.title,
        topic=topic,
    )


def news_notification(post) -> dict:
    """One notification for everyone, opening the post on the news page; the bell shows its
    title in each user's language (notifications asks for it)."""
    return notification(
        Recipient.ALL,
        EVERYONE,
        NotificationKind.NEWS,
        f"/news#{post.id}",
        key=str(post.id),
        news_id=str(post.id),
        title=post.title,
    )
