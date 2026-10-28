import httpx

from assistant.constants.show import PAGE_NAMES
from assistant.constants.welcome import WELCOME_LIMIT
from assistant.helpers.trimming import trim
from assistant.integrations import services
from assistant.services.registry import tools

# Pages of an interview's candidates read to find the ones a block showed.
MAX_CANDIDATE_PAGES = 5


async def fetch(path: str, query: dict, token: str, language: str):
    """Companies' data for the viewer's own token; None when it's gone, not theirs any more, or
    companies didn't answer."""
    try:
        response = await services.get("companies", path, query, token, language)
    except httpx.HTTPError:
        return None

    return response.json() if response.is_success else None


async def candidates(refs: list[dict], token: str, language: str) -> dict[str, dict]:
    """The candidates the refs name, by id, from their interviews' lists."""
    found: dict[str, dict] = {}
    wanted = {ref["id"] for ref in refs}

    for interview_id in dict.fromkeys(ref["interview_id"] for ref in refs if ref["interview_id"]):
        for page in range(MAX_CANDIDATE_PAGES):
            query = {"limit": WELCOME_LIMIT, "offset": page * WELCOME_LIMIT}
            rows = await fetch(f"/interviews/{interview_id}/candidates", query, token, language)

            for row in rows or []:
                if row["id"] in wanted:
                    found[row["id"]] = {**row, "interview_id": interview_id}

            if not rows or len(rows) < WELCOME_LIMIT or wanted <= found.keys():
                break

    return found


async def items_for(block: dict, token: str, language: str) -> list[dict | None]:
    """Each ref's item as the viewer may see it now, in order; None for one that's gone."""
    refs = block.get("refs", [])
    kind = block["kind"]

    if kind == "candidate_rows":
        found = await candidates(refs, token, language)
        fields = tools()["list_candidates"].fields | {"interview_id"}

        return [
            trim(found[ref["id"]], fields, 1, 300) if ref["id"] in found else None for ref in refs
        ]

    if kind == "interview":
        fields = tools()["list_interviews"].fields
        rows = [await fetch(f"/interviews/{ref['id']}", {}, token, language) for ref in refs]

        return [trim(row, fields, 1, 300) if row else None for row in rows]

    if kind == "credits":
        balances = {
            row["id"]: row for row in await fetch("/companies/credits", {}, token, language) or []
        }
        rows = []

        for ref in refs:
            row = balances.get(ref["company_id"])
            row = row or await fetch(f"/companies/{ref['company_id']}/credits", {}, token, language)
            rows.append(row)

        return rows

    return []


async def live_link(block: dict, token: str, language: str) -> dict | None:
    """A stored link, named again with the viewer's token; None when what it names is gone."""
    from assistant.services.show import page_name

    page = block.get("page")
    name = await page_name(page, block.get("ids", {}), token, language) if page else None

    if page in PAGE_NAMES and name is None:
        return None

    return {
        "kind": "link",
        "items": [],
        "links": block.get("links", []),
        "page": page,
        "label": name,
    }


async def live(blocks: list[dict], token: str, language: str) -> list[dict]:
    """A stored answer's blocks, fetched again with the viewer's token: what they may see now,
    without anything that's gone (a deleted candidate, a company they left)."""
    shown = []

    for block in blocks:
        if block["kind"] == "link":
            found = await live_link(block, token, language)

            if found is not None:
                shown.append(found)

            continue

        items = await items_for(block, token, language)
        kept = [
            (item, link) for item, link in zip(items, block.get("links", []), strict=False) if item
        ]

        if kept:
            shown.append(
                {
                    "kind": block["kind"],
                    "items": [item for item, _ in kept],
                    "links": [link for _, link in kept],
                    "all": block.get("all"),
                }
            )

    return shown
