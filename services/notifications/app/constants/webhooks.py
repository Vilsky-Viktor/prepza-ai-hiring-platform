# Resend's webhook events meaning the email never reached the inbox: a bounce, a spam complaint,
# an address Resend won't send to after an earlier one, or an email it couldn't send at all (its
# quota, say). Only bounces, complaints and suppressions suppress the address; a failure is
# Resend's, not the address's. `email.delivery_delayed` is temporary: not subscribed to.
BOUNCED_EVENT = "email.bounced"
COMPLAINED_EVENT = "email.complained"
SUPPRESSED_EVENT = "email.suppressed"
FAILED_EVENT = "email.failed"
UNDELIVERED_EVENTS = {BOUNCED_EVENT, COMPLAINED_EVENT, SUPPRESSED_EVENT, FAILED_EVENT}

# Resend signs each webhook with a timestamp; older ones are refused, so a captured one can't
# be replayed.
WEBHOOK_TOLERANCE_SECONDS = 5 * 60
# A web hook's work (the suppression list, telling companies and library) is done within this
# long, inside Resend's deadline of about 30 s; past it the answer is a 503, and Resend sends the
# event again: every step is safe to repeat.
RESEND_HOOK_SECONDS = 20

# Tags Resend's webhooks carry back: what the email is and its id. A candidate's invite:
# "candidate_invite" and the invite's id; their reminder: "candidate_reminder", the invite's id
# and the company's (reminders sent before it had its own kind carry the invite's); an optional
# email: its unsubscribe type ("digest", "reminders", "updates") and the user's id, and a
# campaign's also its bulk send's id (constants/bulk.py SEND_TAG).
KIND_TAG = "kind"
ID_TAG = "id"
COMPANY_TAG = "company"
CANDIDATE_INVITE_KIND = "candidate_invite"
CANDIDATE_REMINDER_KIND = "candidate_reminder"
# Both are about an invite, which a failed one marks undelivered.
CANDIDATE_KINDS = (CANDIDATE_INVITE_KIND, CANDIDATE_REMINDER_KIND)
