import httpx

from app.constants.show import (
    ALL_PAGES,
    LINK_IDS,
    MAX_ROWS,
    NOTHING_TO_SHOW,
    ONE_EACH,
    PAGE_NAMES,
    PAGES,
    ROW_KINDS,
    SETTING_PAGES,
    SHOWN,
)
from app.helpers.blocks import SAFE_ID, link
from app.integrations import services
from app.models.answers import Turn
from app.services.live_blocks import fetch, items_for


async def page_name(page: str, ids: dict, token: str, language: str) -> str | None:
    """What the page is about (an interview's title, a company's name), read with the user's
    token; None for a page named by itself, or when it can't be read."""
    if page not in PAGE_NAMES:
        return None

    service, path, field = PAGE_NAMES[page]

    try:
        response = await services.get(service, link(path, ids) or "", {}, token, language)
    except httpx.HTTPError:
        return None

    return response.json().get(field) if response.is_success else None


def row_link(kind: str, ref: dict, company_id: str | None) -> str | None:
    """The page a row opens."""
    page = {"candidate_rows": "candidate", "interview": "interview", "credits": "top_up"}[kind]

    return link(PAGES[page], {"company_id": company_id, **ref})


def kept_ref(kind: str, ref: dict) -> dict:
    """A row as it's kept and read again (live_blocks): a candidate by "id" within its
    interview, an interview by "id"."""
    if kind == "candidate_rows":
        return {"id": ref["candidate_id"], "interview_id": ref["interview_id"]}

    if kind == "interview":
        return {"id": ref["interview_id"]}

    return ref


def all_link(kind: str, chosen: list[dict], companies: dict, company_id: str | None) -> str | None:
    """The page with all of a list's items, shown under its rows: the interview's candidates when
    the rows are one interview's, the company's interviews; None when the rows have no one page."""
    page = ALL_PAGES.get(kind)
    interviews = {ref.get("interview_id") for ref in chosen}

    if page is None or (kind == "candidate_rows" and len(interviews) != 1):
        return None

    interview_id = next(iter(interviews), None)
    company = companies.get(interview_id, company_id) if kind == "candidate_rows" else company_id

    return link(PAGES[page], {"company_id": company, "interview_id": interview_id})


async def interview_companies(chosen: list[dict], company_id: str | None, turn: Turn) -> dict:
    """Each chosen row's interview's company, read from the interview, when the model didn't
    name the company and none is picked in the panel (its rows' links need one)."""
    if company_id:
        return {}

    found = {}

    for interview_id in dict.fromkeys(ref.get("interview_id") for ref in chosen):
        if interview_id:
            interview = await fetch(f"/interviews/{interview_id}", {}, turn.token, turn.language)
            found[interview_id] = str(interview["company_id"]) if interview else None

    return found


async def rows_block(arguments: dict, turn: Turn) -> dict | None:
    """The rows the model chose, as the user may see them now (read with their token), newest
    first; None when none of them is."""
    kind, keys = ROW_KINDS[arguments["kind"]]
    chosen = [
        {key: str(row.get(key, "")) for key in keys}
        for row in (arguments.get("rows") or [])[:MAX_ROWS]
        if all(SAFE_ID.match(str(row.get(key, ""))) for key in keys)
    ]
    company_id = arguments.get("company_id") or (str(turn.company_id) if turn.company_id else None)
    companies = await interview_companies(chosen, company_id, turn)
    links = [
        row_link(kind, ref, companies.get(ref.get("interview_id"), company_id)) for ref in chosen
    ]
    refs = [kept_ref(kind, ref) for ref in chosen]
    block = {"kind": kind, "refs": refs, "links": links}
    found = await items_for(block, turn.token, turn.language)
    kept = [(item, url, ref) for item, url, ref in zip(found, links, refs, strict=True) if item]

    if not kept:
        return None

    # Newest first, whatever order the model chose them in.
    kept.sort(key=lambda row: str(row[0].get("created_at") or ""), reverse=True)

    every = all_link(kind, chosen, companies, company_id)

    return {
        "kind": kind,
        "items": [item for item, _, _ in kept],
        "links": [url for _, url, _ in kept],
        "all": every,
        "ref": {
            **block,
            "refs": [ref for _, _, ref in kept],
            "links": [url for _, url, _ in kept],
            "all": every,
        },
    }


async def link_block(arguments: dict, turn: Turn) -> dict | None:
    """One link to an app page, built from the fixed map and ids (never a URL from the model),
    named by what it opens; None when it can't be built or what it names isn't the user's."""
    page = arguments.get("page")

    if page not in PAGES:
        return None

    ids = {key: arguments.get(key) for key in LINK_IDS}
    ids["company_id"] = ids["company_id"] or (str(turn.company_id) if turn.company_id else None)
    url = link(PAGES[page], ids)

    if url is None:
        return None

    name = await page_name(page, ids, turn.token, turn.language)

    if page in PAGE_NAMES and name is None:
        return None

    ref = {"kind": "link", "page": page, "ids": {k: v for k, v in ids.items() if v}, "links": [url]}

    return {"kind": "link", "items": [], "links": [url], "page": page, "label": name, "ref": ref}


async def show(arguments: dict, turn: Turn, shown: set) -> tuple[dict, dict | None]:
    """What the model reads back, and the block to show (with `ref`, what's kept of it). One
    list and one link an answer: `shown` holds what this answer showed already."""
    kind = arguments.get("kind")
    slot = "link" if kind == "link" else "rows"

    if slot in shown:
        return {"error": 409, "detail": ONE_EACH}, None

    block = await (link_block(arguments, turn) if slot == "link" else rows_block(arguments, turn))

    if block is None:
        return {"error": 404, "detail": NOTHING_TO_SHOW}, None

    shown.add(slot)

    return {"detail": SHOWN}, block


# The reads that are about one interview, or one candidate, by the argument naming it.
INTERVIEW_ARGUMENT = "interview_id"
CANDIDATE_READS = {"get_scorecard": "invite_id"}


async def setting_link(answer, turn: Turn) -> dict | None:
    """The page of the one setting the answer read (auto top-up, Slack, ATSs, the API), where
    it's changed: asked to change it, the assistant can only point there. None beside an
    action's card."""
    found = {
        (SETTING_PAGES[result.tool], result.arguments.get("company_id"))
        for result in answer.results
        if result.succeeded and result.tool in SETTING_PAGES
    }

    if answer.pending or len(found) != 1:
        return None

    [(page, company_id)] = found

    return await link_block({"kind": "link", "page": page, "company_id": company_id}, turn)


async def implied_link(answer, turn: Turn) -> dict | None:
    """The link an answer about one interview, one candidate or one setting needs when the model
    gave none: that candidate's report, that interview's candidates, or the setting's page,
    from what the turn read."""
    interviews, candidates = set(), set()

    for result in answer.results:
        if not result.succeeded:
            continue

        if result.arguments.get(INTERVIEW_ARGUMENT):
            interviews.add(str(result.arguments[INTERVIEW_ARGUMENT]))

        if result.tool in CANDIDATE_READS:
            candidates.add(str(result.arguments.get(CANDIDATE_READS[result.tool])))

    if not interviews:
        return await setting_link(answer, turn)

    if len(interviews) != 1:
        return None

    [interview_id] = interviews

    if len(candidates) == 1:
        [candidate_id] = candidates
        target = {"page": "candidate", "interview_id": interview_id, "candidate_id": candidate_id}
    else:
        target = {"page": "interview_candidates", "interview_id": interview_id}

    return await link_block({"kind": "link", **target}, turn)


async def finish(answer, turn: Turn, emit) -> None:
    """Sends what the answer shows, once it's written, and keeps its references: the rows, and
    the link to the most specific page (added from what the turn read when the model gave
    none). A single row opens its own page, so it shows alone."""
    rows = next((block for block in answer.shown_blocks if block["kind"] != "link"), None)
    found = next((block for block in answer.shown_blocks if block["kind"] == "link"), None)
    single = rows is not None and len(rows["items"]) == 1

    if single:
        found = None
    elif found is None:
        found = await implied_link(answer, turn)

    for block in (rows, found):
        if block is not None:
            emit({"block": {key: value for key, value in block.items() if key != "ref"}})
            answer.blocks.append(block["ref"])
