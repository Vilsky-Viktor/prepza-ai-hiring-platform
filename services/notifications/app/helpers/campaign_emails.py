# The campaign emails: a superadmin's text in the recipient's language, as an optional email
# (the unsubscribe link and headers of its setting).
from prepza_common.constants import DEFAULT_LANGUAGE

from app.constants.bulk import SEND_TAG
from app.constants.unsubscribe import UnsubscribeType
from app.helpers.emails import optional_email
from app.helpers.markdown import markdown_plain
from app.helpers.member_emails import recipient_data
from app.helpers.rendering import email_language
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
    chosen = texts_in(texts, recipient["language"])
    template = EMAILS[email_language(kind, recipient["language"])][kind]
    data = {
        **recipient_data(recipient),
        "subject": chosen["subject"],
        "preheader": markdown_plain(chosen["text"])[:PREHEADER_LENGTH],
        "button": chosen["button"] if link and chosen["button"] else template["open_site"],
    }
    email = optional_email(
        kind,
        data,
        site_url.rstrip("/") + (link or "/"),
        site_url,
        secret,
        recipient["user_id"],
        UnsubscribeType(kind),
        markdown=chosen["text"],
    )

    if send_id is not None:
        email.tags[SEND_TAG] = send_id

    return email
