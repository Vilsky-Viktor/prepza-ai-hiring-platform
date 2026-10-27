from collections.abc import Callable
from typing import Annotated

from prepza_common.config.constants import MAX_TITLE_LENGTH, MIN_TITLE_LENGTH, TITLE_TOO_SHORT
from pydantic import AfterValidator, Field


def at_least(minimum: int, too_short: str) -> Callable[[str], str]:
    """A check for an edited name or title: kept without spaces at either end, refused (422,
    `too_short`, translated) under `minimum` characters."""

    def checked(value: str) -> str:
        value = value.strip()

        if len(value) < minimum:
            raise ValueError(too_short)

        return value

    return checked


# A test's or a template's title as a member or superadmin edits it.
Title = Annotated[
    str,
    Field(max_length=MAX_TITLE_LENGTH),
    AfterValidator(at_least(MIN_TITLE_LENGTH, TITLE_TOO_SHORT)),
]
