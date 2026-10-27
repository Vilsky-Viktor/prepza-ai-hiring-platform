# How much the assistant may be used: the limits themselves are prepza_common.limits.limit_list's (read
# by name with limits.limit), so they can be edited in the admin zone. Messages are counted as
# they're sent; spending in tokens (input and output, every model call of a turn), added after
# each turn, so a turn already started always finishes.

# The limits for everyone (MESSAGES_PER_DAY, TOKENS_PER_DAY) and the daily AI spend cap hold only
# people working for a company that never topped up, so free accounts can't use them up for
# paying ones. Whether a company paid is asked of billing at most this often.
PAID_CACHE_SECONDS = 600
# Keys of the budgets for everyone, which the admin zone shows as used today.
ALL_TOKENS_KEY = "spend:assistant:all"
ALL_MESSAGES_KEY = "rate:assistant:all"

# The longest voice message (the panel stops recording then).
MAX_AUDIO_SECONDS = 60

# The most an app's registration may take (its JSON), and the longest `state` it sends with a
# request: both are kept (in Postgres for 30 days, in Redis for 10 minutes). Real ones are far
# smaller.
MAX_REGISTRATION_BYTES = 4_000
MAX_STATE_LENGTH = 512
