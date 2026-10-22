from dataclasses import dataclass, field

from app.constants.email import AUTOMATED_HEADERS


@dataclass
class Email:
    to: str
    subject: str
    html: str
    text: str
    # Sent with the email; Resend's webhooks carry them back.
    tags: dict[str, str] = field(default_factory=dict)
    # Where a reply goes: the visitor who wrote through the contact page, or the member who
    # shared a report; any other email's replies go to prepza's inbox (CONTACT_EMAIL).
    reply_to: str | None = None
    # Headers: Auto-Submitted on every email, and the one-click unsubscribe of optional emails
    # and candidate reminders.
    headers: dict[str, str] = field(default_factory=lambda: dict(AUTOMATED_HEADERS))
    # An email the user may turn off (the digest, reminders): sent from MAIL_FROM_UPDATES.
    optional: bool = False
    # An email to a candidate, sent for a company: from MAIL_FROM_CANDIDATES (helpers/senders.py).
    candidate: bool = False
    # Files sent with it: (file name, base64 content).
    attachments: list[tuple[str, str]] = field(default_factory=list)
