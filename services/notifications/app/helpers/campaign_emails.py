# The campaign emails: a superadmin's text in the recipient's language, as an optional email
# (the unsubscribe link and headers of its setting), or for an important notice as a service
# email (from the service sender, nothing to unsubscribe from, its footer saying why).
from prepza_common.config.constants import DEFAULT_LANGUAGE

from app.constants.bulk import OPTIONAL_KINDS, SEND_TAG
from app.constants.unsubscribe import UnsubscribeType
from app.constants.webhooks import ID_TAG, KIND_TAG
from app.helpers.emails import optional_email
from app.helpers.markdown import markdown_plain
from app.helpers.member_emails import recipient_data
from app.helpers.rendering import email_language, render
from app.models.email import Email
from app.templates.emails import EMAILS

# The preheader (the line inboxes show after the subject) is the text's start, this long.
PREHEADER_LENGTH = 120


def texts_in(texts: dict[str, dict], language: str | None) -> dict:
    """The campaign's texts in `language`, or in English until it has them."""
    return texts.get(language) or texts[DEFAULT_LANGUAGE]


def campaign_email(
    kind: str,
    recipient: dict,
    texts: dict[str, dict],
    link: str | None,
    site_url: str,
    secret: str,
    send_id: str | None = None,
) -> Email:
    """The campaign to one user: its subject as the heading, its text (formatted, as its
    editor wrote it), and its button to `link` (a page on the site), or to the site when it has
    none. Tagged with the send, so a spam complaint counts against it; a test has no send."""
    if kind in OPTIONAL_KINDS:
        email = optional_campaign_email(kind, recipient, texts, link, site_url, secret)
    else:
        email = render(
            kind,
            campaign_data(kind, recipient, texts, link),
            site_url.rstrip("/") + (link or "/"),
            markdown=texts_in(texts, recipient["language"])["text"],
        )
        email.tags = {KIND_TAG: kind, ID_TAG: recipient["user_id"]}

    if send_id is not None:
        email.tags[SEND_TAG] = send_id

    return email


def campaign_data(kind: str, recipient: dict, texts: dict[str, dict], link: str | None) -> dict:
    """What fills the campaign's template in the recipient's language."""
    chosen = texts_in(texts, recipient["language"])
    template = EMAILS[email_language(kind, recipient["language"])][kind]

    return {
        **recipient_data(recipient),
        "subject": chosen["subject"],
        "preheader": markdown_plain(chosen["text"])[:PREHEADER_LENGTH],
        "button": chosen["button"] if link and chosen["button"] else template["open_site"],
    }


def optional_campaign_email(
    kind: str, recipient: dict, texts: dict[str, dict], link: str | None, site_url: str, secret: str
) -> Email:
    """A product update or an offer, with the unsubscribe link and headers of its setting."""
    return optional_email(
        kind,
        campaign_data(kind, recipient, texts, link),
        site_url.rstrip("/") + (link or "/"),
        site_url,
        secret,
        recipient["user_id"],
        UnsubscribeType(kind),
        markdown=texts_in(texts, recipient["language"])["text"],
    )
