import re
from enum import StrEnum


class HelpRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


# The help chat: Mira for visitors who aren't signed in, answering from the site's documents.
# The page keeps the conversation and sends it whole; nothing of it is stored. A new question's
# length, the bounds on what's sent, and the earlier messages the model sees with a question.
MAX_HELP_QUESTION_LENGTH = 1_000
MAX_HELP_MESSAGE_LENGTH = 10_000
# What the help chat's signing key is made for (prepza_common.auth.tokens.purpose_key).
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
# Its replies are short, so a call silent for longer has hung; one more try after a failed
# call, both well within the assistant's request timeout (infra/terraform/locals.tf).
HELP_TIMEOUT_SECONDS = 25
HELP_RETRIES = 1
LAST_NOT_QUESTION = "The conversation must end with a question."
# The longest page key a request may name.
MAX_PAGE_KEY_LENGTH = 40
# Rounds' route with what the help chat answers from (the site's documents stay rounds').
KNOWLEDGE_PATH = "/internal/help/knowledge"
# A reply to a visitor asking to sign in or sign up starts with this marker (the prompt says
# so), naming the way they asked for if any; the chat sends a sign-in card in its place.
SIGN_IN_MARKER = re.compile(r"^\s*\[\[sign_in(?::(google|linkedin|github))?\]\]\s*")
SIGN_IN_PREFIX = "[[sign_in"
# A vote on a help chat answer whose signature doesn't match its id and run.
NO_SUCH_ANSWER = "There's no such answer."
# A visitor's question in a Latin-script language is answered in it only with at least this many
# of its common words (prepza_common.i18n.language_words), more than of the page's language; a
# short one is answered in the page's.
HELP_LANGUAGE_WORDS = 2
