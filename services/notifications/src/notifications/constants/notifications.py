# A few short queries per request (streams hold no connection), so a small pool: 2 per instance,
# as infra/terraform/locals.tf budgets it.
DB_POOL_SIZE = 1
DB_MAX_OVERFLOW = 1
# The bell shows the latest few. A recipient keeps at most MAX_PER_RECIPIENT, none older than
# KEEP_DAYS.
DROPDOWN_LIMIT = 10
MAX_PER_RECIPIENT = 100
KEEP_DAYS = 90
# Each new notification removes up to this many expired ones (and their received events), which
# keeps up with how many arrive.
EXPIRED_PER_PRUNE = 100
# Kinds that can come in bursts. One about the same thing (its page and title) within
# GROUP_HOURS of the last adds to it, "3 candidates finished …", instead of a new one.
GROUPED_KINDS = {
    "candidate_finished",
    "invite_undelivered",
    "question_flagged",
    "question_fixed",
    "ats_not_invited",
}
GROUP_HOURS = 24
# A user's open tabs hear about a recipient's new notification on this Redis channel. Each
# instance holds one subscription to them all (CHANNELS) and passes each on to its open tabs.
CHANNEL = "notifications:{recipient}:{recipient_id}"
CHANNELS = "notifications:*"
# After losing that subscription, it's made again this long after.
RESUBSCRIBE_SECONDS = 1
# A stream sends a comment this often, so proxies (nginx, the load balancer) don't close it as
# idle.
HEARTBEAT_SECONDS = 20

# Open bell streams one user may hold (a tab each; limit_list.LIMITS), so one account can't take
# every slot the stream service has; a slot left by a crash frees itself after the longest a
# stream lives.
STREAMS_LIMIT = "STREAMS_PER_USER"
STREAM_SLOT_SECONDS = 3600
# A user's companies are kept this long, so every tab's (re)connect doesn't ask companies.
COMPANY_IDS_SECONDS = 60
COMPANY_IDS_KEY = "notifications:company-ids:{user_id}"
# A stream ends after this long, so the tab reconnects and hears a company joined meanwhile;
# sooner, after STREAM_RETRY_SECONDS, when companies didn't answer and it holds only the user's
# own notifications.
STREAM_REFRESH_SECONDS = 300
STREAM_RETRY_SECONDS = 60
# When a user's account was made (library), kept this long: everyone's notifications newer than
# it are theirs.
ACCOUNT_CREATED_SECONDS = 3600
ACCOUNT_CREATED_KEY = "notifications:account-created:{user_id}"
