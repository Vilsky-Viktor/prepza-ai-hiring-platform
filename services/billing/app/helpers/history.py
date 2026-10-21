from app.constants.credits import ADJUSTMENTS, CANDIDATE_PREFIX, Reason
from app.helpers.money import row_minor
from app.models.billing import Entry
from app.schemas.billing import HistoryEntryOut


def transaction_id(entry: Entry) -> str | None:
    """The Paddle transaction of a top-up ("{transaction}:{product}") or an adjustment
    ("adjustment:{transaction}:{adjustment}"; older ones carry only the adjustment)."""
    if entry.reason == Reason.TOPUP:
        return entry.key.split(":")[0]

    parts = entry.key.split(":")

    if entry.reason in ADJUSTMENTS and len(parts) == 3:
        return parts[1]

    return None


def history_entry_out(entry: Entry) -> HistoryEntryOut:
    """One movement as the history shows it; a candidate's with the key of its hold, which
    companies knows the invite by."""
    hold_key = None

    if entry.reason == Reason.CANDIDATE and entry.key.startswith(CANDIDATE_PREFIX):
        hold_key = entry.key.removeprefix(CANDIDATE_PREFIX)

    return HistoryEntryOut(
        id=entry.id,
        amount=entry.amount,
        reason=entry.reason,
        created_at=entry.created_at,
        total=None if (minor := row_minor(entry)) is None else str(minor),
        currency=entry.currency,
        automatic=entry.automatic,
        note=entry.note,
        transaction_id=transaction_id(entry),
        hold_key=hold_key,
    )
