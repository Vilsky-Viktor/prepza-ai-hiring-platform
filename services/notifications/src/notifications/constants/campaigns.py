# Campaigns (the admin zone's Campaigns tab): product updates and offers to the users who chose
# them, and important notices to everyone they concern, sent through the bulk sender.
from enum import StrEnum


class AudienceGroup(StrEnum):
    """Whom a campaign goes to, besides everyone: the people who joined a company (members), who
    took a company's interview (candidates, rounds' interview sessions) or a free practice round
    (learners, rounds' practice sessions). Someone in several groups gets it once."""

    MEMBERS = "members"
    CANDIDATES = "candidates"
    LEARNERS = "learners"


# An important notice to some companies only (an incident that affects them) names at most this
# many.
MAX_NOTICE_COMPANIES = 50

# A campaign made from a news post: its button's text and the page it opens.
NEWS_BUTTON = "Read the news"
NEWS_LINK = "/news#{news_id}"

# How many campaigns of each kind may go out a day is the CAMPAIGNS_PER_KIND_DAY limit; of
# important notices, the stricter NOTICES_PER_DAY.
ONE_A_DAY = (
    "Today's limit of campaigns of this kind ({limit}) is reached. Send the next one tomorrow."
)
NOT_FOUND = "Not found"
ALREADY_SENT = "This campaign was already sent, so it can't be changed."
NOT_SENT = "This campaign hasn't been sent."
CHANGED = "This campaign's kind was changed meanwhile. Check it and send it again."
LINK_NOT_ON_SITE = "The button's link must be a page on testee, starting with /."
NO_BUTTON_TEXT = "Give the button a text, or leave its link empty too."
NOT_ACKNOWLEDGED = (
    "Confirm that this notice is about the service itself, not a promotion, before sending it."
)
OWNERS_NEED_COMPANIES = "Owners and admins only applies to companies: choose companies too."
COMPANIES_ONLY_NOTICES = "Only an important notice can go to some companies only."
