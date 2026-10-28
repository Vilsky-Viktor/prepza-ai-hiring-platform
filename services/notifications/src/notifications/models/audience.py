from collections.abc import Awaitable, Callable
from dataclasses import dataclass

# A list of user ids served a page at a time: `source(after)` gives the ids after `after`, in
# its own order, ID_PAGE_SIZE of them unless it's the last page.
Source = Callable[[str], Awaitable[list[str]]]


@dataclass
class Audience:
    """Whom a bulk send goes to (services/audiences.py): its sources, read one after the other,
    and for a product update or an offer to some groups the setting each recipient must have on
    (the groups' sources don't know it)."""

    sources: list[Source]
    setting: str | None = None
