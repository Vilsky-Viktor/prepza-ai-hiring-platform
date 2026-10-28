from sqlalchemy import func, select

from ats.constants.ats import RECOVER_LIMIT
from ats.models.ats import AtsCandidate


def in_turns(conditions: tuple, oldest_first) -> select:
    """The candidates matching `conditions`, each connection's in turn (every connection's
    oldest, then every one's second...), at most RECOVER_LIMIT: one company's backlog doesn't
    hold up the others."""
    ranked = (
        select(
            AtsCandidate.id,
            oldest_first.label("since"),
            func.row_number()
            .over(partition_by=AtsCandidate.connection_id, order_by=oldest_first)
            .label("turn"),
        )
        .where(*conditions)
        .subquery()
    )

    return (
        select(AtsCandidate)
        .join(ranked, ranked.c.id == AtsCandidate.id)
        .order_by(ranked.c.turn, ranked.c.since)
        .limit(RECOVER_LIMIT)
    )
