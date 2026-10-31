# What each kind of bulk send is: its email to one user, and for a legal notice its notification
# in the bell. Who it goes to: services/audiences.py.
import uuid

from testee_common.events.notifications import EVERYONE, Recipient

from notifications.config import settings
from notifications.constants.bulk import CAMPAIGN_KINDS, BulkKind
from notifications.core.db import Session
from notifications.helpers.campaign_emails import campaign_email
from notifications.helpers.member_emails import legal_email
from notifications.models.email import Email
from notifications.repositories import campaigns
from notifications.services import notices
from notifications.services.feed import announce


def document_of(kind: str) -> str:
    """A legal notice's document: "legal_terms" is about the terms."""
    return kind.removeprefix("legal_")


async def legal_in_bell(kind: str, version: str, user_ids: list[str]) -> None:
    """The notice in the bell too, opening the new version: one notification for everyone, or
    for the DPA one for each company owner and admin. Stored once each, however often it's
    asked (the key), and announced to the open tabs."""
    data = {"date": version}

    if kind == BulkKind.LEGAL_DPA:
        targets = [(Recipient.USER, user_id) for user_id in user_ids]
    else:
        targets = [(Recipient.ALL, EVERYONE)]

    for recipient, recipient_id in targets:
        event = {
            "recipient": str(recipient),
            "recipient_id": recipient_id,
            "kind": kind,
            "link": f"/{document_of(kind)}",
            "data": data,
        }

        if await notices.store(f"{kind}:{version}:{recipient_id}", event):
            await announce(str(recipient), recipient_id)


async def campaign_texts(about: str) -> tuple[str | None, dict[str, dict]] | None:
    """A campaign's button link and texts by language; None once it's deleted."""
    async with Session() as session:
        found = await campaigns.get(session, uuid.UUID(about))

    if found is None:
        return None

    campaign, texts = found

    return campaign.link, texts


def email_for(kind: str, about: str, send_id: str, recipient: dict, campaign) -> Email:
    """The send's email to one user; `campaign` is campaign_texts() for a campaign."""
    if kind in CAMPAIGN_KINDS:
        link, texts = campaign

        return campaign_email(
            kind, recipient, texts, link, settings.site_url, settings.email_link_secret, send_id
        )

    return legal_email(recipient, document_of(kind), about, settings.site_url)
