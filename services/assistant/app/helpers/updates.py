from datetime import UTC, datetime

from prepza_common.config.constants import MAX_UPDATES

from app.constants.tool_calls import MAX_STRING_LENGTH
from app.constants.updates import (
    ATS_NOT_INVITED,
    BELL_FIELDS,
    CREDITS_LOW,
    FROM_SOURCES,
    PASSED,
    SOURCE_FIELDS,
    TOP_UP_PATH,
)
from app.helpers.trimming import trim


def parsed_since(value: str) -> datetime | None:
    """An ISO 8601 time (UTC when it names no zone); None when it isn't one."""
    try:
        since = datetime.fromisoformat(value)
    except ValueError:
        return None

    return since if since.tzinfo else since.replace(tzinfo=UTC)


def source_event(item: dict, kind: str | None = None) -> dict:
    """An update as its own service tells it (a candidate's step, an ATS candidate not
    invited, a question flagged or fixed): one each, with its page."""
    return {
        "kind": kind or item["kind"],
        "at": item["at"],
        "company_id": str(item["company_id"]),
        "title": item.get("title"),
        **{field: item[field] for field in SOURCE_FIELDS if item.get(field) is not None},
        "link": item["link"],
    }


def bell_event(row: dict) -> dict:
    """A notification of the bell's other kinds (none of which it groups): what it says."""
    data = row["data"]

    return {
        "kind": row["kind"],
        "at": row["created_at"],
        "company_id": row["company_id"],
        "title": data.get("title"),
        **{field: data[field] for field in BELL_FIELDS if field in data},
        "link": row["link"],
    }


def events_of(candidates: list, not_invited: list, questions: list, bell: list) -> list[dict]:
    """Every update, newest first: each from its own service, then the bell's other
    notifications (its own of those kinds, which it groups, would tell them twice)."""
    events = [source_event(item) for item in candidates + questions]
    events += [source_event(item, ATS_NOT_INVITED) for item in not_invited]
    events += [bell_event(row) for row in bell if row["kind"] not in FROM_SOURCES]

    return sorted(events, key=lambda event: datetime.fromisoformat(event["at"]), reverse=True)


def credits_low(company: dict) -> dict:
    """A company running low on credits that no automatic top-up refills: a state, told on
    every check while it lasts."""
    return {
        "kind": CREDITS_LOW,
        "company_id": company["company_id"],
        "candidates_left": company["candidates"],
        "link": TOP_UP_PATH,
    }


def counts_of(candidates: dict, not_invited: dict, questions: dict, events: list[dict]) -> dict:
    """How many of each kind came in all: the services count their own (they list only the
    newest), the bell's other notifications, few, are counted here from `events`."""
    counts = {**candidates["counts"], ATS_NOT_INVITED: not_invited["total"], **questions["counts"]}
    sourced = set(counts)

    for event in events:
        if event["kind"] not in sourced:
            counts[event["kind"]] = counts.get(event["kind"], 0) + 1

    return counts


def summary(counts: dict[str, int], low: list[dict]) -> dict:
    """How many of each kind came (the kinds that did), how many finished candidates passed,
    and how many companies run low on credits."""
    found = {kind: count for kind, count in counts.items() if count}

    if low:
        found[CREDITS_LOW] = len(low)

    return found


def shown(update: dict, site: str) -> dict:
    """An update as the result lists it, without what its group already says."""
    kept = {key: value for key, value in update.items() if key not in ("company_id", "title")}

    return {**kept, "link": site + update["link"]}


def grouped(updates: list[dict], names: dict[str, str], site: str) -> list[dict]:
    """The updates by company, then by interview (by its title; those about no interview
    under `other`), in the order they come."""
    companies: dict[str, dict] = {}

    for update in updates:
        company_id = update["company_id"]
        company = companies.setdefault(
            company_id, {"company_id": company_id, "name": names[company_id], "interviews": {}}
        )
        title = update.get("title")

        if title:
            interview = company["interviews"].setdefault(title, {"title": title, "updates": []})
            interview["updates"].append(shown(update, site))
        else:
            company.setdefault("other", []).append(shown(update, site))

    return [
        {**company, "interviews": list(company["interviews"].values())}
        for company in companies.values()
    ]


def updates_result(
    events: list[dict],
    counts: dict[str, int],
    low: list[dict],
    names: dict[str, str],
    since: datetime,
    site: str,
) -> dict:
    """What get_updates answers: since when, the summary of every update (`counts`), then the
    companies running low on credits and the newest MAX_UPDATES events, grouped (with `shown`
    and `more` when there were more), trimmed like other tools' data."""
    listed = events[:MAX_UPDATES]
    result = {
        "since": since.isoformat(),
        "summary": summary(counts, low),
        "companies": grouped(low + listed, names, site),
    }

    if sum(count for kind, count in counts.items() if kind != PASSED) > len(listed):
        result |= {"shown": len(listed), "more": True}

    # Every listed update stays: none of its lists is longer than these.
    return trim(result, None, len(low) + len(listed), MAX_STRING_LENGTH)
