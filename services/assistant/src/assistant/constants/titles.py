# A conversation's title in the history: a one-line summary the model writes after the first
# answer and again after every TITLE_EVERY-th question; until then, the first question's start.
TITLE_EVERY = 5
MAX_TITLE_LENGTH = 60
# The cheap call (its model and effort are settings): a few output tokens, and at most this
# much of the chat.
TITLE_MAX_TOKENS = 60
TITLE_SOURCE_CHARACTERS = 4_000
