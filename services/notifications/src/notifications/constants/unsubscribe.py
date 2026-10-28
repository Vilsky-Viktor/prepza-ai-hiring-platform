from enum import StrEnum

from prepza_common.events.notifications import NotificationKind


class UnsubscribeType(StrEnum):
    """What an unsubscribe link stops. A user's optional emails: one kind of the activity digest,
    the whole digest, reminders, product updates or offers. A candidate's emails, sent on a
    company's behalf: the reminders for one invite, or every email from that company."""

    CANDIDATE_FINISHED = NotificationKind.CANDIDATE_FINISHED.value
    INVITE_UNDELIVERED = NotificationKind.INVITE_UNDELIVERED.value
    ATS_NOT_INVITED = NotificationKind.ATS_NOT_INVITED.value
    INTERVIEW_READY = NotificationKind.INTERVIEW_READY.value
    DIGEST = "digest"
    REMINDERS = "reminders"
    UPDATES = "updates"
    PROMOTIONS = "promotions"
    INVITE_REMINDERS = "invite_reminders"
    COMPANY = "company"


DIGEST_KINDS = [
    UnsubscribeType.CANDIDATE_FINISHED,
    UnsubscribeType.INVITE_UNDELIVERED,
    UnsubscribeType.ATS_NOT_INVITED,
    UnsubscribeType.INTERVIEW_READY,
]

# The email settings (accounts) each of a user's types turns off; the digest is all its kinds.
USER_SETTINGS = {
    **{kind: [kind.value] for kind in DIGEST_KINDS},
    UnsubscribeType.DIGEST: [kind.value for kind in DIGEST_KINDS],
    UnsubscribeType.REMINDERS: ["reminders"],
    UnsubscribeType.UPDATES: ["updates"],
    UnsubscribeType.PROMOTIONS: ["promotions"],
}

# What a candidate's token names: their address (as its keyed hash, since links end up in request
# logs; a plain SHA-256 in links sent before, without "keyed"), the company, and for reminders the
# invite.
CANDIDATE_FIELDS = {
    UnsubscribeType.INVITE_REMINDERS: ("address", "company_id", "company", "invite_id"),
    UnsubscribeType.COMPANY: ("address", "company_id", "company"),
}

# Keeps these signatures apart from anything else the secret might ever sign.
TOKEN_PURPOSE = b"unsubscribe:"

# Where links point: the page that asks to confirm, the API that one-click mail clients post to
# (RFC 8058), and the user's email settings.
PAGE_PATH = "/unsubscribe?token={token}"
ONE_CLICK_PATH = "/api/notifications/unsubscribe/{token}"
SETTINGS_PATH = "/settings"
ONE_CLICK_BODY = "List-Unsubscribe=One-Click"
