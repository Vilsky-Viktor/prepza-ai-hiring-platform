import logging

from fastapi import HTTPException, status

from notifications.helpers.unsubscribe import address_hash
from notifications.integrations import companies
from notifications.repositories import opt_outs

logger = logging.getLogger(__name__)


async def companies_for(email: str) -> list[dict]:
    """The companies that invited the address or whose emails it stopped, by name, with what it
    stopped; a company that's gone is left out."""
    rows = await opt_outs.of_address(address_hash(email))
    ids = set(await companies.invited_company_ids(email)) | {row.company_id for row in rows}
    found = await companies.members(sorted(ids))

    return sorted(
        (
            {
                "company_id": company["id"],
                "name": company["name"],
                "stopped": any(
                    row.company_id == company["id"] and row.invite_id is None for row in rows
                ),
                "stopped_by_admin": any(
                    row.company_id == company["id"] and row.invite_id is None and row.by_admin
                    for row in rows
                ),
                "stopped_reminders": sum(
                    row.company_id == company["id"] and row.invite_id is not None for row in rows
                ),
            }
            for company in found
        ),
        key=lambda company: company["name"].lower(),
    )


async def set_stopped(email: str, company_id: str, stopped: bool, superadmin_id: str) -> None:
    """Stops every email from a company that invited the address, or lifts that stop again;
    the candidate's own stops, from an email's link, stay. Safe to repeat. Who did it goes to
    the logs, without the address."""
    address = address_hash(email)

    if stopped:
        if company_id not in await companies.invited_company_ids(email):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

        await opt_outs.add(address, company_id, by_admin=True)
    else:
        await opt_outs.remove_admin_stop(address, company_id)

    logger.warning(
        "Company %s's emails to address %s %s by superadmin %s",
        company_id,
        address,
        "stopped" if stopped else "let through again",
        superadmin_id,
    )
