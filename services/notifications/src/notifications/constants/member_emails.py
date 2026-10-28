# The emails to prepza's users (company members) that a schedule sends: the activity digest and
# reminders. Each is sent once (services/member_sends.py claim); a run sends for at most
# RUN_SECONDS, and the next run, a minute later, goes on where it stopped.
from enum import StrEnum


class MemberEmail(StrEnum):
    """What a sent email was, in the sent log: the daily digest, or one kind of reminder."""

    DIGEST = "digest"
    LOW_CREDITS = "low_credits"
    NO_CANDIDATES = "no_candidates"
    REVIEW_WAITING = "review_waiting"


# Other services take at most this many ids in one call.
MAX_IDS_PER_CALL = 1000

# A run works a page of this many companies at a time (services/member_pages.py): their members
# and everything those members' emails cover are read for the page alone, and the page's emails
# go before the next is read. At most this many of a page's members' companies are asked for at
# once.
MEMBER_PAGE = 100
CALLS_AT_ONCE = 10
# Where the day's runs of a job (the digest, reminders) have got to: the last company id of the
# last page done, kept past the day's catch-up hour.
CURSOR_KEY = "member_emails:after:{job}:{day}"
# The reminders' job, by that name (the digest's is MemberEmail.DIGEST).
REMINDERS_JOB = "reminders"
CURSOR_SECONDS = 2 * 24 * 3600

# A run stops sending after this long, well within the scheduler's 60 seconds, and waits this
# long between two emails, so it stays under Resend's per-second limit with room for invites.
RUN_SECONDS = 40
SEND_INTERVAL_SECONDS = 0.6
# The minute of the hour's last run (jobs.tf runs them every minute for an hour, and again for a
# catch-up hour three hours later, which sends what the first missed): one that still leaves
# emails unsent logs an error, as sending is too slow for its hour.
LAST_RUN_MINUTE = 59

# The digest covers the 24 hours before DIGEST_HOUR (UTC) of the day, the same window for every
# run of a day, the catch-up hour's included.
DIGEST_HOURS = 24
DIGEST_HOUR = 7

# A reminder of each kind reaches a user at most once in REMINDER_DAYS.
REMINDER_DAYS = 7
# An interview nobody was invited to NO_CANDIDATES_DAYS after it was ready; one ready more than
# NO_CANDIDATES_WINDOW_DAYS ago (before reminders existed, or missed) isn't reminded about.
NO_CANDIDATES_DAYS = 3
NO_CANDIDATES_WINDOW_DAYS = 10
# Topics waiting for their review for REVIEW_WAITING_DAYS. Generation cancels a review left open
# for 14 days (its REVIEW_EXPIRY_DAYS), so interviews started more than REVIEW_STARTED_DAYS ago
# aren't looked at.
REVIEW_WAITING_DAYS = 1
REVIEW_STARTED_DAYS = 15
# Generation's status of a generation waiting for its topics' review.
AWAITING_REVIEW = "awaiting_review"

# The sent log keeps rows long enough to outlast every window above. The reminders' runs delete
# older rows (and old soft bounces) until this long after the run started, still within the
# scheduler's and Cloud Run's 60 seconds; the next run deletes the rest.
SENT_KEEP_DAYS = 30
CLEANUP_SECONDS = 50

# The pages emails link to.
COMPANIES_LINK = "/companies"
INTERVIEW_LINK = "/companies/{company_id}/interviews/{interview_id}"
TOP_UP_LINK = "/top-up"
