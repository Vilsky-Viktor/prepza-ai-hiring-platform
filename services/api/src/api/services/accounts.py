from uuid import UUID

from fastapi.encoders import jsonable_encoder

from api.core.db import Session
from api.repositories import keys, webhook_retries, webhooks


async def remove_user(user_id: str, email: str | None) -> None:
    """An account deleted in library: the keys and web hooks it made go, and, with its `email`,
    its results as a candidate waiting to be sent again to companies' web hooks. All at once or
    nothing, so a retry finds everything still to delete."""
    async with Session.begin() as session:
        await keys.remove_user(session, user_id)
        await webhooks.remove_user(session, user_id)

        if email is not None:
            await webhook_retries.remove_email(session, email)


async def export_user(user_id: str) -> dict:
    """For "Download my data": the keys (names only) and web hooks the user made."""
    async with Session() as session:
        made_keys = await keys.of_user(session, user_id)
        made_hooks = await webhooks.of_user(session, user_id)

    return jsonable_encoder(
        {
            "api_keys": [
                {"company_id": key.company_id, "name": key.name, "at": key.created_at}
                for key in made_keys
            ],
            "webhooks": [
                {"company_id": hook.company_id, "url": hook.url, "at": hook.created_at}
                for hook in made_hooks
            ],
        }
    )


async def remove_company(company_id: UUID) -> None:
    """A deleted company: its keys and web hooks go together."""
    async with Session.begin() as session:
        await keys.remove_company(session, company_id)
        await webhooks.remove_company(session, company_id)


async def remove_candidate(company_id: UUID, interview_id: str, email: str) -> None:
    """A candidate the company erased: their results waiting to be sent again go."""
    async with Session.begin() as session:
        await webhook_retries.remove_candidate(session, company_id, interview_id, email)


async def remove_interview(company_id: UUID, interview_id: str) -> None:
    """A deleted interview: its candidates' results waiting to be sent again go."""
    async with Session.begin() as session:
        await webhook_retries.remove_interview(session, company_id, interview_id)
