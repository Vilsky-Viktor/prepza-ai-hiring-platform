from pydantic import BaseModel
from testee_common.auth.user import Language, User


class SettingsIn(BaseModel):
    language: Language


class MeOut(User):
    """The signed-in user, and whether they may open the superadmin pages."""

    is_superadmin: bool
