from datetime import datetime
from uuid import UUID

from sqlalchemy import Uuid, literal, tuple_


def changed_since(model, since: datetime, after: UUID | None) -> tuple[list, list]:
    """The filters and order that sync a list: rows changed at `since` or later, oldest change
    first; with `after` (the last row a client got), only rows after it, so rows changed at the
    same moment are neither repeated nor missed."""
    order = [model.updated_at, model.id]

    if after is None:
        return [model.updated_at >= since], order

    return [tuple_(*order) > tuple_(literal(since), literal(after, Uuid))], order
