# A user's deletion or export in one service: it may delete or read every company the user owns,
# and the service may be starting cold, so it waits longer than an ordinary call between services.
ACCOUNT_CALL_TIMEOUT_SECONDS = 60
# Deleted accounts are remembered as long as the database's backups last (14 kept, a day each),
# so a restore's deletions can be run again; then forgotten.
ERASURE_KEEP_DAYS = 14
# Replaying them (services/erasures.py): ERASURE_BATCH at once, newest first (a restore from a
# recent backup brings back the latest), and no batch started after ERASURE_RUN_SECONDS, so the
# last batch (one account call's time) ends inside this service's 150 s request timeout. A run
# stopped for time leaves the rest; the next starts again from the newest.
ERASURE_BATCH = 10
ERASURE_RUN_SECONDS = 60
