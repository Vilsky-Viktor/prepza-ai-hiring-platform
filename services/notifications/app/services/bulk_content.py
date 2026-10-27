# What each kind of bulk send is: its email to one user, and for a legal notice its notification
# in the bell. Who it goes to: services/audiences.py.
import uuid

from prepza_common.events.notifications import EVERYONE, Recipient

from app.config.settings import settings
from app.constants.bulk import CAMPAIGN_KINDS, BulkKind
from app.helpers.campaign_emails import campaign_email
from app.helpers.member_emails import legal_email
from app.models.email import Email
from app.services.feed import announce
from app.storage import campaigns, notifications


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

        if await notifications.add(f"{kind}:{version}:{recipient_id}", event):
            await announce(str(recipient), recipient_id)


async def campaign_texts(about: str) -> tuple[str | None, dict[str, dict]] | None:
    """A campaign's button link and texts by language; None once it's deleted."""
    found = await campaigns.get(uuid.UUID(about))

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
