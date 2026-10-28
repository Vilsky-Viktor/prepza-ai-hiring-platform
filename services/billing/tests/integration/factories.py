"""Rows the integration tests start from, made as the services make them."""

from billing.services import wallets
from tests.integration.transactions import transaction


async def welcomed(company_id: str, owner_email: str) -> bool:
    """The company's wallet with the welcome credits, once per owner's email (the welcome's
    first step, in a transaction of its own)."""
    return await transaction(wallets.welcome_gift, company_id, owner_email)
