from prepza_common.auth.user import User


class MeOut(User):
    """The signed-in user, and whether they may open the superadmin pages."""

    is_superadmin: bool
