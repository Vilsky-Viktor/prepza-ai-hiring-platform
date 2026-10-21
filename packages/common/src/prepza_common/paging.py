from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query
from prepza_common.constants import MAX_PAGE_SIZE


@dataclass
class Page:
    offset: int
    limit: int


def page(
    offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    limit: Annotated[
        int,
        Query(
            ge=1, le=MAX_PAGE_SIZE, description=f"Number of items to return, up to {MAX_PAGE_SIZE}"
        ),
    ] = MAX_PAGE_SIZE,
) -> Page:
    """`?offset=&limit=`; without them, the first full page."""
    return Page(offset=offset, limit=limit)


PageParams = Annotated[Page, Depends(page)]

# A page of ids another service reads in full a page at a time (a bulk send's audience): large,
# as each is a short string, but bounded.
ID_PAGE_SIZE = 5000


@dataclass
class IdPage:
    after: str
    limit: int


def id_page(
    after: Annotated[str, Query(description="The last id of the previous page")] = "",
    limit: Annotated[int, Query(ge=1, le=ID_PAGE_SIZE)] = ID_PAGE_SIZE,
) -> IdPage:
    """`?after=&limit=`: the ids after `after`, in order; without them, the first page."""
    return IdPage(after=after, limit=limit)


IdPageParams = Annotated[IdPage, Depends(id_page)]


async def every_id(read_page: Callable[[str], Awaitable[list[str]]]) -> list[str]:
    """Every id of a list served a page at a time (`read_page(after)`, ids in order), until a
    page comes back short."""
    found: list[str] = []

    while True:
        page_ids = await read_page(found[-1] if found else "")
        found += page_ids

        if len(page_ids) < ID_PAGE_SIZE:
            return found
