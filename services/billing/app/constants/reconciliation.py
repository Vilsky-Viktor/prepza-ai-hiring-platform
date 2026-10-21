from datetime import timedelta

# Once a day billing reads back from Paddle what its web hooks should have done: the completed
# transactions updated, and the approved adjustments created, in this window. Paddle retries a
# web hook for about two days, so a week covers one it gave up on, with days to spare.
RECONCILE_WINDOW = timedelta(days=7)
# Paddle's largest page, and the most pages one run reads of each list, so it ends well within
# billing's request timeout; the next run reads the rest.
PADDLE_PAGE_SIZE = 200
RECONCILE_MAX_PAGES = 10
