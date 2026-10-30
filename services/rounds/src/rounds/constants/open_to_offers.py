import re

# Open to offers: a practice user's opt-in to be listed on the Discover tab of paying companies'
# interviews whose topics and level match their practice (docs/features/templates-and-practice.md).

# The version of the switch's wording the person agreed to (the frontend's openToOffers texts):
# a change to what it says is shared gets a new version, so the consent log tells which wording
# each choice was made under.
CONSENT_VERSION = "2026-10-30"
# An opt-in lapses this many days after it was last turned on, so nobody who stopped looking
# stays listed for good (the privacy policy says so); turning it on again starts it anew.
OPEN_DAYS = 365
# A LinkedIn profile's address: linkedin.com/in/<their handle>, with or without https:// and a
# country subdomain (www., uk.). Kept as https://www.linkedin.com/in/<handle>.
LINKEDIN_PROFILE = re.compile(
    r"(?:https?://)?(?:[a-z]{2,3}\.)?linkedin\.com/in/([A-Za-z0-9\-_%]{3,100})/?",
    re.IGNORECASE,
)
LINKEDIN_URL = "https://www.linkedin.com/in/{handle}"
LINKEDIN_INVALID = "Enter your LinkedIn profile's address, like linkedin.com/in/your-name."
CONSENT_OUTDATED = "The text you agreed to has changed. Reload the page and try again."
# The refusals' stable codes.
LINKEDIN_INVALID_CODE = "linkedin_invalid"
CONSENT_OUTDATED_CODE = "consent_outdated"
# Companies' Discover tab: how many practice topics one request may match, at most.
MAX_MATCH_TOPICS = 500
