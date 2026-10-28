# Another service's answers to a consumer's call that no retry changes: the request was
# malformed, or what the event names doesn't exist (anymore). An event whose handling gets one
# is dropped rather than retried (prepza_common.events.unhandleable). A refused sign-in
# (401, 403), a conflict and an overload (408, 409, 429, 5xx) are retried: a fixed key or a
# finished deploy lets the event through.
FINAL_STATUSES = (400, 404, 410, 422)
