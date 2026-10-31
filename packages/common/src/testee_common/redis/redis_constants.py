# A Redis command whose connection dropped (Redis restarted, or the network blinked) is tried
# again on a new one, up to this many times, instead of failing its request; a connection
# idle this long is checked before use.
REDIS_RETRIES = 3
REDIS_HEALTH_CHECK_SECONDS = 30
# Connecting to Redis, and each command, gives up after this long (Upstash answers in
# milliseconds from the same region), so a Redis outage costs a request seconds, not its deadline.
REDIS_TIMEOUT_SECONDS = 2
