# Pending actions: what the model prepared, waiting for the user's confirmation. Kept only in
# Redis, never in the database, and gone on confirm, cancel or after this long.
ACTION_TTL_SECONDS = 10 * 60
ACTION_KEY = "assistant:action:{action_id}"
# A user's pending actions, so deleting their account deletes them too, and a conversation's,
# so opening it again shows their cards.
USER_ACTIONS_KEY = "assistant:actions:user:{user_id}"
CONVERSATION_ACTIONS_KEY = "assistant:actions:conversation:{conversation_id}"

# The card's states, as the panel shows them.
PENDING = "pending"
DONE = "done"
FAILED = "failed"
CANCELLED = "cancelled"

# What the model reads after preparing one, and with the confirmed result (it isn't the user's
# text: the app tells the model).
PENDING_FOR_MODEL = (
    "Prepared, not done: the panel shows the user a card with exactly this action, which runs "
    "only if they confirm it. Write no text about it: the card says it all."
)
CONFIRMED_NOTE = (
    "[From the app, not the user] The user confirmed the action {tool}; the service answered "
    "{result}. Tell them in one or two sentences what happened to this action alone and, if it "
    "worked, the likely next step. Other cards may still wait for their confirmation: don't "
    "comment on them, and don't prepare another action unless they ask."
)

# The model's preparing an action about something the user can't see (or that's gone).
SUBJECT_NOT_FOUND = "Not found, or you don't have access to it."
# Every value the model sent for a change is already so (for the model only).
NOTHING_TO_CHANGE = "Nothing to change: those values are already set."

# An address in an action that no one gave (for the model only).
UNKNOWN_EMAIL = "{address} isn't an address the user gave or the data shows: ask the user for it"

# What the user reads; translated by its English text.
ACTION_GONE = "This action expired or was already handled. Ask again to prepare it."
