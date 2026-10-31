from dataclasses import dataclass


@dataclass(frozen=True)
class Limit:
    """One of our limits (limit_list.LIMITS). Only the number can be changed (in the admin zone's
    Controls tab), within `lowest` and `highest`, so a typo can't make it 0 or a billion; its
    window stays as it is. A plain value (`counted` False), such as the AI calls generation makes
    at once, is a number the services use as it is: nothing counts against it, so it has no
    window and no hits."""

    # The service that enforces it.
    service: str
    default: int | float
    # calls, items, tokens or usd.
    unit: str
    # Seconds it counts over; None for a count of what exists (keys, members, ...).
    window: int | None
    lowest: int | float
    highest: int | float
    # Whom it counts: user, company, ip or everyone.
    scope: str
    # paid or unpaid when it holds only companies that did or didn't top up; None for everyone.
    audience: str | None = None
    # An unpaid limit's paid counterpart, which the Controls tab shows it beside.
    pair: str | None = None
    counted: bool = True
