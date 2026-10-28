import uuid

from site_content.constants.events import CONTACT_SENT
from site_content.core.db import Session
from site_content.repositories import outbox
from site_content.services import accounts


async def send(email: str, message: str) -> None:
    async with Session.begin() as session:
        outbox.add(
            session,
            CONTACT_SENT,
            {"name": "Ann", "email": email, "message": message, "language": "en"},
        )


def test_a_users_contact_messages_are_exported_and_deleted_by_their_email(run):
    """Whatever the case they wrote it in; another sender's messages stay, and deleting again
    deletes nothing more."""
    ann = f"ann-{uuid.uuid4().hex[:8]}@example.com"
    bob = f"bob-{uuid.uuid4().hex[:8]}@example.com"

    async def scenario():
        await send(ann.upper(), "Do you offer invoices?")
        await send(bob, "Hello")
        exported = await accounts.export_user(ann)
        await accounts.remove_user(ann)
        await accounts.remove_user(ann)

        return exported, await accounts.export_user(ann), await accounts.export_user(bob)

    exported, after, others = run(scenario())

    assert [(m["email"], m["message"]) for m in exported["contact_messages"]] == [
        (ann.upper(), "Do you offer invoices?")
    ]
    assert after == {"contact_messages": []}
    assert [m["message"] for m in others["contact_messages"]] == ["Hello"]
