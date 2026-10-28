from assistant.constants.welcome import Stage


def stage(companies: list[dict], has_candidates: bool) -> Stage:
    """The furthest stage the user's companies (as companies lists them) have reached: none yet,
    not verified, verified without interviews, interviews without candidates, candidates."""
    if not companies:
        return Stage.NO_COMPANY

    if has_candidates:
        return Stage.HAS_CANDIDATES

    if any(company.get("interview_count") for company in companies):
        return Stage.NO_CANDIDATES

    if any(company.get("verified_domain") for company in companies):
        return Stage.NO_INTERVIEWS

    return Stage.UNVERIFIED
