# What scrub.py takes out of Sentry's events and Langfuse's traces (an email: constants.
# EMAIL_PATTERN).
REDACTED_EMAIL = "[email]"
# A URL's path, query and user info can carry credentials (a Slack web hook's path, a customer's
# web hook secret, an invite token): only its scheme and host (group 1) reach Sentry, and the
# fields that hold a query alone are dropped.
URL_PATTERN = r"(https?://)(?:[^\s/?#@'\"]*@)?([^\s/?#'\"]+)[^\s'\"]*"
URL_SCRUBBED = r"\1\2"
QUERY_FIELDS = {"query_string", "http.query", "http.fragment"}
# Langfuse: a person's name or email in a field of data or of JSON text (an assistant tool's
# result) is masked too: any field whose name ends so (`candidate_name`); group 1 keeps the key.
PERSON_FIELD_ENDINGS = ("name", "email")
PERSON_FIELD_PATTERN = r'("[a-z_]*(?:name|email)"\s*:\s*)"(?:[^"\\]|\\.)*"'
REDACTED_PERSON = "[person]"
