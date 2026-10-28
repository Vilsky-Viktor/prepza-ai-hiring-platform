import re

from pydantic import EmailStr, TypeAdapter, ValidationError

from companies.constants.invites import EMAIL_PATTERN

EMAIL = TypeAdapter(EmailStr)


def emails_in(text: str) -> list[str]:
    """Everything in pasted or uploaded text that looks like an email, lowercased, each once, in
    the order it first appears."""
    found = (match.lower().strip(".") for match in re.findall(EMAIL_PATTERN, text))

    return list(dict.fromkeys(found))


def is_email(text: str) -> bool:
    try:
        EMAIL.validate_python(text)
    except ValidationError:
        return False

    return True
