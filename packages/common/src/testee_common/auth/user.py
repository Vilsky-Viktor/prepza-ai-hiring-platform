from typing import Literal

from pydantic import BaseModel, Field
from testee_common.config.constants import DEFAULT_LANGUAGE, LANGUAGES, LEVELS

# A supported language's code (LANGUAGES).
Language = Literal[tuple(LANGUAGES)]
# A test's level (LEVELS).
Level = Literal[LEVELS]


class User(BaseModel):
    uid: str
    email: str
    email_verified: bool
    name: str | None = None
    language: Language = DEFAULT_LANGUAGE
    # How this sign-in was made ("google.com", "github.com", "password", "custom" for a token a
    # service signed): the admin zone takes only Google's. Never part of an answer.
    sign_in_provider: str | None = Field(default=None, exclude=True)


class UserEmailIn(BaseModel):
    """An email address sent in the body, so request logs don't record it: the account's, in
    accounts' calls to delete or export a user's data, or the one a superadmin looks up."""

    email: str
