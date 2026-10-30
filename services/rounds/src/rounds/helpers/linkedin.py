from rounds.constants.open_to_offers import LINKEDIN_PROFILE, LINKEDIN_URL


def linkedin_profile(text: str) -> str | None:
    """The LinkedIn profile's address in one form (https://www.linkedin.com/in/<handle>); None
    when the text isn't a profile's address (a company page, a post, another site)."""
    found = LINKEDIN_PROFILE.fullmatch(text.strip())

    if found is None:
        return None

    return LINKEDIN_URL.format(handle=found.group(1))
