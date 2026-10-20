# A user's deletion or export in one service: it may delete or read every company the user owns,
# and the service may be starting cold, so it waits longer than an ordinary call between services.
ACCOUNT_CALL_TIMEOUT_SECONDS = 60
