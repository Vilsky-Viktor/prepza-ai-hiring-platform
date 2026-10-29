# Where an API invite's return_url may take the candidate once they've finished: any https
# address, or http on the developer's own computer while testing (as OAuth redirect addresses
# allow). The frontend links to it, so no other scheme (javascript:, data:) ever gets through.
LOCAL_HOSTS = ("localhost", "127.0.0.1")
# A refused return_url, as the 422 names it.
RETURN_URL_INVALID = "return_url must be an https address (http only on localhost, for testing)."
