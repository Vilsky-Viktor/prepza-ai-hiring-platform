# Emails to many users at once (services/bulk.py): legal notices and campaigns. A send's
# recipients are worked out once, then each run (every minute, 08:00 to 18:00 UTC) sends the next
# pending ones, paced as the member emails are (constants/member_emails.py).
from enum import StrEnum


class BulkKind(StrEnum):
    """What a bulk send is: a notice of a legal document's new version (a service email, about the
    version), or a campaign (an optional email, about the campaign's id), named after the email
    setting it needs."""

    LEGAL_TERMS = "legal_terms"
    LEGAL_PRIVACY = "legal_privacy"
    LEGAL_DPA = "legal_dpa"
    UPDATES = "updates"
    PROMOTIONS = "promotions"


LEGAL_KINDS = (BulkKind.LEGAL_TERMS, BulkKind.LEGAL_PRIVACY, BulkKind.LEGAL_DPA)
CAMPAIGN_KINDS = (BulkKind.UPDATES, BulkKind.PROMOTIONS)


class RecipientStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    SKIPPED = "skipped"
    FAILED = "failed"


class SkipReason(StrEnum):
    """Why a recipient was skipped: their account or address is gone, the address is on the
    suppression list, they turned the campaign's setting off since it started, or it was
    stopped."""

    GONE = "gone"
    SUPPRESSED = "suppressed"
    UNSUBSCRIBED = "unsubscribed"
    STOPPED = "stopped"


class SuppressionReason(StrEnum):
    BOUNCED = "bounced"
    COMPLAINED = "complained"


# A run reads this many recipients' addresses and languages at once, just before sending them.
BULK_BATCH = 100
# A send that fails is tried again in later runs, this many times in all, then marked failed.
MAX_ATTEMPTS = 3
# Resend's tag carrying the send's id, so a spam complaint counts against its campaign.
SEND_TAG = "send"
# A failure's reason is kept this long.
MAX_REASON_LENGTH = 200
# One bulk run at a time: a run holds this lock while it sends, at most this long (its
# RUN_SECONDS of sending, the batch under way and the sends it prepares first).
BULK_LOCK_KEY = "bulk:lock:send"
BULK_LOCK_SECONDS = 300
