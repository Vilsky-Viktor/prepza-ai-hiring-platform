import base64
import hashlib
import hmac
import re

from prepza_common.auth.tokens import same_secret
from prepza_common.events.notifications import NotificationKind

from notifications.constants.slack import LINKABLE_DOT, ZERO_WIDTH_SPACE

# Why an ATS candidate wasn't invited, as the message says it.
NOT_INVITED = {
    "credits": "out of credits",
    "limit": "an email limit was reached",
    "paused": "invites are paused",
}


def escaped(text: str) -> str:
    """`text` as Slack shows it, never as markup: a title "<!channel>" doesn't ping anyone, and
    a name like "www.evil-login.com" or an email isn't made a link."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return re.sub(LINKABLE_DOT, "." + ZERO_WIDTH_SPACE, text)


def token_hash(token: str) -> str:
    """A workspace's token as stored to find who else uses it: sealed tokens differ each time,
    while this is the same for the same token. A plain SHA-256 suffices, as Slack's tokens are
    long and random."""
    return hashlib.sha256(token.encode()).hexdigest()


def signed_state(secret: str, company_id: str, user_id: str, expires: int, nonce: str) -> str:
    """The "Add to Slack" trip's state: the company and who started it, until `expires` (Unix
    seconds), signed so the callback can trust it; `nonce` lets the callback take it once."""
    payload = f"{company_id}|{user_id}|{expires}|{nonce}"
    signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

    return base64.urlsafe_b64encode(f"{payload}|{signature}".encode()).decode()


def read_state(secret: str, state: str, now: int) -> tuple[str, str, str] | None:
    """The company, user and nonce a state names, if it's ours and not expired."""
    try:
        company_id, user_id, expires, nonce, signature = (
            base64.urlsafe_b64decode(state.encode()).decode().split("|")
        )
    except ValueError:
        return None

    payload = f"{company_id}|{user_id}|{expires}|{nonce}"
    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

    if not same_secret(signature, expected) or int(expires) < now:
        return None

    return company_id, user_id, nonce


def message(event: dict, site: str) -> dict | None:
    """A notification as a Slack message (in English, like the bell's English text), linking to
    where it points; None for a kind Slack doesn't get."""
    data = event.get("data") or {}
    # An interview without its title yet is named without quotes.
    named = f"“{data['title']}”" if data.get("title") else "an interview"
    # "Name (email)" once the candidate's name is known.
    candidate = (
        f"{data['candidate_name']} ({data.get('email')})"
        if data.get("candidate_name")
        else data.get("email")
    )
    texts = {
        NotificationKind.CANDIDATE_FINISHED: f"{candidate} finished {named}"
        + (f": {data['grade']}%." if data.get("grade") is not None else "."),
        NotificationKind.ATS_NOT_INVITED: f"{candidate} from {data.get('ats', 'your ATS')}"
        f" wasn't invited to {named}: "
        f"{NOT_INVITED.get(data.get('reason'), 'something went wrong')}.",
        NotificationKind.INVITE_UNDELIVERED: f"The invite to {candidate} for {named}"
        " wasn't delivered.",
        NotificationKind.INTERVIEW_READY: f"The interview {named} is ready."
        if data.get("title")
        else "An interview is ready.",
        NotificationKind.AUTO_TOP_UP_CHARGED: f"Automatic top-up added {data.get('credits')}"
        " credits.",
        NotificationKind.AUTO_TOP_UP_FAILED: "Automatic top-up couldn't charge the card. Top up"
        " to keep your balance going.",
    }
    text = texts.get(event.get("kind"))

    if text is None:
        return None

    # A finished candidate opens their results; others, the notification's page. Only the values
    # people wrote are escaped: the links are ours.
    link = data.get("candidate_link") or event.get("link", "")

    shown = escaped(text)

    # Plain text, which Slack formats in no way (no *bold*, _italics_ or links in what people
    # wrote), and our own link as a button.
    return {
        "text": shown,
        "blocks": [
            {"type": "section", "text": {"type": "plain_text", "text": shown, "emoji": False}},
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Open in prepza"},
                        "url": f"{site}{link}",
                    }
                ],
            },
        ],
    }
