from enum import StrEnum


class Role(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class Source(StrEnum):
    TEXT = "text"
    VOICE = "voice"


class Status(StrEnum):
    COMPLETE = "complete"
    # Stopped by the user (or a closed tab), with the text it had so far.
    CANCELLED = "cancelled"
    FAILED = "failed"


class ToolState(StrEnum):
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


# A message the user sends, and the page they're on (context for the model only): its path with
# the query (cut to this length) and the ids it's about, each an id's characters only.
MAX_MESSAGE_LENGTH = 2_000
MAX_PAGE_LENGTH = 200
PAGE_ID_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"
# A chat the panel brings back after a reload: one whose last message is at most this old;
# an older one stays in the history and the panel starts a new chat.
RESTORE_MINUTES = 30
# An opened conversation shows its latest messages, this many; earlier ones load on asking.
MESSAGES_SHOWN = 50
# A conversation's title until the model writes one: the start of its first message.
TITLE_LENGTH = 80

# The model: one call's longest answer, how long it may take and how often it's retried.
MAX_ANSWER_TOKENS = 1_500
MODEL_TIMEOUT_SECONDS = 60
MODEL_RETRIES = 2
# With nothing stored at OpenAI, a tool loop sends the model's reasoning back with each call.
MODEL_INCLUDE = ["reasoning.encrypted_content"]
# Steps that call tools in one turn; after the last, the model must answer with what it has.
MAX_TOOL_STEPS = 6
# A whole turn, tools included.
TURN_SECONDS = 90
# Turns streaming on one instance at once, each holding its request up to TURN_SECONDS: about half
# the instance's 80 requests (infra/terraform/locals.tf), so turns never take the slots that short
# requests, AI apps' MCP calls and Pub/Sub's pushes need. One more is refused (503) to be tried
# again after TURNS_BUSY_RETRY_SECONDS.
TURNS_AT_ONCE = 40
TURNS_BUSY_RETRY_SECONDS = 10
# A comment goes out after this long without an event, so proxies keep the stream open.
KEEP_ALIVE_SECONDS = 15
# The earlier messages the model reads with a new one: the latest this many, within this many
# characters (their tool results included while they fit).
HISTORY_MESSAGES = 20
HISTORY_CHARACTERS = 24_000

# What the user reads; translated by its English text.
CHAT_FAILED = "Couldn't get a reply right now. Please try again."
SESSION_EXPIRED = "Your session expired. Sign in again."
QUESTION_TOO_LONG = "The question is too long."
NOT_FOUND = "Not found"
COMPANY_NOT_FOUND = "Company not found"
# A tool call naming a company that isn't one of the user's (or an API key's), for the model.
OTHER_COMPANY = "This company isn't one of yours: use a company id from list_companies."
# With "all companies" picked and several of them, a company's interviews come with this note
# for the model (not the user's text): the company comes first, unless the user named it or
# the interview.
INTERVIEWS_TOOL = "list_interviews"
WHICH_COMPANY_FIRST = (
    "The user picked all companies and has {count}. Unless they named this company or an "
    "interview, don't offer these interviews: ask which company first, by name."
)
# The error event's code when a service refused the user's token mid-turn: the panel refreshes
# the token and sends the message again, once.
SESSION_EXPIRED_CODE = "session_expired"
