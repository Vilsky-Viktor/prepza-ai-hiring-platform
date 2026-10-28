from uuid import UUID

from pydantic import BaseModel


class OwnedCompany(BaseModel):
    id: UUID
    name: str


class LostCompany(OwnedCompany):
    # Its credits, lost with it; None when billing didn't answer.
    credits: int | None


class AccountDeletionOut(BaseModel):
    # Owned and joined by others: another member is made owner first, or the company deleted.
    blocked: list[OwnedCompany]
    # Owned alone: deleted with the account.
    deleted: list[LostCompany]
