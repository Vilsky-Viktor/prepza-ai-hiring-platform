# In-app notifications (the header's bell). A service that knows something important happened
# publishes NOTIFICATION_REQUESTED; the notifications service stores it and tells the recipients'
# open tabs at once. Only the kinds below exist, so the bell stays free of noise.
import logging
from enum import StrEnum

from prepza_common.config.event_constants import PUBLISH_IN_REQUEST_TIMEOUT_SECONDS
from prepza_common.events import pubsub

logger = logging.getLogger(__name__)

NOTIFICATION_REQUESTED = "notification.requested"
# A deleted news post's notification for everyone is taken back (site publishes it, notifications
# deletes it). In the notification family, so notifications' subscription takes it with the rest.
NEWS_WITHDRAWN = "notification.news_withdrawn"


class NotificationKind(StrEnum):
    # A question in the company's test was flagged, then fixed or replaced by the AI.
    QUESTION_FLAGGED = "question_flagged"
    QUESTION_FIXED = "question_fixed"
    # Someone who came through the owner's referral link topped up.
    REFERRAL_REWARDED = "referral_rewarded"
    # An automatic top-up was turned on (its card saved), charged the card, or couldn't; paused,
    # as the card won't pay until it's updated; and what it charges changes from a day (a new
    # price, announced ahead).
    AUTO_TOP_UP_ON = "auto_top_up_on"
    AUTO_TOP_UP_CHARGED = "auto_top_up_charged"
    AUTO_TOP_UP_FAILED = "auto_top_up_failed"
    AUTO_TOP_UP_PAUSED = "auto_top_up_paused"
    AUTO_TOP_UP_PRICE_CHANGE = "auto_top_up_price_change"
    # Companies: a candidate finished, an invite bounced, an interview is ready or was cancelled.
    CANDIDATE_FINISHED = "candidate_finished"
    INVITE_UNDELIVERED = "invite_undelivered"
    INTERVIEW_READY = "interview_ready"
    INTERVIEW_CANCELLED = "interview_cancelled"
    # A candidate an ATS sent couldn't be invited (credits, limits, the pause).
    ATS_NOT_INVITED = "ats_not_invited"
    # An ATS takes the company's key but refuses the results written back (no write access).
    ATS_CANNOT_WRITE = "ats_cannot_write"
    # An ATS or Slack connection stopped working and needs reconnecting.
    CONNECTION_BROKEN = "connection_broken"
    # Members' new notes on an interview, one notification per member and interview while it's
    # unread (never to the note's author).
    NOTE_ADDED = "note_added"
    # Someone the owner invited joined the company's team.
    MEMBER_JOINED = "member_joined"
    # The owner made this member the company's owner.
    OWNERSHIP_RECEIVED = "ownership_received"
    # A superadmin approved or declined the company's verification.
    VERIFICATION_APPROVED = "verification_approved"
    VERIFICATION_DECLINED = "verification_declined"
    # A news post was published: one notification for everyone (Recipient.ALL).
    NEWS = "news"
    # A legal document's new version applies from a day: everyone gets the terms' and the
    # privacy policy's, companies' owners and admins the DPA's.
    LEGAL_TERMS = "legal_terms"
    LEGAL_PRIVACY = "legal_privacy"
    LEGAL_DPA = "legal_dpa"


# Who a notification is for: one user, every member of a company, or every user (ALL, one row
# that each user's feed shows when it's newer than their account).
class Recipient(StrEnum):
    USER = "user"
    COMPANY = "company"
    ALL = "all"


# The recipient id of the notifications for everyone.
EVERYONE = "everyone"


def notification(
    recipient: Recipient | str,
    recipient_id: str,
    kind: NotificationKind,
    link: str,
    key: str | None = None,
    **data,
) -> dict:
    """The event's data. `link` is the page it opens; `data` fills its text (titles, emails,
    credits), and must hold nothing a recipient shouldn't see. `key` names what it's about (for
    example an invite), for a handler that may run again on a retried event: the notifications
    service stores one notification per key."""
    event = {
        "recipient": str(recipient),
        "recipient_id": str(recipient_id),
        "kind": str(kind),
        "link": link,
        "data": data,
    }

    if key is not None:
        event["key"] = f"{kind}:{key}"

    return event


async def publish_quietly(event: dict) -> None:
    """For a service without an outbox: a lost notification is better than a failed or slow
    request."""
    try:
        await pubsub.publish(NOTIFICATION_REQUESTED, event, PUBLISH_IN_REQUEST_TIMEOUT_SECONDS)
    except Exception:
        logger.exception("Couldn't publish a %s notification", event["kind"])
