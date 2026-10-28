from generation.core.db import Session
from generation.repositories import accounts


async def delete_user(user_id: str) -> None:
    """Part of deleting an account: the user's generations stay with their company, without
    the user's id. Safe to repeat."""
    async with Session.begin() as session:
        await accounts.delete_user(session, user_id)
