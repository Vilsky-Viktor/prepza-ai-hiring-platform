from datetime import datetime

from pydantic import BaseModel, Field

from accounts.constants.emails import FIREBASE_LOOKUP_LIMIT


class AccountOut(BaseModel):
    """A testee account, for the admin zone's support tab: `email` is None for an account
    without one (a company's guest candidate), `created_at` when Firebase doesn't say."""

    user_id: str
    email: str | None
    created_at: datetime | None


class ProfilesIn(BaseModel):
    user_ids: list[str] = Field(max_length=FIREBASE_LOOKUP_LIMIT)


class ProfileOut(BaseModel):
    """How an account shows itself to its team: its name (its email without one) and picture."""

    user_id: str
    name: str | None
    photo_url: str | None


class ProfilesOut(BaseModel):
    # Accounts that are gone are left out.
    profiles: list[ProfileOut]
