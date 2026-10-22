# Langfuse's records of AI calls are kept TRACE_RETENTION_DAYS, as the privacy policy says. Its
# free plan reads back only the last 30 days, so a trace is deleted a day before then, while it
# can still be found (trace_retention.py).
TRACE_RETENTION_DAYS = 30
TRACE_DELETE_AFTER_DAYS = TRACE_RETENTION_DAYS - 1
# Langfuse's public API: root observations (one a trace) found by start time, a page at a time
# (at most 1000), and traces deleted by id, at most this many a call (its docs' batch).
OBSERVATIONS_PATH = "/api/public/v2/observations"
TRACES_PATH = "/api/public/traces"
TRACE_PAGE = 1000
TRACE_DELETE_BATCH = 1000
# Calls to Langfuse: a timeout, and tries on its rate limit (429) or an outage, the wait at least
# its Retry-After, otherwise doubling with jitter from TRACE_FIRST_WAIT_SECONDS.
TRACE_TIMEOUT_SECONDS = 30
TRACE_ATTEMPTS = 5
TRACE_FIRST_WAIT_SECONDS = 2
