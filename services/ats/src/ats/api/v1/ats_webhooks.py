from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from prepza_common.http.client_ip import limit_address
from prepza_common.limits.rate_limit import hit_or_skip

from ats.integrations.redis import get_redis
from ats.services import ats_webhooks


async def count_sender(request: Request) -> None:
    """Every web hook is counted by its sending address before its signature (and the database
    lookup that needs) is checked, against floods: generous, as an ATS sends for many companies
    from few addresses; with Redis down, not counted."""
    key = f"rate:ats-webhooks:{limit_address(request)}"
    await hit_or_skip(get_redis(), key, "ATS_WEBHOOKS_PER_IP_MINUTE")


router = APIRouter(prefix="/webhooks", tags=["webhooks"], dependencies=[Depends(count_sender)])


@router.post("/workable/{link_id}", status_code=status.HTTP_200_OK)
async def workable_event(link_id: UUID, request: Request) -> None:
    """Workable's events for one linked job, signed with the account's token (checked on the raw
    body). Open in maintenance mode like every /webhooks/ route, so no candidate is lost."""
    await ats_webhooks.receive_workable(
        link_id, await request.body(), request.headers.get("x-workable-signature", "")
    )


@router.post("/greenhouse/{connection_id}", status_code=status.HTTP_200_OK)
async def greenhouse_event(connection_id: UUID, request: Request) -> None:
    """The company's Greenhouse web hook (stage changes), signed with the connection's secret key
    (the Signature header, checked on the raw body). Greenhouse's ping on saving it is
    answered too."""
    await ats_webhooks.receive_greenhouse(
        connection_id, await request.body(), request.headers.get("signature", "")
    )


@router.post("/teamtailor/{connection_id}", status_code=status.HTTP_200_OK)
async def teamtailor_event(connection_id: UUID, request: Request) -> None:
    """The company's Teamtailor web hook (job applications changed), signed with the signature
    key Teamtailor gave it (the TT-Signature header, checked on the raw body)."""
    await ats_webhooks.receive_teamtailor(
        connection_id, await request.body(), request.headers.get("tt-signature", "")
    )


@router.post("/recruitee/{connection_id}", status_code=status.HTTP_200_OK)
async def recruitee_event(connection_id: UUID, request: Request) -> None:
    """The company's Recruitee web hook (candidates moved), signed with the secret Recruitee
    shows for it (the X-Recruitee-Signature header, checked on the raw body)."""
    await ats_webhooks.receive_recruitee(
        connection_id, await request.body(), request.headers.get("x-recruitee-signature", "")
    )


@router.post("/breezy/{connection_id}", status_code=status.HTTP_200_OK)
async def breezy_event(connection_id: UUID, request: Request) -> None:
    """The web hook prepza created in Breezy HR (candidates' stage changes), signed with its
    secret (the X-Hook-Signature header, checked on the body)."""
    await ats_webhooks.receive_breezy(
        connection_id, await request.body(), request.headers.get("x-hook-signature", "")
    )
