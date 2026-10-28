from site_content.core.db import Session
from site_content.repositories import outbox


async def remove_user(email: str) -> None:
    """The contact messages the user sent from their account's email and site still keeps (until
    a week after they're emailed); safe to repeat."""
    async with Session.begin() as session:
        await outbox.delete_contact_messages(session, email)


async def export_user(email: str) -> dict:
    """The user's own contact messages site still keeps, in plain terms, for their data
    export."""
    async with Session() as session:
        rows = await outbox.contact_messages(session, email)

    return {
        "contact_messages": [
            {
                "name": row.data["name"],
                "email": row.data["email"],
                "message": row.data["message"],
                "sent_at": row.created_at,
            }
            for row in rows
        ],
    }
