from companies.constants.billing import Reason
from companies.integrations import billing
from companies.repositories import credit_invites
from companies.schemas.billing import CreditCandidateOut, HistoryEntryOut


def candidate_out(invite, interview) -> CreditCandidateOut:
    return CreditCandidateOut(
        invite_id=invite.id,
        interview_id=interview.id,
        email=invite.email,
        name=invite.name,
        interview_title=interview.title,
    )


async def page(company_id, offset: int, limit: int) -> list[HistoryEntryOut]:
    """A page of the company's credit movements, newest first. Each candidate's charge names
    its candidate, found by the key of its credits in one query; one whose invite is gone (removed,
    or the candidate deleted their account) says so, and nothing more."""
    rows = await billing.company_history(company_id, offset, limit)
    found = await credit_invites.by_hold_keys(
        company_id, [row["hold_key"] for row in rows if row["hold_key"]]
    )
    out = []

    for row in rows:
        candidate = None

        if row["reason"] == Reason.CANDIDATE and row["hold_key"] in found:
            candidate = candidate_out(*found[row["hold_key"]])

        out.append(
            HistoryEntryOut(
                id=row["id"],
                amount=row["amount"],
                reason=row["reason"],
                created_at=row["created_at"],
                total=row["total"],
                currency=row["currency"],
                automatic=row["automatic"],
                invoice_id=row["transaction_id"] if row["reason"] == Reason.TOPUP else None,
                candidate=candidate,
                candidate_deleted=row["reason"] == Reason.CANDIDATE and candidate is None,
                note=row["note"],
            )
        )

    return out


async def reserved(company_id, offset: int, limit: int) -> list[CreditCandidateOut]:
    """Candidates invited who haven't finished, whose credits are set aside, newest first."""
    rows = await credit_invites.holding(company_id, offset, limit)

    return [candidate_out(invite, interview) for invite, interview in rows]
