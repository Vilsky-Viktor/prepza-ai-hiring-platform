"""Secrets pasted into testee's AI chats (the assistant and the help chat): found before
anything else happens to a message, so it's never stored, logged, shown to a model or sent to
an error report."""

import math
import re
from collections import Counter
from dataclasses import dataclass
from itertools import pairwise

from testee_common.ai.secret_words import API_WORDS, ATS_WORDS, SECRET_WORDS, SLACK_WORDS

# Where the user enters each kind of secret themselves: "api" (testee's API keys and web hook
# secrets), "slack", "ats"; None for a secret testee has no form for.
API, SLACK, ATS = "api", "slack", "ats"
# A secret whose form is the one the message names (an ATS's token, a password for Slack).
NAMED = "named"

# Known formats: the pattern, and the form the secret belongs in.
PATTERNS: list[tuple[re.Pattern, str | None]] = [
    # testee's own API keys and web hook signing secrets.
    (re.compile(r"\bte_[A-Za-z0-9_-]{20,}"), API),
    (re.compile(r"\bwhsec_[A-Za-z0-9_-]{20,}"), API),
    # Slack tokens and incoming web hooks.
    (re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}"), SLACK),
    (re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/_-]{20,}"), SLACK),
    # OpenAI, Anthropic, GitHub, Stripe, Paddle, AWS and Google keys.
    (re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}"), None),
    (re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}"), None),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}"), None),
    (re.compile(r"\b(?:sk|rk|pk)_(?:live|test)_[A-Za-z0-9]{16,}"), None),
    (re.compile(r"\b(?:pdl_(?:live|sdbx)_apikey_|apikey_)[A-Za-z0-9_]{20,}"), None),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), None),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"), None),
    # A JSON web token: three base64url parts, the first a JSON header.
    (re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"), None),
    # A private key.
    (re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----"), None),
    # A long value right after a label saying it's a secret (an ATS's API token, a password).
    (
        re.compile(
            r"(?i)\b(?:api[ _-]?key|token|secret|password|passwd|webhook[ _-]?key)\b"
            r"\s*[:=]?\s*[\"']?[A-Za-z0-9_\-+/=.]{16,}"
        ),
        # The form comes from what the message names.
        NAMED,
    ),
]

# A long run of key-like characters.
CANDIDATE = re.compile(r"[A-Za-z0-9_\-+/=]{16,}")
UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
# With a word saying it's a secret, a value this long counts; without one, a longer value that
# looks random: letters and digits switching often, or all three of upper, lower and digits
# with a spread of characters.
LABELLED_LENGTH = 16
UNLABELLED_LENGTH = 20
MIN_SWITCHES = 6
MIN_ENTROPY = 4.0
# Lowercase letters in a row from which a token reads as glued words, not a key.
MAX_LETTER_RUN = 8


@dataclass(frozen=True)
class Secret:
    """A secret found in a message, and the form it belongs in (None when there's none)."""

    form: str | None


def entropy(text: str) -> float:
    counts = Counter(text)

    return -sum(n / len(text) * math.log2(n / len(text)) for n in counts.values())


def switches(token: str) -> int:
    """How often a token switches between letters and digits."""
    kinds = [char.isdigit() for char in token if char.isalnum()]

    return sum(1 for a, b in pairwise(kinds) if a != b)


def value_like(token: str) -> bool:
    """Letters and digits together, and not a UUID or a path."""
    has_letter = any(char.isalpha() for char in token)
    has_digit = any(char.isdigit() for char in token)

    return has_letter and has_digit and not UUID.match(token) and token.count("/") < 2


def words_glued(token: str) -> bool:
    """A token made of words and version numbers (postgresql16django5): long runs of
    lowercase letters, which a key rarely has."""
    longest = max((len(run) for run in re.findall(r"[a-z]+", token)), default=0)
    mixed_case = any(char.isupper() for char in token)

    return longest >= MAX_LETTER_RUN and not mixed_case


def random_looking(token: str) -> bool:
    """What a key looks like without a word saying so: long, and letters and digits switching
    often (94uf9jf394ur0fj394g3), or upper, lower and digits spread out."""
    if len(token) < UNLABELLED_LENGTH or not value_like(token):
        return False

    mixed_case = any(char.islower() for char in token) and any(char.isupper() for char in token)

    return switches(token) >= MIN_SWITCHES or (mixed_case and entropy(token) >= MIN_ENTROPY)


def has_word(text: str, words: list[str]) -> bool:
    """Whether `text` holds one of `words`: Latin ones at a word's start, others anywhere."""
    lowered = text.lower()

    for word in words:
        if word.isascii():
            if re.search(r"(?<![a-z0-9])" + re.escape(word), lowered):
                return True
        elif word in lowered:
            return True

    return False


def form_named(text: str) -> str | None:
    """The form the message names for its secret: an ATS's, Slack's or testee's API."""
    for words, form in ((ATS_WORDS, ATS), (SLACK_WORDS, SLACK), (API_WORDS, API)):
        if has_word(text, words):
            return form

    return None


def tokens(text: str) -> list[str]:
    """The message's long values: not in an address or an email."""
    found = []

    for word in re.split(r"\s+", text):
        if "://" in word or "@" in word:
            continue

        found += CANDIDATE.findall(word)

    return found


def find_secret(text: str) -> Secret | None:
    """The first secret in `text`, or None, with the form it belongs in."""
    for pattern, form in PATTERNS:
        if pattern.search(text):
            return Secret(form_named(text) if form == NAMED else form)

    labelled = has_word(text, SECRET_WORDS)

    for token in tokens(text):
        labelled_value = (
            labelled
            and len(token) >= LABELLED_LENGTH
            and value_like(token)
            and not words_glued(token)
        )

        if labelled_value or random_looking(token):
            return Secret(form_named(text))

    return None


# What the chats answer instead, translated by its English text (never written by a model):
# in general, and naming the page for that kind of secret (which the answer links to).
REMOVED = (
    "I removed your message: it contained a secret, such as a key, a token or a password. For "
    "your security, secrets never go through the chat."
)
SECRET_REMOVED = REMOVED + " Enter it yourself in the right form on the site."
SECRET_REMOVED_ON_PAGE = {
    API: REMOVED + " Enter it yourself on the API keys page.",
    SLACK: REMOVED + " Enter it yourself on the Slack page.",
    ATS: REMOVED + " Enter it yourself on the integrations page.",
}
# The link's name: "open API keys".
SECRET_PAGE_NAMES = {API: "API keys", SLACK: "Slack", ATS: "integrations"}
# A voice message with a secret in it: its text never comes back.
SECRET_IN_VOICE = (
    "That recording contained a secret, such as a key or a password, so it was removed. Enter "
    "secrets yourself in their form in testee."
)


def secret_in(texts: list[str]) -> Secret | None:
    """The first secret in any of `texts` (a message, and the chat sent along with it)."""
    for text in texts:
        found = find_secret(text)

        if found is not None:
            return found

    return None
