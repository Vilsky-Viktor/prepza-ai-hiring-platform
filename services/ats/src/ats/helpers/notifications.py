from prepza_common.events.notifications import NotificationKind, Recipient, notification

from ats.constants.ats import ATS_NAMES
from ats.constants.notifications import ATS_LINK


def ats_not_invited(
    company_id,
    provider: str,
    ats: str,
    title: str | None,
    email: str,
    reason: str,
    name: str | None = None,
) -> dict:
    """A candidate the ATS named `ats` sent who wasn't invited (with their name, if it sent
    one), and why; that ATS's page, which the notification opens, retries. Several at once add up to one notification."""
    return notification(
        Recipient.COMPANY,
        company_id,
        NotificationKind.ATS_NOT_INVITED,
        ATS_LINK.format(company_id=company_id, provider=provider),
        ats=ats,
        email=email,
        title=title,
        reason=reason,
        **({"candidate_name": name} if name else {}),
    )


def ats_cannot_write(company_id, provider: str, ats: str) -> dict:
    """The ATS named `ats` refuses the results written back: the key can't write. Its page,
    which the notification opens, reconnects."""
    return notification(
        Recipient.COMPANY,
        company_id,
        NotificationKind.ATS_CANNOT_WRITE,
        ATS_LINK.format(company_id=company_id, provider=provider),
        ats=ats,
    )


def connection_broken(company_id, provider: str) -> dict:
    """The company's ATS connection stopped working: its page, which the notification opens,
    reconnects it."""
    return notification(
        Recipient.COMPANY,
        company_id,
        NotificationKind.CONNECTION_BROKEN,
        ATS_LINK.format(company_id=company_id, provider=provider),
        name=ATS_NAMES[provider],
        integration="ats",
    )
