# The check that a pasted text names anything to test (services/screen.py): the user waits on
# it inside the create call, so it's short; a timeout or failure lets the text through.
SCREEN_TIMEOUT_SECONDS = 5
SCREEN_RETRIES = 0
SCREEN_MAX_TOKENS = 20
# What the user reads when the text names nothing to test; translated by its English text.
NOTHING_TO_TEST = (
    "This text doesn't name anything to test. Paste a job description, a role, or the skills "
    "to test."
)
