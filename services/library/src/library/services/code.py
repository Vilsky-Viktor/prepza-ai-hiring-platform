import uuid

from library.core.db import Session
from library.repositories import code


async def tag(languages: dict[uuid.UUID, str], fence: str) -> None:
    """Each question's example, opening with `fence`, gets its language."""
    async with Session.begin() as session:
        await code.tag(session, languages, fence)
