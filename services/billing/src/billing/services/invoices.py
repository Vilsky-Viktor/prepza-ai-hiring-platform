from fastapi import HTTPException, status

from billing.constants.products import OwnerType
from billing.core.db import Session
from billing.integrations import paddle
from billing.repositories import purchases
from billing.schemas.billing import InvoiceOut


async def company_invoice(company_id: str, transaction_id: str) -> InvoiceOut:
    """The invoice of one of the company's top-ups; 404 for anyone else's transaction."""
    async with Session() as session:
        owned = await purchases.owns(session, OwnerType.COMPANY, company_id, transaction_id)

    if not owned:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    return InvoiceOut(url=await paddle.invoice_url(transaction_id))
