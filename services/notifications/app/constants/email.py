RESEND_EMAILS_URL = "https://api.resend.com/emails"
# Resend's own suppression list, one address (or its id) at a time; taking one off needs a key
# with full access, not a sending-only one.
RESEND_SUPPRESSION_URL = "https://api.resend.com/suppressions/{address}"
SEND_TIMEOUT_S = 10
# Requests to Resend a second, from every instance and run together (a Redis counter per
# second): under its limit of 10 a team, with room for a retry.
RESEND_PER_SECOND = 8
RESEND_PACE_KEY = "resend:pace"
# Resend's answers that no retry can change: a malformed request or an address it won't send to.
# Rate limits (resend.ResendBusy), outages and a wrong API key are retried instead.
RESEND_REFUSED = (400, 422)
# The names in Resend's 429 error once the account's daily or monthly sending quota is used up
# (other 429s are its per-second limit): both are counted as its quota (RESEND_DAILY_QUOTA).
RESEND_QUOTA_ERRORS = ("daily_quota_exceeded", "monthly_quota_exceeded")
# Resend's 409s about the idempotency key: used within 24 hours with a changed body, so the email
# already went out (never retried); or the same key still in progress (retried, nothing sent yet).
RESEND_ALREADY_SENT = "invalid_idempotent_request"
RESEND_IN_PROGRESS = "concurrent_idempotent_requests"
# A value shown left to right inside a right-to-left text: an email address or a link.
LTR_VALUE = r"[^\s@]+@[^\s@]+|https?://\S+"
# On every email (RFC 3834): sent by a program, so mail servers and clients send it no
# out-of-office or other automatic replies.
AUTOMATED_HEADERS = {"Auto-Submitted": "auto-generated"}
# A report's attachment name: characters file systems or mail clients mishandle become spaces,
# and the name is cut to this length before ".pdf".
UNSAFE_FILENAME = r'[\\/:*?"<>|\x00-\x1f\x7f]+'
MAX_FILENAME_LENGTH = 100
