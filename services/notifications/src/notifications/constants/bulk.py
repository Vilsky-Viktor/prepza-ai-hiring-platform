# Emails to many users at once (services/bulk.py): legal notices and campaigns. A send's
# recipients are worked out once, then each run (every minute, 08:00 to 18:00 UTC) sends the next
# pending ones, paced as the member emails are (constants/member_emails.py).
from enum import StrEnum


class BulkKind(StrEnum):
    """What a bulk send is: a notice of a legal document's new version (a service email, about the
    version), or a campaign (about the campaign's id): a product update or an offer (optional
    emails, named after the email setting they need), or an important notice (a service email:
    a security incident, planned downtime, a change to how the service works)."""

    LEGAL_TERMS = "legal_terms"
    LEGAL_PRIVACY = "legal_privacy"
    LEGAL_DPA = "legal_dpa"
    UPDATES = "updates"
    PROMOTIONS = "promotions"
    NOTICES = "notices"


LEGAL_KINDS = (BulkKind.LEGAL_TERMS, BulkKind.LEGAL_PRIVACY, BulkKind.LEGAL_DPA)
CAMPAIGN_KINDS = (BulkKind.UPDATES, BulkKind.PROMOTIONS, BulkKind.NOTICES)
# The campaigns that need their setting on, and can be unsubscribed from.
OPTIONAL_KINDS = (BulkKind.UPDATES, BulkKind.PROMOTIONS)


class RecipientStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    SKIPPED = "skipped"
    FAILED = "failed"


class SkipReason(StrEnum):
    """Why a recipient was skipped: their account or address is gone, the address is on the
    suppression list, they turned an optional campaign's setting off since it started, or it was
    stopped."""

    GONE = "gone"
    SUPPRESSED = "suppressed"
    UNSUBSCRIBED = "unsubscribed"
    STOPPED = "stopped"


class SuppressionReason(StrEnum):
    """Why an address is on testee's suppression list: it bounced for good, marked an email as
    spam, Resend suppressed an email to it (on Resend's own list after an earlier one), or it
    bounced for a while again and again (constants/suppression.py)."""

    BOUNCED = "bounced"
    COMPLAINED = "complained"
    SUPPRESSED = "suppressed"
    SOFT_BOUNCED = "soft_bounced"


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
