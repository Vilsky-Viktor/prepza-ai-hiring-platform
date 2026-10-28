from enum import StrEnum

from prepza_common.events.notifications import NotificationKind

# The wording of the email checkboxes (settings and sign-in). Change it whenever that wording
# changes, so the consent log tells which wording each choice was made under.
CONSENT_TEXT_VERSION = "2026-10-08"


class EmailSetting(StrEnum):
    """What a user may get by email beyond service emails, which always go out. The activity
    digest's kinds are notification kinds."""

    CANDIDATE_FINISHED = NotificationKind.CANDIDATE_FINISHED.value
    INVITE_UNDELIVERED = NotificationKind.INVITE_UNDELIVERED.value
    ATS_NOT_INVITED = NotificationKind.ATS_NOT_INVITED.value
    INTERVIEW_READY = NotificationKind.INTERVIEW_READY.value
    REMINDERS = "reminders"
    UPDATES = "updates"
    PROMOTIONS = "promotions"


class ConsentSource(StrEnum):
    SIGN_IN = "sign_in"
    SETTINGS = "settings"
    UNSUBSCRIBE = "unsubscribe"
    # A superadmin, for someone who asked prepza (by email, say) to stop its emails.
    ADMIN = "admin"


class ConsentBasis(StrEnum):
    """Why a setting changed: the user's own choice, or product updates turned on at a first
    sign-in that showed the opt-out unticked (a soft opt-in for prepza's own users)."""

    CHOICE = "choice"
    SOFT_OPT_IN = "soft_opt_in"


# Marketing is off until the user agrees (or, for updates, until a first sign-in that offered
# the opt-out); everything else is on until they turn it off.
MARKETING_SETTINGS = {EmailSetting.UPDATES, EmailSetting.PROMOTIONS}
DEFAULTS = {setting: setting not in MARKETING_SETTINGS for setting in EmailSetting}
# Consent to marketing comes only from the user: a superadmin may turn it off for them, never on.
ADMIN_CANT_CONSENT = (
    "Only the person can turn on product updates and offers. You can only turn them off."
)

# Notifications asks for at most this many users' addresses and preferences in one call; Firebase
# looks up at most FIREBASE_LOOKUP_LIMIT accounts at once.
MAX_RECIPIENTS_PER_CALL = 1000
FIREBASE_LOOKUP_LIMIT = 100
