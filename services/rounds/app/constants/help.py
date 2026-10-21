import re
from enum import StrEnum
from pathlib import Path


class HelpRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


# Legal documents the help routes serve, by the path they're asked for under.
class LegalDocument(StrEnum):
    TERMS = "terms"
    PRIVACY = "privacy"
    DPA = "dpa"


# The page keeps the conversation and sends it whole; nothing of it is stored. A new question's
# length, the bounds on what's sent, and the earlier messages the model sees with a question.
MAX_HELP_QUESTION_LENGTH = 1_000
MAX_HELP_MESSAGE_LENGTH = 10_000
# What the help chat's signing key is made for (prepza_common.tokens.purpose_key).
HELP_SIGNING_PURPOSE = "help-signatures"
# A reply's signature: SHA-256, in hex.
SIGNATURE_LENGTH = 64
# A Langfuse trace id: 32 hex characters.
TRACE_ID_LENGTH = 32
MAX_HELP_MESSAGES = 200
HELP_HISTORY_MESSAGES = 10
# The page's conversation can't be checked, so the model sees at most this many characters of
# it before the question, the latest messages first.
HELP_HISTORY_CHARACTERS = 8_000
# An answer's longest, in tokens (its reasoning included). The tokens all help chats used today
# together (input and output, counted after each answer) are kept under HELP_SPEND_KEY, against
# the HELP_TOKENS_PER_DAY limit: a spent budget refuses new questions (429); a started answer
# always finishes. Every question counts under HELP_ALL_KEY, against HELP_DAILY_LIMIT.
HELP_MAX_OUTPUT_TOKENS = 1_500
HELP_SPEND_KEY = "spend:help:all"
HELP_ALL_KEY = "rate:help:all"
# What the help chat's AI calls are recorded as, and what it is called when the pause refuses it.
HELP_CHAT = "help_chat"
# How long billing's prices are kept for the FAQ and the chat before they're asked again.
CATALOG_KEY = "billing-catalog"
CATALOG_CACHE_SECONDS = 5 * 60
LAST_NOT_QUESTION = "The conversation must end with a question."
QUESTION_TOO_LONG = "The question is too long."

# The FAQ's example of a small company's hiring, in candidates a month, priced over a year.
FAQ_EXAMPLE_CANDIDATES = 5
# How long the platform guide (GET /help/guide) is kept, per language, before it's built again.
GUIDE_CACHE_SECONDS = CATALOG_CACHE_SECONDS
# A reply to a visitor asking to sign in or sign up starts with this marker (the prompt says
# so), naming the way they asked for if any; the chat sends a sign-in card in its place.
SIGN_IN_MARKER = re.compile(r"^\s*\[\[sign_in(?::(google|linkedin|github))?\]\]\s*")
SIGN_IN_PREFIX = "[[sign_in"

# The FAQ names today's prices; without them (billing not answering) it isn't served.
PRICES_UNAVAILABLE = "Prices aren't available right now. Please try again in a minute."

# A page's guide asked for by a key that isn't a page's (GET /help/pages/{key}).
NO_SUCH_PAGE = "There's no guide for this page."
# The longest page key a request may name.
MAX_PAGE_KEY_LENGTH = 40

# The site's guide articles, where the site keeps them: English at guides/<slug>.md, each
# translation at <language>/guides/<slug>.md, Markdown with "key: value" frontmatter. The image
# and the local stack put frontend/content at the same place relative to the code (repo layout).
ARTICLES_ROOT = Path(__file__).resolve().parents[4] / "frontend" / "content"
GUIDES_FOLDER = "guides"
# A slug as the files are named; anything else is never read.
GUIDE_SLUG = re.compile(r"^[a-z0-9-]+$")
# Where the site shows a guide.
GUIDE_PATH = "/guides/{slug}"
NO_SUCH_GUIDE = "There's no such guide."
MAX_GUIDE_SLUG_LENGTH = 80
# The guide article a page's guide points to, by the page's key: its help shows it as a link.
PAGE_ARTICLES = {
    "interviewSettings": "skills-test-timing-and-extra-time",
    "candidate": "skills-test-timing-and-extra-time",
}

# A vote on a help chat answer whose signature doesn't match its id and run.
NO_SUCH_ANSWER = "There's no such answer."
