from pydantic import BaseModel


class UserEmailIn(BaseModel):
    """The deleted account's verified email (empty when it wasn't verified), sent by library."""

    email: str = ""
