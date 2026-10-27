from prepza_common.auth.user import Language, User
from pydantic import BaseModel


class SettingsIn(BaseModel):
    language: Language


class MeOut(User):
    """The signed-in user, and whether they may open the superadmin pages."""

    is_superadmin: bool
