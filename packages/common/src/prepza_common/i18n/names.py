from prepza_common.config.constants import MAX_CANDIDATE_NAME_LENGTH


def clean_name(*parts) -> str | None:
    """A candidate's name from untrusted fields (a sign-in, an inviter, an ATS: a whole name, or
    a first and a last name): the text ones joined, trimmed and cut to MAX_CANDIDATE_NAME_LENGTH;
    None when there's none. Shown only as text."""
    name = " ".join(part.strip() for part in parts if isinstance(part, str) and part.strip())

    return name[:MAX_CANDIDATE_NAME_LENGTH].strip() or None
