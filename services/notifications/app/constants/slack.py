from prepza_common.notifications import NotificationKind

# Slack's "Add to Slack" (OAuth v2): where a company approves, where the code becomes its web hook
# and a token, and where the token is revoked on disconnecting.
SLACK_AUTHORIZE_URL = "https://slack.com/oauth/v2/authorize"
SLACK_ACCESS_URL = "https://slack.com/api/oauth.v2.access"
SLACK_REVOKE_URL = "https://slack.com/api/auth.revoke"
# Only to post to the one channel the company picks while approving.
SLACK_SCOPE = "incoming-webhook"
# Where Slack's incoming web hooks live: a web hook anywhere else is refused, never posted to.
SLACK_HOOKS = "https://hooks.slack.com/"
# Where Slack sends the company back, and the page that then opens.
SLACK_CALLBACK = "{site}/api/notifications/slack/callback"
SLACK_PAGE = "{site}/companies/{company_id}/integrations/slack"
# The same page, as a notification opens it.
SLACK_LINK = "/companies/{company_id}/integrations/slack"
# How long an "Add to Slack" trip may take, from the button to the callback.
SLACK_STATE_SECONDS = 15 * 60
# A trip's nonce in Redis, until the callback takes it (once) or SLACK_STATE_SECONDS pass.
SLACK_STATE_KEY = "slack:state:{nonce}"
# What the state's signing key is made for (prepza_common.tokens.purpose_key).
SLACK_STATE_PURPOSE = "slack-state"
SLACK_TIMEOUT_SECONDS = 10
# What Slack answers when the web hook is gone (the app removed, the channel deleted or
# archived): the connection needs reconnecting.
SLACK_GONE = {
    "invalid_token",
    "no_service",
    "channel_not_found",
    "channel_is_archived",
    "no_active_hooks",
}

# The company's notifications a channel can get, in the order the page lists them, and the ones
# on by default.
SLACK_KINDS = [
    NotificationKind.CANDIDATE_FINISHED,
    NotificationKind.ATS_NOT_INVITED,
    NotificationKind.INVITE_UNDELIVERED,
    NotificationKind.INTERVIEW_READY,
    NotificationKind.AUTO_TOP_UP_CHARGED,
    NotificationKind.AUTO_TOP_UP_FAILED,
]
SLACK_DEFAULT_KINDS = [
    NotificationKind.CANDIDATE_FINISHED,
    NotificationKind.ATS_NOT_INVITED,
    NotificationKind.INVITE_UNDELIVERED,
    NotificationKind.AUTO_TOP_UP_FAILED,
]


class SlackStatus:
    CONNECTED = "connected"
    # Slack no longer takes its messages: reconnect.
    BROKEN = "broken"


# A dot between two letters or digits, as in a domain or an email: Slack would make it a link.
LINKABLE_DOT = r"(?<=\w)\.(?=\w)"
# Put after such a dot, so the text reads the same but Slack doesn't link it.
ZERO_WIDTH_SPACE = "\u200b"
