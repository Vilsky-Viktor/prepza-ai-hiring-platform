import re
from datetime import timedelta

# Service tokens live this long; each call between services signs a new one.
SERVICE_TOKEN_LIFETIME = timedelta(seconds=60)

# A call to another service (or Google's APIs) gives up after this long, unless it sets its own:
# enough for a callee starting cold (3-6 s) and its slowest ordinary answer. A hung callee then
# holds its callers' requests and pool slots for 15 s, not 30, so its trouble spreads less under
# load. Calls known to take longer (deletions, starting a generation) pass their own timeout.
HTTP_TIMEOUT_SECONDS = 15
# Retries only connection attempts that failed, so a request is never sent twice.
HTTP_RETRIES = 3

# Requests that only read: their sign-in token isn't checked for revocation (auth.py), which
# costs a call to Firebase; every other method's is, so a deleted account can't change anything.
READ_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
RATE_LIMITED = "Too many requests. Try again later."
# A 429 says in this header (RFC 9110) how many seconds are left until its limit's window ends.
RETRY_AFTER = "Retry-After"
# A request's body is refused past this many bytes (body_limit.py); a service that takes bigger
# uploads (report PDFs, voice messages) passes its own limit.
MAX_BODY_BYTES = 1_000_000
BODY_TOO_LARGE = "The request is too large."
# Cloud Logging's fields: a JSON log line's `severity` and `message` are read as such, and this
# one ties the line to its request's trace, which the load balancer sends in TRACE_HEADER
# ("TRACE_ID/SPAN_ID;o=1"), so one request can be followed across services.
TRACE_HEADER = "X-Cloud-Trace-Context"
TRACE_FIELD = "logging.googleapis.com/trace"
# Cache-Control on answers to signed-in requests (no_store.py): kept by no browser or proxy.
NO_STORE = "no-store"
# Path parameters that are secret tokens (a link that signs its holder in or acts for them):
# answers to them are never kept either (no_store.py).
SECRET_PATH_PARAMS = ("token",)
# What a request's log line names instead of a route's template when no route took it.
UNMATCHED_ROUTE = "(no route)"
# Answers logged as warnings: a sign-in or a permission refused (logging.RequestLogMiddleware).
REFUSED_STATUSES = (401, 403)

# Logged when a provider's web hook (Paddle, Resend) fails its signature check: usually a wrong
# secret, so every event is refused. The alert in infra/terraform/monitoring.tf matches it.
WEBHOOK_SIGNATURE_REFUSED = "web hook signature refused"
NOT_READY = "Not ready"
# What a call to companies came through when not a person in the app, as the issuer of the
# X-Assistant token the assistant sends: the in-app assistant, or an AI app (Claude, ChatGPT,
# ...) the member connected over MCP, which the assistant serves too. Audit events keep it.
VIA_ASSISTANT = "assistant"
VIA_MCP = "mcp"
# That header: a service token signed for companies, so it can't be forged; other services pass
# it on to companies' access check (prepza_common.company_access).
ASSISTANT_HEADER = "X-Assistant"
# The only service that may read the internal routes of what's new (its get_updates tool).
UPDATES_CALLER = "assistant"
NOT_ALLOWED = "Not allowed"
SIGN_IN_UNAVAILABLE = "Sign-in is temporarily unavailable. Please try again shortly."
MINUTE_SECONDS = 60
HOUR_SECONDS = 60 * MINUTE_SECONDS
DAY_SECONDS = 24 * HOUR_SECONDS

# Database connections per process: at most DB_POOL_SIZE + DB_MAX_OVERFLOW. Services with few,
# short queries pass smaller ones. Every instance's total must fit the database's connection
# budget (infra/terraform/database.tf).
DB_POOL_SIZE = 5
DB_MAX_OVERFLOW = 5
# A pooled connection is replaced once it's this old, instead of pinged before each use (a
# SELECT 1 per checkout). Nothing drops idle ones on the way (Postgres has no idle timeout set,
# and the Cloud SQL connector none); one killed by a database restart fails one request, and
# SQLAlchemy then replaces the whole pool.
DB_POOL_RECYCLE_SECONDS = 1800
# Postgres ends a session whose transaction sits idle this long: one left open by a hung await
# would otherwise hold its pool slot and its row locks for good. No transaction waits on another
# service or a model; the longest wait inside one is the outbox's publish call.
IDLE_IN_TRANSACTION_TIMEOUT = "60s"
# Postgres stops a service's statement that runs this long: the shortest request timeout (60 s),
# after which Cloud Run has already answered the caller, while the query would go on holding a
# connection and its locks. A job that needs longer raises it with SET LOCAL statement_timeout.
STATEMENT_TIMEOUT = "60s"
# Old rows (retention, published events) are deleted this many at a time, each batch its own
# short transaction: one DELETE of a month of rows would run long, hold its locks and write its
# whole WAL at once.
DELETE_BATCH = 1000
# Names SQLAlchemy gives the indexes and constraints a model leaves unnamed, so a migration can
# drop or rename one by a name it knows. They are the names Postgres itself gives (so the
# constraints made before keep theirs, and old migrations make the same ones); a CHECK has no
# column to name it by, so it's named where it's made (ck_<table>_<what>).
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "%(table_name)s_%(column_0_N_name)s_key",
    "ck": "%(constraint_name)s",
    "fk": "%(table_name)s_%(column_0_N_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}
# A migration's statement waits at most this long for a lock, then fails (and the deploy with
# it, to be run again): the running version keeps serving during migrations, and an ALTER TABLE
# queued behind a long transaction would hold every query on its table behind it.
MIGRATION_LOCK_TIMEOUT = "5s"
# A migration's statement that runs this long is stopped (and the deploy with it): a backfill or
# rewrite past it belongs in batches. A migration that must run longer (an index built
# concurrently on a large table) raises it for itself with SET statement_timeout.
MIGRATION_STATEMENT_TIMEOUT = "5min"
# A Redis command whose connection dropped (Redis restarted, or the network blinked) is tried
# again on a new one, up to this many times, instead of failing its request; a connection
# idle this long is checked before use.
REDIS_RETRIES = 3
REDIS_HEALTH_CHECK_SECONDS = 30

# Lists are served a page at a time; a page holds at most this many items.
MAX_PAGE_SIZE = 100

# A superadmin's adjustment of a company's credits (billing makes it, companies takes the
# request): at most this many credits either way, and a note this long.
MAX_ADJUSTMENT = 1_000_000
MAX_ADJUSTMENT_NOTE = 200

# Who a kept row is by once its user deleted their account (a referral, a generation, an ATS or
# Slack connection, an audit entry): the row stays for its company, without their id.
DELETED_USER = "deleted-user"

# Sentry: share of requests traced for performance, and emails scrubbed from every event.
DEFAULT_TRACES_SAMPLE_RATE = "0.1"
# Requests never traced unless part of a traced one: uptime checks (/ready every minute per
# service), and scheduled jobs and Pub/Sub pushes (/internal/), thousands a day with no user
# waiting. Their errors are still reported.
UNTRACED_PATHS = ("/ready", "/health", "/internal/")
EMAIL_PATTERN = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
REDACTED_EMAIL = "[email]"
# A URL's path, query and user info can carry credentials (a Slack web hook's path, a customer's
# web hook secret, an invite token): only its scheme and host (group 1) reach Sentry, and the
# fields that hold a query alone are dropped.
URL_PATTERN = r"(https?://)(?:[^\s/?#@'\"]*@)?([^\s/?#'\"]+)[^\s'\"]*"
URL_SCRUBBED = r"\1\2"
QUERY_FIELDS = {"query_string", "http.query", "http.fragment"}
# Langfuse: a person's name or email in a field of data or of JSON text (an assistant tool's
# result) is masked too: any field whose name ends so (`candidate_name`); group 1 keeps the key.
PERSON_FIELD_ENDINGS = ("name", "email")
PERSON_FIELD_PATTERN = r'("[a-z_]*(?:name|email)"\s*:\s*)"(?:[^"\\]|\\.)*"'
REDACTED_PERSON = "[person]"

# Pub/Sub: the one topic every domain event goes to, and its REST API.
EVENTS_TOPIC = "events"
PUBSUB_URL = "https://pubsub.googleapis.com"
# The attribute that carries an event's own id (its outbox row's), the same on every re-send, so
# consumers can handle it once; events sent without an outbox go without it.
EVENT_ID_ATTRIBUTE = "event_id"
# When the change behind an event happened (ISO 8601): the outbox row's time, the same however
# often it's published, so a consumer can put events in order.
OCCURRED_AT_ATTRIBUTE = "occurred_at"
# Publishing from inside a user's request waits at most this long; the scheduled flush sends
# whatever didn't make it.
PUBLISH_IN_REQUEST_TIMEOUT_SECONDS = 5
# Google APIs our services call with their own credentials (Pub/Sub, Cloud Tasks).
GOOGLE_SCOPE = "https://www.googleapis.com/auth/cloud-platform"
# A Firebase ID token's sign-in provider for Google accounts, the only one the admin zone takes.
GOOGLE_SIGN_IN = "google.com"

# Outbox: events published per call to Pub/Sub, and how long published ones are kept. The
# scheduled flush sends batch after batch until none wait, starting no new batch after
# OUTBOX_FLUSH_SECONDS, so a run (plus its last call's timeout) ends within the shortest
# service timeout (60 s) and a backlog drains in minutes.
OUTBOX_BATCH = 100
OUTBOX_FLUSH_SECONDS = 20
OUTBOX_KEEP_DAYS = 7
# Pub/Sub's answers that mean it won't take a message (too large or malformed): the event is
# tried alone, and parked after OUTBOX_MAX_ATTEMPTS of them so it can't hold up the others.
# Outages and other errors count against no event; the events wait for the next flush.
OUTBOX_REJECTED_STATUSES = (400, 413)
OUTBOX_MAX_ATTEMPTS = 5

# Languages the interface and generated content come in, by code, with the name prompts use.
# Every language prepza supports: the interface, its messages and emails, and the tests it
# generates. Names are as prompts use them.
LANGUAGES = {
    "en": "English",
    "ru": "Russian",
    "uk": "Ukrainian",
    "es": "Spanish",
    "pt": "Portuguese (Brazil)",
    "de": "German",
    "fr": "French",
    "it": "Italian",
    "pl": "Polish",
    "nl": "Dutch",
    "tr": "Turkish",
    "ar": "Arabic",
    "he": "Hebrew",
    "fa": "Persian",
    "ja": "Japanese",
    "zh": "Chinese (Simplified)",
    "ko": "Korean",
    "hi": "Hindi",
    "id": "Indonesian",
    "th": "Thai",
    "vi": "Vietnamese",
    "fil": "Filipino",
    "et": "Estonian",
}
# How hard a test is, from its requirements; generation decides it and
# library filters by it.
LEVELS = ("basic", "medium", "hard")
# Of those, the ones written right to left.
RTL_LANGUAGES = {"ar", "he", "fa"}
DEFAULT_LANGUAGE = "en"
# The Firebase custom claim that carries the user's language in every ID token.
LANGUAGE_CLAIM = "language"

# $1 buys this many credits (billing sells them; the FAQ shows prices in dollars too).
CREDITS_PER_DOLLAR = 100
# The seconds a test's question may have, as an admin sets them (companies); each new test
# starts with its level's (the QUESTION_SECONDS_* values in limit_list).
MIN_QUESTION_SECONDS = 10
MAX_QUESTION_SECONDS = 600

# Funnel events for analytics go on the events topic with this type prefix; only they reach
# BigQuery, and the services' push subscriptions leave them out.
FUNNEL_PREFIX = "funnel."

# Holds the referral code from a ?ref= link until the new person signs up or makes a company.
REFERRAL_COOKIE = "prepza_ref"

# A test's title, as its company can rename it; generated titles aim for 60.
MAX_TITLE_LENGTH = 70
# The least an editable title (a test's, a template's) may have, spaces at either end aside.
MIN_TITLE_LENGTH = 3
TITLE_TOO_SHORT = "Use at least 3 characters."
# The longest candidate name kept (from a sign-in, an inviter or an ATS); a longer one is cut.
MAX_CANDIDATE_NAME_LENGTH = 200

# A job description, as pasted to generate a test.
MAX_GOAL_LENGTH = 10_000

# A news post's title and text (library), written in English and translated into each language
# (generation); a translation must fit them too.
MAX_NEWS_TITLE_LENGTH = 120
MAX_NEWS_TEXT_LENGTH = 500

# A campaign's subject, text and button (notifications), written in English and translated into
# each language (generation); a translation must fit them too.
MAX_CAMPAIGN_SUBJECT_LENGTH = 120
MAX_CAMPAIGN_TEXT_LENGTH = 2000
MAX_CAMPAIGN_BUTTON_LENGTH = 40

# The emergency pause (pause.py): one Redis key every service reads, and the message it refuses
# with while it's on.
PAUSE_KEY = "pause:on"
PAUSED = "New interviews and AI features are paused for now. Please try again later."

# Maintenance mode (maintenance.py): one Redis key every service reads, the message every refused
# request gets while it's on, and what stays open: health checks, the switch itself, calls
# between services, Pub/Sub and Scheduler pushes (under /internal/) and Paddle's and Resend's
# webhooks, so no event, job or payment is lost.
MAINTENANCE_KEY = "maintenance:on"
# When it was turned on: candidates' interview time stops meanwhile and is given back when it's
# turned off.
MAINTENANCE_STARTED_KEY = "maintenance:started"
MAINTENANCE = "prepza is under maintenance. We'll be back soon."
MAINTENANCE_OPEN_PATHS = {"/health", "/ready", "/maintenance", "/superadmin/maintenance"}
# Unsubscribing (a one-click link must always work) and the legal texts stay open too.
MAINTENANCE_OPEN_PREFIXES = ("/internal/", "/webhooks/", "/unsubscribe/", "/help/legal/")
# Each instance reads the switch at most this often; turning it takes that long to reach them all.
MAINTENANCE_CACHE_SECONDS = 5

# The company that runs prepza, as the legal texts, the emails' footer and (mirrored in
# frontend/constants/operator.ts) the site's footer and contact page name it.
OPERATOR = {
    "name": "Arcolabs OÜ",
    "registry_code": "17587452",
    "address": "Sepapaja tn 6, 15551 Tallinn, Harju maakond, Estonia",
    # Questions, requests and the contact page's messages all go here.
    "email": "hello@prepza.ai",
}

# A model call cut short (cancelled, timed out, failed) reports no tokens: they are estimated at
# about this many characters each, as for English text. Prices are in ai_constants.py.
CHARS_PER_TOKEN = 4

# Deleting an account that owns a company others have joined (companies refuses, library says
# so): the company would go with their access and its paid credits.
ACCOUNT_OWNS_SHARED = (
    "Make another member the owner of each company you share, or delete it, before deleting "
    "your account."
)

# Each legal document's version: the day it applies from, which may come after the day it's
# published. Rounds serves the documents (a changed text needs a new version and its copy:
# python -m app.legal_archive in rounds); library records the terms a new account accepts, and
# companies the DPA a new company does.
LEGAL_VERSIONS = {
    "terms": "2026-11-08",
    "privacy": "2026-11-08",
    "dpa": "2026-11-08",
}

# The sign-in a company's own platform gives its candidate with the invite link (no email, no
# account of their own): companies signs it in, library counts it as no sign-up.
GUEST_UID_PREFIX = "guest-"

# Money as people read it (money.py): a currency pattern's decimals, left out of a whole amount
# ("$5", not "$5.00"), and where letters of a currency's symbol meet its number ("CHF2.60"),
# which gets a space.
WHOLE_DECIMALS = re.compile(r"\.0+")
CURRENCY_SPACING = re.compile(r"(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])")
