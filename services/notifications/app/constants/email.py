RESEND_EMAILS_URL = "https://api.resend.com/emails"
SEND_TIMEOUT_S = 10
# Resend's answers that no retry can change: a malformed request or an address it won't send to.
# Rate limits (resend.ResendBusy), outages and a wrong API key are retried instead.
RESEND_REFUSED = (400, 422)
# The name in Resend's 429 error once the account's daily sending quota is used up (other 429s
# are its per-second limit).
RESEND_DAILY_QUOTA_ERROR = "daily_quota_exceeded"
# Resend's 409s about the idempotency key: used within 24 hours with a changed body, so the email
# already went out (never retried); or the same key still in progress (retried, nothing sent yet).
RESEND_ALREADY_SENT = "invalid_idempotent_request"
RESEND_IN_PROGRESS = "concurrent_idempotent_requests"
# On every email (RFC 3834): sent by a program, so mail servers and clients send it no
# out-of-office or other automatic replies.
AUTOMATED_HEADERS = {"Auto-Submitted": "auto-generated"}
# A report's attachment name: characters file systems or mail clients mishandle become spaces,
# and the name is cut to this length before ".pdf".
UNSAFE_FILENAME = r'[\\/:*?"<>|\x00-\x1f\x7f]+'
MAX_FILENAME_LENGTH = 100
