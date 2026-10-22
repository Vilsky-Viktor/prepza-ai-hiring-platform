# A few short queries per chat turn, so a small pool: 4 per instance.
DB_POOL_SIZE = 1
DB_MAX_OVERFLOW = 1
# The retention job deletes idle conversations this many at a time (their messages and tool
# calls go with them).
RETENTION_BATCH = 500
