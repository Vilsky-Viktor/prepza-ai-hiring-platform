from enum import StrEnum


class Stage(StrEnum):
    """Where a signed-in user is, for the panel's welcome: what it says and the questions it
    offers. (Signed-out visitors are "signed_out", which the panel knows without asking.)"""

    NO_COMPANY = "no_company"
    UNVERIFIED = "unverified"
    NO_INTERVIEWS = "no_interviews"
    NO_CANDIDATES = "no_candidates"
    HAS_CANDIDATES = "has_candidates"


# The most companies, and interviews of a company, read to tell the stage.
WELCOME_LIMIT = 100
