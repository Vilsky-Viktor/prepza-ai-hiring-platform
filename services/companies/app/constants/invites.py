from enum import StrEnum
from http import HTTPStatus

from prepza_common.audit_actions import AuditAction
from prepza_common.constants import MAX_CANDIDATE_NAME_LENGTH  # noqa: F401 (re-exported)

# The longest search through candidates' emails and names (an email is at most 254 characters).
MAX_SEARCH_LENGTH = 254


# How an interview's candidates are listed: best grade first, or newest invite first.
class CandidateSort(StrEnum):
    GRADE = "grade"
    DATE = "date"


class InviteStatus(StrEnum):
    INVITED = "invited"
    # The invite email bounced or was marked as spam, before the candidate opened the invite.
    UNDELIVERED = "undelivered"
    IN_PROCESS = "in_process"
    FINISHED = "finished"
    # The candidate deleted their account: their email and results are gone.
    DELETED = "deleted"
    # Never started within INVITE_EXPIRY_DAYS of being sent; sending it again revives it.
    EXPIRED = "expired"


# Statuses of an invite the candidate hasn't started: its credits are set aside, not charged.
NOT_STARTED = (InviteStatus.INVITED, InviteStatus.UNDELIVERED, InviteStatus.EXPIRED)
STARTED = (InviteStatus.IN_PROCESS, InviteStatus.FINISHED)
# What each change an owner or admin makes to a candidate is recorded as.
CHANGE_ACTIONS = {"name": AuditAction.CANDIDATE_RENAMED, "extra_time": AuditAction.EXTRA_TIME_SET}
# Statuses of an invite still open: its link works and its credits are set aside (an expired
# one gave them back).
OPEN = (InviteStatus.INVITED, InviteStatus.UNDELIVERED, InviteStatus.IN_PROCESS)


# Candidate invites, with the candidate's results, are kept this long after they're sent.
CANDIDATE_RETENTION_DAYS = 365
# Erased candidates are remembered (ids only) as long as the database's backups last, so a
# restore's removals can be run again (services/removal_replay.py).
REMOVAL_KEEP_DAYS = 14
# Invites deleted per batch of the daily retention run.
RETENTION_BATCH = 200
# The daily candidate jobs (retention, invite expiry, removals) start no new batch this long
# into a run, so it ends within companies' 150-second request timeout; the next run goes on.
JOB_RUN_SECONDS = 100
# An invite never started this long after it was last sent expires, and its credits come back.
INVITE_EXPIRY_DAYS = 30
# Inviting many at once: refused over the most emails one list may hold (the MAX_BULK_INVITES
# limit), and over the longest text pasted or uploaded (a CSV export with other columns is fine;
# only its emails count).
TOO_MANY_EMAILS = "Too many emails in one list: the most is {limit}."
NO_EMAILS = "No emails found."
NAME_NEEDS_ONE_EMAIL = "A name goes with one email. In a list, write each as Name <email>."
# The longest list: characters pasted, or bytes of an uploaded file (the frontend checks a file's
# size against it before reading it). The messages name the same limits.
MAX_BULK_TEXT_LENGTH = 50_000
FILE_TOO_LARGE = "The file is too large (max 50 KB)."
LIST_TOO_LONG = "The list is too long (max 50,000 characters)."
# An uploaded list is a CSV or TXT file, by its name, and text: no NUL bytes, and few characters
# that couldn't be read (a renamed spreadsheet is mostly those).
LIST_FILE_TYPES = (".csv", ".txt")
NOT_A_LIST_FILE = "Only CSV or TXT files."
MAX_UNREADABLE_SHARE = 0.05
# Anything in a list that looks like an email; each is checked properly after.
EMAIL_PATTERN = r"[^\s,;<>()\"']+@[^\s,;<>()\"']+"


# Why a line of a list can't be used (one reason a line): it has no email, an email that isn't
# valid, or a name that isn't written as "Name <email>" or "email, Name".
class LineProblem(StrEnum):
    NO_EMAIL = "no_email"
    INVALID_EMAIL = "invalid_email"
    UNCLEAR_NAME = "unclear_name"


# Why an email from a list wasn't invited.
class SkipReason(StrEnum):
    INVALID = "invalid"
    # Over the member's email limits for now.
    LIMIT = "limit"
    # The company ran out of credits; the rest of the list wasn't tried.
    NO_CREDITS = "no_credits"
    # The candidate already started or finished: a list doesn't email them again.
    STARTED = "started"
    FAILED = "failed"


# What a refused invite's HTTP status means for the list; any other is FAILED.
SKIP_REASONS = {
    HTTPStatus.PAYMENT_REQUIRED: SkipReason.NO_CREDITS,
    HTTPStatus.TOO_MANY_REQUESTS: SkipReason.LIMIT,
}


# An invite not started this long after it was last sent gets one reminder email.
REMINDER_AFTER_DAYS = 3
# Reminders queued per daily run; the rest go the next day.
REMINDERS_PER_RUN = 500
# Invites expired per batch of the daily expiry run.
EXPIRIES_PER_BATCH = 200
TOO_MANY_COMPANIES = "You already own as many companies as one person may: {limit}."
# Company names are unique across prepza, ignoring case, and short enough for a heading.
MAX_COMPANY_NAME_LENGTH = 45
# A company name may be as short as two letters (EY, HP, 3M), spaces at either end aside.
MIN_COMPANY_NAME_LENGTH = 2
COMPANY_NAME_TOO_SHORT = "Use at least 2 characters."
COMPANY_NAME_TAKEN = "A company with this name already exists."
TOO_MANY_INTERVIEWS = (
    "Your company's daily limit of generated interviews is {limit}. Try again tomorrow."
)
TOO_MANY_INTERVIEWS_UNPAID = (
    "Until your first top-up, your company's daily limit of generated interviews is {limit}. "
    "Try again tomorrow."
)
TOO_MANY_WITHOUT_CANDIDATES = (
    "Invite a candidate to one of your interviews, or delete one, before generating another: "
    "your company's limit of generated interviews waiting without candidates is {limit}."
)
TOO_MANY_WITHOUT_CANDIDATES_UNPAID = (
    "Invite a candidate to one of your interviews, or delete one, before generating another: "
    "until your first top-up, your company's limit of generated interviews waiting without "
    "candidates is {limit}."
)
# Starting an interview with an email the sign-in hasn't verified (GitHub doesn't): a link to
# confirm it was sent when they signed in.
# Inviting a candidate who already finished (their results are in) again.
# An interview without its questions (and so its title) yet takes no invites.
INTERVIEW_NOT_READY = "Interview is still being generated"
ALREADY_FINISHED = "This candidate already finished the interview."
# A reminder asked for a candidate invited without prepza's emails or sign-in.
NO_EMAILS_FOR_GUEST = "prepza doesn't email this candidate: send them their invite link yourself."
NOT_THE_GUEST = "Open the interview from the link the company gave you."
# An invite not started within INVITE_EXPIRY_DAYS; sending it again makes the link work again.
INVITE_EXPIRED = "This invite has expired. Ask the company to send it again."
EMAIL_NOT_VERIFIED = "Confirm your email first: open the link we sent you, then try again."
# A first start without the candidate's pledge to answer on their own.
NO_PLEDGE = "Confirm you'll answer on your own, without AI tools or other people, to start."
# A company a superadmin suspended: its members see why, and candidates that the interview isn't
# available (one already in it may finish).
COMPANY_SUSPENDED = "This company is suspended. Contact hello@prepza.ai to find out more."
INTERVIEW_UNAVAILABLE = "This interview isn't available."
# A shareable link whose company has no credits left for another candidate.
LINK_CLOSED = "This interview isn't taking new candidates right now."
# Random bytes in a shareable link's code.
LINK_TOKEN_BYTES = 12


# What a company can narrow its candidates to: an invite status, or a result: reached the pass
# mark, or flagged by integrity signals. A deleted candidate's row has no email to show.
class CandidateFilter(StrEnum):
    INVITED = InviteStatus.INVITED
    IN_PROCESS = InviteStatus.IN_PROCESS
    FINISHED = InviteStatus.FINISHED
    PASSED = "passed"
    FLAGGED = "flagged"
    UNDELIVERED = InviteStatus.UNDELIVERED
    EXPIRED = InviteStatus.EXPIRED


# Filters that need every candidate's results from rounds, not just their invite.
RESULT_FILTERS = (CandidateFilter.PASSED, CandidateFilter.FLAGGED)
# The integrity signals rounds counts per candidate.
SIGNAL_KEYS = ("tab_leaves", "copies", "fast_answers")

# Extra time a company can give a candidate who needs it, in percent of each question's time.
EXTRA_TIME_OPTIONS = (0, 25, 50, 100)
# Extra time is set before the candidate starts: their questions' time is fixed then.
EXTRA_TIME_STARTED = "Extra time can only be changed before the candidate starts."

# The API's return_url must stay on the company's own site, so it can't send candidates elsewhere.
RETURN_URL_OFF_DOMAIN = (
    "return_url must be an https address on the company's verified website domain; get the "
    "company verified in prepza first (Verify, next to its name)."
)
