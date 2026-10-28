from billing.constants.credits import CANDIDATE_CREDITS, LOW_BALANCE
from billing.models.billing import Wallet
from billing.schemas.billing import BalanceOut


def balance_out(row: Wallet) -> BalanceOut:
    available = row.balance - row.reserved

    return BalanceOut(
        balance=row.balance,
        reserved=row.reserved,
        available=available,
        low=available < LOW_BALANCE,
        candidates=candidates_for(available),
    )


def candidates_for(available: int) -> int:
    """The candidates the available credits pay for."""
    return max(available, 0) // CANDIDATE_CREDITS
