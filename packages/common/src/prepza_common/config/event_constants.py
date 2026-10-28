# Another service's answers to a consumer's call that no retry changes: the request was
# malformed, or what the event names doesn't exist (anymore). An event whose handling gets one
# is dropped rather than retried (prepza_common.events.unhandleable). A refused sign-in
# (401, 403), a conflict and an overload (408, 409, 429, 5xx) are retried: a fixed key or a
# finished deploy lets the event through.
FINAL_STATUSES = (400, 404, 410, 422)

# A record without an outbox (an AI call, a limit hit) is published again after a jittered wait
# from this many seconds (backoff.wait_seconds).
PUBLISH_RETRY_FIRST_WAIT = 0.2
# Pub/Sub: the one topic every domain event goes to, and its REST API.
EVENTS_TOPIC = "events"
PUBSUB_URL = "https://pubsub.googleapis.com"
# An event's id (its outbox row's, the same on each re-send) and family (type to the first dot).
EVENT_ID_ATTRIBUTE = "event_id"
# The trace header of the request that saved the event (TRACE_HEADER's value), so the consumer's
# lines and calls join the action that caused it (observability.logging.follow_trace).
TRACE_ATTRIBUTE = "trace"
FAMILY_ATTRIBUTE = "family"
# When the change behind an event happened (ISO 8601): the outbox row's time, the same however
# often it's published, so a consumer can put events in order.
OCCURRED_AT_ATTRIBUTE = "occurred_at"
# Publishing from inside a user's request waits at most this long; the scheduled flush sends
# whatever didn't make it.
PUBLISH_IN_REQUEST_TIMEOUT_SECONDS = 5

# Outbox: events published per call to Pub/Sub, and how long published ones are kept. The
# scheduled flush sends batch after batch until none wait, starting no new batch after
# OUTBOX_FLUSH_SECONDS, so a run (plus its last call's timeout) ends within the shortest
# service timeout (60 s) and a backlog drains in minutes.
OUTBOX_BATCH = 100
OUTBOX_FLUSH_SECONDS = 20
OUTBOX_KEEP_DAYS = 7
# Pub/Sub's answers that mean it won't take a message (too large or malformed): the event is
# tried alone, and parked after OUTBOX_MAX_ATTEMPTS of them so it can't hold up the others.
# Outages and other errors count against no event; the events wait for the next flush.
OUTBOX_REJECTED_STATUSES = (400, 413)
OUTBOX_MAX_ATTEMPTS = 5
