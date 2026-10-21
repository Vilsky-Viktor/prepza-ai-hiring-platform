# A user's deletion or export in one service: it may delete or read every company the user owns,
# and the service may be starting cold, so it waits longer than an ordinary call between services.
ACCOUNT_CALL_TIMEOUT_SECONDS = 60
# Deleted accounts are remembered as long as the database's backups last (14 kept, a day each),
# so a restore's deletions can be run again; then forgotten.
ERASURE_KEEP_DAYS = 14
