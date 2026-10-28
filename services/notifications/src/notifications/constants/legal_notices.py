# Notices of a significant change to a legal document (prepza_common LEGAL_VERSIONS): a
# superadmin decides a change is significant and asks for its email, which goes out at least
# LEGAL_NOTICE_DAYS before the new version applies (the DPA promises 14 days for a new
# sub-processor), through the bulk sender (constants/bulk.py) in its sending hours, until everyone
# has it.
from enum import StrEnum

LEGAL_NOTICE_DAYS = 14


class LegalNoticeState(StrEnum):
    """Where a document's current version stands: its email can be asked for, it already
    applies, it's too close to the day it applies, or it was asked for (and is going out, or
    went out)."""

    SENDABLE = "sendable"
    IN_FORCE = "in_force"
    TOO_LATE = "too_late"
    SENDING = "sending"
    SENT = "sent"


# Who each notice goes to: everyone with an account, or the companies' owners and admins.
EVERYONE = ("terms", "privacy")
COMPANY_EDITORS = ("dpa",)

TOO_LATE = (
    "A notice goes out at least 14 days before the new version applies: give it a later date."
)
ALREADY_ASKED = "This version's notice was already sent."
