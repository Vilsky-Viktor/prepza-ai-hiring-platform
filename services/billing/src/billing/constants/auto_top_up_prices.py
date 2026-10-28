# What an automatic top-up charges, and how a new price is announced before it applies.

# A new price for an automatic top-up applies from midnight (UTC) this many days after the
# company is told, so at least 30 days pass, as the terms promise.
AUTO_TOP_UP_PRICE_NOTICE_DAYS = 31
# The daily check of automatic top-ups' prices reads this many at a time, and at most this many
# pages a run; the rest waits for the next run.
PRICE_CHECK_BATCH = 200
PRICE_CHECK_MAX_PAGES = 50
