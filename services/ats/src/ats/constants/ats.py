from enum import StrEnum


class AtsProvider(StrEnum):
    """The applicant tracking systems a company can connect."""

    WORKABLE = "workable"
    GREENHOUSE = "greenhouse"
    TEAMTAILOR = "teamtailor"
    RECRUITEE = "recruitee"
    BREEZY = "breezy"


# Each ATS's name as companies know it.
ATS_NAMES = {
    AtsProvider.WORKABLE: "Workable",
    AtsProvider.GREENHOUSE: "Greenhouse",
    AtsProvider.TEAMTAILOR: "Teamtailor",
    AtsProvider.RECRUITEE: "Recruitee",
    AtsProvider.BREEZY: "Breezy HR",
}
# The ATSs whose comments need an author: results go back as the member found at connecting.
NEEDS_AUTHOR = {AtsProvider.WORKABLE, AtsProvider.TEAMTAILOR}


class ConnectionStatus(StrEnum):
    # Working; or its key stopped working (revoked or expired) and needs reconnecting.
    CONNECTED = "connected"
    BROKEN = "broken"


# Workable's API for one account, by its subdomain (acme for acme.workable.com).
WORKABLE_API = "https://{subdomain}.workable.com/spi/v3"
# An account's subdomain as Workable and Recruitee allow it (acme in acme.workable.com).
SUBDOMAIN = r"^[a-z0-9][a-z0-9-]{0,62}$"
# The most jobs one page of Workable's list returns, and how many pages are read at most.
WORKABLE_PAGE = 100
WORKABLE_MAX_PAGES = 10
# Seconds to wait for an ATS's answer.
ATS_TIMEOUT_SECONDS = 15
# One action of an ATS's client, all its calls and pages together (a job list reads up to 20
# pages): it ends within this, inside this service's 60 s request timeout and Pub/Sub's 60 s ack
# deadline, rather than at the most pages × ATS_TIMEOUT_SECONDS.
ATS_ACTION_SECONDS = 45


class CandidateStatus(StrEnum):
    """A candidate the ATS sent: waiting for the interview to be ready (or being invited right
    now), invited, or not invited for `reason`."""

    WAITING = "waiting"
    INVITING = "inviting"
    INVITED = "invited"
    FAILED = "failed"


# An invite claimed this long ago and still not settled was cut off (the server stopped
# mid-invite): it can be claimed again.
STALE_CLAIM_MINUTES = 10
# The most candidates one run of an event or Invite again invites, so it ends well within its
# 60 seconds; the rest stay waiting for the recovery job, every 10 minutes.
INVITE_BATCH = 50
# The recovery job (every 10 minutes, 60 seconds a run) starts no new invite RECOVER_INVITE_SECONDS
# into the run, and no new result sent to an ATS REPORT_SECONDS into it, so it ends in time even
# when an ATS doesn't answer (each call has ATS_TIMEOUT_SECONDS). It reads at most RECOVER_LIMIT
# of each, every connection's in turn; the rest wait for the next run.
RECOVER_INVITE_SECONDS = 20
REPORT_SECONDS = 35
RECOVER_LIMIT = 500
# Invites that failed in passing are tried again by the recovery job this many times in all
# (about an hour), then the candidate is kept as not invited, and the company hears.
MAX_INVITE_ATTEMPTS = 6
# Candidates an ATS sent are kept this long (they hold emails), like companies' candidates.
CANDIDATE_RETENTION_DAYS = 365
# A top-up invites again the candidates refused for lack of credits whom the ATS sent this
# recently; older ones are left for Invite again.
TOPPED_UP_DAYS = 30


class FailReason(StrEnum):
    CREDITS = "credits"
    LIMIT = "limit"
    PAUSED = "paused"
    OTHER = "other"


# The Workable event that sends a candidate: moved into a linked job's stage.
WORKABLE_MOVED = "candidate_moved"
# Where Workable sends it, one address per linked job (Workable wants each target unique).
WORKABLE_WEBHOOK = "{site}/api/ats/webhooks/workable/{link_id}"

# Greenhouse's Harvest API (v3), and where its client credentials become an access token.
GREENHOUSE_API = "https://harvest.greenhouse.io/v3"
GREENHOUSE_TOKEN_URL = "https://auth.greenhouse.io/token"
# What a token may do (its scopes), and the scope writing results back (a note) needs.
GREENHOUSE_INTROSPECT_URL = "https://auth.greenhouse.io/introspect"
GREENHOUSE_NOTES_SCOPE = "harvest:notes:create"
# Connecting a credential that reads but can't write notes (translated in prepza_common.i18n.messages).
GREENHOUSE_CANT_WRITE = (
    "This credential can't add notes, so results can't go back to Greenhouse: allow it the Notes "
    "endpoints too"
)
# A token is renewed this long before Greenhouse said it expires.
GREENHOUSE_TOKEN_MARGIN_SECONDS = 60
GREENHOUSE_PAGE = 500
GREENHOUSE_MAX_PAGES = 10
# Where a company's Greenhouse web hook sends stage changes: one address per connection, which
# the company pastes into Greenhouse with its secret key.
GREENHOUSE_WEBHOOK = "{site}/api/ats/webhooks/greenhouse/{connection_id}"
GREENHOUSE_STAGE_CHANGE = "candidate_stage_change"
# Teamtailor's API in each of its regions; an API key works only in its company's region.
TEAMTAILOR_HOSTS = (
    "https://api.teamtailor.com",
    "https://api.na.teamtailor.com",
    "https://api.au.teamtailor.com",
)
TEAMTAILOR_API_VERSION = "20240904"
TEAMTAILOR_MEDIA_TYPE = "application/vnd.api+json"
# The most items one page of Teamtailor's lists returns, and how many pages are read at most.
TEAMTAILOR_PAGE = 30
TEAMTAILOR_MAX_PAGES = 20
# Jobs no longer hiring, left out of the jobs to link.
TEAMTAILOR_CLOSED_JOBS = {"archived"}
# Where a company's Teamtailor web hook sends its events, one address per connection; the company
# pastes the signature key Teamtailor generates for it back into prepza.
TEAMTAILOR_WEBHOOK = "{site}/api/ats/webhooks/teamtailor/{connection_id}"
# A Teamtailor event signed longer ago than this (or this far ahead) is refused: a replay.
TEAMTAILOR_SIGNATURE_SECONDS = 300
# The events that can bring a candidate into a stage: an application moved, or one made there.
TEAMTAILOR_EVENTS = {"job_application.update", "job_application.create"}
# Recruitee's API for one company, by its subdomain (acme for acme.recruitee.com) or id.
RECRUITEE_API = "https://api.recruitee.com/c/{company}"
# Recruitee's own address for an account, which a company may paste.
RECRUITEE_DOMAIN = ".recruitee.com"
# The jobs to link: hiring ones (published, or internal only), not drafts, closed or archived.
RECRUITEE_OPEN_JOBS = ("published", "internal")
# Where a company's Recruitee web hook sends its events, one address per connection; the company
# pastes the secret Recruitee shows for it back into prepza.
RECRUITEE_WEBHOOK = "{site}/api/ats/webhooks/recruitee/{connection_id}"
RECRUITEE_MOVED = "candidate_moved"
RECRUITEE_STAGE_CHANGED = "stage_changed"
# Breezy HR's API; a personal API key acts as the person who made it.
BREEZY_API = "https://api.breezy.hr/v3"
# Where Breezy sends a company's events, one address per connection; prepza creates that web hook
# itself when connecting, and Breezy gives its signing secret then, once.
BREEZY_WEBHOOK = "{site}/api/ats/webhooks/breezy/{connection_id}"
BREEZY_STATUS_UPDATED = "candidateStatusUpdated"
# Each ATS's web hook address, for the ATSs whose web hook the company sets up itself.
WEBHOOKS = {
    AtsProvider.GREENHOUSE: GREENHOUSE_WEBHOOK,
    AtsProvider.TEAMTAILOR: TEAMTAILOR_WEBHOOK,
    AtsProvider.RECRUITEE: RECRUITEE_WEBHOOK,
}
# The ATSs that make the web hook's secret key themselves: the company pastes it into prepza.
PASTED_KEYS = {AtsProvider.TEAMTAILOR, AtsProvider.RECRUITEE}
# A candidate's scorecard, linked in the results that go back to the ATS.
SCORECARD_LINK = "{site}/companies/{company_id}/interviews/{interview_id}/candidates/{invite_id}"

# The ATS clients' actions that write into the ATS (a candidate's results): one refused while
# the key still reads means the key lacks write access, not that it was revoked.
WRITES = {"comment"}
