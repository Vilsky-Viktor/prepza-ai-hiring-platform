# Every limit of ours, by name: its default and the bounds the Controls tab keeps an edited value
# in, and the plain values tuned there too (counted=False). The services read the current value
# with limits.limit(redis, NAME); billing keeps the edited ones. Not listed, as they aren't limits
# to tune: page and batch sizes, retries, request body sizes (checked before the route runs), and
# the referrals a year, which the terms of service quote.
from prepza_common.constants import (
    DAY_SECONDS,
    HOUR_SECONDS,
    MAX_QUESTION_SECONDS,
    MIN_QUESTION_SECONDS,
    MINUTE_SECONDS,
)
from prepza_common.limit_types import Limit

# The values billing keeps, as a Redis hash every service reads (name to value).
LIMITS_KEY = "limits:values"
# Each service instance reads it at most this often, so a change is in effect within that.
LIMITS_CACHE_SECONDS = 30
# Billing writes the hash again this often, so a Redis wipe heals itself.
LIMITS_SYNC_SECONDS = 5 * 60
# The refusals while the emergency pause is on, recorded like a limit's (pause.py).
PAUSED_LIMIT = "PAUSED"
# A topic review's revisions count over the review's life (generation's REVIEW_EXPIRY_DAYS).
REVIEW_SECONDS = 14 * DAY_SECONDS
SIGNALS_WINDOW = MINUTE_SECONDS
ASSISTANT = "assistant"
COMPANIES = "companies"
GENERATION = "generation"
ROUNDS = "rounds"
EVERYONE = "everyone"

LIMITS = {
    # The assistant: messages and their tokens, voice messages, actions.
    "MESSAGES_PER_USER_HOUR": Limit(ASSISTANT, 30, "calls", HOUR_SECONDS, 1, 1_000, "user"),
    "MESSAGES_PER_USER_DAY": Limit(ASSISTANT, 200, "calls", DAY_SECONDS, 1, 10_000, "user"),
    "MESSAGES_PER_COMPANY_DAY": Limit(
        ASSISTANT, 1_000, "calls", DAY_SECONDS, 1, 100_000, "company"
    ),
    "MESSAGES_PER_DAY": Limit(
        ASSISTANT, 20_000, "calls", DAY_SECONDS, 100, 1_000_000, "everyone", "unpaid"
    ),
    "TOKENS_PER_USER_DAY": Limit(
        ASSISTANT, 2_000_000, "tokens", DAY_SECONDS, 10_000, 100_000_000, "user"
    ),
    "TOKENS_PER_COMPANY_DAY": Limit(
        ASSISTANT, 6_000_000, "tokens", DAY_SECONDS, 10_000, 500_000_000, "company"
    ),
    "TOKENS_PER_DAY": Limit(
        ASSISTANT,
        200_000_000,
        "tokens",
        DAY_SECONDS,
        1_000_000,
        10_000_000_000,
        "everyone",
        "unpaid",
    ),
    "TRANSCRIPTIONS_PER_USER_HOUR": Limit(ASSISTANT, 60, "calls", HOUR_SECONDS, 1, 1_000, "user"),
    "ACTIONS_PER_USER_HOUR": Limit(ASSISTANT, 30, "calls", HOUR_SECONDS, 1, 1_000, "user"),
    # AI apps over MCP, and their OAuth server.
    "MCP_CALLS_PER_USER_MINUTE": Limit(ASSISTANT, 60, "calls", MINUTE_SECONDS, 1, 1_000, "user"),
    "MCP_CALLS_PER_USER_DAY": Limit(ASSISTANT, 3_000, "calls", DAY_SECONDS, 1, 100_000, "user"),
    "REGISTRATIONS_PER_IP_HOUR": Limit(ASSISTANT, 300, "calls", HOUR_SECONDS, 1, 10_000, "ip"),
    "REGISTRATIONS_PER_DAY": Limit(
        ASSISTANT, 20_000, "calls", DAY_SECONDS, 100, 1_000_000, "everyone"
    ),
    "AUTHORIZATIONS_PER_IP_HOUR": Limit(ASSISTANT, 120, "calls", HOUR_SECONDS, 1, 10_000, "ip"),
    "TOKEN_REQUESTS_PER_CLIENT_MINUTE": Limit(
        ASSISTANT, 30, "calls", MINUTE_SECONDS, 1, 1_000, "user"
    ),
    "APPROVALS_PER_USER_HOUR": Limit(ASSISTANT, 20, "calls", HOUR_SECONDS, 1, 1_000, "user"),
    # Companies: what they own, generate, invite and email.
    "MAX_OWNED_COMPANIES": Limit(COMPANIES, 3, "items", None, 1, 50, "user"),
    "INTERVIEWS_PER_DAY": Limit(COMPANIES, 10, "calls", DAY_SECONDS, 1, 1_000, "company", "paid"),
    "INTERVIEWS_PER_DAY_UNPAID": Limit(
        COMPANIES, 3, "calls", DAY_SECONDS, 1, 100, "company", "unpaid", "INTERVIEWS_PER_DAY"
    ),
    "MAX_INTERVIEWS_WITHOUT_CANDIDATES": Limit(
        COMPANIES, 5, "items", None, 1, 1_000, "company", "paid"
    ),
    "MAX_INTERVIEWS_WITHOUT_CANDIDATES_UNPAID": Limit(
        COMPANIES,
        1,
        "items",
        None,
        1,
        100,
        "company",
        "unpaid",
        "MAX_INTERVIEWS_WITHOUT_CANDIDATES",
    ),
    "PREVIEWS_PER_USER_HOUR": Limit(COMPANIES, 20, "calls", HOUR_SECONDS, 1, 1_000, "user"),
    # Checkouts made and failed payments looked up, each a call to Paddle's API.
    "CHECKOUT_CALLS_PER_USER_HOUR": Limit(COMPANIES, 60, "calls", HOUR_SECONDS, 1, 1_000, "user"),
    # Interviews copied from templates (each copies a whole question bank in library).
    "TEMPLATE_COPIES_PER_HOUR": Limit(COMPANIES, 30, "calls", HOUR_SECONDS, 1, 1_000, "company"),
    # A company's platform's candidates signed in by their link alone (each a signed token).
    "GUEST_SIGN_INS_PER_IP_HOUR": Limit(COMPANIES, 60, "calls", HOUR_SECONDS, 1, 10_000, "ip"),
    # Answers marked wrong (each starts the AI verifier) and failed generations run again.
    "WRONG_MARKS_PER_COMPANY_DAY": Limit(COMPANIES, 50, "calls", DAY_SECONDS, 1, 1_000, "company"),
    "GENERATION_RETRIES_PER_COMPANY_DAY": Limit(
        COMPANIES, 20, "calls", DAY_SECONDS, 1, 1_000, "company"
    ),
    "LINK_STARTS_PER_HOUR": Limit(COMPANIES, 30, "calls", HOUR_SECONDS, 1, 10_000, "company"),
    "LINK_STARTS_PER_IP_HOUR": Limit(COMPANIES, 10, "calls", HOUR_SECONDS, 1, 1_000, "ip"),
    "MAX_BULK_INVITES": Limit(COMPANIES, 100, "items", None, 1, 1_000, "company"),
    "MAX_PENDING_INVITES": Limit(COMPANIES, 20, "items", None, 1, 1_000, "company"),
    "MEMBER_INVITES_PER_UNPAID_DAY": Limit(
        COMPANIES, 10, "calls", DAY_SECONDS, 1, 1_000, "company", "unpaid"
    ),
    "EMAIL_HOURLY_LIMIT": Limit(COMPANIES, 100, "calls", HOUR_SECONDS, 1, 10_000, "user"),
    "EMAIL_DAILY_LIMIT": Limit(COMPANIES, 200, "calls", DAY_SECONDS, 1, 100_000, "user"),
    "EMAIL_RECIPIENT_DAILY_LIMIT": Limit(COMPANIES, 3, "calls", DAY_SECONDS, 1, 100, "user"),
    "REPORT_EMAILS_PER_COMPANY_DAY": Limit(
        COMPANIES, 20, "calls", DAY_SECONDS, 1, 10_000, "company"
    ),
    # The seconds each question of a new test starts with, by the test's level (limits.py's
    # question_seconds); an admin can change a test's own, and extra time adds to it.
    "QUESTION_SECONDS_BASIC": Limit(
        COMPANIES,
        60,
        "seconds",
        None,
        MIN_QUESTION_SECONDS,
        MAX_QUESTION_SECONDS,
        EVERYONE,
        counted=False,
    ),
    "QUESTION_SECONDS_MEDIUM": Limit(
        COMPANIES,
        60,
        "seconds",
        None,
        MIN_QUESTION_SECONDS,
        MAX_QUESTION_SECONDS,
        EVERYONE,
        counted=False,
    ),
    "QUESTION_SECONDS_HARD": Limit(
        COMPANIES,
        75,
        "seconds",
        None,
        MIN_QUESTION_SECONDS,
        MAX_QUESTION_SECONDS,
        EVERYONE,
        counted=False,
    ),
    # Generation: tests, regenerated questions, topic revisions, quality checks.
    "GENERATION_LIMIT": Limit(GENERATION, 20, "calls", DAY_SECONDS, 1, 1_000, "user"),
    "REGENERATION_LIMIT": Limit(GENERATION, 100, "calls", DAY_SECONDS, 1, 10_000, "user"),
    "DAILY_GENERATION_LIMIT": Limit(
        GENERATION, 100, "calls", DAY_SECONDS, 1, 10_000, "everyone", "unpaid"
    ),
    "MAX_TOPIC_REVISIONS": Limit(GENERATION, 10, "calls", REVIEW_SECONDS, 1, 100, "company"),
    "DAILY_VERIFY_LIMIT": Limit(GENERATION, 300, "calls", DAY_SECONDS, 1, 10_000, "everyone"),
    # How fast generation writes: the AI calls one generation makes at once, and the calls a
    # second of every generation together (shared through Redis; the help chat isn't held to it).
    # OpenAI allows our account 5,000 requests and 1M tokens a minute.
    "GENERATION_CALLS_AT_ONCE": Limit(
        GENERATION, 24, "calls", None, 1, 64, EVERYONE, counted=False
    ),
    "GENERATION_CALLS_PER_SECOND": Limit(
        GENERATION, 24, "calls", None, 1, 80, EVERYONE, counted=False
    ),
    # The share of every topic's questions, and of every candidate's and practice round's draw
    # from a topic, that are "select all that apply" (multi_answer.py). 10% while multi-answer
    # distractors score below the 3.0 target in the evals (evals/README.md).
    "MULTI_ANSWER_PERCENT": Limit(GENERATION, 10, "percent", None, 0, 50, EVERYONE, counted=False),
    # Questions generated for each topic: an interview's, from which each candidate gets a random
    # subset, and a template's (30 for free practice and 60 for companies' interviews, library's
    # PRACTICE_QUESTIONS and COMPANY_QUESTIONS). A change applies to generations started after it.
    "INTERVIEW_QUESTIONS_PER_TOPIC": Limit(
        GENERATION, 70, "items", None, 10, 500, EVERYONE, counted=False
    ),
    "TEMPLATE_QUESTIONS_PER_TOPIC": Limit(
        GENERATION, 90, "items", None, 10, 500, EVERYONE, counted=False
    ),
    # Main topics an interview or template has, and subtopics a topic has (each subtopic is at
    # least one AI call). The topic review follows them.
    "MAX_TOPICS": Limit(GENERATION, 10, "items", None, 1, 20, EVERYONE, counted=False),
    "MAX_SUBTOPICS": Limit(GENERATION, 5, "items", None, 1, 20, EVERYONE, counted=False),
    # Rounds: practice, interview sessions, the help chat and the contact page.
    "PRACTICE_ROUNDS_PER_HOUR": Limit(ROUNDS, 20, "calls", HOUR_SECONDS, 1, 1_000, "user"),
    "SIGNALS_PER_MINUTE": Limit(ROUNDS, 60, "calls", SIGNALS_WINDOW, 1, 1_000, "user"),
    "MAX_SIGNALS_PER_QUESTION": Limit(ROUNDS, 50, "items", None, 1, 1_000, "user"),
    "HELP_USER_LIMIT": Limit(ROUNDS, 30, "calls", HOUR_SECONDS, 1, 1_000, "user"),
    # Thumbs up or down on the help chat's answers (each may tell Langfuse).
    "HELP_VOTES_PER_IP_HOUR": Limit(ROUNDS, 120, "calls", HOUR_SECONDS, 1, 10_000, "ip"),
    "HELP_IP_LIMIT": Limit(ROUNDS, 60, "calls", HOUR_SECONDS, 1, 1_000, "ip"),
    "HELP_DAILY_LIMIT": Limit(ROUNDS, 5_000, "calls", DAY_SECONDS, 1, 1_000_000, "everyone"),
    "HELP_TOKENS_PER_DAY": Limit(
        ROUNDS, 50_000_000, "tokens", DAY_SECONDS, 100_000, 5_000_000_000, "everyone"
    ),
    "CONTACT_IP_LIMIT": Limit(ROUNDS, 5, "calls", DAY_SECONDS, 1, 100, "ip"),
    "CONTACT_DAILY_LIMIT": Limit(ROUNDS, 200, "calls", DAY_SECONDS, 1, 10_000, "everyone"),
    # Library: feedback on questions.
    # "Download my data": each asks every service for the account's data.
    "DATA_EXPORTS_PER_HOUR": Limit("library", 5, "calls", HOUR_SECONDS, 1, 100, "user"),
    "RATINGS_PER_DAY": Limit("library", 200, "calls", DAY_SECONDS, 1, 10_000, "user"),
    "REPORTS_PER_DAY": Limit("library", 30, "calls", DAY_SECONDS, 1, 1_000, "user"),
    # The public API: keys, web hooks and requests.
    "MAX_API_KEYS": Limit("api", 10, "items", None, 1, 100, "company"),
    "MAX_WEBHOOKS": Limit("api", 5, "items", None, 1, 100, "company"),
    "API_REQUESTS_PER_MINUTE": Limit("api", 60, "calls", MINUTE_SECONDS, 1, 10_000, "company"),
    # Test events sent to a company's web hooks, each a request to the company's server.
    # The bell's open streams (a tab each) one user may hold at once.
    "STREAMS_PER_USER": Limit("notifications", 10, "items", None, 1, 100, "user"),
    "WEBHOOK_TESTS_PER_HOUR": Limit("api", 30, "calls", HOUR_SECONDS, 1, 1_000, "company"),
    # ATS connections made or replaced, each checked with a call to the ATS.
    # Calls a company's ATS pages make to its ATS (jobs, stages, texts, links), and ATS web hooks
    # per sending address, counted before their signature is checked.
    "ATS_CALLS_PER_COMPANY_MINUTE": Limit("ats", 60, "calls", MINUTE_SECONDS, 1, 1_000, "company"),
    "ATS_WEBHOOKS_PER_IP_MINUTE": Limit("ats", 600, "calls", MINUTE_SECONDS, 10, 10_000, "ip"),
    "ATS_CONNECTS_PER_HOUR": Limit("ats", 20, "calls", HOUR_SECONDS, 1, 1_000, "company"),
    # Notifications: emails a day through Resend, for the bulk ones' share (bulk.py).
    "RESEND_DAILY_LIMIT": Limit(
        "notifications", 100, "calls", DAY_SECONDS, 1, 1_000_000, "everyone"
    ),
    # The share of RESEND_DAILY_LIMIT bulk sends leave for everything else (invites first): they
    # stop for the day at the rest.
    "RESEND_RESERVE_PERCENT": Limit(
        "notifications", 20, "percent", None, 0, 90, EVERYONE, counted=False
    ),
    # Campaigns of each kind a day (UTC), so a double click or a hurried second one can't flood
    # people.
    "CAMPAIGNS_PER_KIND_DAY": Limit("notifications", 1, "calls", DAY_SECONDS, 1, 10, EVERYONE),
    # Important notices a day (UTC): they reach people whatever their email settings, so fewer
    # may go out than of the other kinds.
    "NOTICES_PER_DAY": Limit("notifications", 1, "calls", DAY_SECONDS, 1, 3, EVERYONE),
    # Every AI call for unpaid companies and people without a company, in USD a UTC day
    # (ai_cap.py).
    "AI_SPEND_UNPAID_DAY": Limit(
        "billing", 15.0, "usd", DAY_SECONDS, 1.0, 500.0, "everyone", "unpaid"
    ),
    # OpenAI spend a month the AI costs tab compares this month's with; 0: no budget.
    "MONTHLY_BUDGET": Limit("billing", 300.0, "usd", None, 0.0, 100_000.0, EVERYONE, counted=False),
}

# The value giving each level's seconds a question.
QUESTION_SECONDS = {
    "basic": "QUESTION_SECONDS_BASIC",
    "medium": "QUESTION_SECONDS_MEDIUM",
    "hard": "QUESTION_SECONDS_HARD",
}

# Our providers' limits, recorded where a call to them is refused (kind "provider:<name>") and
# shown read-only; Cloud Armor's per-IP limit lives in Terraform and is counted from its logs.
PROVIDER_LIMITS = {
    "OPENAI_RATE_LIMIT": "openai",
    # The account ran out of money: all AI stops, so it's logged as an error and alerts at once.
    "OPENAI_QUOTA": "openai",
    # Waiting in generation's own request limiter (GENERATION_CALLS_PER_SECOND).
    "OPENAI_THROTTLED": "openai",
    "RESEND_RATE_LIMIT": "resend",
    # Resend's sending quota used up, its daily or its monthly one.
    "RESEND_DAILY_QUOTA": "resend",
    "ATS_RATE_LIMIT": "ats",
    "FIREBASE_TOKEN_REFUSED": "firebase",
}
