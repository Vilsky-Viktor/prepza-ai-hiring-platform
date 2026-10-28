from library.core.db import Session
from library.repositories import user_data


async def delete_data(user_id: str) -> None:
    """What library keeps under the user's id (user_data.delete_user), in one save; safe to
    repeat."""
    async with Session.begin() as session:
        await user_data.delete_user(session, user_id)


async def export_data(user_id: str) -> dict:
    async with Session() as session:
        return await user_data.export(session, user_id)
