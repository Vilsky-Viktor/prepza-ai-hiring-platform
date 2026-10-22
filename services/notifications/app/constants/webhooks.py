# Resend's webhook events meaning the email never reached the inbox: a bounce, a spam complaint,
# an address Resend won't send to after an earlier one, or an email it couldn't send at all (its
# quota, say). Only bounces, complaints and suppressions suppress the address; a failure is
# Resend's, not the address's. `email.delivery_delayed` is temporary: not subscribed to.
BOUNCED_EVENT = "email.bounced"
COMPLAINED_EVENT = "email.complained"
FAILED_EVENT = "email.failed"
UNDELIVERED_EVENTS = {BOUNCED_EVENT, COMPLAINED_EVENT, "email.suppressed", FAILED_EVENT}

# Resend signs each webhook with a timestamp; older ones are refused, so a captured one can't
# be replayed.
WEBHOOK_TOLERANCE_SECONDS = 5 * 60

# Tags Resend's webhooks carry back: what the email is and its id. A candidate's invite and
# reminder: "candidate_invite" and the invite's id; an optional email: its unsubscribe type
# ("digest", "reminders", "updates") and the user's id, and a campaign's also its bulk send's id
# (constants/bulk.py SEND_TAG).
KIND_TAG = "kind"
ID_TAG = "id"
CANDIDATE_INVITE_KIND = "candidate_invite"
