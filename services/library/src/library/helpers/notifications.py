from prepza_common.events.notifications import NotificationKind, Recipient, notification

from library.constants.quality import COMPANY_INTERVIEWS_LINK
from library.constants.sets import OwnerType


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
